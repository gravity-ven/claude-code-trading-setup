#!/usr/bin/env python3
"""
DATA GUARDIAN AGENT - FULL DATABASE SCAN
Scans all 12,000+ symbols from symbols_database.json
Uses parallel fetching for maximum speed
"""

import os
import sys
import json
import asyncio
import aiohttp
import redis
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
from collections import defaultdict
from pathlib import Path
from dotenv import load_dotenv
import logging
import signal
import time
from typing import Dict, List, Optional

# Load environment variables
load_dotenv()

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Data source configuration
DATA_SOURCES = {
    'yfinance': {'priority': 1, 'enabled': True},
    'polygon': {'priority': 2, 'enabled': bool(os.getenv('POLYGON_IO_API_KEY'))},
    'marketaux': {'priority': 3, 'enabled': bool(os.getenv('MARKETAUX_API_KEY'))},
    'twelve_data': {'priority': 4, 'enabled': bool(os.getenv('TWELVE_DATA_API_KEY'))},
    'finnhub': {'priority': 5, 'enabled': bool(os.getenv('FINNHUB_API_KEY'))},
    'coingecko': {'priority': 6, 'enabled': True},
}

# Scanning configuration
BATCH_SIZE = 100  # Fetch 100 symbols concurrently
SCAN_INTERVAL = 900  # 15 minutes
MAX_CONCURRENT_REQUESTS = 50  # Limit concurrent requests

