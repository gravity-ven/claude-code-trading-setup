#!/bin/bash
# Setup script for Nano Banana Daily Email Cron Job
# Handles missed runs with catch-up mechanism

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_DIR/venv/bin/python3"
SCRIPT_PATH="$SCRIPT_DIR/nano_banana_daily_email.py"
LOG_DIR="$PROJECT_DIR/logs"
STATE_FILE="$LOG_DIR/.last_run_nano_banana"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Nano Banana Daily Email Cron Setup  ${NC}"
echo -e "${GREEN}========================================${NC}"

# 1. Check if script exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo -e "${RED}Error: Script not found at $SCRIPT_PATH${NC}"
    exit 1
fi

# 2. Make script executable
chmod +x "$SCRIPT_PATH"
echo -e "${GREEN}✓${NC} Made script executable"

# 3. Check Python dependencies
echo -e "\n${YELLOW}Checking Python dependencies...${NC}"
if [ -f "$VENV_PATH" ]; then
    echo -e "${GREEN}✓${NC} Using virtual environment: $VENV_PATH"
    PYTHON_CMD="$VENV_PATH"
else
    echo -e "${YELLOW}⚠${NC} Virtual environment not found, using system Python"
    PYTHON_CMD="python3"
fi

# Check required packages
$PYTHON_CMD -c "import pandas, pandas_ta, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Missing dependencies. Install with:${NC}"
    echo -e "  pip install pandas pandas_ta requests"
    exit 1
fi
echo -e "${GREEN}✓${NC} All dependencies installed"

# 4. Create logs directory
mkdir -p "$LOG_DIR"
echo -e "${GREEN}✓${NC} Created logs directory: $LOG_DIR"

# 5. Check environment variables
echo -e "\n${YELLOW}Checking environment variables...${NC}"
if [ -z "$SENDER_PASSWORD" ]; then
    echo -e "${YELLOW}⚠${NC} SENDER_PASSWORD not set"
    echo -e "  You need to set this before the cron job will work:"
    echo -e "  export SENDER_PASSWORD='your_gmail_app_password'"
fi

if [ -z "$SENDER_EMAIL" ]; then
    echo -e "${YELLOW}⚠${NC} SENDER_EMAIL not set (will use default from script)"
fi

# 6. Create wrapper script with catch-up logic
WRAPPER_SCRIPT="$SCRIPT_DIR/nano_banana_wrapper.sh"
cat > "$WRAPPER_SCRIPT" << 'EOF'
#!/bin/bash
# Wrapper script with catch-up mechanism for missed runs

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_DIR/venv/bin/python3"
SCRIPT_PATH="$SCRIPT_DIR/nano_banana_daily_email.py"
LOG_DIR="$PROJECT_DIR/logs"
STATE_FILE="$LOG_DIR/.last_run_nano_banana"

# Use virtual environment if available
if [ -f "$VENV_PATH" ]; then
    PYTHON_CMD="$VENV_PATH"
else
    PYTHON_CMD="python3"
fi

# Get today's date
TODAY=$(date +%Y-%m-%d)

# Check if already ran today
if [ -f "$STATE_FILE" ]; then
    LAST_RUN=$(cat "$STATE_FILE")
    if [ "$LAST_RUN" == "$TODAY" ]; then
        echo "$(date): Already ran today, skipping" >> "$LOG_DIR/nano_banana_cron.log"
        exit 0
    fi
fi

# Run the script
echo "$(date): Running Nano Banana Daily Email" >> "$LOG_DIR/nano_banana_cron.log"
$PYTHON_CMD "$SCRIPT_PATH"

# Record successful run
if [ $? -eq 0 ]; then
    echo "$TODAY" > "$STATE_FILE"
    echo "$(date): ✓ Success" >> "$LOG_DIR/nano_banana_cron.log"
else
    echo "$(date): ✗ Failed" >> "$LOG_DIR/nano_banana_cron.log"
fi
EOF

chmod +x "$WRAPPER_SCRIPT"
echo -e "${GREEN}✓${NC} Created wrapper script: $WRAPPER_SCRIPT"

# 7. Create cron job entry
CRON_ENTRY="1 8 * * * $WRAPPER_SCRIPT >> $LOG_DIR/nano_banana_cron.log 2>&1"
BOOT_ENTRY="@reboot sleep 60 && $WRAPPER_SCRIPT >> $LOG_DIR/nano_banana_cron.log 2>&1"

echo -e "\n${YELLOW}Cron Job Configuration:${NC}"
echo -e "${GREEN}Daily Run:${NC}  $CRON_ENTRY"
echo -e "${GREEN}Boot Run:${NC}   $BOOT_ENTRY"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "nano_banana_wrapper.sh"; then
    echo -e "\n${YELLOW}⚠${NC} Cron job already exists. Remove old entries? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        # Remove old entries
        crontab -l 2>/dev/null | grep -v "nano_banana_wrapper.sh" | crontab -
        echo -e "${GREEN}✓${NC} Removed old cron entries"
    else
        echo -e "${YELLOW}⚠${NC} Keeping existing cron entries"
        exit 0
    fi
fi

# 8. Install cron job
echo -e "\n${YELLOW}Installing cron job...${NC}"
(crontab -l 2>/dev/null; echo "$CRON_ENTRY"; echo "$BOOT_ENTRY") | crontab -

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Cron job installed successfully!"
else
    echo -e "${RED}✗${NC} Failed to install cron job"
    exit 1
fi

# 9. Verify installation
echo -e "\n${YELLOW}Verifying cron job installation...${NC}"
if crontab -l | grep -q "nano_banana_wrapper.sh"; then
    echo -e "${GREEN}✓${NC} Cron job verified in crontab"
else
    echo -e "${RED}✗${NC} Cron job not found in crontab"
    exit 1
fi

# 10. Test run (optional)
echo -e "\n${YELLOW}Would you like to do a test run now? (y/n)${NC}"
read -r test_response
if [[ "$test_response" =~ ^[Yy]$ ]]; then
    echo -e "\n${YELLOW}Running test...${NC}"
    $WRAPPER_SCRIPT
    echo -e "\n${GREEN}✓${NC} Test complete. Check $LOG_DIR for results."
fi

# 11. Summary
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}         Setup Complete!               ${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e ""
echo -e "${YELLOW}Schedule:${NC}"
echo -e "  • Daily at 08:01 AM"
echo -e "  • On boot (if missed, with 60s delay)"
echo -e ""
echo -e "${YELLOW}Logs:${NC}"
echo -e "  • Cron log: $LOG_DIR/nano_banana_cron.log"
echo -e "  • Script log: $LOG_DIR/nano_banana_*.log"
echo -e ""
echo -e "${YELLOW}Important:${NC}"
echo -e "  • Set ${GREEN}SENDER_PASSWORD${NC} environment variable"
echo -e "  • Set ${GREEN}SENDER_EMAIL${NC} environment variable"
echo -e "  • Add to ~/.bashrc or ~/.profile for persistence:"
echo -e "    ${GREEN}export SENDER_PASSWORD='your_gmail_app_password'${NC}"
echo -e "    ${GREEN}export SENDER_EMAIL='your_email@gmail.com'${NC}"
echo -e ""
echo -e "${YELLOW}Commands:${NC}"
echo -e "  • View logs: ${GREEN}tail -f $LOG_DIR/nano_banana_cron.log${NC}"
echo -e "  • Test run: ${GREEN}$WRAPPER_SCRIPT${NC}"
echo -e "  • Edit cron: ${GREEN}crontab -e${NC}"
echo -e "  • List cron: ${GREEN}crontab -l${NC}"
echo -e ""
