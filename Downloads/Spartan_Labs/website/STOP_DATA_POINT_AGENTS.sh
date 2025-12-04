#!/bin/bash
# STOP DATA POINT AGENTS
# ===================
# Stops all data point agents and monitoring components

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}🛑 STOPPING DATA POINT AGENTS SYSTEM${NC}"
echo -e "${BLUE}============================================${NC}"
echo

# Function to stop process by PID and name
stop_process() {
    local pid_file=$1
    local process_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${YELLOW}⏹️  Stopping $process_name (PID: $pid)...${NC}"
            kill -TERM $pid
            
            # Wait for graceful shutdown
            local count=0
            while ps -p $pid > /dev/null 2>&1 && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # Force kill if still running
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "${RED}⚡ Force killing $process_name${NC}"
                kill -KILL $pid
            else
                echo -e "${GREEN}✅ $process_name stopped gracefully${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️  $process_name was not running${NC}"
        fi
        
        # Remove PID file
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}⚠️  No PID file found for $process_name${NC}"
    fi
    
    echo
}

# Function to kill any remaining agent processes
kill_remaining_agents() {
    echo -e "${BLUE}🔍 Checking for any remaining agent processes...${NC}"
    
    # Find any remaining agent processes
    local agent_processes=$(ps aux | grep "data_point_master_orchestrator\|agent_health_api" | grep python3 | grep -v grep || true)
    
    if [ ! -z "$agent_processes" ]; then
        echo -e "${YELLOW}⚠️  Found remaining agent processes:${NC}"
        echo "$agent_processes"
        echo
        
        echo -e "${YELLOW}🗑️  Killing remaining processes...${NC}"
        echo "$agent_processes" | awk '{print $2}' | xargs kill -TERM
        
        # Wait a moment
        sleep 2
        
        # Force kill if still running
        agent_processes=$(ps aux | grep "data_point_master_orchestrator\|agent_health_api" | grep python3 | grep -v grep || true)
        if [ ! -z "$agent_processes" ]; then
            echo -e "${RED}⚡ Force killing remaining processes...${NC}"
            echo "$agent_processes" | awk '{print $2}' | xargs kill -KILL
        fi
        
        echo -e "${GREEN}✅ All remaining agent processes stopped${NC}"
    else
        echo -e "${GREEN}✅ No remaining agent processes found${NC}"
    fi
    
    echo
}

# Function to cleanup logs (optional)
cleanup_logs() {
    if [ "$1" = "--cleanup-logs" ]; then
        echo -e "${BLUE}🗑️  Cleaning up log files...${NC}"
        rm -rf logs/agents/*.log
        echo -e "${GREEN}✅ Log files cleaned${NC}"
        echo
    fi
}

# Function to show final status
show_final_status() {
    echo -e "${BLUE}📊 FINAL STATUS${NC}"
    echo -e "${BLUE}================${NC}"
    
    # Check for any remaining processes
    local remaining=$(ps aux | grep "data_point_master_orchestrator\|agent_health_api" | grep python3 | grep -v grep || true)
    
    if [ ! -z "$remaining" ]; then
        echo -e "${RED}❌ Some agent processes are still running:${NC}"
        echo "$remaining"
        echo -e "${YELLOW}⚠️  You may need to manually kill these processes${NC}"
    else
        echo -e "${GREEN}✅ All agent processes stopped successfully${NC}"
    fi
    
    echo
    echo -e "${GREEN}👋 Data Point Agents System stopped${NC}"
    echo
    echo -e "${BLUE}🔄 To restart: ./START_DATA_POINT_AGENTS.sh${NC}"
}

# Main execution
main() {
    local cleanup_logs=""
    
    # Check for cleanup flag
    if [ "$1" = "--cleanup-logs" ]; then
        cleanup_logs="--cleanup-logs"
    fi
    
    echo -e "${GREEN}🛑 Stopping Data Point Agents System...${NC}"
    echo
    
    # Stop orchestrator
    stop_process "logs/agents/orchestrator.pid" "Master Orchestrator"
    
    # Stop health API
    stop_process "logs/agents/health_api.pid" "Health Monitoring API"
    
    # Kill any remaining processes
    kill_remaining_agents
    
    # Cleanup logs if requested
    cleanup_logs "$cleanup_logs"
    
    # Show final status
    show_final_status
}

# Handle signals gracefully
trap 'echo ""; echo -e "${YELLOW}⚠️  Received interrupt signal${NC}"; exit 1' INT TERM

# Run main function with all arguments
main "$@"
