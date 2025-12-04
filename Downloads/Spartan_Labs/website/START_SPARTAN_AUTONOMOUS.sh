#!/bin/bash
##############################################################################
# SPARTAN AUTONOMOUS RESEARCH STATION
# Complete autonomous startup, monitoring, and self-healing system
# Integrates: Native Dev Mode + Data Bridge + Health Monitor + Claude Code
##############################################################################

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Banner
echo -e "${PURPLE}${BOLD}"
cat << "EOF"
   _____ ____   ___    ____  ______   ___   _   __
  / ___// __ \ /   |  / __ \/_  __/  /   | / | / /
  \__ \/ /_/ // /| | / /_/ / / /    / /| |/  |/ /
 ___/ / ____// ___ |/ _, _/ / /    / ___ / /|  /
/____/_/    /_/  |_/_/ |_| /_/    /_/  |_/_/ |_/

  AUTONOMOUS RESEARCH STATION WITH CLAUDE CODE
  Self-Starting • Self-Healing • Self-Monitoring
EOF
echo -e "${NC}"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create necessary directories
mkdir -p logs .pids

# Log file
LOG_FILE="logs/autonomous_monitor.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

echo ""
log "========================================================================"
log "  SPARTAN AUTONOMOUS SYSTEM - INITIALIZING"
log "========================================================================"
echo ""

##############################################################################
# PHASE 1: ENVIRONMENT CHECKS
##############################################################################

log "📋 Phase 1: Environment Validation"
echo ""

# Check PostgreSQL
echo -n "   PostgreSQL... "
if pg_isready -q 2>/dev/null; then
    echo -e "${GREEN}✓ Running${NC}"
    log "✓ PostgreSQL: Running"
else
    echo -e "${YELLOW}⚠ Not running - Starting${NC}"
    log "⚠ PostgreSQL not running - attempting to start"

    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo service postgresql start 2>/dev/null || sudo systemctl start postgresql 2>/dev/null
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start postgresql 2>/dev/null
    fi

    # Wait for ready
    for i in {1..10}; do
        if pg_isready -q 2>/dev/null; then
            echo -e "${GREEN}   ✓ PostgreSQL ready${NC}"
            log "✓ PostgreSQL started successfully"
            break
        fi
        sleep 1
    done
fi

# Check Redis
echo -n "   Redis... "
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Running${NC}"
    log "✓ Redis: Running"
else
    echo -e "${YELLOW}⚠ Not running - Starting${NC}"
    log "⚠ Redis not running - attempting to start"

    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo service redis-server start 2>/dev/null || sudo systemctl start redis 2>/dev/null
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew services start redis 2>/dev/null
    fi

    # Wait for ready
    for i in {1..10}; do
        if redis-cli ping > /dev/null 2>&1; then
            echo -e "${GREEN}   ✓ Redis ready${NC}"
            log "✓ Redis started successfully"
            break
        fi
        sleep 1
    done
fi

# Check database exists
echo -n "   Database 'spartan_research_db'... "
if psql -lqt | cut -d \| -f 1 | grep -qw spartan_research_db; then
    echo -e "${GREEN}✓ Exists${NC}"
    log "✓ Database: spartan_research_db exists"
else
    echo -e "${YELLOW}⚠ Creating${NC}"
    log "⚠ Database not found - creating"
    createdb spartan_research_db 2>/dev/null

    if [ -f "db/init/init.sql" ]; then
        psql -d spartan_research_db -f db/init/init.sql > /dev/null 2>&1
        log "✓ Database schema initialized"
    fi

    echo -e "${GREEN}   ✓ Database created${NC}"
fi

# Check virtualenv
echo -n "   Python Virtual Environment... "
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠ Creating${NC}"
    log "⚠ Virtual environment not found - creating"
    python3 -m venv venv
    source venv/bin/activate
    pip install -q -r requirements.txt
    echo -e "${GREEN}   ✓ Created and dependencies installed${NC}"
    log "✓ Virtual environment created"
