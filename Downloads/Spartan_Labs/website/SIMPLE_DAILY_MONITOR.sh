#!/bin/bash
#
# Simple Daily Monitor - Runs Forever
# Checks markets every 24 hours, shows countdown
#
# REAL DATA ONLY - No simulation
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}======================================================================${NC}"
echo -e "${GREEN}SPARTAN DAILY MONITOR - Continuous Mode${NC}"
echo -e "${CYAN}======================================================================${NC}"
echo ""
echo -e "${YELLOW}When it refreshes:${NC}"
echo -e "  * CFTC data: Every Friday 3:30 PM ET (real data source)"
echo -e "  * This monitor: Every 24 hours (checks for new data)"
echo ""
echo -e "${YELLOW}What happens:${NC}"
echo -e "  1. Run analysis cycle (takes ~10 seconds)"
echo -e "  2. Generate trade sheet in simple English"
echo -e "  3. Wait 24 hours"
echo -e "  4. Repeat forever (until you press Ctrl+C)"
echo ""
echo -e "${GREEN}Starting continuous monitor...${NC}"
echo ""

# Cycle counter
CYCLE=0

while true; do
    CYCLE=$((CYCLE + 1))

    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}CYCLE #$CYCLE - $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Run agents
    echo -e "${YELLOW}Running COT analysis...${NC}"
    python3 -u run_100_agents.py --demo --single-cycle 2>&1 | tail -20

    echo ""
    echo -e "${GREEN}✅ Cycle #$CYCLE complete!${NC}"
    echo ""

    # Show trade sheet if it exists
    if [ -f "output/latest_trade_sheet.txt" ]; then
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}LATEST TRADE RECOMMENDATIONS:${NC}"
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""

        # Show first 30 lines of trade sheet
        head -30 output/latest_trade_sheet.txt
        echo ""
        echo -e "${YELLOW}Full report: output/latest_trade_sheet.txt${NC}"
        echo ""
    fi

    # Countdown to next cycle
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Waiting 24 hours until next check...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop monitoring${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Countdown with live updates (every hour)
    SECONDS_LEFT=86400  # 24 hours in seconds

    while [ $SECONDS_LEFT -gt 0 ]; do
        HOURS=$((SECONDS_LEFT / 3600))
        MINS=$(((SECONDS_LEFT % 3600) / 60))

        printf "\r${CYAN}Next cycle in: ${YELLOW}%02d hours %02d minutes${NC}  " $HOURS $MINS

        sleep 3600  # Wait 1 hour
        SECONDS_LEFT=$((SECONDS_LEFT - 3600))
    done

    echo ""
    echo ""
done
