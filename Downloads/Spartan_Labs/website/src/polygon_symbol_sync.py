#!/usr/bin/env python3
"""
Polygon.io Symbol Synchronization System
Fetches ALL symbols from Polygon.io (paid tier) and stores in PostgreSQL
Supports: Stocks, Options, Crypto, Forex
"""

import os
import sys
import asyncio
import aiohttp
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Polygon.io API configuration
POLYGON_API_KEY = os.getenv('POLYGON_IO_API_KEY')
POLYGON_BASE_URL = 'https://api.polygon.io'

# Database configuration (native mode uses localhost)
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/spartan_research_db')
# Fix Docker hostname for native mode
if 'spartan-postgres' in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace('spartan-postgres', 'localhost')


class PolygonSymbolSync:
    """Synchronize all symbols from Polygon.io to PostgreSQL"""

    def __init__(self):
        self.api_key = POLYGON_API_KEY
        self.base_url = POLYGON_BASE_URL
        self.db_conn = None
        self.session = None

        # Rate limiting (paid tier: higher limits)
        self.request_delay = 0.1  # 10 requests/second for paid tier
        self.last_request_time = 0

    async def connect_db(self):
        """Connect to PostgreSQL database"""
        try:
            self.db_conn = psycopg2.connect(DATABASE_URL)
            logger.info("✅ Connected to PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

    def create_tables(self):
        """Create PostgreSQL tables for symbols"""
        try:
            cursor = self.db_conn.cursor()

            # Create symbols table with comprehensive fields
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS polygon_symbols (
                    ticker VARCHAR(50) PRIMARY KEY,
                    name VARCHAR(500),
                    market VARCHAR(50),
                    locale VARCHAR(10),
                    primary_exchange VARCHAR(50),
                    type VARCHAR(50),
                    active BOOLEAN,
                    currency_symbol VARCHAR(10),
                    currency_name VARCHAR(50),
                    base_currency_symbol VARCHAR(10),
                    base_currency_name VARCHAR(50),
                    cik VARCHAR(20),
                    composite_figi VARCHAR(50),
                    share_class_figi VARCHAR(50),
                    last_updated_utc TIMESTAMP,
                    delisted_utc TIMESTAMP,
                    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB
                );

                -- Create indexes for fast lookups
                CREATE INDEX IF NOT EXISTS idx_polygon_ticker ON polygon_symbols(ticker);
                CREATE INDEX IF NOT EXISTS idx_polygon_market ON polygon_symbols(market);
                CREATE INDEX IF NOT EXISTS idx_polygon_type ON polygon_symbols(type);
                CREATE INDEX IF NOT EXISTS idx_polygon_active ON polygon_symbols(active);
                CREATE INDEX IF NOT EXISTS idx_polygon_exchange ON polygon_symbols(primary_exchange);

                -- Create sync status table
                CREATE TABLE IF NOT EXISTS polygon_sync_status (
                    id SERIAL PRIMARY KEY,
                    sync_type VARCHAR(50),
                    total_symbols INTEGER,
                    new_symbols INTEGER,
                    updated_symbols INTEGER,
                    errors INTEGER,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    status VARCHAR(50),
                    error_message TEXT
                );

                -- Create index for sync status
                CREATE INDEX IF NOT EXISTS idx_sync_status_date ON polygon_sync_status(completed_at DESC);
            """)

            self.db_conn.commit()
            logger.info("✅ Database tables created/verified")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to create tables: {e}")
            self.db_conn.rollback()
            return False

    async def rate_limit(self):
        """Apply rate limiting to API requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.request_delay:
            await asyncio.sleep(self.request_delay - time_since_last)

        self.last_request_time = time.time()

    async def fetch_tickers(self, market: str = 'stocks', asset_class: Optional[str] = None) -> List[Dict]:
        """Fetch all tickers from Polygon.io for a specific market"""
        all_tickers = []
        next_url = None

        async with aiohttp.ClientSession() as session:
            self.session = session

            # Build initial URL
            params = {
                'apiKey': self.api_key,
                'limit': 1000,  # Max per request
                'active': 'true',
            }

            if asset_class:
                params['type'] = asset_class

            url = f"{self.base_url}/v3/reference/tickers"

            page = 1
            while True:
                try:
                    await self.rate_limit()

                    logger.info(f"📥 Fetching {market} page {page}...")

                    async with session.get(url, params=params if not next_url else None) as response:
                        if response.status == 200:
                            data = await response.json()

                            results = data.get('results', [])
                            all_tickers.extend(results)

                            logger.info(f"   ✓ Fetched {len(results)} symbols (total: {len(all_tickers)})")

                            # Check for next page
                            next_url = data.get('next_url')
                            if next_url:
                                # Polygon includes full URL with API key
                                url = next_url
                                params = None  # Use URL directly
                                page += 1
                            else:
                                break
                        elif response.status == 429:
                            # Rate limit hit - wait and retry
                            logger.warning("⚠️  Rate limit hit, waiting 60 seconds...")
                            await asyncio.sleep(60)
                        else:
                            logger.error(f"❌ API error: {response.status}")
                            break

                except Exception as e:
                    logger.error(f"❌ Error fetching page {page}: {e}")
                    break

        logger.info(f"✅ Total {market} symbols fetched: {len(all_tickers)}")
        return all_tickers

    def save_symbols(self, symbols: List[Dict], sync_id: int) -> Dict[str, int]:
        """Save symbols to PostgreSQL database"""
        stats = {
            'new': 0,
            'updated': 0,
            'errors': 0
        }

        cursor = self.db_conn.cursor()

        for symbol in symbols:
            try:
                # Extract fields from Polygon.io response
                ticker = symbol.get('ticker')
                name = symbol.get('name')
                market = symbol.get('market', '')
                locale = symbol.get('locale', '')
                primary_exchange = symbol.get('primary_exchange', '')
                symbol_type = symbol.get('type', '')
                active = symbol.get('active', True)
                currency_symbol = symbol.get('currency_symbol', '')
                currency_name = symbol.get('currency_name', '')
                base_currency_symbol = symbol.get('base_currency_symbol', '')
                base_currency_name = symbol.get('base_currency_name', '')
                cik = symbol.get('cik', '')
                composite_figi = symbol.get('composite_figi', '')
                share_class_figi = symbol.get('share_class_figi', '')
                last_updated_utc = symbol.get('last_updated_utc')
                delisted_utc = symbol.get('delisted_utc')

                # Store full metadata as JSONB for flexibility
                import json
                metadata = json.dumps(symbol)

                # Upsert (insert or update)
                cursor.execute("""
                    INSERT INTO polygon_symbols (
                        ticker, name, market, locale, primary_exchange, type, active,
                        currency_symbol, currency_name, base_currency_symbol, base_currency_name,
                        cik, composite_figi, share_class_figi, last_updated_utc, delisted_utc,
                        synced_at, metadata
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s::jsonb
                    )
                    ON CONFLICT (ticker) DO UPDATE SET
                        name = EXCLUDED.name,
                        market = EXCLUDED.market,
                        locale = EXCLUDED.locale,
                        primary_exchange = EXCLUDED.primary_exchange,
                        type = EXCLUDED.type,
                        active = EXCLUDED.active,
                        currency_symbol = EXCLUDED.currency_symbol,
                        currency_name = EXCLUDED.currency_name,
                        base_currency_symbol = EXCLUDED.base_currency_symbol,
                        base_currency_name = EXCLUDED.base_currency_name,
                        cik = EXCLUDED.cik,
                        composite_figi = EXCLUDED.composite_figi,
                        share_class_figi = EXCLUDED.share_class_figi,
                        last_updated_utc = EXCLUDED.last_updated_utc,
                        delisted_utc = EXCLUDED.delisted_utc,
                        synced_at = CURRENT_TIMESTAMP,
                        metadata = EXCLUDED.metadata
                    RETURNING (xmax = 0) AS inserted
                """, (
                    ticker, name, market, locale, primary_exchange, symbol_type, active,
                    currency_symbol, currency_name, base_currency_symbol, base_currency_name,
                    cik, composite_figi, share_class_figi, last_updated_utc, delisted_utc,
                    metadata
                ))

                result = cursor.fetchone()
                if result and result[0]:
                    stats['new'] += 1
                else:
                    stats['updated'] += 1

            except Exception as e:
                logger.error(f"❌ Error saving symbol {symbol.get('ticker', 'UNKNOWN')}: {e}")
                stats['errors'] += 1

        self.db_conn.commit()
        return stats

    async def sync_all_markets(self):
        """Synchronize symbols from all Polygon.io markets"""

        if not self.api_key:
            logger.error("❌ POLYGON_IO_API_KEY not set in environment variables")
            return

        logger.info("=" * 70)
        logger.info("🚀 POLYGON.IO SYMBOL SYNCHRONIZATION")
        logger.info("=" * 70)

        # Connect to database
        if not await self.connect_db():
            return

        # Create tables
        if not self.create_tables():
            return

        # Record sync start
        cursor = self.db_conn.cursor()
        cursor.execute("""
            INSERT INTO polygon_sync_status (sync_type, started_at, status)
            VALUES (%s, CURRENT_TIMESTAMP, %s)
            RETURNING id
        """, ('full_sync', 'running'))
        sync_id = cursor.fetchone()[0]
        self.db_conn.commit()

        total_stats = {
            'new': 0,
            'updated': 0,
            'errors': 0,
            'total': 0
        }

        # Sync different markets
        markets = [
            ('stocks', 'Stocks (US & Global)'),
            ('options', 'Options'),
            ('crypto', 'Cryptocurrency'),
            ('fx', 'Forex'),
            ('otc', 'OTC Markets'),
            ('indices', 'Indices'),
        ]

        for market_code, market_name in markets:
            logger.info("")
            logger.info(f"📊 Syncing {market_name}...")
            logger.info("-" * 70)

            try:
                # Fetch symbols for this market
                symbols = await self.fetch_tickers(market=market_code)

                if symbols:
                    # Save to database
                    stats = self.save_symbols(symbols, sync_id)

                    # Update totals
                    total_stats['new'] += stats['new']
                    total_stats['updated'] += stats['updated']
                    total_stats['errors'] += stats['errors']
                    total_stats['total'] += len(symbols)

                    logger.info(f"✅ {market_name}: {stats['new']} new, {stats['updated']} updated")
                else:
                    logger.warning(f"⚠️  No symbols found for {market_name}")

            except Exception as e:
                logger.error(f"❌ Failed to sync {market_name}: {e}")
                total_stats['errors'] += 1

        # Update sync status
        cursor.execute("""
            UPDATE polygon_sync_status
            SET total_symbols = %s,
                new_symbols = %s,
                updated_symbols = %s,
                errors = %s,
                completed_at = CURRENT_TIMESTAMP,
                status = %s
            WHERE id = %s
        """, (
            total_stats['total'],
            total_stats['new'],
            total_stats['updated'],
            total_stats['errors'],
            'completed' if total_stats['errors'] == 0 else 'completed_with_errors',
            sync_id
        ))
        self.db_conn.commit()

        # Print summary
        logger.info("")
        logger.info("=" * 70)
        logger.info("📊 SYNCHRONIZATION COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Total Symbols:   {total_stats['total']:,}")
        logger.info(f"New Symbols:     {total_stats['new']:,}")
        logger.info(f"Updated Symbols: {total_stats['updated']:,}")
        logger.info(f"Errors:          {total_stats['errors']:,}")
        logger.info("=" * 70)

        # Close database connection
        if self.db_conn:
            self.db_conn.close()


async def main():
    """Main entry point"""
    syncer = PolygonSymbolSync()
    await syncer.sync_all_markets()


if __name__ == "__main__":
    asyncio.run(main())
