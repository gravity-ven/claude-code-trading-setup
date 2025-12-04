#!/bin/bash
#
# Launch COT TUI with Trade Sheet Integration
# Real-time dashboard with investment signals
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "======================================================================"
echo "  Spartan COT Agents - TUI with Trade Sheet"
echo "======================================================================"
echo ""
echo "Starting real-time dashboard with investment signals..."
echo ""
echo "Features:"
echo "  * 4-Tier agent execution (COT, Seasonality, Confluence, Trade Sheet)"
echo "  * Real-time trade signals displayed in TUI"
echo "  * Auto-refreshing investment recommendations"
echo "  * Pure ASCII interface (works everywhere)"
echo ""
echo "Press Ctrl+C to exit at any time"
echo ""
echo "Starting in 3 seconds..."
sleep 3

# Run TUI continuously (every 24 hours)
CYCLE=0
while true; do
    CYCLE=$((CYCLE + 1))

    echo ""
    echo "======================================================================"
    echo "CYCLE #$CYCLE - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "======================================================================"
    echo ""

    # Run TUI with demo mode
    python3 -u run_cot_ascii_tui.py --demo

    echo ""
    echo "======================================================================"
    echo "Cycle #$CYCLE complete. Next run in 24 hours."
    echo "Press Ctrl+C to stop monitoring"
    echo "======================================================================"
    echo ""

    # Wait 24 hours
    sleep 86400
done
