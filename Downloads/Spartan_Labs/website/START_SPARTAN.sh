#!/usr/bin/env bash

##############################################################################
# Spartan Labs Research Station - Universal Startup Script
# Works on: macOS, Linux, Windows WSL
# Starts: All services + Autonomous Monitor + Claude Code Integration
##############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${PURPLE}"
cat << "EOF"
   _____ ____  ___    ____  _________    _   __
  / ___// __ \/   |  / __ \/_  __/   |  / | / /
  \__ \/ /_/ / /| | / /_/ / / / / /| | /  |/ /
 ___/ / ____/ ___ |/ _, _/ / / / ___ |/ /|  /
/____/_/   /_/  |_/_/ |_| /_/ /_/  |_/_/ |_/

    RESEARCH STATION + AUTONOMOUS MONITOR
          🛡️  Self-Healing Intelligence
            🤖 Claude Code Integration
EOF
echo -e "${NC}"

# Get the absolute path to this script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${CYAN}📂 Working Directory: ${GREEN}$SCRIPT_DIR${NC}"

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macOS"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if grep -qi microsoft /proc/version 2>/dev/null; then
            echo "WSL"
        else
            echo "Linux"
        fi
    else
        echo "Unknown"
    fi
}

OS=$(detect_os)
echo -e "${CYAN}🖥️  Detected OS: ${GREEN}$OS${NC}"
echo ""

# Check prerequisites
echo -e "${BLUE}📋 Checking Prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found${NC}"
    echo "Please install Docker Desktop:"
    echo "  macOS:   https://docs.docker.com/desktop/install/mac-install/"
    echo "  Linux:   https://docs.docker.com/engine/install/"
    echo "  Windows: https://docs.docker.com/desktop/install/windows-install/"
    exit 1
fi
echo -e "${GREEN}✅ Docker installed${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose installed${NC}"

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker daemon not running${NC}"
    echo "Please start Docker Desktop and try again"
    exit 1
fi
echo -e "${GREEN}✅ Docker daemon running${NC}"

# Check Claude Code
CLAUDE_AVAILABLE=false
if command -v claude &> /dev/null; then
    echo -e "${GREEN}✅ Claude Code installed${NC}"
    CLAUDE_AVAILABLE=true
elif [ -f "/usr/local/bin/claude" ] || [ -f "$HOME/.local/bin/claude" ]; then
    echo -e "${GREEN}✅ Claude Code installed${NC}"
    CLAUDE_AVAILABLE=true
else
    echo -e "${YELLOW}⚠️  Claude Code not found${NC}"
    echo -e "${CYAN}   Install from: https://claude.ai/download${NC}"
    echo -e "${CYAN}   The system will still work, but without Claude Code integration${NC}"
    CLAUDE_AVAILABLE=false
fi

# Check .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo "Creating .env from template..."
    cp .env.example .env
    echo -e "${CYAN}📝 Please edit .env and add your API keys:${NC}"
    echo "   - ANTHROPIC_API_KEY (for Claude AI monitoring)"
    echo "   - FRED_API_KEY (for economic data)"
    echo "   - Other API keys as needed"
    echo ""
    echo -e "${YELLOW}Press Enter when ready to continue...${NC}"
    read
fi
echo -e "${GREEN}✅ .env file present${NC}"

# Load environment variables
set -a
source .env
set +a

# Check for ANTHROPIC_API_KEY
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  ANTHROPIC_API_KEY not set${NC}"
    echo "   Website Monitor will use fallback logic without Claude AI"
    echo "   For intelligent auto-healing, add ANTHROPIC_API_KEY to .env"
fi

echo ""
echo -e "${BLUE}🚀 Starting Spartan Research Station...${NC}"
echo ""

# Stop any existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose down 2>/dev/null || true

# Build images (only if needed)
echo -e "${BLUE}🔨 Building Docker images...${NC}"
docker-compose build --quiet

# Start services
echo -e "${GREEN}▶️  Starting all services + monitor...${NC}"
echo ""

# Use docker compose v2 if available, otherwise fall back to docker-compose
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

$DOCKER_COMPOSE up -d

echo ""
echo -e "${GREEN}✨ Startup complete!${NC}"
echo ""

# Wait for services to be healthy
echo -e "${CYAN}🏥 Waiting for services to be healthy...${NC}"
sleep 5

# Check service status
echo ""
echo -e "${BLUE}📊 Service Status:${NC}"
echo ""

services=(
    "spartan-research-station:8888"
    "spartan-postgres:5432"
    "spartan-redis:6379"
    "spartan-correlation-api:5004"
    "spartan-daily-planet-api:5000"
    "spartan-swing-api:5002"
    "spartan-garp-api:5003"
    "spartan-website-monitor:N/A"
)

