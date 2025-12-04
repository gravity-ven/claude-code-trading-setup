#!/bin/bash
# Daily Scanner Automation Wrapper
# Runs at 8:00 AM daily to scan market and email top 10 symbols

# Set working directory
cd /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website

# Load environment variables
export POLYGON_IO_API_KEY=08bqd7Ew8fw1b7QcixwkTea1UvJHdRkD

# Log file
LOG_FILE="/mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/daily_scanner.log"

# Run the scanner
echo "========================================" >> "$LOG_FILE"
echo "Daily Scanner Started: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

/usr/bin/python3 daily_scanner_emailer.py >> "$LOG_FILE" 2>&1

# Log completion
echo "Daily Scanner Completed: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
