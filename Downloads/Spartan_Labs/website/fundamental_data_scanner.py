#!/usr/bin/env python3
"""
FUNDAMENTAL DATA SCANNER
Fetches economic indicators, fundamentals, and sentiment data
"""

import os
import asyncio
import aiohttp
import redis
import psycopg2
from datetime import datetime
import json
import logging
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FRED Economic Indicators
FRED_INDICATORS = {
    # GDP and Growth
    'GDP': 'Gross Domestic Product',
    'GDPC1': 'Real GDP',
    'GDPPOT': 'Real Potential GDP',
    
    # Unemployment
    'UNRATE': 'Unemployment Rate',
    'U6RATE': 'U-6 Unemployment Rate',
    'CIVPART': 'Labor Force Participation Rate',
    
    # Inflation
    'CPIAUCSL': 'Consumer Price Index',
    'CPILFESL': 'Core CPI',
    'PCEPI': 'PCE Price Index',
    'PCEPILFE': 'Core PCE',
    
    # Interest Rates
    'FEDFUNDS': 'Federal Funds Rate',
    'DFF': 'Fed Funds Effective Rate',
    'DTB3': '3-Month Treasury',
    'DGS2': '2-Year Treasury',
    'DGS5': '5-Year Treasury',
    'DGS10': '10-Year Treasury',
    'DGS30': '30-Year Treasury',
    
    # Yield Curve
    'T10Y2Y': '10Y-2Y Treasury Spread',
    'T10Y3M': '10Y-3M Treasury Spread',
    
    # Money Supply
    'M1SL': 'M1 Money Supply',
    'M2SL': 'M2 Money Supply',
    'WALCL': 'Fed Balance Sheet',
    
    # Consumer Sentiment
    'UMCSENT': 'U Michigan Consumer Sentiment',
    'CSCICP03USM665S': 'Consumer Confidence',
    
    # Housing
    'HOUST': 'Housing Starts',
    'MORTGAGE30US': '30Y Mortgage Rate',
    
    # Manufacturing
    'INDPRO': 'Industrial Production',
    'NAPM': 'ISM Manufacturing PMI',
    
    # Trade
    'BOPGSTB': 'Trade Balance',
    
    # Corporate
    'BAA10Y': 'BBB Corp Spread',
    'BAMLH0A0HYM2': 'High Yield Spread',
}

