#!/bin/bash
# Autonomous Health Monitor - Checks API and auto-fixes issues

LOG_FILE="/tmp/spartan_health_monitor.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_and_fix() {
    # Test API endpoint
    response=$(curl -s http://localhost:8888/api/market/symbol/SPY 2>&1)

    # Check for errors
    if echo "$response" | grep -qi "error\|transaction.*aborted\|connection"; then
        log "❌ ERROR DETECTED: $response"
        log "🔧 AUTO-FIXING: Restarting web server..."

        docker restart spartan_web
        sleep 10

        # Verify fix
        verify=$(curl -s http://localhost:8888/api/market/indices 2>&1)
        if echo "$verify" | grep -qi "error"; then
            log "❌ RESTART FAILED: $verify"
            log "🔧 Trying database connection reset..."
            docker exec spartan_postgres psql -U spartan_user -d spartan_research -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'spartan_research' AND pid <> pg_backend_pid();" >/dev/null 2>&1
            docker restart spartan_web
            sleep 10
        else
            log "✅ AUTO-FIX SUCCESSFUL: API responding normally"
        fi
    elif echo "$response" | grep -qi "\"data\""; then
        log "✅ HEALTHY: API returning data correctly"
    else
        log "⚠️  UNKNOWN STATE: $response"
    fi
}

log "=========================================="
log "Spartan Health Monitor - Starting"
log "=========================================="

# Run continuous monitoring
while true; do
    check_and_fix
    sleep 60  # Check every minute
done
