#!/bin/bash
# Spartan Research Station - AI Monitoring Interface
# Usage: ./monitor.sh [claude|gemini|auto] [--interactive]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}🤖 Spartan Research Station - AI Monitoring System${NC}"
echo "================================================"

# Parse arguments
AI_CHOICE="${1:-auto}"
INTERACTIVE=""

if [[ "$2" == "--interactive" || "$2" == "-i" ]]; then
    INTERACTIVE="--interactive"
fi

# Validate AI choice
if [[ ! "$AI_CHOICE" =~ ^(claude|gemini|auto)$ ]]; then
    echo -e "${RED}❌ Invalid AI choice: $AI_CHOICE${NC}"
    echo "Usage: $0 [claude|gemini|auto] [--interactive]"
    echo ""
    echo "  claude    - Use Claude Code for monitoring"
    echo "  gemini    - Use Gemini CLI for monitoring"  
    echo "  auto      - Auto-select best available AI (default)"
    echo "  --interactive, -i  - Start interactive monitoring"
    exit 1
fi

echo -e "${YELLOW}🎯 AI Strategy: $AI_CHOICE${NC}"

# Check for available AIs
echo -e "${BLUE}🔍 Checking AI availability...${NC}"

if command -v claude &> /dev/null; then
    CLAUDE_VERSION=$(claude --version 2>/dev/null || echo "unknown")
    echo -e "   Claude Code: ${GREEN}✅ Available${NC} ($CLAUDE_VERSION)"
    CLAUDE_AVAILABLE=true
else
    echo -e "   Claude Code: ${RED}❌ Not found${NC}"
    CLAUDE_AVAILABLE=false
fi

if command -v gemini &> /dev/null; then
    GEMINI_VERSION=$(gemini --version 2>/dev/null || echo "unknown") 
    echo -e "   Gemini CLI:  ${GREEN}✅ Available${NC} ($GEMINI_VERSION)"
    GEMINI_AVAILABLE=true
else
    echo -e "   Gemini CLI:  ${RED}❌ Not found${NC}"
    GEMINI_AVAILABLE=false
fi

# Quick availability check
if [[ "$AI_CHOICE" == "claude" && "$CLAUDE_AVAILABLE" != true ]]; then
    echo -e "${RED}❌ Claude Code not available. Install it first:${NC}"
    echo "   curl -fsSL https://claude.ai/install.sh | sh"
    exit 1
fi

if [[ "$AI_CHOICE" == "gemini" && "$GEMINI_AVAILABLE" != true ]]; then
    echo -e "${RED}❌ Gemini CLI not available. Install it first:${NC}"
    echo "   gem install google-generative-ai"
    exit 1
fi

if [[ "$AI_CHOICE" == "auto" && "$CLAUDE_AVAILABLE" != true && "$GEMINI_AVAILABLE" != true ]]; then
    echo -e "${RED}❌ No AI tools available. Please install one:${NC}"
    echo "   Claude Code: curl -fsSL https://claude.ai/install.sh | sh"
    echo "   Gemini CLI:  gem install google-generative-ai"
    exit 1
fi

echo ""

# Run the monitoring
if python3 ai_monitor.py "$AI_CHOICE" $INTERACTIVE; then
    echo -e "${GREEN}✅ AI Monitoring completed successfully!${NC}"
else
    echo -e "${RED}❌ AI Monitoring failed${NC}"
    exit 1
fi
