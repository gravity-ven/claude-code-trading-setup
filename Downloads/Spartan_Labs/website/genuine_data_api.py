#!/usr/bin/env python3
"""
GENUINE DATA API
================

Flask API that serves real data from autonomous agents to React frontend.
NO simulated data - all data comes from Redis (populated by agents).

Endpoints:
- /api/genuine/recession - Recession indicators
- /api/genuine/market/{category} - Market data by category
- /api/genuine/crypto/{symbol} - Crypto data
- /api/genuine/health - API health check
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import redis
import json
import logging
from datetime import datetime

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis connection
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)


@app.route('/api/genuine/health', methods=['GET'])
def health_check():
    """Check API and agent health"""
    try:
        # Check Redis connection
        redis_client.ping()

        # Check for recent data
        recession_data = redis_client.get('recession:indicators')
        market_summary = redis_client.get('market:summary')
        crypto_summary = redis_client.get('crypto:summary')

        agents_status = {
            'recession_agent': 'active' if recession_data else 'inactive',
            'market_agent': 'active' if market_summary else 'inactive',
            'crypto_agent': 'active' if crypto_summary else 'inactive'
        }

        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'redis': 'connected',
            'agents': agents_status
        })

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@app.route('/api/genuine/recession', methods=['GET'])
def get_recession_indicators():
    """Get recession indicators from agent"""
    try:
        data = redis_client.get('recession:indicators')

        if not data:
            return jsonify({
                'error': 'No recession data available',
                'message': 'Recession indicators agent may not be running'
            }), 404

        indicators = json.loads(data)

        # Format for frontend
        response = {
            'timestamp': indicators.get('timestamp'),
            'indicators': [
                {
                    'name': 'Yield Curve (10Y-2Y)',
                    'value': indicators.get('yield_curve_10y2y'),
                    'threshold': 0,
                    'weight': 25
                },
                {
                    'name': 'Yield Curve (10Y-3M)',
                    'value': indicators.get('yield_curve_10y3m'),
                    'threshold': 0,
                    'weight': 20
                },
                {
                    'name': 'Sahm Rule (Unemployment)',
                    'value': indicators.get('sahm_rule'),
                    'threshold': 0.5,
                    'weight': 20
                },
                {
                    'name': 'Leading Economic Index',
                    'value': indicators.get('lei'),
                    'threshold': -2,
                    'weight': 15
                },
                {
                    'name': 'Credit Spreads (HYG/LQD)',
                    'value': indicators.get('credit_spreads'),
                    'threshold': 1.2,
                    'weight': 10
                },
                {
                    'name': 'PMI Manufacturing',
                    'value': indicators.get('pmi_manufacturing'),
                    'threshold': 50,
                    'weight': 5
                },
                {
                    'name': 'Initial Jobless Claims',
                    'value': indicators.get('initial_claims'),
                    'threshold': 300,
                    'weight': 5
                }
            ],
            'source': 'genuine_agent_data'
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error fetching recession data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/genuine/market/<category>', methods=['GET'])
def get_market_data(category):
    """Get market data for a category"""
    try:
        key = f"market:category:{category}"
        data = redis_client.get(key)

        if not data:
            return jsonify({
                'error': f'No market data for category: {category}',
                'message': 'Market data agent may not be running'
            }), 404

        market_data = json.loads(data)

        return jsonify({
            'category': category,
            'data': market_data,
            'timestamp': datetime.now().isoformat(),
            'source': 'genuine_agent_data'
        })

    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/genuine/market/symbol/<symbol>', methods=['GET'])
def get_market_symbol(symbol):
    """Get data for a specific market symbol"""
    try:
        key = f"market:symbol:{symbol}"
        data = redis_client.get(key)

        if not data:
            return jsonify({
                'error': f'No data for symbol: {symbol}',
                'message': 'Symbol not tracked or agent not running'
            }), 404

        symbol_data = json.loads(data)

        return jsonify(symbol_data)

    except Exception as e:
        logger.error(f"Error fetching symbol data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/genuine/crypto/<symbol>', methods=['GET'])
def get_crypto_data(symbol):
    """Get crypto data for a symbol"""
    try:
        key = f"crypto:symbol:{symbol}"
        data = redis_client.get(key)

        if not data:
            return jsonify({
                'error': f'No crypto data for: {symbol}',
                'message': 'Crypto agent may not be running'
            }), 404

        crypto_data = json.loads(data)

        return jsonify(crypto_data)

    except Exception as e:
        logger.error(f"Error fetching crypto data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/genuine/all-markets', methods=['GET'])
def get_all_markets():
    """Get all market data (indices, commodities, bonds, sectors, global)"""
    try:
        categories = ['indices', 'commodities', 'bonds', 'sectors', 'global']
        result = {}

        for category in categories:
            key = f"market:category:{category}"
            data = redis_client.get(key)
            if data:
                result[category] = json.loads(data)

        if not result:
            return jsonify({
                'error': 'No market data available',
                'message': 'Market data agent may not be running'
            }), 404

        return jsonify({
            'data': result,
            'timestamp': datetime.now().isoformat(),
            'source': 'genuine_agent_data'
        })

    except Exception as e:
        logger.error(f"Error fetching all markets: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/genuine/crypto', methods=['GET'])
def get_all_crypto():
    """Get all crypto data"""
    try:
        symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD', 'AVAX-USD']
        result = {}

        for symbol in symbols:
            key = f"crypto:symbol:{symbol}"
            data = redis_client.get(key)
            if data:
                result[symbol] = json.loads(data)

        if not result:
            return jsonify({
                'error': 'No crypto data available',
                'message': 'Crypto agent may not be running'
            }), 404

        return jsonify({
            'data': result,
            'timestamp': datetime.now().isoformat(),
            'source': 'genuine_agent_data'
        })

    except Exception as e:
        logger.error(f"Error fetching all crypto: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/genuine/barometers', methods=['GET'])
def get_barometers():
    """Get intermarket barometer data"""
    try:
        # Barometers use various sources - compile from market and recession data
        recession_data = redis_client.get('recession:indicators')
        market_summary = redis_client.get('market:summary')

        if not recession_data and not market_summary:
            return jsonify({
                'error': 'No barometer data available',
                'message': 'Agents may not be running'
            }), 404

        recession = json.loads(recession_data) if recession_data else {}
        market = json.loads(market_summary) if market_summary else {}

        # Construct barometers from available data
        barometers = []

        if recession.get('credit_spreads'):
            barometers.append({
                'name': 'Credit Spreads (HYG/LQD)',
                'value': recession['credit_spreads'],
                'timeframe': '6-18 months'
            })

        if recession.get('yield_curve_10y2y') is not None:
            barometers.append({
                'name': 'Yield Curve (10Y-2Y)',
                'value': recession['yield_curve_10y2y'],
                'timeframe': '12-18 months'
            })

        # Add more barometers from available data...

        return jsonify({
            'barometers': barometers,
            'timestamp': datetime.now().isoformat(),
            'source': 'genuine_agent_data'
        })

    except Exception as e:
        logger.error(f"Error fetching barometers: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    logger.info("🚀 Genuine Data API starting on port 5005...")
    app.run(host='0.0.0.0', port=5005, debug=False)
