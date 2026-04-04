# Changelog

## 2.5.3

### 🔧 Bug Fixes

- **Fix ha-mcp on aarch64**: Use system Python 3.12 instead of trying to install Python 3.13 (which isn't available on HA OS aarch64). Added `--index-strategy unsafe-best-match` so uvx can resolve pydantic-core from the HA wheel index (which has aarch64 builds) while pulling other packages from PyPI.
- **Remove unnecessary Python 3.13 install**: Removed `uv python install 3.13` from Dockerfile — not needed and added build time.

## 2.5.2

### 🔧 Bug Fixes

- **Fix ha-mcp pydantic-core wheel resolution**: The HA base image configures a custom wheel index (`wheels.home-assistant.io`) that only has cp312 musl wheels. Added `--no-config` to `uvx` calls so pydantic-core cp313 musllinux wheels are fetched from PyPI instead.
- **Upgrade ha-mcp to latest**: Removed the pin to `ha-mcp@3.5.1` — now installs the latest version (v7.2.0+, 92+ tools).
- **Pre-warm ha-mcp at build time**: Run `uvx --no-config --python 3.13 ha-mcp` during Docker build to cache all dependencies, avoiding slow first-launch installs.

## 2.5.1

### 🔧 Bug Fixes

- **Fix ha-mcp failing to start**: ha-mcp@3.5.1 requires pydantic-core wheels for Python 3.13 (cp313), but Alpine ships Python 3.12. Now explicitly uses `uvx --python 3.13` and pre-installs Python 3.13 at build time via `uv python install 3.13`.

## 2.5.0

### ✨ New Features

- **Home Assistant MCP integration**: Synced with upstream — Claude Code now has native Home Assistant integration via bundled ha-mcp server with 97+ tools for entity control, automations, scripts, dashboards, and more

## 2.4.3

### ✨ New Features

- **Auto-cleanup of uploaded images**: Images in `/data/images/` older than 6 hours are automatically deleted. Runs every 30 minutes to prevent disk usage from growing unbounded. Configurable via the `IMAGE_MAX_AGE_HOURS` environment variable.

## 2.4.2

### 🔧 Bug Fixes

- **Fix select-to-copy in terminal**: Previous monkey-patch of `navigator.clipboard.writeText` didn't work in the HA Ingress iframe context. Now uses a multi-strategy approach:
  - Patches `Clipboard.prototype.writeText` (catches all callers including xterm.js internals)
  - Listens for `mouseup` inside the iframe and copies any selected text via the parent frame — most reliable fallback
  - Retries handler injection at 2s and 5s after iframe load (ttyd rebuilds DOM after WebSocket connects)

## 2.4.1

### 🔧 Bug Fixes

- **Fix auto-copy on text selection in terminal**: xterm.js shows a brief copy icon when selecting text but the clipboard write silently failed in HA Ingress. Now monkey-patches `navigator.clipboard.writeText` inside the ttyd iframe to route through the parent frame's robust clipboard fallback. Select-to-copy now works without needing right-click.

## 2.4.0

### 🔧 Bug Fixes

- **Fix clipboard copy not working**: Click-to-copy on uploaded image paths and terminal text selection copy (Ctrl+C / Cmd+C) now work reliably inside HA Ingress
  - Added `clipboard-read` / `clipboard-write` permissions to the terminal iframe
  - Robust fallback copy using `execCommand` when the Clipboard API is blocked by the nested iframe context
  - Injected clipboard bridge into the ttyd iframe so text selection copy reaches the system clipboard
  - Added `Permissions-Policy` headers for clipboard access on proxied responses
  - Last-resort `window.prompt()` fallback if all clipboard methods fail

## 2.3.4

### 🔧 Stability Fixes

- **Dynamic Node.js heap sizing**: Automatically detect available memory and cap the heap accordingly (64/128/256 MB). Previous fixed 256 MB cap was still too large when the system-wide OOM killer fires due to exhausted RAM+swap.

## 2.3.3

### 🔧 Stability Fixes

- **Fix Claude being OOM-killed on low-memory hosts**: Cap Node.js heap to 256 MB (`--max-old-space-size=256`) so Claude Code doesn't exceed available RAM on typical HA systems with ≤1 GB memory. The default V8 heap (~1.5 GB) triggered the Linux OOM killer almost immediately.
- **Reduce startup memory footprint**: Move ttyd installation to the Docker image (build time) instead of installing at every container start. Eliminates runtime `apk` overhead on memory-constrained systems.

## 2.3.2

### 🔧 Stability Fixes

- **Fix Claude sessions being killed every ~22 seconds**: Two issues combined to make sessions unstable:
  1. **HA Ingress idle timeout** (pre-existing since v2.2.0): HA's reverse proxy drops idle WebSocket connections. Now the proxy sends periodic pings to the browser (every 20s) to keep the Ingress connection alive.
  2. **Proxy not responding to ttyd pings** (introduced in v2.3.0): The image-service proxy used `autoping=False`, so ttyd's PING frames never got a PONG reply — ttyd closed the connection after its pong timeout. Now properly auto-responds to pings on both sides.

## 2.3.0

### ✨ New Features

- **Image paste support**: Paste screenshots directly into the terminal with Ctrl+V / Cmd+V
  - Clipboard images are intercepted before xterm.js and uploaded automatically
  - Images saved to `/data/images/` (persistent across restarts)
  - File path shown in header bar and auto-copied to clipboard
  - Also supports drag-and-drop and file upload button
  - Lightweight Python proxy using aiohttp (no extra dependencies)
  - Tell Claude: `analyze /data/images/pasted-1234567890.png`

## 2.2.1

### 🔧 Stability Fixes

- **Auto-restart Claude on reconnect**: If Claude was killed (OOM, timeout) while you were away, it automatically restarts when you open the terminal again
  - No resources wasted — Claude only restarts when you actually reconnect
  - If Claude is still running, reconnect resumes the live session seamlessly
  - If you intentionally exited Claude, bash shell is preserved (no forced restart)

## 2.2.0

### ✨ New Features

- **Bundled Home Assistant MCP Server** (#48): Claude Code now has native Home Assistant integration
  - Switched to [homeassistant-ai/ha-mcp](https://github.com/homeassistant-ai/ha-mcp) - the comprehensive HA MCP server
  - 97+ tools for entity control, automations, scripts, dashboards, history, and more
  - Automatic configuration using Supervisor API - no manual token setup required
  - Natural language control: "Turn off the living room lights", "Create an automation for sunset"
  - New `enable_ha_mcp` configuration option (enabled by default)
  - Contributed by [@brianegge](https://github.com/brianegge)

### 🔧 Stability Fixes

- **Stable WebSocket connections**: Terminal sessions survive browser navigation and connection drops
  - tmux sessions persist through WebSocket disconnects (SIGHUP handled cleanly)
  - Automatic reattach on reconnect — no re-prompting or welcome screen replay
  - Claude exit drops to bash shell instead of killing the session
  - Faster reconnect (3s interval) with unlimited retries
- **Dynamic changelog in welcome screen**: What's New section now reads from CHANGELOG.md
  - No more hardcoded version entries — just update CHANGELOG.md
  - Shows cumulative changes for users who skip versions
  - Capped at 5 most recent entries with overflow indicator
- **Welcome screen improvements**: Auto-continues after 15s timeout, fixed box alignment

### 🛠️ Configuration

Enable or disable the Home Assistant MCP integration in your add-on config:

```yaml
enable_ha_mcp: true # default
```

### 📦 Technical Details

- Uses `uvx ha-mcp@3.5.1` for automatic package management and Python version handling
- Installed [uv](https://github.com/astral-sh/uv) via Alpine package for fast Python package execution
- MCP server connects to Home Assistant via internal Supervisor API (`http://supervisor/core`)
- Authentication uses the add-on's Supervisor token automatically

### 🔒 Security Note

The ha-mcp integration gives Claude extensive control over your Home Assistant instance, including the ability to control devices, modify automations, and access history data. You can disable it at any time by setting `enable_ha_mcp: false`.

### 💬 Example Usage

Once configured, you can ask Claude things like:

- "What's the current state of my thermostat?"
- "Turn on the porch lights"
- "Create an automation that turns on the coffee maker at 7 AM"
- "Show me the energy usage for the last week"
- "Debug why my motion sensor automation isn't working"

## 2.1.0

### ✨ New Features

- **Smart Status Bar**: tmux status bar now shows live system indicators
  - Auth status: green when authenticated, red when credentials are missing
  - Home Assistant connection: green when connected, yellow on issues
  - "Claude Terminal" identity label on the left side
  - Auto-refreshes every 15 seconds
- **Terminal Theme**: Dark, polished color scheme applied to the web terminal
  - Terracotta (#d97757) accent color for cursor and UI highlights
  - Improved contrast and readability with 14px font size
  - Matching tmux pane borders and window status colors

### 🎨 Visual Improvements

- Redesigned welcome banner with terracotta-accented borders and breathing room
- Redesigned session picker banner with matching branded style
- Dynamic version padding prevents box-drawing misalignment
- Cohesive color language across terminal theme, tmux, and banners

## 2.0.0

### ✨ New Features

- **HA Smart Context**: Claude automatically knows your Home Assistant setup
  - Generates a context file with system info, entity counts, installed add-ons, and recent errors
  - Claude Code loads this automatically — no configuration needed
  - Run `ha-context` to refresh, `ha-context --full` for detailed entity listings
  - New `ha_smart_context` config option (default: true) to enable/disable
  - Queries Supervisor + Core APIs: entities by domain, error log, system health
- **Welcome Screen**: Polished first-launch experience with version tracking
  - Styled banner displayed on every terminal open
  - "What's New" highlights shown once per version upgrade
  - Version tracking persisted across restarts

### 🎯 User Experience

- Every Claude session now has context about your HA environment out of the box
- Ask Claude about your entities, automations, or errors — it already knows

### 💙 Thank You

To everyone who stuck with me through the v1.6–1.9 rough patch — the musl binary issues, the nested tmux errors, the auth helper breakage — thank you for your patience, your bug reports, and your trust. This release is dedicated to you. I heard every issue, and I'm committed to making Claude Terminal the best it can be.

## 1.9.0

### 🔄 Changed

- **Reverted to npm installation**: Switched back from native installer to `npm install -g @anthropic-ai/claude-code`
  - Native binary requires musl 1.2.6+ (`posix_getdents` symbol), which Alpine 3.21 does not ship
  - npm installation runs on Node.js, avoiding all musl binary compatibility issues
  - Resolves #57, #60, #61
- **Removed native binary symlink logic** from `run.sh` (no longer needed with npm install)

## 1.7.0

### ✨ New Features

- **Session Persistence with tmux** (#46): Claude sessions now survive browser navigation
  - Sessions persist when navigating away from the terminal in Home Assistant
  - New "Reconnect to existing session" option in session picker (option 0)
  - Seamless session resumption - conversations continue exactly where you left off
  - tmux integration provides robust session management
  - Contributed by [@petterl](https://github.com/petterl)

### 🛠️ Technical Details

- Added tmux package to container
- Custom tmux configuration optimized for web terminals:
  - Mouse mode intelligently disabled when using ttyd (prevents conflicts)
  - OSC 52 clipboard support for copy/paste to browser
  - 50,000 line history buffer for extensive scrollback
  - Vi-style keybindings in copy mode
  - Visual improvements with better status bar
- Session picker enhanced with reconnection logic
- Automatic session cleanup and management

### 🎯 User Experience

- No more lost work when switching between Home Assistant pages
- Browser refresh no longer interrupts Claude conversations
- Tab switching preserves full session state including history
- Improved reliability for long-running Claude sessions

## 1.6.1

### 🐛 Bug Fix - Native Install Path Mismatch

- **Fixed "installMethod is native, but directory does not exist" error**: Claude binary now available at `$HOME/.local/bin/claude` at runtime
  - **Root cause**: Native installer places Claude at `/root/.local/bin/claude` during Docker build, but at runtime `HOME=/data/home`, so Claude's self-check looks in `/data/home/.local/bin/claude` which didn't exist
  - **Solution**: Symlink created from `/data/home/.local/bin/claude` → `/root/.local/bin/claude` on startup
  - **Result**: Claude native binary resolves correctly regardless of HOME directory change
  - Ref: [ESJavadex/claude-code-ha#3](https://github.com/ESJavadex/claude-code-ha/issues/3)

## 1.6.0 - 2026-01-26

### 🔄 Changed

- **Native Claude Code Installation**: Switched from npm package to official native installer
  - Uses `curl -fsSL https://claude.ai/install.sh | bash` instead of `npm install -g @anthropic-ai/claude-code`
  - Native binary provides automatic background updates from Anthropic
  - Faster startup (no Node.js interpreter overhead)
  - Claude binary symlinked to `/usr/local/bin/claude` for easy access
- **Simplified execution**: All scripts now call `claude` directly instead of `node $(which claude)`
- **Cleaner Dockerfile**: Removed npm retry/timeout configuration (no longer needed)

### 📦 Notes

- Node.js and npm remain available as development tools
- Existing authentication and configuration files are unaffected

## 1.5.0

### ✨ New Features

- **Persistent Package Management** (#32): Install APK and pip packages that survive container restarts
  - New `persist-install` command for installing packages from the terminal
  - Configuration options: `persistent_apk_packages` and `persistent_pip_packages`
  - Packages installed via command or config are automatically reinstalled on startup
  - Supports both Home Assistant add-on config and local state file
  - Inspired by community contribution from [@ESJavadex](https://github.com/ESJavadex)

### 📦 Usage Examples

```bash
# Install APK packages persistently
persist-install apk vim htop

# Install pip packages persistently
persist-install pip requests pandas numpy

# List all persistent packages
persist-install list

# Remove from persistence (package remains until restart)
persist-install remove apk vim
```

### 🛠️ Configuration

Add to your add-on config to auto-install packages:

```yaml
persistent_apk_packages:
  - vim
  - htop
persistent_pip_packages:
  - requests
  - pandas
```

## 1.4.1

### 🐛 Bug Fixes

- **Actually include Python and development tools** (#30): Fixed Dockerfile to include tools documented in v1.4.0
  - Resolves #27 (Add git to container)
  - Resolves #29 (v1.4.0 missing Python and development tools)
- **Added yq**: YAML processor for Home Assistant configuration files

## 1.4.0

### ✨ New Features

- **Added Python and development tools** (#26): Enhanced container with scripting and automation capabilities
  - **Python 3.11** with pip and commonly-used libraries (requests, aiohttp, yaml, beautifulsoup4)
  - **git** for version control
  - **vim** for advanced text editing
  - **jq** for JSON processing (essential for API work)
  - **tree** for directory visualization
  - **wget** and **netcat** for network operations

### 📦 Notes

- Image size increased from ~300 MB to ~457 MB (+52%) to accommodate new tools

## 1.3.2

### 🐛 Bug Fixes

- **Improved installation reliability** (#16): Enhanced resilience for network issues during installation
  - Added retry logic (3 attempts) for npm package installation
  - Configured npm with longer timeouts for slow/unstable connections
  - Explicitly set npm registry to avoid DNS resolution issues
  - Added 10-second delay between retry attempts

### 🛠️ Improvements

- **Enhanced network diagnostics**: Better troubleshooting for connection issues
  - Added DNS resolution checks to identify network configuration problems
  - Check connectivity to GitHub Container Registry (ghcr.io)
  - Extended connection timeouts for virtualized environments
  - More detailed error messages with specific solutions
- **Better virtualization support**: Improved guidance for VirtualBox and Proxmox users
  - Enhanced VirtualBox detection with detailed configuration requirements
  - Added Proxmox/QEMU environment detection
  - Specific network adapter recommendations for VM installations
  - Clear guidance on minimum resource requirements (2GB RAM, 8GB disk)

## 1.3.1

### 🐛 Critical Fix

- **Restored config directory access**: Fixed regression where add-on couldn't access Home Assistant configuration files
  - Re-added `config:rw` volume mapping that was accidentally removed in 1.2.0
  - Users can now properly access and edit their configuration files again

## 1.3.0

### ✨ New Features

- **Full Home Assistant API Access**: Enabled complete API access for automations and entity control
  - Added `hassio_api`, `homeassistant_api`, and `auth_api` permissions
  - Set `hassio_role` to 'manager' for full Supervisor access
  - Created comprehensive API examples script (`ha-api-examples.sh`)
  - Includes Supervisor API, Core API, and WebSocket examples
  - Python and bash code examples for entity control

### 🐛 Bug Fixes

- **Fixed authentication paste issues** (#14): Added authentication helper for clipboard problems
  - New authentication helper script with multiple input methods
  - Manual code entry option when clipboard paste fails
  - File-based authentication via `/config/auth-code.txt`
  - Integrated into session picker as menu option

### 🛠️ Improvements

- **Enhanced diagnostics** (#16): Added comprehensive health check system
  - System resource monitoring (memory, disk space)
  - Permission and dependency validation
  - VirtualBox-specific troubleshooting guidance
  - Automatic health check on startup
  - Improved error handling with strict mode

## 1.2.1

### 🔧 Internal Changes

- Fixed YAML formatting issues for better compatibility
- Added document start marker and fixed line lengths

## 1.2.0

### 🔒 Authentication Persistence Fix (PR #15)

- **Fixed OAuth token persistence**: Tokens now survive container restarts
  - Switched from `/config` to `/data` directory (Home Assistant best practice)
  - Implemented XDG Base Directory specification compliance
  - Added automatic migration for existing authentication files
  - Removed complex symlink/monitoring systems for simplicity
  - Maintains full backward compatibility

## 1.1.4

### 🧹 Maintenance

- **Cleaned up repository**: Removed erroneously committed test files (thanks @lox!)
- **Improved codebase hygiene**: Cleared unnecessary temporary and test configuration files

## 1.1.3

### 🐛 Bug Fixes

- **Fixed session picker input capture**: Resolved issue with ttyd intercepting stdin, preventing proper user input
- **Improved terminal interaction**: Session picker now correctly captures user choices in web terminal environment

## 1.1.2

### 🐛 Bug Fixes

- **Fixed session picker input handling**: Improved compatibility with ttyd web terminal environment
- **Enhanced input processing**: Better handling of user input with whitespace trimming
- **Improved error messages**: Added debugging output showing actual invalid input values
- **Better terminal compatibility**: Replaced `echo -n` with `printf` for web terminals

## 1.1.1

### 🐛 Bug Fixes

- **Fixed session picker not found**: Moved scripts from `/config/scripts/` to `/opt/scripts/` to avoid volume mapping conflicts
- **Fixed authentication persistence**: Improved credential directory setup with proper symlink recreation
- **Enhanced credential management**: Added proper file permissions (600) and logging for debugging
- **Resolved volume mapping issues**: Scripts now persist correctly without being overwritten

## 1.1.0

### ✨ New Features

- **Interactive Session Picker**: New menu-driven interface for choosing Claude session types
  - 🆕 New interactive session (default)
  - ⏩ Continue most recent conversation (-c)
  - 📋 Resume from conversation list (-r)
  - ⚙️ Custom Claude command with manual flags
  - 🐚 Drop to bash shell
  - ❌ Exit option
- **Configurable auto-launch**: New `auto_launch_claude` setting (default: true for backward compatibility)
- **Added nano text editor**: Enables `/memory` functionality and general text editing

### 🛠️ Architecture Changes

- **Simplified credential management**: Removed complex modular credential system
- **Streamlined startup process**: Eliminated problematic background services
- **Cleaner configuration**: Reduced complexity while maintaining functionality
- **Improved reliability**: Removed sources of startup failures from missing script dependencies

### 🔧 Improvements

- **Better startup logging**: More informative messages about configuration and setup
- **Enhanced backward compatibility**: Existing users see no change in behavior by default
- **Improved error handling**: Better fallback behavior when optional components are missing

## 1.0.2

### 🔒 Security Fixes

- **CRITICAL**: Fixed dangerous filesystem operations that could delete system files
- Limited credential searches to safe directories only (`/root`, `/home`, `/tmp`, `/config`)
- Replaced unsafe `find /` commands with targeted directory searches
- Added proper exclusions and safety checks in cleanup scripts

### 🐛 Bug Fixes

- **Fixed architecture mismatch**: Added missing `armv7` support to match build configuration
- **Fixed NPM package installation**: Pinned Claude Code package version for reliable builds
- **Fixed permission conflicts**: Standardized credential file permissions (600) across all scripts
- **Fixed race conditions**: Added proper startup delays for credential management service
- **Fixed script fallbacks**: Implemented embedded scripts when modules aren't found

### 🛠️ Improvements

- Added comprehensive error handling for all critical operations
- Improved build reliability with better package management
- Enhanced credential management with consistent permission handling
- Added proper validation for script copying and execution
- Improved startup logging for better debugging

### 🧪 Development

- Updated development environment to use Podman instead of Docker
- Added proper build arguments for local testing
- Created comprehensive testing framework with Nix development shell
- Added container policy configuration for rootless operation

## 1.0.0

- First stable release of Claude Terminal add-on:
  - Web-based terminal interface using ttyd
  - Pre-installed Claude Code CLI
  - User-friendly interface with clean welcome message
  - Simple claude-logout command for authentication
  - Direct access to Home Assistant configuration
  - OAuth authentication with Anthropic account
  - Auto-launches Claude in interactive mode
