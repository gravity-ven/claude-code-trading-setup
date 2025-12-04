#!/bin/bash
##############################################################################
# STATUS CHECK - SPARTAN AUTONOMOUS SYSTEM
# Shows current status of all services and monitoring
##############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${PURPLE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${PURPLE}${BOLD}  SPARTAN AUTONOMOUS SYSTEM - STATUS REPORT${NC}"
echo -e "${PURPLE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Function to check service status
check_service() {
    local name=$1
    local pid_file=".pids/${name}.pid"
    local port=$2

    echo -n "   $name: "

    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Running${NC} (PID: $pid)"

            if [ ! -z "$port" ]; then
                # Test endpoint
                response=$(curl -s -w "%{http_code}" "http://localhost:$port/health" -o /dev/null 2>&1)
                if [ "$response" = "200" ]; then
                    echo -e "      └─ Health Check: ${GREEN}✓ Responding${NC}"
                else
                    echo -e "      └─ Health Check: ${RED}✗ Failed (HTTP $response)${NC}"
                fi
            fi
        else
            echo -e "${RED}✗ Not Running${NC} (PID file exists but process dead)"
        fi
    else
        echo -e "${YELLOW}⚠ Not Started${NC}"
    fi
}

echo -e "${CYAN}🔧 Infrastructure:${NC}"
echo -n "   PostgreSQL: "
if pg_isready -q 2>/dev/null; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${RED}✗ Not Running${NC}"
fi

echo -n "   Redis: "
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Running${NC}"
    keys=$(redis-cli KEYS 'market:*' 2>/dev/null | wc -l)
    echo -e "      └─ Cached Keys: $keys market keys"
else
    echo -e "${RED}✗ Not Running${NC}"
fi

echo ""
echo -e "${CYAN}🌐 Web Services:${NC}"
check_service "main" "8888"
check_service "correlation" "5004"
check_service "daily_planet" "5000"
check_service "swing" "5002"
check_service "garp" "5003"

echo ""
echo -e "${CYAN}📊 Background Services:${NC}"
check_service "refresh"
check_service "monitor"
check_service "claude_watcher"

echo ""
echo -e "${CYAN}💾 Database:${NC}"
echo -n "   Data Freshness: "
count=$(psql -d spartan_research_db -t -c "SELECT COUNT(*) FROM preloaded_market_data WHERE timestamp > NOW() - INTERVAL '1 hour';" 2>/dev/null | xargs)
if [ ! -z "$count" ] && [ "$count" -gt 0 ]; then
    echo -e "${GREEN}✓ $count records in last hour${NC}"
else
    echo -e "${YELLOW}⚠ No recent data (may be loading)${NC}"
fi

echo ""
echo -e "${CYAN}📝 Recent Activity (last 10 log entries):${NC}"
if [ -f "logs/health_monitor.log" ]; then
    echo -e "${BLUE}───────────────────────────────────────────────────────${NC}"
    tail -n 10 logs/health_monitor.log | while read line; do
        if echo "$line" | grep -q "✅"; then
            echo -e "${GREEN}$line${NC}"
        elif echo "$line" | grep -q "❌\|✗"; then
            echo -e "${RED}$line${NC}"
        elif echo "$line" | grep -q "⚠"; then
            echo -e "${YELLOW}$line${NC}"
        else
            echo "$line"
        fi
    done
    echo -e "${BLUE}───────────────────────────────────────────────────────${NC}"
else
    echo -e "${YELLOW}   ⚠ No logs found (monitor not started)${NC}"
fi

echo ""
echo -e "${CYAN}🔍 Quick Health Test:${NC}"
for endpoint in "8888" "5004" "5000" "5002" "5003"; do
    response=$(curl -s -w "%{http_code}" "http://localhost:$endpoint/health" -o /dev/null 2>&1)
    if [ "$response" = "200" ]; then
        echo -e "   localhost:$endpoint ${GREEN}✓ OK${NC}"
    else
        echo -e "   localhost:$endpoint ${RED}✗ Failed (HTTP $response)${NC}"
    fi
done

echo ""
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Summary
services_up=0
services_down=0

for service in "main" "correlation" "daily_planet" "swing" "garp" "refresh" "monitor"; do
    if [ -f ".pids/${service}.pid" ]; then
        pid=$(cat ".pids/${service}.pid")
        if ps -p "$pid" > /dev/null 2>&1; then
            services_up=$((services_up + 1))
        else
            services_down=$((services_down + 1))
        fi
    else
        services_down=$((services_down + 1))
    fi
done

echo -e "${BOLD}Summary:${NC}"
echo -e "   Services Up: ${GREEN}$services_up${NC}"
echo -e "   Services Down: ${RED}$services_down${NC}"
echo ""

if [ $services_down -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✅ System Status: HEALTHY${NC}"
elif [ $services_up -gt 0 ]; then
    echo -e "${YELLOW}${BOLD}⚠️  System Status: DEGRADED${NC}"
else
    echo -e "${RED}${BOLD}❌ System Status: DOWN${NC}"
fi

echo ""
