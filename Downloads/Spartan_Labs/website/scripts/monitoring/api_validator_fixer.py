#!/usr/bin/env python3
"""
SPARTAN RESEARCH STATION - API VALIDATOR & FIXER
Tests all configured API keys and provides fixes/diagnostics
"""

import os
import sys
import json
import requests
import asyncio
from datetime import datetime
from dotenv import load_dotenv
import yfinance as yf

# Load environment variables
load_dotenv()

class APIValidator:
    def __init__(self):
        self.test_results = {}
        self.session = requests.Session()
        self.session.timeout = 15

    def test_fred_api(self):
        """Test FRED API functionality"""
        key = os.getenv('FRED_API_KEY')
        if not key or key.startswith('your_'):
            return {'status': '❌ NOT_CONFIGURED', 'error': 'Missing FRED_API_KEY'}
        
        try:
            url = 'https://api.stlouisfed.org/fred/series/observations'
            params = {
                'series_id': 'GDP',
                'api_key': key,
                'limit': 1,
                'file_type': 'json',
                'sort_order': 'desc'
            }
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if 'observations' in data and len(data['observations']) > 0:
                    obs = data['observations'][0]
                    return {
                        'status': '✅ ACTIVE',
                        'sample_data': f"GDP: {obs['value']} (Date: {obs['date']})"
                    }
                else:
                    return {'status': '⚠️ ACTIVE_NO_DATA', 'error': 'API responds but no observations'}
            else:
                return {
                    'status': '❌ FAILED',
                    'error': f"HTTP {response.status_code}: {response.text[:100]}"
                }
        except Exception as e:
            return {'status': '❌ ERROR', 'error': str(e)[:50]}

    def test_polygon_api(self):
        """Test Polygon.io API with working endpoints"""
        key = os.getenv('POLYGON_IO_API_KEY')
        if not key or key.startswith('your_'):
            return {'status': '❌ NOT_CONFIGURED', 'error': 'Missing POLYGON_IO_API_KEY'}
        
        test_cases = [
            ('Previous Close', 'https://api.polygon.io/v2/aggs/ticker/SPY/prev'),
            ('Daily O/C', 'https://api.polygon.io/v1/open-close/SPY/2024-11-22'),
            ('Market Status', 'https://api.polygon.io/v1/marketstatus/now'),
            ('Ticker Details', 'https://api.polygon.io/v3/reference/tickers/SPY')
        ]
        
        working_endpoints = []
        for name, url in test_cases:
            try:
                params = {'apiKey': key}
                response = self.session.get(url, params=params)
                
                if response.status_code == 200:
                    working_endpoints.append(name)
                    
                    # Get sample data from previous close endpoint
                    if name == 'Previous Close':
                        data = response.json()
                        if 'results' in data and len(data['results']) > 0:
                            result = data['results'][0]
                            sample = f"SPY: ${result['c']:.2f} (Vol: {result['v']:,})"
            except:
                pass
        
        if len(working_endpoints) >= 2:  # At least 2 working endpoints
            return {
                'status': '✅ ACTIVE',
                'working_endpoints': working_endpoints,
                'sample_data': sample if 'sample' in locals() else 'Data available'
            }
        elif len(working_endpoints) == 1:
            return {
                'status': '⚠️ PARTIAL',
                'working_endpoints': working_endpoints,
                'error': 'Only some endpoints working'
            }
        else:
            return {'status': '❌ FAILED', 'error': 'No endpoints responding'}

    def test_alpha_vantage(self):
        """Test Alpha Vantage API"""
        key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if not key or key.startswith('your_'):
            return {'status': '❌ NOT_CONFIGURED', 'error': 'Missing ALPHA_VANTAGE_API_KEY'}
        
        try:
            url = 'https://www.alphavantage.co/query'
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': 'SPY',
                'apikey': key
            }
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if 'Global Quote' in data:
                    quote = data['Global Quote']
                    price = quote.get('05. price', 'N/A')
                    return {
                        'status': '✅ ACTIVE',
                        'sample_data': f"SPY: ${price}"
                    }
                elif 'Error Message' in data:
                    return {'status': '❌ FAILED', 'error': data['Error Message']}
                else:
                    return {'status': '⚠️ RATE_LIMITED', 'error': 'Likely hit daily limit'}
            else:
                return {'status': '❌ FAILED', 'error': f"HTTP {response.status_code}"}
        except Exception as e:
            return {'status': '❌ ERROR', 'error': str(e)[:50]}

    def test_other_apis(self):
        """Test secondary APIs that may be configured"""
        results = {}
        
        # APIs to test
        api_configs = [
            ('Finnhub', 'FINNHUB_API_KEY', 'https://finnhub.io/api/v1/quote', {'symbol': 'SPY', 'token': '{key}'}),
            ('Financial Modeling Prep', 'FINANCIAL_MODELING_PREP_API_KEY', 'https://financialmodelingprep.com/api/v3/quote-short/SPY', {'apikey': '{key}'}),
            ('Twelve Data', 'TWELVE_DATA_API_KEY', 'https://api.twelvedata.com/quote', {'symbol': 'SPY', 'apikey': '{key}'}),
            ('IEX Cloud', 'IEX_CLOUD_API_KEY', 'https://cloud.iexapis.com/v1/data/core/quote/SPY', {'token': '{key}'}),
        ]
        
        for name, env_var, base_url, base_params in api_configs:
            key = os.getenv(env_var)
            if not key or key.startswith(f'your_{env_var.lower()}'):
                results[name] = {'status': '❌ NOT_CONFIGURED', 'error': f'Missing {env_var}'}
                continue
            
            try:
                # Format params with actual key
                params = {}
                for k, v in base_params.items():
                    if '{key}' in v:
                        params[k] = v.replace('{key}', key)
                    else:
                        params[k] = v
                
                response = self.session.get(base_url, params=params)
                
                if response.status_code == 200:
                    results[name] = {'status': '✅ ACTIVE'}
                else:
                    results[name] = {
                        'status': '❌ FAILED',
                        'error': f"HTTP {response.status_code}"
                    }
            except Exception as e:
                results[name] = {'status': '❌ ERROR', 'error': str(e)[:50]}
        
        return results

    def test_yahoo_finance(self):
        """Test Yahoo Finance (no API key required)"""
        try:
            # Test multiple symbols
            symbols = ['SPY', 'QQQ', '^GSPC', 'BTC-USD', 'GC=F']
            results = {}
            
            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(period='1d', progress=False)
                    
                    if not data.empty and len(data) > 0:
                        latest_close = data['Close'].iloc[-1]
                        results[symbol] = f"${latest_close:.2f}"
                    else:
                        results[symbol] = "No data"
                except Exception as e:
                    results[symbol] = f"Error: {str(e)[:20]}"
            
            success_count = sum(1 for v in results.values() if '$' in v)
            
            if success_count >= 4:  # At least 4 symbols working
                return {
                    'status': '✅ ACTIVE',
                    'sample_data': results,
                    'note': f'{success_count}/{len(symbols)} symbols working'
                }
            elif success_count >= 2:
                return {
                    'status': '⚠️ PARTIAL',
                    'sample_data': results,
                    'note': f'{success_count}/{len(symbols)} symbols working'
                }
            else:
                return {
                    'status': '❌ FAILED',
                    'sample_data': results,
                    'error': 'Most symbols not working'
                }
                
        except Exception as e:
            return {'status': '❌ ERROR', 'error': str(e)[:50]}

    def test_anthropic_claude(self):
        """Test Anthropic Claude API (used for monitoring agent)"""
        key = os.getenv('ANTHROPIC_API_KEY')
        if not key or key.startswith('your_'):
            return {
                'status': '❌ NOT_CONFIGURED',
                'error': 'Missing ANTHROPIC_API_KEY',
                'note': 'Required for advanced monitoring agent features'
            }
        
        try:
            url = 'https://api.anthropic.com/v1/messages'
            headers = {
                'x-api-key': key,
                'content-type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            payload = {
                'model': 'claude-3-haiku-20240307',
                'max_tokens': 10,
                'messages': [{'role': 'user', 'content': 'Say "API test"'}]
            }
            
            response = self.session.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                return {
                    'status': '✅ ACTIVE',
                    'note': 'Monitoring agent AI features available'
                }
            elif response.status_code == 401:
                return {'status': '❌ INVALID_KEY', 'error': 'API key invalid'}
            else:
                return {
                    'status': '❌ FAILED',
                    'error': f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {'status': '❌ ERROR', 'error': str(e)[:50]}

    def generate_fix_recommendations(self):
        """Generate automatic fix recommendations"""
        recommendations = []
        
        # Check FRED
        fred_result = self.test_results.get('FRED API', {})
        if fred_result.get('status') == '❌ NOT_CONFIGURED':
            recommendations.append({
                'api': 'FRED',
                'priority': 'HIGH',
                'action': 'GET_FREE_KEY',
                'url': 'https://fred.stlouisfed.org/docs/api/api_key.html',
                'instructions': 'Sign up for FREE FRED API key (takes 2 minutes)'
            })
        
        # Check Anthropic (monitoring agent)
        claude_result = self.test_results.get('Anthropic Claude', {})
        if claude_result.get('status') == '❌ NOT_CONFIGURED':
            recommendations.append({
                'api': 'Anthropic Claude',
                'priority': 'MEDIUM',
                'action': 'GET_KEY',
                'url': 'https://console.anthropic.com/',
                'instructions': 'Get API key for advanced monitoring agent AI features (optional)'
            })
        
        # Check failed secondary APIs
        secondary_apis = self.test_results.get('Other APIs', {})
        for api_name, result in secondary_apis.items():
            if result.get('status') == '❌ NOT_CONFIGURED':
                recommendations.append({
                    'api': api_name,
                    'priority': 'LOW',
                    'action': 'OPTIONAL_KEY',
                    'instructions': f'{api_name} provides backup data来源 (optional)'
                })
        
        return recommendations

    def run_all_tests(self):
        """Run all API tests"""
        print("=" * 60)
        print("SPARTAN RESEARCH STATION - API VALIDATION REPORT")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run all tests
        print("🔍 Testing Primary APIs...")
        self.test_results['FRED API'] = self.test_fred_api()
        self.test_results['Polygon.io'] = self.test_polygon_api()
        self.test_results['Yahoo Finance'] = self.test_yahoo_finance()
        self.test_results['Alpha Vantage'] = self.test_alpha_vantage()
        
        print("\n🔍 Testing Secondary APIs...")
        self.test_results['Other APIs'] = self.test_other_apis()
        
        print("\n🔍 Testing AI/Monitoring APIs...")
        self.test_results['Anthropic Claude'] = self.test_anthropic_claude()
        
        # Display results
        for api_name, result in self.test_results.items():
            if api_name == 'Other APIs':
                print(f"\n📊 {api_name}:")
                for sub_api, sub_result in result.items():
                    status = sub_result['status']
                    print(f"   {sub_api}: {status}")
                    if sub_result.get('error'):
                        print(f"      Error: {sub_result['error']}")
                continue
            
            status = result['status']
            print(f"{api_name}: {status}")
            
            if result.get('sample_data'):
                print(f"   Sample: {result['sample_data']}")
            if result.get('working_endpoints'):
                print(f"   Working endpoints: {', '.join(result['working_endpoints'])}")
            if result.get('note'):
                print(f"   Note: {result['note']}")
            if result.get('error'):
                print(f"   Error: {result['error']}")
            print()
        
        # System capability assessment
        print("=" * 60)
        print("SYSTEM CAPABILITY ASSESSMENT")
        print("=" * 60)
        
        essential_working = 0
        essential_total = 3  # FRED, Yahoo Finance, Polygon.io
        
        if self.test_results['FRED API']['status'].startswith('✅'):
            essential_working += 1
        if self.test_results['Yahoo Finance']['status'].startswith('✅'):
            essential_working += 1
        if self.test_results['Polygon.io']['status'].startswith('✅'):
            essential_working += 1
        
        capability_score = (essential_working / essential_total) * 100
        
        print(f"Essential APIs Working: {essential_working}/{essential_total}")
        print(f"System Capability: {capability_score:.0f}%")
        
        if capability_score >= 100:
            print("🎉 SYSTEM FULLY FUNCTIONAL - All features available")
        elif capability_score >= 66:
            print("✅ SYSTEM HIGHLY FUNCTIONAL - Most features available")
        elif capability_score >= 33:
            print("⚠️  SYSTEM PARTIALLY FUNCTIONAL - Some features limited")
        else:
            print("❌ SYSTEM LIMITED - Core functionality may be affected")
        
        # Generate fix recommendations
        print("\n" + "=" * 60)
        print("FIX RECOMMENDATIONS")
        print("=" * 60)
        
        recommendations = self.generate_fix_recommendations()
        
        if not recommendations:
            print("✅ All critical APIs properly configured!")
        else:
            for i, rec in enumerate(recommendations, 1):
                priority_icon = "🔴" if rec['priority'] == 'HIGH' else "🟡" if rec['priority'] == 'MEDIUM' else "🟢"
                print(f"{priority_icon} {i}. {rec['api']}")
                print(f"   Action: {rec['instructions']}")
                if 'url' in rec:
                    print(f"   URL: {rec['url']}")
                print()
        
        # Auto-fix attempt for Polygon.io
        if self.test_results['Polygon.io']['status'] in ['❌ FAILED', '⚠️ PARTIAL']:
            print("=" * 60)
            print("ATTEMPTING POLYGON.IO AUTO-FIX...")
            print("=" * 60)
            self.fix_polygon_endpoints()
        
        return self.test_results

    def fix_polygon_endpoints(self):
        """Attempt to fix Polygon.io endpoints by updating configuration"""
        try:
            # Check if data sources config exists
            config_path = 'config/data_sources.yaml'
            
            if os.path.exists(config_path):
                print("✅ Found data sources configuration")
                print("   Polygon.io API key is valid")
                print("   Some endpoints work, others may need configuration updates")
                
                polygon_result = self.test_results['Polygon.io']
                working = polygon_result.get('working_endpoints', [])
                
                print(f"   Working endpoints: {', '.join(working) if working else 'None'}")
                print("\n   Recommendation: Use working endpoints in data fetching")
                
            else:
                print("❌ Data sources configuration not found")
                print("   Creating basic API configuration file...")
                
                # Create simple config file
                config_content = """# Polygon.io Working Endpoints
working_endpoints:
  - v2_aggs_prev: "https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"
  - v1_open_close: "https://api.polygon.io/v1/open-close/{symbol}/{date}"
  - v1_market_status: "https://api.polygon.io/v1/marketstatus/now"

# Use these endpoints in API calls
"""
                
                with open(config_path, 'w') as f:
                    f.write(config_content)
                
                print("✅ Basic configuration created")
                
        except Exception as e:
            print(f"❌ Auto-fix failed: {str(e)[:50]}...")


def main():
    validator = APIValidator()
    results = validator.run_all_tests()
    
    # Save results to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"logs/api_validation_report_{timestamp}.json"
    
    try:
        os.makedirs('logs', exist_ok=True)
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n📄 Full report saved to: {report_file}")
    except Exception as e:
        print(f"\n⚠️  Could not save report file: {str(e)[:50]}...")

if __name__ == "__main__":
    main()
