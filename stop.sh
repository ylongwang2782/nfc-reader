#!/bin/bash

cd "$(dirname "$0")"

echo "🛑 Stopping NFC Reader Server..."

if [ -f ".pid" ]; then
    PID=$(cat .pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        rm .pid
        echo "✅ Server stopped (PID: $PID)"
    else
        rm .pid
        echo "⚠️  Server was not running (stale PID file removed)"
    fi
else
    # Try to find and kill by port
    PID=$(lsof -ti:3001 2>/dev/null)
    if [ -n "$PID" ]; then
        kill $PID
        echo "✅ Server stopped (PID: $PID)"
    else
        echo "⚠️  Server is not running"
    fi
fi
