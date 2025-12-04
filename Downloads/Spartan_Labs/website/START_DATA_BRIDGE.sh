#!/usr/bin/env bash

##############################################################################
# Start Spartan Data Bridge - Claude Code Integration
# Starts the complete data validation and autonomous fixing system
# NO FAKE DATA - Only genuine data monitoring and fixes
##############################################################################

set -e

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
   ____  _  _____  _      ____  ____  ____  ____  ____  _____
  / ___\/ \/ __  \/ \  /|/ ___\/ ___\/  __\/  __\/  __\/  __/
  |    \| ||  \/||| |  ||| ___/|    \|  \/||  \/||  \/||  |
  \___ || ||  __/| |  ||| |   | |   ||    /|  \/||  __/|  |__
  \____/\_/\_/   \_/  \|\_/   \_|___/\_/\_\\_/\_\\_/   \____\

         DATA VALIDATION + CLAUDE CODE BRIDGE
            🛡️  Autonomous Data Healing
EOF
echo -e "${NC}"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${CYAN}📂 Working Directory: ${GREEN}$SCRIPT_DIR${NC}"
echo ""

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker daemon not running${NC}"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

echo -e "${GREEN}✅ Docker daemon running${NC}"

# Check if Claude Code is installed
CLAUDE_AVAILABLE=false
if command -v claude &> /dev/null; then
    echo -e "${GREEN}✅ Claude Code installed${NC}"
    CLAUDE_AVAILABLE=true
else
    echo -e "${YELLOW}⚠️  Claude Code not found (install from: https://claude.ai/download)${NC}"
    echo -e "${CYAN}   System will monitor but cannot auto-launch Claude Code${NC}"
fi

echo ""
echo -e "${BLUE}🚀 Starting Data Validation Bridge...${NC}"
echo ""

# Start data validator container
echo -e "${CYAN}📊 Starting data validation monitor...${NC}"

if docker-compose ps | grep -q spartan-data-validator; then
    echo -e "${YELLOW}⚠️  Data validator already running, restarting...${NC}"
    docker-compose restart spartan-data-validator
else
    echo -e "${GREEN}▶️  Starting data validator container...${NC}"
    docker-compose up -d spartan-data-validator
fi

echo ""
echo -e "${GREEN}✅ Data validator started${NC}"

# Create logs directory if it doesn't exist
mkdir -p logs

# Start Claude Code watcher (if Claude is available)
if [ "$CLAUDE_AVAILABLE" = true ]; then
    echo ""
    echo -e "${CYAN}🤖 Starting Claude Code watcher...${NC}"

    # Check if watcher is already running
    if [ -f logs/claude_data_watcher.pid ]; then
        OLD_PID=$(cat logs/claude_data_watcher.pid)
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  Claude watcher already running (PID: $OLD_PID)${NC}"
        else
            # Start watcher in background
            nohup ./logs/claude_data_watcher.sh > logs/claude_data_watcher.log 2>&1 &
            WATCHER_PID=$!
            echo -e "${GREEN}✅ Claude watcher started (PID: $WATCHER_PID)${NC}"
        fi
    else
        # Start watcher in background
        nohup ./logs/claude_data_watcher.sh > logs/claude_data_watcher.log 2>&1 &
        WATCHER_PID=$!
        echo -e "${GREEN}✅ Claude watcher started (PID: $WATCHER_PID)${NC}"
    fi
fi

echo ""
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 Data Validation Bridge is ACTIVE!${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${CYAN}📊 Monitoring:${NC}"
echo -e "   ${GREEN}✓${NC} Redis cache data freshness"
echo -e "   ${GREEN}✓${NC} PostgreSQL data availability"
echo -e "   ${GREEN}✓${NC} Critical data sources"
echo -e "   ${GREEN}✓${NC} Auto-trigger Claude Code on failures"
echo ""

echo -e "${CYAN}🔍 API Endpoints:${NC}"
echo -e "   ${GREEN}Health Summary:${NC}    curl http://localhost:8888/api/health/data/summary"
echo -e "   ${GREEN}Full Report:${NC}       curl http://localhost:8888/api/health/data"
echo -e "   ${GREEN}Redis Status:${NC}      curl http://localhost:8888/api/health/data/redis"
echo -e "   ${GREEN}PostgreSQL:${NC}        curl http://localhost:8888/api/health/data/postgres"
echo -e "   ${GREEN}Bridge Status:${NC}     curl http://localhost:8888/api/health/data/claude-bridge"
echo -e "   ${GREEN}Manual Trigger:${NC}    curl -X POST http://localhost:8888/api/health/data/trigger-claude"
echo ""

echo -e "${CYAN}📝 Logs:${NC}"
echo -e "   ${GREEN}Monitor Logs:${NC}      tail -f logs/data_validation_monitor.log"
echo -e "   ${GREEN}Watcher Logs:${NC}      tail -f logs/claude_data_watcher.log"
echo -e "   ${GREEN}Latest Status:${NC}     cat logs/data_validation_latest.json | jq"
echo ""

echo -e "${CYAN}🛠️  Commands:${NC}"
echo -e "   ${YELLOW}View status:${NC}       docker-compose logs -f spartan-data-validator"
echo -e "   ${YELLOW}Stop bridge:${NC}       docker-compose stop spartan-data-validator"
echo -e "   ${YELLOW}Restart:${NC}           docker-compose restart spartan-data-validator"
echo -e "   ${YELLOW}Manual trigger:${NC}    ./logs/trigger_claude_data_fix.sh"
echo ""

echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}🚀 System monitoring... Data failures will auto-trigger Claude Code!${NC}"
echo ""

# Optionally follow logs
echo -e "${YELLOW}Press Ctrl+C to exit log view (monitoring continues in background)${NC}"
echo -e "${YELLOW}Following validator logs...${NC}"
echo ""

sleep 2
docker-compose logs -f spartan-data-validator
