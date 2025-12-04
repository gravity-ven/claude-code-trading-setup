#!/usr/bin/env python3
"""Quick API test script"""
import os
import asyncio
import aiohttp
from dotenv import load_dotenv

load_dotenv()

async def test_apis():
    """Test each API source"""

    # Get API keys
    polygon_key = os.getenv('POLYGON_IO_API_KEY')
    twelve_data_key = os.getenv('TWELVE_DATA_API_KEY')
    alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    finnhub_key = os.getenv('FINNHUB_API_KEY')

    print("=" * 70)
    print("API KEY CHECK")
    print("=" * 70)
    print(f"Polygon: {'✅' if polygon_key and len(polygon_key) > 20 else '❌'} ({len(polygon_key) if polygon_key else 0} chars)")
    print(f"Twelve Data: {'✅' if twelve_data_key and len(twelve_data_key) > 20 else '❌'} ({len(twelve_data_key) if twelve_data_key else 0} chars)")
    print(f"Alpha Vantage: {'✅' if alpha_vantage_key and len(alpha_vantage_key) > 10 else '❌'} ({len(alpha_vantage_key) if alpha_vantage_key else 0} chars)")
    print(f"Finnhub: {'✅' if finnhub_key and len(finnhub_key) > 10 else '❌'} ({len(finnhub_key) if finnhub_key else 0} chars)")
    print()

    async with aiohttp.ClientSession() as session:
        # Test CoinGecko (no key needed)
        print("Testing CoinGecko (Bitcoin)...")
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {'ids': 'bitcoin', 'vs_currencies': 'usd', 'include_24hr_change': 'true'}
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"  ✅ CoinGecko: BTC = ${data['bitcoin']['usd']:,.2f}")
                else:
                    print(f"  ❌ CoinGecko: HTTP {response.status}")
        except Exception as e:
            print(f"  ❌ CoinGecko error: {e}")

        # Test Polygon
        if polygon_key:
            print("\nTesting Polygon.io (SPY)...")
            try:
                url = f"https://api.polygon.io/v2/aggs/ticker/SPY/prev"
                params = {'apiKey': polygon_key}
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('results'):
                            result = data['results'][0]
                            print(f"  ✅ Polygon: SPY = ${result['c']:.2f}")
                        else:
                            print(f"  ⚠️  Polygon: No results in response")
                    else:
                        text = await response.text()
                        print(f"  ❌ Polygon: HTTP {response.status}")
                        print(f"     Response: {text[:200]}")
            except Exception as e:
                print(f"  ❌ Polygon error: {e}")

        # Test Twelve Data
        if twelve_data_key:
            print("\nTesting Twelve Data (SPY)...")
            try:
                url = "https://api.twelvedata.com/quote"
                params = {'symbol': 'SPY', 'apikey': twelve_data_key}
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'close' in data:
                            print(f"  ✅ Twelve Data: SPY = ${float(data['close']):.2f}")
                        else:
                            print(f"  ⚠️  Twelve Data: {data}")
                    else:
                        text = await response.text()
                        print(f"  ❌ Twelve Data: HTTP {response.status}")
                        print(f"     Response: {text[:200]}")
            except Exception as e:
                print(f"  ❌ Twelve Data error: {e}")

        # Test Alpha Vantage
        if alpha_vantage_key:
            print("\nTesting Alpha Vantage (SPY)...")
            try:
                url = "https://www.alphavantage.co/query"
                params = {
                    'function': 'GLOBAL_QUOTE',
                    'symbol': 'SPY',
                    'apikey': alpha_vantage_key
                }
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'Global Quote' in data and '05. price' in data['Global Quote']:
                            print(f"  ✅ Alpha Vantage: SPY = ${float(data['Global Quote']['05. price']):.2f}")
                        else:
                            print(f"  ⚠️  Alpha Vantage: {data}")
                    else:
                        text = await response.text()
                        print(f"  ❌ Alpha Vantage: HTTP {response.status}")
                        print(f"     Response: {text[:200]}")
            except Exception as e:
                print(f"  ❌ Alpha Vantage error: {e}")

if __name__ == '__main__':
    asyncio.run(test_apis())
