#!/usr/bin/env bash
# Genius DNA Watchdog - Auto-restart daemon if data is stale
# Monitors metrics freshness and restarts learning daemon automatically

# Configuration
GENIUS_DNA_PATH="/mnt/c/Users/Quantum/genius-dna"
METRICS_FILE="/mnt/d/genius-dna-files/latest_metrics.json"
WATCHDOG_LOG="/tmp/genius_dna_watchdog.log"
MAX_AGE_MINUTES=60  # Consider stale if older than 1 hour

# Function to log with timestamp
log() {
    echo "$(date -Iseconds): $1" >> "$WATCHDOG_LOG"
}

# Function to check if daemon is running
is_daemon_running() {
    pgrep -f "learning_daemon.py" > /dev/null 2>&1
    return $?
}

# Function to get file age in minutes
get_file_age_minutes() {
    local file="$1"
    if [ ! -f "$file" ]; then
        echo "999999"  # File doesn't exist = very old
        return
    fi

    local file_time=$(stat -c %Y "$file" 2>/dev/null)
    local current_time=$(date +%s)
    local age_seconds=$((current_time - file_time))
    local age_minutes=$((age_seconds / 60))
    echo "$age_minutes"
}

# Function to restart daemon
restart_daemon() {
    log "🔄 Restarting learning daemon (data was stale)"

    # Kill existing daemon if running
    pkill -f "learning_daemon.py" 2>/dev/null
    sleep 1

    # Start fresh daemon
    cd "$GENIUS_DNA_PATH"
    nohup python3 learning_daemon.py start >> "$WATCHDOG_LOG" 2>&1 &
    sleep 2

    # Export fresh metrics
    python3 export_metrics.py >> "$WATCHDOG_LOG" 2>&1

    if is_daemon_running; then
        log "✅ Learning daemon restarted successfully"
        return 0
    else
        log "❌ Failed to restart learning daemon"
        return 1
    fi
}

# Main watchdog logic
main() {
    # Check if genius-dna exists
    if [ ! -d "$GENIUS_DNA_PATH" ]; then
        log "⚠️  Genius DNA path not found: $GENIUS_DNA_PATH"
        exit 0
    fi

    # Check metrics file age
    local age_minutes=$(get_file_age_minutes "$METRICS_FILE")

    if [ "$age_minutes" -gt "$MAX_AGE_MINUTES" ]; then
        log "⚠️  Metrics stale (${age_minutes} minutes old, threshold: ${MAX_AGE_MINUTES})"

        # Check if daemon is running
        if is_daemon_running; then
            log "⚠️  Daemon running but data stale - forcing restart"
            restart_daemon
        else
            log "⚠️  Daemon not running - starting now"
            restart_daemon
        fi
    else
        # Data is fresh, but verify daemon is running
        if ! is_daemon_running; then
            log "⚠️  Data fresh but daemon not running - starting daemon"
            restart_daemon
        fi
    fi
}

# Run main logic
main

exit 0
