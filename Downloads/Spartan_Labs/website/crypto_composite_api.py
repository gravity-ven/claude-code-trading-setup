#!/usr/bin/env python3
"""
Crypto Composite Indicator API
Real-time crypto market signals combining Fear & Greed, MVRV, funding rates, and on-chain data
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os
from datetime import datetime, timedelta
import json

app = Flask(__name__)
CORS(app)

# API Keys
COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY', '')  # Free tier available
GLASSNODE_API_KEY = os.getenv('GLASSNODE_API_KEY', '')  # For on-chain data

# Cache configuration
CACHE_DURATION = 900  # 15 minutes
cache = {}

def get_cached_or_fetch(key, fetch_func, ttl=CACHE_DURATION):
    """Cache wrapper to avoid excessive API calls"""
    now = datetime.now().timestamp()

    if key in cache:
        data, timestamp = cache[key]
        if now - timestamp < ttl:
            return data

    try:
        data = fetch_func()
        cache[key] = (data, now)
        return data
    except Exception as e:
        print(f"Error fetching {key}: {e}")
        # Return cached data even if expired, or None
        if key in cache:
            return cache[key][0]
        return None

def fetch_fear_greed_index():
    """
    Fetch Crypto Fear & Greed Index from Alternative.me
    Free API, no key required
    """
    url = "https://api.alternative.me/fng/?limit=30"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            latest = data['data'][0]

            value = int(latest['value'])
            classification = latest['value_classification']

            # Calculate signal based on contrarian approach
            if value <= 20:
                signal = "STRONG BUY"
                strength = 95
                color = "#00ff00"
            elif value <= 30:
                signal = "BUY"
                strength = 75
                color = "#66ff66"
            elif value <= 45:
                signal = "NEUTRAL-BULLISH"
                strength = 55
                color = "#ffcc00"
            elif value <= 55:
                signal = "NEUTRAL"
                strength = 50
                color = "#ffff00"
            elif value <= 70:
                signal = "NEUTRAL-BEARISH"
                strength = 45
                color = "#ff9900"
            elif value <= 80:
                signal = "SELL"
                strength = 25
                color = "#ff6600"
            else:
                signal = "STRONG SELL"
                strength = 5
                color = "#ff0000"

            # Get historical trend (last 7 days)
            week_data = data['data'][:7]
            avg_week = sum(int(d['value']) for d in week_data) / len(week_data)
            trend = "Rising" if value > avg_week else "Falling" if value < avg_week else "Stable"

            return {
                'value': value,
                'classification': classification,
                'signal': signal,
                'strength': strength,
                'color': color,
                'trend': trend,
                'timestamp': latest['timestamp']
            }
    except Exception as e:
        print(f"Fear & Greed error: {e}")

    return None

def fetch_bitcoin_metrics():
    """
    Fetch Bitcoin price, dominance, and volatility from CoinGecko
    Free API
    """
    try:
        # Bitcoin price and market data
        btc_url = "https://api.coingecko.com/api/v3/coins/bitcoin?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false"
        response = requests.get(btc_url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            market_data = data['market_data']

            price = market_data['current_price']['usd']
            price_change_24h = market_data['price_change_percentage_24h']
            price_change_7d = market_data['price_change_percentage_7d']
            price_change_30d = market_data['price_change_percentage_30d']

            market_cap = market_data['market_cap']['usd']
            volume_24h = market_data['total_volume']['usd']

            # Calculate dominance
            global_url = "https://api.coingecko.com/api/v3/global"
            global_response = requests.get(global_url, timeout=10)

            dominance = 0
            if global_response.status_code == 200:
                global_data = global_response.json()['data']
                dominance = global_data['market_cap_percentage'].get('btc', 0)

            # Dominance signal
            if dominance > 60:
                dominance_signal = "Risk-Off (Money in BTC)"
                dominance_color = "#ff9900"
            elif dominance > 50:
                dominance_signal = "BTC Dominance High"
                dominance_color = "#ffcc00"
            elif dominance > 45:
                dominance_signal = "Balanced Market"
                dominance_color = "#ffff00"
            else:
                dominance_signal = "Altseason Potential"
                dominance_color = "#00ff00"

            # Simple MVRV approximation (price vs 200-day MA)
            # Real MVRV requires on-chain data
            ath = market_data['ath']['usd']
            mvrv_approx = (price / ath) * 10  # Simplified Z-score

            if mvrv_approx < 2:
                mvrv_signal = "UNDERVALUED"
                mvrv_color = "#00ff00"
            elif mvrv_approx < 5:
                mvrv_signal = "FAIR VALUE"
                mvrv_color = "#ffff00"
            else:
                mvrv_signal = "OVERVALUED"
                mvrv_color = "#ff6600"

            return {
                'price': price,
                'price_change_24h': round(price_change_24h, 2),
                'price_change_7d': round(price_change_7d, 2),
                'price_change_30d': round(price_change_30d, 2),
                'market_cap': market_cap,
                'volume_24h': volume_24h,
                'dominance': round(dominance, 2),
                'dominance_signal': dominance_signal,
                'dominance_color': dominance_color,
                'mvrv_approx': round(mvrv_approx, 2),
                'mvrv_signal': mvrv_signal,
                'mvrv_color': mvrv_color,
                'ath': ath
            }
    except Exception as e:
        print(f"Bitcoin metrics error: {e}")

    return None

def fetch_funding_rates():
    """
    Fetch perpetual futures funding rates
    Using Binance public API (no key required)
    """
    try:
        url = "https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            funding_rate = float(data['lastFundingRate']) * 100  # Convert to percentage

            # Funding rate signal
            if funding_rate < -0.1:
                signal = "EXTREME CAPITULATION"
                strength = 95
                color = "#00ff00"
            elif funding_rate < -0.05:
                signal = "Heavy Shorts (Bullish)"
                strength = 75
                color = "#66ff66"
            elif funding_rate < -0.01:
                signal = "Mild Short Bias"
                strength = 60
                color = "#ffcc00"
            elif funding_rate < 0.01:
                signal = "NEUTRAL"
                strength = 50
                color = "#ffff00"
            elif funding_rate < 0.05:
                signal = "Mild Long Bias"
                strength = 40
                color = "#ff9900"
            elif funding_rate < 0.1:
                signal = "Heavy Longs (Bearish)"
                strength = 25
                color = "#ff6600"
            else:
                signal = "EXTREME GREED"
                strength = 5
                color = "#ff0000"

            return {
                'funding_rate': round(funding_rate, 4),
                'signal': signal,
                'strength': strength,
                'color': color
            }
    except Exception as e:
        print(f"Funding rate error: {e}")

    return None

def calculate_composite_score(fear_greed, btc_metrics, funding):
    """
    Calculate overall composite score from all indicators
    Score: 0-100 (0 = extreme bearish, 100 = extreme bullish)
    """
    scores = []

    # Fear & Greed (contrarian - low fear = bullish)
    if fear_greed:
        fg_score = 100 - fear_greed['value']  # Invert for contrarian
        scores.append(fg_score)

    # MVRV (undervalued = bullish)
    if btc_metrics:
        if btc_metrics['mvrv_signal'] == 'UNDERVALUED':
            mvrv_score = 80
        elif btc_metrics['mvrv_signal'] == 'FAIR VALUE':
            mvrv_score = 50
        else:
            mvrv_score = 20
        scores.append(mvrv_score)

    # Funding rates (negative = bullish)
    if funding:
        funding_score = funding['strength']
        scores.append(funding_score)

    # Dominance (low dominance = altcoin opportunity)
    if btc_metrics and btc_metrics['dominance']:
        if btc_metrics['dominance'] < 45:
            dom_score = 70
        elif btc_metrics['dominance'] < 50:
            dom_score = 60
        elif btc_metrics['dominance'] < 55:
            dom_score = 50
        else:
            dom_score = 40
        scores.append(dom_score)

    # Calculate average
    if scores:
        composite = sum(scores) / len(scores)

        # Determine signal
        if composite >= 75:
            signal = "STRONG BUY"
            color = "#00ff00"
        elif composite >= 60:
            signal = "BUY"
            color = "#66ff66"
        elif composite >= 55:
            signal = "NEUTRAL-BULLISH"
            color = "#ffcc00"
        elif composite >= 45:
            signal = "NEUTRAL"
            color = "#ffff00"
        elif composite >= 40:
            signal = "NEUTRAL-BEARISH"
            color = "#ff9900"
        elif composite >= 25:
            signal = "SELL"
            color = "#ff6600"
        else:
            signal = "STRONG SELL"
            color = "#ff0000"

        return {
            'score': round(composite, 1),
            'signal': signal,
            'color': color,
            'component_scores': {
                'fear_greed_contrarian': round(scores[0], 1) if len(scores) > 0 else None,
                'mvrv': round(scores[1], 1) if len(scores) > 1 else None,
                'funding': round(scores[2], 1) if len(scores) > 2 else None,
                'dominance': round(scores[3], 1) if len(scores) > 3 else None
            }
        }

    return None

@app.route('/api/crypto-composite', methods=['GET'])
def get_crypto_composite():
    """Main endpoint for crypto composite indicator"""

    # Fetch all components
    fear_greed = get_cached_or_fetch('fear_greed', fetch_fear_greed_index)
    btc_metrics = get_cached_or_fetch('btc_metrics', fetch_bitcoin_metrics)
    funding = get_cached_or_fetch('funding', fetch_funding_rates)

    # Calculate composite
    composite = calculate_composite_score(fear_greed, btc_metrics, funding)

    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'composite': composite,
        'fear_greed': fear_greed,
        'bitcoin': btc_metrics,
        'funding_rates': funding,
        'status': 'success'
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Crypto Composite API',
        'version': '1.0.0'
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5005))
    app.run(host='0.0.0.0', port=port, debug=False)
