#!/bin/bash
#
# Download 156 Weeks (3 Years) of Historical COT Data
# Run this ONCE to bootstrap the system with historical data
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║         DOWNLOAD HISTORICAL COT DATA (156 WEEKS)                ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "This will download 3 years of CFTC Commitment of Traders data"
echo "for all 42+ markets (Gold, Oil, Bitcoin, S&P 500, etc.)"
echo ""
echo "What this does:"
echo "  ✅ Downloads real CFTC.gov data (156 weeks)"
echo "  ✅ Stores in PostgreSQL database"
echo "  ✅ Enables COT Index calculation"
echo "  ✅ Unlocks trade signal generation"
echo ""
echo "Time required: 3-7 minutes"
echo "Run this ONCE, then agents auto-maintain data weekly"
echo ""
echo "Press Enter to continue or Ctrl+C to cancel..."
read

# Run downloader (execute directly to use shebang)
./download_historical_cot_data.py

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║                ✅ HISTORICAL DATA DOWNLOAD COMPLETE              ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Launch TUI: ./START_TUI_WITH_TRADES.sh"
echo "  2. Trade signals will now appear (if COT extremes exist)"
echo "  3. System auto-updates weekly going forward"
echo ""
