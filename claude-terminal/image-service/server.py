#!/usr/bin/env python3
"""Image upload proxy for Claude Terminal.

Lightweight aiohttp server (no extra deps — py3-aiohttp is pre-installed) that:
  - Serves custom HTML with paste/drag-drop image upload support
  - Handles POST /upload (saves images to /data/images/)
  - Proxies HTTP + WebSocket to ttyd on an internal port
"""

import asyncio
import os
import time
from pathlib import Path

from aiohttp import web, ClientSession, WSMsgType

TTYD_PORT = int(os.environ.get('TTYD_PORT', 7681))
TTYD_URL = f'http://127.0.0.1:{TTYD_PORT}'
UPLOAD_DIR = Path(os.environ.get('UPLOAD_DIR', '/data/images'))
PORT = int(os.environ.get('IMAGE_SERVICE_PORT', 7680))
MAX_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_TYPES = frozenset({
    'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml',
})
EXT_MAP = {
    'image/jpeg': '.jpg', 'image/png': '.png', 'image/gif': '.gif',
    'image/webp': '.webp', 'image/svg+xml': '.svg',
}
STATIC_DIR = Path(__file__).parent / 'static'


# ---------------------------------------------------------------------------
# Startup / shutdown hooks
# ---------------------------------------------------------------------------

async def on_startup(app):
    app['session'] = ClientSession()


async def on_cleanup(app):
    await app['session'].close()


# ---------------------------------------------------------------------------
# Image upload
# ---------------------------------------------------------------------------

async def handle_upload(request):
    """Save an uploaded image and return its file path."""
    reader = await request.multipart()
    field = await reader.next()
    if not field or field.name != 'image':
        return web.json_response({'error': 'No image provided'}, status=400)

    content_type = field.headers.get('Content-Type', '')
    if content_type not in ALLOWED_TYPES:
        return web.json_response(
            {'error': f'Unsupported image type: {content_type}'}, status=400,
        )

    ext = EXT_MAP.get(content_type, '.png')
    filename = f'pasted-{int(time.time() * 1000)}{ext}'
    filepath = UPLOAD_DIR / filename

    size = 0
    with open(filepath, 'wb') as f:
        while True:
            chunk = await field.read_chunk(8192)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_SIZE:
                filepath.unlink(missing_ok=True)
                return web.json_response(
                    {'error': 'File too large (10 MB max)'}, status=400,
                )
            f.write(chunk)

    filepath.chmod(0o644)
    return web.json_response({
        'success': True,
        'path': str(filepath),
        'filename': filename,
        'size': size,
    })


# ---------------------------------------------------------------------------
# WebSocket proxy  (ttyd uses binary frames with a 1-byte type prefix)
# ---------------------------------------------------------------------------

async def ws_proxy(request, path='ws'):
    """Bidirectional WebSocket proxy to ttyd."""
    ws_up = web.WebSocketResponse(protocols=['tty'])
    await ws_up.prepare(request)

    qs = request.query_string
    ws_url = f'ws://127.0.0.1:{TTYD_PORT}/{path}{"?" + qs if qs else ""}'

    session = request.app['session']
    try:
        async with session.ws_connect(ws_url, protocols=['tty']) as ws_down:
            async def forward(src, dst):
                async for msg in src:
                    if msg.type == WSMsgType.BINARY:
                        await dst.send_bytes(msg.data)
                    elif msg.type == WSMsgType.TEXT:
                        await dst.send_str(msg.data)
                    elif msg.type in (
                        WSMsgType.CLOSE, WSMsgType.CLOSING, WSMsgType.ERROR,
                    ):
                        return

            done, pending = await asyncio.wait(
                [
                    asyncio.create_task(forward(ws_up, ws_down)),
                    asyncio.create_task(forward(ws_down, ws_up)),
                ],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
    except Exception as exc:
        print(f'[image-service] WebSocket proxy error: {exc}')

    return ws_up


# ---------------------------------------------------------------------------
# HTTP reverse proxy  (ttyd assets, /token endpoint, etc.)
# ---------------------------------------------------------------------------

async def terminal_proxy(request):
    """Proxy /terminal/* to ttyd — handles both HTTP and WebSocket."""
    path = request.match_info.get('path', '')

    # WebSocket upgrade
    if request.headers.get('upgrade', '').lower() == 'websocket':
        return await ws_proxy(request, path)

    # Regular HTTP
    url = f'{TTYD_URL}/{path}'
    if request.query_string:
        url += f'?{request.query_string}'

    session = request.app['session']
    try:
        async with session.request(
            request.method,
            url,
            headers={
                k: v for k, v in request.headers.items()
                if k.lower() not in ('host', 'connection', 'upgrade')
            },
            data=await request.read(),
        ) as resp:
            skip = frozenset({
                'transfer-encoding', 'connection', 'content-encoding',
            })
            headers = {
                k: v for k, v in resp.headers.items()
                if k.lower() not in skip
            }
            return web.Response(
                body=await resp.read(),
                status=resp.status,
                headers=headers,
            )
    except Exception as exc:
        return web.Response(text=f'Terminal not ready: {exc}', status=502)


# ---------------------------------------------------------------------------
# Static index
# ---------------------------------------------------------------------------

async def index_handler(request):
    return web.FileResponse(STATIC_DIR / 'index.html')


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    app = web.Application(client_max_size=MAX_SIZE + 4096)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    app.router.add_get('/', index_handler)
    app.router.add_post('/upload', handle_upload)
    app.router.add_route('*', '/terminal/{path:.*}', terminal_proxy)
    app.router.add_route('*', '/terminal', terminal_proxy)

    return app


if __name__ == '__main__':
    print(f'[image-service] port {PORT} → ttyd :{TTYD_PORT}')
    web.run_app(
        create_app(),
        host='0.0.0.0',
        port=PORT,
        print=lambda s: print(f'[image-service] {s}'),
    )
