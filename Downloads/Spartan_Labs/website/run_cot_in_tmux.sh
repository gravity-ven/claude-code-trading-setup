#!/bin/bash
#
# Runner script for tmux session
# This is executed inside the tmux session
#

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Clear screen
clear

echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║        ${GREEN}SPARTAN 100 COT AGENTS${CYAN} - Live Output Monitor         ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}🤖 Starting autonomous agent system...${NC}"
echo -e "${BLUE}📁 Working directory: ${SCRIPT_DIR}${NC}"
echo -e "${BLUE}⏰ Started at: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""
echo -e "${CYAN}────────────────────────────────────────────────────────────────────${NC}"
echo ""
echo -e "${GREEN}Executing: python3 run_100_agents.py $@${NC}"
echo ""
echo -e "${CYAN}────────────────────────────────────────────────────────────────────${NC}"
echo ""

# Run agents with unbuffered output
python3 -u run_100_agents.py "$@"

EXIT_CODE=$?

echo ""
echo -e "${CYAN}────────────────────────────────────────────────────────────────────${NC}"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Agent execution completed successfully${NC}"
else
    echo -e "${RED}❌ Agent execution failed with code: $EXIT_CODE${NC}"
fi
echo -e "${YELLOW}⏰ Finished at: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""
echo -e "${BLUE}📊 View trade sheet:${NC}"
echo "   cat output/latest_trade_sheet.txt"
echo ""
echo -e "${BLUE}📋 View full logs:${NC}"
echo "   tail -f logs/agents.log"
echo ""
echo -e "${YELLOW}Press Ctrl+B then D to detach, or Enter to exit session...${NC}"

# Keep session alive
read -r