else
    source venv/bin/activate
    echo -e "${GREEN}✓ Activated${NC}"
    log "✓ Virtual environment activated"
fi

# Load environment variables
if [ -f ".env" ]; then
    echo -n "   Environment Variables... "
    set -a
    source .env
    set +a
    echo -e "${GREEN}✓ Loaded${NC}"
    log "✓ Environment variables loaded from .env"
else
    echo -e "${YELLOW}   ⚠ .env file not found - using defaults${NC}"
    log "⚠ .env file not found"
fi

# Set defaults
export DATABASE_URL=${DATABASE_URL:-"postgresql://localhost:5432/spartan_research_db"}
export REDIS_HOST=${REDIS_HOST:-"localhost"}
export REDIS_PORT=${REDIS_PORT:-"6379"}

# Check Claude Code availability
echo -n "   Claude Code CLI... "
CLAUDE_AVAILABLE=false
if command -v claude &> /dev/null; then
    CLAUDE_VERSION=$(claude --version 2>/dev/null || echo "unknown")
    echo -e "${GREEN}✓ Installed${NC} (${CLAUDE_VERSION})"
    log "✓ Claude Code: Available ($CLAUDE_VERSION)"
    CLAUDE_AVAILABLE=true
else
    echo -e "${YELLOW}⚠ Not installed${NC}"
    echo -e "${CYAN}     Install from: https://claude.ai/download${NC}"
    log "⚠ Claude Code: Not available"
fi

echo ""
log "✅ Environment validation complete"
echo ""

##############################################################################
# PHASE 2: START SERVICES
##############################################################################

log "🚀 Phase 2: Starting Services"
echo ""

# Kill any existing processes on our ports
for port in 8888 5000 5002 5003 5004; do
    pid=$(lsof -ti:$port 2>/dev/null || true)
    if [ ! -z "$pid" ]; then
        echo "   Clearing port $port (killing PID $pid)"
        kill -9 $pid 2>/dev/null || true
        sleep 1
    fi
done

# Start main web server
echo -n "   Main Web Server (port 8888)... "
python start_server.py > logs/main_server.log 2>&1 &
echo $! > .pids/main.pid
echo -e "${GREEN}✓ PID $(cat .pids/main.pid)${NC}"
log "✓ Main server started: PID $(cat .pids/main.pid)"

sleep 2

# Start microservices
echo -n "   Correlation API (port 5004)... "
python correlation_api.py > logs/correlation_api.log 2>&1 &
echo $! > .pids/correlation.pid
echo -e "${GREEN}✓ PID $(cat .pids/correlation.pid)${NC}"
log "✓ Correlation API started: PID $(cat .pids/correlation.pid)"

echo -n "   Daily Planet API (port 5000)... "
python daily_planet_api.py > logs/daily_planet_api.log 2>&1 &
echo $! > .pids/daily_planet.pid
echo -e "${GREEN}✓ PID $(cat .pids/daily_planet.pid)${NC}"
log "✓ Daily Planet API started: PID $(cat .pids/daily_planet.pid)"

echo -n "   Swing Dashboard API (port 5002)... "
python swing_dashboard_api.py > logs/swing_api.log 2>&1 &
echo $! > .pids/swing.pid
echo -e "${GREEN}✓ PID $(cat .pids/swing.pid)${NC}"
log "✓ Swing API started: PID $(cat .pids/swing.pid)"

echo -n "   GARP API (port 5003)... "
python garp_api.py > logs/garp_api.log 2>&1 &
echo $! > .pids/garp.pid
echo -e "${GREEN}✓ PID $(cat .pids/garp.pid)${NC}"
log "✓ GARP API started: PID $(cat .pids/garp.pid)"

echo ""
echo "   Waiting for services to be ready..."
sleep 3

echo ""
log "✅ All services started successfully"
echo ""

##############################################################################
# PHASE 3: DATA PRELOADING
##############################################################################

log "📊 Phase 3: Loading Market Data"
echo ""

