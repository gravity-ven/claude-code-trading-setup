#!/usr/bin/env python3
"""
Swing Trading Dashboard API Server
===================================

Comprehensive multi-market data API for swing trading analysis.
Implements all features from technical_blueprint.md with real data sources.

Data Sources (Free Tier):
- yfinance: Market indices, commodities, forex (unlimited, free)
- FRED API: US rates, credit spreads, yields (120 req/min free)
- Alpha Vantage: Volatility indices (25 calls/day free)
- ExchangeRate-API: Forex rates (1,500/month free)

Author: Spartan Research Station
Version: 1.0.0
"""

import os
import asyncio
import aiohttp
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# API Keys (from environment variables or defaults)
# PRIORITY ORDER: Polygon.io (paid) → Yahoo Finance (free) → FRED (free) → Others
POLYGON_API_KEY = os.getenv('POLYGON_IO_API_KEY', '')
FRED_API_KEY = os.getenv('FRED_API_KEY', 'a6137538793a55227cbae2119e1573f5')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')
EXCHANGE_RATE_API_KEY = os.getenv('EXCHANGERATE_API_KEY', '')

# API Endpoints
POLYGON_BASE_URL = 'https://api.polygon.io'
FRED_BASE_URL = 'https://api.stlouisfed.org/fred/series/observations'
ALPHA_VANTAGE_BASE_URL = 'https://www.alphavantage.co/query'
EXCHANGE_RATE_BASE_URL = 'https://v6.exchangerate-api.com/v6'

# Data source priority (checked in order until success)
HAS_POLYGON = bool(POLYGON_API_KEY and POLYGON_API_KEY != 'your_polygon_api_key')
print(f"🔑 Polygon.io API: {'✅ ACTIVE (Premium)' if HAS_POLYGON else '❌ Not configured'}")
print(f"🔑 FRED API: {'✅ ACTIVE' if FRED_API_KEY else '❌ Not configured'}")

# Cache configuration
CACHE = {}
CACHE_DURATION = timedelta(minutes=15)  # 15-minute cache for real-time data


def get_cached_data(key: str) -> Optional[Any]:
    """Get data from cache if available and not expired."""
    if key in CACHE:
        data, timestamp = CACHE[key]
        if datetime.now() - timestamp < CACHE_DURATION:
            return data
    return None


def set_cached_data(key: str, data: Any) -> None:
    """Store data in cache with timestamp."""
    CACHE[key] = (data, datetime.now())


def fetch_polygon_data(symbols: List[str]) -> Dict[str, Dict]:
    """
    Fetch market data from Polygon.io (PREMIUM SOURCE - FIRST PRIORITY).
    Requires paid API key for real-time data.

    API Docs: https://polygon.io/docs/stocks/get_v2_aggs_ticker__stocksticker__prev

    Returns: {symbol: {price, change, change_pct, volume}}
    """
    if not HAS_POLYGON:
        return {}  # Return empty if no key configured

    results = {}

    for symbol in symbols:
        try:
            # Polygon.io endpoint: /v2/aggs/ticker/{symbol}/prev
            # Gets previous day's OHLCV data
            url = f"{POLYGON_BASE_URL}/v2/aggs/ticker/{symbol}/prev"
            params = {'apiKey': POLYGON_API_KEY, 'adjusted': 'true'}

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if data.get('status') == 'OK' and data.get('results'):
                    result = data['results'][0]
                    close_price = result['c']  # Close price
                    open_price = result['o']  # Open price
                    change = close_price - open_price
                    change_pct = (change / open_price) * 100 if open_price != 0 else 0

                    results[symbol] = {
                        'price': round(close_price, 2),
                        'change': round(change, 2),
                        'change_pct': round(change_pct, 2),
                        'volume': int(result['v']),  # Volume
                        'high': round(result['h'], 2),  # High
                        'low': round(result['l'], 2),  # Low
                        'timestamp': datetime.now().isoformat(),
                        'source': 'polygon.io'
                    }
                    print(f"✅ Polygon.io: {symbol} = ${close_price:.2f}")
                else:
                    print(f"⚠️ Polygon.io: No data for {symbol}")
            else:
                print(f"❌ Polygon.io API error {response.status_code} for {symbol}")

        except Exception as e:
            print(f"❌ Polygon.io error for {symbol}: {e}")

    return results


