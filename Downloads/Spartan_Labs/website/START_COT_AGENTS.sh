#!/bin/bash
#
# Launch COT Agents in new window (WSL-friendly)
# Usage: ./START_COT_AGENTS.sh [--demo] [--single-cycle]
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARGS="${@:---demo --single-cycle}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}=====================================================================${NC}"
echo -e "${GREEN}  Spartan COT Agents Launcher${NC}"
echo -e "${GREEN}=====================================================================${NC}"
echo ""

# Convert to Windows path
WIN_DIR=$(wslpath -w "$SCRIPT_DIR")

# Launch batch file which handles the new window
echo -e "${YELLOW}Launching agents in new window...${NC}"
echo -e "${YELLOW}Arguments: ${ARGS}${NC}"
echo ""

# Use cmd to launch the batch file
cd "$SCRIPT_DIR"
cmd.exe /c "start_cot_agents.bat $ARGS"

echo -e "${GREEN}✅ Launched! Check the new window for output.${NC}"
echo ""
echo -e "${BLUE}View logs:${NC}"
echo "  tail -f logs/agents.log"
echo ""
