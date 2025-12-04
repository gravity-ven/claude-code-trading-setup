#!/bin/bash

# SPARTAN RESEARCH STATION CONTROL PANEL
# Single file to START, STOP, RESTART, and CHECK status
# Works on macOS and Linux with Docker Desktop

# ============================================================
# COLOR DEFINITIONS
# ============================================================
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
RESET='\033[0m'

# ============================================================
# FUNCTIONS
# ============================================================

show_menu() {
    clear
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${CYAN}║                                                          ║${RESET}"
    echo -e "${CYAN}║${RESET}        ${WHITE}SPARTAN RESEARCH STATION - CONTROL PANEL${RESET}        ${CYAN}║${RESET}"
    echo -e "${CYAN}║                                                          ║${RESET}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${RESET}"
    echo ""
    echo -e "${YELLOW}  What would you like to do?${RESET}"
    echo ""
    echo -e "   ${GREEN}[1]${RESET} START   - Start all services"
    echo -e "   ${RED}[2]${RESET} STOP    - Stop all services"
    echo -e "   ${YELLOW}[3]${RESET} RESTART - Restart all services"
    echo -e "   ${BLUE}[4]${RESET} STATUS  - Check system status"
    echo -e "   ${CYAN}[5]${RESET} BUILD   - Rebuild containers"
    echo -e "   ${WHITE}[6]${RESET} LOGS    - View logs"
    echo -e "   ${RED}[0]${RESET} EXIT    - Exit control panel"
    echo ""
    read -p "$(echo -e ${CYAN}Enter your choice [0-6]:${RESET} )" choice

    case $choice in
        1) start_services ;;
        2) stop_services ;;
        3) restart_services ;;
        4) check_status ;;
        5) build_containers ;;
        6) view_logs ;;
        0) exit_script ;;
        *) show_menu ;;
    esac
}

start_services() {
    clear
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${GREEN}║         STARTING SPARTAN RESEARCH STATION                ║${RESET}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${RESET}"
    echo ""

    # Get script directory
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    cd "$SCRIPT_DIR"

    # Check Docker Desktop
    echo -e "${CYAN}[1/3] Checking Docker Desktop...${RESET}"
    if ! docker info &> /dev/null; then
        echo -e "${RED}❌ ERROR: Docker Desktop is not running!${RESET}"
        echo ""
        echo -e "${YELLOW}Please start Docker Desktop and try again.${RESET}"
        read -p "Press Enter to continue..."
        show_menu
        return
    fi
    echo -e "${GREEN}✓ Docker Desktop is running${RESET}"
    echo ""

    # Start services
    echo -e "${CYAN}[2/3] Starting all services...${RESET}"
    if ! docker-compose -f docker-compose.spartan.yml up -d; then
        echo -e "${RED}❌ ERROR: Failed to start services!${RESET}"
        read -p "Press Enter to continue..."
        show_menu
        return
    fi
    echo -e "${GREEN}✓ Services started successfully${RESET}"
    echo ""

    # Wait for services to be ready
    echo -e "${CYAN}[3/3] Waiting for services to be ready...${RESET}"
    sleep 5
    echo -e "${GREEN}✓ Services ready${RESET}"
    echo ""

    # Show access info
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${GREEN}║                    ✓ SYSTEM STARTED                      ║${RESET}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${RESET}"
    echo ""
    echo -e "${CYAN}Access your dashboard at:${RESET}"
    echo -e "   ${WHITE}http://localhost:8888${RESET}"
    echo ""
    echo -e "${CYAN}Services running:${RESET}"
    echo -e "   ${WHITE}• PostgreSQL  (Database)${RESET}"
    echo -e "   ${WHITE}• Redis       (Cache)${RESET}"
    echo -e "   ${WHITE}• Web Server  (Ports 8888, 9000)${RESET}"
    echo -e "   ${WHITE}• Grafana     (Port 3000)${RESET}"
    echo ""
    read -p "Press Enter to continue..."
    show_menu
}

stop_services() {
    clear
    echo ""
    echo -e "${RED}╔══════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${RED}║          STOPPING SPARTAN RESEARCH STATION               ║${RESET}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════╝${RESET}"
    echo ""

    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    cd "$SCRIPT_DIR"

    echo -e "${CYAN}Stopping all services...${RESET}"
    if ! docker-compose -f docker-compose.spartan.yml down; then
        echo -e "${RED}❌ ERROR: Failed to stop services!${RESET}"
        read -p "Press Enter to continue..."
        show_menu
        return
    fi

    echo ""
    echo -e "${GREEN}✓ All services stopped successfully${RESET}"
    echo ""
    read -p "Press Enter to continue..."
    show_menu
}

