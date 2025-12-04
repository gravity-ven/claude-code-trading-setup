#!/bin/bash
#
# COT Agents Live Output Runner
# This script is launched in the new terminal window
#

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Clear screen
clear

echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                                    ║${NC}"
echo -e "${CYAN}║        ${GREEN}SPARTAN 100 COT AGENTS${CYAN} - Live Output Monitor         ║${NC}"
echo -e "${CYAN}║                                                                    ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}🤖 Starting autonomous agent system...${NC}"
echo -e "${BLUE}📁 Working directory: ${SCRIPT_DIR}${NC}"
echo -e "${BLUE}⏰ Started at: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""
echo -e "${CYAN}────────────────────────────────────────────────────────────────────${NC}"
echo ""

# Change to script directory
cd "$SCRIPT_DIR"

# Run the agents with arguments passed from launcher
echo -e "${GREEN}Executing: python3 run_100_agents.py $@${NC}"
echo ""
echo -e "${CYAN}────────────────────────────────────────────────────────────────────${NC}"
echo ""

# Run agents with unbuffered output
python3 -u run_100_agents.py "$@"

# When done (if single-cycle)
echo ""
echo -e "${CYAN}────────────────────────────────────────────────────────────────────${NC}"
echo -e "${GREEN}✅ Agent execution completed${NC}"
echo -e "${YELLOW}⏰ Finished at: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""
echo -e "${BLUE}📊 View trade sheet:${NC}"
echo -e "   cat output/latest_trade_sheet.txt"
echo ""
echo -e "${BLUE}📋 View full logs:${NC}"
echo -e "   tail -f logs/agents.log"
echo ""
echo -e "${YELLOW}Press Enter to close this window...${NC}"
read
