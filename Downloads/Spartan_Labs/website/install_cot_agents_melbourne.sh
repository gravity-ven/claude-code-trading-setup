#!/bin/bash
#
# Install COT Agents for Melbourne, Australia Timezone
# Runs on Saturday/Sunday/Monday mornings for weekend review
#
# Usage: ./install_cot_agents_melbourne.sh
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=====================================================================${NC}"
echo -e "${GREEN}  COT Agents Installation - Melbourne Weekend Schedule${NC}"
echo -e "${GREEN}=====================================================================${NC}"
echo ""

# Get the current directory
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "${YELLOW}📁 Install directory: ${INSTALL_DIR}${NC}"

# Get the user
CURRENT_USER="${USER}"
echo -e "${YELLOW}👤 Installing for user: ${CURRENT_USER}${NC}"

# Check timezone
CURRENT_TZ=$(timedatectl show --property=Timezone --value 2>/dev/null || echo "Unknown")
echo -e "${YELLOW}🌍 Current timezone: ${CURRENT_TZ}${NC}"

if [[ ! "$CURRENT_TZ" =~ "Australia" ]]; then
    echo -e "${YELLOW}⚠️  Warning: Timezone is not set to Australia${NC}"
    echo -e "${YELLOW}   Current: ${CURRENT_TZ}${NC}"
    echo -e "${YELLOW}   Recommended: Australia/Melbourne or Australia/Sydney${NC}"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}To set Melbourne timezone:${NC}"
        echo -e "  sudo timedatectl set-timezone Australia/Melbourne"
        exit 1
    fi
fi

echo ""
echo -e "${BLUE}=====================================================================${NC}"
echo -e "${BLUE}  SCHEDULE OVERVIEW${NC}"
echo -e "${BLUE}=====================================================================${NC}"
echo ""
echo -e "${GREEN}CFTC publishes:${NC} Friday 3:30 PM ET (US)"
echo -e "${GREEN}Available in Melbourne:${NC} Saturday ~7:30 AM AEDT / 6:30 AM AEST"
echo ""
echo -e "${GREEN}Your Schedule:${NC}"
echo -e "  📅 ${YELLOW}Saturday 8:00 AM${NC}  - Primary fetch & analysis"
echo -e "  📅 ${YELLOW}Sunday 10:00 AM${NC}  - Backup check & update"
echo -e "  📅 ${YELLOW}Monday 8:00 AM${NC}   - Final review before trading week"
echo ""
echo -e "${BLUE}=====================================================================${NC}"
echo ""

# Create cron jobs
echo -e "${YELLOW}📝 Setting up cron schedule...${NC}"

# Create temporary cron file
CRON_FILE="/tmp/cot_agents_cron_${CURRENT_USER}.txt"

# Get existing crontab (if any)
crontab -l > "${CRON_FILE}" 2>/dev/null || echo "# COT Agents Crontab" > "${CRON_FILE}"

# Remove any existing COT agents entries
sed -i '/# COT Agents - Melbourne Weekend Schedule/,+3d' "${CRON_FILE}"

# Add new entries
cat >> "${CRON_FILE}" <<EOF

# COT Agents - Melbourne Weekend Schedule
# Saturday 8:00 AM - Primary fetch
0 8 * * 6 cd ${INSTALL_DIR} && python3 run_100_agents.py --single-cycle >> logs/cot_weekend.log 2>&1

# Sunday 10:00 AM - Backup check
0 10 * * 0 cd ${INSTALL_DIR} && python3 run_100_agents.py --single-cycle >> logs/cot_weekend.log 2>&1

# Monday 8:00 AM - Final review
0 8 * * 1 cd ${INSTALL_DIR} && python3 run_100_agents.py --single-cycle >> logs/cot_weekend.log 2>&1

EOF

# Install the crontab
crontab "${CRON_FILE}"
rm "${CRON_FILE}"

echo -e "${GREEN}✅ Cron jobs installed${NC}"
echo ""

