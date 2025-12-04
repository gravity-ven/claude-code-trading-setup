#!/bin/bash
#
# Launch COT 100 Agents in Alacritty terminal (if installed)
# Alternative launcher for Alacritty users
#
# Usage: ./START_COT_AGENTS_ALACRITTY.sh [--demo] [--single-cycle]
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

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=====================================================================${NC}"
echo -e "${GREEN}  Spartan 100 COT Agents - Alacritty Launcher${NC}"
echo -e "${GREEN}=====================================================================${NC}"
echo ""

# Check if Alacritty is installed
if ! command -v alacritty &> /dev/null; then
    echo -e "${RED}❌ Alacritty not found${NC}"
    echo ""
    echo -e "${YELLOW}To install Alacritty:${NC}"
    echo ""
    echo -e "${BLUE}On Windows (download from):${NC}"
    echo "  https://github.com/alacritty/alacritty/releases"
    echo ""
    echo -e "${BLUE}On Linux/WSL (if using X server):${NC}"
    echo "  cargo install alacritty"
    echo "  # OR"
    echo "  sudo apt install alacritty"
    echo ""
    echo -e "${YELLOW}Alternative: Use Windows Terminal launcher instead:${NC}"
    echo "  ./START_COT_AGENTS_TERMINAL.sh $ARGS"
    echo ""
    exit 1
fi

echo -e "${YELLOW}Launching COT agents in new Alacritty window...${NC}"
echo -e "${YELLOW}Arguments: ${ARGS}${NC}"
echo ""

# Create runner script if it doesn't exist
RUNNER_SCRIPT="${SCRIPT_DIR}/run_cot_agents_live.sh"
if [ ! -f "$RUNNER_SCRIPT" ]; then
    echo -e "${YELLOW}Creating agent runner script...${NC}"
    cat > "$RUNNER_SCRIPT" <<'EOFRUNNER'
#!/bin/bash
#
# COT Agents Live Output Runner
#

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

clear

echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║        ${GREEN}SPARTAN 100 COT AGENTS${CYAN} - Live Output Monitor         ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}🤖 Starting autonomous agent system...${NC}"
echo -e "${BLUE}⏰ Started at: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""

cd "$SCRIPT_DIR"
python3 -u run_100_agents.py "$@"

echo ""
echo -e "${GREEN}✅ Agent execution completed${NC}"
echo -e "${YELLOW}Press Enter to close...${NC}"
read
EOFRUNNER
    chmod +x "$RUNNER_SCRIPT"
fi

# Launch Alacritty with the runner
alacritty \
    --title "Spartan COT Agents" \
    -e bash -c "cd '$SCRIPT_DIR' && ./run_cot_agents_live.sh $ARGS" &

echo -e "${GREEN}✅ Launched in Alacritty${NC}"
echo ""
echo -e "${GREEN}=====================================================================${NC}"
echo -e "${GREEN}  Agent window launched!${NC}"
echo -e "${GREEN}=====================================================================${NC}"
echo ""
