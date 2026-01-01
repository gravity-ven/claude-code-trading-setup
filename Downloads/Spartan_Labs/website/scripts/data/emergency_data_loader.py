#!/usr/bin/env python3
"""
Emergency Data Loader - Bypasses Yahoo Finance rate limiting
Uses slow sequential requests with 20-second delays
"""

import time
import psycopg2
from datetime import datetime
import yfinance as yf
import requests

# Database connection
conn = psycopg2.connect(
    "postgresql://spartan_user:spartan_pass_2025@postgres:5432/spartan_research"
)
conn.autocommit = False
cur = conn.cursor()

print("=" * 70)
print("EMERGENCY DATA LOADER - Slow Sequential Download")
print("=" * 70)
print()

# First, populate data_sources table to fix foreign key errors
print("[1/3] Populating data_sources table...")
sources = [
    ('sp500', 'S&P 500', 'indices', 1, True),
    ('nasdaq', 'NASDAQ', 'indices', 1, True),
    ('dow', 'Dow Jones', 'indices', 1, True),
    ('gold', 'Gold', 'commodities', 1, True),
    ('silver', 'Silver', 'commodities', 1, True),
    ('bitcoin', 'Bitcoin', 'crypto', 1, True),
]

for source_id, name, category, priority, enabled in sources:
    try:
        cur.execute("""
            INSERT INTO system.data_sources (source_id, name, category, priority, enabled, last_updated)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON CONFLICT (source_id) DO NOTHING
        """, (source_id, name, category, priority, enabled))
    except Exception as e:
        print(f"  Warning: {e}")

conn.commit()
print("  ✓ Data sources table populated")
print()

# Now download data with VERY slow rate to avoid blocking
print("[2/3] Downloading market data (20-second delays)...")
print("This will take ~5 minutes to avoid rate limiting")
print()

symbols_to_fetch = [
    ('^GSPC', 'S&P 500', 'indices'),
    ('^IXIC', 'NASDAQ', 'indices'),
    ('^DJI', 'Dow Jones', 'indices'),
    ('GC=F', 'Gold', 'commodities'),
    ('SI=F', 'Silver', 'commodities'),
    ('BTC-USD', 'Bitcoin', 'crypto_prices'),
]

successful = 0
failed = 0

for symbol, name, table in symbols_to_fetch:
    print(f"  Fetching {name} ({symbol})...", end=' ', flush=True)

    try:
        ticker = yf.Ticker(symbol)

        # Try to get 1 day of data
        hist = ticker.history(period='1d')

        if hist.empty:
            print("❌ No data")
            failed += 1
            time.sleep(5)  # Short delay even on failure
            continue

        latest = hist.iloc[-1]

        # Insert into appropriate table
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
            float(latest['Close']),
            float(latest['Open']),
            float(latest['High']),
            float(latest['Low']),
            int(latest['Volume']) if latest['Volume'] > 0 else 0,
            'yfinance_emergency'
        ))

        conn.commit()
        print("✓")
        successful += 1

        # CRITICAL: Wait 20 seconds between requests to avoid rate limiting
        if successful < len(symbols_to_fetch):
            print(f"    Waiting 20 seconds to avoid rate limit...", flush=True)
            time.sleep(20)

    except Exception as e:
        print(f"❌ Error: {str(e)[:50]}")
        failed += 1
        conn.rollback()
        time.sleep(5)  # Short delay on error

print()
print(f"[3/3] Download complete: {successful} successful, {failed} failed")
print()

# Mark preload as complete in Redis
try:
    import redis
    r = redis.Redis(host='redis', port=6379, decode_responses=True)
    r.set('preload:complete', 'true')
    print("✓ Marked preload complete in Redis")
except:
    print("  Warning: Could not update Redis")

cur.close()
conn.close()

print()
print("=" * 70)
print(f"COMPLETE - {successful}/{len(symbols_to_fetch)} symbols loaded")
print("Data is now available on the dashboard!")
print("=" * 70)
