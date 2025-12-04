#!/bin/bash
#
# Automatically check for CFTC data and run agents
# Then display trade sheet results
#
# Usage: ./CHECK_AND_RUN_COT.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

clear

echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                                    ║${NC}"
echo -e "${CYAN}║        ${GREEN}SPARTAN COT AGENTS${CYAN} - Auto Data Check & Run           ║${NC}"
echo -e "${CYAN}║                                                                    ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check current day
CURRENT_DAY=$(date +%A)
CURRENT_TIME=$(date +%H:%M)
CURRENT_DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo -e "${BLUE}📅 Current time: ${CURRENT_DATE}${NC}"
echo -e "${BLUE}📊 CFTC releases: Fridays at 3:30 PM ET${NC}"
echo ""

# Function to check CFTC data
check_cftc_data() {
    python3 << 'PYEOF'
import requests
from datetime import datetime
import sys

# Check the weekly COT files (these are the ones CFTC actually publishes)
cot_files = {
    'Disaggregated Futures': 'https://www.cftc.gov/dea/newcot/f_disagg.txt',
    'Futures Only': 'https://www.cftc.gov/dea/newcot/deafut.txt',
    'Financial Futures': 'https://www.cftc.gov/dea/newcot/FinFutWk.txt',
}

for name, url in cot_files.items():
    try:
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            last_mod = response.headers.get('Last-Modified', 'Unknown')
            print(f"AVAILABLE:{name}:{last_mod}:{url}")
            sys.exit(0)
    except:
        pass

print("NOT_AVAILABLE")
sys.exit(1)
PYEOF
}

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}  STEP 1: Checking CFTC Data Availability${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

CFTC_CHECK=$(check_cftc_data)

if [[ $CFTC_CHECK == AVAILABLE:* ]]; then
    YEAR=$(echo "$CFTC_CHECK" | cut -d: -f2)
    LAST_MOD=$(echo "$CFTC_CHECK" | cut -d: -f3)
    URL=$(echo "$CFTC_CHECK" | cut -d: -f4)

    echo -e "${GREEN}✅ CFTC data is available!${NC}"
    echo -e "${GREEN}   Year: ${YEAR}${NC}"
    echo -e "${GREEN}   Last updated: ${LAST_MOD}${NC}"
    echo -e "${GREEN}   Source: ${URL}${NC}"
    echo ""

    DATA_AVAILABLE=true
else
    echo -e "${YELLOW}⚠️  CFTC data not yet available for 2025 or 2024${NC}"
    echo ""
    echo -e "${BLUE}ℹ️  CFTC publishes COT reports:${NC}"
    echo -e "   • Every Friday at 3:30 PM Eastern Time"
    echo -e "   • Data reflects positions as of Tuesday close"
    echo ""

    # Calculate next Friday
    if [ "$CURRENT_DAY" = "Friday" ]; then
        NEXT_RELEASE="Today (after 3:30 PM ET)"
    else
        NEXT_RELEASE="Next Friday at 3:30 PM ET"
    fi

    echo -e "${CYAN}📆 Next expected release: ${NEXT_RELEASE}${NC}"
    echo ""

    DATA_AVAILABLE=false
fi

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}  STEP 2: Running COT Agents${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ "$DATA_AVAILABLE" = true ]; then
    echo -e "${GREEN}Running agents with live CFTC data...${NC}"
else
    echo -e "${YELLOW}Running agents in demo mode (no live data available)...${NC}"
fi
echo ""

# Run the TUI dashboard
./START_COT_TUI.sh --demo --single-cycle

echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}  STEP 3: Trade Sheet Results${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check for trade sheet
TRADE_SHEET="output/latest_trade_sheet.txt"

if [ -f "$TRADE_SHEET" ]; then
    echo -e "${GREEN}✅ Trade sheet found!${NC}"
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  📊 LATEST TRADE SHEET${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════════════${NC}"
    echo ""

    # Display trade sheet with syntax highlighting
    cat "$TRADE_SHEET"

    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BLUE}📄 Full trade sheet saved to:${NC}"
    echo -e "   ${TRADE_SHEET}"
    echo ""
else
    echo -e "${YELLOW}⚠️  No trade sheet generated${NC}"
    echo ""
    echo -e "${BLUE}ℹ️  Possible reasons:${NC}"
    echo -e "   • CFTC data not yet available"
    echo -e "   • No high-confidence opportunities found"
    echo -e "   • Agents still waiting for new weekly data"
    echo ""
    echo -e "${CYAN}💡 Try again after Friday 3:30 PM ET when new data is released${NC}"
    echo ""
fi

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}  Summary${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ "$DATA_AVAILABLE" = true ]; then
    echo -e "${GREEN}✅ CFTC data: Available${NC}"
else
    echo -e "${YELLOW}⚠️  CFTC data: Waiting for next release${NC}"
fi

if [ -f "$TRADE_SHEET" ]; then
    SHEET_SIZE=$(wc -l < "$TRADE_SHEET")
    echo -e "${GREEN}✅ Trade sheet: Generated (${SHEET_SIZE} lines)${NC}"
else
    echo -e "${YELLOW}⚠️  Trade sheet: Not yet available${NC}"
fi

echo ""
echo -e "${BLUE}📋 View detailed logs:${NC}"
echo "   tail -f logs/agents.log"
echo ""
echo -e "${BLUE}🔄 Run this check again:${NC}"
echo "   ./CHECK_AND_RUN_COT.sh"
echo ""
