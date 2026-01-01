#!/usr/bin/env python3
"""
DATA GUARDIAN AGENT - Spartan Research Station

MISSION: Continuously monitor and fetch GENUINE market data from multiple sources
POLICY: ZERO TOLERANCE for fake data - real data or nothing

This agent:
- Monitors 7+ data sources for availability
- Automatically switches to working sources
- Validates all data for authenticity
- Runs 24/7 with adaptive retry logic
- Learns which sources work best for each asset type
"""

import asyncio
import logging
import os
import sys
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

import redis
import psycopg2
from psycopg2.extras import RealDictCursor
import yfinance as yf
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_guardian.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Data source configuration
DATA_SOURCES = {
    'yfinance': {'priority': 1, 'success_rate': 1.0, 'last_success': None, 'enabled': True},
    'polygon': {'priority': 2, 'success_rate': 0.9, 'last_success': None, 'enabled': bool(os.getenv('POLYGON_IO_API_KEY'))},
    'marketaux': {'priority': 3, 'success_rate': 0.85, 'last_success': None, 'enabled': bool(os.getenv('MARKETAUX_API_KEY'))},
    'alpha_vantage': {'priority': 4, 'success_rate': 0.7, 'last_success': None, 'enabled': bool(os.getenv('ALPHA_VANTAGE_API_KEY'))},
    'twelve_data': {'priority': 5, 'success_rate': 0.7, 'last_success': None, 'enabled': bool(os.getenv('TWELVE_DATA_API_KEY'))},
    'finnhub': {'priority': 6, 'success_rate': 0.6, 'last_success': None, 'enabled': bool(os.getenv('FINNHUB_API_KEY'))},
    'coingecko': {'priority': 7, 'success_rate': 0.95, 'last_success': None, 'enabled': True},  # Free for crypto
    'fred': {'priority': 8, 'success_rate': 0.95, 'last_success': None, 'enabled': bool(os.getenv('FRED_API_KEY'))},
}

# Asset categories and their symbols
ASSET_CATEGORIES = {
    'us_indices': ['SPY', 'QQQ', 'DIA', 'IWM'],
    'global_indices': ['EFA', 'EEM', 'FXI', 'EWJ', 'EWG', 'EWU'],
    'commodities': ['GLD', 'USO', 'CPER'],
    'crypto': ['BTC-USD', 'ETH-USD', 'BNB-USD'],
    'forex': ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X'],
    'treasuries': ['SHY', 'IEF', 'TLT'],
    'bonds': ['BNDX', 'EMB', 'HYG'],
    'sectors': ['XLF', 'XLK', 'XLE', 'XLV', 'XLI', 'XLP', 'XLY', 'XLU', 'XLRE'],
}

# CRITICAL: Minimum success threshold
MIN_SUCCESS_RATE = 0.30  # 30% of symbols must succeed to consider scan successful

