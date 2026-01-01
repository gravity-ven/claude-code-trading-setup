#!/usr/bin/env python3
"""
GARP (Growth at Reasonable Price) Stock Screener API
====================================================

Screens stocks based on GARP methodology using real financial data.

GARP Metrics:
- P/E Ratio (Price-to-Earnings): Lower is better (< 20 ideal)
- PEG Ratio (P/E to Growth): < 1.0 is excellent, < 2.0 is good
- Revenue Growth: YoY revenue growth % (higher is better)
- Earnings Growth: YoY earnings growth % (higher is better)
- ROE (Return on Equity): > 15% is good
- Debt-to-Equity: < 1.0 is good

Data Sources:
- yfinance: Financial metrics, historical data (free, unlimited)

Author: Spartan Research Station
Version: 1.0.0
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import numpy as np

app = Flask(__name__)
CORS(app)

# Cache configuration
CACHE = {}
CACHE_DURATION = timedelta(hours=4)  # 4-hour cache for fundamental data

# Stock universe for GARP screening (major US stocks across sectors)
STOCK_UNIVERSE = {
    'Technology': ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AMD', 'CRM', 'ADBE', 'INTC', 'CSCO', 'ORCL', 'AVGO'],
    'Healthcare': ['JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'DHR', 'LLY', 'MRK', 'ABT', 'CVS'],
    'Financial': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'SCHW', 'USB', 'PNC'],
    'Consumer': ['AMZN', 'WMT', 'HD', 'PG', 'KO', 'PEP', 'COST', 'NKE', 'MCD', 'SBUX', 'TGT'],
    'Industrial': ['CAT', 'BA', 'HON', 'UNP', 'GE', 'MMM', 'LMT', 'RTX', 'DE'],
    'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'PSX', 'VLO', 'MPC', 'OXY'],
    'Materials': ['LIN', 'APD', 'ECL', 'DD', 'DOW', 'NEM', 'FCX'],
    'Utilities': ['NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'SRE'],
    'Real Estate': ['AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'DLR', 'O'],
    'Communication': ['T', 'VZ', 'CMCSA', 'DIS', 'NFLX', 'TMUS']
}


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


def calculate_garp_score(metrics: Dict) -> Dict:
    """
    Calculate GARP quality score (0-100) based on multiple factors.

    Scoring:
    - PEG Ratio: 30 points (< 1.0 = 30, 1.0-2.0 = 15, > 2.0 = 0)
    - P/E Ratio: 20 points (< 15 = 20, 15-25 = 10, > 25 = 0)
    - Revenue Growth: 20 points (> 20% = 20, 10-20% = 10, < 10% = 0)
    - Earnings Growth: 15 points (> 20% = 15, 10-20% = 8, < 10% = 0)
    - ROE: 10 points (> 20% = 10, 10-20% = 5, < 10% = 0)
    - Debt/Equity: 5 points (< 0.5 = 5, 0.5-1.0 = 3, > 1.0 = 0)
    """
    score = 0
    breakdown = {}

    # PEG Ratio scoring (30 points)
    peg = metrics.get('peg_ratio')
    if peg and peg > 0:
        if peg < 1.0:
            score += 30
            breakdown['peg'] = 30
        elif peg < 2.0:
            score += 15
            breakdown['peg'] = 15
        else:
            breakdown['peg'] = 0
    else:
        breakdown['peg'] = 0

    # P/E Ratio scoring (20 points)
    pe = metrics.get('pe_ratio')
    if pe and pe > 0:
        if pe < 15:
            score += 20
            breakdown['pe'] = 20
        elif pe < 25:
            score += 10
            breakdown['pe'] = 10
        else:
            breakdown['pe'] = 0
    else:
        breakdown['pe'] = 0

    # Revenue Growth scoring (20 points)
    rev_growth = metrics.get('revenue_growth')
    if rev_growth is not None:
        if rev_growth > 20:
            score += 20
            breakdown['revenue_growth'] = 20
        elif rev_growth > 10:
            score += 10
            breakdown['revenue_growth'] = 10
        else:
            breakdown['revenue_growth'] = 0
    else:
        breakdown['revenue_growth'] = 0

    # Earnings Growth scoring (15 points)
    earnings_growth = metrics.get('earnings_growth')
    if earnings_growth is not None:
        if earnings_growth > 20:
            score += 15
            breakdown['earnings_growth'] = 15
        elif earnings_growth > 10:
            score += 8
            breakdown['earnings_growth'] = 8
        else:
            breakdown['earnings_growth'] = 0
    else:
        breakdown['earnings_growth'] = 0

    # ROE scoring (10 points)
    roe = metrics.get('roe')
    if roe is not None:
        if roe > 20:
            score += 10
            breakdown['roe'] = 10
        elif roe > 10:
            score += 5
            breakdown['roe'] = 5
        else:
            breakdown['roe'] = 0
    else:
        breakdown['roe'] = 0

    # Debt/Equity scoring (5 points)
    debt_equity = metrics.get('debt_to_equity')
    if debt_equity is not None:
        if debt_equity < 0.5:
            score += 5
            breakdown['debt_equity'] = 5
        elif debt_equity < 1.0:
            score += 3
            breakdown['debt_equity'] = 3
        else:
            breakdown['debt_equity'] = 0
    else:
        breakdown['debt_equity'] = 0

    return {
        'total_score': score,
        'breakdown': breakdown,
        'rating': get_rating(score)
    }


def get_rating(score: int) -> str:
    """Convert numeric score to rating."""
    if score >= 80:
        return 'Excellent'
    elif score >= 60:
        return 'Good'
    elif score >= 40:
        return 'Fair'
    else:
        return 'Poor'


def fetch_stock_metrics(symbol: str) -> Optional[Dict]:
    """Fetch GARP metrics for a single stock using yfinance."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # Get basic info
        name = info.get('longName', symbol)
        sector = info.get('sector', 'Unknown')

        # P/E Ratio
        pe_ratio = info.get('trailingPE') or info.get('forwardPE')

        # PEG Ratio
        peg_ratio = info.get('pegRatio')

        # Growth rates
        revenue_growth = info.get('revenueGrowth')
        if revenue_growth:
            revenue_growth = revenue_growth * 100  # Convert to percentage

        earnings_growth = info.get('earningsGrowth')
        if earnings_growth:
            earnings_growth = earnings_growth * 100  # Convert to percentage

        # ROE (Return on Equity)
        roe = info.get('returnOnEquity')
        if roe:
            roe = roe * 100  # Convert to percentage

        # Debt to Equity
        debt_to_equity = info.get('debtToEquity')
        if debt_to_equity:
            debt_to_equity = debt_to_equity / 100  # Normalize

        # Market Cap
        market_cap = info.get('marketCap')

        # Current price
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')

        # Get price change
        hist = ticker.history(period='5d')
        price_change_pct = 0
        if len(hist) >= 2:
            current = hist['Close'].iloc[-1]
            previous = hist['Close'].iloc[-2]
            price_change_pct = ((current - previous) / previous) * 100

        metrics = {
            'symbol': symbol,
            'name': name,
            'sector': sector,
            'price': round(current_price, 2) if current_price else None,
            'price_change_pct': round(price_change_pct, 2),
            'pe_ratio': round(pe_ratio, 2) if pe_ratio else None,
            'peg_ratio': round(peg_ratio, 2) if peg_ratio else None,
            'revenue_growth': round(revenue_growth, 2) if revenue_growth else None,
            'earnings_growth': round(earnings_growth, 2) if earnings_growth else None,
            'roe': round(roe, 2) if roe else None,
            'debt_to_equity': round(debt_to_equity, 2) if debt_to_equity else None,
            'market_cap': market_cap,
            'market_cap_formatted': format_market_cap(market_cap) if market_cap else None
        }

        # Calculate GARP score
        score_data = calculate_garp_score(metrics)
        metrics['garp_score'] = score_data['total_score']
        metrics['garp_rating'] = score_data['rating']
        metrics['score_breakdown'] = score_data['breakdown']

        return metrics

    except Exception as e:
        print(f"Error fetching metrics for {symbol}: {e}")
        return None


