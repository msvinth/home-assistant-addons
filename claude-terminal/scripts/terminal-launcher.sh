#!/bin/bash

# Terminal launcher for ttyd - manages welcome screen and tmux sessions
# Handles reconnection gracefully by skipping welcome on existing sessions.
# If Claude was killed while the user was away, it auto-restarts on reconnect
# (but only then — no resources wasted while nobody is watching).

SESSION_NAME="claude"

# If a tmux session already exists, handle reconnection.
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    # Check if this is a true reconnect (no browser tabs currently connected)
    # and whether Claude has exited (pane is running plain bash).
    client_count=$(tmux list-clients -t "$SESSION_NAME" 2>/dev/null | wc -l | tr -d ' ')
    pane_cmd=$(tmux display-message -t "$SESSION_NAME" -p '#{pane_current_command}')

    if [ "$client_count" -eq 0 ] && [ "$pane_cmd" = "bash" ]; then
        # User is reconnecting after being away, and Claude isn't running.
        # Restart Claude automatically so they come back to a live session.
        tmux send-keys -t "$SESSION_NAME" "claude" Enter
    fi

    exec tmux attach-session -t "$SESSION_NAME"
fi

# First launch - show welcome if available
if command -v welcome >/dev/null 2>&1; then
    welcome
fi

# Start new tmux session running claude.
# If claude exits (crash, auth failure, user quit), fall back to bash
# so the tmux session stays alive and the user can retry or debug.
# On next browser reconnect, terminal-launcher will auto-restart claude.
# 'exec' replaces this process with tmux, so SIGHUP from ttyd goes
# directly to the tmux client which detaches cleanly (session survives).
exec tmux new-session -s "$SESSION_NAME" 'claude; echo ""; echo "Claude exited. You are now in a bash shell."; echo "Run '\''claude'\'' to restart, or '\''exit'\'' to close."; exec bash'