for service_port in "${services[@]}"; do
    service="${service_port%:*}"
    port="${service_port#*:}"

    if docker ps --format '{{.Names}}' | grep -q "^$service$"; then
        status=$(docker inspect --format='{{.State.Status}}' "$service" 2>/dev/null || echo "unknown")
        if [ "$status" == "running" ]; then
            echo -e "  ${GREEN}✅${NC} $service ${CYAN}($port)${NC} - ${GREEN}running${NC}"
        else
            echo -e "  ${YELLOW}⚠️${NC}  $service ${CYAN}($port)${NC} - ${YELLOW}$status${NC}"
        fi
    else
        echo -e "  ${RED}❌${NC} $service - ${RED}not found${NC}"
    fi
done

echo ""
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 Spartan Research Station is LIVE!${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${CYAN}📍 Access Points:${NC}"
echo ""
echo -e "   ${GREEN}🌐 Main Dashboard:${NC}     http://localhost:8888"
echo -e "   ${GREEN}📊 Capital Flows:${NC}      http://localhost:8888/global_capital_flow_swing_trading.html"
echo -e "   ${GREEN}📰 Daily Planet:${NC}       http://localhost:8888/daily_planet.html"
echo -e "   ${GREEN}💹 GARP Screener:${NC}      http://localhost:8888/garp.html"
echo ""
echo -e "${CYAN}🛡️  Autonomous Monitor:${NC}"
echo -e "   ${GREEN}Status:${NC} Monitoring all services every 30 seconds"
echo -e "   ${GREEN}Claude AI:${NC} $( [ -n "$ANTHROPIC_API_KEY" ] && echo 'Enabled ✅' || echo 'Disabled ⚠️' )"
echo -e "   ${GREEN}Auto-Heal:${NC} Enabled ✅"
echo -e "   ${GREEN}Logs:${NC} ./logs/website_monitor.log"
echo ""
echo -e "${CYAN}🔧 Management Commands:${NC}"
echo ""
echo -e "   ${YELLOW}View logs:${NC}          docker-compose logs -f"
echo -e "   ${YELLOW}Monitor logs:${NC}       docker-compose logs -f spartan-website-monitor"
echo -e "   ${YELLOW}Stop all:${NC}           docker-compose down"
echo -e "   ${YELLOW}Restart service:${NC}    docker-compose restart <service-name>"
echo -e "   ${YELLOW}View status:${NC}        docker-compose ps"
echo ""

# Create monitoring fifo for agent-to-Claude communication
MONITOR_FIFO="$SCRIPT_DIR/logs/monitor_alerts.fifo"
mkdir -p "$SCRIPT_DIR/logs"

if [ ! -p "$MONITOR_FIFO" ]; then
    mkfifo "$MONITOR_FIFO" 2>/dev/null || true
fi

# Create alert monitoring script
cat > "$SCRIPT_DIR/logs/alert_watcher.sh" << 'ALERT_SCRIPT'
#!/usr/bin/env bash

# Alert watcher - monitors for critical issues and invokes Claude Code

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

FIFO="$SCRIPT_DIR/monitor_alerts.fifo"
CLAUDE_TRIGGER="$SCRIPT_DIR/claude_trigger.txt"

echo "🔍 Alert Watcher started - monitoring for critical issues..."

# Watch Docker logs for critical errors
docker-compose logs -f spartan-website-monitor 2>/dev/null | while read -r line; do
    # Detect critical errors that need Claude intervention
    if echo "$line" | grep -qE "(CRITICAL|container_unhealthy|healing_failed|auto_heal_failed)"; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ALERT: $line" | tee -a "$SCRIPT_DIR/critical_alerts.log"

        # Write to trigger file for Claude
        echo "$line" >> "$CLAUDE_TRIGGER"

        # Check if Claude should be invoked
        FAILURE_COUNT=$(grep -c "healing_failed\|auto_heal_failed" "$SCRIPT_DIR/critical_alerts.log" 2>/dev/null || echo 0)

        if [ "$FAILURE_COUNT" -ge 2 ]; then
            echo "⚠️  Multiple healing failures detected - Claude Code intervention needed"
            echo "INVOKE_CLAUDE: $line" > "$FIFO" 2>/dev/null || true
        fi
    fi
done
ALERT_SCRIPT

chmod +x "$SCRIPT_DIR/logs/alert_watcher.sh"

# Start Claude Code integration if available
if [ "$CLAUDE_AVAILABLE" = true ]; then
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}🤖 Claude Code Integration${NC}"
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}Starting Claude Code in autonomous monitoring mode...${NC}"
    echo ""

    # Create Claude Code prompt for autonomous monitoring
    CLAUDE_PROMPT="$SCRIPT_DIR/logs/claude_monitoring_prompt.txt"
    cat > "$CLAUDE_PROMPT" << 'CLAUDE_PROMPT_EOF'
