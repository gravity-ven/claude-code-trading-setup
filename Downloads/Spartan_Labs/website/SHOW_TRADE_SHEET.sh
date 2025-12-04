#!/bin/bash
#
# Display the latest trade sheet in a beautiful format
#
# Usage: ./SHOW_TRADE_SHEET.sh
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

TRADE_SHEET="output/latest_trade_sheet.txt"

clear

echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                                    ║${NC}"
echo -e "${CYAN}║            ${GREEN}SPARTAN COT AGENTS${CYAN} - Trade Sheet Viewer             ║${NC}"
echo -e "${CYAN}║                                                                    ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ ! -f "$TRADE_SHEET" ]; then
    echo -e "${YELLOW}⚠️  No trade sheet found${NC}"
    echo ""
    echo -e "${BLUE}ℹ️  To generate a trade sheet:${NC}"
    echo "   ./CHECK_AND_RUN_COT.sh"
    echo ""
    echo -e "${BLUE}📍 Trade sheet location:${NC}"
    echo "   $TRADE_SHEET"
    echo ""
    exit 1
fi

# Get file info
MODIFIED=$(date -r "$TRADE_SHEET" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || stat -c %y "$TRADE_SHEET" | cut -d. -f1)
SIZE=$(wc -l < "$TRADE_SHEET")

echo -e "${GREEN}✅ Trade sheet found!${NC}"
echo ""
echo -e "${BLUE}📄 File: ${TRADE_SHEET}${NC}"
echo -e "${BLUE}📅 Last updated: ${MODIFIED}${NC}"
echo -e "${BLUE}📏 Size: ${SIZE} lines${NC}"
echo ""

echo -e "${CYAN}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  📊 TRADE SHEET CONTENTS${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Display with line numbers and syntax highlighting
if command -v bat &> /dev/null; then
    # Use bat if available (better syntax highlighting)
    bat --style=plain --color=always "$TRADE_SHEET"
elif command -v pygmentize &> /dev/null; then
    # Use pygmentize if available
    pygmentize -f terminal "$TRADE_SHEET"
else
    # Fallback to cat with basic formatting
    cat -n "$TRADE_SHEET" | while read line; do
        # Highlight section headers
        if echo "$line" | grep -q "═\|TOP LONG\|TOP SHORT\|SUMMARY"; then
            echo -e "${YELLOW}${line}${NC}"
        elif echo "$line" | grep -q "Symbol:\|Confidence:"; then
            echo -e "${GREEN}${line}${NC}"
        else
            echo "$line"
        fi
    done
fi

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Parse and display summary if available
if grep -q "TOP LONG" "$TRADE_SHEET" 2>/dev/null; then
    echo -e "${GREEN}📈 Trade Opportunities Found!${NC}"
    echo ""

    # Count long opportunities
    LONG_COUNT=$(grep -c "Symbol:" "$TRADE_SHEET" | head -1 || echo "0")

    echo -e "${BLUE}🎯 Quick Summary:${NC}"

    # Extract top long opportunity
    TOP_LONG=$(grep -A 3 "TOP LONG" "$TRADE_SHEET" | grep "Symbol:" | head -1)
    if [ ! -z "$TOP_LONG" ]; then
        echo -e "   ${GREEN}Top Long: ${TOP_LONG}${NC}"
    fi

    # Extract top short opportunity
    TOP_SHORT=$(grep -A 3 "TOP SHORT" "$TRADE_SHEET" | grep "Symbol:" | head -1)
    if [ ! -z "$TOP_SHORT" ]; then
        echo -e "   ${RED}Top Short: ${TOP_SHORT}${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  No opportunities in current trade sheet${NC}"
    echo ""
    echo -e "${BLUE}ℹ️  This usually means:${NC}"
    echo "   • Waiting for new CFTC data (released Fridays)"
    echo "   • No high-confidence setups at this time"
    echo "   • Market conditions don't meet criteria"
fi

echo ""
echo -e "${BLUE}🔄 Refresh trade sheet:${NC}"
echo "   ./CHECK_AND_RUN_COT.sh"
echo ""
echo -e "${BLUE}📋 View detailed logs:${NC}"
echo "   tail -f logs/agents.log"
echo ""