def format_market_cap(market_cap: float) -> str:
    """Format market cap in human-readable form."""
    if market_cap >= 1_000_000_000_000:  # Trillion
        return f"${market_cap / 1_000_000_000_000:.2f}T"
    elif market_cap >= 1_000_000_000:  # Billion
        return f"${market_cap / 1_000_000_000:.2f}B"
    elif market_cap >= 1_000_000:  # Million
        return f"${market_cap / 1_000_000:.2f}M"
    else:
        return f"${market_cap:,.0f}"


@app.route('/api/garp/screen', methods=['GET'])
def screen_stocks():
    """
    Screen all stocks in the universe and return GARP candidates.

    Query params:
    - sector: Filter by sector (optional)
    - min_score: Minimum GARP score (default: 0)
    - limit: Maximum number of results (default: 50)
    """
    # Check cache
    cache_key = f"garp_screen_{request.args.get('sector', 'all')}"
    cached = get_cached_data(cache_key)
    if cached:
        return jsonify(cached)

    sector_filter = request.args.get('sector')
    min_score = int(request.args.get('min_score', 0))
    limit = int(request.args.get('limit', 50))

    results = []

    # Determine which sectors to screen
    if sector_filter and sector_filter in STOCK_UNIVERSE:
        sectors_to_screen = {sector_filter: STOCK_UNIVERSE[sector_filter]}
    else:
        sectors_to_screen = STOCK_UNIVERSE

    # Screen all stocks
    for sector, symbols in sectors_to_screen.items():
        for symbol in symbols:
            metrics = fetch_stock_metrics(symbol)
            if metrics and metrics.get('garp_score', 0) >= min_score:
                results.append(metrics)

    # Sort by GARP score (descending)
    results.sort(key=lambda x: x.get('garp_score', 0), reverse=True)

    # Limit results
    results = results[:limit]

    response = {
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'total_screened': sum(len(symbols) for symbols in sectors_to_screen.values()),
        'total_found': len(results),
        'stocks': results,
        'cache_duration_hours': CACHE_DURATION.total_seconds() / 3600
    }

    # Cache the results
    set_cached_data(cache_key, response)

    return jsonify(response)


