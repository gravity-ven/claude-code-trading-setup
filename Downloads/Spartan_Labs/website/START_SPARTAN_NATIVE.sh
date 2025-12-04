#!/bin/bash
##############################################################################
# Spartan Research Station - Native Startup (NO DOCKER!)
# High-performance, real-time market data with native services
##############################################################################

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}   SPARTAN RESEARCH STATION - NATIVE MODE${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""

# Step 1: Start PostgreSQL and Redis
echo -e "${BLUE}Starting database services...${NC}"
sudo service postgresql start 2>/dev/null || echo "PostgreSQL already running"
sudo service redis-server start 2>/dev/null || echo "Redis already running"

# Step 2: Check services
echo -e "${BLUE}Checking services...${NC}"
pg_isready -q && echo -e "${GREEN}✅ PostgreSQL is running${NC}" || echo -e "${RED}❌ PostgreSQL not running${NC}"
redis-cli ping > /dev/null 2>&1 && echo -e "${GREEN}✅ Redis is running${NC}" || echo -e "${RED}❌ Redis not running${NC}"

# Step 3: Create database if needed
echo -e "${BLUE}Setting up database...${NC}"
psql -U postgres -c "CREATE DATABASE spartan_research_db;" 2>/dev/null || echo "Database already exists"
psql -U postgres -c "CREATE USER spartan WITH PASSWORD 'spartan';" 2>/dev/null || echo "User already exists"
psql -U postgres -c "GRANT ALL ON DATABASE spartan_research_db TO spartan;" 2>/dev/null || echo "Permissions already granted"

# Step 4: Install Python dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
pip install -q psycopg2-binary redis yfinance fredapi requests python-dotenv flask gunicorn

# Step 5: Start data loader in background
echo -e "${BLUE}Starting comprehensive data loader...${NC}"
pkill -f "load_all_data.py" 2>/dev/null || true
nohup python3 load_all_data.py > /dev/null 2>&1 &
echo -e "${GREEN}✅ Data loader started (PID: $!)${NC}"

# Step 6: Start data preloader
echo -e "${BLUE}Loading market data...${NC}"
python3 src/data_preloader.py &
PRELOADER_PID=$!
echo -e "${GREEN}✅ Data preloader started (PID: $PRELOADER_PID)${NC}"

# Step 7: Start web server
echo -e "${BLUE}Starting web server...${NC}"
pkill -f "start_server.py" 2>/dev/null || true
nohup python3 start_server.py > server.log 2>&1 &
SERVER_PID=$!
echo -e "${GREEN}✅ Web server started (PID: $SERVER_PID)${NC}"

# Step 8: Start data refresh scheduler
echo -e "${BLUE}Starting auto-refresh scheduler...${NC}"
pkill -f "data_refresh_scheduler.py" 2>/dev/null || true
nohup python3 src/data_refresh_scheduler.py > /dev/null 2>&1 &
echo -e "${GREEN}✅ Auto-refresh started (PID: $!)${NC}"

# Step 9: Start comprehensive scanner
echo -e "${BLUE}Starting comprehensive macro scanner...${NC}"
pkill -f "comprehensive_macro_scanner.py" 2>/dev/null || true
nohup python3 comprehensive_macro_scanner.py > /dev/null 2>&1 &
echo -e "${GREEN}✅ Macro scanner started (PID: $!)${NC}"

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}   SPARTAN RESEARCH STATION IS READY!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${GREEN}🌐 Dashboard: http://localhost:8888${NC}"
echo -e "${GREEN}📊 Real-time market data with visualizations${NC}"
echo -e "${GREEN}🔄 Auto-refresh every 5 minutes${NC}"
echo ""
echo -e "${YELLOW}To stop all services, run: ./STOP_SPARTAN_NATIVE.sh${NC}"
echo ""