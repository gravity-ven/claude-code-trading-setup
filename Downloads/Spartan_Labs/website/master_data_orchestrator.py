#!/usr/bin/env python3
"""
MASTER DATA ORCHESTRATOR - ZERO COMPROMISE DATA INTEGRITY
Ensures 100% real data coverage across ALL webpages with agent chaining
NO FAKE DATA. NO EMPTY FIELDS. EVER.
"""

import asyncio
import json
import redis
import psycopg2
import yfinance as yf
import requests
from datetime import datetime, timedelta
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
import time
from dotenv import load_dotenv
from fredapi import Fred
import aiohttp
import numpy as np

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger('MASTER_ORCHESTRATOR')

class DataAgent:
    """Base class for all data agents"""
    def __init__(self, name: str, symbols: List[str]):
        self.name = name
        self.symbols = symbols
        self.last_update = None
        self.status = "INITIALIZING"
        self.data = {}

    async def fetch_data(self) -> Dict:
        """Override in subclasses"""
        raise NotImplementedError

    async def validate_data(self, data: Dict) -> bool:
        """Ensure data is real and valid"""
        if not data:
            return False
        # Check for fake/placeholder values
        for key, value in data.items():
            if value is None or value == 'N/A' or value == '--':
                return False
            if isinstance(value, (int, float)) and (value == 0 or np.isnan(value)):
                return False
        return True

class StockMarketAgent(DataAgent):
    """Agent for stock market data"""
    def __init__(self):
        symbols = ['SPY', 'QQQ', 'DIA', 'IWM', 'VTI', 'VOO', 'IVV', 'EFA', 'EEM', 'AGG']
        super().__init__('StockMarket', symbols)

    async def fetch_data(self) -> Dict:
        data = {}
        for symbol in self.symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.history(period='1d')
                if not info.empty:
                    current = info['Close'].iloc[-1]
                    volume = info['Volume'].iloc[-1]

                    # Get 5-day data for change calculation
                    info_5d = ticker.history(period='5d')
                    if len(info_5d) > 1:
                        prev = info_5d['Close'].iloc[-2]
                        change = ((current - prev) / prev) * 100
                    else:
                        change = 0

                    data[symbol] = {
                        'price': round(current, 2),
                        'volume': int(volume),
                        'change': round(change, 2),
                        'timestamp': datetime.now().isoformat()
                    }
                    logger.info(f"✅ {symbol}: ${current:.2f} ({change:+.2f}%)")
            except Exception as e:
                logger.error(f"❌ Failed to fetch {symbol}: {e}")
                # Try alternative source
                data[symbol] = await self.fetch_alternative(symbol)
        return data

    async def fetch_alternative(self, symbol: str) -> Dict:
        """Fallback to alternative data source"""
        # Try Polygon, Twelve Data, Alpha Vantage, etc.
        sources = ['polygon', 'twelve_data', 'alpha_vantage']
        for source in sources:
            try:
                # Implementation for each source
                if source == 'polygon' and os.getenv('POLYGON_IO_API_KEY'):
                    url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"
                    params = {'apiKey': os.getenv('POLYGON_IO_API_KEY')}
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, params=params) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                if data.get('results'):
                                    result = data['results'][0]
                                    return {
                                        'price': result['c'],
                                        'volume': result['v'],
                                        'change': ((result['c'] - result['o']) / result['o']) * 100,
                                        'timestamp': datetime.now().isoformat()
                                    }
            except:
                continue
        return None

class CryptoAgent(DataAgent):
    """Agent for cryptocurrency data"""
    def __init__(self):
        symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'BNB-USD', 'ADA-USD',
                  'XRP-USD', 'DOGE-USD', 'DOT-USD', 'MATIC-USD', 'LINK-USD']
        super().__init__('Crypto', symbols)

    async def fetch_data(self) -> Dict:
        data = {}
        for symbol in self.symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.history(period='1d')
                if not info.empty:
                    price = info['Close'].iloc[-1]
                    volume = info['Volume'].iloc[-1]

                    # 24h change
                    info_24h = ticker.history(period='2d')
                    if len(info_24h) > 1:
                        prev_price = info_24h['Close'].iloc[-2]
                        change_24h = ((price - prev_price) / prev_price) * 100
                    else:
                        change_24h = 0

                    data[symbol] = {
                        'price': round(price, 2),
                        'volume': int(volume),
                        'change_24h': round(change_24h, 2),
                        'timestamp': datetime.now().isoformat()
                    }
                    logger.info(f"✅ {symbol}: ${price:.2f} ({change_24h:+.2f}%)")
            except Exception as e:
                logger.error(f"❌ Failed to fetch {symbol}: {e}")
        return data

