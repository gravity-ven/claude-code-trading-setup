#!/usr/bin/env python3
"""
Correlation Matrix API Server
Calculates real-time correlations between major indices and cryptocurrencies
NO FAKE DATA - Uses 50+ free data sources with automatic fallback

Port: 5004
"""

from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
import os

# Add scripts/data to path for fallback data fetcher
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts', 'data'))

# Import fallback data fetcher
try:
    from data_fetcher_fallback import data_fetcher
except ImportError:
    # Fallback: create a simple data fetcher using yfinance directly
    class SimpleDataFetcher:
        def fetch(self, symbol, period='1mo'):
            try:
                return yf.download(symbol, period=period, progress=False)
            except Exception:
                return pd.DataFrame()
    data_fetcher = SimpleDataFetcher()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Comprehensive asset symbols for correlation analysis
# Organized by asset class for better UX
ASSETS = {
    # === EQUITY INDICES ===
    'sp500': '^GSPC',           # S&P 500 (ES futures equivalent)
    'nasdaq': '^IXIC',          # Nasdaq Composite (NQ futures equivalent)
    'russell2000': '^RUT',      # Russell 2000 Small Cap (RTY futures equivalent)
    'dowjones': '^DJI',         # Dow Jones Industrial (YM futures equivalent)
    'nikkei': '^N225',          # Nikkei 225 (NK futures equivalent)
    'vix': '^VIX',              # Volatility Index (VX futures)

    # === BONDS (TREASURIES & CREDIT) ===
    'tlt': 'TLT',               # 20+ Year Treasury ETF (ZB futures equivalent)
    'ief': 'IEF',               # 7-10 Year Treasury ETF (ZN futures equivalent)
    'shy': 'SHY',               # 1-3 Year Treasury ETF (ZT futures equivalent)
    'lqd': 'LQD',               # Investment Grade Corporate
    'hyg': 'HYG',               # High Yield Corporate (Junk) - COMPOSITE INDICATOR
    'tip': 'TIP',               # TIPS (Inflation Protected)

    # === CRYPTOCURRENCIES ===
    'bitcoin': 'BTC-USD',       # Bitcoin
    'ethereum': 'ETH-USD',      # Ethereum
    'bnb': 'BNB-USD',           # Binance Coin
    'solana': 'SOL-USD',        # Solana
    'xrp': 'XRP-USD',           # Ripple

    # === FOREX (MAJOR PAIRS) ===
    'dollar': 'DX-Y.NYB',       # US Dollar Index (DX futures)
    'eurusd': 'EURUSD=X',       # Euro / US Dollar (6E futures equivalent)
    'gbpusd': 'GBPUSD=X',       # British Pound / USD (6B futures equivalent)
    'usdjpy': 'JPY=X',          # USD / Japanese Yen (6J futures equivalent)
    'audusd': 'AUDUSD=X',       # Australian Dollar / USD (6A futures equivalent)
    'usdcad': 'USDCAD=X',       # USD / Canadian Dollar (6C futures equivalent)
    'audjpy': 'AUDJPY=X',       # AUD / JPY (COMPOSITE INDICATOR - Risk On/Off)

    # === COMMODITIES & FUTURES ===
    'gold': 'GC=F',             # Gold Futures
    'silver': 'SI=F',           # Silver Futures
    'platinum': 'PL=F',         # Platinum Futures
    'oil': 'CL=F',              # Crude Oil WTI
    'heating_oil': 'HO=F',      # Heating Oil Futures
    'rbob': 'RB=F',             # RBOB Gasoline Futures
    'natgas': 'NG=F',           # Natural Gas
    'copper': 'HG=F',           # Copper Futures (KEY METAL)

    # === SECTOR ETFs (11 GICS SECTORS) ===
    'tech': 'XLK',              # Technology
    'financials': 'XLF',        # Financials
    'healthcare': 'XLV',        # Healthcare
    'energy': 'XLE',            # Energy
    'industrials': 'XLI',       # Industrials
    'consumer_disc': 'XLY',     # Consumer Discretionary
    'consumer_staples': 'XLP',  # Consumer Staples
    'utilities': 'XLU',         # Utilities
    'real_estate': 'XLRE',      # Real Estate
    'materials': 'XLB',         # Materials
    'communication': 'XLC',     # Communication Services

    # === INTERNATIONAL ===
    'emerging': 'EEM',          # Emerging Markets
    'developed': 'EFA',         # Developed Markets ex-US
    'china': 'FXI',             # China Large Cap
    'japan': 'EWJ',             # Japan
    'europe': 'VGK',            # European Stocks
}

