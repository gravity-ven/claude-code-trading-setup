#!/usr/bin/env bash
#
# Spartan Research Station - Agent Persistence Script
# ====================================================
#
# This script ensures agents stay running as long as the computer is on.
# Add to crontab to run every 5 minutes:
#   */5 * * * * /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/KEEP_AGENTS_RUNNING.sh
#

WEBSITE_DIR="/mnt/c/Users/Quantum/Downloads/Spartan_Labs/website"
LOG_FILE="$WEBSITE_DIR/agent_persistence.log"

cd "$WEBSITE_DIR" || exit 1

echo "[$(date)] Checking agent status..." >> "$LOG_FILE"

# Check if agent orchestrator is running
if ! pgrep -f "agent_orchestrator.py" > /dev/null; then
    echo "[$(date)] ⚠️  Agent orchestrator not running - starting now..." >> "$LOG_FILE"

    # Check if PostgreSQL is running
    if ! pg_isready -q; then
        echo "[$(date)] ❌ PostgreSQL not running - cannot start agents" >> "$LOG_FILE"
        exit 1
    fi

    # Check if Redis is running
    if ! redis-cli ping > /dev/null 2>&1; then
        echo "[$(date)] ❌ Redis not running - cannot start agents" >> "$LOG_FILE"
        exit 1
    fi

    # Start agent orchestrator
    python3 agent_orchestrator.py >> agent_orchestrator.log 2>&1 &
    echo "[$(date)] ✅ Agent orchestrator started (PID: $!)" >> "$LOG_FILE"
else
    AGENT_PID=$(pgrep -f "agent_orchestrator.py")
    echo "[$(date)] ✅ Agent orchestrator running (PID: $AGENT_PID)" >> "$LOG_FILE"
fi

# Check if data scanners are running
if ! pgrep -f "data_guardian_agent_full.py" > /dev/null; then
    echo "[$(date)] ⚠️  Data guardian scanner not running - starting now..." >> "$LOG_FILE"
    python3 data_guardian_agent_full.py >> data_guardian.log 2>&1 &
    echo "[$(date)] ✅ Data guardian started (PID: $!)" >> "$LOG_FILE"
fi

if ! pgrep -f "comprehensive_macro_scanner.py" > /dev/null; then
    echo "[$(date)] ⚠️  Comprehensive scanner not running - starting now..." >> "$LOG_FILE"
    python3 comprehensive_macro_scanner.py >> comprehensive_scanner.log 2>&1 &
    echo "[$(date)] ✅ Comprehensive scanner started (PID: $!)" >> "$LOG_FILE"
fi

# Check if website data validator is running
if ! pgrep -f "website_data_validator_agent.py" > /dev/null; then
    echo "[$(date)] ⚠️  Website data validator not running - starting now..." >> "$LOG_FILE"
    python3 agents/website_data_validator_agent.py >> website_data_validation.log 2>&1 &
    echo "[$(date)] ✅ Website data validator started (PID: $!)" >> "$LOG_FILE"
fi

# Check if composite data refresh agent is running
if ! pgrep -f "composite_data_refresh_agent.py" > /dev/null; then
    echo "[$(date)] ⚠️  Composite data refresh agent not running - starting now..." >> "$LOG_FILE"
    python3 agents/composite_data_refresh_agent.py >> composite_refresh.log 2>&1 &
    echo "[$(date)] ✅ Composite data refresh agent started (PID: $!)" >> "$LOG_FILE"
fi

# Check if web server is running
if ! pgrep -f "start_server.py" > /dev/null; then
    echo "[$(date)] ⚠️  Web server not running - starting now..." >> "$LOG_FILE"
    python3 start_server.py >> start_server.log 2>&1 &
    echo "[$(date)] ✅ Web server started (PID: $!)" >> "$LOG_FILE"
fi

echo "[$(date)] All services checked" >> "$LOG_FILE"
