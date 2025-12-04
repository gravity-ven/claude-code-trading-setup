#!/bin/bash
#
# Quick script to attach to COT agents tmux session
#
# Usage: ./VIEW_COT_AGENTS.sh
#

SESSION_NAME="spartan-cot-agents"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Spartan COT Agents - Session Viewer${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if session exists
if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo -e "${RED}❌ No session found: $SESSION_NAME${NC}"
    echo ""
    echo -e "${YELLOW}Start the agents first with:${NC}"
    echo "  ./START_COT_AGENTS_WSL.sh --demo --single-cycle"
    echo ""
    exit 1
fi

echo -e "${GREEN}✅ Found session: $SESSION_NAME${NC}"
echo ""
echo -e "${YELLOW}Attaching to session...${NC}"
echo -e "${BLUE}(Press Ctrl+B then D to detach)${NC}"
echo ""
sleep 1

tmux attach -t "$SESSION_NAME"
