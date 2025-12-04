#!/bin/bash
#
# Install Spartan 100 Agents as a systemd service
# This enables auto-start on boot and background execution
#
# Usage: sudo ./install_agents_service.sh
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}  Spartan 100 Agents - systemd Service Installation${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Please run as root: sudo $0${NC}"
    exit 1
fi

# Get the current directory
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "${YELLOW}📁 Install directory: ${INSTALL_DIR}${NC}"

# Get the user who should run the service (the one who executed sudo)
SERVICE_USER="${SUDO_USER:-$USER}"
echo -e "${YELLOW}👤 Service will run as user: ${SERVICE_USER}${NC}"

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 is not installed. Please install Python 3.8+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ Found ${PYTHON_VERSION}${NC}"

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠️  PostgreSQL not found. Install with:${NC}"
    echo -e "   Ubuntu/Debian: sudo apt install postgresql"
    echo -e "   macOS: brew install postgresql@15"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create systemd service file
SERVICE_FILE="/etc/systemd/system/spartan_agents.service"

echo -e "${YELLOW}📝 Creating systemd service file: ${SERVICE_FILE}${NC}"

cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=Spartan 100 Autonomous COT Stock Research Agents
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=${SERVICE_USER}
WorkingDirectory=${INSTALL_DIR}
ExecStart=/usr/bin/python3 ${INSTALL_DIR}/run_100_agents.py
Restart=on-failure
RestartSec=30
StandardOutput=append:${INSTALL_DIR}/logs/agents.log
StandardError=append:${INSTALL_DIR}/logs/agents.log

# Environment variables (customize as needed)
Environment="POSTGRES_HOST=localhost"
Environment="POSTGRES_PORT=5432"
Environment="POSTGRES_DB=spartan_research_db"
Environment="POSTGRES_USER=spartan"
Environment="POSTGRES_PASSWORD=spartan"

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✅ Service file created${NC}"

# Create logs directory if it doesn't exist
mkdir -p "${INSTALL_DIR}/logs"
chown -R "${SERVICE_USER}:${SERVICE_USER}" "${INSTALL_DIR}/logs"

echo -e "${GREEN}✅ Logs directory created: ${INSTALL_DIR}/logs${NC}"

# Create output directory if it doesn't exist
mkdir -p "${INSTALL_DIR}/output"
chown -R "${SERVICE_USER}:${SERVICE_USER}" "${INSTALL_DIR}/output"

echo -e "${GREEN}✅ Output directory created: ${INSTALL_DIR}/output${NC}"

# Reload systemd daemon
echo -e "${YELLOW}🔄 Reloading systemd daemon...${NC}"
systemctl daemon-reload

echo -e "${GREEN}✅ Systemd daemon reloaded${NC}"

# Enable service (auto-start on boot)
echo -e "${YELLOW}🔧 Enabling service for auto-start on boot...${NC}"
systemctl enable spartan_agents.service

echo -e "${GREEN}✅ Service enabled${NC}"

# Start the service
echo -e "${YELLOW}🚀 Starting service...${NC}"
systemctl start spartan_agents.service

echo -e "${GREEN}✅ Service started${NC}"

# Check status
sleep 2
echo ""
echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""
echo -e "${YELLOW}Service Status:${NC}"
systemctl status spartan_agents.service --no-pager -l
echo ""
echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}  Control Commands:${NC}"
echo -e "${GREEN}======================================================================${NC}"
echo ""
echo -e "  ${YELLOW}View live output:${NC}"
echo -e "    tail -f ${INSTALL_DIR}/logs/agents.log"
echo -e "    ${INSTALL_DIR}/view_agent_output.sh"
echo ""
echo -e "  ${YELLOW}Check status:${NC}"
echo -e "    sudo systemctl status spartan_agents"
echo ""
echo -e "  ${YELLOW}Stop agents:${NC}"
echo -e "    sudo systemctl stop spartan_agents"
echo ""
echo -e "  ${YELLOW}Start agents:${NC}"
echo -e "    sudo systemctl start spartan_agents"
echo ""
echo -e "  ${YELLOW}Restart agents:${NC}"
echo -e "    sudo systemctl restart spartan_agents"
echo ""
echo -e "  ${YELLOW}Disable auto-start:${NC}"
echo -e "    sudo systemctl disable spartan_agents"
echo ""
echo -e "  ${YELLOW}View latest trade sheet:${NC}"
echo -e "    cat ${INSTALL_DIR}/output/latest_trade_sheet.txt"
echo ""
echo -e "${GREEN}======================================================================${NC}"
echo -e "${GREEN}  The agents are now running in the background!${NC}"
echo -e "${GREEN}  Trade sheets will be generated every hour in:${NC}"
echo -e "${GREEN}  ${INSTALL_DIR}/output/latest_trade_sheet.txt${NC}"
echo -e "${GREEN}======================================================================${NC}"
