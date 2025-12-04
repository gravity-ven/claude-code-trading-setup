#!/usr/bin/env python3
"""
COMPREHENSIVE MACRO & MARKET DATA SCANNER
Fetches ALL macro economic data + website requirements (70-75 data points)
"""

import os
import asyncio
import aiohttp
import redis
import psycopg2
from datetime import datetime
import json
import logging
from typing import Dict, Optional, List
from dotenv import load_dotenv
import time

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# COMPREHENSIVE FRED ECONOMIC INDICATORS (100+ indicators)
# ============================================================================

FRED_INDICATORS = {
    # ========================================================================
    # GDP & ECONOMIC GROWTH
    # ========================================================================
    'GDP': 'Gross Domestic Product',
    'GDPC1': 'Real GDP',
    'GDPPOT': 'Real Potential GDP',
    'GDPCA': 'Real GDP Per Capita',
    'A191RL1Q225SBEA': 'Real GDP Growth Rate',

    # ========================================================================
    # EMPLOYMENT & LABOR MARKET
    # ========================================================================
    'UNRATE': 'Unemployment Rate',
    'U6RATE': 'U-6 Total Unemployment Rate',
    'CIVPART': 'Labor Force Participation Rate',
    'EMRATIO': 'Employment-Population Ratio',
    'PAYEMS': 'Total Nonfarm Payrolls',
    'MANEMP': 'Manufacturing Employment',
    'USCONS': 'Construction Employment',
    'USTRADE': 'Retail Trade Employment',
    'USEHS': 'Education & Health Services Employment',
    'USFIRE': 'Financial Activities Employment',
    'USPBS': 'Professional & Business Services Employment',
    'USSERV': 'Service-Providing Employment',
    'ICSA': 'Initial Jobless Claims',
    'CCSA': 'Continued Jobless Claims',
    'JTSJOL': 'Job Openings (JOLTS)',
    'JTSQUL': 'Quits Rate (JOLTS)',
    'AWHMAN': 'Average Weekly Hours (Manufacturing)',
    'CES0500000003': 'Average Hourly Earnings',

    # ========================================================================
    # INFLATION & PRICES
    # ========================================================================
    'CPIAUCSL': 'Consumer Price Index (All Items)',
    'CPILFESL': 'Core CPI (Ex Food & Energy)',
    'CPIENGSL': 'CPI: Energy',
    'CPIUFDSL': 'CPI: Food',
    'CUSR0000SEHC': 'CPI: Housing',
    'CUSR0000SAM': 'CPI: Medical Care',
    'PCEPI': 'PCE Price Index',
    'PCEPILFE': 'Core PCE (Fed\'s Preferred)',
    'PPIFIS': 'Producer Price Index',
    'PPIACO': 'PPI: All Commodities',
    'WPSFD49207': 'PPI: Finished Goods',
    'GASREGCOVW': 'Gas Prices (Regular)',
    'APU0000708111': 'Electricity Prices',
    'CUSR0000SAH1': 'CPI: Shelter',
    'CUUR0000SEHA': 'CPI: Rent',

    # ========================================================================
    # INTEREST RATES & MONETARY POLICY
    # ========================================================================
    'FEDFUNDS': 'Federal Funds Rate',
    'DFF': 'Federal Funds Effective Rate',
    'DFEDTARU': 'Federal Funds Target Range - Upper Limit',
    'DFEDTARL': 'Federal Funds Target Range - Lower Limit',
    'DTB3': '3-Month Treasury Bill',
    'DTB6': '6-Month Treasury Bill',
    'DGS1': '1-Year Treasury',
    'DGS2': '2-Year Treasury',
    'DGS3': '3-Year Treasury',
    'DGS5': '5-Year Treasury',
    'DGS7': '7-Year Treasury',
    'DGS10': '10-Year Treasury',
    'DGS20': '20-Year Treasury',
    'DGS30': '30-Year Treasury',
    'T10Y2Y': '10Y-2Y Treasury Spread',
    'T10Y3M': '10Y-3M Treasury Spread',
    'T10YIE': '10-Year Breakeven Inflation Rate',
    'T5YIE': '5-Year Breakeven Inflation Rate',
    'MORTGAGE30US': '30-Year Mortgage Rate',
    'MORTGAGE15US': '15-Year Mortgage Rate',

    # ========================================================================
    # MONEY SUPPLY & CREDIT
    # ========================================================================
    'M1SL': 'M1 Money Stock',
    'M2SL': 'M2 Money Stock',
    'MABMM301USM189S': 'M3 Money Stock',
    'TOTRESNS': 'Total Bank Reserves',
    'EXCSRESNW': 'Excess Bank Reserves',
    'WALCL': 'Fed Balance Sheet (Total Assets)',
    'WSHOMCB': 'Mortgage-Backed Securities Held by Fed',
    'TREAST': 'Treasury Securities Held by Fed',
    'TOTLL': 'Total Consumer Credit Outstanding',
    'REVOLSL': 'Revolving Consumer Credit',
    'BUSLOANS': 'Commercial & Industrial Loans',
    'DRBLACBS': 'Bank Credit',

    # ========================================================================
    # CONSUMER & HOUSING
    # ========================================================================
    'UMCSENT': 'U Michigan Consumer Sentiment',
    'CSCICP03USM665S': 'Consumer Confidence Index',
    'DPCERAM1M225NBEA': 'Personal Consumption Expenditures',
    'PCE': 'Personal Consumption Expenditures',
    'PSAVERT': 'Personal Saving Rate',
    'HOUST': 'Housing Starts',
    'HOUST1F': 'Housing Starts: Single-Family',
    'HOUSTNSA': 'Housing Starts (Not Seasonally Adjusted)',
    'PERMIT': 'New Private Housing Permits',
    'HNGSUPCS': 'New Houses for Sale',
    'MSACSR': 'Monthly Supply of Houses',
    'MSPUS': 'Median Sales Price of Houses',
    'USSTHPI': 'Housing Price Index',
    'ETOTALUSQ176N': 'Home Equity Extraction',
    'COMPUTSA': 'Housing Completions',

    # ========================================================================
    # MANUFACTURING & PRODUCTION
    # ========================================================================
    'INDPRO': 'Industrial Production Index',
    'IPMANSICS': 'Industrial Production: Manufacturing',
    'IPB50001N': 'Industrial Production: Mining',
    'IPG': 'Industrial Production: Utilities',
    'CAPUTLG2111S': 'Capacity Utilization',
    'TCU': 'Capacity Utilization Rate',
    'NAPM': 'ISM Manufacturing PMI',
    'NAPMNOI': 'ISM Manufacturing: New Orders',
    'NAPMPI': 'ISM Manufacturing: Prices',
    'NAPMEI': 'ISM Manufacturing: Employment',
    'NAPMSDI': 'ISM Manufacturing: Supplier Deliveries',
    'NAPM NPI': 'ISM Non-Manufacturing PMI',
    'GACDISA066MSFRBCHI': 'Chicago Fed National Activity Index',
    'NEWORDER': 'Manufacturers\' New Orders',
    'AMTMNO': 'Manufacturers\' New Orders: Durable Goods',

    # ========================================================================
    # RETAIL & TRADE
    # ========================================================================
    'RSXFS': 'Retail Sales',
    'MRTSSM44X72USS': 'Retail Sales: Total',
    'RSAFS': 'Retail Sales: Food Services',
    'RSGMS': 'Retail Sales: General Merchandise',
    'RSSGHBMS': 'Retail Sales: Gasoline Stations',
    'BOPGSTB': 'Trade Balance',
    'BOPGTB': 'Trade Balance: Goods',
    'BOPGTKB': 'Trade Balance: Services',
    'NETEXP': 'Net Exports',
    'EXPGS': 'Exports of Goods & Services',
    'IMPGS': 'Imports of Goods & Services',

    # ========================================================================
    # CORPORATE & CREDIT MARKETS
    # ========================================================================
    'BAA10Y': 'BBB Corporate Bond Spread',
    'BAMLH0A0HYM2': 'High Yield Bond Spread',
    'BAMLC0A4CBBB': 'BBB Corporate Bond OAS',
    'BAMLC0A1CAAAEY': 'AAA Corporate Bond Yield',
    'BOGZ1FL893064105Q': 'Nonfinancial Corporate Business Debt',
    'NCBDBIQ027S': 'Household Debt',
    'TDSP': 'Total Debt Securities',
    'COMPOUT': 'Commercial Paper Outstanding',

    # ========================================================================
    # GOVERNMENT & FISCAL
    # ========================================================================
    'GFDEBTN': 'Federal Debt: Total Public Debt',
    'GFDGDPA188S': 'Federal Debt as % of GDP',
    'FYFSD': 'Federal Surplus or Deficit',
    'FYONGDA188S': 'Federal Net Outlays as % of GDP',
    'FGRECPT': 'Federal Government Tax Receipts',
    'FGEXPND': 'Federal Government Expenditures',
    'MTSDS133FMS': 'Federal Debt Held by Public',
    'GFDEBTN_FYGFDPUN': 'Federal Debt Held by Foreign & International',

    # ========================================================================
    # LEADING & COMPOSITE INDICATORS
    # ========================================================================
    'USSLIND': 'Leading Economic Indicators Index',
    'CSINFT03USM661S': 'Conference Board Leading Indicators',
    'DCOILWTICO': 'WTI Crude Oil Price',
    'DCOILBRENTEU': 'Brent Crude Oil Price',
    'DEXUSEU': 'US / Euro Exchange Rate',
    'DEXUSUK': 'US / UK Exchange Rate',
    'DEXJPUS': 'Japan / US Exchange Rate',
    'DEXCHUS': 'China / US Exchange Rate',
    'VIXCLS': 'CBOE Volatility Index (VIX)',
    'WILL5000IND': 'Wilshire 5000 Total Market Index',
    'SP500': 'S&P 500 Index',
}

