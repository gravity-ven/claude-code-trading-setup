#!/bin/bash
# Start Spartan Trading Agent in paper trading mode

set -e

echo "=========================================="
echo "Spartan Trading Agent"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Run ./setup.sh first"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Run ./setup.sh and configure your API keys"
    exit 1
fi

# Check if logs directory exists
mkdir -p logs

echo "✓ Environment ready"
echo ""
echo "Starting paper trading..."
echo "Press Ctrl+C to stop"
echo ""
echo "=========================================="
echo ""

# Run the trading agent
python examples/basic_trading.py