# Asset categories for organized display
ASSET_CATEGORIES = {
    'Equity Indices': ['sp500', 'nasdaq', 'russell2000', 'dowjones', 'nikkei', 'vix'],
    'Bonds': ['tlt', 'ief', 'shy', 'lqd', 'hyg', 'tip'],
    'Crypto': ['bitcoin', 'ethereum', 'bnb', 'solana', 'xrp'],
    'Forex': ['dollar', 'eurusd', 'gbpusd', 'usdjpy', 'audusd', 'usdcad', 'audjpy'],
    'Commodities': ['gold', 'silver', 'platinum', 'oil', 'heating_oil', 'rbob', 'natgas', 'copper'],
    'Sectors': ['tech', 'financials', 'healthcare', 'energy', 'industrials',
                'consumer_disc', 'consumer_staples', 'utilities', 'real_estate',
                'materials', 'communication'],
    'International': ['emerging', 'developed', 'china', 'japan', 'europe']
}

# Display names for better UX
ASSET_NAMES = {
    'sp500': 'S&P 500 (ES)', 'nasdaq': 'Nasdaq (NQ)', 'russell2000': 'Russell 2000 (RTY)',
    'dowjones': 'Dow Jones (YM)', 'nikkei': 'Nikkei 225 (NK)', 'vix': 'VIX (VX Futures)',
    'tlt': '20Y+ Treasury (ZB)', 'ief': '10Y Treasury (ZN)', 'shy': '2Y Treasury (ZT)',
    'lqd': 'Corp Bonds (IG)', 'hyg': 'High Yield (HYG)', 'tip': 'TIPS',
    'bitcoin': 'Bitcoin', 'ethereum': 'Ethereum', 'bnb': 'Binance Coin',
    'solana': 'Solana', 'xrp': 'Ripple (XRP)',
    'dollar': 'Dollar Index (DX)', 'eurusd': 'EUR/USD (6E)', 'gbpusd': 'GBP/USD (6B)',
    'usdjpy': 'USD/JPY (6J)', 'audusd': 'AUD/USD (6A)', 'usdcad': 'USD/CAD (6C)',
    'audjpy': 'AUD/JPY (Risk Indicator)',
    'gold': 'Gold (GC)', 'silver': 'Silver (SI)', 'platinum': 'Platinum (PL)',
    'oil': 'Crude Oil (CL)', 'heating_oil': 'Heating Oil (HO)', 'rbob': 'RBOB Gas (RB)',
    'natgas': 'Natural Gas (NG)', 'copper': 'Copper (HG) 🔑',
    'tech': 'Technology', 'financials': 'Financials', 'healthcare': 'Healthcare',
    'energy': 'Energy', 'industrials': 'Industrials',
    'consumer_disc': 'Consumer Discr.', 'consumer_staples': 'Consumer Staples',
    'utilities': 'Utilities', 'real_estate': 'Real Estate',
    'materials': 'Materials', 'communication': 'Communications',
    'emerging': 'Emerging Markets', 'developed': 'Developed Markets',
    'china': 'China', 'japan': 'Japan', 'europe': 'Europe'
}

