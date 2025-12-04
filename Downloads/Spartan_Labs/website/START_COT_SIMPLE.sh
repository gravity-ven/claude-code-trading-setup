#!/bin/bash
#
# Simple COT Agents Launcher - Opens new CMD window
# Works on WSL2 without requiring Windows Terminal
#
# Usage: ./START_COT_SIMPLE.sh [--demo] [--single-cycle]
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARGS="${@:---demo --single-cycle}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}=====================================================================${NC}"
echo -e "${GREEN}  Spartan COT Agents - Simple Launcher (CMD Window)${NC}"
echo -e "${GREEN}=====================================================================${NC}"
echo ""
echo -e "${YELLOW}Opening new CMD window with agents...${NC}"
echo -e "${YELLOW}Arguments: ${ARGS}${NC}"
echo ""

# Convert WSL path to Windows path
WIN_DIR=$(wslpath -w "$SCRIPT_DIR" | sed 's/\\/\\\\/g')

# Launch in new CMD window using start
cmd.exe /c "start cmd.exe /k \"cd /d $WIN_DIR && wsl python3 run_100_agents.py $ARGS\""

echo -e "${GREEN}✅ Agents launched in new CMD window${NC}"
echo ""
echo -e "${BLUE}To view output later:${NC}"
echo "  tail -f logs/agents.log"
echo ""