# Create notification script for when data is ready
cat > "${INSTALL_DIR}/check_cot_data.sh" <<'EOF'
#!/bin/bash
# Quick check if COT data is available

OUTPUT_FILE="output/latest_trade_sheet.txt"

if [ -f "$OUTPUT_FILE" ]; then
    SHEET_DATE=$(head -5 "$OUTPUT_FILE" | grep -oP '\d{4}-\d{2}-\d{2}' | head -1)
    echo "✅ Trade sheet available: $SHEET_DATE"
    echo ""
    echo "View with:"
    echo "  cat output/latest_trade_sheet.txt"
    echo ""
    echo "Recent opportunities:"
    grep -A 5 "TOP LONG" "$OUTPUT_FILE" 2>/dev/null || echo "  (Waiting for CFTC data)"
else
    echo "⏳ No trade sheet yet - waiting for CFTC data"
    echo ""
    echo "Check logs:"
    echo "  tail -20 logs/cot_weekend.log"
fi
EOF

chmod +x "${INSTALL_DIR}/check_cot_data.sh"

echo -e "${GREEN}✅ Created check script: check_cot_data.sh${NC}"
echo ""

# Verify cron installation
echo -e "${YELLOW}📋 Verifying cron schedule...${NC}"
echo ""
crontab -l | grep -A 3 "COT Agents - Melbourne Weekend Schedule"
echo ""

echo -e "${GREEN}=====================================================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${GREEN}=====================================================================${NC}"
echo ""
echo -e "${BLUE}Your COT Agents will now run:${NC}"
echo ""
echo -e "  📅 ${GREEN}Saturday 8:00 AM${NC}   → Fetch CFTC data, generate trade sheet"
echo -e "  📅 ${GREEN}Sunday 10:00 AM${NC}   → Verify & update"
echo -e "  📅 ${GREEN}Monday 8:00 AM${NC}    → Final review"
echo ""
echo -e "${BLUE}=====================================================================${NC}"
echo -e "${BLUE}  Quick Commands${NC}"
echo -e "${BLUE}=====================================================================${NC}"
echo ""
echo -e "  ${YELLOW}Check if data is ready:${NC}"
echo -e "    ./check_cot_data.sh"
echo ""
echo -e "  ${YELLOW}View latest trade sheet:${NC}"
echo -e "    cat output/latest_trade_sheet.txt"
echo ""
echo -e "  ${YELLOW}View weekend logs:${NC}"
echo -e "    tail -f logs/cot_weekend.log"
echo ""
echo -e "  ${YELLOW}Run manually now:${NC}"
echo -e "    python3 run_100_agents.py --single-cycle"
echo ""
echo -e "  ${YELLOW}View cron schedule:${NC}"
echo -e "    crontab -l | grep COT"
echo ""
echo -e "  ${YELLOW}Remove scheduled runs:${NC}"
echo -e "    crontab -e  # Then delete the COT Agents lines"
echo ""
echo -e "${BLUE}=====================================================================${NC}"
echo -e "${BLUE}  What Happens Next?${NC}"
echo -e "${BLUE}=====================================================================${NC}"
echo ""
echo -e "1. ${GREEN}This Saturday at 8:00 AM:${NC}"
echo -e "   - Agents will fetch CFTC data automatically"
echo -e "   - Trade sheet will be generated"
echo -e "   - Check with: ./check_cot_data.sh"
echo ""
echo -e "2. ${GREEN}Sunday & Monday:${NC}"
echo -e "   - Backup runs to ensure data freshness"
echo -e "   - Updated analysis each day"
echo ""
echo -e "3. ${GREEN}Review over the weekend:${NC}"
echo -e "   - Trade sheet available all weekend"
echo -e "   - Plan your trades for the week ahead"
echo ""
echo -e "${BLUE}=====================================================================${NC}"
echo -e "${GREEN}🇦🇺 Optimized for Melbourne, Australia timezone!${NC}"
echo -e "${BLUE}=====================================================================${NC}"
