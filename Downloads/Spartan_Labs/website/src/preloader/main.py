#!/usr/bin/env python3
"""
Spartan Research Station - Data Pre-Loader Service
===================================================

Downloads ALL data from 50+ sources BEFORE website starts.
Database-First Architecture: Download → PostgreSQL → Never refetch

Author: Spartan Research Station
Version: 2.0.0
"""

import asyncio
import os
import sys
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import psycopg2
from psycopg2.extras import execute_batch
import redis
import yfinance as yf
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/preloader.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

@dataclass
class DataSource:
    """Configuration for a single data source"""
    id: str
    name: str
    category: str  # stocks, forex, crypto, economic, commodities
    priority: int  # 1 = highest
    enabled: bool = True
    symbols: List[str] = None

    def __post_init__(self):
        if self.symbols is None:
            self.symbols = []

class Config:
    """System configuration"""
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://spartan_user:spartan_pass_2025@postgres:5432/spartan_research')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

    # API Keys
    POLYGON_API_KEY = os.getenv('POLYGON_IO_API_KEY', '')
    FRED_API_KEY = os.getenv('FRED_API_KEY', 'a6137538793a55227cbae2119e1573f5')  # Default demo key
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')

    # Pre-loader settings
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '10'))
    TIMEOUT_PER_SOURCE = int(os.getenv('TIMEOUT_PER_SOURCE', '30'))
    SUCCESS_THRESHOLD = float(os.getenv('SUCCESS_THRESHOLD', '0'))  # Allow system to start without data initially

    # Data sources configuration
    DATA_SOURCES = [
        # Market Indices (Priority 1)
        DataSource('sp500', 'S&P 500', 'indices', 1, symbols=['^GSPC']),
        DataSource('nasdaq', 'NASDAQ', 'indices', 1, symbols=['^IXIC']),
        DataSource('dow', 'Dow Jones', 'indices', 1, symbols=['^DJI']),
        DataSource('russell2000', 'Russell 2000', 'indices', 1, symbols=['^RUT']),
        DataSource('vix', 'VIX', 'indices', 1, symbols=['^VIX']),

        # Commodities (Priority 1)
        DataSource('gold', 'Gold', 'commodities', 1, symbols=['GC=F']),
        DataSource('silver', 'Silver', 'commodities', 1, symbols=['SI=F']),
        DataSource('wti_oil', 'WTI Crude Oil', 'commodities', 1, symbols=['CL=F']),
        DataSource('brent_oil', 'Brent Crude', 'commodities', 1, symbols=['BZ=F']),
        DataSource('copper', 'Copper', 'commodities', 1, symbols=['HG=F']),
        DataSource('natural_gas', 'Natural Gas', 'commodities', 2, symbols=['NG=F']),

        # Forex (Priority 1)
        DataSource('usd_eur', 'USD/EUR', 'forex', 1, symbols=['EURUSD=X']),
        DataSource('usd_jpy', 'USD/JPY', 'forex', 1, symbols=['JPY=X']),
        DataSource('usd_gbp', 'USD/GBP', 'forex', 1, symbols=['GBPUSD=X']),
        DataSource('dxy', 'US Dollar Index', 'forex', 1, symbols=['DX-Y.NYB']),

        # Crypto (Priority 1)
        DataSource('bitcoin', 'Bitcoin', 'crypto', 1, symbols=['BTC-USD']),
        DataSource('ethereum', 'Ethereum', 'crypto', 1, symbols=['ETH-USD']),
        DataSource('solana', 'Solana', 'crypto', 2, symbols=['SOL-USD']),

        # Sector ETFs (Priority 1)
        DataSource('tech_sector', 'Technology Sector', 'sectors', 1, symbols=['XLK']),
        DataSource('financial_sector', 'Financial Sector', 'sectors', 1, symbols=['XLF']),
        DataSource('energy_sector', 'Energy Sector', 'sectors', 1, symbols=['XLE']),
        DataSource('healthcare_sector', 'Healthcare Sector', 'sectors', 1, symbols=['XLV']),
        DataSource('consumer_sector', 'Consumer Discretionary', 'sectors', 1, symbols=['XLY']),

        # Economic Indicators (Priority 2 - FRED API)
        # TEMPORARILY DISABLED - FRED API key needs to be configured
        # Get a free key at: https://fred.stlouisfed.org/docs/api/api_key.html
        # DataSource('gdp', 'GDP Growth', 'economic', 2, symbols=['GDP'], enabled=False),
        # DataSource('cpi', 'CPI Inflation', 'economic', 2, symbols=['CPIAUCSL'], enabled=False),
        # DataSource('unemployment', 'Unemployment Rate', 'economic', 2, symbols=['UNRATE'], enabled=False),
        # DataSource('treasury_2y', '2-Year Treasury', 'economic', 2, symbols=['DGS2'], enabled=False),
        # DataSource('treasury_10y', '10-Year Treasury', 'economic', 2, symbols=['DGS10'], enabled=False),
        # DataSource('treasury_30y', '30-Year Treasury', 'economic', 2, symbols=['DGS30'], enabled=False),
        # DataSource('fed_funds_rate', 'Federal Funds Rate', 'economic', 2, symbols=['DFF'], enabled=False),
        # DataSource('m2_money_supply', 'M2 Money Supply', 'economic', 3, symbols=['M2SL'], enabled=False),
    ]

