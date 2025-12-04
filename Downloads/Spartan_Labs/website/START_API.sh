#!/bin/bash
echo "========================================"
echo "Spartan Research Station - Market Highlights API"
echo "========================================"
echo ""
echo "Starting backend API server..."
echo "Data Source: yfinance (real market data)"
echo "Server: http://localhost:5001"
echo ""

cd api

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet

# Start the API server
echo ""
echo "Starting API server..."
python highlights_api.py
