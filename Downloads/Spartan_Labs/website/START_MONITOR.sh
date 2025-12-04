#!/bin/bash
#
# Start Spartan COT Agents - Persistent Market Monitor
#
# REAL DATA ONLY - Continuous analysis
# Runs forever until you stop it (Ctrl+C)
#
# Usage:
#   ./START_MONITOR.sh                    # Production (100 agents, 1 hour interval)
#   ./START_MONITOR.sh --demo             # Demo (4 agents, 1 hour interval)
#   ./START_MONITOR.sh --demo --interval 6  # Demo (4 agents, 6 hour interval)
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
echo -e "${CYAN}      ${GREEN}SPARTAN COT AGENTS${CYAN} - Persistent Market Monitor           ${NC}"
echo -e "${CYAN}                                                                      ${NC}"
echo -e "${CYAN}======================================================================${NC}"
echo ""
echo -e "${YELLOW}REAL DATA ONLY - Continuous market analysis${NC}"
echo -e "${YELLOW}Trade sheet displayed inline in dashboard${NC}"
echo -e "${YELLOW}Runs forever until you stop it (Ctrl+C)${NC}"
echo ""
sleep 2

# Run the persistent monitor TUI
python3 run_cot_monitor_tui.py "$@"
