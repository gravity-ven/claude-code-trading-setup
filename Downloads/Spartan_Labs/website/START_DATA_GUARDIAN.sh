#!/bin/bash

##############################################################################
# START DATA GUARDIAN AGENT
#
# Launches the autonomous Data Guardian Agent that continuously monitors
# multiple data sources for genuine market data
#
# Usage:
#   ./START_DATA_GUARDIAN.sh           # Run in foreground
#   ./START_DATA_GUARDIAN.sh bg        # Run in background
##############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}══════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   DATA GUARDIAN AGENT - Spartan Research Station${NC}"
echo -e "${BLUE}══════════════════════════════════════════════════════════════════${NC}"

# Check if PostgreSQL is running
echo -e "\n${YELLOW}Checking PostgreSQL...${NC}"
if ! sudo service postgresql status >/dev/null 2>&1; then
    echo -e "${YELLOW}Starting PostgreSQL...${NC}"
    sudo service postgresql start
fi
echo -e "${GREEN}✓ PostgreSQL is running${NC}"

# Check if Redis is running
echo -e "\n${YELLOW}Checking Redis...${NC}"
if ! redis-cli ping >/dev/null 2>&1; then
    echo -e "${YELLOW}Starting Redis...${NC}"
    sudo service redis-server start
fi
echo -e "${GREEN}✓ Redis is running${NC}"

# Check Python dependencies
echo -e "\n${YELLOW}Checking Python dependencies...${NC}"
if ! python3 -c "import redis, psycopg2, yfinance" 2>/dev/null; then
    echo -e "${YELLOW}Installing missing dependencies...${NC}"
    pip install redis psycopg2-binary yfinance python-dotenv requests
fi
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Check .env file
if [ ! -f .env ]; then
    echo -e "\n${YELLOW}⚠️  No .env file found${NC}"
    echo -e "${YELLOW}Creating .env from example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
    echo -e "${YELLOW}⚠️  Please add your API keys to .env for better coverage:${NC}"
    echo -e "   - FRED_API_KEY (economic data)"
    echo -e "   - POLYGON_IO_API_KEY (market data backup)"
    echo -e "   - ALPHA_VANTAGE_API_KEY (market data backup)"
fi

# Display configuration
echo -e "\n${BLUE}Configuration:${NC}"
echo -e "   Working Directory: ${SCRIPT_DIR}"
echo -e "   Log File: data_guardian.log"
echo -e "   Scan Interval: 15 minutes"
echo -e "   Data Sources: 7 (yfinance, polygon, alpha_vantage, twelve_data, finnhub, coingecko, fred)"

# Check if already running
if [ -f data_guardian.pid ]; then
    PID=$(cat data_guardian.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "\n${RED}❌ Data Guardian Agent is already running (PID: $PID)${NC}"
        echo -e "${YELLOW}To stop it, run: kill $PID${NC}"
        exit 1
    else
        # Stale PID file
        rm data_guardian.pid
    fi
fi

# Run mode
if [ "$1" == "bg" ] || [ "$1" == "background" ]; then
    echo -e "\n${BLUE}Starting Data Guardian Agent in BACKGROUND mode...${NC}"
    nohup python3 data_guardian_agent.py > data_guardian_output.log 2>&1 &
    AGENT_PID=$!
    echo $AGENT_PID > data_guardian.pid
    echo -e "${GREEN}✅ Data Guardian Agent started (PID: $AGENT_PID)${NC}"
    echo -e "\n${YELLOW}Monitor logs:${NC}"
    echo -e "   tail -f data_guardian.log"
    echo -e "   tail -f data_guardian_output.log"
    echo -e "\n${YELLOW}To stop:${NC}"
    echo -e "   kill $AGENT_PID"
    echo -e "   # or"
    echo -e "   ./STOP_DATA_GUARDIAN.sh"
else
    echo -e "\n${BLUE}Starting Data Guardian Agent in FOREGROUND mode...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}\n"
    python3 data_guardian_agent.py
fi
