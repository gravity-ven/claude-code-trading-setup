#!/bin/bash
# CHECK DATA POINT AGENTS STATUS
# ==============================
# Quick script to check the status of running data point agents

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}📊 DATA POINT AGENTS STATUS CHECK${NC}"
echo -e "${BLUE}============================================${NC}"
echo

# Function to check if process is running
check_process() {
    local pid_file=$1
    local process_name=$2
    local service_url=$3
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $process_name is running (PID: $pid)${NC}"
            
            # Check service if URL provided
            if [ ! -z "$service_url" ]; then
                if curl -s "$service_url" > /dev/null 2>&1; then
                    echo -e "${GREEN}   🌐 Service responding at $service_url${NC}"
                else
                    echo -e "${YELLOW}   ⚠️  Service not responding (may still be starting)${NC}"
                fi
            fi
            return 0
        else
            echo -e "${RED}❌ $process_name is NOT running (stale PID file)${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ $process_name is NOT running (no PID file)${NC}"
        return 1
    fi
}

# Function to test API endpoints
test_api_endpoints() {
    echo -e "${BLUE}🔗 Testing API Endpoints...${NC}"
    
    local base_url="http://localhost:8890"
    
    # Test different endpoints
    local endpoints=(
        "/api/agents/health:System Health"
        "/api/agents/list:Agent List"
        "/api/agents/metrics:System Metrics"
        "/api/data/market-summary:Market Summary"
    )
    
    for endpoint in "${endpoints[@]}"; do
        local url_path="${endpoint%%:*}"
        local description="${endpoint##*:}"
        
        if curl -s "$base_url$url_path" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $description${NC}"
        else
            echo -e "${RED}❌ $description (failed)${NC}"
        fi
    done
    
    echo
}

# Function to show system summary
show_system_summary() {
    echo -e "${BLUE}📊 SYSTEM SUMMARY${NC}"
    echo -e "${BLUE}================${NC}"
    
    # Check number of running processes
    local orchestrator_running=0
    local health_api_running=0
    
    if [ -f "logs/agents/orchestrator.pid" ]; then
        local pid=$(cat logs/agents/orchestrator.pid)
        if ps -p $pid > /dev/null 2>&1; then
            orchestrator_running=1
        fi
    fi
    
    if [ -f "logs/agents/health_api.pid" ]; then
        local pid=$(cat logs/agents/health_api.pid)
        if ps -p $pid > /dev/null 2>&1; then
            health_api_running=1
        fi
    fi
    
    # Show overall status
    if [ $orchestrator_running -eq 1 ] && [ $health_api_running -eq 1 ]; then
        echo -e "${GREEN}🟢 SYSTEM HEALTHY - All components running${NC}"
    elif [ $orchestrator_running -eq 1 ]; then
        echo -e "${YELLOW}🟡 SYSTEM DEGRADED - Orchestrator running, API not responding${NC}"
    else
        echo -e "${RED}🔴 SYSTEM DOWN - No components running${NC}"
    fi
    
    echo
    echo -e "${GREEN}🔧 Available Commands:${NC}"
    echo -e "   View real-time logs:   tail -f logs/agents/orchestrator.log"
    echo -e "   View API logs:         tail -f logs/agents/health_api.log"
    echo -e "   Test system health:    curl http://localhost:8890/api/agents/health"
    echo -e "   Restart system:       ./START_DATA_POINT_AGENTS.sh"
    echo -e "   Stop system:           ./STOP_DATA_POINT_AGENTS.sh"
    echo
}

# Function to show agent data
show_agent_data() {
    echo -e "${BLUE}📈 LIVE DATA FROM AGENTS${NC}"
    echo -e "${BLUE}=====================${NC}"
    
    if curl -s http://localhost:8890/api/data/market-summary > /dev/null 2>&1; then
        # Get market summary
        local market_data=$(curl -s http://localhost:8890/api/data/market-summary)
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}📊 Market Summary:${NC}"
            echo "$market_data" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f\"📅 Timestamp: {data.get('timestamp', 'N/A')}\")
print(f\"📊 Market Sentiment: {data.get('market_sentiment', 'N/A')}\")
if 'average_change' in data:
    print(f\"📈 Average Change: {data['average_change']:+.2f}%\")
print()
for symbol, info in data.get('indices', {}).items():
    price = info.get('price', 'N/A')
    change = info.get('change_percent', 'N/A')
    source = info.get('source', 'N/A')
    print(f\"  {symbol}: \\${price} ({change:+.2f}%) [{source}]\")
" 2>/dev/null || echo -e "${YELLOW}⚠️  Could not parse market data${NC}"
        else
            echo -e "${YELLOW}⚠️  Market data not available${NC}"
        fi
    else
        echo -e "${RED}❌ Cannot connect to agent system${NC}"
    fi
    
    echo
}

# Main execution
main() {
    # Check if we're in the right directory
    if [ ! -d "logs/agents" ]; then
        echo -e "${YELLOW}⚠️  Agent logs directory not found. Agents may not be running.${NC}"
        echo -e "${YELLOW}   Current directory: $(pwd)${NC}"
        echo
    fi
    
    echo -e "${GREEN}🔍 Checking Data Point Agents Status...${NC}"
    echo
    
    # Check orchestrator
    local orchestrator_status=0
    check_process "logs/agents/orchestrator.pid" "Master Orchestrator"
    orchestrator_status=$?
    echo
    
    # Check health API
    local api_status=0
    check_process "logs/agents/health_api.pid" "Health Monitoring API" "http://localhost:8890/api/agents/health"
    api_status=$?
    echo
    
    # Test API endpoints if API is running
    if [ $api_status -eq 0 ]; then
        test_api_endpoints
        show_agent_data
    fi
    
    # Show system summary
    show_system_summary
    
    # Exit with appropriate code
    if [ $orchestrator_status -eq 0 ] && [ $api_status -eq 0 ]; then
        exit 0
    else
        echo -e "${RED}❌ System is not fully operational${NC}"
        echo -e "${BLUE}💡 Run './START_DATA_POINT_AGENTS.sh' to start the system${NC}"
        exit 1
    fi
}

# Run main function
main
