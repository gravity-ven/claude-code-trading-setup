#!/bin/bash
#
# Launch COT 100 Agents in a new Windows Terminal window
#
# Usage: ./START_COT_AGENTS_TERMINAL.sh [--demo] [--single-cycle]
#

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse arguments
ARGS="$@"

# Default to continuous mode with demo
if [ -z "$ARGS" ]; then
    ARGS="--demo"
fi

# Colors for current terminal
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=====================================================================${NC}"
echo -e "${GREEN}  Spartan 100 COT Agents - Windows Terminal Launcher${NC}"
echo -e "${GREEN}=====================================================================${NC}"
echo ""
echo -e "${YELLOW}Launching COT agents in new Windows Terminal window...${NC}"
echo -e "${YELLOW}Arguments: ${ARGS}${NC}"
echo ""

# Convert WSL path to Windows path for wt.exe
WIN_SCRIPT_DIR=$(wslpath -w "$SCRIPT_DIR")

# Create the command to run in new terminal
# We'll use the run_cot_agents_live.sh script
RUNNER_SCRIPT="${SCRIPT_DIR}/run_cot_agents_live.sh"

# Make sure runner exists
if [ ! -f "$RUNNER_SCRIPT" ]; then
    echo -e "${YELLOW}Creating agent runner script...${NC}"
    cat > "$RUNNER_SCRIPT" <<'EOFRUNNER'
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
EOFRUNNER
    chmod +x "$RUNNER_SCRIPT"
fi

# Launch Windows Terminal with the runner script
# Using wt.exe to open a new tab/window
echo -e "${BLUE}Opening new terminal...${NC}"

# Method 1: Try using wt.exe directly
if command -v wt.exe &> /dev/null; then
    wt.exe -w 0 new-tab --title "Spartan COT Agents" bash -c "cd '$SCRIPT_DIR' && ./run_cot_agents_live.sh $ARGS; exec bash"
    echo -e "${GREEN}✅ Launched in Windows Terminal${NC}"
elif command -v cmd.exe &> /dev/null; then
    # Method 2: Fallback to cmd.exe launching wt
    cmd.exe /c start wt.exe -w 0 new-tab --title "Spartan COT Agents" bash -c "cd '$SCRIPT_DIR' && ./run_cot_agents_live.sh $ARGS; exec bash"
    echo -e "${GREEN}✅ Launched in Windows Terminal (via cmd.exe)${NC}"
else
    echo -e "${RED}❌ Could not find wt.exe or cmd.exe${NC}"
    echo -e "${YELLOW}Falling back to current terminal...${NC}"
    ./run_cot_agents_live.sh $ARGS
fi

echo ""
echo -e "${GREEN}=====================================================================${NC}"
echo -e "${GREEN}  Agent window launched!${NC}"
echo -e "${GREEN}=====================================================================${NC}"
echo ""
echo -e "${BLUE}The COT agents are now running in a separate terminal window.${NC}"
echo ""
echo -e "${YELLOW}To stop the agents:${NC}"
echo -e "  - Press Ctrl+C in the agent terminal window"
echo ""
echo -e "${YELLOW}To view output later:${NC}"
echo -e "  ./view_agent_output.sh"
echo ""
