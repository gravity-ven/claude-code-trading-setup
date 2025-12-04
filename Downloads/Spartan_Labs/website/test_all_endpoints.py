#!/usr/bin/env python3
"""
Comprehensive Website Testing Suite
Tests all APIs and data flows to ensure REAL DATA is available
"""

import requests
import json
import redis
import psycopg2

print("=" * 80)
print("🧪 SPARTAN LABS WEBSITE - COMPREHENSIVE TEST SUITE")
print("=" * 80)

# Test results
tests_passed = 0
tests_failed = 0

def test(name, condition, details=""):
    global tests_passed, tests_failed
    if condition:
        print(f"✅ {name}")
        if details:
            print(f"   {details}")
        tests_passed += 1
    else:
        print(f"❌ {name}")
        if details:
            print(f"   {details}")
        tests_failed += 1

# ========================================
# 1. Redis Data Tests
# ========================================
print("\n📦 REDIS CACHE TESTS:")
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Test: Redis connection
try:
    r.ping()
    test("Redis connection", True)
except Exception as e:
    test("Redis connection", False, f"Error: {e}")

# Test: SPY data in Redis
try:
    spy_data = r.get('market:index:SPY')
    if spy_data:
        spy = json.loads(spy_data)
        test("SPY data in Redis", True, f"Price: ${spy.get('price', 0):.2f}")
    else:
        test("SPY data in Redis", False, "No data found")
except Exception as e:
    test("SPY data in Redis", False, f"Error: {e}")

# Test: Market data keys count
try:
    keys = r.keys('market:*')
    test(f"Market data keys count", len(keys) > 0, f"Found {len(keys)} keys")
except Exception as e:
    test("Market data keys count", False, f"Error: {e}")

# ========================================
# 2. PostgreSQL Database Tests
# ========================================
print("\n🗄️ POSTGRESQL DATABASE TESTS:")
try:
    conn = psycopg2.connect(
        dbname="spartan_research_db",
        user="spartan",
        password="spartan",
        host="localhost"
    )
    cursor = conn.cursor()
    test("PostgreSQL connection", True)

    # Test: Preloaded data count
    cursor.execute("SELECT COUNT(*) FROM preloaded_market_data WHERE timestamp > NOW() - INTERVAL '1 hour'")
    count = cursor.fetchone()[0]
    test("Recent preloaded data", count > 0, f"{count} records in last hour")

    # Test: SPY in database
    cursor.execute("SELECT symbol, price, change_percent FROM preloaded_market_data WHERE symbol = 'SPY' ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()
    if row:
        test("SPY in PostgreSQL", True, f"Price: ${row[1]:.2f}, Change: {row[2]:+.2f}%")
    else:
        test("SPY in PostgreSQL", False, "No SPY data found")

    cursor.close()
    conn.close()

except Exception as e:
    test("PostgreSQL connection", False, f"Error: {e}")

# ========================================
# 3. Main Web Server Tests (Port 8888)
# ========================================
print("\n🌐 MAIN WEB SERVER TESTS (Port 8888):")

# Test: Health endpoint
try:
    r = requests.get('http://localhost:8888/health', timeout=5)
    test("Health endpoint", r.status_code == 200, f"Status: {r.json().get('status')}")
except Exception as e:
    test("Health endpoint", False, f"Error: {e}")

# Test: Index.html loads
try:
    r = requests.get('http://localhost:8888/index.html', timeout=5)
    test("index.html loads", r.status_code == 200, f"Size: {len(r.text)} bytes")
except Exception as e:
    test("index.html loads", False, f"Error: {e}")

# Test: Market indices API
try:
    r = requests.get('http://localhost:8888/api/market/indices', timeout=5)
    data = r.json()
    if 'data' in data and len(data['data']) > 0:
        test("Market indices API", True, f"{len(data['data'])} indices returned")
    else:
        test("Market indices API", False, "No data in response")
except Exception as e:
    test("Market indices API", False, f"Error: {e}")

# ========================================
# 4. Economic Cycle API Tests (Port 5006)
# ========================================
print("\n🌐 ECONOMIC CYCLE API TESTS (Port 5006):")

# Test: Economic Cycle health
try:
    r = requests.get('http://localhost:5006/health', timeout=5)
    data = r.json()
    test("Economic Cycle health", r.status_code == 200, f"FRED configured: {data.get('fred_configured')}")
except Exception as e:
    test("Economic Cycle health", False, f"Error: {e}")

# Test: Dashboard endpoint with real data
try:
    r = requests.get('http://localhost:5006/api/economic-cycle/dashboard', timeout=10)
    data = r.json()

    # Check key indicators
    indicators = data.get('key_indicators', {})
    has_data = any([
        indicators.get('unemployment') is not None,
        indicators.get('inflation_cpi') is not None,
        indicators.get('consumer_confidence') is not None
    ])

    if has_data:
        test("Economic dashboard real data", True,
             f"Unemployment: {indicators.get('unemployment', 'N/A')}%, CPI: {indicators.get('inflation_cpi', 'N/A')}%")
    else:
        test("Economic dashboard real data", False, "No real indicators found")

    # Check NO FAKE DATA policy
    data_quality = data.get('data_quality', {})
    test("NO FAKE DATA policy enforced", data_quality.get('no_fake_data') == True)

except Exception as e:
    test("Economic dashboard endpoint", False, f"Error: {e}")

# ========================================
# 5. Frontend Integration Tests
# ========================================
print("\n🎨 FRONTEND INTEGRATION TESTS:")

# Test: spartan-preloader.js exists
try:
    r = requests.get('http://localhost:8888/js/spartan-preloader.js', timeout=5)
    test("spartan-preloader.js loads", r.status_code == 200, f"Size: {len(r.text)} bytes")
except Exception as e:
    test("spartan-preloader.js", False, f"Error: {e}")

# Test: Economic Cycle Dashboard HTML exists in index.html
try:
    r = requests.get('http://localhost:8888/index.html', timeout=5)
    html = r.text
    has_econ_dashboard = 'Economic Cycle Intelligence' in html or 'cycle-phase-emoji' in html
    test("Economic Cycle Dashboard in HTML", has_econ_dashboard)
except Exception as e:
    test("Economic Cycle Dashboard in HTML", False, f"Error: {e}")

# ========================================
# Summary
# ========================================
print("\n" + "=" * 80)
total_tests = tests_passed + tests_failed
success_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0
print(f"✅ PASSED: {tests_passed}/{total_tests} ({success_rate:.1f}%)")
print(f"❌ FAILED: {tests_failed}/{total_tests}")
print("=" * 80)

if tests_failed == 0:
    print("\n🎉 ALL TESTS PASSED! Website is fully operational with REAL DATA.")
    exit(0)
else:
    print(f"\n⚠️  {tests_failed} tests failed. Review errors above.")
    exit(1)
