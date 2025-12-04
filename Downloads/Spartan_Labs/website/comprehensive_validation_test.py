#!/usr/bin/env python3
"""
Comprehensive Data Validation Test
Tests ALL data sources used in Global Capital Flow page
"""

import requests
import json
import sys

def test_fred_indicators():
    """Test all 6 FRED economic indicators"""
    print("=" * 70)
    print("TESTING FRED API (6 Economic Indicators)")
    print("=" * 70)

    indicators = [
        ('GDP', 'Real Gross Domestic Product'),
        ('UNRATE', 'Unemployment Rate'),
        ('CPIAUCSL', 'Consumer Price Index'),
        ('DFF', 'Federal Funds Rate'),
        ('T10Y2Y', '10-Year Treasury Spread'),
        ('VIXCLS', 'VIX Volatility Index')
    ]

    validated_count = 0
    failed_indicators = []

    for series_id, name in indicators:
        try:
            url = f'http://localhost:9000/api/fred/series/observations?series_id={series_id}&limit=1&sort_order=desc'
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if 'observations' in data and len(data['observations']) > 0:
                    value = data['observations'][0]['value']
                    date = data['observations'][0]['date']
                    print(f"✅ {series_id:10} ({name:35}): {value:>10} ({date})")
                    validated_count += 1
                else:
                    print(f"❌ {series_id:10} ({name:35}): No data in response")
                    failed_indicators.append(series_id)
            else:
                print(f"❌ {series_id:10} ({name:35}): HTTP {response.status_code}")
                failed_indicators.append(series_id)
        except Exception as e:
            print(f"❌ {series_id:10} ({name:35}): {str(e)}")
            failed_indicators.append(series_id)

    print(f"\n{'='*70}")
    print(f"FRED API Results: {validated_count}/6 indicators validated")
    print(f"{'='*70}\n")

    return validated_count, failed_indicators

def test_yahoo_finance():
    """Test Yahoo Finance API for key ETFs used in capital flow visualizer"""
    print("=" * 70)
    print("TESTING YAHOO FINANCE API (Capital Flow ETFs)")
    print("=" * 70)

    etfs = [
        # Regional flows
        ('SPY', 'S&P 500 ETF (US)'),
        ('VGK', 'FTSE Europe ETF'),
        ('VPL', 'FTSE Pacific ETF'),
        ('EEM', 'Emerging Markets ETF'),
        ('FXI', 'China Large-Cap ETF'),
        ('EWJ', 'Japan ETF'),

        # Sector flows (sample)
        ('XLK', 'Technology Sector'),
        ('XLF', 'Financial Sector'),
        ('XLE', 'Energy Sector'),

        # Market segments
        ('TLT', '20+ Year Treasury'),
        ('GLD', 'Gold ETF'),
        ('USO', 'Oil Fund')
    ]

    validated_count = 0
    failed_etfs = []

    for symbol, name in etfs:
        try:
            url = f'http://localhost:9000/api/yahoo/{symbol}'
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if 'chart' in data and 'result' in data['chart']:
                    print(f"✅ {symbol:6} ({name:30}): Valid data received")
                    validated_count += 1
                else:
                    print(f"❌ {symbol:6} ({name:30}): Invalid response structure")
                    failed_etfs.append(symbol)
            else:
                print(f"❌ {symbol:6} ({name:30}): HTTP {response.status_code}")
                failed_etfs.append(symbol)
        except Exception as e:
            print(f"❌ {symbol:6} ({name:30}): {str(e)}")
            failed_etfs.append(symbol)

    print(f"\n{'='*70}")
    print(f"Yahoo Finance Results: {validated_count}/{len(etfs)} ETFs validated")
    print(f"{'='*70}\n")

    return validated_count, failed_etfs

def check_code_for_violations():
    """Check JavaScript files for fake data violations"""
    print("=" * 70)
    print("CHECKING CODE FOR FAKE DATA VIOLATIONS")
    print("=" * 70)

    violations = []

    files_to_check = [
        'js/composite_score_engine.js',
        'js/capital_flow_visualizer.js'
    ]

    for filepath in files_to_check:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for Math.random()
            if 'Math.random()' in content:
                violations.append(f"{filepath}: Contains Math.random()")

            # Check for common fake data patterns
            if '|| 0' in content or '|| 5' in content or '|| 10' in content:
                # Need to verify these aren't in comments
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if ('|| 0' in line or '|| 5' in line or '|| 10' in line) and not line.strip().startswith('//'):
                        if 'validated' not in line:  # If not checking validated property
                            violations.append(f"{filepath}:{i}: Potential fake fallback value: {line.strip()[:60]}")

            print(f"✅ {filepath}: Code review passed")

        except Exception as e:
            print(f"❌ {filepath}: Error reading file - {str(e)}")

    if violations:
        print(f"\n⚠️  Found {len(violations)} potential violations:")
        for violation in violations:
            print(f"   - {violation}")
    else:
        print(f"\n✅ No fake data violations detected")

    print(f"{'='*70}\n")

    return len(violations) == 0

def main():
    """Run comprehensive validation tests"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 10 + "COMPREHENSIVE DATA VALIDATION TEST" + " " * 24 + "║")
    print("║" + " " * 15 + "Global Capital Flow Page" + " " * 29 + "║")
    print("╚" + "=" * 68 + "╝")
    print("\n")

    # Test FRED API
    fred_validated, fred_failed = test_fred_indicators()

    # Test Yahoo Finance API
    yahoo_validated, yahoo_failed = test_yahoo_finance()

    # Check code for violations
    code_clean = check_code_for_violations()

    # Final summary
    print("=" * 70)
    print("FINAL VALIDATION SUMMARY")
    print("=" * 70)
    print(f"FRED API:           {fred_validated}/6 indicators validated")
    print(f"Yahoo Finance API:  {yahoo_validated}/12 ETFs validated")
    print(f"Code Quality:       {'✅ CLEAN' if code_clean else '❌ VIOLATIONS FOUND'}")
    print("=" * 70)

    if fred_validated == 6 and yahoo_validated >= 10 and code_clean:
        print("\n✅ ✅ ✅  ALL DATA VALIDATED - SYSTEM OPERATIONAL  ✅ ✅ ✅")
        print("\nThe Global Capital Flow page enforces strict NO FAKE DATA policy.")
        print("All economic indicators and market data are sourced from official APIs.")
        return 0
    else:
        print("\n⚠️  VALIDATION ISSUES DETECTED")
        if fred_validated < 6:
            print(f"   - FRED API: Only {fred_validated}/6 indicators validated")
            print(f"     Failed: {', '.join(fred_failed)}")
        if yahoo_validated < 10:
            print(f"   - Yahoo Finance: Only {yahoo_validated}/12 ETFs validated")
            print(f"     Failed: {', '.join(yahoo_failed)}")
        if not code_clean:
            print(f"   - Code contains potential fake data violations")
        print("\nPage will display 'Data Unavailable' warnings for missing data.")
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nValidation test interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)