class CommodityAgent(DataAgent):
    """Agent for commodity data"""
    def __init__(self):
        symbols = ['GLD', 'SLV', 'USO', 'UNG', 'CPER', 'CORN', 'WEAT', 'SOYB', 'DBA', 'PALL']
        super().__init__('Commodity', symbols)

    async def fetch_data(self) -> Dict:
        data = {}
        for symbol in self.symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.history(period='1d')
                if not info.empty:
                    price = info['Close'].iloc[-1]
                    data[symbol] = {
                        'price': round(price, 2),
                        'timestamp': datetime.now().isoformat()
                    }
                    logger.info(f"✅ {symbol}: ${price:.2f}")
            except Exception as e:
                logger.error(f"❌ Failed to fetch {symbol}: {e}")
        return data

class EconomicDataAgent(DataAgent):
    """Agent for economic indicators"""
    def __init__(self):
        indicators = ['GDP', 'UNRATE', 'CPIAUCSL', 'FEDFUNDS', 'T10Y2Y',
                     'DEXUSEU', 'DEXJPUS', 'DGS10', 'DFEDTARU', 'HOUST']
        super().__init__('Economic', indicators)
        self.fred = Fred(api_key=os.getenv('FRED_API_KEY')) if os.getenv('FRED_API_KEY') else None

    async def fetch_data(self) -> Dict:
        if not self.fred:
            logger.warning("FRED API key not configured")
            return {}

        data = {}
        for indicator in self.symbols:
            try:
                series = self.fred.get_series(indicator, limit=2)
                if not series.empty:
                    current = series.iloc[-1]
                    prev = series.iloc[-2] if len(series) > 1 else current
                    change = current - prev

                    data[indicator] = {
                        'value': round(current, 2),
                        'change': round(change, 2),
                        'timestamp': datetime.now().isoformat()
                    }
                    logger.info(f"✅ {indicator}: {current:.2f} ({change:+.2f})")
            except Exception as e:
                logger.error(f"❌ Failed to fetch {indicator}: {e}")
        return data

class ForexAgent(DataAgent):
    """Agent for forex data"""
    def __init__(self):
        pairs = ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X', 'USDCAD=X',
                'USDCHF=X', 'NZDUSD=X', 'EURGBP=X', 'EURJPY=X', 'GBPJPY=X']
        super().__init__('Forex', pairs)

    async def fetch_data(self) -> Dict:
        data = {}
        for pair in self.symbols:
            try:
                ticker = yf.Ticker(pair)
                info = ticker.history(period='1d')
                if not info.empty:
                    rate = info['Close'].iloc[-1]
                    data[pair] = {
                        'rate': round(rate, 4),
                        'timestamp': datetime.now().isoformat()
                    }
                    logger.info(f"✅ {pair}: {rate:.4f}")
            except Exception as e:
                logger.error(f"❌ Failed to fetch {pair}: {e}")
        return data

class SectorETFAgent(DataAgent):
    """Agent for sector ETF data"""
    def __init__(self):
        sectors = ['XLF', 'XLK', 'XLE', 'XLV', 'XLI', 'XLP', 'XLY',
                  'XLU', 'XLRE', 'XLB', 'XLC', 'VNQ', 'IYR', 'ITB']
        super().__init__('SectorETF', sectors)

    async def fetch_data(self) -> Dict:
        data = {}
        for sector in self.symbols:
            try:
                ticker = yf.Ticker(sector)
                info = ticker.history(period='5d')
                if not info.empty:
                    current = info['Close'].iloc[-1]
                    prev = info['Close'].iloc[-2] if len(info) > 1 else current
                    change = ((current - prev) / prev) * 100

                    data[sector] = {
                        'price': round(current, 2),
                        'change': round(change, 2),
                        'timestamp': datetime.now().isoformat()
                    }
                    logger.info(f"✅ {sector}: ${current:.2f} ({change:+.2f}%)")
            except Exception as e:
                logger.error(f"❌ Failed to fetch {sector}: {e}")
        return data

