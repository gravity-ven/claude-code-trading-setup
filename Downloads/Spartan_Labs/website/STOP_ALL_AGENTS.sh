#!/bin/bash
##############################################################################
# Stop All Spartan Research Station Agents
##############################################################################

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Stopping all Spartan agents...${NC}"

# Kill all agent processes
pkill -f "master_data_orchestrator.py" 2>/dev/null && echo -e "${GREEN}✅ Master Orchestrator stopped${NC}"
pkill -f "data_integrity_enforcer.py" 2>/dev/null && echo -e "${GREEN}✅ Data Enforcer stopped${NC}"
pkill -f "load_all_data.py" 2>/dev/null && echo -e "${GREEN}✅ Data Loader stopped${NC}"
pkill -f "comprehensive_macro_scanner.py" 2>/dev/null && echo -e "${GREEN}✅ Macro Scanner stopped${NC}"
pkill -f "data_preloader.py" 2>/dev/null && echo -e "${GREEN}✅ Data Preloader stopped${NC}"
pkill -f "data_refresh_scheduler.py" 2>/dev/null && echo -e "${GREEN}✅ Refresh Scheduler stopped${NC}"
pkill -f "start_server.py" 2>/dev/null && echo -e "${GREEN}✅ Web Server stopped${NC}"
pkill -f "complete_data_provider.py" 2>/dev/null && echo -e "${GREEN}✅ Data Provider stopped${NC}"

echo ""
echo -e "${GREEN}All agents stopped.${NC}"
echo -e "${YELLOW}Note: PostgreSQL and Redis are still running.${NC}"