restart_services() {
    clear
    echo ""
    echo -e "${YELLOW}╔══════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${YELLOW}║         RESTARTING SPARTAN RESEARCH STATION              ║${RESET}"
    echo -e "${YELLOW}╚══════════════════════════════════════════════════════════╝${RESET}"
    echo ""

    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    cd "$SCRIPT_DIR"

    echo -e "${CYAN}[1/2] Stopping services...${RESET}"
    docker-compose -f docker-compose.spartan.yml down
    echo -e "${GREEN}✓ Services stopped${RESET}"
    echo ""

    echo -e "${CYAN}[2/2] Starting services...${RESET}"
    if ! docker-compose -f docker-compose.spartan.yml up -d; then
        echo -e "${RED}❌ ERROR: Failed to restart services!${RESET}"
        read -p "Press Enter to continue..."
        show_menu
        return
    fi
    echo -e "${GREEN}✓ Services restarted${RESET}"
    echo ""

    sleep 3
    echo -e "${GREEN}System ready at http://localhost:8888${RESET}"
    echo ""
    read -p "Press Enter to continue..."
    show_menu
}

check_status() {
    clear
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${BLUE}║              SPARTAN SYSTEM STATUS                       ║${RESET}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${RESET}"
    echo ""

    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    cd "$SCRIPT_DIR"

    # Check Docker
    echo -e "${CYAN}Docker Desktop Status:${RESET}"
    if ! docker info &> /dev/null; then
        echo -e "   ${RED}❌ Docker Desktop is NOT running${RESET}"
    else
        echo -e "   ${GREEN}✓ Docker Desktop is running${RESET}"
    fi
    echo ""

    # Check containers
    echo -e "${CYAN}Container Status:${RESET}"
    docker-compose -f docker-compose.spartan.yml ps
    echo ""

    # Check website accessibility
    echo -e "${CYAN}Website Accessibility:${RESET}"
    if curl -s http://localhost:8888/health > /dev/null 2>&1; then
        echo -e "   ${GREEN}✓ Website is accessible at http://localhost:8888${RESET}"
    else
        echo -e "   ${RED}❌ Website is NOT accessible${RESET}"
    fi
    echo ""

    read -p "Press Enter to continue..."
    show_menu
}

build_containers() {
    clear
    echo ""
    echo -e "${YELLOW}╔══════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${YELLOW}║           REBUILDING DOCKER CONTAINERS                   ║${RESET}"
    echo -e "${YELLOW}╚══════════════════════════════════════════════════════════╝${RESET}"
    echo ""

    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    cd "$SCRIPT_DIR"

    echo -e "${CYAN}This will rebuild all containers from scratch.${RESET}"
    echo -e "${YELLOW}This may take several minutes...${RESET}"
    echo ""
    read -p "Continue? (Y/N): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        show_menu
        return
    fi

    echo ""
    echo -e "${CYAN}Building containers...${RESET}"
    if ! docker-compose -f docker-compose.spartan.yml build; then
        echo -e "${RED}❌ ERROR: Build failed!${RESET}"
        read -p "Press Enter to continue..."
        show_menu
        return
    fi

    echo ""
    echo -e "${GREEN}✓ Build completed successfully${RESET}"
    echo ""
    echo -e "${YELLOW}Run START to launch the rebuilt containers.${RESET}"
    echo ""
    read -p "Press Enter to continue..."
    show_menu
}

view_logs() {
    clear
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${CYAN}║                   VIEW CONTAINER LOGS                    ║${RESET}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${RESET}"
    echo ""

    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    cd "$SCRIPT_DIR"

    echo -e "${WHITE}Available containers:${RESET}"
    echo -e "   ${CYAN}[1]${RESET} spartan_web"
    echo -e "   ${CYAN}[2]${RESET} spartan_postgres"
    echo -e "   ${CYAN}[3]${RESET} spartan_redis"
    echo -e "   ${CYAN}[4]${RESET} spartan_preloader"
    echo -e "   ${CYAN}[5]${RESET} spartan_grafana"
    echo -e "   ${CYAN}[0]${RESET} Back to main menu"
    echo ""
    read -p "Select container: " logchoice

    case $logchoice in
        1) docker logs spartan_web --tail 50 ;;
        2) docker logs spartan_postgres --tail 50 ;;
        3) docker logs spartan_redis --tail 50 ;;
        4) docker logs spartan_preloader --tail 50 ;;
        5) docker logs spartan_grafana --tail 50 ;;
        0) show_menu; return ;;
    esac

    echo ""
    read -p "Press Enter to continue..."
    view_logs
}

exit_script() {
    clear
    echo ""
    echo -e "${GREEN}Thank you for using Spartan Research Station!${RESET}"
    echo ""
    sleep 2
    exit 0
}

# ============================================================
# MAIN
# ============================================================

# Check if running on macOS or Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected: macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected: Linux"
fi

# Start menu
show_menu
