#!/bin/bash
#
# Alacritty Startup Script for COT Monitor
# This script runs when Alacritty terminal opens
#

# Navigate to project directory
cd /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website

# Show banner
clear
cat << 'EOF'
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║           SPARTAN COT AGENTS - Daily Market Monitor             ║
║                                                                  ║
║  Analyzing markets using real CFTC data (professional traders)  ║
║  Updates: Every 24 hours                                         ║
║  Press Ctrl+C to stop                                            ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
EOF

echo ""
echo "Starting in 3 seconds..."
sleep 3

# Run the daily monitor
exec ./SIMPLE_DAILY_MONITOR.sh
