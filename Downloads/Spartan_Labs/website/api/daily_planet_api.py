#!/usr/bin/env python3
"""
Daily Planet API Server
Provides real market data to the Daily Planet dashboard
Uses yfinance for market data (unlimited free API)
"""

import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
from datetime import datetime, timedelta
import logging
import requests
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



@app.route('/api/market-news', methods=['GET'])
def get_market_news():
    """Fetch latest market news from yfinance"""
    try:
        logger.info("Fetching market news...")

        # Fetch news for major indices
        tickers = ['SPY', 'QQQ', 'DIA']
        all_news = []

        for ticker_symbol in tickers:
            try:
                ticker = yf.Ticker(ticker_symbol)
                news = ticker.news

                if news:
                    for item in news[:5]:  # Top 5 news per ticker
                        all_news.append({
                            'title': item.get('title', 'No title'),
                            'source': item.get('publisher', 'Market News'),
                            'timestamp': item.get('providerPublishTime', None),
                            'link': item.get('link', '')
                        })
            except Exception as e:
                logger.warning(f"Failed to fetch news for {ticker_symbol}: {e}")
                continue

        # Sort by timestamp (most recent first)
        all_news.sort(key=lambda x: x.get('timestamp', 0), reverse=True)

        # Deduplicate by title
        seen_titles = set()
        unique_news = []
        for item in all_news:
            if item['title'] not in seen_titles:
                seen_titles.add(item['title'])
                unique_news.append(item)

        logger.info(f"Successfully fetched {len(unique_news)} unique news items")

        return jsonify({
            'success': True,
            'news': unique_news[:15],  # Return top 15
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error fetching market news: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'news': []
        }), 500


@app.route('/api/economic-calendar', methods=['GET'])


def get_economic_calendar():


    """Get economic calendar events (requires paid API integration)"""


    try:


        logger.warning("Economic calendar endpoint called - feature not yet implemented")





        # NO FAKE DATA POLICY: Return NULL with explanation


        # This feature requires a paid API (Trading Economics, Econoday, etc.)


        # Real economic calendar data will be added when API is integrated





        return jsonify({


            'success': False,


            'error': 'Economic calendar feature not yet implemented',


            'message': 'This feature requires a paid API integration (Trading Economics, Econoday, etc.). Use FRED API for historical economic data instead.',


            'events': None,


            'timestamp': datetime.now().isoformat(),


            'alternatives': {


                'fred_api': '/api/fred/series/observations?series_id=ICSA',  # Example: Initial Jobless Claims


                'documentation': 'See FRED API documentation for economic indicators'


            }


        }), 501  # 501 Not Implemented status code





    except Exception as e:


        logger.error(f"Error in economic calendar endpoint: {e}")


        return jsonify({


            'success': False,


            'error': str(e),


            'events': None


        }), 500





@app.route('/api/market-movers', methods=['POST'])