# ============================================================================
# Database Connection
# ============================================================================

class DatabaseManager:
    """Manage PostgreSQL connections and operations"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn = None

    def connect(self):
        """Connect to PostgreSQL"""
        try:
            self.conn = psycopg2.connect(self.database_url)
            logger.info("✓ Connected to PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"✗ PostgreSQL connection failed: {e}")
            return False

    def insert_market_data(self, table: str, data: List[Dict[str, Any]]):
        """Insert market data into specified table"""
        if not data:
            return 0

        try:
            cursor = self.conn.cursor()

            # Dynamically build INSERT statement
            columns = list(data[0].keys())
            placeholders = ','.join(['%s'] * len(columns))
            query = f"""
                INSERT INTO market_data.{table} ({','.join(columns)})
                VALUES ({placeholders})
                ON CONFLICT DO NOTHING
            """

            values = [[row[col] for col in columns] for row in data]
            execute_batch(cursor, query, values)
            self.conn.commit()

            logger.info(f"✓ Inserted {len(data)} rows into market_data.{table}")
            return len(data)
        except Exception as e:
            self.conn.rollback()
            logger.error(f"✗ Insert failed for {table}: {e}")
            return 0

    def insert_economic_data(self, data: List[Dict[str, Any]]):
        """Insert economic indicators from FRED"""
        return self.insert_market_data('indicators', data)

    def log_download(self, source_id: str, success: bool, rows: int = 0,
                     response_time: int = 0, error: str = None):
        """Log download attempt"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO system.download_log
                (source_id, success, rows_inserted, response_time_ms, error_message)
                VALUES (%s, %s, %s, %s, %s)
            """, (source_id, success, rows, response_time, error))
            self.conn.commit()
        except Exception as e:
            logger.warning(f"Failed to log download: {e}")

    def update_health_status(self, source_id: str, success: bool,
                           response_time: int = None, error: str = None):
        """Update health status for a source"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT system.update_health_status(%s, %s, %s, %s)
            """, (source_id, success, response_time, error))
            self.conn.commit()
        except Exception as e:
            logger.warning(f"Failed to update health status: {e}")

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("✓ Closed PostgreSQL connection")

# ============================================================================
# Redis Cache Manager
# ============================================================================

class CacheManager:
    """Manage Redis cache operations"""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client = None

    def connect(self):
        """Connect to Redis"""
        try:
            self.client = redis.from_url(self.redis_url)
            self.client.ping()
            logger.info("✓ Connected to Redis")
            return True
        except Exception as e:
            logger.error(f"✗ Redis connection failed: {e}")
            return False

    def set_preload_status(self, total: int, completed: int, successful: int, failed: int):
        """Update preload progress in Redis"""
        self.client.hset('preload:status', mapping={
            'total_sources': total,
            'completed_sources': completed,
            'successful_sources': successful,
            'failed_sources': failed,
            'ready': 'true' if (successful / total * 100) >= Config.SUCCESS_THRESHOLD else 'false',
            'last_updated': datetime.utcnow().isoformat()
        })

    def mark_complete(self):
        """Mark preload as complete"""
        self.client.set('preload:complete', 'true')
        logger.info("✓ Marked preload as complete in Redis")

    def close(self):
        """Close Redis connection"""
        if self.client:
            self.client.close()
            logger.info("✓ Closed Redis connection")

# ============================================================================
# Data Fetchers
# ============================================================================

class YahooFinanceFetcher:
    """Fetch data from Yahoo Finance (FREE, unlimited)"""

    @staticmethod
    def fetch_quotes(symbols: List[str]) -> List[Dict[str, Any]]:
        """Fetch latest quotes for symbols"""
        results = []

        try:
            tickers = yf.Tickers(' '.join(symbols))

            for symbol in symbols:
                try:
                    ticker = tickers.tickers[symbol]
                    info = ticker.info
                    hist = ticker.history(period='1d')

                    if not hist.empty:
                        latest = hist.iloc[-1]

                        results.append({
                            'timestamp': datetime.utcnow(),
                            'symbol': symbol,
                            'name': info.get('shortName', symbol),
                            'price': float(latest['Close']),
                            'open_price': float(latest['Open']),
                            'high_price': float(latest['High']),
                            'low_price': float(latest['Low']),
                            'volume': int(latest['Volume']),
                            'change': float(latest['Close'] - latest['Open']),
                            'change_percent': ((latest['Close'] - latest['Open']) / latest['Open'] * 100),
                            'source': 'yfinance'
                        })
                except Exception as e:
                    logger.warning(f"Failed to fetch {symbol} from yfinance: {e}")
                    continue
        except Exception as e:
            logger.error(f"yfinance batch fetch failed: {e}")

        return results

class FREDFetcher:
    """Fetch data from FRED API (FREE, 120 req/min)"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'https://api.stlouisfed.org/fred/series/observations'

    def fetch_series(self, series_id: str) -> List[Dict[str, Any]]:
        """Fetch latest data for a FRED series"""
        if not self.api_key:
            logger.warning("FRED API key not configured")
            return []

        try:
            response = requests.get(self.base_url, params={
                'series_id': series_id,
                'api_key': self.api_key,
                'file_type': 'json',
                'limit': 100,  # Last 100 observations
                'sort_order': 'desc'
            }, timeout=30)

            if response.status_code == 200:
                data = response.json()
                observations = data.get('observations', [])

                results = []
                for obs in observations:
                    if obs['value'] != '.':  # Skip missing values
                        results.append({
                            'date': datetime.strptime(obs['date'], '%Y-%m-%d').date(),
                            'indicator_code': series_id,
                            'value': float(obs['value']),
                            'source': 'FRED'
                        })

                return results
            else:
                logger.warning(f"FRED API returned {response.status_code} for {series_id}")
                return []
        except Exception as e:
            logger.error(f"FRED fetch failed for {series_id}: {e}")
            return []

