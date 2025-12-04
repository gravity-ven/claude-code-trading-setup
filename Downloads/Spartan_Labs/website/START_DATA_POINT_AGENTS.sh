#!/bin/bash
# START DATA POINT AGENTS
# ===================
# Starts the full agent-per-data-point system with monitoring

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}🚀 STARTING DATA POINT AGENTS SYSTEM${NC}"
echo -e "${BLUE}============================================${NC}"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "agents/data_point_master_orchestrator.py" ]; then
    echo -e "${YELLOW}⚠️  Please run this script from the website directory${NC}"
    echo -e "${YELLOW}   Current directory: $(pwd)${NC}"
    exit 1
fi

# Create logs directory
mkdir -p logs/agents

echo -e "${GREEN}📋 Starting Data Point Master Orchestrator...${NC}"
echo -e "${GREEN}   Each agent will manage ONE data point 24/7${NC}"
echo -e "${GREEN}   Auto-healing enabled for failed agents${NC}"
echo

# Function to start orchestrator
start_orchestrator() {
    echo -e "${BLUE}🎯 Starting Data Point Master Orchestrator...${NC}"
    
    # Start in background
    python3 agents/data_point_master_orchestrator.py > logs/agents/orchestrator.log 2>&1 &
    ORCHESTRATOR_PID=$!
    
    echo -e "${GREEN}✅ Master Orchestrator started (PID: $ORCHESTRATOR_PID)${NC}"
    echo -e "${GREEN}📊 Logs: logs/agents/orchestrator.log${NC}"
    
    # Wait a moment for startup
    sleep 3
}

# Function to start health API
start_health_api() {
    echo -e "${BLUE}🏥 Starting Agent Health Monitoring API...${NC}"
    
    # Start in background
    python3 agents/agent_health_api.py > logs/agents/health_api.log 2>&1 &
    HEALTH_API_PID=$!
    
    echo -e "${GREEN}✅ Health API started (PID: $HEALTH_API_PID)${NC}"
    echo -e "${GREEN}🌐 API: http://localhost:8890${NC}"
    echo -e "${GREEN}📊 Logs: logs/agents/health_api.log${NC}"
    
    # Save PIDs for later
    echo $ORCHESTRATOR_PID > logs/agents/orchestrator.pid
    echo $HEALTH_API_PID > logs/agents/health_api.pid
    
    # Wait a moment for startup
    sleep 3
}

# Function to check system health
check_health() {
    echo -e "${BLUE}🔍 Checking system health...${NC}"
    
    # Check orchestrator
    if [ -f logs/agents/orchestrator.pid ]; then
        PID=$(cat logs/agents/orchestrator.pid)
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Orchestrator running (PID: $PID)${NC}"
        else
            echo -e "${RED}❌ Orchestrator not running${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Orchestrator PID file not found${NC}"
        return 1
    fi
    
    # Check health API
    if [ -f logs/agents/health_api.pid ]; then
        PID=$(cat logs/agents/health_api.pid)
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Health API running (PID: $PID)${NC}"
        else
            echo -e "${RED}❌ Health API not running${NC}"
            return 1
        fi
    fi
    
    # Test health endpoint
    echo -e "${BLUE}🔗 Testing health endpoint...${NC}"
    if curl -s http://localhost:8890/api/agents/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Health API responding${NC}"
    else
        echo -e "${YELLOW}⚠️  Health API not yet responding (still starting)${NC}"
    fi
    
    return 0
}

# Function to show status
show_status() {
    echo
    echo -e "${BLUE}📊 SYSTEM STATUS${NC}"
    echo -e "${BLUE}================${NC}"
    
    # Show running processes
    echo -e "${GREEN}🔄 Running Processes:${NC}"
    ps aux | grep -E "(orchestrator|health_api)" | grep python3 || echo "No processes found"
    
    echo
    echo -e "${GREEN}🌐 Available Endpoints:${NC}"
    echo -e "   Health Dashboard: http://localhost:8890"
    echo -e "   System Health:     http://localhost:8890/api/agents/health"
    echo -e "   All Agents:        http://localhost:8890/api/agents/list" 
    echo -e "   Market Summary:    http://localhost:8890/api/data/market-summary"
    echo -e "   Real-time Updates: ws://localhost:8890/ws/health"
    
    echo
    echo -e "${GREEN}📝 Data Point Agents:${NC}"
    echo -e "   🏦 SPY Agent  - S&P 500 ETF"
    echo -e "   📈 QQQ Agent  - NASDAQ-100 ETF"  
    echo -e "   ₿ BTC Agent  - Bitcoin USD"
    echo -e "   📉 VIX Agent  - Volatility Index"
    echo -e "   🇺🇸 10Y Agent - 10-Year Treasury"
    
    echo
    echo -e "${GREEN}🔧 Management Commands:${NC}"
    echo -e "   Stop System:     ./STOP_DATA_POINT_AGENTS.sh"
    echo -e "   View Logs:       tail -f logs/agents/orchestrator.log"
    echo -e "   Health Check:    curl http://localhost:8890/api/agents/health"
    echo -e "   Agent Status:    curl http://localhost:8890/api/agents/status/spy_agent"
}

# Main execution
main() {
    # Start orchestrator
    start_orchestrator
    
    # Start health API
    start_health_api
    
    # Check health
    if check_health; then
        echo
        echo -e "${GREEN}🎉 Data Point Agents System Started Successfully!${NC}"
        echo
        show_status
    else
        echo -e "${RED}❌ Failed to start system${NC}"
        echo -e "${YELLOW}📋 Check logs for details:${NC}"
        echo -e "${YELLOW}   Orchestrator: logs/agents/orchestrator.log${NC}"
        echo -e "${YELLOW}   Health API:   logs/agents/health_api.log${NC}"
        exit 1
    fi
}

# Trap signals for cleanup
trap cleanup INT TERM

cleanup() {
    echo
    echo -e "${YELLOW}🛑 Shutting down Data Point Agents System...${NC}"
    
    # Kill processes
    if [ -f logs/agents/orchestrator.pid ]; then
        PID=$(cat logs/agents/orchestrator.pid)
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID
            echo -e "${GREEN}✅ Stopped orchestrator (PID: $PID)${NC}"
        fi
    fi
    
    if [ -f logs/agents/health_api.pid ]; then
        PID=$(cat logs/agents/health_api.pid)
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID
            echo -e "${GREEN}✅ Stopped health API (PID: $PID)${NC}"
        fi
    fi
    
    echo -e "${GREEN}👋 Data Point Agents System stopped${NC}"
}

# Run main function
main
