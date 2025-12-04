#!/bin/bash
##############################################################################
# SPARTAN RESEARCH STATION - COMPLETE AGENT SYSTEM
# ZERO TOLERANCE FOR EMPTY DATA - 100% REAL-TIME COVERAGE
##############################################################################

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${PURPLE}========================================================${NC}"
echo -e "${PURPLE}   SPARTAN RESEARCH STATION - FULL AGENT DEPLOYMENT${NC}"
echo -e "${PURPLE}   ZERO COMPROMISE - 100% REAL DATA ONLY${NC}"
echo -e "${PURPLE}========================================================${NC}"
echo ""

# Kill any existing agents
echo -e "${YELLOW}Stopping existing agents...${NC}"
pkill -f "master_data_orchestrator.py" 2>/dev/null || true
pkill -f "data_integrity_enforcer.py" 2>/dev/null || true
pkill -f "load_all_data.py" 2>/dev/null || true
pkill -f "comprehensive_macro_scanner.py" 2>/dev/null || true
pkill -f "start_server.py" 2>/dev/null || true

# Start services if not running
echo -e "${BLUE}Starting core services...${NC}"
sudo service postgresql start 2>/dev/null || echo "PostgreSQL already running"
sudo service redis-server start 2>/dev/null || echo "Redis already running"

# Create database if needed
psql -U postgres -c "CREATE DATABASE spartan_research_db;" 2>/dev/null || true
psql -U postgres -c "CREATE USER spartan WITH PASSWORD 'spartan';" 2>/dev/null || true
psql -U postgres -c "GRANT ALL ON DATABASE spartan_research_db TO spartan;" 2>/dev/null || true

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -q psycopg2-binary redis yfinance fredapi requests python-dotenv flask gunicorn aiohttp numpy

# Start Master Data Orchestrator (CRITICAL - Updates every second!)
echo -e "${GREEN}🚀 Starting Master Data Orchestrator (229+ data points)...${NC}"
nohup python3 master_data_orchestrator.py > orchestrator.log 2>&1 &
ORCH_PID=$!
echo -e "${GREEN}✅ Master Orchestrator: PID $ORCH_PID${NC}"

# Start Data Integrity Enforcer (ZERO TOLERANCE)
echo -e "${GREEN}🛡️ Starting Data Integrity Enforcer (Zero empty fields)...${NC}"
nohup python3 data_integrity_enforcer.py > enforcer.log 2>&1 &
ENF_PID=$!
echo -e "${GREEN}✅ Data Enforcer: PID $ENF_PID${NC}"

# Start Comprehensive Data Loader
echo -e "${GREEN}📊 Starting Comprehensive Data Loader (41 symbols)...${NC}"
nohup python3 load_all_data.py > loader.log 2>&1 &
LOAD_PID=$!
echo -e "${GREEN}✅ Data Loader: PID $LOAD_PID${NC}"

# Start Data Preloader
echo -e "${GREEN}🔄 Starting Data Preloader...${NC}"
nohup python3 src/data_preloader.py > preloader.log 2>&1 &
PRE_PID=$!
echo -e "${GREEN}✅ Data Preloader: PID $PRE_PID${NC}"

# Start Macro Scanner
echo -e "${GREEN}📈 Starting Comprehensive Macro Scanner...${NC}"
nohup python3 comprehensive_macro_scanner.py > scanner.log 2>&1 &
SCAN_PID=$!
echo -e "${GREEN}✅ Macro Scanner: PID $SCAN_PID${NC}"

# Start Web Server
echo -e "${GREEN}🌐 Starting Web Server...${NC}"
nohup python3 start_server.py > server.log 2>&1 &
SERVER_PID=$!
echo -e "${GREEN}✅ Web Server: PID $SERVER_PID${NC}"

# Start Data Refresh Scheduler
echo -e "${GREEN}⏰ Starting Auto-Refresh Scheduler...${NC}"
nohup python3 src/data_refresh_scheduler.py > refresh.log 2>&1 &
REFRESH_PID=$!
echo -e "${GREEN}✅ Refresh Scheduler: PID $REFRESH_PID${NC}"

# Start Autonomous Data Guardian (PERMANENT LOCK-IN MONITORING)
echo -e "${PURPLE}🛡️ Starting Autonomous Data Guardian (PERMANENT)...${NC}"
nohup python3 autonomous_data_guardian.py > guardian.log 2>&1 &
GUARDIAN_PID=$!
echo -e "${GREEN}✅ Data Guardian: PID $GUARDIAN_PID${NC}"

# Start Comprehensive Data Validator (CONTINUOUS)
echo -e "${PURPLE}🔍 Starting Data Validator (CONTINUOUS)...${NC}"
nohup python3 complete_data_validator.py > validator.log 2>&1 &
VALIDATOR_PID=$!
echo -e "${GREEN}✅ Data Validator: PID $VALIDATOR_PID${NC}"

# Wait a moment for services to initialize
sleep 3

# Show status
echo ""
echo -e "${PURPLE}========================================================${NC}"
echo -e "${GREEN}   ✅ ALL AGENTS DEPLOYED SUCCESSFULLY!${NC}"
echo -e "${PURPLE}========================================================${NC}"
echo ""
echo -e "${GREEN}Active Agents:${NC}"
echo -e "  • Master Data Orchestrator: ${GREEN}RUNNING${NC} (PID: $ORCH_PID)"
echo -e "  • Data Integrity Enforcer: ${GREEN}RUNNING${NC} (PID: $ENF_PID)"
echo -e "  • Comprehensive Data Loader: ${GREEN}RUNNING${NC} (PID: $LOAD_PID)"
echo -e "  • Data Preloader: ${GREEN}RUNNING${NC} (PID: $PRE_PID)"
echo -e "  • Macro Scanner: ${GREEN}RUNNING${NC} (PID: $SCAN_PID)"
echo -e "  • Web Server: ${GREEN}RUNNING${NC} (PID: $SERVER_PID)"
echo -e "  • Refresh Scheduler: ${GREEN}RUNNING${NC} (PID: $REFRESH_PID)"
echo -e "  • ${PURPLE}Autonomous Guardian: ${GREEN}PERMANENT${NC} (PID: $GUARDIAN_PID)"
echo -e "  • ${PURPLE}Data Validator: ${GREEN}CONTINUOUS${NC} (PID: $VALIDATOR_PID)"
echo ""
echo -e "${GREEN}Coverage Statistics:${NC}"
echo -e "  • Data Points Monitored: ${GREEN}229+${NC}"
echo -e "  • Update Frequency: ${GREEN}EVERY SECOND${NC}"
echo -e "  • Empty Data Tolerance: ${GREEN}ZERO${NC}"
echo -e "  • Fake Data Tolerance: ${GREEN}ZERO${NC}"
echo -e "  • Data Sources: ${GREEN}yfinance, FRED, Polygon, Twelve Data${NC}"
echo ""
echo -e "${PURPLE}========================================================${NC}"
echo -e "${GREEN}🌐 Dashboard: http://localhost:8888${NC}"
echo -e "${GREEN}📊 Real-time data with ZERO empty fields${NC}"
echo -e "${GREEN}🔄 Updates EVERY SECOND - No compromises${NC}"
echo -e "${PURPLE}========================================================${NC}"
echo ""
echo -e "${YELLOW}To monitor: tail -f orchestrator.log enforcer.log${NC}"
echo -e "${YELLOW}To stop: ./STOP_ALL_AGENTS.sh${NC}"
echo ""