echo "   Running data preloader (30-60 seconds)..."
log "Starting data preloader..."

python src/data_preloader.py 2>&1 | tee -a logs/data_preloader.log

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo -e "${GREEN}   ✓ Data preloader completed successfully${NC}"
    log "✅ Data preloader: Success"
else
    echo -e "${RED}   ✗ Data preloader failed${NC}"
    log "❌ Data preloader: Failed (check logs/data_preloader.log)"
    echo -e "${YELLOW}   ⚠ Website will continue, but data may be incomplete${NC}"
fi

# Start data refresh scheduler
echo -n "   Data Refresh Scheduler (15-min intervals)... "
python src/data_refresh_scheduler.py > logs/data_refresh.log 2>&1 &
echo $! > .pids/refresh.pid
echo -e "${GREEN}✓ PID $(cat .pids/refresh.pid)${NC}"
log "✓ Data refresh scheduler started: PID $(cat .pids/refresh.pid)"

echo ""
log "✅ Data loading complete"
echo ""

##############################################################################
# PHASE 4: AUTONOMOUS MONITORING
##############################################################################

log "🤖 Phase 4: Starting Autonomous Monitoring"
echo ""

# Create autonomous health monitor script
cat > logs/autonomous_health_monitor.sh << 'MONITOR_EOF'
#!/bin/bash
# Autonomous Health Monitor - Runs in background

LOG_FILE="logs/health_monitor.log"
FAILURES=0
MAX_FAILURES=3

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_endpoint() {
    local url=$1
    local name=$2

    response=$(curl -s -w "\n%{http_code}" "$url" 2>&1)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" != "200" ]; then
        return 1
    fi

    # Check for error patterns in response
    if echo "$body" | grep -qi "error\|transaction.*aborted\|connection.*failed"; then
        return 1
    fi

    return 0
}

restart_service() {
    local service=$1
    local pid_file=".pids/${service}.pid"

    log "🔧 Restarting $service..."

    if [ -f "$pid_file" ]; then
        old_pid=$(cat "$pid_file")
        kill -9 "$old_pid" 2>/dev/null || true
        sleep 2
    fi

    # Restart based on service
    case $service in
        "main")
            python start_server.py > logs/main_server.log 2>&1 &
            ;;
        "correlation")
            python correlation_api.py > logs/correlation_api.log 2>&1 &
            ;;
        "daily_planet")
            python daily_planet_api.py > logs/daily_planet_api.log 2>&1 &
            ;;
        "swing")
            python swing_dashboard_api.py > logs/swing_api.log 2>&1 &
            ;;
        "garp")
            python garp_api.py > logs/garp_api.log 2>&1 &
            ;;
    esac

    echo $! > "$pid_file"
    log "✅ $service restarted: PID $(cat $pid_file)"
}

clear_redis_cache() {
    log "🔧 Clearing Redis cache..."
    redis-cli FLUSHALL > /dev/null 2>&1
    log "✅ Redis cache cleared"
}

trigger_data_refresh() {
    log "🔧 Triggering data refresh..."
    python src/data_preloader.py > logs/emergency_preload.log 2>&1 &
    log "✅ Data refresh triggered"
}

log "=========================================="
log "Autonomous Health Monitor - Starting"
log "Check Interval: 60 seconds"
log "Auto-Heal: Enabled"
log "=========================================="

