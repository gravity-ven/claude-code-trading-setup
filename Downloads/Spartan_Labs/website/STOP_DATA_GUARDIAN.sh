#!/bin/bash

##############################################################################
# STOP DATA GUARDIAN AGENT
#
# Gracefully stops the running Data Guardian Agent
##############################################################################

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}Stopping Data Guardian Agent...${NC}"

if [ -f data_guardian.pid ]; then
    PID=$(cat data_guardian.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${YELLOW}Sending SIGTERM to PID $PID...${NC}"
        kill -TERM $PID

        # Wait for graceful shutdown (max 10 seconds)
        for i in {1..10}; do
            if ! ps -p $PID > /dev/null 2>&1; then
                break
            fi
            sleep 1
        done

        # Force kill if still running
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${YELLOW}Force killing PID $PID...${NC}"
            kill -9 $PID
        fi

        rm data_guardian.pid
        echo -e "${GREEN}✅ Data Guardian Agent stopped${NC}"
    else
        echo -e "${RED}❌ Process $PID not found (stale PID file)${NC}"
        rm data_guardian.pid
    fi
else
    echo -e "${RED}❌ No PID file found - agent may not be running${NC}"

    # Try to find by process name
    PIDS=$(pgrep -f data_guardian_agent.py)
    if [ ! -z "$PIDS" ]; then
        echo -e "${YELLOW}Found Data Guardian processes: $PIDS${NC}"
        echo -e "${YELLOW}Killing them...${NC}"
        pkill -f data_guardian_agent.py
        echo -e "${GREEN}✅ Killed all Data Guardian processes${NC}"
    fi
fi