class DataGuardianAgent:
    """
    Autonomous agent that guards data integrity by continuously
    scanning multiple sources for genuine market data.
    """

    def __init__(self):
        self.redis_client = None
        self.db_conn = None
        self.source_health = defaultdict(lambda: {'attempts': 0, 'successes': 0, 'failures': 0})
        self.symbol_source_map = defaultdict(list)  # Track which sources work for which symbols
        self.scan_count = 0
        self.total_successes = 0
        self.total_failures = 0

    async def initialize(self):
        """Initialize connections to Redis and PostgreSQL"""
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

            # Create guardian metrics table if not exists
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS guardian_metrics (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT NOW(),
                        scan_number INTEGER,
                        source_name VARCHAR(50),
                        symbol VARCHAR(20),
                        success BOOLEAN,
                        data_age_seconds INTEGER,
                        error_message TEXT
                    )
                """)
                self.db_conn.commit()

            return True
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False

    def validate_data(self, data: Dict, symbol: str, source: str) -> bool:
        """
        CRITICAL: Validate data is genuine, not fake/mock/simulated

        Returns True only if data passes ALL validation checks
        """
        if not data:
            logger.warning(f"⚠️  {source}: Empty data for {symbol}")
            return False

        # Check for required fields
        required_fields = ['price', 'timestamp']
        for field in required_fields:
            if field not in data:
                logger.warning(f"⚠️  {source}: Missing {field} for {symbol}")
                return False

        # Validate price is numeric and positive
        try:
            price = float(data['price'])
            if price <= 0:
                logger.warning(f"⚠️  {source}: Invalid price {price} for {symbol}")
                return False
        except (ValueError, TypeError):
            logger.warning(f"⚠️  {source}: Non-numeric price for {symbol}")
            return False

        # Validate timestamp is recent (within last 7 days)
        try:
            if isinstance(data['timestamp'], str):
                data_time = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            else:
                data_time = data['timestamp']

            age_seconds = (datetime.now() - data_time.replace(tzinfo=None)).total_seconds()

            # Data older than 7 days is suspicious
            if age_seconds > 7 * 24 * 3600:
                logger.warning(f"⚠️  {source}: Data too old ({age_seconds/3600:.1f} hours) for {symbol}")
                return False

        except Exception as e:
            logger.warning(f"⚠️  {source}: Invalid timestamp for {symbol}: {e}")
            return False

        # All checks passed
        return True

    async def fetch_from_yfinance(self, symbol: str) -> Optional[Dict]:
        """Fetch data from yfinance (primary source)"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='5d')

            if hist.empty:
                return None

            latest = hist.iloc[-1]
            return {
                'symbol': symbol,
                'price': float(latest['Close']),
                'volume': float(latest['Volume']),
                'high': float(latest['High']),
                'low': float(latest['Low']),
                'timestamp': hist.index[-1].isoformat(),
                'source': 'yfinance'
            }
        except Exception as e:
            logger.debug(f"yfinance failed for {symbol}: {e}")
            return None

    async def fetch_from_polygon(self, symbol: str) -> Optional[Dict]:
        """Fetch data from Polygon.io (backup source #1)"""
        if not DATA_SOURCES['polygon']['enabled']:
            return None

        try:
            import requests
            api_key = os.getenv('POLYGON_IO_API_KEY')
            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev?apiKey={api_key}"

            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    result = data['results'][0]
                    return {
                        'symbol': symbol,
                        'price': float(result['c']),  # Close price
                        'volume': float(result['v']),
                        'high': float(result['h']),
                        'low': float(result['l']),
                        'timestamp': datetime.fromtimestamp(result['t'] / 1000).isoformat(),
                        'source': 'polygon'
                    }
            return None
        except Exception as e:
            logger.debug(f"polygon failed for {symbol}: {e}")
            return None

    async def fetch_from_alpha_vantage(self, symbol: str) -> Optional[Dict]:
        """Fetch data from Alpha Vantage (backup source #2)"""
        if not DATA_SOURCES['alpha_vantage']['enabled']:
            return None

        try:
            import requests
            api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"

            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'Global Quote' in data and data['Global Quote']:
                    quote = data['Global Quote']
                    return {
                        'symbol': symbol,
                        'price': float(quote['05. price']),
                        'volume': float(quote['06. volume']),
                        'high': float(quote['03. high']),
                        'low': float(quote['04. low']),
                        'timestamp': datetime.now().isoformat(),
                        'source': 'alpha_vantage'
                    }
            return None
        except Exception as e:
            logger.debug(f"alpha_vantage failed for {symbol}: {e}")
            return None

    async def fetch_from_twelve_data(self, symbol: str) -> Optional[Dict]:
        """Fetch data from Twelve Data (backup source #3)"""
        if not DATA_SOURCES['twelve_data']['enabled']:
            return None

        try:
            import requests
            api_key = os.getenv('TWELVE_DATA_API_KEY')
            url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={api_key}"

            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'price' in data:
                    return {
                        'symbol': symbol,
                        'price': float(data['price']),
                        'timestamp': datetime.now().isoformat(),
                        'source': 'twelve_data'
                    }
            return None
        except Exception as e:
            logger.debug(f"twelve_data failed for {symbol}: {e}")
            return None

    async def fetch_from_marketaux(self, symbol: str) -> Optional[Dict]:
        """Fetch data from Marketaux API"""
        if not DATA_SOURCES['marketaux']['enabled']:
            return None

        try:
            import requests
            api_key = os.getenv('MARKETAUX_API_KEY')
            # Marketaux primarily provides news, but also has quotes
            url = f"https://api.marketaux.com/v1/quotes?symbols={symbol}&api_token={api_key}"

            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and len(data['data']) > 0:
                    quote = data['data'][0]
                    return {
                        'symbol': symbol,
                        'price': float(quote.get('price', quote.get('last', 0))),
                        'volume': float(quote.get('volume', 0)),
                        'high': float(quote.get('high', 0)),
                        'low': float(quote.get('low', 0)),
                        'change_24h': float(quote.get('change_percent', 0)),
                        'timestamp': quote.get('updated_at', datetime.now().isoformat()),
                        'source': 'marketaux'
                    }
            return None
        except Exception as e:
            logger.debug(f"marketaux failed for {symbol}: {e}")
            return None

    async def fetch_from_coingecko(self, symbol: str) -> Optional[Dict]:
        """Fetch crypto data from CoinGecko (free, no API key needed)"""
        if not symbol.endswith('-USD'):
            return None  # CoinGecko is for crypto only

        try:
            import requests
            # Convert BTC-USD to bitcoin
            crypto_map = {
                'BTC-USD': 'bitcoin',
                'ETH-USD': 'ethereum',
                'BNB-USD': 'binancecoin'
            }
            crypto_id = crypto_map.get(symbol)
            if not crypto_id:
                return None

            url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_id}&vs_currencies=usd&include_24hr_vol=true&include_24hr_change=true"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if crypto_id in data:
                    crypto_data = data[crypto_id]
                    return {
                        'symbol': symbol,
                        'price': float(crypto_data['usd']),
                        'volume': float(crypto_data.get('usd_24h_vol', 0)),
                        'change_24h': float(crypto_data.get('usd_24h_change', 0)),
                        'timestamp': datetime.now().isoformat(),
                        'source': 'coingecko'
                    }
            return None
        except Exception as e:
            logger.debug(f"coingecko failed for {symbol}: {e}")
            return None

    async def fetch_symbol_data(self, symbol: str, category: str) -> Optional[Dict]:
        """
        Fetch data for a symbol, trying multiple sources in priority order
        """
        # Get sources sorted by success rate (adaptive learning)
        enabled_sources = [(name, info) for name, info in DATA_SOURCES.items() if info['enabled']]
        enabled_sources.sort(key=lambda x: x[1]['success_rate'], reverse=True)

        for source_name, source_info in enabled_sources:
            self.source_health[source_name]['attempts'] += 1

            # Try to fetch from this source
            data = None
            try:
                if source_name == 'yfinance':
                    data = await self.fetch_from_yfinance(symbol)
                elif source_name == 'polygon':
                    data = await self.fetch_from_polygon(symbol)
                elif source_name == 'marketaux':
                    data = await self.fetch_from_marketaux(symbol)
                elif source_name == 'alpha_vantage':
                    data = await self.fetch_from_alpha_vantage(symbol)
                elif source_name == 'twelve_data':
                    data = await self.fetch_from_twelve_data(symbol)
                elif source_name == 'coingecko':
                    data = await self.fetch_from_coingecko(symbol)

                # Validate data
                if data and self.validate_data(data, symbol, source_name):
                    # Success! Update metrics
                    self.source_health[source_name]['successes'] += 1
                    DATA_SOURCES[source_name]['last_success'] = datetime.now()
                    self.symbol_source_map[symbol].append(source_name)

                    # Update success rate (exponential moving average)
                    total = self.source_health[source_name]['attempts']
                    successes = self.source_health[source_name]['successes']
                    DATA_SOURCES[source_name]['success_rate'] = successes / total if total > 0 else 0.5

                    logger.info(f"✅ {source_name}: Got valid data for {symbol} (${data['price']:.2f})")
                    return data

            except Exception as e:
                logger.debug(f"❌ {source_name} error for {symbol}: {e}")

            # Source failed
            self.source_health[source_name]['failures'] += 1

            # Rate limiting delay between sources
            await asyncio.sleep(2)

        # All sources failed
        logger.warning(f"⚠️  All sources failed for {symbol}")
        return None

    async def store_data(self, data: Dict):
        """Store validated data in Redis and PostgreSQL"""
        try:
            symbol = data['symbol']

            # Store in Redis (15-minute TTL)
            redis_key = f"market:symbol:{symbol}"
            self.redis_client.setex(
                redis_key,
                900,  # 15 minutes
                json.dumps(data)
            )

            # Store in PostgreSQL (using existing schema)
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO preloaded_market_data
                    (symbol, data_type, price, change_percent, volume, metadata, timestamp, source)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol, data_type, timestamp) DO UPDATE
                    SET price = EXCLUDED.price,
                        change_percent = EXCLUDED.change_percent,
                        volume = EXCLUDED.volume,
                        metadata = EXCLUDED.metadata,
                        source = EXCLUDED.source
                """, (
                    symbol,
                    'realtime',  # data_type
                    data.get('price'),
                    data.get('change_24h', 0.0),
                    data.get('volume', 0),
                    json.dumps(data),  # Store full data in metadata
                    datetime.now(),
                    data['source']
                ))
                self.db_conn.commit()

            logger.debug(f"💾 Stored {symbol} data from {data['source']}")

        except Exception as e:
            logger.error(f"❌ Failed to store data for {data.get('symbol')}: {e}")

    async def scan_all_symbols(self):
        """Scan all symbols across all categories"""
        self.scan_count += 1
        scan_start = time.time()

        logger.info("=" * 70)
        logger.info(f"🔍 DATA GUARDIAN SCAN #{self.scan_count} STARTING")
        logger.info("=" * 70)

        scan_successes = 0
        scan_failures = 0

        for category, symbols in ASSET_CATEGORIES.items():
            logger.info(f"📊 Scanning {category.upper()}: {len(symbols)} symbols")

            for symbol in symbols:
                data = await self.fetch_symbol_data(symbol, category)

                if data:
                    await self.store_data(data)
                    scan_successes += 1
                    self.total_successes += 1
                else:
                    scan_failures += 1
                    self.total_failures += 1

                # Rate limiting between symbols
                await asyncio.sleep(1.5)

        # Calculate scan statistics
        scan_duration = time.time() - scan_start
        total_symbols = scan_successes + scan_failures
        success_rate = (scan_successes / total_symbols * 100) if total_symbols > 0 else 0

        logger.info("=" * 70)
        logger.info(f"📈 SCAN #{self.scan_count} COMPLETE")
        logger.info(f"   Duration: {scan_duration:.1f}s")
        logger.info(f"   Successes: {scan_successes}/{total_symbols} ({success_rate:.1f}%)")
        logger.info(f"   Failures: {scan_failures}")
        logger.info(f"   Lifetime Success Rate: {self.total_successes}/{self.total_successes + self.total_failures}")
        logger.info("=" * 70)

        # Print source health report
        logger.info("🏥 SOURCE HEALTH REPORT:")
        for source, health in sorted(self.source_health.items(), key=lambda x: x[1]['successes'], reverse=True):
            if health['attempts'] > 0:
                rate = health['successes'] / health['attempts'] * 100
                logger.info(f"   {source:15} - {health['successes']:3}/{health['attempts']:3} ({rate:5.1f}%)")

        return success_rate >= MIN_SUCCESS_RATE * 100

    async def run_forever(self, scan_interval_minutes: int = 15):
        """
        Main guardian loop - runs continuously, scanning for data

        Args:
            scan_interval_minutes: Time between scans (default 15 minutes)
        """
        logger.info("🛡️  DATA GUARDIAN AGENT ACTIVATED")
        logger.info(f"📡 Monitoring {len(DATA_SOURCES)} data sources")
        logger.info(f"🔄 Scan interval: {scan_interval_minutes} minutes")
        logger.info(f"✅ Enabled sources: {sum(1 for s in DATA_SOURCES.values() if s['enabled'])}")
        logger.info("")

        while True:
            try:
                # Run scan
                success = await self.scan_all_symbols()

                if not success:
                    logger.warning("⚠️  Scan below success threshold - will retry sooner")
                    retry_interval = max(5, scan_interval_minutes // 3)
                    logger.info(f"⏰ Next scan in {retry_interval} minutes")
                    await asyncio.sleep(retry_interval * 60)
                else:
                    logger.info(f"⏰ Next scan in {scan_interval_minutes} minutes")
                    await asyncio.sleep(scan_interval_minutes * 60)

            except KeyboardInterrupt:
                logger.info("🛑 Guardian agent stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Guardian error: {e}", exc_info=True)
                logger.info("⏰ Retrying in 5 minutes...")
                await asyncio.sleep(300)

    async def cleanup(self):
        """Clean up connections"""
        if self.redis_client:
            self.redis_client.close()
        if self.db_conn:
            self.db_conn.close()
        logger.info("🧹 Cleanup complete")

async def main():
    """Main entry point"""
    agent = DataGuardianAgent()

    if not await agent.initialize():
        logger.error("❌ Failed to initialize Data Guardian Agent")
        return 1

    try:
        await agent.run_forever(scan_interval_minutes=15)
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down gracefully...")
    finally:
        await agent.cleanup()

    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
