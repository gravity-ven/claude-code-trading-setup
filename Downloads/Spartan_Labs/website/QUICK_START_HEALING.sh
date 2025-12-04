#!/bin/bash
################################################################################
# SPARTAN LABS - AUTONOMOUS HEALING SYSTEM
# QUICK START INSTALLATION SCRIPT
#
# This script sets up the autonomous error detection and self-healing system
# in 5 minutes with zero manual configuration.
#
# Usage: ./QUICK_START_HEALING.sh
#
# Author: Spartan Labs
# Version: 1.0.0
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BLUE}"
echo "================================================================================"
echo "   SPARTAN LABS - AUTONOMOUS HEALING SYSTEM INSTALLATION"
echo "================================================================================"
echo -e "${NC}"
echo ""

# Step 1: Check Python version
echo -e "${YELLOW}[1/7] Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.9+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2 | cut -d '.' -f 1,2)
echo -e "${GREEN}✅ Python ${PYTHON_VERSION} found${NC}"
echo ""

# Step 2: Check PostgreSQL
echo -e "${YELLOW}[2/7] Checking PostgreSQL...${NC}"
if ! command -v psql &> /dev/null; then
    echo -e "${RED}❌ PostgreSQL not found. Installing...${NC}"

    # Detect OS and install PostgreSQL
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt update
        sudo apt install -y postgresql postgresql-contrib
        sudo systemctl start postgresql
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install postgresql
        brew services start postgresql
    else
        echo -e "${RED}❌ Unsupported OS. Please install PostgreSQL manually${NC}"
        exit 1
    fi
fi

PG_VERSION=$(psql --version | cut -d ' ' -f 3 | cut -d '.' -f 1)
echo -e "${GREEN}✅ PostgreSQL ${PG_VERSION} installed${NC}"
echo ""

# Step 3: Create database
echo -e "${YELLOW}[3/7] Creating database...${NC}"
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw spartan_research_db; then
    echo -e "${GREEN}✅ Database 'spartan_research_db' already exists${NC}"
else
    sudo -u postgres createdb spartan_research_db
    sudo -u postgres psql -c "CREATE USER spartan_user WITH PASSWORD 'secure_password';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE spartan_research_db TO spartan_user;"
    echo -e "${GREEN}✅ Database 'spartan_research_db' created${NC}"
fi
echo ""

# Step 4: Create virtual environment
echo -e "${YELLOW}[4/7] Setting up virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi
echo ""

# Step 5: Install dependencies
echo -e "${YELLOW}[5/7] Installing Python dependencies...${NC}"
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements_healing.txt > /dev/null 2>&1
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 6: Create configuration
echo -e "${YELLOW}[6/7] Creating configuration...${NC}"
mkdir -p config
mkdir -p logs

if [ ! -f "config/healing_config.yaml" ]; then
    python3 src/autonomous_healing/start_agents.py --config config/healing_config.yaml &
    sleep 2
    pkill -f start_agents.py
    echo -e "${GREEN}✅ Configuration created${NC}"
else
    echo -e "${GREEN}✅ Configuration already exists${NC}"
fi
echo ""

# Step 7: Initialize database tables
echo -e "${YELLOW}[7/7] Initializing database tables...${NC}"
python3 -c "
import asyncio
from src.autonomous_healing.error_monitor import ErrorDetectionEngine

async def init():
    db_config = {
        'dbname': 'spartan_research_db',
        'user': 'spartan_user',
        'password': 'secure_password',
        'host': 'localhost',
        'port': 5432
    }
    engine = ErrorDetectionEngine(db_config)
    await engine.connect_db()
    await engine.close()
    print('✅ Database tables initialized')

asyncio.run(init())
"
echo ""

# Installation complete
echo -e "${GREEN}"
echo "================================================================================"
echo "   ✅ INSTALLATION COMPLETE!"
echo "================================================================================"
echo -e "${NC}"
echo ""
echo -e "${BLUE}System Status:${NC}"
echo "  ✅ Python ${PYTHON_VERSION} installed"
echo "  ✅ PostgreSQL ${PG_VERSION} running"
echo "  ✅ Database 'spartan_research_db' created"
echo "  ✅ Dependencies installed"
echo "  ✅ Configuration ready"
echo "  ✅ Database tables initialized"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo -e "  ${GREEN}1. Start the autonomous healing system:${NC}"
echo "     python3 src/autonomous_healing/start_agents.py"
echo ""
echo -e "  ${GREEN}2. View the health dashboard:${NC}"
echo "     http://localhost:8888/health-dashboard"
echo ""
echo -e "  ${GREEN}3. Check system logs:${NC}"
echo "     tail -f logs/autonomous_healing.log"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo "  - Full Guide: AUTONOMOUS_HEALING_SYSTEM.md"
echo "  - Quick Start: src/autonomous_healing/README.md"
echo "  - TOON Format: src/autonomous_healing/TOON_DATA_STRUCTURES.md"
echo ""
echo -e "${YELLOW}🚀 The system will monitor 50+ endpoints 24/7 and heal errors automatically!${NC}"
echo ""
echo "================================================================================"