# ============================================================================
# WEBSITE-REQUIRED SYMBOLS (All asset classes)
# ============================================================================

WEBSITE_SYMBOLS = {
    # US Indices (Major)
    'us_indices': [
        'SPY', '^GSPC', 'QQQ', '^IXIC', 'DIA', '^DJI',
        'IWM', '^RUT', '^VIX', 'VXX', 'UVXY'
    ],

    # Sector ETFs (All 11 sectors)
    'sectors': [
        'XLK',  # Technology
        'XLF',  # Financials
        'XLE',  # Energy
        'XLV',  # Healthcare
        'XLY',  # Consumer Discretionary
        'XLP',  # Consumer Staples
        'XLI',  # Industrials
        'XLB',  # Materials
        'XLU',  # Utilities
        'XLRE', # Real Estate
        'XLC'   # Communications
    ],

    # Commodities & Precious Metals
    'commodities': [
        'GLD',   # Gold ETF
        'GC=F',  # Gold Futures
        'SLV',   # Silver ETF
        'SI=F',  # Silver Futures
        'PPLT',  # Platinum ETF
        'PL=F',  # Platinum Futures
        'CPER',  # Copper ETF
        'HG=F',  # Copper Futures
        'USO',   # Oil ETF
        'CL=F',  # Crude Oil Futures
        'UNG',   # Natural Gas ETF
        'NG=F'   # Natural Gas Futures
    ],

    # Bonds & Fixed Income
    'bonds': [
        'TLT',   # 20+ Year Treasury
        'IEF',   # 7-10 Year Treasury
        'SHY',   # 1-3 Year Treasury
        'HYG',   # High Yield Corporate
        'LQD',   # Investment Grade Corporate
        'EMB',   # Emerging Market Bonds
        'BNDX',  # International Bonds
        '^TNX',  # 10-Year Treasury Yield
        '^FVX',  # 5-Year Treasury Yield
        '^TYX'   # 30-Year Treasury Yield
    ],

    # Forex & Currencies
    'forex': [
        'UUP',          # US Dollar Index ETF
        'DX-Y.NYE',     # US Dollar Index
        'EURUSD=X',     # Euro/USD
        'GBPUSD=X',     # Pound/USD
        'USDJPY=X',     # USD/Yen
        'AUDJPY=X',     # Aud/Yen (Risk barometer)
        'AUDUSD=X',     # Aud/USD
        'USDCAD=X',     # USD/CAD
        'USDCHF=X'      # USD/CHF
    ],

    # Crypto
    'crypto': [
        'BTC-USD',  # Bitcoin
        'ETH-USD',  # Ethereum
        'SOL-USD',  # Solana
        'BNB-USD'   # Binance Coin
    ],

    # Global Indices
    'global': [
        'EFA',  # EAFE (Developed ex-US)
        'EEM',  # Emerging Markets
        'FXI',  # China
        'EWJ',  # Japan
        'EWG',  # Germany
        'EWU',  # UK
        'EWT',  # Taiwan
        'EWY',  # South Korea
        'EWZ'   # Brazil
    ],

    # Futures
    'futures': [
        'ES=F',   # E-mini S&P 500
        'NQ=F',   # E-mini NASDAQ
        'YM=F',   # E-mini Dow
        'RTY=F'   # E-mini Russell 2000
    ]
}

