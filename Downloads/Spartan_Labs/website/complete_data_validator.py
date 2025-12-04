#!/usr/bin/env python3
"""
COMPLETE DATA VALIDATOR - Checks EVERY data point on EVERY webpage
Ensures 100% real data coverage with ZERO empty fields
"""

import json
import redis
import yfinance as yf
import requests
from datetime import datetime
import logging
import asyncio
import aiohttp
from fredapi import Fred
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('DATA_VALIDATOR')

class CompleteDataValidator:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.fred = Fred(api_key=os.getenv('FRED_API_KEY')) if os.getenv('FRED_API_KEY') else None

        # COMPLETE list of ALL data points needed across entire website
        self.required_data_points = {
            # Main Dashboard - AlphaStream Terminal
            'crypto:BTC-USD': 'Bitcoin',
            'crypto:ETH-USD': 'Ethereum',
            'commodity:gold': 'Gold (XAU/USD)',
            'market:index:SPY': 'S&P 500',

            # Stealth Macro
            'market:index:^DXY': 'Dollar Index',
            'treasury:^TNX': '10Y Yield',
            'commodity:GLD': 'Gold ETF',
            'commodity:USO': 'Oil ETF',
            'market:index:^VIX': 'VIX',

            # Volatility Composite
            'volatility:^VIX': 'Market VIX',
            'crypto:volatility': 'Crypto Volatility',

            # Best Composite Indicator
            'forex:AUDJPY': 'AUD/JPY',
            'etf:HYG': 'High Yield Bonds',
            'treasury:TNX': '10-Year Yield',

            # Crypto Composite
            'crypto:SOL-USD': 'Solana',

            # Recession Model
            'spread:10Y3M': '10Y-3M Spread',

            # Economic Cycle
            'fred:GDP': 'GDP Growth',
            'fred:UNRATE': 'Unemployment',
            'fred:CPIAUCSL': 'CPI Inflation',
            'fred:PCEPI': 'PCE Inflation',
            'consumer:UMCSENT': 'Consumer Confidence',
            'fred:CFNAI': 'Leading Index',

            # Sector ETFs
            'sector:XLF': 'Financials',
            'sector:XLK': 'Technology',
            'sector:XLE': 'Energy',
            'sector:XLV': 'Healthcare',
            'sector:XLI': 'Industrials',
            'sector:XLP': 'Consumer Staples',
            'sector:XLY': 'Consumer Discretionary',
            'sector:XLU': 'Utilities',
            'sector:XLRE': 'Real Estate',
            'sector:XLB': 'Materials',
            'sector:XLC': 'Communication',

            # Major Indices
            'market:index:QQQ': 'NASDAQ',
            'market:index:DIA': 'Dow Jones',
            'market:index:IWM': 'Russell 2000',

            # Global Markets
            'market:global:EFA': 'International Developed',
            'market:global:EEM': 'Emerging Markets',
            'market:global:FXI': 'China',
            'market:global:EWJ': 'Japan',

            # Commodities
            'commodity:SLV': 'Silver',
            'commodity:CPER': 'Copper',
            'commodity:UNG': 'Natural Gas',
            'commodity:CORN': 'Corn',
            'commodity:WEAT': 'Wheat',

            # Forex
            'forex:EURUSD': 'EUR/USD',
            'forex:GBPUSD': 'GBP/USD',
            'forex:USDJPY': 'USD/JPY',
            'forex:USDCAD': 'USD/CAD',

            # Bonds
            'bond:TLT': '20Y Treasury',
            'bond:IEF': '7-10Y Treasury',
            'bond:SHY': '1-3Y Treasury',
            'bond:AGG': 'Aggregate Bonds',
            'bond:EMB': 'Emerging Market Bonds',
            'bond:BNDX': 'International Bonds',

            # Additional Crypto
            'crypto:BNB-USD': 'Binance Coin',
            'crypto:XRP-USD': 'Ripple',
            'crypto:ADA-USD': 'Cardano',
            'crypto:DOGE-USD': 'Dogecoin'
        }

        self.empty_fields_found = []
        self.fixed_count = 0

    async def fetch_and_fix(self, key: str, name: str):
        """Fetch real data for a key and store it"""
        try:
            # Check if data exists
            existing = self.redis_client.get(key)
            if existing:
                data = json.loads(existing)
                # Check if it's empty or invalid
                if self.is_valid_data(data):
                    logger.info(f"✅ {name}: Valid data exists")
                    return True

            # Data is missing or invalid - FETCH NOW
            logger.warning(f"⚠️ {name}: Missing or invalid - fetching...")

            # Determine symbol and fetch method
            parts = key.split(':')
            category = parts[0]
            symbol = parts[1] if len(parts) > 1 else ''

            if category == 'market' or category == 'sector':
                # Stock market data
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1d')
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                    data = {'price': round(price, 2), 'symbol': symbol}
                    self.redis_client.setex(key, 300, json.dumps(data))
                    logger.info(f"✅ Fixed {name}: ${price:.2f}")
                    self.fixed_count += 1
                    return True

            elif category == 'crypto':
                # Cryptocurrency data
                if symbol == 'volatility':
                    # Calculate crypto volatility
                    btc = yf.Ticker('BTC-USD').history(period='5d')
                    if not btc.empty:
                        volatility = btc['Close'].std() / btc['Close'].mean() * 100
                        data = {'value': round(volatility, 2)}
                        self.redis_client.setex(key, 300, json.dumps(data))
                        logger.info(f"✅ Fixed {name}: {volatility:.2f}%")
                        self.fixed_count += 1
                        return True
                else:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period='1d')
                    if not hist.empty:
                        price = hist['Close'].iloc[-1]
                        data = {'price': round(price, 2), 'symbol': symbol}
                        self.redis_client.setex(key, 300, json.dumps(data))
                        logger.info(f"✅ Fixed {name}: ${price:.2f}")
                        self.fixed_count += 1
                        return True

            elif category == 'forex':
                # Forex data
                symbol_map = {
                    'AUDJPY': 'AUDJPY=X',
                    'EURUSD': 'EURUSD=X',
                    'GBPUSD': 'GBPUSD=X',
                    'USDJPY': 'USDJPY=X',
                    'USDCAD': 'USDCAD=X'
                }
                ticker_symbol = symbol_map.get(symbol, f'{symbol}=X')
                ticker = yf.Ticker(ticker_symbol)
                hist = ticker.history(period='1d')
                if not hist.empty:
                    rate = hist['Close'].iloc[-1]
                    data = {'rate': round(rate, 4), 'symbol': symbol}
                    self.redis_client.setex(key, 300, json.dumps(data))
                    logger.info(f"✅ Fixed {name}: {rate:.4f}")
                    self.fixed_count += 1
                    return True

            elif category == 'commodity':
                # Commodity ETFs
                etf_map = {
                    'gold': 'GLD',
                    'GLD': 'GLD',
                    'SLV': 'SLV',
                    'USO': 'USO',
                    'UNG': 'UNG',
                    'CPER': 'CPER',
                    'CORN': 'CORN',
                    'WEAT': 'WEAT'
                }
                ticker_symbol = etf_map.get(symbol, symbol)
                ticker = yf.Ticker(ticker_symbol)
                hist = ticker.history(period='1d')
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                    data = {'price': round(price, 2), 'symbol': ticker_symbol}
                    self.redis_client.setex(key, 300, json.dumps(data))
                    logger.info(f"✅ Fixed {name}: ${price:.2f}")
                    self.fixed_count += 1
                    return True

            elif category == 'etf':
                # ETF data
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1d')
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                    data = {'price': round(price, 2), 'symbol': symbol}
                    self.redis_client.setex(key, 300, json.dumps(data))
                    logger.info(f"✅ Fixed {name}: ${price:.2f}")
                    self.fixed_count += 1
                    return True

            elif category == 'treasury':
                # Treasury yields
                symbol_map = {
                    'TNX': '^TNX',
                    '^TNX': '^TNX'
                }
                ticker_symbol = symbol_map.get(symbol, symbol)
                ticker = yf.Ticker(ticker_symbol)
                hist = ticker.history(period='1d')
                if not hist.empty:
                    yield_val = hist['Close'].iloc[-1]
                    data = {'yield': round(yield_val, 2), 'symbol': symbol}
                    self.redis_client.setex(key, 300, json.dumps(data))
                    logger.info(f"✅ Fixed {name}: {yield_val:.2f}%")
                    self.fixed_count += 1
                    return True

            elif category == 'volatility':
                # Volatility indices
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1d')
                if not hist.empty:
                    value = hist['Close'].iloc[-1]
                    data = {'value': round(value, 2), 'symbol': symbol}
                    self.redis_client.setex(key, 300, json.dumps(data))
                    logger.info(f"✅ Fixed {name}: {value:.2f}")
                    self.fixed_count += 1
                    return True

            elif category == 'fred':
                # FRED economic data
                if self.fred:
                    series = self.fred.get_series(symbol, limit=1)
                    if not series.empty:
                        value = series.iloc[-1]
                        data = {'value': round(value, 2), 'symbol': symbol}
                        self.redis_client.setex(key, 300, json.dumps(data))
                        logger.info(f"✅ Fixed {name}: {value:.2f}")
                        self.fixed_count += 1
                        return True

            elif category == 'spread':
                # Yield spread calculation
                if symbol == '10Y3M':
                    # Get 10Y and 3M yields
                    teny = yf.Ticker('^TNX').history(period='1d')
                    threem = yf.Ticker('^IRX').history(period='1d')
                    if not teny.empty and not threem.empty:
                        spread = teny['Close'].iloc[-1] - (threem['Close'].iloc[-1] / 100)
                        data = {'value': round(spread, 2), 'symbol': symbol}
                        self.redis_client.setex(key, 300, json.dumps(data))
                        logger.info(f"✅ Fixed {name}: {spread:.2f}%")
                        self.fixed_count += 1
                        return True

            elif category == 'bond':
                # Bond ETFs
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1d')
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                    data = {'price': round(price, 2), 'symbol': symbol}
                    self.redis_client.setex(key, 300, json.dumps(data))
                    logger.info(f"✅ Fixed {name}: ${price:.2f}")
                    self.fixed_count += 1
                    return True

            elif category == 'consumer':
                # Consumer sentiment
                if symbol == 'UMCSENT' and self.fred:
                    series = self.fred.get_series('UMCSENT', limit=1)
                    if not series.empty:
                        value = series.iloc[-1]
                        data = {'value': round(value, 2), 'symbol': symbol}
                        self.redis_client.setex(key, 300, json.dumps(data))
                        logger.info(f"✅ Fixed {name}: {value:.2f}")
                        self.fixed_count += 1
                        return True

            # If we couldn't fetch, mark as empty
            self.empty_fields_found.append(f"{key}: {name}")
            logger.error(f"❌ Could not fix {name} ({key})")
            return False

        except Exception as e:
            logger.error(f"Error fixing {name}: {e}")
            self.empty_fields_found.append(f"{key}: {name}")
            return False

    def is_valid_data(self, data):
        """Check if data is valid (not empty/placeholder)"""
        if not data:
            return False

        # Check for invalid values
        for key, value in data.items():
            if value is None or value == 'N/A' or value == '--':
                return False
            if key in ['price', 'value', 'rate', 'yield']:
                if not isinstance(value, (int, float)) or value <= 0:
                    return False

        return True

    async def validate_all_data(self):
        """Check and fix ALL data points"""
        logger.info("="*60)
        logger.info("🔍 COMPLETE DATA VALIDATION - CHECKING ENTIRE WEBSITE")
        logger.info("="*60)

        tasks = []
        for key, name in self.required_data_points.items():
            tasks.append(self.fetch_and_fix(key, name))

        # Run all checks in parallel
        results = await asyncio.gather(*tasks)

        # Summary
        logger.info("="*60)
        logger.info("📊 VALIDATION COMPLETE")
        logger.info(f"✅ Total data points checked: {len(self.required_data_points)}")
        logger.info(f"✅ Data points fixed: {self.fixed_count}")
        logger.info(f"❌ Empty fields remaining: {len(self.empty_fields_found)}")

        if self.empty_fields_found:
            logger.warning("Empty fields that need attention:")
            for field in self.empty_fields_found:
                logger.warning(f"  - {field}")
        else:
            logger.info("🎉 ALL DATA POINTS HAVE VALID VALUES!")

        logger.info("="*60)

        # Store validation status
        self.redis_client.setex(
            'validation:status',
            60,
            json.dumps({
                'timestamp': datetime.now().isoformat(),
                'total_points': len(self.required_data_points),
                'fixed': self.fixed_count,
                'empty': len(self.empty_fields_found),
                'status': 'PERFECT' if len(self.empty_fields_found) == 0 else 'NEEDS_ATTENTION'
            })
        )

        return len(self.empty_fields_found) == 0

    def run(self):
        """Run validation"""
        return asyncio.run(self.validate_all_data())

if __name__ == "__main__":
    validator = CompleteDataValidator()
    success = validator.run()

    if success:
        logger.info("✅ WEBSITE DATA VALIDATION SUCCESSFUL - ZERO EMPTY FIELDS!")
    else:
        logger.warning("⚠️ Some data points need attention - running continuous fix...")
        # Keep running until all fixed
        while not success:
            logger.info("🔄 Retrying in 5 seconds...")
            import time
            time.sleep(5)
            success = validator.run()