def fetch_yfinance_data(symbols: List[str]) -> Dict[str, Dict]:
    """
    Fetch market data from Yahoo Finance using yfinance.
    Free, unlimited API - FALLBACK data source (after Polygon.io).

    Returns: {symbol: {price, change, change_pct, volume}}
    """
    results = {}

    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='5d')

            if len(hist) >= 2:
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                change = current_price - prev_price
                change_pct = (change / prev_price) * 100

                results[symbol] = {
                    'price': round(current_price, 2),
                    'change': round(change, 2),
                    'change_pct': round(change_pct, 2),
                    'volume': int(hist['Volume'].iloc[-1]),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'yahoo_finance'
                }
                print(f"✅ Yahoo Finance: {symbol} = ${current_price:.2f}")
        except Exception as e:
            print(f"❌ Yahoo Finance error for {symbol}: {e}")
            results[symbol] = {
                'price': None,
                'change': None,
                'change_pct': None,
                'volume': None,
                'error': str(e),
                'source': 'yahoo_finance'
            }

    return results


async def fetch_fred_series(session: aiohttp.ClientSession, series_id: str) -> Optional[float]:
    """
    Fetch economic data from FRED API.
    Free tier: 120 requests/minute.

    Returns: Latest value from the series
    """
    params = {
        'series_id': series_id,
        'api_key': FRED_API_KEY,
        'file_type': 'json',
        'sort_order': 'desc',
        'limit': 1
    }

    try:
        async with session.get(FRED_BASE_URL, params=params) as response:
            if response.status == 200:
                data = await response.json()
                observations = data.get('observations', [])
                if observations:
                    return float(observations[0]['value'])
    except Exception as e:
        print(f"Error fetching FRED series {series_id}: {e}")

    return None


async def fetch_alpha_vantage(session: aiohttp.ClientSession, function: str, symbol: str) -> Optional[Dict]:
    """
    Fetch data from Alpha Vantage API.
    Free tier: 25 requests/day (use sparingly!).

    Returns: Latest data point
    """
    params = {
        'function': function,
        'symbol': symbol,
        'apikey': ALPHA_VANTAGE_API_KEY
    }

    try:
        async with session.get(ALPHA_VANTAGE_BASE_URL, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return data
    except Exception as e:
        print(f"Error fetching Alpha Vantage {symbol}: {e}")

    return None


def fetch_forex_data() -> Dict[str, Dict]:
    """
    Fetch forex rates from Yahoo Finance using yfinance.
    Free and unlimited - no API key required.

    Returns: Forex rates dict
    """
    # Yahoo Finance forex symbols
    forex_symbols = {
        'EURUSD=X': 'eurusd',
        'GBPUSD=X': 'gbpusd',
        'USDJPY=X': 'usdjpy',
        'USDCAD=X': 'usdcad',
        'AUDUSD=X': 'audusd',
        'NZDUSD=X': 'nzdusd',
        'USDCHF=X': 'usdchf'
    }

    results = {}
    for symbol, key in forex_symbols.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='5d')

            if len(hist) >= 2:
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                change = current_price - prev_price
                change_pct = (change / prev_price) * 100

                results[key] = {
                    'value': round(current_price, 4),
                    'change': round(change, 4),
                    'change_pct': round(change_pct, 2)
                }
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            results[key] = {'value': None, 'change': None, 'change_pct': None}

    # Calculate DXY (simplified)
    if results.get('eurusd', {}).get('value'):
        dxy_value = 100.0 / results['eurusd']['value']
        results['dxy'] = {'value': round(dxy_value, 2), 'change': 0.0, 'change_pct': 0.0}

    return results


@app.route('/api/swing-dashboard/market-indices', methods=['GET'])
def get_market_indices():
    """
    Get global market indices data (US, China, India, Japan, Germany).
    Uses yfinance - free and unlimited.
    """
    cache_key = 'market_indices'
    cached = get_cached_data(cache_key)
    if cached:
        return jsonify(cached)

    symbols = [
        # US Markets
        'SPY', 'QQQ', 'DIA', 'IWM',
        # China Markets
        '000001.SS',  # Shanghai Composite
        '^HSI',       # Hang Seng
        'FXI',        # China Large Cap ETF
        # India Markets
        '^BSESN',     # Sensex
        '^NSEI',      # Nifty 50
        'INDA',       # India ETF
        # Japan Markets
        '^N225',      # Nikkei 225
        'EWJ',        # Japan ETF
        'DXJ',        # Japan Currency Hedged ETF
        # Germany Markets
        '^GDAXI',     # DAX
        'EWG'         # Germany ETF
    ]

    data = fetch_yfinance_data(symbols)

    result = {
        'us_markets': {
            'spy': data.get('SPY', {}),
            'qqq': data.get('QQQ', {}),
            'dia': data.get('DIA', {}),
            'iwm': data.get('IWM', {})
        },
        'china_markets': {
            'shanghai': data.get('000001.SS', {}),
            'hang_seng': data.get('^HSI', {}),
            'fxi': data.get('FXI', {})
        },
        'india_markets': {
            'sensex': data.get('^BSESN', {}),
            'nifty50': data.get('^NSEI', {}),
            'inda': data.get('INDA', {})
        },
        'japan_markets': {
            'nikkei': data.get('^N225', {}),
            'ewj': data.get('EWJ', {}),
            'dxj': data.get('DXJ', {})
        },
        'germany_markets': {
            'dax': data.get('^GDAXI', {}),
            'ewg': data.get('EWG', {})
        },
        'timestamp': datetime.now().isoformat()
    }

    set_cached_data(cache_key, result)
    return jsonify(result)


