#!/usr/bin/env python3
"""
Market Highlights API Server
Serves real-time market data using yfinance for the Spartan Research Station
NO FAKE DATA - All data from real market APIs
"""

from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf
from datetime import datetime
import logging

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/api/highlights/symbol/<symbol>', methods=['GET'])
def get_symbol_data(symbol):
    """
    Fetch real-time data for a single symbol using yfinance

    Returns:
        JSON with symbol, name, price, change, changePercent, volume
    """
    try:
        logger.info(f"Fetching data for symbol: {symbol}")

        # Create ticker object
        ticker = yf.Ticker(symbol)

        # Get current market data
        info = ticker.info

        # Get historical data for price change calculation
        hist = ticker.history(period='2d')

        if hist.empty or len(hist) < 2:
            logger.warning(f"Insufficient data for {symbol}")
            return jsonify({'error': 'Insufficient data'}), 404

        # Current price (latest close)
        current_price = float(hist['Close'].iloc[-1])

        # Previous close
        previous_close = float(hist['Close'].iloc[-2])

        # Calculate change
        change = current_price - previous_close
        change_percent = (change / previous_close) * 100

        # Volume
        volume = int(hist['Volume'].iloc[-1])

        # Company name
        name = info.get('longName', symbol)

        data = {
            'symbol': symbol,
            'name': name,
            'price': round(current_price, 2),
            'change': round(change, 2),
            'changePercent': round(change_percent, 2),
            'volume': volume,
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"Successfully fetched {symbol}: ${current_price:.2f} ({change_percent:+.2f}%)")
        return jsonify(data)

    except Exception as e:
        logger.error(f"Error fetching {symbol}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/highlights/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'service': 'Market Highlights API',
        'timestamp': datetime.now().isoformat(),
        'data_source': 'yfinance (real market data)'
    })


@app.route('/api/highlights/batch', methods=['POST'])
def get_batch_data():
    """
    Fetch data for multiple symbols in one request
    Expects JSON body with 'symbols' array
    """
    from flask import request

    try:
        symbols = request.json.get('symbols', [])

        if not symbols:
            return jsonify({'error': 'No symbols provided'}), 400

        logger.info(f"Fetching batch data for {len(symbols)} symbols")

        results = []
        errors = []

        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period='2d')

                if hist.empty or len(hist) < 2:
                    errors.append(symbol)
                    continue

                current_price = float(hist['Close'].iloc[-1])
                previous_close = float(hist['Close'].iloc[-2])
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100
                volume = int(hist['Volume'].iloc[-1])
                name = info.get('longName', symbol)

                results.append({
                    'symbol': symbol,
                    'name': name,
                    'price': round(current_price, 2),
                    'change': round(change, 2),
                    'changePercent': round(change_percent, 2),
                    'volume': volume
                })

            except Exception as e:
                logger.error(f"Error fetching {symbol}: {str(e)}")
                errors.append(symbol)

        return jsonify({
            'data': results,
            'errors': errors,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Batch fetch error: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    logger.info("Starting Market Highlights API Server...")
    logger.info("Data Source: yfinance (real market data)")
    logger.info("Endpoint: http://localhost:5001")

    # Run Flask server
    app.run(host='0.0.0.0', port=5001, debug=True)
