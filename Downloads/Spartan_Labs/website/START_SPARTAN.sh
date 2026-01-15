#!/usr/bin/env bash

##############################################################################
# Spartan Labs Research Station - Universal Startup Script
# Works on: macOS, Linux, Windows WSL
# Starts: All services via unified_startup.py
##############################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Banner
echo -e "${PURPLE}"
cat << "EOF"
   _____ ____  ___    ____  _________    _   __
  / ___// __ \/   |  / __ \/_  __/   |  / | / /
  \__ \/ /_/ / /| | / /_/ / / / / /| | /  |/ /
 ___/ / ____/ ___ |/ _, _/ / / / ___ |/ /|  /
/____/_/   /_/  |_/_/ |_| /_/ /_/  |_/_/ |_/

         RESEARCH STATION v2.0
           Native Python Mode
EOF
echo -e "${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${CYAN}Working Directory: ${GREEN}$SCRIPT_DIR${NC}"
echo ""

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macOS"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if grep -qi microsoft /proc/version 2>/dev/null; then
            echo "WSL"
        else
            echo "Linux"
        fi
    else
        echo "Unknown"
    fi
}

OS=$(detect_os)
echo -e "${CYAN}OS: ${GREEN}$OS${NC}"

# Find Python - prefer conda spartan env, then venv, then system
PYTHON=""

# Check for conda spartan environment
if [ -n "$CONDA_PREFIX" ]; then
    PYTHON="$CONDA_PREFIX/bin/python"
    echo -e "${GREEN}Using conda environment: $CONDA_PREFIX${NC}"
elif [ -f "/home/spartan/miniconda3/envs/spartan/bin/python" ]; then
    # Activate conda spartan environment
    source /home/spartan/miniconda3/etc/profile.d/conda.sh 2>/dev/null
    conda activate spartan 2>/dev/null
    PYTHON="/home/spartan/miniconda3/envs/spartan/bin/python"
    echo -e "${GREEN}Activated conda spartan environment${NC}"
elif [ -f "venv/bin/python" ]; then
    source venv/bin/activate
    PYTHON="venv/bin/python"
    echo -e "${GREEN}Using venv${NC}"
elif command -v python3 &> /dev/null; then
    PYTHON="python3"
    echo -e "${YELLOW}Using system Python${NC}"
else
    echo -e "${RED}Python not found!${NC}"
    exit 1
fi

echo -e "${CYAN}Python: ${GREEN}$PYTHON${NC}"
echo ""

# Check infrastructure
echo -e "${BLUE}[Infrastructure Check]${NC}"

# Check PostgreSQL
if pg_isready -h localhost >/dev/null 2>&1; then
    echo -e "  ${GREEN}PostgreSQL: Running${NC}"
else
    echo -e "  ${YELLOW}PostgreSQL: Not running${NC}"
    echo -e "  ${CYAN}  Try: sudo service postgresql start${NC}"
fi

# Check Redis
if redis-cli ping >/dev/null 2>&1; then
    echo -e "  ${GREEN}Redis: Running${NC}"
else
    echo -e "  ${YELLOW}Redis: Not running${NC}"
    echo -e "  ${CYAN}  Try: sudo service redis-server start${NC}"
fi

echo ""

# Create logs directory
mkdir -p logs

# Start unified startup manager
echo -e "${BLUE}[Starting Services]${NC}"
echo ""

$PYTHON unified_startup.py

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}All services started successfully!${NC}"
    echo ""
    echo -e "${CYAN}Quick Commands:${NC}"
    echo -e "  Status:  ${YELLOW}python unified_startup.py --status${NC}"
    echo -e "  Stop:    ${YELLOW}python unified_startup.py --stop${NC}"
    echo -e "  Restart: ${YELLOW}python unified_startup.py --restart${NC}"
    echo ""
    echo -e "${CYAN}Dashboard: ${GREEN}http://localhost:8888${NC}"
else
    echo ""
    echo -e "${YELLOW}Some services may have failed. Check logs:${NC}"
    echo -e "  ${CYAN}ls -la logs/*.log${NC}"
fi
