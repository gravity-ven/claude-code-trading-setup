#!/bin/bash

# Spartan Trading Agent - Quick Start Script
# Run this to get started immediately!

echo "🎯 Spartan Trading Agent - Quick Start"
echo "========================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"
echo ""

# Step 1: Choose your path
echo "Choose your starting path:"
echo ""
echo "1) 🚀 FASTEST: Yahoo Finance (5 min, FREE, no broker signup)"
echo "2) 📊 RECOMMENDED: Alpaca Paper Trading (10 min, FREE, requires signup)"
echo "3) 💼 PROFESSIONAL: Interactive Brokers (30 min, professional setup)"
echo ""
read -p "Enter choice (1, 2, or 3): " choice

case $choice in
    1)
        echo ""
        echo "📖 Opening Yahoo Finance Quick Start..."
        cat NO_API_KEY_START.md
        ;;
    2)
        echo ""
        echo "📖 Opening Getting Started Guide..."
        cat GETTING_STARTED.md | head -100
        echo ""
        echo "📄 Full guide: GETTING_STARTED.md"
        ;;
    3)
        echo ""
        echo "📖 Opening Broker Alternatives Guide..."
        cat docs/broker_alternatives.md | head -100
        echo ""
        echo "📄 Full guide: docs/broker_alternatives.md"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🎉 Ready to start trading!"
echo ""
echo "Next steps:"
echo "1. Run: ./setup.sh"
echo "2. Configure: nano .env"
echo "3. Test: python3 examples/simple_test.py"
echo "4. Trade: python3 examples/yahoo_finance_trading.py"