@app.route('/api/swing-dashboard/volatility', methods=['GET'])
def get_volatility_indicators():
    """
    Get volatility and risk indicators.
    Uses yfinance for VIX ETFs (free) and Alpha Vantage for advanced metrics (limited).
    """
    cache_key = 'volatility_indicators'
    cached = get_cached_data(cache_key)
    if cached:
        return jsonify(cached)

    # VIX-related symbols (free via yfinance)
    symbols = [
        '^VIX',      # CBOE Volatility Index
        'VXX',       # VIX Short-Term Futures ETF
        'UVXY'       # 2x VIX Short-Term Futures
    ]

    data = fetch_yfinance_data(symbols)

    result = {
        'vix': data.get('^VIX', {}),
        'vxx': data.get('VXX', {}),
        'uvxy': data.get('UVXY', {}),
        'vvix': {'price': None, 'change': None, 'note': 'Alpha Vantage API limit'},
        'skew': {'price': None, 'change': None, 'note': 'CBOE direct feed required'},
        'move': {'price': None, 'change': None, 'note': 'ICE BofA feed required'},
        'timestamp': datetime.now().isoformat()
    }

    set_cached_data(cache_key, result)
    return jsonify(result)


@app.route('/api/swing-dashboard/credit-spreads', methods=['GET'])
def get_credit_spreads():
    """
    Get credit spreads from FRED API.
    Free tier: 120 requests/minute.
    """
    cache_key = 'credit_spreads'
    cached = get_cached_data(cache_key)
    if cached:
        return jsonify(cached)

    async def fetch_all_spreads():
        async with aiohttp.ClientSession() as session:
            tasks = [
                fetch_fred_series(session, 'BAMLH0A0HYM2'),  # HY OAS
                fetch_fred_series(session, 'BAMLC0A4CBBB'),  # IG BBB
                fetch_fred_series(session, 'DAAA'),          # AAA Spread
            ]
            results = await asyncio.gather(*tasks)
            return results

    try:
        hy_oas, ig_bbb, aaa_spread = asyncio.run(fetch_all_spreads())

        result = {
            'hy_oas': {'value': hy_oas, 'unit': 'bps', 'series': 'BAMLH0A0HYM2'},
            'ig_bbb': {'value': ig_bbb, 'unit': 'bps', 'series': 'BAMLC0A4CBBB'},
            'aaa_spread': {'value': aaa_spread, 'unit': 'bps', 'series': 'DAAA'},
            'em_spread': {'value': None, 'note': 'EM EMBI+ spread requires Bloomberg'},
            'source': 'FRED API (St. Louis Fed)',
            'timestamp': datetime.now().isoformat()
        }

        set_cached_data(cache_key, result)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/swing-dashboard/treasury-yields', methods=['GET'])
def get_treasury_yields():
    """
    Get US Treasury yields from FRED API.
    Free tier: 120 requests/minute.
    """
    cache_key = 'treasury_yields'
    cached = get_cached_data(cache_key)
    if cached:
        return jsonify(cached)

    async def fetch_all_yields():
        async with aiohttp.ClientSession() as session:
            tasks = [
                fetch_fred_series(session, 'DGS2'),   # 2-Year
                fetch_fred_series(session, 'DGS10'),  # 10-Year
                fetch_fred_series(session, 'DGS30'),  # 30-Year
                fetch_fred_series(session, 'T10Y2Y'), # 2s10s Spread
            ]
            results = await asyncio.gather(*tasks)
            return results

    try:
        dgs2, dgs10, dgs30, curve = asyncio.run(fetch_all_yields())

        result = {
            'dgs2': {'value': dgs2, 'unit': '%', 'series': 'DGS2'},
            'dgs10': {'value': dgs10, 'unit': '%', 'series': 'DGS10'},
            'dgs30': {'value': dgs30, 'unit': '%', 'series': 'DGS30'},
            'yield_curve_2s10s': {'value': curve, 'unit': '%', 'series': 'T10Y2Y'},
            'source': 'FRED API (US Treasury)',
            'timestamp': datetime.now().isoformat()
        }

        set_cached_data(cache_key, result)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/swing-dashboard/forex', methods=['GET'])
