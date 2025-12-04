#!/bin/bash
# RESTART_SPARTAN_DEV.sh
# Restart all native development services

echo "========================================================================"
echo "  SPARTAN RESEARCH STATION - RESTARTING DEVELOPMENT SERVICES"
echo "========================================================================"
echo ""

# Stop all services
./STOP_SPARTAN_DEV.sh

# Wait a moment for ports to be released
sleep 2

# Start all services
./START_SPARTAN_DEV.sh
