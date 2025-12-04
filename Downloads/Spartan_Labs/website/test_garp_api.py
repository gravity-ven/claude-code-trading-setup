#!/usr/bin/env python3
"""
Quick test script for GARP API
Tests basic functionality without running full server
"""

import sys
sys.path.insert(0, '.')

from garp_api import fetch_stock_metrics, calculate_garp_score, STOCK_UNIVERSE

def test_single_stock():
    """Test fetching metrics for a single stock"""
    print("=" * 60)
    print("Testing GARP Stock Screener API")
    print("=" * 60)

    test_symbol = 'AAPL'
    print(f"\n1. Fetching metrics for {test_symbol}...")

    try:
        metrics = fetch_stock_metrics(test_symbol)

        if metrics:
            print(f"✓ Successfully fetched data for {test_symbol}")
            print(f"\nStock Details:")
            print(f"  Symbol: {metrics['symbol']}")
            print(f"  Name: {metrics['name']}")
            print(f"  Sector: {metrics['sector']}")
            print(f"  Price: ${metrics['price']}")
            print(f"  Price Change: {metrics['price_change_pct']}%")
            print(f"\nGARP Metrics:")
            print(f"  P/E Ratio: {metrics['pe_ratio']}")
            print(f"  PEG Ratio: {metrics['peg_ratio']}")
            print(f"  Revenue Growth: {metrics['revenue_growth']}%")
            print(f"  Earnings Growth: {metrics['earnings_growth']}%")
            print(f"  ROE: {metrics['roe']}%")
            print(f"  Debt/Equity: {metrics['debt_to_equity']}")
            print(f"\nGARP Score: {metrics['garp_score']}/100 ({metrics['garp_rating']})")
            print(f"Score Breakdown:")
            for key, value in metrics['score_breakdown'].items():
                print(f"  {key}: {value} pts")

            return True
        else:
            print(f"✗ Failed to fetch data for {test_symbol}")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_scoring_system():
    """Test GARP scoring calculation"""
    print("\n" + "=" * 60)
    print("2. Testing GARP Scoring System")
    print("=" * 60)

    # Test case: Excellent stock
    excellent_metrics = {
        'pe_ratio': 12.0,      # < 15 = 20 pts
        'peg_ratio': 0.8,      # < 1.0 = 30 pts
        'revenue_growth': 25.0, # > 20% = 20 pts
        'earnings_growth': 22.0, # > 20% = 15 pts
        'roe': 25.0,           # > 20% = 10 pts
        'debt_to_equity': 0.3   # < 0.5 = 5 pts
    }

    score = calculate_garp_score(excellent_metrics)
    print(f"\nTest Case - Excellent Stock:")
    print(f"  Expected Score: 100/100")
    print(f"  Actual Score: {score['total_score']}/100")
    print(f"  Rating: {score['rating']}")

    if score['total_score'] == 100:
        print("  ✓ Scoring calculation correct")
        return True
    else:
        print("  ✗ Scoring calculation incorrect")
        return False


def test_stock_universe():
    """Test stock universe configuration"""
    print("\n" + "=" * 60)
    print("3. Testing Stock Universe")
    print("=" * 60)

    total_stocks = sum(len(symbols) for symbols in STOCK_UNIVERSE.values())
    print(f"\nTotal sectors: {len(STOCK_UNIVERSE)}")
    print(f"Total stocks: {total_stocks}")

    print(f"\nBreakdown by sector:")
    for sector, symbols in STOCK_UNIVERSE.items():
        print(f"  {sector}: {len(symbols)} stocks")

    if total_stocks >= 100:
        print(f"\n✓ Stock universe properly configured")
        return True
    else:
        print(f"\n✗ Stock universe incomplete")
        return False


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("GARP API Test Suite")
    print("=" * 60)
    print("\nNOTE: This will make real API calls to Yahoo Finance.")
    print("First test may take 5-10 seconds.\n")

    results = []

    # Run tests
    results.append(("Stock Universe", test_stock_universe()))
    results.append(("Scoring System", test_scoring_system()))
    results.append(("Single Stock Fetch", test_single_stock()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! API is ready to use.")
        print("\nNext steps:")
        print("  1. Run API server: python garp_api.py")
        print("  2. Open dashboard: open garp.html")
    else:
        print("\n✗ Some tests failed. Check configuration.")
        sys.exit(1)
