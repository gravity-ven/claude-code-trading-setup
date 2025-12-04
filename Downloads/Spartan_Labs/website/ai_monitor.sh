#!/bin/bash
# SPARTAN RESEARCH STATION - AI MONITORING INTERFACE
# Unified access to Claude Code and Gemini CLI with shared DNA

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && mkdir -p "$(dirname "${BASH_SOURCE[0]}")")"
cd "$SCRIPT_DIR"

# Display header
echo -e "${PURPLE}🤖 SPARTAN RESEARCH STATION - DUAL AI MONITORING${NC}"
echo -e "${BLUE}Claude Code + Gemini CLI with Shared DNA${NC}"
echo "=================================================="

# Parse arguments
AI_CHOICE="${1:-auto}"
CONTEXT="${2:-ROUTINE_MONITORING}"
INTERACTIVE=""

# Check for interactive flag
if [[ "$3" == "--interactive" || "$3" == "-i" ]]; then
    INTERACTIVE="--interactive"
fi

echo -e "${YELLOW}🎯 Strategy: $AI_CHOICE | Context: $CONTEXT${NC}"

# Check AI availability
echo -e "${BLUE}🔍 Checking AI systems...${NC}"

CLAUDE_AVAILABLE=false
GEMINI_AVAILABLE=false

if command -v claude &> /dev/null; then
    CLAUDE_VERSION=$(claude --version 2>/dev/null || echo "unknown")
    echo -e "   🧠 Claude Code: ${GREEN}✅ Available${NC} ($CLAUDE_VERSION)"
    CLAUDE_AVAILABLE=true
else
    echo -e "   🧠 Claude Code: ${RED}❌ Not found${NC}"
fi

if command -v gemini &> /dev/null; then
    GEMINI_VERSION=$(gemini --version 2>/dev/null || echo "unknown")
    echo -e "   💎 Gemini CLI:  ${GREEN}✅ Available${NC} ($GEMINI_VERSION)"
    GEMINI_AVAILABLE=true
else
    echo -e "   💎 Gemini CLI:  ${RED}❌ Not found${NC}"
fi

# Validate strategy
echo -e "${BLUE}🧬 Applying shared DNA framework...${NC}"

case $AI_CHOICE in
    "claude")
        if [[ "$CLAUDE_AVAILABLE" != true ]]; then
            echo -e "${RED}❌ Claude Code not available. Install:${NC}"
            echo "   curl -fsSL https://claude.ai/install.sh | sh"
            exit 1
        fi
        echo -e "${GREEN}🧠 Using Claude Code with shared monitoring DNA${NC}"
        python3 ai_monitor.py claude $INTERACTIVE
        ;;
        
    "gemini")
        if [[ "$GEMINI_AVAILABLE" != true ]]; then
            echo -e "${RED}❌ Gemini CLI not available. Install:${NC}"
            echo "   gem install google-generative-ai"
            exit 1
        fi
        echo -e "${GREEN}💎 Using Gemini CLI with shared monitoring DNA${NC}"
        python3 ai_monitor.py gemini $INTERACTIVE
        ;;
        
    "auto")
        echo -e "${BLUE}🔄 Auto-selecting best available AI...${NC}"
        python3 ai_monitor.py auto $INTERACTIVE
        ;;
        
    *)
        echo -e "${RED}❌ Invalid AI choice: $AI_CHOICE${NC}"
        echo ""
        echo "Usage: $0 [claude|gemini|auto] [context] [--interactive]"
        echo ""
        echo "  claude    - Use Claude Code with shared DNA"
        echo "  gemini    - Use Gemini CLI with shared DNA"
        echo "  auto      - Auto-select best available AI (default)"
        echo "  context   - Monitoring context (default: ROUTINE_MONITORING)"
        echo "  -i        - Interactive mode"
        echo ""
        echo "Examples:"
        echo "  $0 claude                   # Claude with default monitoring"
        echo "  $0 gemini URGENT_HEALTH     # Gemini with urgent context"
        echo "  $0 auto --interactive       # Auto AI with interactive mode"
        exit 1
        ;;
esac

# Show DNA framework info
echo ""
echo -e "${PURPLE}🧬 Shared DNA Framework Applied:${NC}"
echo "✅ Unified monitoring personality"
echo "✅ Compatible response formats"
echo "✅ Same priority matrix (HIGH/MEDIUM/LOW)"
echo "✅ Identical analysis approach"
echo "✅ Coordinated success metrics"