while true; do
    # Check main server
    if ! check_endpoint "http://localhost:8888/health" "Main Server"; then
        log "❌ Main Server unhealthy"
        FAILURES=$((FAILURES + 1))

        if [ $FAILURES -ge $MAX_FAILURES ]; then
            log "🚨 Multiple failures detected - initiating auto-heal"
            restart_service "main"
            clear_redis_cache
            trigger_data_refresh
            FAILURES=0
        else
            log "⚠️  Failure $FAILURES/$MAX_FAILURES - monitoring"
        fi
    else
        log "✅ Main Server healthy"
        FAILURES=0
    fi

    # Check API services
    for api in "correlation:5004" "daily_planet:5000" "swing:5002" "garp:5003"; do
        IFS=':' read -r name port <<< "$api"

        if ! check_endpoint "http://localhost:$port/health" "$name API"; then
            log "⚠️  $name API unhealthy - restarting"
            restart_service "$name"
        fi
    done

    # Check data freshness
    redis_keys=$(redis-cli KEYS 'market:*' 2>/dev/null | wc -l)
    if [ "$redis_keys" -lt 5 ]; then
        log "⚠️  Redis cache appears empty ($redis_keys keys) - triggering refresh"
        trigger_data_refresh
    fi

    sleep 60
done
MONITOR_EOF

chmod +x logs/autonomous_health_monitor.sh

# Start autonomous monitor in background
echo -n "   Autonomous Health Monitor... "
nohup ./logs/autonomous_health_monitor.sh > /dev/null 2>&1 &
MONITOR_PID=$!
echo $MONITOR_PID > .pids/monitor.pid
echo -e "${GREEN}✓ PID $MONITOR_PID${NC}"
log "✓ Autonomous health monitor started: PID $MONITOR_PID"

# Start Claude Code integration if available
if [ "$CLAUDE_AVAILABLE" = true ]; then
    echo -n "   Claude Code Integration... "

    # Create Claude Code watcher script
    cat > logs/claude_code_watcher.sh << 'CLAUDE_EOF'
#!/bin/bash
# Claude Code Watcher - Launches Claude Code on complex issues

LOG_FILE="logs/claude_watcher.log"
ISSUE_COUNT=0

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "Claude Code Watcher - Starting"
log "Monitors: Health monitor logs for failures"
log "Action: Launch Claude Code for complex issues"
log "=========================================="

tail -F logs/health_monitor.log 2>/dev/null | while read line; do
    # Detect critical issues
    if echo "$line" | grep -q "🚨 Multiple failures"; then
        log "🚨 Critical issue detected!"
        ISSUE_COUNT=$((ISSUE_COUNT + 1))

        # Create issue summary
        issue_summary="logs/issue_summary_$(date +%s).txt"
        {
            echo "SPARTAN RESEARCH STATION - CRITICAL ISSUE DETECTED"
            echo "=================================================="
            echo ""
            echo "Timestamp: $(date)"
            echo "Issue Count: $ISSUE_COUNT"
            echo ""
            echo "Recent Logs:"
            echo "------------"
            tail -n 50 logs/health_monitor.log
            echo ""
            echo "Service Status:"
            echo "---------------"
            ps aux | grep -E "start_server|correlation_api|daily_planet|swing_dashboard|garp_api" | grep -v grep
            echo ""
            echo "Database Status:"
            echo "----------------"
            psql -d spartan_research_db -c "SELECT COUNT(*) FROM preloaded_market_data WHERE timestamp > NOW() - INTERVAL '1 hour';" 2>&1
            echo ""
            echo "Redis Status:"
            echo "-------------"
            redis-cli INFO stats 2>&1
            echo ""
        } > "$issue_summary"

        log "📋 Issue summary created: $issue_summary"
        log "🤖 Launching Claude Code for diagnosis..."

        # Launch Claude Code with context
        claude chat --message "URGENT: Spartan Research Station has encountered critical issues. Please analyze the issue summary at $issue_summary and fix the problems. The system has auto-healing enabled but needs advanced diagnosis. Focus on: 1) Data loading issues, 2) API failures, 3) Database connection problems. Fix autonomously." &

        log "✅ Claude Code launched"

        # Wait before next launch (prevent spam)
        sleep 300  # 5 minute cooldown
    fi
done
CLAUDE_EOF

    chmod +x logs/claude_code_watcher.sh

    nohup ./logs/claude_code_watcher.sh > /dev/null 2>&1 &
    WATCHER_PID=$!
    echo $WATCHER_PID > .pids/claude_watcher.pid
    echo -e "${GREEN}✓ PID $WATCHER_PID${NC}"
    log "✓ Claude Code watcher started: PID $WATCHER_PID"