You are now in autonomous monitoring mode for the Spartan Research Station.

**Your Role**: Monitor the website_monitor agent logs and Docker services. Fix any issues that arise automatically.

**Context**:
- All Docker services are running
- Website Monitor agent is checking health every 30 seconds
- Auto-healing is enabled but may fail for complex issues
- You have full access to the codebase and can make fixes

**What to Monitor**:
1. Monitor logs: `docker-compose logs -f spartan-website-monitor`
2. Check for errors: `docker-compose logs --tail=100 | grep -i error`
3. Service status: `docker-compose ps`
4. Database: `docker exec -it spartan-postgres psql -U spartan -d spartan_research_db -c "SELECT * FROM monitor_incidents ORDER BY timestamp DESC LIMIT 5;"`

**When Issues Arise**:
1. Investigate: Read logs, check container status, review code
2. Diagnose: Determine root cause
3. Fix: Make code changes, update configs, restart services
4. Verify: Confirm the fix worked
5. Document: Commit changes with clear message

**Critical Issues to Watch For**:
- ❌ Container restart loops (agent can't fix)
- ❌ Database connection errors (check PostgreSQL)
- ❌ API authentication failures (check .env keys)
- ❌ Port conflicts (check if ports are in use)
- ❌ Memory leaks (monitor container stats)
- ❌ Code errors in services (Python tracebacks)

**Available Commands**:
- View logs: `docker-compose logs -f <service>`
- Restart: `docker-compose restart <service>`
- Rebuild: `docker-compose build <service> && docker-compose up -d <service>`
- Database: `docker exec -it spartan-postgres psql -U spartan -d spartan_research_db`
- Execute in container: `docker exec -it <container> <command>`

**Your Goal**: Keep the website running 24/7 without manual intervention. Fix issues before users notice.

**Start by**: Checking current system status and watching for any immediate issues.
CLAUDE_PROMPT_EOF

    echo -e "${GREEN}✅ Claude monitoring prompt created${NC}"
    echo -e "${CYAN}📝 Prompt location: $CLAUDE_PROMPT${NC}"
    echo ""

    # Option to start Claude Code in background monitoring mode
    echo -e "${YELLOW}Do you want to start Claude Code in background monitoring mode? (y/n)${NC}"
    read -r -n 1 START_CLAUDE
    echo ""

    if [[ $START_CLAUDE =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}🚀 Launching Claude Code...${NC}"
        echo ""

        # Start alert watcher in background
        nohup "$SCRIPT_DIR/logs/alert_watcher.sh" > "$SCRIPT_DIR/logs/alert_watcher.log" 2>&1 &
        WATCHER_PID=$!
        echo "$WATCHER_PID" > "$SCRIPT_DIR/logs/alert_watcher.pid"
        echo -e "${GREEN}✅ Alert watcher started (PID: $WATCHER_PID)${NC}"

        # Start Claude Code session
        echo -e "${CYAN}Starting Claude Code in monitoring mode...${NC}"
        echo -e "${YELLOW}Note: Claude will work in this terminal. Keep it open for autonomous monitoring.${NC}"
        echo ""

        sleep 2

        # Launch Claude with monitoring prompt
        if command -v claude &> /dev/null; then
            # Pass the monitoring prompt to Claude
            cat "$CLAUDE_PROMPT"
            echo ""
            echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${GREEN}🤖 Claude Code Ready - Autonomous Monitoring Active${NC}"
            echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""

            # Start Claude in the current directory
            exec claude
        else
            echo -e "${RED}❌ Failed to launch Claude Code${NC}"
            echo -e "${YELLOW}You can manually run: claude${NC}"
        fi
    else
        echo -e "${CYAN}Skipping Claude Code integration${NC}"
        echo -e "${YELLOW}You can manually start Claude later by running: claude${NC}"
        echo -e "${CYAN}Then paste the prompt from: $CLAUDE_PROMPT${NC}"
    fi
else
    echo -e "${CYAN}💡 Tip: Install Claude Code for autonomous monitoring${NC}"
    echo -e "${CYAN}   Download: https://claude.ai/download${NC}"
fi

echo ""
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}🚀 System fully operational!${NC}"
echo -e "${CYAN}💡 Monitor is watching all services and will auto-heal issues${NC}"
echo ""

# If Claude not started, follow monitor logs
if [ "$CLAUDE_AVAILABLE" != true ] || [[ ! $START_CLAUDE =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Press Ctrl+C to exit log view (services continue running)${NC}"
    echo -e "${YELLOW}Following monitor logs...${NC}"
    echo ""

    sleep 2
    $DOCKER_COMPOSE logs -f spartan-website-monitor
fi
