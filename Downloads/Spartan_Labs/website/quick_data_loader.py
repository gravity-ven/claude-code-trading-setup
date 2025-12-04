#!/usr/bin/env python3
"""
Quick Data Loader - Fast bootstrap for Spartan Labs website
Uses yfinance to quickly populate Redis with essential market data
NO FAKE DATA - Real API calls only
"""

import redis
import yfinance as yf
from datetime import datetime
import json
import logging
import time
import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Connect to PostgreSQL
pg_conn = psycopg2.connect(
    dbname="spartan_research_db",
    user="spartan",
    password="spartan",
    host="localhost",
    port=5432
)
pg_cursor = pg_conn.cursor()

def load_symbol(symbol, category='index'):
    """Load real data for a symbol using yfinance"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='5d')

        if hist.empty:
            logger.warning(f"❌ {symbol}: No data")
            return False

        latest = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) > 1 else latest

        data = {
            'symbol': symbol,
            'price': float(latest['Close']),
            'change': float(latest['Close'] - prev['Close']),
            'change_pct': float((latest['Close'] - prev['Close']) / prev['Close'] * 100),
            'volume': int(latest['Volume']),
            'timestamp': datetime.now().isoformat(),
            'source': 'yfinance'
        }

        # Store in Redis (15 min TTL)
        redis_key = f'market:{category}:{symbol}'
        r.set(redis_key, json.dumps(data), ex=900)

        # Store in PostgreSQL (matching actual schema)
        pg_cursor.execute("""
            INSERT INTO preloaded_market_data (symbol, data_type, price, change_percent, volume, metadata, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (symbol, data_type, timestamp) DO NOTHING
        """, (symbol, category, data['price'], data['change_pct'], data['volume'], json.dumps(data), 'yfinance'))

        logger.info(f"✅ {symbol}: ${data['price']:.2f} ({data['change_pct']:+.2f}%)")
        return True

    except Exception as e:
        logger.error(f"❌ {symbol}: {e}")
        return False

# Essential market data
logger.info("="*70)
logger.info("🚀 Quick Data Loader - Loading essential market data...")
logger.info("="*70)

success_count = 0
total_count = 0

# US Indices (Critical)
logger.info("\n📊 US Indices:")
indices = ['SPY', 'QQQ', 'DIA', 'IWM', 'VTI']
for symbol in indices:
    total_count += 1
    if load_symbol(symbol, 'index'):
        success_count += 1
    time.sleep(0.5)  # Rate limiting

# Global Indices
logger.info("\n🌍 Global Indices:")
global_indices = ['EFA', 'EEM', 'FXI', 'EWJ', 'EWG', 'EWU']
for symbol in global_indices:
    total_count += 1
    if load_symbol(symbol, 'global'):
        success_count += 1
    time.sleep(0.5)

# Commodities
logger.info("\n🥇 Commodities:")
commodities = ['GLD', 'SLV', 'USO', 'UNG', 'DBA', 'CPER']
for symbol in commodities:
    total_count += 1
    if load_symbol(symbol, 'commodity'):
        success_count += 1
    time.sleep(0.5)

# Treasuries
logger.info("\n📈 Treasuries:")
treasuries = ['SHY', 'IEF', 'TLT', 'TIP']
for symbol in treasuries:
    total_count += 1
    if load_symbol(symbol, 'treasury'):
        success_count += 1
    time.sleep(0.5)

# Sectors
logger.info("\n🏭 Sectors:")
sectors = ['XLF', 'XLK', 'XLE', 'XLV', 'XLI', 'XLP', 'XLY', 'XLU', 'XLRE', 'XLB', 'XLC']
for symbol in sectors:
    total_count += 1
    if load_symbol(symbol, 'sector'):
        success_count += 1
    time.sleep(0.5)

# Volatility
logger.info("\n⚡ Volatility:")
volatility = ['^VIX']
for symbol in volatility:
    total_count += 1
    if load_symbol(symbol, 'volatility'):
        success_count += 1
    time.sleep(0.5)

# Crypto
logger.info("\n₿ Crypto:")
crypto = ['BTC-USD', 'ETH-USD']
for symbol in crypto:
    total_count += 1
    if load_symbol(symbol, 'crypto'):
        success_count += 1
    time.sleep(0.5)

# Forex
logger.info("\n💱 Forex:")
forex = ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X']
for symbol in forex:
    total_count += 1
    if load_symbol(symbol, 'forex'):
        success_count += 1
    time.sleep(0.5)

# Commit PostgreSQL changes
pg_conn.commit()
pg_cursor.close()
pg_conn.close()

# Summary
success_rate = (success_count / total_count * 100) if total_count > 0 else 0
logger.info("\n" + "="*70)
logger.info(f"✅ Data loading complete: {success_count}/{total_count} ({success_rate:.1f}%)")
logger.info("="*70)

# Validation threshold
if success_rate >= 80:
    logger.info("✅ SUCCESS: Data preload validation passed (≥80%)")
    exit(0)
else:
    logger.error(f"❌ FAILURE: Only {success_rate:.1f}% data loaded (need ≥80%)")
    exit(1)
