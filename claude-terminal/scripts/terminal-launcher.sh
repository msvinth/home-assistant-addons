#!/bin/bash

# Terminal launcher for ttyd - manages welcome screen and tmux sessions
# Handles reconnection gracefully by skipping welcome on existing sessions
# and ensuring the session stays alive even if claude exits.

SESSION_NAME="claude"

# If a tmux session already exists, skip welcome and reattach directly.
# This makes WebSocket reconnects seamless - no re-prompting.
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    exec tmux attach-session -t "$SESSION_NAME"
fi

# First launch - show welcome if available
if command -v welcome >/dev/null 2>&1; then
    welcome
fi

# Start new tmux session running claude.
# If claude exits (crash, auth failure, user quit), fall back to bash
# so the tmux session stays alive and the user can retry or debug.
# 'exec' replaces this process with tmux, so SIGHUP from ttyd goes
# directly to the tmux client which detaches cleanly (session survives).
exec tmux new-session -s "$SESSION_NAME" 'claude; echo ""; echo "Claude exited. You are now in a bash shell."; echo "Run '\''claude'\'' to restart, or '\''exit'\'' to close."; exec bash'
