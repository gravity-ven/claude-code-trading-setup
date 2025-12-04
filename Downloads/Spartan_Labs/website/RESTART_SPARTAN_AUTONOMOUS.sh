#!/bin/bash
##############################################################################
# RESTART SPARTAN AUTONOMOUS SYSTEM
# Stops and restarts all services
##############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Restarting Spartan Autonomous Research Station...${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Stop first
echo -e "${CYAN}Step 1: Stopping services...${NC}"
echo ""
./STOP_SPARTAN_AUTONOMOUS.sh

echo ""
echo -e "${CYAN}Step 2: Waiting 3 seconds...${NC}"
sleep 3

echo ""
echo -e "${CYAN}Step 3: Starting services...${NC}"
echo ""

# Start
./START_SPARTAN_AUTONOMOUS.sh
