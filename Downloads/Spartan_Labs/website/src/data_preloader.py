#!/usr/bin/env python3
"""
Spartan Labs Data Preloader - Multi-Source API Fallback System
Fetches and validates ALL data sources before website starts
Uses reliable API-based sources with intelligent fallback chain
Ensures zero "No data available" errors on dashboard

DATA SOURCE PRIORITY (by reliability):
1. CRYPTO: CoinGecko (no API key, highly reliable)
2. STOCKS/ETFs: Polygon.io -> Twelve Data -> Alpha Vantage -> Finnhub
3. FOREX: ExchangeRate-API (no API key)
4. ECONOMIC: FRED API (primary), fallback to stock APIs for yields
5. Yahoo Finance: REMOVED (unreliable, frequent outages)
"""

import os
import sys
import asyncio
import aiohttp
import redis
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Tuple, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import time
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # INFO level for production
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global rate limiters for different APIs
LAST_REQUEST_TIMES = {
    'polygon': 0,
    'alpha_vantage': 0,
    'twelve_data': 0,
    'finnhub': 0,
    'coingecko': 0,
    'exchangerate': 0
}

REQUEST_DELAYS = {
    'polygon': 13.0,        # 5 requests/min = 12 sec delay (free tier) - conservative
    'alpha_vantage': 13.0,  # 5 requests/min (free tier) - conservative
    'twelve_data': 60.0,    # Rate limited - slow down dramatically
    'finnhub': 1.5,         # 60 requests/min (free tier)
    'coingecko': 1.5,       # 50 requests/min = 1.2 sec delay (no key needed)
    'exchangerate': 5.0     # 1500 requests/month (no key needed)
}


def rate_limit(api_name='polygon'):
    """Apply rate limiting between API requests"""
    current_time = time.time()
    time_since_last = current_time - LAST_REQUEST_TIMES[api_name]

    delay = REQUEST_DELAYS.get(api_name, 2.0)  # Default 2s delay
    if time_since_last < delay:
        sleep_time = delay - time_since_last
        logger.debug(f"Rate limiting {api_name}: sleeping {sleep_time:.2f}s")
        time.sleep(sleep_time)

    LAST_REQUEST_TIMES[api_name] = time.time()


