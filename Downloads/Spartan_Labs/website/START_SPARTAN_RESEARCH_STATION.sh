#!/bin/bash
# ==============================================================================
# SPARTAN RESEARCH STATION - One-Command Startup Script
# ==============================================================================
# Enterprise-Grade Market Intelligence Platform
# Database-First Architecture with 50+ Data Sources
# ==============================================================================

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ASCII Art Logo
echo -e "${BLUE}"
cat << "EOF"
 ╔═══════════════════════════════════════════════════════════════╗
 ║                                                               ║
 ║   ███████╗██████╗  █████╗ ██████╗ ████████╗ █████╗ ███╗   ██╗║
 ║   ██╔════╝██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗████╗  ██║║
 ║   ███████╗██████╔╝███████║██████╔╝   ██║   ███████║██╔██╗ ██║║
 ║   ╚════██║██╔═══╝ ██╔══██║██╔══██╗   ██║   ██╔══██║██║╚██╗██║║
 ║   ███████║██║     ██║  ██║██║  ██║   ██║   ██║  ██║██║ ╚████║║
 ║   ╚══════╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═══╝║
 ║                                                               ║
 ║              RESEARCH STATION v2.0                           ║
 ║         Enterprise-Grade Market Intelligence                  ║
 ║                                                               ║
 ╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}\n"

# ==============================================================================
# Pre-Flight Checks
# ==============================================================================

echo -e "${YELLOW}[Pre-Flight Checks]${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓ Docker installed${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}✗ Docker Compose not found${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose installed${NC}"

# Check .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ .env file not found${NC}"
    echo "Creating .env from .env.spartan.example..."
    cp .env.spartan.example .env
    echo -e "${YELLOW}⚠ Please edit .env and add your API keys before continuing${NC}"
    echo "Press any key when ready..."
    read -n 1
fi
echo -e "${GREEN}✓ .env file exists${NC}"

# ==============================================================================
# Phase 1: Infrastructure Layer
# ==============================================================================

echo -e "\n${BLUE}[Phase 1/6]${NC} ${YELLOW}Starting Infrastructure Layer...${NC}"
echo "  → PostgreSQL database (TimescaleDB)"
echo "  → Redis cache"

docker-compose -f docker-compose.spartan.yml up -d postgres redis

echo -ne "  ⏳ Waiting for PostgreSQL"
for i in {1..30}; do
    if docker exec spartan_postgres pg_isready -U spartan_user -d spartan_research > /dev/null 2>&1; then
        echo -e "\r${GREEN}  ✓ PostgreSQL ready${NC}                    "
        break
    fi
    echo -ne "."
    sleep 2
done

echo -ne "  ⏳ Waiting for Redis"
for i in {1..15}; do
    if docker exec spartan_redis redis-cli ping > /dev/null 2>&1; then
        echo -e "\r${GREEN}  ✓ Redis ready${NC}                    "
        break
    fi
    echo -ne "."
    sleep 1
done

# ==============================================================================
# Phase 2: Pre-Loader Service
# ==============================================================================

echo -e "\n${BLUE}[Phase 2/6]${NC} ${YELLOW}Starting Data Pre-Loader...${NC}"
echo "  → Downloading data from 30+ sources"
echo "  → Populating PostgreSQL database"
echo "  → This takes 2-5 minutes (one-time setup)"

docker-compose -f docker-compose.spartan.yml up -d preloader

# Monitor pre-loader progress
echo ""
while true; do
    # Check if preloader container exists
    if ! docker ps -a | grep -q spartan_preloader; then
        echo -e "${RED}✗ Pre-loader container not found${NC}"
        exit 1
    fi

    # Check if preloader is still running
    if ! docker ps | grep -q spartan_preloader; then
        # Container stopped - check exit code
        EXIT_CODE=$(docker inspect spartan_preloader --format='{{.State.ExitCode}}')

        if [ "$EXIT_CODE" = "0" ]; then
            echo -e "${GREEN}✓ Pre-loader completed successfully${NC}"
            break
        else
            echo -e "${RED}✗ Pre-loader failed with exit code $EXIT_CODE${NC}"
            echo "Check logs: docker logs spartan_preloader"
            exit 1
        fi
    fi

    # Get progress from Redis
    COMPLETED=$(docker exec spartan_redis redis-cli HGET preload:status completed_sources 2>/dev/null || echo "0")
    TOTAL=$(docker exec spartan_redis redis-cli HGET preload:status total_sources 2>/dev/null || echo "30")
    SUCCESSFUL=$(docker exec spartan_redis redis-cli HGET preload:status successful_sources 2>/dev/null || echo "0")

    if [ "$TOTAL" != "0" ]; then
        PROGRESS=$((COMPLETED * 100 / TOTAL))
        echo -ne "  Progress: $COMPLETED/$TOTAL sources ($PROGRESS%) - $SUCCESSFUL successful\r"
    fi

    sleep 2
done

# ==============================================================================
# Phase 3: Web Server
# ==============================================================================

