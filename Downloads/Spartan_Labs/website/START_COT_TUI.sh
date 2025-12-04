#!/bin/bash
#
# Launch COT Agents with Beautiful TUI Dashboard (tmux)
# Usage: ./START_COT_TUI.sh [--demo] [--single-cycle]
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SESSION_NAME="spartan-cot-agents-tui"
ARGS="${@:---demo --single-cycle}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

clear

echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                                    ║${NC}"
echo -e "${CYAN}║     ${GREEN}SPARTAN COT AGENTS${CYAN} - Beautiful TUI Dashboard           ║${NC}"
echo -e "${CYAN}║                                                                    ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if session already exists
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  TUI session already running${NC}"
    echo ""
    read -p "Kill existing session and restart? (y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Restarting...${NC}"
        tmux kill-session -t "$SESSION_NAME"
    else
        echo -e "${BLUE}Attaching to existing session...${NC}"
        echo -e "${YELLOW}Press Ctrl+B then D to detach${NC}"
        echo ""
        sleep 1
        tmux attach -t "$SESSION_NAME"
        exit 0
    fi
fi

echo -e "${YELLOW}🚀 Launching beautiful dashboard...${NC}"
echo -e "${YELLOW}📁 Working directory: ${SCRIPT_DIR}${NC}"
echo -e "${YELLOW}🎯 Arguments: ${ARGS}${NC}"
echo ""

# Create new tmux session
cd "$SCRIPT_DIR"
tmux new-session -d -s "$SESSION_NAME" -n "COT-Dashboard" "./run_cot_in_tmux_tui.sh $ARGS"

sleep 1

echo -e "${GREEN}✅ Dashboard session created: ${SESSION_NAME}${NC}"
echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  How to View the Dashboard${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Attach to dashboard:[/green]"
echo -e "   ${YELLOW}tmux attach -t $SESSION_NAME${NC}"
echo ""
echo -e "${GREEN}Detach from dashboard (keep it running):[/green]"
echo -e "   ${YELLOW}Press: Ctrl+B, then D${NC}"
echo ""
echo -e "${GREEN}Stop dashboard:[/green]"
echo -e "   ${YELLOW}tmux kill-session -t $SESSION_NAME${NC}"
echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════════════${NC}"
echo ""

read -p "$(echo -e ${YELLOW}Attach to dashboard now? [Y/n]${NC} )" -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo -e "${BLUE}Opening dashboard...${NC}"
    echo ""
    sleep 1
    tmux attach -t "$SESSION_NAME"
else
    echo -e "${GREEN}Dashboard running in background.${NC}"
    echo -e "${YELLOW}View anytime: tmux attach -t $SESSION_NAME${NC}"
    echo ""
fi
