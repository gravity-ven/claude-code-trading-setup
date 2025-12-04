#!/bin/bash
# Configure Nano Banana Email Credentials
# This script sets up environment variables for the email system

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Configuring Email Credentials       ${NC}"
echo -e "${GREEN}========================================${NC}"

# Password provided by user (spaces removed)
SENDER_EMAIL="your_email@gmail.com"  # You'll need to update this
SENDER_PASSWORD="ekpjeaketpirvck"
RECEIVER_EMAIL="naga.kvv@gmail.com"

# Determine shell config file
if [ -f "$HOME/.bashrc" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
elif [ -f "$HOME/.zshrc" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
else
    SHELL_CONFIG="$HOME/.profile"
fi

echo -e "${YELLOW}Using shell config: $SHELL_CONFIG${NC}"

# Backup existing config
cp "$SHELL_CONFIG" "${SHELL_CONFIG}.backup_$(date +%Y%m%d_%H%M%S)"
echo -e "${GREEN}✓${NC} Backed up shell config"

# Remove old Nano Banana entries if they exist
sed -i '/# Nano Banana Email Configuration/,+3d' "$SHELL_CONFIG" 2>/dev/null || true

# Add new configuration
cat >> "$SHELL_CONFIG" << 'EOF'

# Nano Banana Email Configuration
export SENDER_EMAIL="your_email@gmail.com"
export SENDER_PASSWORD="ekpjeaketpirvck"
export RECEIVER_EMAIL="naga.kvv@gmail.com"
EOF

echo -e "${GREEN}✓${NC} Added credentials to $SHELL_CONFIG"

# Export for current session
export SENDER_EMAIL="your_email@gmail.com"
export SENDER_PASSWORD="ekpjeaketpirvck"
export RECEIVER_EMAIL="naga.kvv@gmail.com"

echo -e "${GREEN}✓${NC} Exported variables for current session"

# Verify
echo -e "\n${YELLOW}Verifying configuration:${NC}"
echo -e "  SENDER_EMAIL:     ${GREEN}${SENDER_EMAIL}${NC}"
echo -e "  SENDER_PASSWORD:  ${GREEN}[HIDDEN - Length: ${#SENDER_PASSWORD} chars]${NC}"
echo -e "  RECEIVER_EMAIL:   ${GREEN}${RECEIVER_EMAIL}${NC}"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}       Configuration Complete!         ${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e ""
echo -e "${YELLOW}IMPORTANT:${NC} You need to edit the SENDER_EMAIL"
echo -e "           Replace 'your_email@gmail.com' with your actual Gmail address"
echo -e ""
echo -e "Edit file: ${GREEN}$SHELL_CONFIG${NC}"
echo -e "Or export manually:"
echo -e "  ${GREEN}export SENDER_EMAIL=\"your_actual_email@gmail.com\"${NC}"
echo -e ""
echo -e "Then reload: ${GREEN}source $SHELL_CONFIG${NC}"
echo -e ""
