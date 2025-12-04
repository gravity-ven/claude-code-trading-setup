#!/bin/bash
# START_SPARTAN_DEV.sh
# Native development mode - runs services without Docker for fast iteration

set -e  # Exit on error

echo "========================================================================"
echo "  SPARTAN RESEARCH STATION - DEVELOPMENT MODE (Native)"
echo "========================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create .pids directory if it doesn't exist
mkdir -p .pids

# Check if PostgreSQL is running
echo -n "Checking PostgreSQL... "
if pg_isready -q 2>/dev/null; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${YELLOW}⚠ Not running${NC}"
    echo "Starting PostgreSQL..."

    # Try different methods based on OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux/WSL
        sudo service postgresql start 2>/dev/null || sudo systemctl start postgresql 2>/dev/null || {
            echo -e "${RED}✗ Failed to start PostgreSQL${NC}"
            echo "Please start PostgreSQL manually:"
            echo "  sudo service postgresql start"
            exit 1
        }
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew services start postgresql 2>/dev/null || {
            echo -e "${RED}✗ Failed to start PostgreSQL${NC}"
            echo "Please start PostgreSQL manually:"
            echo "  brew services start postgresql"
            exit 1
        }
    fi

    # Wait for PostgreSQL to be ready
    echo "Waiting for PostgreSQL to be ready..."
    for i in {1..10}; do
        if pg_isready -q 2>/dev/null; then
            echo -e "${GREEN}✓ PostgreSQL ready${NC}"
            break
        fi
        sleep 1
    done
fi

# Check if Redis is running
echo -n "Checking Redis... "
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${YELLOW}⚠ Not running${NC}"
    echo "Starting Redis..."

    # Try different methods based on OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux/WSL
        sudo service redis-server start 2>/dev/null || sudo systemctl start redis 2>/dev/null || {
            echo -e "${RED}✗ Failed to start Redis${NC}"
            echo "Please start Redis manually:"
            echo "  sudo service redis-server start"
            exit 1
        }
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew services start redis 2>/dev/null || {
            echo -e "${RED}✗ Failed to start Redis${NC}"
            echo "Please start Redis manually:"
            echo "  brew services start redis"
            exit 1
        }
    fi

    # Wait for Redis to be ready
    echo "Waiting for Redis to be ready..."
    for i in {1..10}; do
        if redis-cli ping > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Redis ready${NC}"
            break
        fi
        sleep 1
    done
fi

# Check if database exists
echo -n "Checking database 'spartan_research_db'... "
if psql -lqt | cut -d \| -f 1 | grep -qw spartan_research_db; then
    echo -e "${GREEN}✓ Exists${NC}"
else
    echo -e "${YELLOW}⚠ Not found${NC}"
    echo "Creating database 'spartan_research_db'..."
    createdb spartan_research_db 2>/dev/null || {
        echo -e "${RED}✗ Failed to create database${NC}"
        echo "Please create database manually:"
        echo "  createdb spartan_research_db"
        exit 1
    }
    echo -e "${GREEN}✓ Database created${NC}"
fi

# Initialize database schema if needed
if [ -f "db/init/init.sql" ]; then
    echo "Initializing database schema..."
    psql -d spartan_research_db -f db/init/init.sql > /dev/null 2>&1 || echo -e "${YELLOW}⚠ Schema already initialized or error occurred${NC}"
fi

# Check for virtualenv
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠ Virtual environment not found${NC}"
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    echo -n "Activating virtual environment... "
    source venv/bin/activate
    echo -e "${GREEN}✓${NC}"
fi

# Load environment variables
if [ -f ".env" ]; then
    echo -n "Loading environment variables... "
    set -a
    source .env
    set +a
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠ .env file not found - using defaults${NC}"
    echo "Create .env file with your API keys for full functionality"
fi

# Set default environment variables if not set
export DATABASE_URL=${DATABASE_URL:-"postgresql://localhost:5432/spartan_research_db"}
export REDIS_HOST=${REDIS_HOST:-"localhost"}
export REDIS_PORT=${REDIS_PORT:-"6379"}

