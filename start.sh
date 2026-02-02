#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "🚀 Starting NFC Reader Web Interface..."

# Check if Python venv exists, create if not
if [ ! -d "venv_nfc" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv_nfc
    echo "📦 Installing pyscard..."
    ./venv_nfc/bin/pip install pyscard > /dev/null
    echo "✅ Python environment ready"
else
    echo "✅ Python environment found"
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
    echo "✅ Node.js dependencies installed"
else
    echo "✅ Node.js dependencies found"
fi

# Check if server is already running
if [ -f ".pid" ]; then
    OLD_PID=$(cat .pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "⚠️  Server already running (PID: $OLD_PID)"
        echo "   Run ./stop.sh first or access http://localhost:3001"
        exit 1
    else
        rm .pid
    fi
fi

# Start server
echo ""
echo "▶️  Starting server..."
nohup node server.js > server.log 2>&1 &
echo $! > .pid

sleep 1

if ps -p $(cat .pid) > /dev/null 2>&1; then
    echo ""
    echo "✅ Server started successfully!"
    echo ""
    echo "   🌐 Open in browser: http://localhost:3001"
    echo "   📋 Logs: tail -f server.log"
    echo "   🛑 Stop: ./stop.sh"
    echo ""
else
    echo "❌ Failed to start server. Check server.log for details."
    cat server.log
    exit 1
fi
