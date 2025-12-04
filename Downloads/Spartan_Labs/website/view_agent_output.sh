#!/bin/bash
#
# View Spartan 100 Agents live output
#
# Usage: ./view_agent_output.sh
#

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/logs/agents.log"

echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}  Spartan 100 Agents - Live Output Viewer${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""
echo -e "${YELLOW}Watching: ${LOG_FILE}${NC}"
echo -e "${YELLOW}Press Ctrl+C to exit${NC}"
echo ""
echo -e "${GREEN}======================================================================${NC}"
echo ""

# Check if log file exists
if [ ! -f "${LOG_FILE}" ]; then
    echo -e "${RED}❌ Log file not found: ${LOG_FILE}${NC}"
    echo ""
    echo "Agents may not be running. Start them with:"
    echo "  sudo systemctl start spartan_agents"
    echo ""
    echo "Or run manually:"
    echo "  python3 run_100_agents.py --demo"
    exit 1
fi

# Follow log file
tail -f "${LOG_FILE}"