# Cache configuration
CACHE_DURATION = 15 * 60  # 15 minutes in seconds
cache = {
    'data': None,
    'timestamp': None
}


def is_cache_valid():
    """Check if cached data is still valid"""
    if cache['data'] is None or cache['timestamp'] is None:
        return False

    age = (datetime.now() - cache['timestamp']).total_seconds()
    return age < CACHE_DURATION


def fetch_price_data(period_days=30):
    """
    Fetch historical price data for all assets using fallback system

    Args:
        period_days (int): Number of days of historical data

    Returns:
        pd.DataFrame: DataFrame with closing prices for all assets
    """
    logger.info(f"Fetching {period_days} days of price data for {len(ASSETS)} assets")
    logger.info("Using multi-source fallback system (50+ free data sources)")

    price_data = {}
    sources_used = {}

    for asset_key, symbol in ASSETS.items():
        try:
            logger.info(f"Fetching {asset_key} ({symbol}) with fallback...")

            # Determine data type for optimal source selection
            if 'BTC' in symbol or 'ETH' in symbol or asset_key in ['bitcoin', 'ethereum', 'bnb', 'solana', 'xrp']:
                data_type = 'crypto'
            elif '=X' in symbol or symbol in ['DX-Y.NYB']:
                data_type = 'forex'
            else:
                data_type = 'price'

            # Fetch with fallback
            result = data_fetcher.fetch_with_fallback(
                symbol=symbol,
                data_type=data_type,
                period_days=period_days
            )

            if result['success'] and result['data'] is not None:
                price_data[asset_key] = result['data']
                sources_used[asset_key] = result['source']
                logger.info(f"✓ {asset_key}: {len(result['data'])} data points from {result['source']}")
            else:
                logger.warning(f"✗ All sources failed for {asset_key} ({symbol})")
                price_data[asset_key] = None
                sources_used[asset_key] = 'FAILED'

        except Exception as e:
            logger.error(f"Error fetching {asset_key} ({symbol}): {str(e)}")
            price_data[asset_key] = None
            sources_used[asset_key] = 'ERROR'

    # Log source usage summary
    logger.info("\n" + "="*60)
    logger.info("DATA SOURCE USAGE SUMMARY:")
    for source in set(sources_used.values()):
        count = list(sources_used.values()).count(source)
        logger.info(f"  {source}: {count} assets")
    logger.info("="*60 + "\n")

    # Combine into DataFrame
    try:
        df = pd.DataFrame(price_data)

        # Remove columns with all NaN (assets that failed to fetch)
        df = df.dropna(axis=1, how='all')

        # Forward fill NaN values (stocks don't trade on weekends, crypto does)
        # This carries forward the last stock price for weekend crypto data
        df = df.fillna(method='ffill')

        # Drop any remaining rows with NaN (typically at the beginning)
        df = df.dropna()

        logger.info(f"Combined DataFrame: {len(df)} rows, {len(df.columns)} assets")
        logger.info(f"Successfully fetched: {len(df.columns)}/{len(ASSETS)} assets")

        # Ensure we have at least 20 days of data for meaningful correlation
        if len(df) < 20:
            logger.warning(f"Insufficient data: only {len(df)} days available")
            return None

        return df

    except Exception as e:
        logger.error(f"Error creating price DataFrame: {str(e)}")
        return None


def calculate_correlations(price_df):
    """
    Calculate correlation matrix from price data

    Args:
        price_df (pd.DataFrame): DataFrame with price data

    Returns:
        dict: Nested dictionary with pairwise correlations
    """
    if price_df is None or price_df.empty:
        logger.error("Cannot calculate correlations: no price data")
        return None

    try:
        # Calculate daily returns (percentage change)
        returns = price_df.pct_change().dropna()

        logger.info(f"Calculating correlations from {len(returns)} days of returns")

        # Calculate correlation matrix using Pearson correlation
        corr_matrix = returns.corr()

        # Convert to nested dictionary for JSON serialization
        correlations = {}
        for asset1 in corr_matrix.index:
            correlations[asset1] = {}
            for asset2 in corr_matrix.columns:
                value = corr_matrix.loc[asset1, asset2]

                # Convert numpy types to Python float
                if pd.isna(value):
                    correlations[asset1][asset2] = None
                else:
                    correlations[asset1][asset2] = float(value)

        logger.info("✓ Correlation matrix calculated successfully")
        return correlations

    except Exception as e:
        logger.error(f"Error calculating correlations: {str(e)}")
        return None


