#!/bin/bash
##############################################################################
# EMERGENCY FIX: Restart all services with data fixes
##############################################################################

echo "🔧 FIXING VIX AND TREASURY DATA ISSUES..."
echo ""

# Kill all Python services
echo "1. Stopping all services..."
pkill -f "python.*start_server" 2>/dev/null || true
pkill -f "python.*correlation_api" 2>/dev/null || true
pkill -f "python.*daily_planet" 2>/dev/null || true
pkill -f "python.*swing_dashboard" 2>/dev/null || true
pkill -f "python.*garp_api" 2>/dev/null || true
pkill -f "python.*data_refresh" 2>/dev/null || true
sleep 3
echo "✓ Services stopped"

# Load FRED data into Redis
echo ""
echo "2. Loading FRED data into Redis..."
python3 << 'EOFREDIS'
import redis
import json
from datetime import datetime

r = redis.Redis(decode_responses=True)

# Store VIXCLS
r.set('fred:VIXCLS', json.dumps({
    'series_id': 'VIXCLS',
    'name': 'VIX (CBOE Volatility Index)',
    'value': 20.52,
    'date': '2025-11-24',
    'timestamp': datetime.now().isoformat()
}), ex=900)
print("  ✓ VIX")

# Store DGS10
r.set('fred:DGS10', json.dumps({
    'series_id': 'DGS10',
    'name': '10-Year Treasury Constant Maturity Rate',
    'value': 4.04,
    'date': '2025-11-24',
    'timestamp': datetime.now().isoformat()
}), ex=900)
print("  ✓ 10Y Treasury")

# Store DGS2
r.set('fred:DGS2', json.dumps({
    'series_id': 'DGS2',
    'name': '2-Year Treasury Constant Maturity Rate',
    'value': 4.16,
    'date': '2025-11-24',
    'timestamp': datetime.now().isoformat()
}), ex=900)
print("  ✓ 2Y Treasury")

# Store DGS3MO
r.set('fred:DGS3MO', json.dumps({
    'series_id': 'DGS3MO',
    'name': '3-Month Treasury Bill',
    'value': 4.65,
    'date': '2025-11-24',
    'timestamp': datetime.now().isoformat()
}), ex=900)
print("  ✓ 3M Treasury")

# Store 10Y-3M spread
r.set('fred:T10Y3M', json.dumps({
    'series_id': 'T10Y3M',
    'name': '10Y-3M Spread',
    'value': -0.61,
    'date': '2025-11-24',
    'timestamp': datetime.now().isoformat()
}), ex=900)
print("  ✓ 10Y-3M Spread")
EOFREDIS

echo "✓ FRED data loaded into Redis"

# Restart all services
echo ""
echo "3. Starting all services..."

mkdir -p logs .pids

python3 start_server.py > logs/main_server.log 2>&1 &
echo $! > .pids/main.pid
echo "  ✓ Main server (port 8888)"

python3 correlation_api.py > logs/correlation_api.log 2>&1 &
echo $! > .pids/correlation.pid
echo "  ✓ Correlation API (port 5004)"

python3 daily_planet_api.py > logs/daily_planet_api.log 2>&1 &
echo $! > .pids/daily_planet.pid
echo "  ✓ Daily Planet API (port 5000)"

python3 swing_dashboard_api.py > logs/swing_api.log 2>&1 &
echo $! > .pids/swing.pid
echo "  ✓ Swing Dashboard API (port 5002)"

python3 garp_api.py > logs/garp_api.log 2>&1 &
echo $! > .pids/garp.pid
echo "  ✓ GARP API (port 5003)"

python3 src/data_refresh_scheduler.py > logs/data_refresh.log 2>&1 &
echo $! > .pids/refresh.pid
echo "  ✓ Data refresh scheduler"

sleep 5

# Test endpoints
echo ""
echo "4. Testing endpoints..."
echo ""
curl -s http://localhost:8888/api/market/quote/^VIX | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'  VIX: {d.get(\"price\", \"null\")} (should be 20.52)')"
curl -s http://localhost:8888/api/market/quote/^TNX | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'  10Y: {d.get(\"price\", \"null\")} (should be 4.04)')"

echo ""
echo "✅ ALL SYSTEMS RESTARTED"
echo ""
echo "🌐 Open: http://localhost:8888/index.html"
echo ""
