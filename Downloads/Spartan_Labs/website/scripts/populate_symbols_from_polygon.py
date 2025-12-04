#!/usr/bin/env python3
"""
Populate market_data.symbols table with comprehensive symbol list from Polygon.io
Target: 12,000+ US-listed stocks, ETFs, and other securities
"""

import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import os
from datetime import datetime

# Polygon API configuration
POLYGON_API_KEY = os.getenv('POLYGON_IO_API_KEY', '08bqd7Ew8fw1b7QcixwkTea1UvJHdRkD')
POLYGON_BASE_URL = 'https://api.polygon.io'

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://spartan:spartan@localhost:5432/spartan_research_db')

def fetch_all_tickers(market='stocks', limit=1000, offset=0):
    """
    Fetch comprehensive ticker list from Polygon.io

    Markets: stocks, otc, fx, crypto, indices
    Limit: max 1000 per request
    """
    url = f"{POLYGON_BASE_URL}/v3/reference/tickers"

    params = {
        'market': market,
        'active': 'true',
        'limit': limit,
        'apiKey': POLYGON_API_KEY
    }

    if offset > 0:
        params['cursor'] = offset

    try:
        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 200:
            data = response.json()
            tickers = data.get('results', [])
            next_url = data.get('next_url')
            return tickers, next_url
        elif response.status_code == 429:
            print(f"⚠️  Rate limit hit. Waiting 60 seconds...")
            time.sleep(60)
            return fetch_all_tickers(market, limit, offset)
        else:
            print(f"❌ Polygon API error {response.status_code}: {response.text}")
            return [], None

    except Exception as e:
        print(f"❌ Error fetching tickers: {e}")
        return [], None

def insert_symbols_batch(conn, symbols_batch):
    """Insert symbols batch into database"""
    if not symbols_batch:
        return 0

    cursor = conn.cursor()

    insert_query = """
        INSERT INTO market_data.symbols
        (symbol, name, asset_type, exchange, country, currency)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (symbol) DO UPDATE SET
            name = EXCLUDED.name,
            asset_type = EXCLUDED.asset_type,
            exchange = EXCLUDED.exchange,
            country = EXCLUDED.country,
            currency = EXCLUDED.currency,
            updated_at = CURRENT_TIMESTAMP
    """

    inserted = 0
    for symbol_data in symbols_batch:
        try:
            cursor.execute(insert_query, (
                symbol_data['symbol'],
                symbol_data['name'],
                symbol_data['asset_type'],
                symbol_data['exchange'],
                symbol_data['country'],
                symbol_data['currency']
            ))
            inserted += 1
        except Exception as e:
            print(f"⚠️  Skipped {symbol_data['symbol']}: {e}")

    conn.commit()
    cursor.close()

    return inserted

def populate_symbols(markets=['stocks', 'otc', 'crypto', 'fx']):
    """
    Main function to populate symbols from all markets

    Expected totals:
    - stocks: ~8,000-10,000 symbols
    - otc: ~3,000-5,000 symbols
    - crypto: ~200-500 symbols
    - fx: ~100-200 symbols
    Total: 12,000+ symbols
    """
    print("\n" + "=" * 70)
    print("🚀 Populating Comprehensive Symbols Database from Polygon.io")
    print("=" * 70)

    # Connect to database
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print(f"✅ Connected to PostgreSQL database")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return

    total_inserted = 0

    for market in markets:
        print(f"\n📊 Fetching {market.upper()} symbols...")

        market_total = 0
        next_url = None
        page = 1

        while True:
            # Fetch batch
            tickers, next_url = fetch_all_tickers(market=market, limit=1000)

            if not tickers:
                break

            # Convert to database format
            symbols_batch = []
            for ticker in tickers:
                symbol_obj = {
                    'symbol': ticker.get('ticker', '').upper(),
                    'name': ticker.get('name', 'N/A')[:255],  # Limit to 255 chars
                    'asset_type': market,
                    'exchange': ticker.get('primary_exchange', 'N/A')[:100],
                    'country': ticker.get('locale', 'US').upper()[:100],
                    'currency': ticker.get('currency_name', 'USD')[:10]
                }

                # Only add if symbol has minimum required data
                if symbol_obj['symbol'] and len(symbol_obj['symbol']) <= 20:
                    symbols_batch.append(symbol_obj)

            # Insert batch
            inserted = insert_symbols_batch(conn, symbols_batch)
            market_total += inserted
            total_inserted += inserted

            print(f"   Page {page}: +{inserted} symbols (Market Total: {market_total})")

            # Check if there are more pages
            if not next_url:
                break

            page += 1
            time.sleep(0.25)  # Rate limit: ~4 requests per second

        print(f"✅ {market.upper()}: {market_total} symbols")

    # Final count
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM market_data.symbols")
    final_count = cursor.fetchone()[0]
    cursor.close()

    conn.close()

    print("\n" + "=" * 70)
    print(f"🎉 SUCCESS! Comprehensive Symbols Database Populated")
    print("=" * 70)
    print(f"   Total Symbols in Database: {final_count:,}")
    print(f"   Newly Inserted/Updated: {total_inserted:,}")
    print(f"   Data Source: Polygon.io API")
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    if final_count >= 12000:
        print(f"✅ Target achieved: {final_count:,} >= 12,000 symbols")
    else:
        print(f"⚠️  Below target: {final_count:,} < 12,000 symbols")
        print(f"   Consider adding more markets or OTC symbols")

    return final_count

if __name__ == '__main__':
    try:
        final_count = populate_symbols(markets=['stocks', 'otc', 'crypto', 'fx'])

        if final_count >= 12000:
            exit(0)
        else:
            print(f"\n⚠️  Warning: Only {final_count:,} symbols populated (target: 12,000+)")
            exit(0)  # Still exit successfully, just a warning

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
