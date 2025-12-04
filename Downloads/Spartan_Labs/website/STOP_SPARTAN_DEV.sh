#!/bin/bash
# STOP_SPARTAN_DEV.sh
# Stop all native development services

echo "========================================================================"
echo "  SPARTAN RESEARCH STATION - STOPPING DEVELOPMENT SERVICES"
echo "========================================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if .pids directory exists
if [ ! -d ".pids" ]; then
    echo -e "${YELLOW}⚠ No .pids directory found${NC}"
    echo "Services may not be running, or were started differently"
    exit 0
fi

# Function to stop a service
stop_service() {
    local name=$1
    local pid_file=$2

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -n "Stopping $name (PID $pid)... "
            kill -15 $pid 2>/dev/null || kill -9 $pid 2>/dev/null

            # Wait up to 5 seconds for graceful shutdown
            for i in {1..5}; do
                if ! ps -p $pid > /dev/null 2>&1; then
                    break
                fi
                sleep 1
            done

            # Force kill if still running
            if ps -p $pid > /dev/null 2>&1; then
                kill -9 $pid 2>/dev/null
            fi

            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${YELLOW}⚠ $name not running (stale PID)${NC}"
        fi
        rm "$pid_file"
    fi
}

# Stop all services
stop_service "Main Server" ".pids/main.pid"
stop_service "Correlation API" ".pids/correlation.pid"
stop_service "Daily Planet API" ".pids/daily_planet.pid"
stop_service "Swing Dashboard API" ".pids/swing.pid"
stop_service "GARP API" ".pids/garp.pid"
stop_service "Data Refresh Scheduler" ".pids/refresh.pid"

# Also kill any processes on our ports (safety net)
echo ""
echo "Checking for stray processes on service ports..."
for port in 8888 5000 5002 5003 5004; do
    pid=$(lsof -ti:$port 2>/dev/null || true)
    if [ ! -z "$pid" ]; then
        echo -n "Killing process on port $port (PID: $pid)... "
        kill -9 $pid 2>/dev/null
        echo -e "${GREEN}✓${NC}"
    fi
done

# Clean up empty .pids directory
if [ -d ".pids" ] && [ -z "$(ls -A .pids)" ]; then
    rmdir .pids
fi

echo ""
echo -e "${GREEN}✓ All development services stopped${NC}"
echo ""
echo "To start again, run: ./START_SPARTAN_DEV.sh"
echo ""
