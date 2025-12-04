#!/usr/bin/env python3
"""
Comprehensive Data Loader for Spartan Research Station
Loads ALL market data with real-time updates and proper visualization support
"""

import json
import yfinance as yf
import redis
import psycopg2
from datetime import datetime, timedelta
import logging
import os
from dotenv import load_dotenv
import requests
import asyncio
import aiohttp
from fredapi import Fred
import time

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveDataLoader:
    def __init__(self):
        # Redis connection
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

        # PostgreSQL connection (optional - we'll use Redis primarily)
        try:
            self.db_conn = psycopg2.connect(
                host='localhost',
                database='spartan_research_db',
                user='spartan',
                password='spartan'
            )
        except:
            # If DB not available, continue with Redis only
            self.db_conn = None
            logger.warning("PostgreSQL not available, using Redis only")

        # API Keys
        self.fred_key = os.getenv('FRED_API_KEY')
        self.polygon_key = os.getenv('POLYGON_IO_API_KEY')

        # Initialize FRED if key available
        self.fred = Fred(api_key=self.fred_key) if self.fred_key else None

    def fetch_market_indices(self):
        """Fetch major market indices"""
        indices = {
            'SPY': 'S&P 500',
            'QQQ': 'NASDAQ',
            'DIA': 'Dow Jones',
            'IWM': 'Russell 2000',
            '^VIX': 'VIX',
            '^DXY': 'Dollar Index',
            '^TNX': '10Y Treasury'
        }

        data = {}
        for symbol, name in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.history(period='5d')
                if not info.empty:
                    current = info['Close'].iloc[-1]
                    prev = info['Close'].iloc[-2] if len(info) > 1 else current
                    change = ((current - prev) / prev) * 100

                    data[symbol] = {
                        'name': name,
                        'price': round(current, 2),
                        'change': round(change, 2),
                        'timestamp': datetime.now().isoformat()
                    }

                    # Cache in Redis
                    self.redis_client.setex(
                        f'market:index:{symbol}',
                        900,  # 15 minutes
                        json.dumps(data[symbol])
                    )
                    logger.info(f"✅ {name}: ${current:.2f} ({change:+.2f}%)")
            except Exception as e:
                logger.error(f"❌ Failed to fetch {symbol}: {e}")

        return data

    def fetch_crypto_data(self):
        """Fetch cryptocurrency data"""
        cryptos = {
            'BTC-USD': 'Bitcoin',
            'ETH-USD': 'Ethereum',
            'SOL-USD': 'Solana',
            'BNB-USD': 'Binance Coin',
            'ADA-USD': 'Cardano'
        }

        data = {}
        for symbol, name in cryptos.items():
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.history(period='1d')
                if not info.empty:
                    price = info['Close'].iloc[-1]
                    volume = info['Volume'].iloc[-1]

                    # Get 24h change
                    info_24h = ticker.history(period='2d')
                    if len(info_24h) > 1:
                        prev_price = info_24h['Close'].iloc[-2]
                        change_24h = ((price - prev_price) / prev_price) * 100
                    else:
                        change_24h = 0

                    data[symbol] = {
                        'name': name,
                        'price': round(price, 2),
                        'change_24h': round(change_24h, 2),
                        'volume': int(volume),
                        'timestamp': datetime.now().isoformat()
                    }

                    # Cache in Redis
                    self.redis_client.setex(
                        f'crypto:{symbol}',
                        300,  # 5 minutes for crypto
                        json.dumps(data[symbol])
                    )
                    logger.info(f"✅ {name}: ${price:.2f} ({change_24h:+.2f}%)")
            except Exception as e:
                logger.error(f"❌ Failed to fetch {symbol}: {e}")

        return data

    def fetch_commodities(self):
        """Fetch commodity data"""
        commodities = {
            'GLD': 'Gold',
            'SLV': 'Silver',
            'USO': 'Oil',
            'UNG': 'Natural Gas',
            'CPER': 'Copper',
            'CORN': 'Corn',
            'WEAT': 'Wheat'
        }

        data = {}
        for symbol, name in commodities.items():
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.history(period='5d')
                if not info.empty:
                    current = info['Close'].iloc[-1]
                    prev = info['Close'].iloc[-2] if len(info) > 1 else current
                    change = ((current - prev) / prev) * 100

                    data[symbol] = {
                        'name': name,
                        'price': round(current, 2),
                        'change': round(change, 2),
                        'timestamp': datetime.now().isoformat()
                    }

                    # Cache in Redis
                    self.redis_client.setex(
                        f'commodity:{symbol}',
                        900,
                        json.dumps(data[symbol])
                    )
                    logger.info(f"✅ {name}: ${current:.2f} ({change:+.2f}%)")
            except Exception as e:
                logger.error(f"❌ Failed to fetch {symbol}: {e}")

        return data

    def fetch_economic_data(self):
        """Fetch FRED economic data"""
        if not self.fred:
            logger.warning("⚠️ FRED API key not configured")
            return {}

        indicators = {
            'GDP': 'GDP Growth',
            'UNRATE': 'Unemployment Rate',
            'CPIAUCSL': 'CPI Inflation',
            'FEDFUNDS': 'Fed Funds Rate',
            'T10Y2Y': '10Y-2Y Spread',
            'DEXUSEU': 'EUR/USD',
            'DEXJPUS': 'USD/JPY',
            'DGS10': '10Y Treasury Yield'
        }

        data = {}
        for series, name in indicators.items():
            try:
                value = self.fred.get_series(series, limit=2)
                if not value.empty:
                    current = value.iloc[-1]
                    prev = value.iloc[-2] if len(value) > 1 else current
                    change = current - prev

                    data[series] = {
                        'name': name,
                        'value': round(current, 2),
                        'change': round(change, 2),
                        'timestamp': datetime.now().isoformat()
                    }

                    # Cache in Redis
                    self.redis_client.setex(
                        f'fred:{series}',
                        3600,  # 1 hour for economic data
                        json.dumps(data[series])
                    )
                    logger.info(f"✅ {name}: {current:.2f} ({change:+.2f})")
            except Exception as e:
                logger.error(f"❌ Failed to fetch {series}: {e}")

        return data

    def fetch_sectors(self):
        """Fetch sector ETF data"""
        sectors = {
            'XLF': 'Financials',
            'XLK': 'Technology',
            'XLE': 'Energy',
            'XLV': 'Healthcare',
            'XLI': 'Industrials',
            'XLP': 'Consumer Staples',
            'XLY': 'Consumer Discretionary',
            'XLU': 'Utilities',
            'XLRE': 'Real Estate',
            'XLB': 'Materials',
            'XLC': 'Communication'
        }

        data = {}
        for symbol, name in sectors.items():
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.history(period='5d')
                if not info.empty:
                    current = info['Close'].iloc[-1]
                    prev = info['Close'].iloc[-2] if len(info) > 1 else current
                    change = ((current - prev) / prev) * 100

                    # Get 5-day performance
                    start_price = info['Close'].iloc[0]
                    change_5d = ((current - start_price) / start_price) * 100

                    data[symbol] = {
                        'name': name,
                        'price': round(current, 2),
                        'change': round(change, 2),
                        'change_5d': round(change_5d, 2),
                        'timestamp': datetime.now().isoformat()
                    }

                    # Cache in Redis
                    self.redis_client.setex(
                        f'sector:{symbol}',
                        900,
                        json.dumps(data[symbol])
                    )
                    logger.info(f"✅ {name}: ${current:.2f} ({change:+.2f}%)")
            except Exception as e:
                logger.error(f"❌ Failed to fetch {symbol}: {e}")

        return data

    def generate_visualization_data(self):
        """Generate data for Mermaid-like visualizations"""
        viz_data = {
            'market_flow': {
                'risk_on': [],
                'risk_off': [],
                'neutral': []
            },
            'sector_rotation': {},
            'correlation_matrix': {},
            'economic_cycle': {}
        }

        # Categorize assets by risk sentiment
        try:
            # Risk-on assets
            for symbol in ['QQQ', 'XLK', 'XLY', 'BTC-USD', 'ETH-USD']:
                key = f'market:index:{symbol}' if symbol in ['QQQ'] else f'crypto:{symbol}' if 'USD' in symbol else f'sector:{symbol}'
                data = self.redis_client.get(key)
                if data:
                    asset = json.loads(data)
                    if asset.get('change', 0) > 0:
                        viz_data['market_flow']['risk_on'].append({
                            'name': symbol,
                            'value': asset.get('change', 0)
                        })

            # Risk-off assets
            for symbol in ['^VIX', 'GLD', 'XLP', 'XLU']:
                key = f'market:index:{symbol}' if '^' in symbol else f'commodity:{symbol}' if symbol == 'GLD' else f'sector:{symbol}'
                data = self.redis_client.get(key)
                if data:
                    asset = json.loads(data)
                    if asset.get('change', 0) > 0:
                        viz_data['market_flow']['risk_off'].append({
                            'name': symbol,
                            'value': asset.get('change', 0)
                        })

        except Exception as e:
            logger.error(f"Error generating visualization data: {e}")

        # Save visualization data
        self.redis_client.setex(
            'visualization:market_flow',
            900,
            json.dumps(viz_data)
        )

        return viz_data

    def run_complete_load(self):
        """Run complete data load"""
        logger.info("="*60)
        logger.info("🚀 STARTING COMPREHENSIVE DATA LOAD")
        logger.info("="*60)

        # Load all data types
        results = {
            'indices': self.fetch_market_indices(),
            'crypto': self.fetch_crypto_data(),
            'commodities': self.fetch_commodities(),
            'sectors': self.fetch_sectors(),
            'economic': self.fetch_economic_data(),
            'visualizations': self.generate_visualization_data()
        }

        # Store summary in Redis
        summary = {
            'last_update': datetime.now().isoformat(),
            'total_symbols': sum(len(v) for v in results.values() if isinstance(v, dict)),
            'status': 'active'
        }
        self.redis_client.setex(
            'data:summary',
            900,
            json.dumps(summary)
        )

        logger.info("="*60)
        logger.info(f"✅ DATA LOAD COMPLETE - {summary['total_symbols']} symbols loaded")
        logger.info("="*60)

        return results

if __name__ == "__main__":
    loader = ComprehensiveDataLoader()

    # Initial load
    loader.run_complete_load()

    # Keep running and refresh every 5 minutes
    while True:
        time.sleep(300)  # 5 minutes
        logger.info("🔄 Refreshing data...")
        loader.run_complete_load()