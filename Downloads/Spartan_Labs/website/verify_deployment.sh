#!/bin/bash
# Spartan Research Station - Deployment Verification Script
# Verifies all critical fixes and production readiness

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║     SPARTAN RESEARCH STATION - DEPLOYMENT VERIFICATION       ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

PASS=0
FAIL=0

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. FILE INTEGRITY CHECKS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check FredApiClient exists
if [ -f "js/fred_api_client.js" ]; then
    echo -e "${GREEN}✅ PASS${NC} - FredApiClient exists (js/fred_api_client.js)"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC} - FredApiClient missing"
    ((FAIL++))
fi

# Check highlights_api.py port configuration
if grep -q "port=5001" api/highlights_api.py; then
    echo -e "${GREEN}✅ PASS${NC} - highlights_api.py using port 5001"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC} - highlights_api.py port not 5001"
    ((FAIL++))
fi

# Check daily_planet_api.py doesn't have placeholder economic data
if grep -q "events = \[" daily_planet_api.py; then
    echo -e "${RED}❌ FAIL${NC} - daily_planet_api.py still has placeholder economic data"
    ((FAIL++))
else
    echo -e "${GREEN}✅ PASS${NC} - daily_planet_api.py placeholder data removed"
    ((PASS++))
fi

# Check test file has correct link
if grep -q "global_capital_flow_swing_trading.html" test_page_validation.html; then
    echo -e "${GREEN}✅ PASS${NC} - test_page_validation.html link corrected"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC} - test_page_validation.html link still broken"
    ((FAIL++))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. PORT CONFLICT CHECKS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Extract ports from API files
PORT_5000=$(grep -c "port=5000" daily_planet_api.py)
PORT_5001=$(grep -c "port=5001" api/highlights_api.py)
PORT_5002=$(grep -c "port=5002" swing_dashboard_api.py)
PORT_5003=$(grep -c "port=5003" garp_api.py)

if [ "$PORT_5000" -eq 1 ]; then
    echo -e "${GREEN}✅ PASS${NC} - daily_planet_api.py: port 5000"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC} - daily_planet_api.py: incorrect port"
    ((FAIL++))
fi

if [ "$PORT_5001" -eq 1 ]; then
    echo -e "${GREEN}✅ PASS${NC} - highlights_api.py: port 5001"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC} - highlights_api.py: incorrect port"
    ((FAIL++))
fi

if [ "$PORT_5002" -eq 1 ]; then
    echo -e "${GREEN}✅ PASS${NC} - swing_dashboard_api.py: port 5002"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC} - swing_dashboard_api.py: incorrect port"
    ((FAIL++))
fi

if [ "$PORT_5003" -eq 1 ]; then
    echo -e "${GREEN}✅ PASS${NC} - garp_api.py: port 5003"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC} - garp_api.py: incorrect port"
    ((FAIL++))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. NO FAKE DATA POLICY CHECKS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check for Math.random() in JavaScript files
RANDOM_COUNT=$(find js -name "*.js" -type f -exec grep -c "Math.random()" {} + 2>/dev/null | awk '{s+=$1} END {print s}')

if [ -z "$RANDOM_COUNT" ] || [ "$RANDOM_COUNT" -eq 0 ]; then
    echo -e "${GREEN}✅ PASS${NC} - Zero Math.random() usage detected"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC} - Math.random() found in $RANDOM_COUNT locations"
    ((FAIL++))
fi

# Check daily_planet_api.py returns proper error for economic calendar
if grep -q "501" daily_planet_api.py && grep -q "Not Implemented" daily_planet_api.py; then
    echo -e "${GREEN}✅ PASS${NC} - Economic calendar returns proper 501 status"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC} - Economic calendar response incorrect"
    ((FAIL++))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. DEPENDENCY CHECKS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check FredApiClient is loaded in timeframe fetchers
FRED_CLIENT_LOADS=$(grep -c "fred_api_client.js" tab_*.html)

if [ "$FRED_CLIENT_LOADS" -ge 4 ]; then
    echo -e "${GREEN}✅ PASS${NC} - FredApiClient loaded in $FRED_CLIENT_LOADS tab files"
    ((PASS++))
else
    echo -e "${YELLOW}⚠️  WARN${NC} - FredApiClient loaded in only $FRED_CLIENT_LOADS tab files"
fi

# Check timeframe fetchers reference FredApiClient
FETCHER_COUNT=$(grep -c "new FredApiClient()" js/timeframe_data_fetcher_*.js 2>/dev/null | wc -l)

if [ "$FETCHER_COUNT" -ge 4 ]; then
    echo -e "${GREEN}✅ PASS${NC} - $FETCHER_COUNT timeframe fetchers use FredApiClient"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC} - Only $FETCHER_COUNT timeframe fetchers use FredApiClient"
    ((FAIL++))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. NAVIGATION CHECKS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check critical pages exist
CRITICAL_PAGES=(
    "index.html"
    "global_capital_flow_swing_trading.html"
    "highlights.html"
    "elite_tools.html"
    "COMPREHENSIVE_TRADING_JOURNAL.html"
)

for page in "${CRITICAL_PAGES[@]}"; do
    if [ -f "$page" ]; then
        echo -e "${GREEN}✅ PASS${NC} - $page exists"
        ((PASS++))
    else
        echo -e "${RED}❌ FAIL${NC} - $page missing"
        ((FAIL++))
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "VERIFICATION SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

TOTAL=$((PASS + FAIL))
SUCCESS_RATE=$((PASS * 100 / TOTAL))

echo "Tests Passed: $PASS"
echo "Tests Failed: $FAIL"
echo "Success Rate: ${SUCCESS_RATE}%"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}║              ✅ DEPLOYMENT VERIFICATION PASSED                ║${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}║                 🚀 READY FOR PRODUCTION 🚀                   ║${NC}"
    echo -e "${GREEN}║                                                               ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Start all API servers"
    echo "2. Test in browser: http://localhost:8888/index.html"
    echo "3. Monitor logs for 24 hours"
    exit 0
else
    echo -e "${RED}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                                               ║${NC}"
    echo -e "${RED}║            ❌ DEPLOYMENT VERIFICATION FAILED                  ║${NC}"
    echo -e "${RED}║                                                               ║${NC}"
    echo -e "${RED}║              RESOLVE ISSUES BEFORE DEPLOYING                  ║${NC}"
    echo -e "${RED}║                                                               ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Review failed tests above and fix issues."
    exit 1
fi