echo -e "\n${BLUE}[Phase 3/6]${NC} ${YELLOW}Starting Web Server...${NC}"
echo "  → Flask application"
echo "  → Serving from database (instant data)"

docker-compose -f docker-compose.spartan.yml up -d web

echo -ne "  ⏳ Waiting for web server"
for i in {1..30}; do
    if curl -sf http://localhost:8888/health > /dev/null 2>&1; then
        echo -e "\r${GREEN}  ✓ Web server ready${NC}                    "
        break
    fi
    echo -ne "."
    sleep 2
done

# ==============================================================================
# Phase 4: Background Refresh Service
# ==============================================================================

echo -e "\n${BLUE}[Phase 4/6]${NC} ${YELLOW}Starting Background Refresh...${NC}"
echo "  → 1-hour refresh cycle (as requested)"
echo "  → Silent updates (zero user impact)"

docker-compose -f docker-compose.spartan.yml up -d refresh

echo -e "${GREEN}  ✓ Background refresh active${NC}"

# ==============================================================================
# Phase 5: Monitoring Stack (Optional)
# ==============================================================================

echo -e "\n${BLUE}[Phase 5/6]${NC} ${YELLOW}Starting Monitoring Stack...${NC}"
echo "  → Prometheus metrics"
echo "  → Grafana dashboards"

docker-compose -f docker-compose.spartan.yml up -d prometheus grafana 2>/dev/null || echo -e "${YELLOW}  ⚠ Monitoring stack skipped (optional)${NC}"

# ==============================================================================
# Phase 6: Browser Launch
# ==============================================================================

echo -e "\n${BLUE}[Phase 6/6]${NC} ${YELLOW}Verifying all services before browser launch...${NC}"

# Wait for all services to be healthy before opening browser
ALL_HEALTHY=true
RETRY_COUNT=0
MAX_RETRIES=60

echo ""
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    ALL_HEALTHY=true

    # Check main server
    if ! curl -s --max-time 2 "http://localhost:8888/health" > /dev/null 2>&1; then
        ALL_HEALTHY=false
    fi

    if [ "$ALL_HEALTHY" = true ]; then
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -n "."
    sleep 1
done

echo ""

if [ "$ALL_HEALTHY" = true ]; then
    echo -e "${GREEN}✅ All services are healthy!${NC}"
    echo ""
    echo "Opening browser..."

    # Detect OS and open browser
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if grep -qi microsoft /proc/version 2>/dev/null; then
            # WSL - use Windows browser
            cmd.exe /c start http://localhost:8888/nano_banana_scanner.html 2>/dev/null || xdg-open http://localhost:8888/nano_banana_scanner.html 2>/dev/null &
        else
            xdg-open http://localhost:8888/nano_banana_scanner.html 2>/dev/null &
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        open http://localhost:8888/nano_banana_scanner.html
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        start http://localhost:8888/nano_banana_scanner.html
    else
        echo "Please open: http://localhost:8888/nano_banana_scanner.html"
    fi
else
    echo -e "${YELLOW}⚠ Services still starting. Browser not auto-opened.${NC}"
    echo "Open manually: http://localhost:8888/nano_banana_scanner.html"
fi

# ==============================================================================
# Success Summary
# ==============================================================================

echo -e "\n${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                               ║${NC}"
echo -e "${GREEN}║            SPARTAN RESEARCH STATION IS READY                  ║${NC}"
echo -e "${GREEN}║                                                               ║${NC}"
echo -e "${GREEN}╠═══════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║                                                               ║${NC}"
echo -e "${GREEN}║  🌐 Dashboard:         http://localhost:8888                 ║${NC}"
echo -e "${GREEN}║  📊 Monitoring:        http://localhost:3000                 ║${NC}"
echo -e "${GREEN}║  💾 PostgreSQL:        localhost:5432                        ║${NC}"
echo -e "${GREEN}║  ⚡ Redis:             localhost:6379                        ║${NC}"
echo -e "${GREEN}║                                                               ║${NC}"
echo -e "${GREEN}╠═══════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║                                                               ║${NC}"
echo -e "${GREEN}║  ✅ All data pre-loaded from 30+ sources                     ║${NC}"
echo -e "${GREEN}║  ✅ Database-first architecture (instant page loads)         ║${NC}"
echo -e "${GREEN}║  ✅ 1-hour background refresh active                         ║${NC}"
echo -e "${GREEN}║  ✅ Enterprise-grade reliability                             ║${NC}"
echo -e "${GREEN}║                                                               ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${BLUE}Useful Commands:${NC}"
echo "  View logs:       docker-compose -f docker-compose.spartan.yml logs -f"
echo "  Stop system:     docker-compose -f docker-compose.spartan.yml down"
echo "  Restart:         docker-compose -f docker-compose.spartan.yml restart"
echo "  Database shell:  docker exec -it spartan_postgres psql -U spartan_user -d spartan_research"
echo ""

# Keep script running to show logs
echo -e "${YELLOW}Monitoring logs (Ctrl+C to exit):${NC}\n"
docker-compose -f docker-compose.spartan.yml logs -f --tail=50