@app.route('/api/garp/stock/<symbol>', methods=['GET'])
def get_stock_metrics(symbol: str):
    """Get detailed GARP metrics for a specific stock."""
    symbol = symbol.upper()

    # Check cache
    cache_key = f"garp_stock_{symbol}"
    cached = get_cached_data(cache_key)
    if cached:
        return jsonify(cached)

    metrics = fetch_stock_metrics(symbol)

    if metrics:
        response = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'data': metrics
        }
        set_cached_data(cache_key, response)
        return jsonify(response)
    else:
        return jsonify({
            'success': False,
            'error': f'Unable to fetch metrics for {symbol}'
        }), 404


@app.route('/api/garp/sectors', methods=['GET'])
def get_sectors():
    """Get list of available sectors."""
    return jsonify({
        'success': True,
        'sectors': list(STOCK_UNIVERSE.keys()),
        'stock_count': {sector: len(symbols) for sector, symbols in STOCK_UNIVERSE.items()}
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'GARP Stock Screener API',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    print("=" * 60)
    print("GARP Stock Screener API Server")
    print("=" * 60)
    print(f"Starting server on http://localhost:5003")
    print(f"Cache duration: {CACHE_DURATION.total_seconds() / 3600} hours")
    print(f"Total stocks in universe: {sum(len(symbols) for symbols in STOCK_UNIVERSE.values())}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5003, debug=False)
