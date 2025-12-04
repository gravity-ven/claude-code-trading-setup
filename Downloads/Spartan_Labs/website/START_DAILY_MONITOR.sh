#!/bin/bash
#
# Start Spartan COT Agents - Daily Investment Monitor
#
# WHEN IT REFRESHES:
#   - Checks markets: Every 24 hours (daily)
#   - New CFTC data: Every Friday at 3:30 PM ET
#   - Best time to check results: Friday evenings or Saturday mornings
#
# WHAT YOU GET:
#   - Clear investment recommendations in simple English
#   - "BUY Gold because..." explanations
#   - Which symbols are worth investing in and why
#
# Usage:
#   ./START_DAILY_MONITOR.sh              # Demo mode (4 agents)
#   ./START_DAILY_MONITOR.sh --production # Production (100 agents)
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

clear

echo -e "${CYAN}======================================================================${NC}"
echo -e "${CYAN}                                                                      ${NC}"
echo -e "${CYAN}        ${GREEN}SPARTAN COT AGENTS${CYAN} - Daily Investment Monitor             ${NC}"
echo -e "${CYAN}                                                                      ${NC}"
echo -e "${CYAN}======================================================================${NC}"
echo ""
echo -e "${GREEN}WHAT THIS DOES:${NC}"
echo -e "  * Analyzes markets using real CFTC data (professional traders' positions)"
echo -e "  * Shows which symbols are worth investing in"
echo -e "  * Explains WHY in simple English"
echo ""
echo -e "${YELLOW}WHEN IT REFRESHES:${NC}"
echo -e "  * This monitor checks: Every 24 hours (once per day)"
echo -e "  * CFTC releases new data: Every Friday at 3:30 PM ET"
echo -e "  * Data reflects: Tuesday's market positions (3-day lag is normal)"
echo ""
echo -e "${YELLOW}BEST TIME TO CHECK RESULTS:${NC}"
echo -e "  * Friday evenings (after 3:30 PM ET) - Fresh data just released"
echo -e "  * Saturday mornings - Review weekly opportunities"
echo -e "  * Sunday - Plan your week's trades"
echo ""
echo -e "${GREEN}UNDERSTANDING THE DATA:${NC}"
echo -e "  * Week 1-4: System is learning (building database)"
echo -e "  * Week 5-10: First opportunities start appearing"
echo -e "  * Week 26+: Full confidence signals available"
echo ""
echo -e "${YELLOW}Starting daily monitor...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop monitoring${NC}"
echo ""
sleep 3

# Determine mode
if [[ "$1" == "--production" ]]; then
    echo -e "${GREEN}Running in PRODUCTION mode (100 agents)${NC}"
    echo ""
    python3 run_cot_monitor_tui.py --interval 24
else
    echo -e "${GREEN}Running in DEMO mode (4 agents - recommended for testing)${NC}"
    echo ""
    python3 run_cot_monitor_tui.py --demo --interval 24
fi