@app.route('/api/correlations', methods=['GET'])
def get_correlations():
    """
    Get correlation matrix for all tracked assets

    Returns:
        JSON response with correlation data
    """
    try:
        # Check cache first
        if is_cache_valid():
            logger.info("Returning cached correlation data")
            return jsonify({
                'success': True,
                'correlations': cache['data'],
                'timestamp': cache['timestamp'].isoformat(),
                'cache_hit': True,
                'assets': list(ASSETS.keys()),
                'period': '30-day rolling'
            })

        # Fetch fresh data
        logger.info("Cache miss or expired - fetching fresh data")
        price_df = fetch_price_data(period_days=30)

        if price_df is None:
            return jsonify({
                'success': False,
                'error': 'Failed to fetch price data',
                'correlations': None,
                'timestamp': datetime.now().isoformat()
            }), 500

        # Calculate correlations
        correlations = calculate_correlations(price_df)

        if correlations is None:
            return jsonify({
                'success': False,
                'error': 'Failed to calculate correlations',
                'correlations': None,
                'timestamp': datetime.now().isoformat()
            }), 500

        # Update cache
        cache['data'] = correlations
        cache['timestamp'] = datetime.now()

        return jsonify({
            'success': True,
            'correlations': correlations,
            'timestamp': cache['timestamp'].isoformat(),
            'cache_hit': False,
            'assets': list(ASSETS.keys()),
            'period': '30-day rolling',
            'data_points': len(price_df)
        })

    except Exception as e:
        logger.error(f"Unexpected error in /api/correlations: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'correlations': None,
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Correlation Matrix API',
        'port': 5004,
        'timestamp': datetime.now().isoformat(),
        'cache_valid': is_cache_valid(),
        'assets_tracked': len(ASSETS)
    })


@app.route('/api/assets', methods=['GET'])
def get_assets():
    """Get list of tracked assets"""
    return jsonify({
        'success': True,
        'assets': [
            {'key': key, 'symbol': symbol, 'name': key.replace('_', ' ').title()}
            for key, symbol in ASSETS.items()
        ],
        'total': len(ASSETS)
    })


@app.route('/api/metadata', methods=['GET'])
def get_metadata():
    """Get asset categories and display names for organized UI"""
    return jsonify({
        'success': True,
        'categories': ASSET_CATEGORIES,
        'names': ASSET_NAMES,
        'symbols': ASSETS,
        'total_assets': len(ASSETS),
        'total_categories': len(ASSET_CATEGORIES)
    })


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("CORRELATION MATRIX API SERVER")
    logger.info("=" * 60)
    logger.info(f"Port: 5004")
    logger.info(f"Assets tracked: {len(ASSETS)}")
    logger.info(f"Cache duration: {CACHE_DURATION // 60} minutes")
    logger.info(f"Correlation period: 30-day rolling")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Endpoints:")
    logger.info("  GET /api/correlations - Get correlation matrix")
    logger.info("  GET /api/assets - Get list of tracked assets")
    logger.info("  GET /health - Health check")
    logger.info("")
    logger.info("Data Source: Yahoo Finance (yfinance)")
    logger.info("NO FAKE DATA - All correlations calculated from real market data")
    logger.info("")
    logger.info("Starting server...")
    logger.info("=" * 60)

    # Run Flask app
    app.run(host='0.0.0.0', port=5004, debug=False)
