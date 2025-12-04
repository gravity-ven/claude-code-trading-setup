#!/usr/bin/env python3
"""
Comprehensive Data Endpoint Test Suite
Tests all available endpoints systematically
"""

import requests
import json
from datetime import datetime

# Server base URL
BASE_URL = 'http://localhost:8888'

def test_endpoint(url, method='GET', params=None, data=None):
    """Test a single endpoint"""
    
    try:
        url = f"{BASE_URL}{url}"
        print(f"Testing: {method} {url}")
        
        if params:
            # Convert dict to query string
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            url += f"?{query_string}"
        
        if data:
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, headers=headers, json=data)
        else:
            response = requests.get(url)
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ SUCCESS: {url}")
                return True, data
            except json.JSONDecodeError:
                print(f"✅ SUCCESS: {url} (non-JSON response)")
                return True, response.text
        else:
            print(f"❌ FAILED: {url} - {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ ERROR: {url} - {e}")
        return False, None

def main():
    print("=== SPARTAN RESEARCH STATION - COMPREHENSIVE ENDPOINT TEST ===")
    print()
    
    test_results = {}
    
    # Test basic health endpoint
    print("1. Testing Health Endpoint...")
    success, data = test_endpoint('/health')
    test_results['health'] = {'success': success, 'data': data}
    
    # Test database endpoints
    print("\n2. Testing Database Endpoints...")
    
    print("   - Database Statistics...")
    success, data = test_endpoint('/api/db/stats')
    test_results['db_stats'] = {'success': success, 'data': data}
    
    print("   - Database Search (test for SPY)...")
    success, data = test_endpoint('/api/db/search?query=SPY&limit=10')
    test_results['db_search_SPY'] = {'success': success, 'data': data}
    
    print("   - Database Symbols...")
    success, data = test_endpoint('/api/db/symbols?limit=10')
    test_results['db_symbols'] = {'success': success, 'data': data}
    
    # Test main market data endpoints (these SHOULD work with simple HTTP server if data is in database)
    print("\n3. Testing Market Data Endpoints...")
    
    print("   - Market Indices...")
    success, data = test_endpoint('/api/market/indices')
    test_results['market_indices'] = {'success': success, 'data': data}
    
    print("   - Market Commodities...")
    success, data = test_endpoint('/api/market/commodities')
    test_results['market_commodities'] = {'success': success, 'data': data}
    
    print("   - Market Forex...")
    success, data = test_endpoint('/api/market/forex')
    test_results['market_forex'] = {'success': success, 'data': data}
    
    print("   - Market Crypto...")
    success, data = test_endpoint('/api/market/crypto')
    test_results['market_crypto'] = {'success': success, 'data': data}
    
    print("   - Volatility...")
    success, data = test_endpoint('/api/market/volatility')
    test_results['market_volatility'] = {'success': success, 'data': data}
    
    # Test economic data endpoints
    print("\n4. Testing Economic Data Endpoints...")
    
    print("   - FRED Economic Indicators...")
    success, data = test_endpoint('/api/economic/fred')
    test_results['economic_fred'] = {'success': success, 'data': data}
    
    print("   - General Economic Indicators...")
    success, data = test_endpoint('/api/economic/indicators')
    test_results['economic_indicators'] = {'success': success, 'data': data}
    
    # Test analytics endpoints
    print("\n5. Testing Analytics Endpoints...")
    
    print("   - Correlations...")
    success, data = test_endpoint('/api/analytics/correlations')
    test_results['analytics_correlations'] = {'success': success, 'data': data}
    
    print("   - Sector Rotation...")
    success, data = test_endpoint('/api/analytics/sector_rotation')
    test_results['analytics_sector_rotation'] = {'success': success, 'data': data}
    
    print("   - Sentiment Indicators...")
    success, data = test_endpoint('/api/analytics/sentiment')
    test_results['analytics_sentiment'] = {'success': success, 'data': data}
    
    print("   - Market Breadth...")
    success, data = test_endpoint('/api/analytics/market_breadth')
    test_results['analytics_market_breadth'] = {'success': success, 'data': data}
    
    # Test compatibility endpoints that pages expect
    print("\n6. Testing Compatibility Endpoints...")
    
    print("   - Yahoo Quote (for pages expecting port 8888)...")
    success, data = test_endpoint('/api/yahoo/quote?symbols=SPY,QQQ')  
    print("   - Yahoo Chart (for charts and graphs)...")
    success, data = test_endpoint('/api/yahoo/chart/SPY?interval=1d&range=1mo') 
    
    # Test error handling
    print("\n7. Testing Error Handling...")
    success, data = test_endpoint('/nonexistent/endpoint')
    test_results['error_handling'] = {'success': success, 'data': data}
    
    # Generate comprehensive report
    print("\n=== TEST RESULTS SUMMARY ===")
    print()
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result['success'])
    
    print(f"Total Endpoints Tested: {total_tests}")
    print(f"✅ Successful Tests: {passed_tests}")
    print(f"❌ Failed Tests: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\n=== FAILED ENDPOINTS ===")
    for endpoint, result in test_results.items():
        if not result['success']:
            print(f"❌ {endpoint}")
    print()
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Data endpoints are working correctly!")
    else:
        print("⚠️ Some tests failed. Check logs for details.")
    
    return test_results

if __name__ == '__main__':
    main()
