#!/bin/bash
# Complete Setup Script for Nano Banana Daily Email
# Configures credentials and installs cron job

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}       Nano Banana Daily Email - Complete Setup        ${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo ""

# Get sender email
echo -e "${YELLOW}Step 1: Enter your Gmail address (sender)${NC}"
read -p "Gmail address: " SENDER_EMAIL

if [[ ! "$SENDER_EMAIL" =~ @gmail\.com$ ]]; then
    echo -e "${RED}Warning: This doesn't look like a Gmail address${NC}"
    read -p "Continue anyway? (y/n): " continue_choice
    if [[ ! "$continue_choice" =~ ^[Yy]$ ]]; then
        echo "Setup cancelled"
        exit 1
    fi
fi

# Password already provided
SENDER_PASSWORD="ekpjeaketpirvck"
RECEIVER_EMAIL="naga.kvv@gmail.com"

echo -e "${GREEN}✓${NC} Sender: $SENDER_EMAIL"
echo -e "${GREEN}✓${NC} Receiver: $RECEIVER_EMAIL"
echo -e "${GREEN}✓${NC} Password: [CONFIGURED - 16 chars]"

# Determine shell config file
if [ -f "$HOME/.bashrc" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
elif [ -f "$HOME/.zshrc" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
else
    SHELL_CONFIG="$HOME/.profile"
fi

echo -e "\n${YELLOW}Step 2: Configuring environment variables${NC}"
echo -e "Target: $SHELL_CONFIG"

# Backup existing config
cp "$SHELL_CONFIG" "${SHELL_CONFIG}.backup_$(date +%Y%m%d_%H%M%S)"
echo -e "${GREEN}✓${NC} Backed up shell config"

# Remove old Nano Banana entries if they exist
sed -i '/# Nano Banana Email Configuration/,+3d' "$SHELL_CONFIG" 2>/dev/null || true

# Add new configuration
cat >> "$SHELL_CONFIG" << EOF

# Nano Banana Email Configuration
export SENDER_EMAIL="$SENDER_EMAIL"
export SENDER_PASSWORD="$SENDER_PASSWORD"
export RECEIVER_EMAIL="$RECEIVER_EMAIL"
EOF

echo -e "${GREEN}✓${NC} Added credentials to $SHELL_CONFIG"

# Export for current session
export SENDER_EMAIL="$SENDER_EMAIL"
export SENDER_PASSWORD="$SENDER_PASSWORD"
export RECEIVER_EMAIL="$RECEIVER_EMAIL"

echo -e "${GREEN}✓${NC} Exported for current session"

# Check Python dependencies
echo -e "\n${YELLOW}Step 3: Checking dependencies${NC}"
python3 -c "import pandas, pandas_ta, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠${NC} Installing missing dependencies..."
    pip3 install pandas pandas_ta requests
fi
echo -e "${GREEN}✓${NC} All dependencies installed"

# Test email script
echo -e "\n${YELLOW}Step 4: Testing email script${NC}"
read -p "Would you like to send a test email now? (y/n): " test_choice

if [[ "$test_choice" =~ ^[Yy]$ ]]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    echo -e "${YELLOW}Sending test email...${NC}"

    python3 "$SCRIPT_DIR/nano_banana_daily_email.py"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Test email sent successfully!"
        echo -e "${GREEN}✓${NC} Check $RECEIVER_EMAIL for the email"
    else
        echo -e "${RED}✗${NC} Test email failed. Check logs for details."
        exit 1
    fi
else
    echo -e "${YELLOW}⚠${NC} Skipping test email"
fi

# Install cron job
echo -e "\n${YELLOW}Step 5: Installing cron job${NC}"
read -p "Install cron job for daily emails at 08:01 AM? (y/n): " cron_choice

if [[ "$cron_choice" =~ ^[Yy]$ ]]; then
    # Run the cron setup script
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    "$SCRIPT_DIR/setup_nano_banana_cron.sh"

    echo -e "${GREEN}✓${NC} Cron job installed!"
else
    echo -e "${YELLOW}⚠${NC} Skipping cron installation"
    echo -e "  You can install it later by running:"
    echo -e "  ${GREEN}./setup_nano_banana_cron.sh${NC}"
fi

# Final summary
echo -e "\n${GREEN}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}             Setup Complete! 🍌                         ${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
echo -e ""
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  Sender:    ${GREEN}$SENDER_EMAIL${NC}"
echo -e "  Receiver:  ${GREEN}$RECEIVER_EMAIL${NC}"
echo -e "  Password:  ${GREEN}[Configured]${NC}"
echo -e ""
echo -e "${YELLOW}Schedule:${NC}"
echo -e "  Daily:     ${GREEN}08:01 AM${NC}"
echo -e "  On boot:   ${GREEN}Catch-up if missed${NC}"
echo -e ""
echo -e "${YELLOW}Logs:${NC}"
echo -e "  Cron:      ${GREEN}../logs/nano_banana_cron.log${NC}"
echo -e "  Script:    ${GREEN}../logs/nano_banana_$(date +%Y%m).log${NC}"
echo -e ""
echo -e "${YELLOW}Useful Commands:${NC}"
echo -e "  Test run:  ${GREEN}./nano_banana_wrapper.sh${NC}"
echo -e "  View logs: ${GREEN}tail -f ../logs/nano_banana_cron.log${NC}"
echo -e "  Edit cron: ${GREEN}crontab -e${NC}"
echo -e "  List jobs: ${GREEN}crontab -l${NC}"
echo -e ""
echo -e "${GREEN}Ready to trade contrarian! 🍌${NC}"
echo -e ""
