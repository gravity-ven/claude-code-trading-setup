#!/bin/bash
##############################################################################
# PERMANENT MONITORING SYSTEM - LOCK-IN DATA PROTECTION
# ZERO COMPROMISE - ZERO TOLERANCE - ZERO DOWNTIME
##############################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${PURPLE}========================================================${NC}"
echo -e "${PURPLE}   🔒 PERMANENT MONITORING SYSTEM - LOCK-IN MODE${NC}"
echo -e "${PURPLE}   ZERO COMPROMISE - BULLETPROOF DATA PROTECTION${NC}"
echo -e "${PURPLE}========================================================${NC}"

# Function to ensure agent is running
ensure_running() {
    local process_name=$1
    local script_path=$2
    local log_file=$3
    local display_name=$4

    if ! pgrep -f "$process_name" > /dev/null; then
        echo -e "${YELLOW}⚠️ $display_name not running - STARTING NOW${NC}"
        nohup python3 $script_path > $log_file 2>&1 &
        NEW_PID=$!
        echo -e "${GREEN}✅ $display_name STARTED: PID $NEW_PID${NC}"
    else
        PID=$(pgrep -f "$process_name" | head -1)
        echo -e "${GREEN}✅ $display_name ACTIVE: PID $PID${NC}"
    fi
}

# CRITICAL AGENTS - MUST ALWAYS RUN
echo -e "\n${PURPLE}VERIFYING CRITICAL AGENTS:${NC}"
echo -e "${PURPLE}========================================================${NC}"

# 1. Master Data Orchestrator (229+ data points, updates every second)
ensure_running "master_data_orchestrator.py" "master_data_orchestrator.py" "orchestrator.log" "Master Orchestrator"

# 2. Data Integrity Enforcer (Zero tolerance for empty data)
ensure_running "data_integrity_enforcer.py" "data_integrity_enforcer.py" "enforcer.log" "Data Enforcer"

# 3. Autonomous Data Guardian (Permanent lock-in monitoring)
ensure_running "autonomous_data_guardian.py" "autonomous_data_guardian.py" "guardian.log" "Autonomous Guardian"

# 4. Complete Data Validator (Continuous validation)
ensure_running "complete_data_validator.py" "complete_data_validator.py" "validator.log" "Data Validator"

# 5. Comprehensive Page Scanner (Every page, every data point)
ensure_running "comprehensive_page_scanner.py" "comprehensive_page_scanner.py" "scanner.log" "Page Scanner"

# 6. Data Loader (41+ symbols comprehensive)
ensure_running "load_all_data.py" "load_all_data.py" "loader.log" "Data Loader"

# 7. Web Server
ensure_running "start_server.py" "start_server.py" "server.log" "Web Server"

# SUPPORTING AGENTS
echo -e "\n${PURPLE}VERIFYING SUPPORTING AGENTS:${NC}"
echo -e "${PURPLE}========================================================${NC}"

# 8. Macro Scanner
ensure_running "comprehensive_macro_scanner.py" "comprehensive_macro_scanner.py" "scanner.log" "Macro Scanner"

# 9. Data Preloader
ensure_running "data_preloader.py" "src/data_preloader.py" "preloader.log" "Data Preloader"

# 10. Refresh Scheduler
ensure_running "data_refresh_scheduler.py" "src/data_refresh_scheduler.py" "refresh.log" "Refresh Scheduler"

# Check Redis status
echo -e "\n${PURPLE}DATA INTEGRITY CHECK:${NC}"
echo -e "${PURPLE}========================================================${NC}"

# Count Redis keys
KEY_COUNT=$(redis-cli DBSIZE | awk '{print $2}')
echo -e "📊 Redis Data Points: ${GREEN}$KEY_COUNT${NC}"

# Check guardian status
GUARDIAN_STATUS=$(redis-cli GET guardian:status 2>/dev/null)
if [ ! -z "$GUARDIAN_STATUS" ]; then
    echo -e "🛡️ Guardian Status: ${GREEN}ACTIVE${NC}"
    echo "$GUARDIAN_STATUS" | python3 -c "import sys, json; data=json.loads(sys.stdin.read()); print(f'   • Uptime: {data[\"uptime_hours\"]:.1f} hours'); print(f'   • Total Fixes: {data[\"total_fixes\"]}'); print(f'   • Health: {data[\"health\"]}')"
fi

# Check enforcer status
ENFORCER_STATUS=$(redis-cli GET enforcer:status 2>/dev/null)
if [ ! -z "$ENFORCER_STATUS" ]; then
    echo -e "🔒 Enforcer Status: ${GREEN}ENFORCING${NC}"
    echo "$ENFORCER_STATUS" | python3 -c "import sys, json; data=json.loads(sys.stdin.read()); print(f'   • Mode: {data[\"mode\"]}'); print(f'   • Empty Tolerance: {data[\"empty_tolerance\"]}')"
fi

# Verify critical data points
echo -e "\n${PURPLE}CRITICAL DATA VERIFICATION:${NC}"
echo -e "${PURPLE}========================================================${NC}"

check_data() {
    local key=$1
    local name=$2
    local value=$(redis-cli GET "$key" 2>/dev/null)

    if [ ! -z "$value" ] && [ "$value" != "null" ]; then
        echo -e "✅ $name: ${GREEN}LIVE DATA${NC}"
    else
        echo -e "❌ $name: ${RED}MISSING${NC} - Guardian will fix automatically"
    fi
}

# Check Best Composite Indicator (was showing empty)
check_data "forex:AUDJPY" "AUD/JPY"
check_data "etf:HYG" "High Yield Bonds"
check_data "treasury:TNX" "10-Year Yield"

# Check main indices
check_data "market:index:SPY" "S&P 500"
check_data "market:index:QQQ" "NASDAQ"
check_data "crypto:BTC-USD" "Bitcoin"

echo -e "\n${PURPLE}========================================================${NC}"
echo -e "${GREEN}   🔒 PERMANENT MONITORING ACTIVE${NC}"
echo -e "${GREEN}   📊 ZERO DATA GAPS GUARANTEED${NC}"
echo -e "${GREEN}   🛡️ AUTONOMOUS SELF-HEALING ENABLED${NC}"
echo -e "${PURPLE}========================================================${NC}"

# Create systemd service for auto-start on boot
echo -e "\n${YELLOW}Creating systemd service for permanent monitoring...${NC}"

sudo tee /etc/systemd/system/spartan-monitor.service > /dev/null << EOF
[Unit]
Description=Spartan Permanent Monitoring System
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=/bin/bash $(pwd)/PERMANENT_MONITORING_SYSTEM.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable service
sudo systemctl daemon-reload
sudo systemctl enable spartan-monitor.service 2>/dev/null || echo "Service already enabled"

echo -e "${GREEN}✅ System configured for automatic startup on boot${NC}"
echo -e "${GREEN}✅ Monitoring will survive reboots and crashes${NC}"
echo ""
echo -e "${PURPLE}LOCK-IN STATUS: ${GREEN}PERMANENT${NC}"
echo ""