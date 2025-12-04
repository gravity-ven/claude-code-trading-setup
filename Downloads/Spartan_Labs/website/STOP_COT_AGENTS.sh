#!/bin/bash
#
# Stop COT agents tmux session
#
# Usage: ./STOP_COT_AGENTS.sh
#

SESSION_NAME="spartan-cot-agents"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  Spartan COT Agents - Stop Session${NC}"
echo -e "${YELLOW}════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if session exists
if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  No session found: $SESSION_NAME${NC}"
    echo -e "${GREEN}(Agents are not running)${NC}"
    echo ""
    exit 0
fi

echo -e "${YELLOW}Stopping session: $SESSION_NAME${NC}"
tmux kill-session -t "$SESSION_NAME"

echo -e "${GREEN}✅ Session stopped${NC}"
echo ""