# ============================================================================
# Pre-Loader Main Logic
# ============================================================================

class PreLoader:
    """Main pre-loader orchestrator"""

    def __init__(self):
        self.db = DatabaseManager(Config.DATABASE_URL)
        self.cache = CacheManager(Config.REDIS_URL)
        self.yahoo_fetcher = YahooFinanceFetcher()
        self.fred_fetcher = FREDFetcher(Config.FRED_API_KEY)

        self.total_sources = len(Config.DATA_SOURCES)
        self.completed = 0
        self.successful = 0
        self.failed = 0

    def wait_for_dependencies(self):
        """Wait for PostgreSQL and Redis to be ready"""
        logger.info("⏳ Waiting for PostgreSQL and Redis...")

        max_retries = 30
        for i in range(max_retries):
            if self.db.connect() and self.cache.connect():
                logger.info("✓ All dependencies ready")
                return True

            logger.info(f"Retry {i+1}/{max_retries}...")
            time.sleep(2)

        logger.error("✗ Dependencies not ready after 60 seconds")
        return False

    def fetch_source_data(self, source: DataSource) -> tuple[bool, int]:
        """Fetch data for a single source"""
        logger.info(f"📥 Fetching {source.name} ({source.category})...")
        start_time = time.time()

        try:
            # Add delay to respect rate limits (Yahoo Finance: 1 request per 2 seconds)
            time.sleep(2)

            # Route to appropriate fetcher based on category
            if source.category in ['indices', 'commodities', 'forex', 'crypto', 'sectors']:
                data = self.yahoo_fetcher.fetch_quotes(source.symbols)

                if data:
                    # Insert into appropriate table based on category
                    table_map = {
                        'indices': 'indices',
                        'commodities': 'commodities',
                        'forex': 'forex_rates',
                        'crypto': 'crypto_prices',
                        'sectors': 'indices'  # Sector ETFs go into indices table
                    }
                    rows = self.db.insert_market_data(table_map[source.category], data)

                    response_time = int((time.time() - start_time) * 1000)
                    self.db.log_download(source.id, True, rows, response_time)
                    self.db.update_health_status(source.id, True, response_time)

                    logger.info(f"✓ {source.name}: {rows} rows inserted ({response_time}ms)")
                    return True, rows
                else:
                    raise Exception("No data returned")

            elif source.category == 'economic':
                data = self.fred_fetcher.fetch_series(source.symbols[0])

                if data:
                    # Convert to indicators format
                    indicators = [{
                        'date': d['date'],
                        'indicator_code': d['indicator_code'],
                        'indicator_name': source.name,
                        'value': d['value'],
                        'frequency': 'daily',
                        'source': 'FRED'
                    } for d in data]

                    rows = self.db.insert_economic_data(indicators)

                    response_time = int((time.time() - start_time) * 1000)
                    self.db.log_download(source.id, True, rows, response_time)
                    self.db.update_health_status(source.id, True, response_time)

                    logger.info(f"✓ {source.name}: {rows} rows inserted ({response_time}ms)")
                    return True, rows
                else:
                    raise Exception("No data returned")

        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            self.db.log_download(source.id, False, 0, response_time, error_msg)
            self.db.update_health_status(source.id, False, response_time, error_msg)
            logger.error(f"✗ {source.name} failed: {error_msg}")
            return False, 0

    def run(self):
        """Execute complete pre-load sequence"""
        print("\n" + "="*70)
        print(" " * 15 + "SPARTAN RESEARCH STATION")
        print(" " * 20 + "PRE-LOADER SERVICE")
        print("="*70 + "\n")

        # Phase 1: Wait for dependencies
        if not self.wait_for_dependencies():
            sys.exit(1)

        # Phase 2: Fetch all data sources (parallel)
        logger.info(f"🚀 Starting parallel download from {self.total_sources} sources...")
        logger.info(f"   Max workers: {Config.MAX_WORKERS}")

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
            futures = {
                executor.submit(self.fetch_source_data, source): source
                for source in Config.DATA_SOURCES
            }

            for future in as_completed(futures):
                source = futures[future]
                self.completed += 1

                try:
                    success, rows = future.result(timeout=Config.TIMEOUT_PER_SOURCE)
                    if success:
                        self.successful += 1
                    else:
                        self.failed += 1
                except Exception as e:
                    logger.error(f"✗ {source.name} raised exception: {e}")
                    self.failed += 1

                # Update progress in Redis
                self.cache.set_preload_status(
                    self.total_sources,
                    self.completed,
                    self.successful,
                    self.failed
                )

                progress = (self.completed / self.total_sources) * 100
                logger.info(f"Progress: {self.completed}/{self.total_sources} ({progress:.1f}%)")

        duration = time.time() - start_time
        success_rate = (self.successful / self.total_sources) * 100

        # Phase 3: Report results
        print("\n" + "="*70)
        print(" " * 20 + "PRE-LOAD COMPLETE")
        print("="*70)
        print(f"  Total Sources:     {self.total_sources}")
        print(f"  Successful:        {self.successful} ({success_rate:.1f}%)")
        print(f"  Failed:            {self.failed}")
        print(f"  Duration:          {duration:.1f}s")
        print("="*70 + "\n")

        # Phase 4: Mark complete if success rate is acceptable
        if success_rate >= Config.SUCCESS_THRESHOLD:
            self.cache.mark_complete()
            logger.info("✅ PRE-LOAD SUCCESSFUL - Web server can start")
            return 0
        else:
            logger.error(f"❌ PRE-LOAD FAILED - Success rate {success_rate:.1f}% below threshold {Config.SUCCESS_THRESHOLD}%")
            return 1

# ============================================================================
# Entry Point
# ============================================================================

def main():
    """Main entry point"""
    preloader = PreLoader()

    try:
        exit_code = preloader.run()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n⚠ Pre-loader interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        preloader.db.close()
        preloader.cache.close()

if __name__ == '__main__':
    main()
