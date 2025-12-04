#!/bin/bash
##############################################################################
# Stop Spartan Research Station - Native Mode
##############################################################################

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Stopping Spartan Research Station...${NC}"

# Kill Python processes
pkill -f "start_server.py" 2>/dev/null && echo -e "${GREEN}✅ Web server stopped${NC}"
pkill -f "load_all_data.py" 2>/dev/null && echo -e "${GREEN}✅ Data loader stopped${NC}"
pkill -f "data_preloader.py" 2>/dev/null && echo -e "${GREEN}✅ Data preloader stopped${NC}"
pkill -f "data_refresh_scheduler.py" 2>/dev/null && echo -e "${GREEN}✅ Refresh scheduler stopped${NC}"
pkill -f "comprehensive_macro_scanner.py" 2>/dev/null && echo -e "${GREEN}✅ Macro scanner stopped${NC}"
pkill -f "complete_data_provider.py" 2>/dev/null && echo -e "${GREEN}✅ Data provider stopped${NC}"

echo ""
echo -e "${GREEN}All services stopped.${NC}"
echo -e "${YELLOW}Note: PostgreSQL and Redis are still running for other applications.${NC}"
echo -e "${YELLOW}To stop them: sudo service postgresql stop && sudo service redis-server stop${NC}"