class FullDatabaseScanner:
    """Enhanced Data Guardian that scans all symbols from database"""

    def __init__(self):
        self.redis_client = None
        self.db_conn = None
        self.session = None
        self.all_symbols = []
        self.scan_count = 0
        self.stats = {
            'total_scanned': 0,
            'successful': 0,
            'failed': 0,
            'scan_start': None,
            'scan_end': None
        }
        self.source_stats = defaultdict(lambda: {'success': 0, 'fail': 0})
        self.running = True

    async def initialize(self):
        """Initialize connections and load symbols"""
        try:
            # Connect to Redis
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("✅ Connected to Redis")

            # Connect to PostgreSQL
            self.db_conn = psycopg2.connect(
                dbname=os.getenv('POSTGRES_DB', 'spartan_research_db'),
                user=os.getenv('POSTGRES_USER', 'spartan'),
                password=os.getenv('POSTGRES_PASSWORD', 'spartan'),
                host='localhost',
                port=5432
            )
            logger.info("✅ Connected to PostgreSQL")

            # Create HTTP session for async requests
            self.session = aiohttp.ClientSession()
            logger.info("✅ Created HTTP session")

            # Load all symbols from database
            await self.load_symbols()

            logger.info(f"🎯 Initialization complete - Ready to scan {len(self.all_symbols)} symbols")
            return True

        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False

    async def load_symbols(self):
        """Load all symbols from symbols_database.json"""
        try:
            # PRIORITY SYMBOLS - Critical for website agents (scanned FIRST)
            PRIORITY_SYMBOLS = [
                {'symbol': 'SPY', 'name': 'SPDR S&P 500 ETF', 'type': 'ETF'},
                {'symbol': 'UUP', 'name': 'Dollar Index ETF', 'type': 'ETF'},
                {'symbol': 'GLD', 'name': 'Gold ETF', 'type': 'ETF'},
                {'symbol': 'USO', 'name': 'Oil ETF', 'type': 'ETF'},
                {'symbol': 'BTC-USD', 'name': 'Bitcoin', 'type': 'Cryptocurrency'},
                {'symbol': 'ETH-USD', 'name': 'Ethereum', 'type': 'Cryptocurrency'},
                {'symbol': 'SOL-USD', 'name': 'Solana', 'type': 'Cryptocurrency'},
                {'symbol': 'AUDJPY=X', 'name': 'AUD/JPY Forex', 'type': 'Currency'},
                {'symbol': 'HYG', 'name': 'High Yield Bond ETF', 'type': 'ETF'},
                {'symbol': 'QQQ', 'name': 'NASDAQ 100 ETF', 'type': 'ETF'},
                {'symbol': 'DIA', 'name': 'Dow Jones ETF', 'type': 'ETF'},
                {'symbol': 'IWM', 'name': 'Russell 2000 ETF', 'type': 'ETF'},
            ]

            db_path = Path(__file__).parent / 'symbols_database.json'

            if not db_path.exists():
                logger.error(f"❌ symbols_database.json not found at {db_path}")
                # Use priority symbols only if database not found
                self.all_symbols = PRIORITY_SYMBOLS
                logger.info(f"⚠️  Using {len(self.all_symbols)} priority symbols only")
                return

            with open(db_path, 'r') as f:
                data = json.load(f)

            # Extract all symbols from the database
            if 'symbols' in data:
                all_loaded_symbols = [
                    {
                        'symbol': item['symbol'],
                        'name': item.get('name', ''),
                        'type': item.get('type', 'Stock'),
                        'exchange': item.get('exchange', ''),
                        'country': item.get('country', 'USA')
                    }
                    for item in data['symbols']
                ]

                # PRIORITIZE: Put priority symbols FIRST, then rest
                priority_symbol_list = [s['symbol'] for s in PRIORITY_SYMBOLS]
                other_symbols = [s for s in all_loaded_symbols if s['symbol'] not in priority_symbol_list]

                self.all_symbols = PRIORITY_SYMBOLS + other_symbols

                logger.info(f"📊 Loaded {len(self.all_symbols)} symbols from database")
                logger.info(f"🎯 Priority symbols ({len(PRIORITY_SYMBOLS)}) will be scanned FIRST")

            else:
                logger.error("❌ Invalid database structure - 'symbols' key not found")
                self.all_symbols = PRIORITY_SYMBOLS
                logger.info(f"⚠️  Using {len(self.all_symbols)} priority symbols only")
                return

            # Log symbol breakdown by type
            types = defaultdict(int)
            for sym in self.all_symbols:
                types[sym['type']] += 1

            logger.info("📈 Symbol breakdown:")
            for sym_type, count in sorted(types.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"   {sym_type}: {count}")

        except Exception as e:
            logger.error(f"❌ Failed to load symbols: {e}")
            self.all_symbols = []

    async def fetch_polygon(self, symbol: str) -> Optional[Dict]:
        """Fetch from Polygon.io"""
        api_key = os.getenv('POLYGON_IO_API_KEY')
        if not api_key:
            return None

        try:
            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev?apiKey={api_key}"
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'results' in data and len(data['results']) > 0:
                        result = data['results'][0]
                        return {
                            'symbol': symbol,
                            'price': result['c'],  # close price
                            'volume': result['v'],
                            'high': result['h'],
                            'low': result['l'],
                            'timestamp': datetime.fromtimestamp(result['t'] / 1000).isoformat(),
                            'source': 'polygon'
                        }
        except Exception as e:
            logger.debug(f"Polygon error for {symbol}: {e}")

        return None

    async def fetch_symbol_data(self, symbol_info: Dict) -> Optional[Dict]:
        """Fetch data for a single symbol from best available source"""
        symbol = symbol_info['symbol']

        # Try Polygon.io first (most reliable for US stocks)
        if DATA_SOURCES['polygon']['enabled']:
            data = await self.fetch_polygon(symbol)
            if data:
                self.source_stats['polygon']['success'] += 1
                return data
            self.source_stats['polygon']['fail'] += 1

        # Add other sources here if needed

        return None

    async def store_batch(self, batch_data: List[Dict]):
        """Store batch of symbol data efficiently"""
        if not batch_data:
            return

        try:
            # Store in Redis
            pipe = self.redis_client.pipeline()
            for data in batch_data:
                redis_key = f"market:symbol:{data['symbol']}"
                pipe.setex(redis_key, 900, json.dumps(data))  # 15-min TTL
            pipe.execute()

            # Store in PostgreSQL (batch insert)
            with self.db_conn.cursor() as cur:
                insert_data = [
                    (
                        item['symbol'],
                        'realtime',
                        item.get('price'),
                        item.get('change_24h', 0.0),
                        item.get('volume', 0),
                        json.dumps(item),
                        datetime.now(),
                        item['source']
                    )
                    for item in batch_data
                ]

                execute_values(
                    cur,
                    """
                    INSERT INTO preloaded_market_data
                    (symbol, data_type, price, change_percent, volume, metadata, timestamp, source)
                    VALUES %s
                    ON CONFLICT (symbol, data_type, timestamp) DO UPDATE
                    SET price = EXCLUDED.price,
                        change_percent = EXCLUDED.change_percent,
                        volume = EXCLUDED.volume,
                        metadata = EXCLUDED.metadata,
                        source = EXCLUDED.source
                    """,
                    insert_data
                )
                self.db_conn.commit()

            logger.debug(f"💾 Stored batch of {len(batch_data)} symbols")

        except Exception as e:
            logger.error(f"❌ Failed to store batch: {e}")

    async def scan_batch(self, symbols_batch: List[Dict]) -> int:
        """Scan a batch of symbols concurrently"""
        tasks = [self.fetch_symbol_data(sym_info) for sym_info in symbols_batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful results
        successful_data = [
            r for r in results
            if r and isinstance(r, dict) and not isinstance(r, Exception)
        ]

        # Store successful results
        if successful_data:
            await self.store_batch(successful_data)

        return len(successful_data)

    async def full_scan(self):
        """Perform full scan of all symbols"""
        self.scan_count += 1
        self.stats['scan_start'] = time.time()
        self.stats['total_scanned'] = 0
        self.stats['successful'] = 0
        self.stats['failed'] = 0

        logger.info("=" * 70)
        logger.info(f"🔍 FULL DATABASE SCAN #{self.scan_count} STARTING")
        logger.info(f"📊 Total symbols to scan: {len(self.all_symbols)}")
        logger.info("=" * 70)

        # Split symbols into batches
        total_batches = (len(self.all_symbols) + BATCH_SIZE - 1) // BATCH_SIZE

        for i in range(0, len(self.all_symbols), BATCH_SIZE):
            if not self.running:
                logger.info("🛑 Scan interrupted by shutdown signal")
                break

            batch = self.all_symbols[i:i+BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1

            logger.info(f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} symbols)")

            successful = await self.scan_batch(batch)

            self.stats['total_scanned'] += len(batch)
            self.stats['successful'] += successful
            self.stats['failed'] += len(batch) - successful

            # Progress update every 10 batches
            if batch_num % 10 == 0:
                progress = (self.stats['total_scanned'] / len(self.all_symbols)) * 100
                success_rate = (self.stats['successful'] / self.stats['total_scanned'] * 100) if self.stats['total_scanned'] > 0 else 0
                logger.info(f"📈 Progress: {progress:.1f}% | Success rate: {success_rate:.1f}%")

            # Small delay between batches to avoid overwhelming APIs
            await asyncio.sleep(0.5)

        self.stats['scan_end'] = time.time()
        duration = self.stats['scan_end'] - self.stats['scan_start']

        logger.info("=" * 70)
        logger.info(f"✅ SCAN #{self.scan_count} COMPLETE")
        logger.info(f"   Duration: {duration:.1f}s ({duration/60:.1f} minutes)")
        logger.info(f"   Scanned: {self.stats['total_scanned']} symbols")
        logger.info(f"   Successful: {self.stats['successful']} ({self.stats['successful']/self.stats['total_scanned']*100:.1f}%)")
        logger.info(f"   Failed: {self.stats['failed']}")
        logger.info(f"   Speed: {self.stats['total_scanned']/duration:.1f} symbols/second")
        logger.info("=" * 70)

        # Source statistics
        logger.info("📊 Source Statistics:")
        for source, stats in self.source_stats.items():
            total = stats['success'] + stats['fail']
            if total > 0:
                rate = stats['success'] / total * 100
                logger.info(f"   {source:15} - {stats['success']:5}/{total:5} ({rate:5.1f}%)")

    async def run_continuous(self):
        """Run continuous scanning every 15 minutes"""
        logger.info("🚀 Starting continuous scanning mode")
        logger.info(f"📅 Scan interval: {SCAN_INTERVAL}s ({SCAN_INTERVAL/60:.0f} minutes)")

        while self.running:
            try:
                await self.full_scan()

                if self.running:
                    logger.info(f"⏰ Next scan in {SCAN_INTERVAL/60:.0f} minutes")
                    logger.info("")
                    await asyncio.sleep(SCAN_INTERVAL)

            except Exception as e:
                logger.error(f"❌ Error in scan loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down Data Guardian Agent...")
        self.running = False

        if self.session:
            await self.session.close()
        if self.db_conn:
            self.db_conn.close()

        logger.info("✅ Shutdown complete")

async def main():
    """Main entry point"""
    scanner = FullDatabaseScanner()

    # Handle shutdown signals
    def signal_handler(sig, frame):
        logger.info(f"📡 Received signal {sig}")
        asyncio.create_task(scanner.shutdown())

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Initialize
    if not await scanner.initialize():
        logger.error("❌ Initialization failed - exiting")
        return 1

    # Run continuous scanning
    try:
        await scanner.run_continuous()
    except KeyboardInterrupt:
        logger.info("🛑 Keyboard interrupt received")
    finally:
        await scanner.shutdown()

    return 0

if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