def get_forex_rates():
    """
    Get forex rates from Yahoo Finance via yfinance.
    Free and unlimited - no API key required.
    """
    cache_key = 'forex_rates'
    cached = get_cached_data(cache_key)
    if cached:
        return jsonify(cached)

    try:
        rates = fetch_forex_data()

        result = {
            'dxy': rates.get('dxy', {}),
            'eurusd': rates.get('eurusd', {}),
            'usdjpy': rates.get('usdjpy', {}),
            'gbpusd': rates.get('gbpusd', {}),
            'usdcad': rates.get('usdcad', {}),
            'audusd': rates.get('audusd', {}),
            'nzdusd': rates.get('nzdusd', {}),
            'usdchf': rates.get('usdchf', {}),
            'source': 'Yahoo Finance (yfinance)',
            'timestamp': datetime.now().isoformat()
        }

        set_cached_data(cache_key, result)
        return jsonify(result)
    except Exception as e:
        print(f"Forex endpoint error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/swing-dashboard/commodities', methods=['GET'])
def get_commodities():
    """
    Get commodity prices via yfinance ETFs.
    Free and unlimited.
    """
    cache_key = 'commodities'
    cached = get_cached_data(cache_key)
    if cached:
        return jsonify(cached)

    symbols = [
        'GLD',   # Gold
        'SLV',   # Silver
        'USO',   # Oil
        'COPX',  # Copper
        'UNG',   # Natural Gas
        'DBA'    # Agriculture
    ]

    data = fetch_yfinance_data(symbols)

    result = {
        'gold': data.get('GLD', {}),
        'silver': data.get('SLV', {}),
        'oil': data.get('USO', {}),
        'copper': data.get('COPX', {}),
        'natural_gas': data.get('UNG', {}),
        'agriculture': data.get('DBA', {}),
        'source': 'Yahoo Finance (ETF proxies)',
        'timestamp': datetime.now().isoformat()
    }

    set_cached_data(cache_key, result)
    return jsonify(result)


@app.route('/api/swing-dashboard/sector-rotation', methods=['GET'])
def get_sector_rotation():
    """
    Get sector rotation data via sector ETFs.
    Uses yfinance - free and unlimited.
    """
    cache_key = 'sector_rotation'
    cached = get_cached_data(cache_key)
    if cached:
        return jsonify(cached)

    sectors = {
        'XLK': 'Technology',
        'XLF': 'Financials',
        'XLE': 'Energy',
        'XLV': 'Healthcare',
        'XLI': 'Industrials',
        'XLP': 'Consumer Staples',
        'XLY': 'Consumer Discretionary',
        'XLU': 'Utilities',
        'XLB': 'Materials',
        'XLRE': 'Real Estate',
        'XLC': 'Communications'
    }

    data = fetch_yfinance_data(list(sectors.keys()))

    # Calculate relative strength vs SPY
    spy_data = fetch_yfinance_data(['SPY'])
    spy_return = spy_data['SPY'].get('change_pct', 0) if 'SPY' in spy_data else 0

    sector_data = []
    for etf, sector_name in sectors.items():
        if etf in data:
            etf_return = data[etf].get('change_pct', 0)
            relative_strength = etf_return - spy_return

            # Determine recommendation
            if relative_strength > 2:
                recommendation = 'BUY'
            elif relative_strength < -2:
                recommendation = 'SELL'
            else:
                recommendation = 'HOLD'

            sector_data.append({
                'sector': sector_name,
                'etf': etf,
                'performance_1w': data[etf].get('change_pct'),
                'performance_1m': None,  # Would require historical data
                'relative_strength': round(relative_strength, 2),
                'recommendation': recommendation
            })

    result = {
        'sectors': sector_data,
        'benchmark': 'SPY',
        'benchmark_return': spy_return,
        'source': 'Yahoo Finance',
        'timestamp': datetime.now().isoformat()
    }

    set_cached_data(cache_key, result)
    return jsonify(result)


@app.route('/api/swing-dashboard/market-health', methods=['GET'])
def get_market_health():
    """
    Calculate comprehensive market health score.
    Aggregates data from multiple indicators.
    """
    cache_key = 'market_health'
    cached = get_cached_data(cache_key)
    if cached:
        return jsonify(cached)

    # Fetch key indicators
    spy_data = fetch_yfinance_data(['SPY', '^VIX'])

    # Simple health score calculation
    # In production, this would be much more sophisticated
    spy_return = spy_data.get('SPY', {}).get('change_pct', 0)
    vix_level = spy_data.get('^VIX', {}).get('price', 20)

    # Score components (0-100 scale)
    equity_score = min(100, max(0, 50 + spy_return * 5))  # Equity performance
    volatility_score = min(100, max(0, 100 - vix_level))  # Lower VIX = better

    # Overall health score (simple average)
    health_score = (equity_score + volatility_score) / 2

    # Determine status
    if health_score >= 70:
        status = 'Strong Bull Market'
    elif health_score >= 50:
        status = 'Neutral Market'
    elif health_score >= 30:
        status = 'Cautious Bear Market'
    else:
        status = 'Strong Bear Market'

    result = {
        'health_score': round(health_score, 1),
        'status': status,
        'components': {
            'equity_score': round(equity_score, 1),
            'volatility_score': round(volatility_score, 1)
        },
        'timestamp': datetime.now().isoformat()
    }

    set_cached_data(cache_key, result)
    return jsonify(result)


@app.route('/api/fred/series/observations', methods=['GET'])
def fred_proxy():
    """
    FRED API proxy endpoint for Capital Flow Dashboard.
    Proxies requests to FRED API with automatic API key injection.
    """
    series_id = request.args.get('series_id')
    limit = request.args.get('limit', '1')
    sort_order = request.args.get('sort_order', 'desc')

    if not series_id:
        return jsonify({'error': 'series_id parameter required'}), 400

    cache_key = f'fred_{series_id}_{limit}_{sort_order}'
    cached = get_cached_data(cache_key)
    if cached:
        return jsonify(cached)

    try:
        # Build FRED API URL with API key
        params = {
            'series_id': series_id,
            'api_key': FRED_API_KEY,
            'file_type': 'json',
            'limit': limit,
            'sort_order': sort_order
        }

        response = requests.get(FRED_BASE_URL, params=params)

        if response.status_code == 200:
            data = response.json()
            set_cached_data(cache_key, data)
            return jsonify(data)
        else:
            return jsonify({
                'error': 'FRED API request failed',
                'status_code': response.status_code
            }), response.status_code

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/swing-dashboard/health', methods=['GET'])
def health_check():
    """API health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'Swing Dashboard API',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/yahoo/quote', methods=['GET'])
def get_yahoo_quote():
    """
    MULTI-SOURCE QUOTE ENDPOINT with cascading fallback.

    Priority order:
    1. Polygon.io (Premium, real-time) ← FIRST PRIORITY
    2. Yahoo Finance (Free, unlimited)   ← FALLBACK
    3. FRED (Economic data only)         ← FALLBACK

    Accepts single symbol or comma-separated list.
    Example: /api/yahoo/quote?symbols=AAPL,MSFT,^GSPC
    """
    symbols_param = request.args.get('symbols', '')
    if not symbols_param:
        return jsonify({'error': 'Missing symbols parameter'}), 400

    symbols = [s.strip() for s in symbols_param.split(',')]

    # Create cache key from symbols
    cache_key = f'quote_{symbols_param}'
    cached = get_cached_data(cache_key)
    if cached:
        return jsonify(cached)

    # PRIORITY 1: Try Polygon.io (if configured)
    data = {}
    if HAS_POLYGON:
        print(f"🔹 Trying Polygon.io for {len(symbols)} symbols...")
        data = fetch_polygon_data(symbols)

        # Track what we got from Polygon
        polygon_success = [s for s in symbols if s in data and data[s].get('price') is not None]
        if polygon_success:
            print(f"✅ Polygon.io: Got {len(polygon_success)}/{len(symbols)} symbols")

    # PRIORITY 2: Fallback to Yahoo Finance for missing symbols
    missing_symbols = [s for s in symbols if s not in data or data[s].get('price') is None]
    if missing_symbols:
        print(f"🔹 Falling back to Yahoo Finance for {len(missing_symbols)} symbols...")
        yahoo_data = fetch_yfinance_data(missing_symbols)
        data.update(yahoo_data)  # Merge Yahoo data into results

    result = {
        'data': data,
        'timestamp': datetime.now().isoformat(),
        'sources_used': {
            'polygon': len([s for s in data.values() if s.get('source') == 'polygon.io']),
            'yahoo': len([s for s in data.values() if s.get('source') != 'polygon.io'])
        }
    }

    set_cached_data(cache_key, result)
    return jsonify(result)


def convert_to_polygon_symbol(yahoo_symbol: str) -> str:
    """
    Convert Yahoo Finance symbol to Polygon.io format.

    Examples:
    - AAPL → AAPL (stocks remain same)
    - AUDJPY=X → C:AUDJPY (forex)
    - ^TNX → I:TNX (indices)
    - BTC-USD → X:BTCUSD (crypto)
    """
    symbol_map = {
        # Forex (Yahoo uses =X suffix, Polygon uses C: prefix)
        'AUDJPY=X': 'C:AUDJPY',
        'EURUSD=X': 'C:EURUSD',
        'GBPUSD=X': 'C:GBPUSD',
        'USDJPY=X': 'C:USDJPY',
        'AUDUSD=X': 'C:AUDUSD',

        # Indices (Yahoo uses ^ prefix, Polygon uses I: prefix)
        '^TNX': 'I:TNX',      # 10-Year Treasury
        '^VIX': 'I:VIX',      # Volatility Index
        '^SPX': 'I:SPX',      # S&P 500 Index
        '^DJI': 'I:DJI',      # Dow Jones

        # Crypto (Yahoo uses - separator, Polygon uses X: prefix)
        'BTC-USD': 'X:BTCUSD',
        'ETH-USD': 'X:ETHUSD',
    }

    return symbol_map.get(yahoo_symbol, yahoo_symbol)  # Return original if no mapping


def fetch_polygon_chart(symbol: str, interval: str = '1d', range_param: str = '5d') -> Optional[Dict]:
    """
    Fetch chart data from Polygon.io and format it like Yahoo Finance.

    Returns data in Yahoo Finance chart format for compatibility.
    """
    if not HAS_POLYGON:
        return None

    try:
        # Parse range to get number of days
        days = int(range_param.replace('d', '').replace('mo', ''))
        if 'mo' in range_param:
            days = days * 30  # Approximate months to days

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Polygon.io aggregates endpoint
        # /v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}
        url = f"{POLYGON_BASE_URL}/v2/aggs/ticker/{symbol}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        params = {'apiKey': POLYGON_API_KEY, 'adjusted': 'true', 'sort': 'asc'}

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()

            if data.get('status') == 'OK' and data.get('results'):
                results = data['results']

                # Convert to Yahoo Finance format
                timestamps = [r['t'] // 1000 for r in results]  # Convert ms to seconds
                opens = [r['o'] for r in results]
                highs = [r['h'] for r in results]
                lows = [r['l'] for r in results]
                closes = [r['c'] for r in results]
                volumes = [r['v'] for r in results]

                # Build Yahoo-compatible response
                yahoo_format = {
                    'chart': {
                        'result': [{
                            'meta': {
                                'currency': 'USD',
                                'symbol': symbol,
                                'regularMarketPrice': closes[-1] if closes else None,
                                'dataGranularity': interval,
                                'range': range_param,
                            },
                            'timestamp': timestamps,
                            'indicators': {
                                'quote': [{
                                    'open': opens,
                                    'high': highs,
                                    'low': lows,
                                    'close': closes,
                                    'volume': volumes
                                }]
                            }
                        }],
                        'error': None
                    }
                }

                print(f"✅ Polygon.io fallback success for {symbol}")
                return yahoo_format
            else:
                print(f"⚠️ Polygon.io: No results for {symbol}")
                return None
        else:
            print(f"❌ Polygon.io API error {response.status_code} for {symbol}")
            return None

    except Exception as e:
        print(f"❌ Polygon.io chart fetch error for {symbol}: {e}")
        return None


def fetch_yfinance_chart(symbol: str, interval: str = '1d', range_param: str = '5d') -> Optional[Dict]:
    """
    Fetch chart data using yfinance library (direct scraping - ultimate fallback).
    Bypasses Yahoo Finance API rate limits.

    Returns data in Yahoo Finance chart format for compatibility.
    """
    try:
        # Parse period from range_param
        period_map = {
            '1d': '1d', '5d': '5d', '1mo': '1mo', '3mo': '3mo',
            '6mo': '6mo', '1y': '1y', '2y': '2y', '5y': '5y',
            '10y': '10y', 'ytd': 'ytd', 'max': 'max'
        }
        period = period_map.get(range_param, range_param)

        # Fetch data using yfinance
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)

        if hist.empty:
            print(f"⚠️ yfinance: No data for {symbol}")
            return None

        # Convert to lists for JSON serialization
        timestamps = [int(idx.timestamp()) for idx in hist.index]
        opens = hist['Open'].tolist()
        highs = hist['High'].tolist()
        lows = hist['Low'].tolist()
        closes = hist['Close'].tolist()
        volumes = hist['Volume'].tolist()

        # Build Yahoo Finance API compatible response
        yahoo_format = {
            'chart': {
                'result': [{
                    'meta': {
                        'currency': 'USD',
                        'symbol': symbol,
                        'regularMarketPrice': closes[-1] if closes else None,
                        'dataGranularity': interval,
                        'range': range_param,
                    },
                    'timestamp': timestamps,
                    'indicators': {
                        'quote': [{
                            'open': opens,
                            'high': highs,
                            'low': lows,
                            'close': closes,
                            'volume': volumes
                        }]
                    }
                }],
                'error': None
            }
        }

        print(f"✅ yfinance library fallback success for {symbol}")
        return yahoo_format

    except Exception as e:
        print(f"❌ yfinance library error for {symbol}: {e}")
        return None


@app.route('/api/yahoo/chart/<symbol>', methods=['GET'])
def get_yahoo_chart(symbol):
    """
    Yahoo Finance chart endpoint with multi-tier fallback - proxy to avoid CORS.
    Example: /api/yahoo/chart/AAPL?interval=1d&range=5d

    Fallback Strategy:
    1. Try Yahoo Finance API (free, unlimited but rate-limited)
    2. If Yahoo returns 429 (rate limit), try Polygon.io (paid tier)
    3. If Polygon fails, try yfinance Python library (direct scraping, unlimited)
    4. If all fail, return error
    """
    interval = request.args.get('interval', '1d')
    range_param = request.args.get('range', '5d')

    cache_key = f'yahoo_chart_{symbol}_{interval}_{range_param}'
    cached = get_cached_data(cache_key)
    if cached:
        return jsonify(cached)

    # Try Yahoo Finance API first
    try:
        url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}'
        params = {'interval': interval, 'range': range_param}
        response = requests.get(url, params=params, timeout=10)

        if response.ok:
            data = response.json()
            set_cached_data(cache_key, data)
            return jsonify(data)
        elif response.status_code == 429:
            # Yahoo hit rate limit - try Polygon.io fallback
            if HAS_POLYGON:
                print(f"⚠️ Yahoo 429 for {symbol}, trying Polygon.io fallback...")
                polygon_symbol = convert_to_polygon_symbol(symbol)
                polygon_data = fetch_polygon_chart(polygon_symbol, interval, range_param)

                if polygon_data:
                    set_cached_data(cache_key, polygon_data)
                    return jsonify(polygon_data)

            # Polygon failed or not available - try yfinance library (final fallback)
            print(f"⚠️ Polygon failed for {symbol}, trying yfinance library...")
            yfinance_data = fetch_yfinance_chart(symbol, interval, range_param)

            if yfinance_data:
                set_cached_data(cache_key, yfinance_data)
                return jsonify(yfinance_data)
            else:
                return jsonify({'error': f'All data sources failed for {symbol}'}), 500
        else:
            return jsonify({'error': f'Yahoo API error: {response.status_code}'}), 500
    except Exception as e:
        # On exception, try Polygon.io and yfinance fallbacks
        if HAS_POLYGON:
            print(f"⚠️ Yahoo exception for {symbol}, trying Polygon.io fallback...")
            polygon_symbol = convert_to_polygon_symbol(symbol)
            polygon_data = fetch_polygon_chart(polygon_symbol, interval, range_param)

            if polygon_data:
                set_cached_data(cache_key, polygon_data)
                return jsonify(polygon_data)

        # Final fallback: yfinance library
        print(f"⚠️ Trying yfinance library as final fallback for {symbol}...")
        yfinance_data = fetch_yfinance_chart(symbol, interval, range_param)

        if yfinance_data:
            set_cached_data(cache_key, yfinance_data)
            return jsonify(yfinance_data)

        return jsonify({'error': str(e)}), 500


@app.route('/api/fred/<path:fred_path>', methods=['GET'])
def get_fred_data(fred_path):
    """
    Universal FRED API proxy - handles any FRED endpoint.
    Example: /api/fred/series/observations?series_id=GDP&api_key=...
    """
    if not FRED_API_KEY:
        return jsonify({'error': 'FRED API key not configured'}), 500

    # Build cache key from path and params
    query_string = request.query_string.decode('utf-8')
    cache_key = f'fred_{fred_path}_{query_string}'
    cached = get_cached_data(cache_key)
    if cached:
        return jsonify(cached)

    try:
        # Forward request to FRED API
        url = f'https://api.stlouisfed.org/fred/{fred_path}'

        # Get all query parameters and add API key
        params = dict(request.args)
        params['api_key'] = FRED_API_KEY
        params['file_type'] = 'json'

        response = requests.get(url, params=params, timeout=10)

        if response.ok:
            data = response.json()
            set_cached_data(cache_key, data)
            return jsonify(data)
        else:
            return jsonify({'error': f'FRED API error: {response.status_code}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/alpha-vantage/query', methods=['GET'])
def get_alpha_vantage_query():
    """
    Universal Alpha Vantage query endpoint - proxy to avoid CORS.
    Example: /api/alpha-vantage/query?function=GLOBAL_QUOTE&symbol=AAPL
    """
    if not ALPHA_VANTAGE_API_KEY:
        return jsonify({'error': 'Alpha Vantage API key not configured'}), 500

    # Build cache key from query params
    query_string = request.query_string.decode('utf-8')
    cache_key = f'alpha_vantage_query_{query_string}'
    cached = get_cached_data(cache_key)
    if cached:
        return jsonify(cached)

    try:
        url = 'https://www.alphavantage.co/query'

        # Forward all query params and add API key
        params = dict(request.args)
        params['apikey'] = ALPHA_VANTAGE_API_KEY

        response = requests.get(url, params=params, timeout=10)

        if response.ok:
            data = response.json()
            set_cached_data(cache_key, data)
            return jsonify(data)
        else:
            return jsonify({'error': f'Alpha Vantage API error: {response.status_code}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/recession-probability', methods=['GET'])
def get_recession_probability():
    """
    Probabilistic Recession Model - NY Fed Methodology

    Uses logistic regression on the 10Y-3M Treasury yield spread to calculate
    recession probability 12 months ahead.

    Formula: P(Recession) = 1 / (1 + e^-(β₀ + β₁ × Spread))
    Where:
        β₀ = -0.5203 (model intercept)
        β₁ = -0.6501 (spread coefficient)
        Spread = T10Y3M (10-Year minus 3-Month Treasury rate)

    Returns:
        {
            'spread': float,  # Current 10Y-3M spread (%)
            'probability': float,  # Recession probability (0-100%)
            'risk_level': str,  # LOW, MODERATE, ELEVATED, HIGH, CRITICAL
            'risk_emoji': str,  # Visual indicator
            'description': str  # Risk level description
        }
    """
    cache_key = 'recession_probability'
    cached = get_cached_data(cache_key)
    if cached:
        return jsonify(cached)

    try:
        # Model parameters (trained on 1985-2024 data)
        BETA_0 = -0.5203  # Intercept
        BETA_1 = -0.6501  # Coefficient for spread

        # Fetch T10Y3M from FRED
        if not FRED_API_KEY:
            return jsonify({'error': 'FRED API key not configured'}), 500

        fred_url = 'https://api.stlouisfed.org/fred/series/observations'
        params = {
            'series_id': 'T10Y3M',
            'api_key': FRED_API_KEY,
            'file_type': 'json',
            'sort_order': 'desc',
            'limit': 1  # Get most recent value only
        }

        response = requests.get(fred_url, params=params, timeout=10)

        if not response.ok:
            return jsonify({'error': f'FRED API error: {response.status_code}'}), 500

        fred_data = response.json()

        if 'observations' not in fred_data or len(fred_data['observations']) == 0:
            return jsonify({'error': 'No T10Y3M data available from FRED'}), 500

        # Extract spread value
        spread_str = fred_data['observations'][0]['value']

        # Handle missing data (represented as '.')
        if spread_str == '.':
            return jsonify({'error': 'T10Y3M data currently unavailable'}), 500

        spread = float(spread_str)

        # Calculate log-odds: β₀ + β₁ × Spread
        log_odds = BETA_0 + (BETA_1 * spread)

        # Calculate probability using logistic function: 1 / (1 + e^-log_odds)
        import math
        probability = 1 / (1 + math.exp(-log_odds))

        # Convert to percentage
        probability_pct = probability * 100

        # Determine risk level based on probability
        if probability_pct < 15:
            risk_level = 'LOW'
            risk_emoji = '🟢'
            description = 'Normal equity allocation'
        elif probability_pct < 30:
            risk_level = 'MODERATE'
            risk_emoji = '🟡'
            description = 'Begin monitoring closely'
        elif probability_pct < 50:
            risk_level = 'ELEVATED'
            risk_emoji = '🟠'
            description = 'Defensive positioning recommended'
        elif probability_pct < 70:
            risk_level = 'HIGH'
            risk_emoji = '🔴'
            description = 'Reduce risk exposure'
        else:
            risk_level = 'CRITICAL'
            risk_emoji = '⚫'
            description = 'Maximum defensive stance'

        result = {
            'spread': round(spread, 4),
            'probability': round(probability_pct, 2),
            'risk_level': risk_level,
            'risk_emoji': risk_emoji,
            'description': description,
            'last_updated': fred_data['observations'][0]['date']
        }

        # Cache for 15 minutes (standard cache duration)
        set_cached_data(cache_key, result)

        print(f"✅ Recession model: {spread:.2f}% spread → {probability_pct:.1f}% probability ({risk_level})")

        return jsonify(result)

    except Exception as e:
        print(f"❌ Recession probability calculation error: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("=" * 80)
    print("SPARTAN SWING DASHBOARD API SERVER")
    print("=" * 80)
    print("\nStarting server on http://localhost:5002")
    print("\nEndpoints:")
    print("  - GET /api/swing-dashboard/market-indices")
    print("  - GET /api/swing-dashboard/volatility")
    print("  - GET /api/swing-dashboard/credit-spreads")
    print("  - GET /api/swing-dashboard/treasury-yields")
    print("  - GET /api/swing-dashboard/forex")
    print("  - GET /api/swing-dashboard/commodities")
    print("  - GET /api/swing-dashboard/sector-rotation")
    print("  - GET /api/swing-dashboard/market-health")
    print("  - GET /api/yahoo/quote?symbols=AAPL,MSFT  (Generic proxy)")
    print("\nData Sources:")
    print("  - yfinance (FREE, unlimited)")
    print("  - FRED API (FREE, 120 req/min)")
    print("  - Alpha Vantage (FREE, 25 req/day)")
    print("  - ExchangeRate-API (FREE, 1,500 req/month)")
    print("\n" + "=" * 80)

    app.run(host='0.0.0.0', port=5002, debug=False)
