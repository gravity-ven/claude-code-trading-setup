#!/usr/bin/env python3
"""
COMPREHENSIVE PAGE SCANNER - Checks EVERY data point on EVERY page
NO COMPROMISE - Fixes ALL errors immediately
"""

import json
import redis
import yfinance as yf
import requests
from datetime import datetime
import logging
import asyncio
from fredapi import Fred
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('PAGE_SCANNER')

class ComprehensivePageScanner:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.fred = Fred(api_key=os.getenv('FRED_API_KEY')) if os.getenv('FRED_API_KEY') else None
        self.errors_found = []
        self.fixes_applied = 0

    def scan_page_data(self, page_name, required_fields):
        """Scan a specific page for missing data"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📄 SCANNING: {page_name}")
        logger.info(f"{'='*60}")

        page_errors = []

        for field_key, field_name in required_fields.items():
            try:
                # Check Redis cache
                data = self.redis_client.get(field_key)

                if not data:
                    logger.error(f"❌ EMPTY: {field_name} ({field_key})")
                    page_errors.append((field_key, field_name))
                else:
                    parsed = json.loads(data)

                    # Check for invalid values
                    invalid = False
                    for key, value in parsed.items():
                        if value in [None, 'N/A', '--', 'unavailable', 'error', 'OFFLINE', 'STALE']:
                            invalid = True
                            break
                        if key in ['price', 'value', 'rate', 'yield'] and (not isinstance(value, (int, float)) or value <= 0):
                            invalid = True
                            break

                    if invalid:
                        logger.error(f"❌ INVALID: {field_name} = {parsed}")
                        page_errors.append((field_key, field_name))
                    else:
                        logger.info(f"✅ OK: {field_name} = {parsed}")

            except Exception as e:
                logger.error(f"❌ ERROR: {field_name} - {e}")
                page_errors.append((field_key, field_name))

        return page_errors

    async def fix_data_error(self, field_key, field_name):
        """Fix a single data error with real data"""
        try:
            logger.warning(f"🔧 FIXING: {field_name} ({field_key})")

            parts = field_key.split(':')
            category = parts[0]
            symbol = parts[1] if len(parts) > 1 else ''

            # Fetch real data based on category
            if category == 'market' or category == 'sector':
                ticker = yf.Ticker(symbol if symbol else field_key.split(':')[-1])
                hist = ticker.history(period='1d')
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                    data = {'price': round(price, 2), 'symbol': symbol}
                    self.redis_client.setex(field_key, 300, json.dumps(data))
                    logger.info(f"✅ FIXED: {field_name} = ${price:.2f}")
                    self.fixes_applied += 1
                    return True

            elif category == 'crypto':
                if symbol == 'volatility':
                    # Calculate crypto volatility
                    btc = yf.Ticker('BTC-USD').history(period='5d')
                    if not btc.empty:
                        volatility = btc['Close'].std() / btc['Close'].mean() * 100
                        data = {'value': round(volatility, 2)}
                        self.redis_client.setex(field_key, 300, json.dumps(data))
                        logger.info(f"✅ FIXED: {field_name} = {volatility:.2f}%")
                        self.fixes_applied += 1
                        return True
                else:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period='1d')
                    if not hist.empty:
                        price = hist['Close'].iloc[-1]
                        data = {'price': round(price, 2), 'symbol': symbol}
                        self.redis_client.setex(field_key, 300, json.dumps(data))
                        logger.info(f"✅ FIXED: {field_name} = ${price:.2f}")
                        self.fixes_applied += 1
                        return True

            elif category == 'forex':
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
                    self.redis_client.setex(field_key, 300, json.dumps(data))
                    logger.info(f"✅ FIXED: {field_name} = {rate:.4f}")
                    self.fixes_applied += 1
                    return True

            elif category == 'commodity':
                etf_map = {
                    'gold': 'GLD',
                    'silver': 'SLV',
                    'oil': 'USO',
                    'GLD': 'GLD',
                    'SLV': 'SLV',
                    'USO': 'USO',
                    'CPER': 'CPER',
                    'UNG': 'UNG',
                    'CORN': 'CORN',
                    'WEAT': 'WEAT'
                }
                ticker_symbol = etf_map.get(symbol, symbol)
                ticker = yf.Ticker(ticker_symbol)
                hist = ticker.history(period='1d')
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                    data = {'price': round(price, 2), 'symbol': ticker_symbol}
                    self.redis_client.setex(field_key, 300, json.dumps(data))
                    logger.info(f"✅ FIXED: {field_name} = ${price:.2f}")
                    self.fixes_applied += 1
                    return True

            elif category == 'treasury':
                symbol_map = {
                    'TNX': '^TNX',
                    '^TNX': '^TNX',
                    'IRX': '^IRX',
                    '^IRX': '^IRX'
                }
                ticker_symbol = symbol_map.get(symbol, symbol)
                ticker = yf.Ticker(ticker_symbol)
                hist = ticker.history(period='1d')
                if not hist.empty:
                    yield_val = hist['Close'].iloc[-1]
                    data = {'yield': round(yield_val, 2), 'symbol': symbol}
                    self.redis_client.setex(field_key, 300, json.dumps(data))
                    logger.info(f"✅ FIXED: {field_name} = {yield_val:.2f}%")
                    self.fixes_applied += 1
                    return True

            elif category == 'volatility':
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1d')
                if not hist.empty:
                    value = hist['Close'].iloc[-1]
                    data = {'value': round(value, 2), 'symbol': symbol}
                    self.redis_client.setex(field_key, 300, json.dumps(data))
                    logger.info(f"✅ FIXED: {field_name} = {value:.2f}")
                    self.fixes_applied += 1
                    return True

            elif category == 'fred' and self.fred:
                series = self.fred.get_series(symbol, limit=1)
                if not series.empty:
                    value = series.iloc[-1]
                    data = {'value': round(value, 2), 'symbol': symbol}
                    self.redis_client.setex(field_key, 300, json.dumps(data))
                    logger.info(f"✅ FIXED: {field_name} = {value:.2f}")
                    self.fixes_applied += 1
                    return True

            elif category == 'etf':
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1d')
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                    data = {'price': round(price, 2), 'symbol': symbol}
                    self.redis_client.setex(field_key, 300, json.dumps(data))
                    logger.info(f"✅ FIXED: {field_name} = ${price:.2f}")
                    self.fixes_applied += 1
                    return True

            elif category == 'bond':
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period='1d')
                if not hist.empty:
                    price = hist['Close'].iloc[-1]
                    data = {'price': round(price, 2), 'symbol': symbol}
                    self.redis_client.setex(field_key, 300, json.dumps(data))
                    logger.info(f"✅ FIXED: {field_name} = ${price:.2f}")
                    self.fixes_applied += 1
                    return True

            elif category == 'spread':
                if symbol == '10Y3M':
                    # Calculate spread
                    teny = yf.Ticker('^TNX').history(period='1d')
                    threem = yf.Ticker('^IRX').history(period='1d')
                    if not teny.empty and not threem.empty:
                        spread = teny['Close'].iloc[-1] - (threem['Close'].iloc[-1] / 100)
                        data = {'value': round(spread, 2), 'symbol': symbol}
                        self.redis_client.setex(field_key, 300, json.dumps(data))
                        logger.info(f"✅ FIXED: {field_name} = {spread:.2f}%")
                        self.fixes_applied += 1
                        return True

            logger.error(f"❌ Could not fix {field_name}")
            return False

        except Exception as e:
            logger.error(f"❌ Error fixing {field_name}: {e}")
            return False

    async def scan_all_pages(self):
        """Scan ALL pages for data errors"""

        # Define ALL pages and their required data
        pages = {
            "AlphaStream Terminal (Main Dashboard)": {
                'market:index:SPY': 'S&P 500',
                'market:index:QQQ': 'NASDAQ',
                'market:index:DIA': 'Dow Jones',
                'market:index:IWM': 'Russell 2000',
                'crypto:BTC-USD': 'Bitcoin',
                'crypto:ETH-USD': 'Ethereum',
                'commodity:gold': 'Gold',
                'commodity:oil': 'Oil',
                'market:index:^VIX': 'VIX',
                'fred:UNRATE': 'Unemployment',
                'fred:GDP': 'GDP',
                'fred:CPIAUCSL': 'CPI'
            },

            "Stealth Macro": {
                'market:index:^DXY': 'Dollar Index',
                'treasury:^TNX': '10Y Yield',
                'commodity:GLD': 'Gold ETF',
                'commodity:USO': 'Oil ETF',
                'market:index:^VIX': 'VIX',
                'market:index:SPY': 'S&P 500',
                'forex:EURUSD': 'EUR/USD',
                'forex:USDJPY': 'USD/JPY'
            },

            "Volatility Composite": {
                'volatility:^VIX': 'Market VIX',
                'crypto:volatility': 'Crypto Volatility',
                'market:index:SPY': 'S&P 500',
                'market:index:QQQ': 'NASDAQ',
                'bond:TLT': '20Y Treasury',
                'commodity:GLD': 'Gold'
            },

            "Best Composite Indicator": {
                'forex:AUDJPY': 'AUD/JPY',
                'etf:HYG': 'High Yield Bonds',
                'treasury:TNX': '10-Year Yield',
                'market:index:SPY': 'S&P 500',
                'market:index:^VIX': 'VIX'
            },

            "Crypto Composite": {
                'crypto:BTC-USD': 'Bitcoin',
                'crypto:ETH-USD': 'Ethereum',
                'crypto:SOL-USD': 'Solana',
                'crypto:BNB-USD': 'Binance Coin',
                'crypto:XRP-USD': 'Ripple',
                'crypto:ADA-USD': 'Cardano',
                'crypto:DOGE-USD': 'Dogecoin'
            },

            "Economic Cycle": {
                'fred:GDP': 'GDP Growth',
                'fred:UNRATE': 'Unemployment',
                'fred:CPIAUCSL': 'CPI Inflation',
                'fred:PCEPI': 'PCE Inflation',
                'consumer:UMCSENT': 'Consumer Confidence',
                'fred:CFNAI': 'Leading Index',
                'fred:FEDFUNDS': 'Fed Funds Rate'
            },

            "Recession Model": {
                'spread:10Y3M': '10Y-3M Spread',
                'fred:UNRATE': 'Unemployment Rate',
                'fred:GDP': 'GDP Growth',
                'consumer:UMCSENT': 'Consumer Sentiment',
                'market:index:^VIX': 'VIX',
                'fred:CFNAI': 'Leading Index'
            },

            "Sector Rotation": {
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
                'sector:XLC': 'Communication'
            },

            "Global Markets": {
                'market:global:EFA': 'International Developed',
                'market:global:EEM': 'Emerging Markets',
                'market:global:FXI': 'China',
                'market:global:EWJ': 'Japan',
                'forex:EURUSD': 'EUR/USD',
                'forex:GBPUSD': 'GBP/USD',
                'forex:USDJPY': 'USD/JPY',
                'forex:USDCAD': 'USD/CAD'
            },

            "Bond Markets": {
                'bond:TLT': '20Y Treasury',
                'bond:IEF': '7-10Y Treasury',
                'bond:SHY': '1-3Y Treasury',
                'bond:AGG': 'Aggregate Bonds',
                'bond:HYG': 'High Yield',
                'bond:EMB': 'Emerging Market Bonds',
                'bond:BNDX': 'International Bonds'
            },

            "Commodities": {
                'commodity:gold': 'Gold',
                'commodity:SLV': 'Silver',
                'commodity:USO': 'Oil',
                'commodity:UNG': 'Natural Gas',
                'commodity:CPER': 'Copper',
                'commodity:CORN': 'Corn',
                'commodity:WEAT': 'Wheat'
            }
        }

        logger.info("\n" + "="*60)
        logger.info("🔍 COMPREHENSIVE PAGE SCAN - NO COMPROMISE")
        logger.info("="*60)

        all_errors = []

        # Scan each page
        for page_name, fields in pages.items():
            page_errors = self.scan_page_data(page_name, fields)
            if page_errors:
                all_errors.extend(page_errors)
                self.errors_found.append({
                    'page': page_name,
                    'errors': page_errors
                })

        # Fix ALL errors found
        if all_errors:
            logger.warning(f"\n⚠️ FOUND {len(all_errors)} DATA ERRORS - FIXING ALL NOW!")

            tasks = []
            for field_key, field_name in all_errors:
                tasks.append(self.fix_data_error(field_key, field_name))

            await asyncio.gather(*tasks)

        # Final report
        logger.info("\n" + "="*60)
        logger.info("📊 SCAN COMPLETE - FINAL REPORT")
        logger.info("="*60)
        logger.info(f"✅ Pages Scanned: {len(pages)}")
        logger.info(f"✅ Total Fields Checked: {sum(len(fields) for fields in pages.values())}")
        logger.info(f"✅ Errors Found: {len(all_errors)}")
        logger.info(f"✅ Fixes Applied: {self.fixes_applied}")

        if self.fixes_applied == len(all_errors):
            logger.info("🎉 ALL ERRORS FIXED - ZERO DATA GAPS!")
        else:
            logger.warning(f"⚠️ {len(all_errors) - self.fixes_applied} errors could not be fixed")

        logger.info("="*60)

        # Update scan status
        self.redis_client.setex(
            'page_scan:status',
            60,
            json.dumps({
                'timestamp': datetime.now().isoformat(),
                'pages_scanned': len(pages),
                'total_fields': sum(len(fields) for fields in pages.values()),
                'errors_found': len(all_errors),
                'fixes_applied': self.fixes_applied,
                'status': 'PERFECT' if self.fixes_applied == len(all_errors) else 'PARTIAL'
            })
        )

        return self.fixes_applied == len(all_errors)

    def run(self):
        """Run the comprehensive scan"""
        return asyncio.run(self.scan_all_pages())

if __name__ == "__main__":
    scanner = ComprehensivePageScanner()
    success = scanner.run()

    if success:
        logger.info("\n✅ PERFECT - ALL PAGES HAVE COMPLETE DATA!")
    else:
        logger.warning("\n⚠️ Some errors remain - running continuous fix...")
        # Keep trying until all fixed
        while not success:
            logger.info("🔄 Retrying in 5 seconds...")
            import time
            time.sleep(5)
            success = scanner.run()