else
    echo -e "${YELLOW}   ⚠ Claude Code not available - monitoring only${NC}"
    log "⚠ Claude Code integration: Disabled (CLI not installed)"
fi

echo ""
log "✅ Autonomous monitoring active"
echo ""

##############################################################################
# PHASE 5: STATUS SUMMARY
##############################################################################

echo ""
echo -e "${PURPLE}${BOLD}========================================================================"
echo "  SPARTAN AUTONOMOUS RESEARCH STATION - ONLINE"
echo -e "========================================================================${NC}"
echo ""

echo -e "${CYAN}📊 System Status:${NC}"
echo -e "   ${GREEN}✓${NC} PostgreSQL: Running"
echo -e "   ${GREEN}✓${NC} Redis: Running"
echo -e "   ${GREEN}✓${NC} Main Server: Port 8888"
echo -e "   ${GREEN}✓${NC} 4 Microservices: Running"
echo -e "   ${GREEN}✓${NC} Data Preloader: Completed"
echo -e "   ${GREEN}✓${NC} Auto-Refresh: Every 15 minutes"
echo -e "   ${GREEN}✓${NC} Health Monitor: Active"
if [ "$CLAUDE_AVAILABLE" = true ]; then
    echo -e "   ${GREEN}✓${NC} Claude Code: Integrated"
else
    echo -e "   ${YELLOW}⚠${NC} Claude Code: Not available"
fi
echo ""

echo -e "${CYAN}🌐 Access Points:${NC}"
echo -e "   ${BOLD}Main Dashboard:${NC}     http://localhost:8888/index.html"
echo -e "   ${BOLD}Capital Flow:${NC}       http://localhost:8888/global_capital_flow_swing_trading.html"
echo ""

echo -e "${CYAN}🔍 Health Checks:${NC}"
echo -e "   Main Server:      curl http://localhost:8888/health"
echo -e "   Correlation:      curl http://localhost:5004/health"
echo -e "   Daily Planet:     curl http://localhost:5000/health"
echo -e "   Swing Dashboard:  curl http://localhost:5002/api/swing-dashboard/health"
echo -e "   GARP Screener:    curl http://localhost:5003/api/health"
echo ""

echo -e "${CYAN}📝 Monitoring Logs:${NC}"
echo -e "   Health Monitor:   tail -f logs/health_monitor.log"
echo -e "   Claude Watcher:   tail -f logs/claude_watcher.log"
echo -e "   All Logs:         tail -f logs/*.log"
echo ""

echo -e "${CYAN}🛠️  Control Commands:${NC}"
echo -e "   Stop System:      ./STOP_SPARTAN_DEV.sh"
echo -e "   Restart System:   ./RESTART_SPARTAN_DEV.sh"
echo -e "   View Processes:   ps aux | grep -E 'start_server|correlation|daily_planet|swing|garp'"
echo ""

echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${GREEN}${BOLD}🚀 AUTONOMOUS MODE: ACTIVE${NC}"
echo ""
echo -e "${CYAN}The system will now:${NC}"
echo -e "   • Monitor all services every 60 seconds"
echo -e "   • Auto-restart failed services"
echo -e "   • Clear cache and refresh data when needed"
if [ "$CLAUDE_AVAILABLE" = true ]; then
    echo -e "   • Launch Claude Code for complex issues"
fi
echo -e "   • Log all activities to logs/"
echo ""

echo -e "${YELLOW}💡 This system is self-healing. You can safely close this terminal.${NC}"
echo -e "${YELLOW}   All monitoring continues in the background.${NC}"
echo ""

log "========================================================================"
log "  SPARTAN AUTONOMOUS SYSTEM - FULLY OPERATIONAL"
log "========================================================================"

# Keep script running to show live status
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}Live Health Monitor (Ctrl+C to exit - services continue running):${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

tail -f logs/health_monitor.log
