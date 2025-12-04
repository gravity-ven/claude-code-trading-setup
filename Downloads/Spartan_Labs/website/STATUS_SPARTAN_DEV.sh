#!/bin/bash
# STATUS_SPARTAN_DEV.sh
# Check status of all native development services

echo "========================================================================"
echo "  SPARTAN RESEARCH STATION - SERVICE STATUS"
echo "========================================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to check service status
check_service() {
    local name=$1
    local pid_file=$2
    local port=$3
    local health_url=$4

    echo -n "$name: "

    # Check if PID file exists
    if [ ! -f "$pid_file" ]; then
        echo -e "${RED}NOT RUNNING (no PID file)${NC}"
        return
    fi

    # Check if process is running
    local pid=$(cat "$pid_file")
    if ! ps -p $pid > /dev/null 2>&1; then
        echo -e "${RED}NOT RUNNING (stale PID)${NC}"
        return
    fi

    # Check if port is listening
    if ! lsof -ti:$port > /dev/null 2>&1; then
        echo -e "${YELLOW}RUNNING (PID $pid) but not listening on port $port${NC}"
        return
    fi

    # Check health endpoint if provided
    if [ ! -z "$health_url" ]; then
        if curl -sf "$health_url" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ HEALTHY (PID $pid, port $port)${NC}"
        else
            echo -e "${YELLOW}⚠ RUNNING (PID $pid) but health check failed${NC}"
        fi
    else
        echo -e "${GREEN}✓ RUNNING (PID $pid, port $port)${NC}"
    fi
}

# Check infrastructure
echo "Infrastructure:"
echo -n "  PostgreSQL: "
if pg_isready -q 2>/dev/null; then
    echo -e "${GREEN}✓ RUNNING${NC}"
else
    echo -e "${RED}NOT RUNNING${NC}"
fi

echo -n "  Redis:      "
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ RUNNING${NC}"
else
    echo -e "${RED}NOT RUNNING${NC}"
fi

echo ""
echo "Services:"

# Check all services
check_service "  Main Server       " ".pids/main.pid" "8888" "http://localhost:8888/health"
check_service "  Correlation API   " ".pids/correlation.pid" "5004" "http://localhost:5004/health"
check_service "  Daily Planet API  " ".pids/daily_planet.pid" "5000" "http://localhost:5000/health"
check_service "  Swing Dashboard   " ".pids/swing.pid" "5002" "http://localhost:5002/api/swing-dashboard/health"
check_service "  GARP API          " ".pids/garp.pid" "5003" "http://localhost:5003/api/health"
check_service "  Data Refresh      " ".pids/refresh.pid" "" ""

echo ""
echo "Recent Logs:"
echo "------------"
if [ -f "logs/main_server.log" ]; then
    echo "Main Server (last 3 lines):"
    tail -3 logs/main_server.log | sed 's/^/  /'
    echo ""
fi

echo "Cache Status:"
echo "-------------"
echo -n "Redis Keys: "
redis_keys=$(redis-cli DBSIZE 2>/dev/null | awk '{print $2}')
if [ ! -z "$redis_keys" ]; then
    echo -e "${GREEN}$redis_keys keys${NC}"

    # Check for some expected keys
    if redis-cli EXISTS market:index:SPY > /dev/null 2>&1; then
        ttl=$(redis-cli TTL market:index:SPY 2>/dev/null)
        echo "  Sample key (market:index:SPY): TTL $ttl seconds"
    fi
else
    echo -e "${YELLOW}Unable to check${NC}"
fi

echo ""
echo "PostgreSQL Database:"
echo "--------------------"
count=$(psql -d spartan_research_db -t -c "SELECT COUNT(*) FROM preloaded_market_data WHERE timestamp > NOW() - INTERVAL '1 hour';" 2>/dev/null | xargs || echo "0")
echo "Recent data entries (last hour): $count"

echo ""
echo "========================================================================"
echo ""
echo "Quick Actions:"
echo "  View logs:     tail -f logs/*.log"
echo "  Restart all:   ./RESTART_SPARTAN_DEV.sh"
echo "  Stop all:      ./STOP_SPARTAN_DEV.sh"
echo ""
