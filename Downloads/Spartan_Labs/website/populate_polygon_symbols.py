#!/usr/bin/env python3
"""
Populate PostgreSQL with all symbols from Polygon.io
Fetches 12,000+ symbols and stores them in polygon_symbols table
"""

import requests
import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv
import time
from datetime import datetime

load_dotenv()

POLYGON_API_KEY = os.getenv('POLYGON_IO_API_KEY', '08bqd7Ew8fw1b7QcixwkTea1UvJHdRkD')
POLYGON_BASE_URL = 'https://api.polygon.io'

def connect_db():
    """Connect to PostgreSQL"""
    return psycopg2.connect(
        dbname=os.getenv('POSTGRES_DB', 'spartan_research_db'),
        user=os.getenv('POSTGRES_USER', 'spartan'),
        password=os.getenv('POSTGRES_PASSWORD', 'spartan'),
        host='localhost',
        port=5432
    )

def fetch_all_tickers():
    """Fetch all tickers from Polygon.io with pagination"""
    all_tickers = []
    next_url = f"{POLYGON_BASE_URL}/v3/reference/tickers?active=true&limit=1000&apiKey={POLYGON_API_KEY}"

    page = 1
    while next_url:
        print(f"Fetching page {page}...")

        try:
            response = requests.get(next_url)
            response.raise_for_status()
            data = response.json()

            results = data.get('results', [])
            all_tickers.extend(results)

            print(f"  Retrieved {len(results)} symbols (Total: {len(all_tickers)})")

            # Get next page URL
            next_url = data.get('next_url')
            if next_url:
                next_url += f"&apiKey={POLYGON_API_KEY}"
                time.sleep(12)  # Rate limit: 5 requests/sec for free tier = 12s between requests

            page += 1

        except Exception as e:
            print(f"  Error fetching page {page}: {e}")
            break

    print(f"\n✅ Total symbols fetched: {len(all_tickers)}")
    return all_tickers

def insert_symbols(conn, symbols):
    """Insert symbols into PostgreSQL"""
    cursor = conn.cursor()

    # CRITICAL: Deduplicate by ticker (Polygon.io sometimes returns duplicates)
    unique_symbols = {}
    for symbol in symbols:
        ticker = symbol.get('ticker')
        if ticker:
            unique_symbols[ticker] = symbol  # Keep latest version of each ticker

    print(f"\n📊 Total symbols fetched: {len(symbols)}")
    print(f"📊 Unique symbols (after deduplication): {len(unique_symbols)}")
    if len(symbols) != len(unique_symbols):
        print(f"⚠️  Removed {len(symbols) - len(unique_symbols)} duplicate symbols")

    # Prepare data for insertion
    values = []
    for symbol in unique_symbols.values():
        values.append((
            symbol.get('ticker'),
            symbol.get('name'),
            symbol.get('market'),
            symbol.get('locale'),
            symbol.get('primary_exchange'),
            symbol.get('type'),
            symbol.get('active', True),
            symbol.get('currency_symbol'),
            symbol.get('currency_name'),
            symbol.get('base_currency_symbol'),
            symbol.get('base_currency_name'),
            symbol.get('cik'),
            symbol.get('composite_figi'),
            symbol.get('share_class_figi'),
            symbol.get('last_updated_utc'),
            symbol.get('delisted_utc'),
            datetime.now()
        ))

    # Insert using execute_values for performance
    insert_query = """
        INSERT INTO polygon_symbols (
            ticker, name, market, locale, primary_exchange, type, active,
            currency_symbol, currency_name, base_currency_symbol, base_currency_name,
            cik, composite_figi, share_class_figi, last_updated_utc, delisted_utc, synced_at
        ) VALUES %s
        ON CONFLICT (ticker) DO UPDATE SET
            name = EXCLUDED.name,
            market = EXCLUDED.market,
            locale = EXCLUDED.locale,
            primary_exchange = EXCLUDED.primary_exchange,
            type = EXCLUDED.type,
            active = EXCLUDED.active,
            synced_at = EXCLUDED.synced_at
    """

    print(f"\n💾 Inserting {len(values)} unique symbols into PostgreSQL...")
    execute_values(cursor, insert_query, values)
    conn.commit()
    print(f"✅ Successfully inserted/updated {len(values)} symbols")

def main():
    """Main function"""
    print("=" * 70)
    print("POLYGON.IO SYMBOL POPULATION SCRIPT")
    print("=" * 70)
    print()

    # Fetch all symbols
    print("Step 1: Fetching all symbols from Polygon.io...")
    symbols = fetch_all_tickers()

    if not symbols:
        print("❌ No symbols fetched. Exiting.")
        return

    # Connect to database
    print("\nStep 2: Connecting to PostgreSQL...")
    conn = connect_db()
    print("✅ Connected to database")

    # Insert symbols
    print("\nStep 3: Inserting symbols...")
    insert_symbols(conn, symbols)

    # Show statistics
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM polygon_symbols WHERE active = TRUE")
    total_active = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM polygon_symbols WHERE active = TRUE AND type != 'OS'")
    total_non_otc = cursor.fetchone()[0]

    cursor.execute("""
        SELECT type, COUNT(*)
        FROM polygon_symbols
        WHERE active = TRUE AND type != 'OS'
        GROUP BY type
        ORDER BY COUNT(*) DESC
        LIMIT 10
    """)
    type_breakdown = cursor.fetchall()

    conn.close()

    print()
    print("=" * 70)
    print("POPULATION COMPLETE!")
    print("=" * 70)
    print(f"Total active symbols: {total_active:,}")
    print(f"Total non-OTC symbols: {total_non_otc:,}")
    print()
    print("Top symbol types:")
    for symbol_type, count in type_breakdown:
        print(f"  {symbol_type:12s}: {count:,}")
    print()
    print("✅ W/M Scanner ready to scan all symbols!")
    print("=" * 70)

if __name__ == "__main__":
    main()
