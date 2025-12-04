#!/usr/bin/env bash

##############################################################################
# Spartan Labs Research Station - Shutdown Script
# Stops all services, monitor, and Claude Code integration
##############################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🛑 Stopping Spartan Research Station...${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Stop alert watcher if running
if [ -f "$SCRIPT_DIR/logs/alert_watcher.pid" ]; then
    WATCHER_PID=$(cat "$SCRIPT_DIR/logs/alert_watcher.pid")
    if ps -p "$WATCHER_PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping alert watcher (PID: $WATCHER_PID)...${NC}"
        kill "$WATCHER_PID" 2>/dev/null || true
        rm -f "$SCRIPT_DIR/logs/alert_watcher.pid"
        echo -e "${GREEN}✅ Alert watcher stopped${NC}"
    fi
fi

# Stop Docker services
echo -e "${YELLOW}Stopping Docker services...${NC}"

if docker compose version &> /dev/null; then
    docker compose down
else
    docker-compose down
fi

echo ""
echo -e "${GREEN}✅ All services stopped${NC}"
echo ""
echo -e "${BLUE}Service status:${NC}"

# Check if containers are stopped
if ! docker ps --format '{{.Names}}' | grep -q "spartan-"; then
    echo -e "  ${GREEN}✅ No Spartan containers running${NC}"
else
    echo -e "  ${YELLOW}⚠️  Some containers still running:${NC}"
    docker ps --format '{{.Names}}' | grep "spartan-" | while read -r container; do
        echo -e "     - $container"
    done
fi

echo ""
echo -e "${CYAN}💡 To restart: ./START_SPARTAN.sh${NC}"
echo ""