class ComprehensiveMacroScanner:
    """Enhanced scanner for ALL macro + market data"""

    def __init__(self):
        self.redis_client = None
        self.db_conn = None
        self.session = None
        self.fred_key = os.getenv('FRED_API_KEY')
        self.polygon_key = os.getenv('POLYGON_IO_API_KEY')
        self.twelve_data_key = os.getenv('TWELVE_DATA_API_KEY')

        self.stats = {
            'fred_success': 0,
            'fred_fail': 0,
            'market_success': 0,
            'market_fail': 0,
            'total_datapoints': 0
        }

    async def initialize(self):
        """Initialize all connections"""
        try:
            self.redis_client = redis.Redis(
                host='localhost', port=6379, db=0,
                decode_responses=True
            )
            self.redis_client.ping()

            self.db_conn = psycopg2.connect(
                dbname=os.getenv('POSTGRES_DB', 'spartan_research_db'),
                user=os.getenv('POSTGRES_USER', 'spartan'),
                password=os.getenv('POSTGRES_PASSWORD', 'spartan'),
                host='localhost', port=5432
            )

            self.session = aiohttp.ClientSession()

            logger.info("✅ Comprehensive scanner initialized")
            logger.info(f"   FRED indicators: {len(FRED_INDICATORS)}")
            logger.info(f"   Market symbols: {sum(len(v) for v in WEBSITE_SYMBOLS.values())}")
            logger.info(f"   Total data points: {len(FRED_INDICATORS) + sum(len(v) for v in WEBSITE_SYMBOLS.values())}")

            return True
        except Exception as e:
            logger.error(f"❌ Init failed: {e}")
            return False

    async def fetch_fred(self, series_id: str, name: str) -> Optional[Dict]:
        """Fetch FRED indicator"""
        if not self.fred_key:
            return None

        try:
            url = "https://api.stlouisfed.org/fred/series/observations"
            params = {
                'series_id': series_id,
                'api_key': self.fred_key,
                'file_type': 'json',
                'limit': 1,
                'sort_order': 'desc'
            }

            async with self.session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'observations' in data and len(data['observations']) > 0:
                        obs = data['observations'][0]
                        if obs['value'] != '.':  # FRED uses '.' for missing data
                            self.stats['fred_success'] += 1
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
            logger.debug(f"FRED error {series_id}: {e}")

        self.stats['fred_fail'] += 1
        return None

    async def fetch_polygon_symbol(self, symbol: str) -> Optional[Dict]:
        """Fetch symbol from Polygon.io"""
        if not self.polygon_key:
            return None

        try:
            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"
            params = {'apiKey': self.polygon_key}

            async with self.session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'results' in data and len(data['results']) > 0:
                        result = data['results'][0]
                        self.stats['market_success'] += 1
                        return {
                            'symbol': symbol,
                            'price': result['c'],
                            'volume': result['v'],
                            'high': result['h'],
                            'low': result['l'],
                            'open': result['o'],
                            'timestamp': datetime.fromtimestamp(result['t']/1000).isoformat(),
                            'source': 'polygon',
                            'category': 'market'
                        }
        except Exception as e:
            logger.debug(f"Polygon error {symbol}: {e}")

        self.stats['market_fail'] += 1
        return None

    async def store_data(self, data: Dict):
        """Store data in Redis + PostgreSQL"""
        try:
            category = data.get('category', 'unknown')
            symbol = data.get('symbol', 'UNKNOWN')

            # Redis (1 hour TTL for economic, 15 min for market)
            ttl = 3600 if category == 'economic' else 900
            redis_key = f"{category}:{symbol}"
            self.redis_client.setex(redis_key, ttl, json.dumps(data))

            # PostgreSQL
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO preloaded_market_data
                    (symbol, data_type, price, metadata, timestamp, source)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol, data_type, timestamp) DO UPDATE
                    SET price = EXCLUDED.price,
                        metadata = EXCLUDED.metadata
                """, (
                    symbol,
                    category,
                    data.get('value') or data.get('price'),
                    json.dumps(data),
                    datetime.now(),
                    data['source']
                ))
                self.db_conn.commit()

            self.stats['total_datapoints'] += 1

        except Exception as e:
            logger.error(f"Store error: {e}")

    async def scan_all_fred(self):
        """Scan all FRED indicators"""
        logger.info(f"📊 Scanning {len(FRED_INDICATORS)} FRED indicators...")

        tasks = []
        for series_id, name in FRED_INDICATORS.items():
            tasks.append(self.fetch_fred(series_id, name))

            # Rate limiting - FRED allows 120 calls/minute
            if len(tasks) >= 50:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if result and isinstance(result, dict):
                        await self.store_data(result)
                tasks = []
                await asyncio.sleep(30)  # 30 sec pause every 50 calls

        # Process remaining
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if result and isinstance(result, dict):
                    await self.store_data(result)

    async def scan_all_market_symbols(self):
        """Scan all market symbols"""
        total_symbols = sum(len(v) for v in WEBSITE_SYMBOLS.values())
        logger.info(f"📈 Scanning {total_symbols} market symbols...")

        for category, symbols in WEBSITE_SYMBOLS.items():
            logger.info(f"   Scanning {category}: {len(symbols)} symbols")

            for symbol in symbols:
                data = await self.fetch_polygon_symbol(symbol)
                if data:
                    await self.store_data(data)
                await asyncio.sleep(0.1)  # Rate limiting

    async def full_scan(self):
        """Execute complete scan"""
        scan_start = time.time()

        logger.info("=" * 70)
        logger.info("🔍 COMPREHENSIVE MACRO & MARKET SCAN STARTING")
        logger.info("=" * 70)

        # Scan FRED indicators
        await self.scan_all_fred()

        # Scan market symbols
        await self.scan_all_market_symbols()

        scan_duration = time.time() - scan_start

        logger.info("=" * 70)
        logger.info("✅ COMPREHENSIVE SCAN COMPLETE")
        logger.info(f"   Duration: {scan_duration:.1f}s ({scan_duration/60:.1f} min)")
        logger.info(f"   FRED Success: {self.stats['fred_success']}/{self.stats['fred_success']+self.stats['fred_fail']}")
        logger.info(f"   Market Success: {self.stats['market_success']}/{self.stats['market_success']+self.stats['market_fail']}")
        logger.info(f"   Total Data Points: {self.stats['total_datapoints']}")
        logger.info("=" * 70)

    async def run_continuous(self):
        """Run continuous scanning (1 hour interval)"""
        logger.info("🚀 Starting comprehensive scanning (1 hour interval)")

        while True:
            try:
                await self.full_scan()
                logger.info("⏰ Next scan in 1 hour")
                await asyncio.sleep(3600)
            except Exception as e:
                logger.error(f"❌ Scan error: {e}")
                await asyncio.sleep(300)

    async def shutdown(self):
        """Cleanup"""
        if self.session:
            await self.session.close()
        if self.db_conn:
            self.db_conn.close()
        logger.info("✅ Shutdown complete")

async def main():
    scanner = ComprehensiveMacroScanner()

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
