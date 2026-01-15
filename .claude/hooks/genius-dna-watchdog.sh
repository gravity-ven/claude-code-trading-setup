#!/usr/bin/env bash
# Genius DNA Watchdog - Continuous monitoring daemon with infinite loop
# Monitors metrics freshness, restarts learning daemon, and sources bashrc on changes

# Configuration
GENIUS_DNA_PATH="/mnt/c/Users/Quantum/genius-dna"
METRICS_FILE="/mnt/d/genius-dna-files/latest_metrics.json"
WATCHDOG_LOG="/tmp/genius_dna_watchdog.log"
MAX_AGE_MINUTES=60  # Consider stale if older than 1 hour
CHECK_INTERVAL=30   # Check every 30 seconds
BASHRC_FILES=(
    "/mnt/c/Users/Quantum/.bashrc"
    "/mnt/c/Users/Quantum/.bashrc.d/genius-dna-gemini.sh"
    "/home/spartan/.bashrc"
)

# Track last modification times for bashrc files
declare -A BASHRC_MTIMES

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

# Function to get file modification time
get_mtime() {
    local file="$1"
    [ -f "$file" ] && stat -c %Y "$file" 2>/dev/null || echo "0"
}

# Function to check and source bashrc changes
check_bashrc_changes() {
    local changes_detected=false

    for bashrc_file in "${BASHRC_FILES[@]}"; do
        if [ ! -f "$bashrc_file" ]; then
            continue
        fi

        local current_mtime=$(get_mtime "$bashrc_file")
        local stored_mtime="${BASHRC_MTIMES[$bashrc_file]:-0}"

        if [ "$current_mtime" != "$stored_mtime" ]; then
            log "🔄 Detected change in: $bashrc_file"

            # Source the file
            if source "$bashrc_file" 2>/dev/null; then
                log "✅ Sourced: $bashrc_file"
                changes_detected=true
            else
                log "⚠️  Failed to source: $bashrc_file"
            fi

            # Update stored mtime
            BASHRC_MTIMES[$bashrc_file]="$current_mtime"
        fi
    done

    if [ "$changes_detected" = true ]; then
        log "📋 Bashrc changes applied - environment refreshed"
    fi
}

# Function to initialize bashrc tracking
init_bashrc_tracking() {
    for bashrc_file in "${BASHRC_FILES[@]}"; do
        if [ -f "$bashrc_file" ]; then
            BASHRC_MTIMES[$bashrc_file]=$(get_mtime "$bashrc_file")
        fi
    done
    log "✅ Initialized bashrc tracking for ${#BASHRC_MTIMES[@]} files"
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

# Main watchdog check
check_watchdog() {
    # Check if genius-dna exists
    if [ ! -d "$GENIUS_DNA_PATH" ]; then
        log "⚠️  Genius DNA path not found: $GENIUS_DNA_PATH"
        return
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

# Main infinite loop
main_loop() {
    log "🚀 Genius DNA Watchdog started (infinite loop mode)"
    log "📊 Check interval: ${CHECK_INTERVAL}s"
    log "⏰ Staleness threshold: ${MAX_AGE_MINUTES} minutes"

    # Initialize bashrc tracking
    init_bashrc_tracking

    # Infinite loop
    while true; do
        # Check for bashrc changes
        check_bashrc_changes

        # Check watchdog conditions
        check_watchdog

        # Sleep before next check
        sleep "$CHECK_INTERVAL"
    done
}

# Trap signals for graceful shutdown
trap 'log "🛑 Watchdog received shutdown signal"; exit 0' SIGINT SIGTERM

# Check if running in daemon mode or one-shot mode
if [ "${GENIUS_WATCHDOG_MODE:-oneshot}" = "daemon" ]; then
    # Daemon mode - infinite loop
    main_loop
else
    # One-shot mode (for hooks)
    check_bashrc_changes
    check_watchdog
    exit 0
fi
