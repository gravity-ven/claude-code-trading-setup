#!/bin/bash
#
# Launch Spartan COT Agents - Live TUI Dashboard
#
# REAL DATA ONLY - No fake/simulated data allowed
#
# This runs directly in your terminal with real-time updates
# No tmux required - pure Rich library live display
#
# Usage:
#   ./START_LIVE_TUI.sh              # Run all 100 agents (production)
#   ./START_LIVE_TUI.sh --demo       # Run 4 agents (demo mode)
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

echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                                    ║${NC}"
echo -e "${CYAN}║        ${GREEN}SPARTAN COT AGENTS${CYAN} - Live TUI Dashboard               ║${NC}"
echo -e "${CYAN}║                                                                    ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}🚀 Launching live dashboard with real-time updates...${NC}"
echo -e "${YELLOW}📊 Press Ctrl+C to exit${NC}"
echo ""
sleep 2

# Run the ASCII TUI (no Unicode encoding issues)
python3 run_cot_ascii_tui.py "$@"