def get_market_movers():
    """Fetch real-time market movers data from yfinance"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA'])

        logger.info(f"Fetching market movers for {len(symbols)} symbols...")

        movers = []

        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period='1d')

                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    open_price = hist['Open'].iloc[0]
                    change_pct = ((current_price - open_price) / open_price) * 100

                    movers.append({
                        'symbol': symbol,
                        'name': info.get('shortName', symbol),
                        'price': float(current_price),
                        'change_pct': float(change_pct),
                        'volume': int(hist['Volume'].iloc[-1]) if 'Volume' in hist else 0
                    })

            except Exception as e:
                logger.warning(f"Failed to fetch data for {symbol}: {e}")
                continue

        logger.info(f"Successfully fetched {len(movers)} market movers")

        return jsonify({
            'success': True,
            'movers': movers,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error fetching market movers: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'movers': []
        }), 500


@app.route('/api/sector-rotation', methods=['POST'])
def get_sector_rotation():
    """Fetch sector rotation data from yfinance"""
    try:
        data = request.get_json()
        sectors = data.get('sectors', {})

        logger.info(f"Fetching sector data for {len(sectors)} sectors...")

        sector_data = []

        for etf_symbol, sector_name in sectors.items():
            try:
                ticker = yf.Ticker(etf_symbol)
                hist = ticker.history(period='1d')

                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    open_price = hist['Open'].iloc[0]
                    change_pct = ((current_price - open_price) / open_price) * 100

                    sector_data.append({
                        'symbol': etf_symbol,
                        'name': sector_name,
                        'price': float(current_price),
                        'change_pct': float(change_pct),
                        'volume': int(hist['Volume'].iloc[-1]) if 'Volume' in hist else 0
                    })

            except Exception as e:
                logger.warning(f"Failed to fetch data for {etf_symbol}: {e}")
                continue

        logger.info(f"Successfully fetched {len(sector_data)} sector data points")

        return jsonify({
            'success': True,
            'sectors': sector_data,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error fetching sector rotation: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'sectors': []
        }), 500


@app.route('/api/sentiment-analysis', methods=['GET'])
def get_sentiment_analysis():
    """Calculate market sentiment based on market indices"""
    try:
        logger.info("Calculating market sentiment...")

        # Fetch major indices
        indices = {
            'SPY': yf.Ticker('SPY'),
            'QQQ': yf.Ticker('QQQ'),
            'VIX': yf.Ticker('^VIX')
        }

        spy_hist = indices['SPY'].history(period='5d')
        qqq_hist = indices['QQQ'].history(period='5d')
        vix_hist = indices['VIX'].history(period='1d')

        # Calculate changes
        spy_change = ((spy_hist['Close'].iloc[-1] - spy_hist['Close'].iloc[0]) /
                      spy_hist['Close'].iloc[0]) * 100
        qqq_change = ((qqq_hist['Close'].iloc[-1] - qqq_hist['Close'].iloc[0]) /
                      qqq_hist['Close'].iloc[0]) * 100

        # VIX sentiment (inverse - lower VIX = more bullish)
        vix_current = vix_hist['Close'].iloc[-1]

        # Calculate overall sentiment (0-100 scale)
        # Positive market changes + low VIX = bullish
        market_sentiment = (spy_change + qqq_change) / 2

        # Adjust based on VIX
        if vix_current < 15:
            vix_adjustment = 10  # Very bullish
        elif vix_current < 20:
            vix_adjustment = 5   # Moderately bullish
        elif vix_current < 30:
            vix_adjustment = 0   # Neutral
        else:
            vix_adjustment = -10  # Bearish

        overall = 50 + (market_sentiment * 2) + vix_adjustment
        overall = max(0, min(100, overall))  # Clamp to 0-100

        # Calculate breakdown
        if overall >= 60:
            bullish = 60
            neutral = 25
            bearish = 15
        elif overall >= 50:
            bullish = 45
            neutral = 35
            bearish = 20
        elif overall >= 40:
            bullish = 30
            neutral = 40
            bearish = 30
        else:
            bullish = 20
            neutral = 25
            bearish = 55

        sentiment = {
            'overall': int(overall),
            'bullish': int(bullish),
            'neutral': int(neutral),
            'bearish': int(bearish)
        }

        logger.info(f"Sentiment calculated: {overall:.1f} (VIX: {vix_current:.2f})")

        return jsonify({
            'success': True,
            'sentiment': sentiment,
            'vix': float(vix_current),
            'spy_change': float(spy_change),
            'qqq_change': float(qqq_change),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error calculating sentiment: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'sentiment': None
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Daily Planet API',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("Daily Planet API Server Starting...")
    logger.info("=" * 60)
    logger.info("Server: http://localhost:5000")
    logger.info("Endpoints:")
    logger.info("  GET  /api/market-news         - Latest market news")
    logger.info("  GET  /api/economic-calendar   - Economic events")
    logger.info("  POST /api/market-movers       - Top market movers")
    logger.info("  POST /api/sector-rotation     - Sector performance")
    logger.info("  GET  /api/sentiment-analysis  - Market sentiment")
    logger.info("  GET  /health                  - Health check")
    logger.info("=" * 60)
    logger.info("Data Source: yfinance (unlimited free API)")
    logger.info("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=False)