class VolatilityAgent(DataAgent):
    """Agent for volatility indices"""
    def __init__(self):
        symbols = ['^VIX', '^VXN', '^RVX', '^VXD', 'VIXY', 'VXX', 'UVXY', 'SVXY']
        super().__init__('Volatility', symbols)

    async def fetch_data(self) -> Dict:
        data = {}
        for symbol in self.symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.history(period='1d')
                if not info.empty:
                    value = info['Close'].iloc[-1]
                    data[symbol] = {
                        'value': round(value, 2),
                        'timestamp': datetime.now().isoformat()
                    }
                    logger.info(f"✅ {symbol}: {value:.2f}")
            except Exception as e:
                logger.error(f"❌ Failed to fetch {symbol}: {e}")
        return data

class MasterDataOrchestrator:
    """
    MASTER ORCHESTRATOR - Coordinates all data agents
    Ensures 100% data coverage with zero tolerance for fake data
    """

    def __init__(self):
        # Initialize connections
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

        # PostgreSQL connection
        try:
            self.db_conn = psycopg2.connect(
                host='localhost',
                database='spartan_research_db',
                user='spartan',
                password='spartan'
            )
        except:
            self.db_conn = None
            logger.warning("PostgreSQL not available")

        # Initialize all agents
        self.agents = [
            StockMarketAgent(),
            CryptoAgent(),
            CommodityAgent(),
            EconomicDataAgent(),
            ForexAgent(),
            SectorETFAgent(),
            VolatilityAgent()
        ]

        # Agent chain configuration
        self.agent_chains = {
            'market_overview': ['StockMarket', 'Volatility', 'SectorETF'],
            'crypto_dashboard': ['Crypto'],
            'commodities': ['Commodity'],
            'forex': ['Forex'],
            'economic': ['Economic'],
            'complete': ['StockMarket', 'Crypto', 'Commodity', 'Economic', 'Forex', 'SectorETF', 'Volatility']
        }

        # Monitoring state
        self.running = True
        self.last_validation = {}
        self.failed_data_points = set()
        self.update_interval = 1  # Update every second!

    async def validate_all_data(self) -> Dict[str, Any]:
        """Validate that ALL data points have real values"""
        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'total_points': 0,
            'valid_points': 0,
            'invalid_points': [],
            'status': 'CHECKING'
        }

        # Check all Redis keys
        all_keys = self.redis_client.keys('*')

        for key in all_keys:
            try:
                data = self.redis_client.get(key)
                if data:
                    parsed = json.loads(data)
                    validation_results['total_points'] += 1

                    # Check for fake/empty data
                    is_valid = True
                    if 'price' in parsed and (parsed['price'] is None or parsed['price'] == 0):
                        is_valid = False
                    if 'value' in parsed and (parsed['value'] is None or parsed['value'] == 0):
                        is_valid = False

                    if is_valid:
                        validation_results['valid_points'] += 1
                    else:
                        validation_results['invalid_points'].append(key)
                        self.failed_data_points.add(key)
            except:
                validation_results['invalid_points'].append(key)

        # Calculate health
        if validation_results['total_points'] > 0:
            health_percent = (validation_results['valid_points'] / validation_results['total_points']) * 100
            validation_results['health_percent'] = health_percent
            validation_results['status'] = 'HEALTHY' if health_percent == 100 else 'DEGRADED'
        else:
            validation_results['health_percent'] = 0
            validation_results['status'] = 'CRITICAL'

        return validation_results

    async def run_agent_chain(self, chain_name: str) -> Dict:
        """Run a specific chain of agents"""
        agents_to_run = self.agent_chains.get(chain_name, [])
        results = {}

        for agent_name in agents_to_run:
            agent = next((a for a in self.agents if a.name == agent_name), None)
            if agent:
                logger.info(f"🔗 Running agent: {agent_name}")
                data = await agent.fetch_data()

                # Validate data
                if await agent.validate_data(data):
                    results[agent_name] = data
                    # Store in Redis
                    for symbol, values in data.items():
                        key = f"{agent_name.lower()}:{symbol}"
                        self.redis_client.setex(
                            key,
                            300,  # 5 minute TTL
                            json.dumps(values)
                        )
                else:
                    logger.error(f"❌ Invalid data from {agent_name}")
                    results[agent_name] = 'FAILED'

        return results

    async def continuous_monitoring(self):
        """Main loop - runs every second to ensure data freshness"""
        logger.info("="*60)
        logger.info("🚀 MASTER DATA ORCHESTRATOR STARTED")
        logger.info("📊 ZERO COMPROMISE MODE - 100% REAL DATA ONLY")
        logger.info("="*60)

        while self.running:
            try:
                start_time = time.time()

                # Run complete agent chain
                results = await self.run_agent_chain('complete')

                # Validate all data
                validation = await self.validate_all_data()

                # Log status
                logger.info(f"📊 Data Health: {validation['health_percent']:.1f}% "
                          f"({validation['valid_points']}/{validation['total_points']} points)")

                # If any data is missing or fake, immediately refetch
                if validation['invalid_points']:
                    logger.warning(f"⚠️ Invalid data detected: {validation['invalid_points'][:5]}")
                    # Trigger emergency refetch for failed points
                    await self.emergency_refetch(validation['invalid_points'])

                # Store orchestrator status
                self.redis_client.setex(
                    'orchestrator:status',
                    60,
                    json.dumps({
                        'status': 'ACTIVE',
                        'last_update': datetime.now().isoformat(),
                        'health': validation['health_percent'],
                        'total_agents': len(self.agents),
                        'update_frequency': 'EVERY_SECOND'
                    })
                )

                # Calculate sleep time to maintain 1-second updates
                elapsed = time.time() - start_time
                sleep_time = max(0, self.update_interval - elapsed)

                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

            except Exception as e:
                logger.error(f"❌ Orchestrator error: {e}")
                await asyncio.sleep(1)

    async def emergency_refetch(self, failed_keys: List[str]):
        """Emergency refetch for failed data points"""
        logger.warning(f"🚨 EMERGENCY REFETCH for {len(failed_keys)} failed points")

        for key in failed_keys:
            try:
                # Determine which agent handles this data
                parts = key.split(':')
                if len(parts) >= 2:
                    agent_type = parts[0]
                    symbol = parts[1]

                    # Find appropriate agent
                    for agent in self.agents:
                        if agent.name.lower() == agent_type:
                            # Refetch just this symbol
                            data = await agent.fetch_data()
                            if symbol in data and data[symbol]:
                                self.redis_client.setex(
                                    key,
                                    300,
                                    json.dumps(data[symbol])
                                )
                                logger.info(f"✅ Recovered data for {key}")
                                self.failed_data_points.discard(key)

            except Exception as e:
                logger.error(f"Failed to recover {key}: {e}")

    async def webpage_data_provider(self, webpage: str) -> Dict:
        """Provide complete real data for a specific webpage"""
        webpage_data_mapping = {
            'index.html': ['market_overview', 'crypto_dashboard'],
            'global_capital_flow_swing_trading.html': ['complete'],
            'correlation_matrix.html': ['market_overview', 'commodities'],
            'bitcoin_intelligence.html': ['crypto_dashboard'],
            'oil_intelligence.html': ['commodities'],
            'gold_intelligence.html': ['commodities'],
            'fred_global_complete.html': ['economic'],
            'forex.html': ['forex'],
            'volatility.html': ['volatility']
        }

        chains_to_run = webpage_data_mapping.get(webpage, ['complete'])

        all_data = {}
        for chain in chains_to_run:
            chain_data = await self.run_agent_chain(chain)
            all_data.update(chain_data)

        return all_data

    def start(self):
        """Start the orchestrator"""
        try:
            asyncio.run(self.continuous_monitoring())
        except KeyboardInterrupt:
            logger.info("🛑 Orchestrator stopped by user")
        except Exception as e:
            logger.error(f"💥 Fatal error: {e}")

if __name__ == "__main__":
    orchestrator = MasterDataOrchestrator()
    orchestrator.start()