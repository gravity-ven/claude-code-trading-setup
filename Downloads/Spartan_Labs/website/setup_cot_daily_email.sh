#!/bin/bash
###############################################################################
# Spartan Labs - COT Daily Email Setup (Linux/WSL Cron)
###############################################################################
# This script sets up a cron job to run the COT emailer daily
###############################################################################

set -e  # Exit on error

echo ""
echo "========================================================================"
echo "SPARTAN LABS - COT DAILY EMAIL SETUP (Linux/WSL)"
echo "========================================================================"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/cot_daily_emailer.py"
VENV_DIR="${SCRIPT_DIR}/venv"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python 3 not found!"
    echo ""
    echo "Install Python 3.13+:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "  macOS:         brew install python@3.13"
    echo ""
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Check if COT script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ ERROR: COT emailer script not found!"
    echo "Expected: $PYTHON_SCRIPT"
    echo ""
    exit 1
fi

echo "✅ COT script found: $PYTHON_SCRIPT"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "✅ Virtual environment created"
    echo ""
fi

# Activate virtual environment and install dependencies
echo "Installing required packages..."
source "$VENV_DIR/bin/activate"
pip install --quiet matplotlib pandas numpy requests python-dotenv
echo "✅ Packages installed"
echo ""

# Deactivate venv
deactivate

# Prompt for email time
echo "========================================================================"
echo "SCHEDULE CONFIGURATION"
echo "========================================================================"
echo ""
echo "What time should the COT report be sent daily?"
echo "Default: 08:00 AM"
echo ""
read -p "Enter time (HH:MM format, 24-hour): " EMAIL_TIME

if [ -z "$EMAIL_TIME" ]; then
    EMAIL_TIME="08:00"
    echo "Using default time: 08:00 AM"
fi

# Parse time
HOUR=$(echo "$EMAIL_TIME" | cut -d: -f1)
MINUTE=$(echo "$EMAIL_TIME" | cut -d: -f2)

# Create wrapper script for cron with catch-up mechanism
WRAPPER_SCRIPT="${SCRIPT_DIR}/run_cot_daily.sh"
LAST_RUN_FILE="${SCRIPT_DIR}/.cot_last_run"

cat > "$WRAPPER_SCRIPT" << 'EOF'
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

# Load environment variables (handle spaces in values)
set -a
source .env
set +a

# Activate virtual environment and run script
source "$VENV_DIR/bin/activate"
python3 "$PYTHON_SCRIPT" >> "${SCRIPT_DIR}/cot_daily_cron.log" 2>&1
EXIT_CODE=$?
deactivate

# If successful, record today's date
if [ $EXIT_CODE -eq 0 ]; then
    echo "$TODAY" > "$LAST_RUN_FILE"
    echo "$(date): COT report sent successfully for $TODAY" >> "${SCRIPT_DIR}/cot_daily_cron.log"
else
    echo "$(date): COT report failed with exit code $EXIT_CODE" >> "${SCRIPT_DIR}/cot_daily_cron.log"
fi

exit $EXIT_CODE
EOF

chmod +x "$WRAPPER_SCRIPT"

echo ""
echo "✅ Wrapper script created: $WRAPPER_SCRIPT"
echo ""

# Create cron job entries
# Primary: Run at specified time (e.g., 8:00 AM)
PRIMARY_CRON="$MINUTE $HOUR * * * $WRAPPER_SCRIPT"

# Catch-up: Run every 3 hours (in case computer was off at scheduled time)
# This ensures the report is sent when computer turns on
CATCHUP_CRON="0 */3 * * * $WRAPPER_SCRIPT"

# Check if cron jobs already exist
if crontab -l 2>/dev/null | grep -q "run_cot_daily.sh"; then
    echo "Removing existing cron jobs..."
    crontab -l 2>/dev/null | grep -v "run_cot_daily.sh" | crontab -
fi

# Add new cron jobs
echo "Adding cron jobs..."
(
    crontab -l 2>/dev/null
    echo "# COT Daily Email - Primary (scheduled time)"
    echo "$PRIMARY_CRON"
    echo "# COT Daily Email - Catch-up (runs every 3 hours if computer was off)"
    echo "$CATCHUP_CRON"
) | crontab -

echo ""
echo "========================================================================"
echo "SUCCESS! COT Daily Email Configured"
echo "========================================================================"
echo ""
echo "Primary Schedule: Every day at $EMAIL_TIME"
echo "Catch-up:         Every 3 hours (runs only if missed today)"
echo "Script:           $PYTHON_SCRIPT"
echo "Wrapper:          $WRAPPER_SCRIPT"
echo "Log File:         ${SCRIPT_DIR}/cot_daily_cron.log"
echo ""
echo "✅ CATCH-UP ENABLED: If your computer is off at $EMAIL_TIME, the task"
echo "   will run automatically when the computer turns on (checks every 3 hours)."
echo "   The wrapper script ensures the email is sent only ONCE per day."
echo ""
echo "========================================================================"
echo "IMPORTANT NEXT STEPS"
echo "========================================================================"
echo ""
echo "1. CREATE GMAIL APP PASSWORD:"
echo "   - Go to: https://myaccount.google.com/security"
echo "   - Enable 2-Step Verification"
echo "   - Search for 'App passwords'"
echo "   - Create password for 'Mail'"
echo "   - Copy the 16-character code"
echo ""
echo "2. UPDATE .env FILE:"
echo "   - Edit: ${SCRIPT_DIR}/.env"
echo "   - Find line: SMTP_PASSWORD=YOUR_16_CHAR_APP_PASSWORD_HERE"
echo "   - Replace with your App Password (no spaces)"
echo "   - Example: SMTP_PASSWORD=abcdabcdabcdabcd"
echo ""
echo "3. TEST THE SCRIPT:"
echo "   - Run: $WRAPPER_SCRIPT"
echo "   - Check your email: naga.kvv@gmail.com"
echo "   - Check log: ${SCRIPT_DIR}/cot_daily_cron.log"
echo ""
echo "4. VIEW CRON JOBS:"
echo "   - Run: crontab -l"
echo ""
echo "5. REMOVE CRON JOB (if needed):"
echo "   - Run: crontab -e"
echo "   - Delete the line containing 'run_cot_daily.sh'"
echo ""
echo "========================================================================"
echo ""

echo "Cron jobs successfully installed:"
crontab -l | grep "COT Daily Email" -A 1
echo ""