echo ""
echo "========================================================================"
echo "  Starting Services"
echo "========================================================================"
echo ""

# Kill any existing processes on our ports
for port in 8888 5000 5002 5003 5004; do
    pid=$(lsof -ti:$port 2>/dev/null || true)
    if [ ! -z "$pid" ]; then
        echo "Killing existing process on port $port (PID: $pid)"
        kill -9 $pid 2>/dev/null || true
        sleep 1
    fi
done

# Start main web server
echo -n "Starting main web server (port 8888)... "
python start_server.py > logs/main_server.log 2>&1 &
echo $! > .pids/main.pid
echo -e "${GREEN}✓ PID $(cat .pids/main.pid)${NC}"

# Wait for main server to be ready
sleep 2

# Start microservices
echo -n "Starting Correlation API (port 5004)... "
python correlation_api.py > logs/correlation_api.log 2>&1 &
echo $! > .pids/correlation.pid
echo -e "${GREEN}✓ PID $(cat .pids/correlation.pid)${NC}"

echo -n "Starting Daily Planet API (port 5000)... "
python daily_planet_api.py > logs/daily_planet_api.log 2>&1 &
echo $! > .pids/daily_planet.pid
echo -e "${GREEN}✓ PID $(cat .pids/daily_planet.pid)${NC}"

echo -n "Starting Swing Dashboard API (port 5002)... "
python swing_dashboard_api.py > logs/swing_api.log 2>&1 &
echo $! > .pids/swing.pid
echo -e "${GREEN}✓ PID $(cat .pids/swing.pid)${NC}"

echo -n "Starting GARP API (port 5003)... "
python garp_api.py > logs/garp_api.log 2>&1 &
echo $! > .pids/garp.pid
echo -e "${GREEN}✓ PID $(cat .pids/garp.pid)${NC}"

# Wait for all services to be ready
echo ""
echo "Waiting for services to be ready..."
sleep 3

echo ""
echo "========================================================================"
echo "  Loading Market Data"
echo "========================================================================"
echo ""

# Run data preloader
echo "Running data preloader (this may take 30-60 seconds)..."
python src/data_preloader.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Data preloader completed successfully${NC}"
else
    echo -e "${RED}✗ Data preloader failed${NC}"
    echo "Check logs/data_preloader.log for details"
    echo "Website will still start, but may show missing data"
fi

# Start data refresh scheduler
echo -n "Starting data refresh scheduler (15-min intervals)... "
python src/data_refresh_scheduler.py > logs/data_refresh.log 2>&1 &
echo $! > .pids/refresh.pid
echo -e "${GREEN}✓ PID $(cat .pids/refresh.pid)${NC}"

echo ""
echo "========================================================================"
echo "  SPARTAN RESEARCH STATION IS READY!"
echo "========================================================================"
echo ""
echo "  Main Dashboard:     http://localhost:8888/index.html"
echo "  Capital Flow:       http://localhost:8888/global_capital_flow_swing_trading.html"
echo ""
echo "  API Endpoints:"
echo "    Main Server:      http://localhost:8888/health"
echo "    Correlation:      http://localhost:5004/health"
echo "    Daily Planet:     http://localhost:5000/health"
echo "    Swing Dashboard:  http://localhost:5002/api/swing-dashboard/health"
echo "    GARP Screener:    http://localhost:5003/api/health"
echo ""
echo "  Logs:"
echo "    Main Server:      tail -f logs/main_server.log"
echo "    All Services:     tail -f logs/*.log"
echo ""
echo "  Control:"
echo "    Stop All:         ./STOP_SPARTAN_DEV.sh"
echo "    Restart All:      ./RESTART_SPARTAN_DEV.sh"
echo "    Restart One:      kill -9 \$(cat .pids/main.pid) && python start_server.py &"
echo ""
echo "========================================================================"
echo ""
echo -e "${GREEN}✓ Development mode active - changes take effect immediately!${NC}"
echo -e "${YELLOW}⚠ Press Ctrl+C will NOT stop services (use ./STOP_SPARTAN_DEV.sh)${NC}"
echo ""
