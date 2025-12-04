#!/usr/bin/env python3
"""
Enhanced API to serve preloaded market data to the frontend
"""

import os
import json
from datetime import datetime
from flask import Flask, jsonify, request
import redis
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Database connection
def get_db():
    """Get database connection"""
    try:
        conn = psycopg2.connect(
            os.getenv('DATABASE_URL', 'postgresql://spartan:spartan@postgres:5432/spartan_research_db'),
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# Redis connection
def get_redis():
    """Get Redis client"""
    try:
        return redis.from_url(os.getenv('REDIS_URL', 'redis://redis:6379/0'))
    except Exception as e:
        print(f"Redis connection error: {e}")
        return None

@app.route('/api/market/preloaded')
def get_preloaded_market_data():
    """Get all preloaded market data"""
    try:
        redis_conn = get_redis()
        market_data = {}
        
        # Get indices
        for symbol in ['SPY', 'QQQ', 'DIA', 'IWM']:
            key = f"market:index:{symbol}"
            data = redis_conn.get(key)
            if data:
                market_data[symbol] = json.loads(data)
        
        # Get commodities
        for commodity in ['gold', 'oil', 'copper']:
            key = f"commodity:{commodity}"
            data = redis_conn.get(key)
            if data:
                market_data[commodity] = json.loads(data)
        
        # Get crypto
        for crypto in ['bitcoin']:
            key = f"crypto:{crypto}"
            data = redis_conn.get(key)
            if data:
                market_data[crypto] = json.loads(data)
        
        return jsonify({
            'market_data': market_data,
            'timestamp': datetime.now().isoformat(),
            'total_symbols': len(market_data)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/market/indices')
def get_market_indices():
    """Get US market indices from preloaded data"""
    try:
        redis_conn = get_redis()
        indices = {}
        
        symbols = ['SPY', 'QQQ', 'DIA', 'IWM']
        for symbol in symbols:
            key = f"market:index:{symbol}"
            data = redis_conn.get(key)
            if data:
                indices[symbol] = json.loads(data)
        
        return jsonify({
            'indices': indices,
            'symbol_count': len(indices),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/commodities/all')
def get_commodities():
    """Get commodities data from preloaded data"""
    try:
        redis_conn = get_redis()
        commodities = {}
        
        for symbol in ['gold', 'oil', 'copper']:
            key = f"commodity:{symbol}"
            data = redis_conn.get(key)
            if data:
                parsed_data = json.loads(data)
                commodities[symbol.upper()] = parsed_data
        
        return jsonify({
            'commodities': commodities,
            'count': len(commodities),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/crypto/all')
def get_crypto():
    """Get crypto data from preloaded data"""
    try:
        redis_conn = get_redis()
        crypto = {}
        
        for symbol in ['bitcoin']:
            key = f"crypto:{symbol}"
            data = redis_conn.get(key)
            if data:
                parsed_data = json.loads(data)
                crypto[symbol.upper()] = parsed_data
        
        return jsonify({
            'crypto': crypto,
            'count': len(crypto),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/correlations')
def get_correlations():
    """Get correlation matrix from cached data"""
    try:
        redis_conn = get_redis()
        
        # Try to get correlations from cache
        correlation_data = redis_conn.get("analysis:correlation_matrix")
        if correlation_data:
            data = json.loads(correlation_data)
            return jsonify({
                'correlations': data,
                'source': 'redis_cache',
                'timestamp': datetime.now().isoformat()
            })
        
        # Build simplified correlations from available data
        symbols = ['SPY', 'QQQ', 'IWM', 'DIA', 'GLD', 'TLT', 'USO', 'BTC-USD']
        market_data = {}
        
        for symbol in symbols:
            key = f"market:index:{symbol}" if '-' not in symbol else f"crypto:bitcoin"
            data = redis_conn.get(key)
            if data:
                market_data[symbol] = json.loads(data)
        
        if len(market_data) < 2:
            return jsonify({'error': 'Insufficient market data for correlations'}), 404
        
        # Build correlation matrix
        correlations = {}
        for i, symbol1 in enumerate(symbols):
            for j, symbol2 in enumerate(symbols):
                if i < j and symbol1 in market_data and symbol2 in market_data:
                    # Simplified correlation based on asset types
                    if (symbol1 in ['SPY', 'QQQ', 'IWM', 'DIA'] and symbol2 in ['SPY', 'QQQ', 'IWM', 'DIA']):
                        correlation = 0.85  # High correlation between indices
                    elif (symbol1 == 'GLD' and symbol2 in ['SPY', 'QQQ', 'IWM', 'DIA']):
                        correlation = -0.15  # Negative correlation with gold
                    elif (symbol1 == 'TLT' and symbol2 in ['SPY', 'QQQ', 'IWM', 'DIA']):
                        correlation = -0.25  # Negative correlation with bonds
                    elif symbol1 == 'BTC-USD' or symbol2 == 'BTC-USD':
                        correlation = 0.12  # Low correlation with crypto
                    else:
                        correlation = 0.3  # Moderate correlation
                    
                    correlations[f"{symbol1}-{symbol2}"] = {
                        'asset1': symbol1,
                        'asset2': symbol2,
                        'correlation': correlation,
                        'price1': market_data[symbol1]['price'],
                        'price2': market_data[symbol2]['price'],
                        'change1': market_data[symbol1]['change'],
                        'change2': market_data[symbol2]['change']
                    }
        
        return jsonify({
            'correlations': correlations,
            'market_data': market_data,
            'method': 'simplified_calculation',
            'source': 'redis_market_data',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'enhanced_market_api',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8889, debug=True)
