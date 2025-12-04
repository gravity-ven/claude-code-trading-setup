#!/bin/bash
# Auto-generated wrapper script for COT daily emailer with catch-up

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAST_RUN_FILE="${SCRIPT_DIR}/.cot_last_run"
TODAY=$(date +%Y-%m-%d)

# Change to script directory
cd "$SCRIPT_DIR"

# Check if we already ran today
if [ -f "$LAST_RUN_FILE" ]; then
    LAST_RUN=$(cat "$LAST_RUN_FILE")
    if [ "$LAST_RUN" == "$TODAY" ]; then
        echo "$(date): COT report already sent today. Skipping." >> "${SCRIPT_DIR}/cot_daily_cron.log"
        exit 0
    fi
fi

# Run the script
python3 "${SCRIPT_DIR}/cot_daily_emailer.py" >> "${SCRIPT_DIR}/cot_daily_cron.log" 2>&1
EXIT_CODE=$?

# If successful, record today's date
if [ $EXIT_CODE -eq 0 ]; then
    echo "$TODAY" > "$LAST_RUN_FILE"
    echo "$(date): COT report sent successfully for $TODAY" >> "${SCRIPT_DIR}/cot_daily_cron.log"
else
    echo "$(date): COT report failed with exit code $EXIT_CODE" >> "${SCRIPT_DIR}/cot_daily_cron.log"
fi

exit $EXIT_CODE
