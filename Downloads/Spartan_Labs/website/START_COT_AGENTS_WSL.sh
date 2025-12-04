#!/bin/bash
#
# Launch COT Agents in tmux session (WSL2-native)
# Perfect for WSL2 - no Windows Terminal or X server needed!
#
# Usage: ./START_COT_AGENTS_WSL.sh [--demo] [--single-cycle]
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SESSION_NAME="spartan-cot-agents"
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
echo -e "${CYAN}║        ${GREEN}SPARTAN 100 COT AGENTS${CYAN} - WSL2 Tmux Launcher         ║${NC}"
echo -e "${CYAN}║                                                                    ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if session already exists
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Session '$SESSION_NAME' already running${NC}"
    echo ""
    echo -e "${BLUE}Options:${NC}"
    echo -e "  1. ${GREEN}Attach to existing session:${NC}"
    echo -e "     tmux attach -t $SESSION_NAME"
    echo ""
    echo -e "  2. ${RED}Kill and restart:${NC}"
    echo -e "     tmux kill-session -t $SESSION_NAME"
    echo -e "     ./START_COT_AGENTS_WSL.sh $ARGS"
    echo ""
    read -p "Kill existing session and restart? (y/N) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Killing existing session...${NC}"
        tmux kill-session -t "$SESSION_NAME"
    else
        echo -e "${BLUE}Attaching to existing session...${NC}"
        echo -e "${YELLOW}Press Ctrl+B then D to detach${NC}"
        echo ""
        sleep 2
        tmux attach -t "$SESSION_NAME"
        exit 0
    fi
fi

echo -e "${YELLOW}🚀 Launching agents in tmux session: ${SESSION_NAME}${NC}"
echo -e "${YELLOW}📁 Working directory: ${SCRIPT_DIR}${NC}"
echo -e "${YELLOW}🎯 Arguments: ${ARGS}${NC}"
echo ""

# Create new tmux session in detached mode
cd "$SCRIPT_DIR"

# Use the runner script for cleaner execution
tmux new-session -d -s "$SESSION_NAME" -n "COT-Agents" "./run_cot_in_tmux.sh $ARGS"

sleep 1

echo -e "${GREEN}✅ Tmux session created: ${SESSION_NAME}${NC}"
echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  How to View Agent Output${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}1. Attach to session (view live output):${NC}"
echo -e "   ${YELLOW}tmux attach -t $SESSION_NAME${NC}"
echo ""
echo -e "${GREEN}2. Detach from session (while keeping it running):${NC}"
echo -e "   ${YELLOW}Press: Ctrl+B, then press D${NC}"
echo ""
echo -e "${GREEN}3. View all tmux sessions:${NC}"
echo -e "   ${YELLOW}tmux ls${NC}"
echo ""
echo -e "${GREEN}4. Kill session (stop agents):${NC}"
echo -e "   ${YELLOW}tmux kill-session -t $SESSION_NAME${NC}"
echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}💡 Quick Tip:${NC}"
echo -e "   The agents are running in the background now."
echo -e "   Attach to see live output, detach to return here."
echo ""
read -p "$(echo -e ${YELLOW}Attach to session now? [Y/n]${NC} )" -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo -e "${BLUE}Attaching to session...${NC}"
    echo -e "${YELLOW}Press Ctrl+B then D to detach${NC}"
    echo ""
    sleep 1
    tmux attach -t "$SESSION_NAME"
else
    echo -e "${GREEN}Session running in background.${NC}"
    echo -e "${YELLOW}Attach anytime with: tmux attach -t $SESSION_NAME${NC}"
    echo ""
fi
