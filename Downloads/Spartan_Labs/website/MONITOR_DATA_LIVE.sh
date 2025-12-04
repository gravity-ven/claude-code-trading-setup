#!/usr/bin/env bash
#
# LIVE DATA INTEGRITY MONITOR
# ============================
#
# Real-time dashboard showing what data is available RIGHT NOW
#

echo "================================================================================"
echo "🔴 LIVE DATA INTEGRITY MONITOR"
echo "================================================================================"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Check processes
echo "🖥️  PROCESS STATUS"
echo "--------------------------------------------------------------------------------"

if pgrep -f "agent_orchestrator.py" > /dev/null; then
    echo "✅ Agent Orchestrator:     RUNNING (PID: $(pgrep -f agent_orchestrator.py))"
else
    echo "❌ Agent Orchestrator:     NOT RUNNING"
fi

if pgrep -f "data_guardian_agent_full.py" > /dev/null; then
    echo "✅ Data Guardian Scanner:  RUNNING (PID: $(pgrep -f data_guardian_agent_full.py))"
else
    echo "❌ Data Guardian Scanner:  NOT RUNNING"
fi

if pgrep -f "comprehensive_macro_scanner.py" > /dev/null; then
    echo "✅ Macro Scanner:          RUNNING (PID: $(pgrep -f comprehensive_macro_scanner.py))"
else
    echo "❌ Macro Scanner:          NOT RUNNING"
fi

if pgrep -f "start_server.py" > /dev/null; then
    echo "✅ Web Server:             RUNNING (PID: $(pgrep -f start_server.py))"
else
    echo "❌ Web Server:             NOT RUNNING"
fi

echo ""

# Check Redis data
echo "📦 REDIS CACHE DATA (Main Page Requirements)"
echo "--------------------------------------------------------------------------------"

# Function to check Redis key and display status
check_redis_key() {
    local key=$1
    local label=$2
    local value=$(redis-cli GET "$key" 2>/dev/null)

    if [ -n "$value" ] && [ "$value" != "(nil)" ]; then
        # Extract price/value from JSON
        local price=$(echo "$value" | jq -r '.price // .value // "N/A"' 2>/dev/null)
        local source=$(echo "$value" | jq -r '.source // "unknown"' 2>/dev/null)
        local ttl=$(redis-cli TTL "$key" 2>/dev/null)

        if [ "$ttl" == "-1" ]; then
            echo "✅ $label | $price | Source: $source | TTL: No expiry"
        elif [ "$ttl" == "-2" ]; then
            echo "❌ $label | EXPIRED"
        else
            echo "✅ $label | $price | Source: $source | TTL: ${ttl}s"
        fi
    else
        echo "❌ $label | NO DATA"
    fi
}

# Check market indices
echo ""
echo "Stock/ETF Prices:"
check_redis_key "market:symbol:SPY" "  SPY (S&P 500)        "
check_redis_key "market:symbol:UUP" "  UUP (Dollar Index)   "
check_redis_key "market:symbol:GLD" "  GLD (Gold)           "
check_redis_key "market:symbol:USO" "  USO (Oil)            "
check_redis_key "market:symbol:HYG" "  HYG (High Yield)     "

echo ""
echo "Crypto Prices:"
check_redis_key "market:symbol:BTC-USD" "  BTC (Bitcoin)        "
check_redis_key "market:symbol:ETH-USD" "  ETH (Ethereum)       "
check_redis_key "market:symbol:SOL-USD" "  SOL (Solana)         "

echo ""
echo "Economic Indicators:"
check_redis_key "economic:DGS10" "  Treasury 10Y Yield   "
check_redis_key "economic:DTB3" "  Treasury 3M Yield    "
check_redis_key "economic:VIXCLS" "  VIX Index            "

echo ""
echo "Composite Indicators:"
check_redis_key "composite:symbol:RECESSION_PROB" "  Recession Probability"
check_redis_key "composite:symbol:MARKET_NARRATIVE" "  Market Narrative     "

echo ""
echo "Forex:"
check_redis_key "market:symbol:AUDJPY=X" "  AUD/JPY              "

echo ""

# Calculate success rate
total_checked=14
found=0

for key in "market:symbol:SPY" "market:symbol:UUP" "market:symbol:GLD" "market:symbol:USO" "market:symbol:HYG" "market:symbol:BTC-USD" "market:symbol:ETH-USD" "market:symbol:SOL-USD" "economic:DGS10" "economic:DTB3" "economic:VIXCLS" "composite:symbol:RECESSION_PROB" "composite:symbol:MARKET_NARRATIVE" "market:symbol:AUDJPY=X"; do
    if redis-cli EXISTS "$key" | grep -q "1"; then
        ((found++))
    fi
done

success_rate=$((found * 100 / total_checked))

echo "Summary: $found/$total_checked keys found ($success_rate% data coverage)"

echo ""

# Check PostgreSQL
echo "🗄️  POSTGRESQL DATABASE"
echo "--------------------------------------------------------------------------------"

if pg_isready -q 2>/dev/null; then
    recent_count=$(psql -d spartan_research_db -U spartan -t -c "SELECT COUNT(DISTINCT symbol) FROM preloaded_market_data WHERE timestamp > NOW() - INTERVAL '24 hours';" 2>/dev/null | xargs)

    if [ -n "$recent_count" ] && [ "$recent_count" != "0" ]; then
        echo "✅ PostgreSQL: $recent_count symbols with data in last 24 hours"
    else
        echo "⚠️  PostgreSQL: Connected but no recent data"
    fi
else
    echo "❌ PostgreSQL: Not accessible"
fi

echo ""

# Recent agent activity
echo "🤖 RECENT AGENT ACTIVITY (Last 20 log entries)"
echo "--------------------------------------------------------------------------------"

if [ -f "agent_orchestrator_fixed.log" ]; then
    tail -20 agent_orchestrator_fixed.log | grep -E "✅|❌|Retrieved|Updated" | tail -10
else
    echo "⚠️  Log file not found"
fi

echo ""

# Overall health
echo "================================================================================"
echo "📊 OVERALL HEALTH"
echo "================================================================================"

if [ "$success_rate" -ge 90 ]; then
    echo "🟢 EXCELLENT ($success_rate% coverage) - All systems operational"
elif [ "$success_rate" -ge 70 ]; then
    echo "🟡 GOOD ($success_rate% coverage) - Most data available"
elif [ "$success_rate" -ge 50 ]; then
    echo "🟠 DEGRADED ($success_rate% coverage) - Significant data missing"
else
    echo "🔴 CRITICAL ($success_rate% coverage) - Most data unavailable"
fi

echo ""
echo "Last Updated: $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================================================"