class FundamentalDataScanner:
    """Scanner for fundamental and economic data"""
    
    def __init__(self):
        self.redis_client = None
        self.db_conn = None
        self.session = None
        self.fred_api_key = os.getenv('FRED_API_KEY')
        self.finnhub_api_key = os.getenv('FINNHUB_API_KEY')
        self.twelve_data_key = os.getenv('TWELVE_DATA_API_KEY')
        
    async def initialize(self):
        """Initialize connections"""
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            self.redis_client.ping()
            
            self.db_conn = psycopg2.connect(
                dbname=os.getenv('POSTGRES_DB', 'spartan_research_db'),
                user=os.getenv('POSTGRES_USER', 'spartan'),
                password=os.getenv('POSTGRES_PASSWORD', 'spartan'),
                host='localhost', port=5432
            )
            
            self.session = aiohttp.ClientSession()
            
            logger.info("✅ Fundamental scanner initialized")
            logger.info(f"   FRED API: {'✅' if self.fred_api_key else '❌'}")
            logger.info(f"   Finnhub: {'✅' if self.finnhub_api_key else '❌'}")
            logger.info(f"   Twelve Data: {'✅' if self.twelve_data_key else '❌'}")
            
            return True
        except Exception as e:
            logger.error(f"❌ Init failed: {e}")
            return False
    
    async def fetch_fred_indicator(self, series_id: str, name: str) -> Optional[Dict]:
        """Fetch single FRED indicator"""
        if not self.fred_api_key:
            return None
            
        try:
            url = f"https://api.stlouisfed.org/fred/series/observations"
            params = {
                'series_id': series_id,
                'api_key': self.fred_api_key,
                'file_type': 'json',
                'limit': 1,
                'sort_order': 'desc'
            }
            
            async with self.session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'observations' in data and len(data['observations']) > 0:
                        obs = data['observations'][0]
                        return {
                            'symbol': series_id,
                            'name': name,
                            'value': float(obs['value']),
                            'date': obs['date'],
                            'timestamp': datetime.now().isoformat(),
                            'source': 'fred',
                            'category': 'economic'
                        }
        except Exception as e:
            logger.debug(f"FRED error for {series_id}: {e}")
        
        return None
    
    async def fetch_finnhub_fundamentals(self, symbol: str) -> Optional[Dict]:
        """Fetch company fundamentals from Finnhub"""
        if not self.finnhub_api_key:
            return None
            
        try:
            url = f"https://finnhub.io/api/v1/stock/metric"
            params = {
                'symbol': symbol,
                'metric': 'all',
                'token': self.finnhub_api_key
            }
            
            async with self.session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'metric' in data:
                        metrics = data['metric']
                        return {
                            'symbol': symbol,
                            'pe_ratio': metrics.get('peNormalizedAnnual'),
                            'pb_ratio': metrics.get('pbAnnual'),
                            'roe': metrics.get('roeRfy'),
                            'eps': metrics.get('epsInclExtraItemsTTM'),
                            'dividend_yield': metrics.get('dividendYieldIndicatedAnnual'),
                            'market_cap': metrics.get('marketCapitalization'),
                            'beta': metrics.get('beta'),
                            'timestamp': datetime.now().isoformat(),
                            'source': 'finnhub',
                            'category': 'fundamentals'
                        }
        except Exception as e:
            logger.debug(f"Finnhub error for {symbol}: {e}")
        
        return None
    
    async def fetch_forex_rates(self) -> list:
        """Fetch major forex rates from Twelve Data"""
        if not self.twelve_data_key:
            return []
        
        pairs = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'USD/CAD', 'USD/CHF']
        results = []
        
        for pair in pairs:
            try:
                url = f"https://api.twelvedata.com/price"
                params = {
                    'symbol': pair,
                    'apikey': self.twelve_data_key
                }
                
                async with self.session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'price' in data:
                            results.append({
                                'symbol': pair.replace('/', ''),
                                'name': f'{pair} Exchange Rate',
                                'price': float(data['price']),
                                'timestamp': datetime.now().isoformat(),
                                'source': 'twelve_data',
                                'category': 'forex'
                            })
                
                await asyncio.sleep(8)  # Free tier rate limit
            except Exception as e:
                logger.debug(f"Forex error for {pair}: {e}")
        
        return results
    
    async def store_data(self, data: Dict):
        """Store fundamental data"""
        try:
            symbol = data.get('symbol', data.get('name', 'UNKNOWN'))
            category = data.get('category', 'fundamental')
            
            # Redis
            redis_key = f"fundamental:{category}:{symbol}"
            self.redis_client.setex(redis_key, 3600, json.dumps(data))  # 1 hour TTL
            
            # PostgreSQL
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO preloaded_market_data
                    (symbol, data_type, price, metadata, timestamp, source)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol, data_type, timestamp) DO UPDATE
                    SET price = EXCLUDED.price,
                        metadata = EXCLUDED.metadata,
                        source = EXCLUDED.source
                """, (
                    symbol,
                    category,
                    data.get('value') or data.get('price'),
                    json.dumps(data),
                    datetime.now(),
                    data['source']
                ))
                self.db_conn.commit()
            
            logger.debug(f"💾 Stored {category} data for {symbol}")
            
        except Exception as e:
            logger.error(f"❌ Store error: {e}")
    
    async def scan_all_fundamentals(self):
        """Scan all fundamental data sources"""
        logger.info("=" * 70)
        logger.info("📊 FUNDAMENTAL DATA SCAN STARTING")
        logger.info("=" * 70)
        
        total_success = 0
        
        # 1. FRED Economic Indicators
        if self.fred_api_key:
            logger.info(f"📈 Fetching {len(FRED_INDICATORS)} FRED indicators...")
            for series_id, name in FRED_INDICATORS.items():
                data = await self.fetch_fred_indicator(series_id, name)
                if data:
                    await self.store_data(data)
                    total_success += 1
                await asyncio.sleep(0.5)  # Rate limiting
        
        # 2. Forex Rates
        if self.twelve_data_key:
            logger.info("💱 Fetching forex rates...")
            forex_data = await self.fetch_forex_rates()
            for data in forex_data:
                await self.store_data(data)
                total_success += 1
        
        # 3. Major Stock Fundamentals (sample)
        if self.finnhub_api_key:
            logger.info("📊 Fetching stock fundamentals...")
            major_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
            for symbol in major_stocks:
                data = await self.fetch_finnhub_fundamentals(symbol)
                if data:
                    await self.store_data(data)
                    total_success += 1
                await asyncio.sleep(1)
        
        logger.info("=" * 70)
        logger.info(f"✅ FUNDAMENTAL SCAN COMPLETE")
        logger.info(f"   Indicators stored: {total_success}")
        logger.info("=" * 70)
    
    async def run_continuous(self):
        """Run continuous scanning every hour"""
        logger.info("🚀 Starting continuous fundamental scanning (1 hour interval)")
        
        while True:
            try:
                await self.scan_all_fundamentals()
                logger.info("⏰ Next scan in 1 hour")
                await asyncio.sleep(3600)  # 1 hour
            except Exception as e:
                logger.error(f"❌ Scan error: {e}")
                await asyncio.sleep(300)  # 5 min on error
    
    async def shutdown(self):
        """Cleanup"""
        if self.session:
            await self.session.close()
        if self.db_conn:
            self.db_conn.close()

async def main():
    scanner = FundamentalDataScanner()
    
    if not await scanner.initialize():
        return 1
    
    try:
        await scanner.run_continuous()
    except KeyboardInterrupt:
        logger.info("🛑 Stopped by user")
    finally:
        await scanner.shutdown()
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(asyncio.run(main()))
