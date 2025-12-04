#!/bin/bash

################################################################################
# Spartan GARP Stock Screener - Quick Start Script
################################################################################

echo "════════════════════════════════════════════════════════════════════════"
echo "  SPARTAN GARP STOCK SCREENER - QUICK START"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "✗ Error: Python 3 not found"
    echo "  Install Python 3.8+ and try again"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Check dependencies
echo ""
echo "Checking dependencies..."

MISSING_DEPS=0

for package in flask yfinance pandas numpy; do
    if ! python3 -c "import $package" 2>/dev/null; then
        echo "  ✗ Missing: $package"
        MISSING_DEPS=1
    else
        echo "  ✓ Found: $package"
    fi
done

if [ $MISSING_DEPS -eq 1 ]; then
    echo ""
    echo "Installing missing dependencies..."
    pip3 install flask flask-cors yfinance pandas numpy
    if [ $? -ne 0 ]; then
        echo "✗ Failed to install dependencies"
        exit 1
    fi
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "  STARTING GARP API SERVER"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "API Endpoint: http://localhost:5003"
echo "Dashboard: Open garp.html in your browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "────────────────────────────────────────────────────────────────────────"
echo ""

# Start the API server
python3 garp_api.py
