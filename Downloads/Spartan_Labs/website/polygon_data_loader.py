#!/usr/bin/env python3
"""
Polygon.io Data Loader - Professional-grade market data
Uses paid Polygon.io API for reliable, unblocked access
"""

import time
import psycopg2
from datetime import datetime, timedelta
import requests

# Configuration
POLYGON_API_KEY = "08bqd7Ew8fw1b7QcixwkTea1UvJHdRkD"
BASE_URL = "https://api.polygon.io"

# Database connection
conn = psycopg2.connect(
    "postgresql://spartan_user:spartan_pass_2025@postgres:5432/spartan_research"
)
conn.autocommit = False
cur = conn.cursor()

print("=" * 70)
print("POLYGON.IO DATA LOADER - Professional Market Data")
print("=" * 70)
print()

# Symbols mapped to Polygon.io format
symbols_to_fetch = [
    ('SPY', 'S&P 500', 'indices'),  # SPY ETF as proxy for S&P 500
    ('QQQ', 'NASDAQ', 'indices'),   # QQQ ETF as proxy for NASDAQ
    ('DIA', 'Dow Jones', 'indices'), # DIA ETF as proxy for Dow
    ('GLD', 'Gold', 'commodities'),  # GLD ETF as proxy for Gold
    ('SLV', 'Silver', 'commodities'), # SLV ETF as proxy for Silver
    ('BTC', 'Bitcoin', 'crypto_prices', True),  # Crypto ticker
]

successful = 0
failed = 0

# Get yesterday's date (Polygon returns previous trading day data)
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

print(f"[1/2] Fetching data for {yesterday} (latest available)...")
print()

for item in symbols_to_fetch:
    if len(item) == 4:
        symbol, name, table, is_crypto = item
    else:
        symbol, name, table = item
        is_crypto = False

    print(f"  {name} ({symbol})...", end=' ', flush=True)

    try:
        # Different endpoints for stocks vs crypto
        if is_crypto:
            # Crypto endpoint
            url = f"{BASE_URL}/v1/open-close/crypto/{symbol}/USD/{yesterday}"
        else:
            # Stocks/ETFs endpoint
            url = f"{BASE_URL}/v1/open-close/{symbol}/{yesterday}"

        response = requests.get(url, params={
            'apiKey': POLYGON_API_KEY,
            'adjusted': 'true'
        }, timeout=30)

        if response.status_code == 200:
            data = response.json()

            # Extract data
            if is_crypto:
                price = data.get('close', 0)
                open_price = data.get('open', 0)
                high_price = data.get('high', 0)
                low_price = data.get('low', 0)
                volume = int(data.get('volume', 0))
            else:
                price = data.get('close', 0)
                open_price = data.get('open', 0)
                high_price = data.get('high', 0)
                low_price = data.get('low', 0)
                volume = int(data.get('volume', 0))

            if price > 0:
                # Insert into database
                cur.execute(f"""
                    INSERT INTO market_data.{table}
                    (timestamp, symbol, name, price, open_price, high_price, low_price, volume, source)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol, timestamp) DO UPDATE SET
                        price = EXCLUDED.price,
                        open_price = EXCLUDED.open_price,
                        high_price = EXCLUDED.high_price,
                        low_price = EXCLUDED.low_price,
                        volume = EXCLUDED.volume
                """, (
                    datetime.now(),
                    symbol,
                    name,
                    float(price),
                    float(open_price),
                    float(high_price),
                    float(low_price),
                    volume,
                    'polygon.io'
                ))

                conn.commit()
                print(f"✓ ${price:.2f}")
                successful += 1
            else:
                print("❌ No price data")
                failed += 1
                conn.rollback()

        elif response.status_code == 429:
            print("❌ Rate limit - waiting 60s...")
            failed += 1
            conn.rollback()
            time.sleep(60)

        elif response.status_code == 403:
            print(f"❌ API key invalid or expired")
            failed += 1
            conn.rollback()

        else:
            print(f"❌ API error: {response.status_code}")
            failed += 1
            conn.rollback()

        # Rate limiting: Wait 1 second between requests (well under 5 req/min limit)
        time.sleep(1)

    except Exception as e:
        print(f"❌ {str(e)[:40]}")
        failed += 1
        conn.rollback()
        time.sleep(2)

print()
print(f"[2/2] Download complete: {successful} successful, {failed} failed")
print()

if successful > 0:
    # Mark preload as complete in Redis
    try:
        import redis
        r = redis.Redis(host='redis', port=6379, decode_responses=True)
        r.set('preload:complete', 'true')
        print("✓ Marked preload complete in Redis")
    except Exception as e:
        print(f"  Warning: Could not update Redis: {e}")

cur.close()
conn.close()

print()
print("=" * 70)
if successful > 0:
    print(f"SUCCESS - {successful}/{len(symbols_to_fetch)} symbols loaded")
    print("Real market data is now available on the dashboard!")
else:
    print("FAILED - No data could be loaded")
    print("Check Polygon.io API key and account status")
print("=" * 70)