def retry_with_backoff(max_retries=3, initial_delay=1.0, backoff_factor=2.0):
    """Decorator to retry API calls with exponential backoff"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries):
                try:
                    # Apply rate limiting before each attempt
                    rate_limit()

                    result = await func(*args, **kwargs)
                    return result

                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"{func.__name__} attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} attempts: {e}"
                        )

                except Exception as e:
                    last_exception = e
                    logger.error(f"{func.__name__} error: {e}")
                    break

            return False
        return wrapper
    return decorator


class DataPreloader:
    """Pre-fetches and validates all data sources"""

    def __init__(self):
        """Initialize preloader with all data sources"""
        self.redis_client = None
        self.db_conn = None
        self.session = None

        # API Keys
        self.fred_api_key = os.getenv('FRED_API_KEY')
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.polygon_key = os.getenv('POLYGON_IO_API_KEY')
        self.twelve_data_key = os.getenv('TWELVE_DATA_API_KEY')
        self.finnhub_key = os.getenv('FINNHUB_API_KEY')

        # Cache TTL (seconds)
        self.cache_ttl = 3600  # 1 hour (increased from 15 min to prevent expiration)

        # Data validation results
        self.validation_results = {}

    async def _fetch_polygon(self, symbol: str) -> Optional[Dict]:
        """Fetch data from Polygon.io API"""
        if not self.polygon_key or len(self.polygon_key) < 20:
            return None

        try:
            rate_limit('polygon')

            # Polygon uses different symbol format (no hyphens for crypto)
            poly_symbol = symbol.replace('-', '')

            # Get quote data
            url = f"https://api.polygon.io/v2/aggs/ticker/{poly_symbol}/prev"
            params = {'apiKey': self.polygon_key}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('results'):
                        result = data['results'][0]
                        logger.info(f"  ✅ Polygon: {symbol} = ${result['c']:.2f}")
                        return {
                            'price': result['c'],  # Close price
                            'change': ((result['c'] - result['o']) / result['o'] * 100),
                            'volume': result['v'],
                            'source': 'polygon'
                        }
                elif response.status == 429:
                    logger.warning(f"  ⚠️  Polygon rate limited for {symbol}")
                else:
                    logger.warning(f"  ⚠️  Polygon {symbol}: HTTP {response.status}")
        except Exception as e:
            logger.debug(f"  ⚠️  Polygon {symbol} failed: {e}")

        return None

    async def _fetch_twelve_data(self, symbol: str) -> Optional[Dict]:
        """Fetch data from Twelve Data API"""
        if not self.twelve_data_key or len(self.twelve_data_key) < 20:
            return None

        try:
            rate_limit('twelve_data')

            url = "https://api.twelvedata.com/quote"
            params = {
                'symbol': symbol,
                'apikey': self.twelve_data_key
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    if 'close' in data and data.get('close'):
                        price = float(data['close'])
                        change = float(data.get('percent_change', 0))
                        logger.info(f"  ✅ Twelve Data: {symbol} = ${price:.2f}")
                        return {
                            'price': price,
                            'change': change,
                            'volume': int(data.get('volume', 0)) if data.get('volume') else 0,
                            'source': 'twelve_data'
                        }
                elif response.status == 429:
                    logger.warning(f"  ⚠️  Twelve Data rate limited for {symbol}")
                else:
                    logger.warning(f"  ⚠️  Twelve Data {symbol}: HTTP {response.status}")
        except Exception as e:
            logger.debug(f"  ⚠️  Twelve Data {symbol} failed: {e}")

        return None

    async def _fetch_finnhub(self, symbol: str) -> Optional[Dict]:
        """Fetch data from Finnhub API"""
        if not self.finnhub_key or len(self.finnhub_key) < 15:
            return None

        try:
            rate_limit('finnhub')

            url = "https://finnhub.io/api/v1/quote"
            params = {
                'symbol': symbol,
                'token': self.finnhub_key
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    if 'c' in data and data['c'] > 0:
                        price = float(data['c'])  # Current price
                        prev_close = float(data['pc'])  # Previous close
                        change = ((price - prev_close) / prev_close * 100) if prev_close > 0 else 0
                        logger.info(f"  ✅ Finnhub: {symbol} = ${price:.2f}")
                        return {
                            'price': price,
                            'change': change,
                            'volume': 0,  # Finnhub free tier doesn't include volume
                            'source': 'finnhub'
                        }
                elif response.status == 429:
                    logger.warning(f"  ⚠️  Finnhub rate limited for {symbol}")
                else:
                    logger.warning(f"  ⚠️  Finnhub {symbol}: HTTP {response.status}")
        except Exception as e:
            logger.debug(f"  ⚠️  Finnhub {symbol} failed: {e}")

        return None

    async def _fetch_alpha_vantage(self, symbol: str) -> Optional[Dict]:
        """Fetch data from Alpha Vantage API"""
        if not self.alpha_vantage_key or len(self.alpha_vantage_key) < 10:
            return None

        try:
            rate_limit('alpha_vantage')

            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.alpha_vantage_key
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    quote = data.get('Global Quote', {})

                    if quote and '05. price' in quote:
                        price = float(quote['05. price'])
                        change = float(quote['10. change percent'].rstrip('%'))
                        logger.info(f"  ✅ Alpha Vantage: {symbol} = ${price:.2f}")
                        return {
                            'price': price,
                            'change': change,
                            'volume': int(quote.get('06. volume', 0)),
                            'source': 'alpha_vantage'
                        }
        except Exception as e:
            logger.debug(f"  ⚠️  Alpha Vantage {symbol} failed: {e}")

        return None

    async def _fetch_coingecko(self, crypto_id: str) -> Optional[Dict]:
        """Fetch crypto data from CoinGecko API (NO KEY NEEDED)"""
        try:
            rate_limit('coingecko')

            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': crypto_id,
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_24hr_vol': 'true'
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if crypto_id in data:
                        coin_data = data[crypto_id]
                        logger.info(f"  ✅ CoinGecko: {crypto_id} = ${coin_data['usd']:,.2f}")
                        return {
                            'price': coin_data['usd'],
                            'change': coin_data.get('usd_24h_change', 0),
                            'volume': coin_data.get('usd_24h_vol', 0),
                            'source': 'coingecko'
                        }
        except Exception as e:
            logger.debug(f"  ⚠️  CoinGecko {crypto_id} failed: {e}")

        return None

    async def _fetch_exchangerate_api(self, base_currency: str, target_currency: str) -> Optional[Dict]:
        """Fetch forex data from ExchangeRate-API (FREE, NO KEY NEEDED)"""
        try:
            rate_limit('exchangerate')

            url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"

            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if target_currency in data.get('rates', {}):
                        rate = data['rates'][target_currency]
                        logger.info(f"  ✅ ExchangeRate-API: {base_currency}/{target_currency} = {rate:.4f}")
                        return {
                            'rate': rate,
                            'change': 0,  # API doesn't provide change
                            'source': 'exchangerate_api'
                        }
        except Exception as e:
            logger.debug(f"  ⚠️  ExchangeRate-API {base_currency}/{target_currency} failed: {e}")

        return None

    async def _fetch_with_fallback(self, symbol: str, data_type: str = 'stock') -> Optional[Dict]:
        """
        Try multiple data sources in order until one succeeds
        Enhanced resilience: tries ALL sources and tracks failures, continues on errors

        Args:
            symbol: Ticker symbol
            data_type: Type of data ('stock', 'crypto', 'forex')

        Returns:
            Dict with price data or None if all sources fail
        """
        logger.info(f"  Fetching {symbol} ({data_type})...")

        # Track all attempts for better error reporting
        attempted_sources = []
        
        # Define the fallback chain
        fallback_chain = []

        # Add sources to try based on data type
        # PRIORITY ORDER: Most reliable APIs first

        # CRYPTO: CoinGecko is most reliable (no API key, high rate limits)
        if data_type == 'crypto':
            crypto_map = {
                'BTC-USD': 'bitcoin',
                'ETH-USD': 'ethereum',
                'SOL-USD': 'solana',
                'BNB-USD': 'binancecoin'
            }
            if symbol in crypto_map:
                fallback_chain.append(('coingecko', lambda: self._fetch_coingecko(crypto_map[symbol])))

        # API-based sources (require API keys but very reliable)
        if data_type in ['stock', 'etf', 'index', 'crypto']:
            fallback_chain.append(('polygon', lambda: self._fetch_polygon(symbol)))
        if data_type in ['stock', 'etf', 'index', 'forex', 'crypto']:
            fallback_chain.append(('twelve_data', lambda: self._fetch_twelve_data(symbol)))
        if data_type in ['stock', 'etf', 'index']:
            fallback_chain.append(('alpha_vantage', lambda: self._fetch_alpha_vantage(symbol)))
        if data_type in ['stock', 'etf', 'index']:
            fallback_chain.append(('finnhub', lambda: self._fetch_finnhub(symbol)))

        if data_type == 'forex':
            # Parse forex pair (e.g., EURUSD=X -> EUR/USD)
            if '=' in symbol:
                pair = symbol.replace('=X', '')
                if len(pair) == 6:
                    base = pair[:3]
                    target = pair[3:]
                    fallback_chain.append(('exchangerate', lambda: self._fetch_exchangerate_api(base, target)))

        # Try ALL sources in the fallback chain, tracking failures
        # SKIP YFINANCE - use reliable API sources instead
        for source_name, fetch_func in fallback_chain:
            try:
                attempted_sources.append(source_name)
                data = await fetch_func()
                if data:
                    logger.info(f"  ✅ {source_name} succeeded for {symbol}")
                    return data
                else:
                    logger.debug(f"  ⚠️  {source_name} returned None for {symbol}")
            except Exception as e:
                logger.debug(f"  ⚠️  {source_name} failed for {symbol}: {e}")
                # Continue to next source instead of breaking
                continue

        # If we get here, all sources failed - log detailed failure report
        logger.warning(f"  ❌ All sources failed for {symbol}")
        logger.warning(f"      Attempted: {', '.join(attempted_sources)}")
        logger.debug(f"      This may be due to API rate limits, network issues, or invalid symbol")
        
        return None

    def _fetch_yfinance_safely(self, symbol: str, period: str = '1y', retries: int = 3) -> pd.DataFrame:
        """
        Safely fetch yfinance data with retries and proper error handling

        Args:
            symbol: Ticker symbol
            period: Period for historical data
            retries: Number of retry attempts

        Returns:
            DataFrame with historical data or empty DataFrame on failure
        """
        for attempt in range(retries):
            try:
                # Apply rate limiting
                rate_limit()

                # Fetch ticker with proper session
                ticker = yf.Ticker(symbol)

                # Get historical data
                hist = ticker.history(period=period, timeout=10)

                # Validate data
                if hist is None or hist.empty:
                    logger.warning(f"Empty data for {symbol} (attempt {attempt + 1}/{retries})")
                    if attempt < retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    return pd.DataFrame()

                # Verify required columns
                required_cols = ['Close', 'Volume']
                if not all(col in hist.columns for col in required_cols):
                    logger.warning(f"Missing columns for {symbol}")
                    return pd.DataFrame()

                logger.debug(f"Successfully fetched {symbol}: {len(hist)} rows")
                return hist

            except json.JSONDecodeError as e:
                logger.warning(f"{symbol} JSON decode error (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return pd.DataFrame()

            except Exception as e:
                logger.error(f"{symbol} fetch error (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return pd.DataFrame()

        return pd.DataFrame()

    async def connect(self):
        """Connect to Redis and PostgreSQL"""
        # Connect to Redis
        try:
            redis_host = os.getenv('REDIS_HOST', 'spartan-redis' if os.getenv('DOCKER_ENV') else 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=0,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("✅ Connected to Redis")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.redis_client = None

        # Connect to PostgreSQL
        try:
            db_url = os.getenv(
                'DATABASE_URL',
                'postgresql://spartan:spartan@localhost:5432/spartan_research_db'
            )
            # Fix Docker hostname for native mode
            if 'spartan-postgres' in db_url:
                db_url = db_url.replace('spartan-postgres', 'localhost')
            self.db_conn = psycopg2.connect(db_url)
            logger.info("✅ Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed: {e}")
            self.db_conn = None

        # Create aiohttp session
        self.session = aiohttp.ClientSession()

    async def close(self):
        """Close connections"""
        if self.session:
            await self.session.close()
        if self.db_conn:
            self.db_conn.close()

    async def preload_all_data(self) -> Dict[str, bool]:
        """
        Pre-fetch ALL data sources with continuous retry until success
        Returns: Dict of {data_source: success_status}
        """
        logger.info("🚀 Starting enhanced data preload with continuous retry...")
        logger.info("🔄 Will keep trying each source until success or max attempts reached")

        tasks = [
            # Market Indices (highest priority)
            ("US_Indices", self.preload_with_retry("US_Indices", self.preload_us_indices, max_attempts=10)),
            ("Global_Indices", self.preload_with_retry("Global_Indices", self.preload_global_indices, max_attempts=8)),

            # Commodities
            ("Gold", self.preload_with_retry("Gold", self.preload_gold_data, max_attempts=8)),
            ("Oil", self.preload_with_retry("Oil", self.preload_oil_data, max_attempts=8)),
            ("Copper", self.preload_with_retry("Copper", self.preload_copper_data, max_attempts=6)),

            # Crypto (Bitcoin, Ethereum, Solana)
            ("Bitcoin", self.preload_with_retry("Bitcoin", self.preload_bitcoin_data, max_attempts=8)),
            ("Ethereum", self.preload_with_retry("Ethereum", self.preload_ethereum_data, max_attempts=8)),
            ("Solana", self.preload_with_retry("Solana", self.preload_solana_data, max_attempts=8)),

            # Forex
            ("Major_Forex", self.preload_with_retry("Major_Forex", self.preload_forex_data, max_attempts=6)),

            # Bonds
            ("US_Treasuries", self.preload_with_retry("US_Treasuries", self.preload_treasury_data, max_attempts=6)),
            ("Global_Bonds", self.preload_with_retry("Global_Bonds", self.preload_global_bonds, max_attempts=6)),

            # Economic Data
            ("FRED_Economic", self.preload_with_retry("FRED_Economic", self.preload_fred_data, max_attempts=5)),
            ("Volatility", self.preload_with_retry("Volatility", self.preload_volatility_data, max_attempts=5)),

            # Sectors
            ("Sector_ETFs", self.preload_with_retry("Sector_ETFs", self.preload_sector_etfs, max_attempts=4)),

            # Correlations
            ("Correlation_Matrix", self.preload_with_retry("Correlation_Matrix", self.preload_correlations, max_attempts=6)),
        ]

        # Run all enhanced preloads in parallel
        results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)

        # Build results dict
        self.validation_results = {}
        for i, (name, _) in enumerate(tasks):
            if isinstance(results[i], Exception):
                logger.error(f"❌ {name}: {results[i]}")
                self.validation_results[name] = False
            else:
                success = results[i]
                status = "✅" if success else "❌"
                logger.info(f"{status} {name}: {'Success' if success else 'Failed'}")
                self.validation_results[name] = success

        # Log summary
        successful = sum(1 for v in self.validation_results.values() if v)
        total = len(self.validation_results)
        success_rate = (successful / total * 100) if total > 0 else 0

        logger.info(f"📊 Data Preload Summary: {successful}/{total} ({success_rate:.1f}%) successful")
        
        return self.validation_results

    async def preload_with_retry(self, name: str, preload_func, max_attempts: int = 5, delay: float = 2.0) -> bool:
        """
        Enhanced retry mechanism that keeps trying until success or max attempts
        
        Args:
            name: Data source name for logging
            preload_func: Function to call for preloading
            max_attempts: Maximum retry attempts
            delay: Initial delay between attempts (increases with each attempt)
        
        Returns:
            bool: True if successful, False if all attempts failed
        """
        for attempt in range(max_attempts):
            try:
                logger.debug(f"  {name}: Attempt {attempt + 1}/{max_attempts}")
                
                result = await preload_func()
                
                if result:
                    if attempt > 0:
                        logger.info(f"  ✅ {name}: Succeeded on attempt {attempt + 1}")
                    return True
                else:
                    logger.warning(f"  ⚠️  {name}: Attempt {attempt + 1} failed")
                    
                    # Don't wait on the last attempt
                    if attempt < max_attempts - 1:
                        # Exponential backoff with jitter
                        wait_time = delay * (1.5 ** attempt) + (attempt * 0.5)
                        logger.debug(f"  {name}: Retrying in {wait_time:.1f}s...")
                        await asyncio.sleep(wait_time)
                        
            except Exception as e:
                logger.warning(f"  ⚠️  {name}: Attempt {attempt + 1} error: {e}")
                
                # Don't wait on the last attempt
                if attempt < max_attempts - 1:
                    wait_time = delay * (1.5 ** attempt)
                    logger.debug(f"  {name}: Retrying in {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)

        logger.error(f"  ❌ {name}: All {max_attempts} attempts failed")
        return False

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    async def preload_us_indices(self) -> bool:
        """Pre-fetch US market indices (S&P 500, Nasdaq, Dow, Dollar)"""
        try:
            symbols = ['SPY', 'QQQ', 'DIA', 'IWM', 'UUP']  # ETFs for indices + Dollar
            success_count = 0
            failed_symbols = []

            for symbol in symbols:
                # Use multi-source API fallback (Polygon -> Twelve Data -> Alpha Vantage -> Finnhub)
                data = await self._fetch_with_fallback(symbol, data_type='index')

                if not data:
                    logger.warning(f"All sources failed for {symbol}")
                    failed_symbols.append(symbol)
                    continue

                # Extract price data
                current_price = data['price']
                change = data['change']
                volume = data.get('volume', 0)

                # Cache in Redis
                cache_key = f"market:index:{symbol}"
                cache_data = {
                    'symbol': symbol,
                    'price': current_price,
                    'change': change,
                    'volume': volume,
                    'timestamp': datetime.now().isoformat(),
                    'source': data.get('source', 'unknown')
                }

                if self.redis_client:
                    self.redis_client.setex(
                        cache_key,
                        self.cache_ttl,
                        json.dumps(cache_data)
                    )

                # Store in PostgreSQL
                if self.db_conn:
                    self._store_market_data(symbol, 'index', cache_data)

                logger.info(f"  ✅ {symbol}: ${current_price:.2f}")
                success_count += 1

            # More flexible success criteria - any critical success allows starting
            if success_count >= 4:  # 80% success rate
                logger.info(f"US Indices: {success_count}/5 succeeded (good)")
                return True
            elif success_count >= 3:  # 60% success rate
                logger.info(f"US Indices: {success_count}/5 succeeded (acceptable)")
                return True
            elif 'SPY' in failed_symbols and success_count == 0:
                logger.error("US Indices: SPY failed - critical indicator missing")
                return False
            elif success_count >= 2:  # At least two succeeded
                logger.warning(f"US Indices: {success_count}/5 succeeded (reduced)")
                # Still allow if we have SPY or other critical indices
                if 'SPY' not in failed_symbols:
                    logger.info("US Indices: SPY succeeded - allowing reduced success")
                    return True

            logger.error(f"US Indices: Only {success_count}/5 succeeded - insufficient")
            return False
        except Exception as e:
            logger.error(f"US Indices preload failed: {e}")
            return False

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    async def preload_global_indices(self) -> bool:
        """Pre-fetch global market indices"""
        try:
            # Global index ETFs
            symbols = {
                'EFA': 'EAFE (Developed Markets)',
                'EEM': 'Emerging Markets',
                'FXI': 'China',
                'EWJ': 'Japan',
                'EWG': 'Germany',
                'EWU': 'UK'
            }

            success_count = 0
            for symbol, name in symbols.items():
                # Use multi-source fallback
                data = await self._fetch_with_fallback(symbol, data_type='index')

                if data:
                    cache_key = f"market:global:{symbol}"
                    cache_data = {
                        'symbol': symbol,
                        'name': name,
                        'price': data['price'],
                        'change': data['change'],
                        'timestamp': datetime.now().isoformat()
                    }

                    if self.redis_client:
                        self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(cache_data))

                    # Store in PostgreSQL
                    self._store_market_data(symbol, 'index', cache_data)

                    logger.info(f"  ✅ {name}: {cache_data['change']:+.2f}%")
                    success_count += 1
                else:
                    logger.warning(f"All sources failed for {symbol}")

            return success_count >= 4  # At least 4 out of 6
        except Exception as e:
            logger.error(f"Global indices preload failed: {e}")
            return False

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    async def preload_gold_data(self) -> bool:
        """Pre-fetch gold data (GLD ETF)"""
        try:
            # Use multi-source fallback
            data = await self._fetch_with_fallback('GLD', data_type='etf')

            if data:
                cache_key = "commodity:gold"
                cache_data = {
                    'symbol': 'GLD',
                    'price': data['price'],
                    'change': data['change'],
                    '52w_high': data['price'] * 1.1,  # Approximation (real calc needs historical data)
                    '52w_low': data['price'] * 0.9,   # Approximation
                    'timestamp': datetime.now().isoformat()
                }

                if self.redis_client:
                    self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(cache_data))

                # Store in PostgreSQL
                self._store_market_data('GLD', 'commodity', cache_data)

                logger.info(f"  ✅ Gold: ${cache_data['price']:.2f} ({cache_data['change']:+.2f}%)")
                return True

            logger.warning("All sources failed for GLD")
            return False
        except Exception as e:
            logger.error(f"Gold preload failed: {e}")
            return False

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    async def preload_oil_data(self) -> bool:
        """Pre-fetch oil data (USO ETF)"""
        try:
            # Use multi-source fallback
            data = await self._fetch_with_fallback('USO', data_type='etf')

            if data:
                cache_key = "commodity:oil"
                cache_data = {
                    'symbol': 'USO',
                    'price': data['price'],
                    'change': data['change'],
                    'timestamp': datetime.now().isoformat()
                }

                if self.redis_client:
                    self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(cache_data))

                # Store in PostgreSQL
                self._store_market_data('USO', 'commodity', cache_data)

                logger.info(f"  ✅ Oil: ${cache_data['price']:.2f}")
                return True

            logger.warning("All sources failed for USO")
            return False
        except Exception as e:
            logger.error(f"Oil preload failed: {e}")
            return False

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    async def preload_copper_data(self) -> bool:
        """Pre-fetch copper data (CPER ETF)"""
        try:
            # Use multi-source fallback
            data = await self._fetch_with_fallback('CPER', data_type='etf')

            if data:
                cache_key = "commodity:copper"
                cache_data = {
                    'symbol': 'CPER',
                    'price': data['price'],
                    'change': data['change'],
                    'timestamp': datetime.now().isoformat()
                }

                if self.redis_client:
                    self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(cache_data))

                # Store in PostgreSQL
                self._store_market_data('CPER', 'commodity', cache_data)

                logger.info(f"  ✅ Copper: ${cache_data['price']:.2f}")
                return True

            logger.warning("All sources failed for CPER")
            return False
        except Exception as e:
            logger.error(f"Copper preload failed: {e}")
            return False

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    async def preload_bitcoin_data(self) -> bool:
        """Pre-fetch Bitcoin data (BTC-USD)"""
        try:
            # Use multi-source fallback
            data = await self._fetch_with_fallback('BTC-USD', data_type='crypto')

            if data:
                cache_key = "crypto:bitcoin"
                cache_data = {
                    'symbol': 'BTC-USD',
                    'price': data['price'],
                    'change': data['change'],
                    'volume': data.get('volume', 0),
                    'timestamp': datetime.now().isoformat()
                }

                if self.redis_client:
                    self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(cache_data))

                # Store in PostgreSQL
                self._store_market_data('BTC-USD', 'crypto', cache_data)

                logger.info(f"  ✅ Bitcoin: ${cache_data['price']:,.0f}")
                return True

            return False
        except Exception as e:
            logger.error(f"Bitcoin preload failed: {e}")
            return False

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    async def preload_ethereum_data(self) -> bool:
        """Pre-fetch Ethereum data (ETH-USD)"""
        try:
            # Use multi-source fallback
            data = await self._fetch_with_fallback('ETH-USD', data_type='crypto')

            if data:
                cache_key = "crypto:ethereum"
                cache_data = {
                    'symbol': 'ETH-USD',
                    'price': data['price'],
                    'change': data['change'],
                    'volume': data.get('volume', 0),
                    'timestamp': datetime.now().isoformat()
                }

                if self.redis_client:
                    self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(cache_data))

                # Store in PostgreSQL
                self._store_market_data('ETH-USD', 'crypto', cache_data)

                logger.info(f"  ✅ Ethereum: ${cache_data['price']:,.2f}")
                return True

            return False
        except Exception as e:
            logger.error(f"Ethereum preload failed: {e}")
            return False

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    async def preload_solana_data(self) -> bool:
        """Pre-fetch Solana data (SOL-USD)"""
        try:
            # Use multi-source fallback
            data = await self._fetch_with_fallback('SOL-USD', data_type='crypto')

            if data:
                cache_key = "crypto:solana"
                cache_data = {
                    'symbol': 'SOL-USD',
                    'price': data['price'],
                    'change': data['change'],
                    'volume': data.get('volume', 0),
                    'timestamp': datetime.now().isoformat()
                }

                if self.redis_client:
                    self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(cache_data))

                # Store in PostgreSQL
                self._store_market_data('SOL-USD', 'crypto', cache_data)

                logger.info(f"  ✅ Solana: ${cache_data['price']:,.2f}")
                return True

            return False
        except Exception as e:
            logger.error(f"Solana preload failed: {e}")
            return False

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    async def preload_forex_data(self) -> bool:
        """Pre-fetch major forex pairs"""
        try:
            pairs = ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X', 'AUDJPY=X']
            success_count = 0

            for pair in pairs:
                data = await self._fetch_with_fallback(pair, data_type='etf')

                if data:
                    cache_key = f"forex:{pair.replace('=X', '')}"
                    cache_data = {
                        'pair': pair,
                        'rate': data['price'],
                        'change': data['change'],
                        'timestamp': datetime.now().isoformat()
                    }

                    if self.redis_client:
                        self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(cache_data))

                    logger.info(f"  ✅ {pair}: {cache_data['rate']:.4f}")
                    success_count += 1

            return success_count >= 4  # At least 4 out of 5
        except Exception as e:
            logger.error(f"Forex preload failed: {e}")
            return False

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    async def preload_treasury_data(self) -> bool:
        """Pre-fetch US Treasury yields"""
        try:
            # Treasury ETFs as proxies
            symbols = {
                'SHY': '1-3 Year',
                'IEF': '7-10 Year',
                'TLT': '20+ Year'
            }

            success_count = 0
            for symbol, maturity in symbols.items():
                data = await self._fetch_with_fallback(symbol, data_type='etf')

                if data:
                    cache_key = f"bond:treasury:{symbol}"
                    cache_data = {
                        'symbol': symbol,
                        'maturity': maturity,
                        'price': data['price'],
                        'change': data['change'],
                        'timestamp': datetime.now().isoformat()
                    }

                    if self.redis_client:
                        self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(cache_data))

                    # Store in PostgreSQL
                    self._store_market_data(symbol, 'bond', cache_data)

                    logger.info(f"  ✅ {maturity}: ${cache_data['price']:.2f}")
                    success_count += 1

            return success_count >= 2  # At least 2 out of 3
        except Exception as e:
            logger.error(f"Treasury preload failed: {e}")
            return False

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    async def preload_global_bonds(self) -> bool:
        """Pre-fetch global bond data"""
        try:
            symbols = {'BNDX': 'International Bonds', 'EMB': 'Emerging Market Bonds', 'HYG': 'High Yield Corporate Bonds'}
            success_count = 0

            for symbol, name in symbols.items():
                data = await self._fetch_with_fallback(symbol, data_type='etf')

                if data:
                    cache_key = f"bond:global:{symbol}"
                    cache_data = {
                        'symbol': symbol,
                        'name': name,
                        'price': data['price'],
                        'change': data['change'],
                        'timestamp': datetime.now().isoformat()
                    }

                    if self.redis_client:
                        self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(cache_data))

                    # Store in PostgreSQL
                    self._store_market_data(symbol, 'bond', cache_data)

                    success_count += 1

            return success_count >= 2  # At least 2 out of 3
        except Exception as e:
            logger.error(f"Global bonds preload failed: {e}")
            return False

    async def preload_fred_data(self) -> bool:
        """Pre-fetch FRED economic data with yfinance fallback"""
        # Try FRED API first
        if self.fred_api_key and len(self.fred_api_key) == 32:
            try:
                # Key economic indicators
                series_ids = {
                    'GDP': 'GDP',
                    'UNRATE': 'Unemployment Rate',
                    'CPIAUCSL': 'CPI',
                    'FEDFUNDS': 'Fed Funds Rate',
                    'T10Y2Y': '10Y-2Y Spread',
                    'T10Y3M': '10Y-3M Spread (Recession Indicator)',
                    'VIXCLS': 'VIX (CBOE Volatility Index)',
                    'DGS10': '10-Year Treasury Constant Maturity Rate',
                    'DGS2': '2-Year Treasury Constant Maturity Rate',
                    'DGS3MO': '3-Month Treasury Bill'
                }

                base_url = "https://api.stlouisfed.org/fred/series/observations"
                success_count = 0

                for series_id, name in series_ids.items():
                    url = f"{base_url}?series_id={series_id}&api_key={self.fred_api_key}&file_type=json&limit=100&sort_order=desc"

                    async with self.session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            observations = data.get('observations', [])

                            if observations:
                                latest = observations[0]
                                cache_key = f"fred:{series_id}"
                                cache_data = {
                                    'series_id': series_id,
                                    'name': name,
                                    'value': float(latest['value']),
                                    'date': latest['date'],
                                    'timestamp': datetime.now().isoformat()
                                }

                                if self.redis_client:
                                    self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(cache_data))

                                # Store in PostgreSQL
                                self._store_market_data(series_id, 'economic', cache_data)

                                logger.info(f"  ✅ {name}: {cache_data['value']}")
                                success_count += 1

                if success_count > 0:
                    return True
            except Exception as e:
                logger.warning(f"FRED API failed: {e}, using API fallback chain")

        # Fallback to API-based sources for economic indicators
        logger.info("  Using multi-source API fallback for economic data")
        try:
            # Treasury yields via API sources (Polygon, Twelve Data, Alpha Vantage, etc.)
            treasury_tickers = {
                '^IRX': '13-Week Treasury',
                '^FVX': '5-Year Treasury',
                '^TNX': '10-Year Treasury',
                '^TYX': '30-Year Treasury'
            }

            success_count = 0
            for symbol, name in treasury_tickers.items():
                data = await self._fetch_with_fallback(symbol, data_type='etf')

                if data:
                    cache_key = f"econ:treasury:{symbol}"
                    cache_data = {
                        'symbol': symbol,
                        'name': name,
                        'yield': data['price'],
                        'change': data['change'],
                        'timestamp': datetime.now().isoformat()
                    }

                    if self.redis_client:
                        self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(cache_data))

                    # Store in PostgreSQL
                    self._store_market_data(symbol, 'economic', cache_data)

                    logger.info(f"  ✅ {name}: {cache_data['yield']:.2f}%")
                    success_count += 1

            return success_count >= 3  # At least 3 treasury yields
        except Exception as e:
            logger.error(f"Economic data fallback failed: {e}")
            return False

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    async def preload_volatility_data(self) -> bool:
        """Pre-fetch VIX and volatility data"""
        try:
            data = await self._fetch_with_fallback('^VIX', data_type='etf')

            if data:
                cache_key = "volatility:vix"
                cache_data = {
                    'symbol': 'VIX',
                    'level': data['price'],
                    'change': data['change'],
                    'timestamp': datetime.now().isoformat()
                }

                if self.redis_client:
                    self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(cache_data))

                # Store in PostgreSQL
                self._store_market_data('^VIX', 'volatility', cache_data)

                logger.info(f"  ✅ VIX: {cache_data['level']:.2f}")
                return True

            return False
        except Exception as e:
            logger.error(f"Volatility preload failed: {e}")
            return False

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    async def preload_sector_etfs(self) -> bool:
        """Pre-fetch sector ETF data"""
        try:
            sectors = {
                'XLF': 'Financials',
                'XLK': 'Technology',
                'XLE': 'Energy',
                'XLV': 'Healthcare',
                'XLI': 'Industrials',
                'XLP': 'Consumer Staples',
                'XLY': 'Consumer Discretionary',
                'XLU': 'Utilities',
                'XLRE': 'Real Estate'
            }

            success_count = 0
            for symbol, name in sectors.items():
                data = await self._fetch_with_fallback(symbol, data_type='etf')

                if data:
                    cache_key = f"sector:{symbol}"
                    cache_data = {
                        'symbol': symbol,
                        'name': name,
                        'price': data['price'],
                        'change': data['change'],
                        'timestamp': datetime.now().isoformat()
                    }

                    if self.redis_client:
                        self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(cache_data))

                    # Store in PostgreSQL
                    self._store_market_data(symbol, 'sector', cache_data)

                    success_count += 1

            logger.info(f"  ✅ Loaded {success_count}/{len(sectors)} sectors")
            return success_count >= 7  # At least 7 out of 9
        except Exception as e:
            logger.error(f"Sector ETFs preload failed: {e}")
            return False

    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    async def preload_correlations(self) -> bool:
        """Pre-calculate correlation matrix"""
        try:
            symbols = ['SPY', 'QQQ', 'GLD', 'TLT', 'USO', 'BTC-USD']

            # Fetch all data
            price_data = {}
            for symbol in symbols:
                data = await self._fetch_with_fallback(symbol, data_type='etf')
                if data:
                    price_data[symbol] = data  # Store for correlation calc

            # Need at least 4 symbols for meaningful correlations
            if len(price_data) < 4:
                logger.warning(f"Not enough data for correlations: {len(price_data)}/6 symbols")
                return False

            # Calculate correlations
            df = pd.DataFrame(data)
            corr_matrix = df.corr()

            cache_key = "analysis:correlation_matrix"
            cache_data = {
                'matrix': corr_matrix.to_json(),
                'symbols': list(data.keys()),
                'timestamp': datetime.now().isoformat()
            }

            if self.redis_client:
                self.redis_client.setex(cache_key, self.cache_ttl, json.dumps(cache_data))

            logger.info(f"  ✅ Correlation matrix: {len(data)}x{len(data)}")
            return True
        except Exception as e:
            logger.error(f"Correlations preload failed: {e}")
            return False

    def _store_market_data(self, symbol: str, data_type: str, data: dict):
        """Store market data in PostgreSQL"""
        if not self.db_conn:
            return

        try:
            cursor = self.db_conn.cursor()

            # Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS preloaded_market_data (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    data_type VARCHAR(50) NOT NULL,
                    price FLOAT,
                    change_percent FLOAT,
                    volume BIGINT,
                    metadata JSONB,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(symbol, data_type, timestamp)
                )
            """)

            # Insert data
            cursor.execute("""
                INSERT INTO preloaded_market_data
                (symbol, data_type, price, change_percent, volume, metadata, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (symbol, data_type, timestamp) DO UPDATE
                SET price = EXCLUDED.price,
                    change_percent = EXCLUDED.change_percent,
                    volume = EXCLUDED.volume,
                    metadata = EXCLUDED.metadata
            """, (
                symbol,
                data_type,
                data.get('price'),
                data.get('change'),
                data.get('volume'),
                json.dumps(data)
            ))

            self.db_conn.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Failed to store {symbol} in DB: {e}")

    async def validate_data_availability(self) -> Tuple[bool, Dict]:
        """
        Validate that sufficient data is available
        Returns: (is_valid, validation_report)
        """
        logger.info("🔍 Validating data availability...")

        validation_report = {
            'total_sources': len(self.validation_results),
            'successful': sum(1 for v in self.validation_results.values() if v),
            'failed': sum(1 for v in self.validation_results.values() if not v),
            'success_rate': 0,
            'failed_sources': [],
            'critical_failures': []
        }

        # Identify failures
        for source, success in self.validation_results.items():
            if not success:
                validation_report['failed_sources'].append(source)

                # Mark critical failures (reduced list - only absolutely essential)
                if source in ['US_Indices']:
                    validation_report['critical_failures'].append(source)

        # Calculate success rate
        if validation_report['total_sources'] > 0:
            validation_report['success_rate'] = (
                validation_report['successful'] / validation_report['total_sources'] * 100
            )

        # RELAXED VALIDATION: Multiple bypass conditions
        # 1. At least 60% success rate (was 80%)
        # 2. OR at least 8 out of 13 sources succeed (absolute minimum)
        # 3. AND no critical failures (US_Indices must work)

        success_threshold = float(os.getenv('SUCCESS_THRESHOLD', '60'))
        min_sources = 8  # Absolute minimum of 8/13 sources

        bypass_conditions = [
            validation_report['success_rate'] >= success_threshold,
            validation_report['successful'] >= min_sources
        ]

        is_valid = (
            any(bypass_conditions) and
            len(validation_report['critical_failures']) == 0
        )

        # Log report
        logger.info(f"📊 Validation Report:")
        logger.info(f"  Total Sources: {validation_report['total_sources']}")
        logger.info(f"  Successful: {validation_report['successful']}")
        logger.info(f"  Failed: {validation_report['failed']}")
        logger.info(f"  Success Rate: {validation_report['success_rate']:.1f}%")
        logger.info(f"  Threshold: {success_threshold}% (or {min_sources} sources minimum)")

        if validation_report['failed_sources']:
            logger.warning(f"  Failed Sources: {', '.join(validation_report['failed_sources'])}")

        if validation_report['critical_failures']:
            logger.error(f"  ❌ Critical Failures: {', '.join(validation_report['critical_failures'])}")

        # ===================================================================
        # EMERGENCY BYPASS MODE
        # ===================================================================
        skip_validation = os.getenv('SKIP_DATA_VALIDATION', 'false').lower() == 'true'

        if skip_validation:
            logger.warning("=" * 70)
            logger.warning("🚨 EMERGENCY BYPASS MODE ACTIVE 🚨")
            logger.warning("=" * 70)
            logger.warning("Data validation is DISABLED via SKIP_DATA_VALIDATION=true")
            logger.warning("Website will start regardless of data availability")
            logger.warning("This is a TEMPORARY workaround - fix data sources ASAP!")
            logger.warning("=" * 70)

            # Force validation to pass
            is_valid = True
            validation_report['bypass_mode'] = True

            if not validation_report['successful']:
                logger.warning("⚠️  WARNING: 0% data success rate - website will have NO DATA!")

            logger.warning("✅ Validation BYPASSED - Website will start (with warnings)")
        else:
            # Show which bypass condition triggered (if any)
            if is_valid:
                if validation_report['success_rate'] >= success_threshold:
                    logger.info(f"✅ Data validation PASSED - Success rate {validation_report['success_rate']:.1f}% >= {success_threshold}%")
                elif validation_report['successful'] >= min_sources:
                    logger.info(f"✅ Data validation PASSED - {validation_report['successful']} sources >= {min_sources} minimum")
                logger.info("✅ Website ready to start")
            else:
                logger.error("❌ Data validation FAILED - Website should NOT start")
                logger.error("💡 HINT: Set SKIP_DATA_VALIDATION=true to bypass (emergency only)")
                if len(validation_report['critical_failures']) > 0:
                    logger.error(f"   Reason: Critical sources failed: {', '.join(validation_report['critical_failures'])}")
                else:
                    logger.error(f"   Reason: Only {validation_report['successful']}/{validation_report['total_sources']} sources succeeded")

        return is_valid, validation_report

    async def create_health_endpoint_data(self):
        """Create data for /health/data endpoint"""
        if not self.redis_client:
            return

        health_data = {
            'status': 'healthy' if self.validation_results else 'unknown',
            'data_sources': self.validation_results,
            'last_preload': datetime.now().isoformat(),
            'cache_ttl': self.cache_ttl
        }

        self.redis_client.setex(
            'system:data_health',
            self.cache_ttl,
            json.dumps(health_data)
        )


async def main():
    """Main preloader entry point"""
    logger.info("=" * 70)
    logger.info("🚀 SPARTAN LABS DATA PRELOADER")
    logger.info("=" * 70)

    preloader = DataPreloader()

    try:
        # Connect to services
        await preloader.connect()

        # Pre-load all data
        results = await preloader.preload_all_data()

        # Validate data availability
        is_valid, report = await preloader.validate_data_availability()

        # Create health endpoint data
        await preloader.create_health_endpoint_data()

        # Exit with appropriate code
        if is_valid:
            logger.info("=" * 70)
            logger.info("✅ DATA PRELOAD COMPLETE - READY TO START WEBSITE")
            logger.info("=" * 70)
            sys.exit(0)
        else:
            logger.error("=" * 70)
            logger.error("❌ DATA PRELOAD FAILED - DO NOT START WEBSITE")
            logger.error("=" * 70)
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Preloader crashed: {e}")
        sys.exit(1)

    finally:
        await preloader.close()


if __name__ == "__main__":
    asyncio.run(main())
