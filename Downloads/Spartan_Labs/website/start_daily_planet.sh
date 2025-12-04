#!/bin/bash

# Daily Planet Quick Start Script
# Automatically starts the API server and opens the dashboard

echo "============================================================"
echo "           DAILY PLANET - QUICK START"
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://www.python.org/"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Check if required packages are installed
echo "Checking dependencies..."
MISSING_DEPS=""

if ! python3 -c "import flask" 2>/dev/null; then
    MISSING_DEPS="$MISSING_DEPS flask"
fi

if ! python3 -c "import flask_cors" 2>/dev/null; then
    MISSING_DEPS="$MISSING_DEPS flask-cors"
fi

if ! python3 -c "import yfinance" 2>/dev/null; then
    MISSING_DEPS="$MISSING_DEPS yfinance"
fi

if [ -n "$MISSING_DEPS" ]; then
    echo "❌ Missing dependencies:$MISSING_DEPS"
    echo ""
    echo "Installing dependencies..."
    pip install flask flask-cors yfinance

    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        echo "Please run manually: pip install flask flask-cors yfinance"
        exit 1
    fi
    echo "✅ Dependencies installed successfully"
else
    echo "✅ All dependencies found"
fi

echo ""
echo "============================================================"
echo "Starting Daily Planet API Server..."
echo "============================================================"
echo ""

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if API script exists
if [ ! -f "daily_planet_api.py" ]; then
    echo "❌ Error: daily_planet_api.py not found in $SCRIPT_DIR"
    exit 1
fi

# Start API server in background
python3 daily_planet_api.py &
API_PID=$!

echo "✅ API Server started (PID: $API_PID)"
echo ""

# Wait for API to start
echo "Waiting for API server to initialize..."
sleep 3

# Check if API is running
if curl -s http://localhost:5000/health > /dev/null; then
    echo "✅ API Server is healthy and responding"
else
    echo "⚠️  Warning: API server may not be ready yet"
    echo "   Give it a few more seconds..."
fi

echo ""
echo "============================================================"
echo "Opening Daily Planet Dashboard..."
echo "============================================================"
echo ""

# Detect OS and open browser
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux (WSL)
    if grep -qi microsoft /proc/version; then
        # WSL - use Windows browser
        HTML_PATH="$(wslpath -w "$SCRIPT_DIR/daily_planet.html")"
        cmd.exe /c start "$HTML_PATH"
        echo "✅ Dashboard opened in Windows browser"
    else
        # Native Linux
        xdg-open "$SCRIPT_DIR/daily_planet.html"
        echo "✅ Dashboard opened in default browser"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "$SCRIPT_DIR/daily_planet.html"
    echo "✅ Dashboard opened in default browser"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows Git Bash / Cygwin
    start "$SCRIPT_DIR/daily_planet.html"
    echo "✅ Dashboard opened in default browser"
else
    echo "⚠️  Could not auto-open browser. Please open manually:"
    echo "   file://$SCRIPT_DIR/daily_planet.html"
fi

echo ""
echo "============================================================"
echo "           DAILY PLANET IS NOW RUNNING"
echo "============================================================"
echo ""
echo "📊 Dashboard: file://$SCRIPT_DIR/daily_planet.html"
echo "🔌 API Server: http://localhost:5000"
echo "📝 Logs: Check terminal output below"
echo ""
echo "To stop the server:"
echo "  Press Ctrl+C or run: kill $API_PID"
echo ""
echo "============================================================"
echo ""

# Keep script running to show API logs
wait $API_PID
