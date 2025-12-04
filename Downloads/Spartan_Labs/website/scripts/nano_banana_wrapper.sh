#!/bin/bash
# Wrapper script with catch-up mechanism for missed runs

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_DIR/venv/bin/python3"
SCRIPT_PATH="$SCRIPT_DIR/nano_banana_daily_email.py"
LOG_DIR="$PROJECT_DIR/logs"
STATE_FILE="$LOG_DIR/.last_run_nano_banana"

# Email credentials
export SENDER_EMAIL="naga.kvv@gmail.com"
export SENDER_PASSWORD="wxrwhmtnfzmknggv"
export RECEIVER_EMAIL="naga.kvv@gmail.com"

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
