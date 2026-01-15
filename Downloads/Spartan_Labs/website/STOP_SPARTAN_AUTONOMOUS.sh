#!/bin/bash
##############################################################################
# STOP SPARTAN AUTONOMOUS SYSTEM
# Gracefully stops all services and monitoring
##############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Stopping Spartan Autonomous Research Station...${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Function to stop a service
stop_service() {
    local name=$1
    local pid_file=".pids/${name}.pid"

    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo -n "   Stopping $name (PID $pid)... "
            kill -9 "$pid" 2>/dev/null
            rm -f "$pid_file"
            echo -e "${GREEN}✓${NC}"
        else
            echo -n "   $name (PID $pid not running)... "
            rm -f "$pid_file"
            echo -e "${YELLOW}⚠${NC}"
        fi
    else
        echo -n "   $name... "
        echo -e "${YELLOW}⚠ Not found${NC}"
    fi
}

# Stop all services
stop_service "main"
stop_service "correlation"
stop_service "daily_planet"
stop_service "swing"
stop_service "garp"
stop_service "cot_scanner"
stop_service "oi_scanner"
stop_service "refresh"
stop_service "monitor"
stop_service "claude_watcher"

# Kill any remaining processes on our ports
echo ""
echo "Clearing ports..."
for port in 8888 5000 5002 5003 5004 5009 5010; do
    pid=$(lsof -ti:$port 2>/dev/null || true)
    if [ ! -z "$pid" ]; then
        echo "   Port $port (PID $pid)... "
        kill -9 $pid 2>/dev/null || true
        echo -e "${GREEN}   ✓ Cleared${NC}"
    fi
done

echo ""
echo -e "${GREEN}✅ All services stopped${NC}"
echo ""
echo -e "${CYAN}To restart: ./START_SPARTAN_AUTONOMOUS.sh${NC}"
echo ""
