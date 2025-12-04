#!/usr/bin/env python3
"""
Spartan Research Station - Web Server
==============================================================================
Flask application serving market intelligence dashboard.
Database-First Architecture: ALL data from PostgreSQL (NEVER external APIs).
==============================================================================
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Flask, jsonify, render_template, send_from_directory, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
from functools import wraps
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()

# Initialize Flask app
app = Flask(__name__,
           static_folder='/app',
           template_folder='/app')

# CORS configuration
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv('CORS_ORIGINS', '*').split(','),
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
    }
})

# Configuration
class Config:
    """Web server configuration"""
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://spartan_user:spartan_pass_2025@postgres:5432/spartan_research')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    CACHE_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', '300'))  # 5 minutes
    MAX_DB_CONNECTIONS = int(os.getenv('MAX_DB_CONNECTIONS', '50'))
    SECRET_KEY = os.getenv('SECRET_KEY', 'spartan_research_station_2025')
    DEBUG = os.getenv('FLASK_DEBUG', '0') == '1'

app.config.from_object(Config)

# Database connection pool
db_conn = None
redis_client = None


def get_db():
    """Get database connection"""
    global db_conn
    if db_conn is None or db_conn.closed:
        db_conn = psycopg2.connect(
            Config.DATABASE_URL,
            cursor_factory=RealDictCursor
        )
    return db_conn


def get_redis():
    """Get Redis client"""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(Config.REDIS_URL)
    return redis_client


def cache_result(timeout=300):
    """Decorator to cache API results in Redis"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"cache:{f.__name__}:{str(args)}:{str(kwargs)}"

            try:
                r = get_redis()
                cached = r.get(cache_key)

                if cached:
                    logger.debug("cache_hit", function=f.__name__, cache_key=cache_key)
                    # Return cached data as-is (Flask Response object)
                    cached_data = json.loads(cached)
                    return jsonify(cached_data) if isinstance(cached_data, dict) else cached_data
            except Exception as e:
                logger.warning("cache_read_error", error=str(e))

            # Execute function
            result = f(*args, **kwargs)

            # Cache result (extract JSON data from Flask Response)
            try:
                r = get_redis()
                # If result is a Flask Response, extract the JSON data
                if hasattr(result, 'get_json'):
                    cache_data = result.get_json()
                elif isinstance(result, tuple):  # (response, status_code)
                    cache_data = result[0].get_json() if hasattr(result[0], 'get_json') else result[0]
                else:
                    cache_data = result

                r.setex(cache_key, timeout, json.dumps(cache_data))
                logger.debug("cache_set", function=f.__name__, cache_key=cache_key, timeout=timeout)
            except Exception as e:
                logger.warning("cache_write_error", error=str(e), function=f.__name__)

            return result
        return decorated_function
    return decorator


# ==============================================================================
# Health and System Endpoints
# ==============================================================================

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Check database
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()

        # Check Redis
        r = get_redis()
        r.ping()

        # Get refresh status
        refresh_status = r.hgetall('refresh:status')

        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'redis': 'connected',
            'refresh_status': {
                k.decode('utf-8'): v.decode('utf-8')
                for k, v in refresh_status.items()
            } if refresh_status else {}
        })
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@app.route('/api/system/status')
@cache_result(timeout=10)
def system_status():
    """Get system status and statistics"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Get data source health
        cursor.execute("""
            SELECT
                source_id,
                last_success,
                last_failure,
                success_count,
                failure_count,
                avg_response_time_ms,
                status
            FROM system.health_status
            ORDER BY source_id
        """)
        data_sources = cursor.fetchall()

        # Get latest refresh stats
        r = get_redis()
        refresh_status = r.hgetall('refresh:status')

        # Get database statistics
        cursor.execute("""
            SELECT
                schemaname,
                tablename,
                n_live_tup as row_count
            FROM pg_stat_user_tables
            WHERE schemaname IN ('market_data', 'economic_data', 'analytics')
            ORDER BY schemaname, tablename
        """)
        table_stats = cursor.fetchall()

        cursor.close()

        return jsonify({
            'data_sources': [dict(row) for row in data_sources],
            'refresh_status': {
                k.decode('utf-8'): v.decode('utf-8')
                for k, v in refresh_status.items()
            } if refresh_status else {},
            'table_stats': [dict(row) for row in table_stats],
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error("system_status_error", error=str(e), exc_info=True)
        return jsonify({'error': str(e)}), 500


# ==============================================================================
# Market Data Endpoints
# ==============================================================================

@app.route('/api/market/indices')
@cache_result(timeout=Config.CACHE_TIMEOUT)
def market_indices():
    """Get major market indices"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT ON (symbol)
                symbol,
                price,
                change_percent,
                volume,
                timestamp
            FROM preloaded_market_data WHERE data_type = 'index' AND timestamp > NOW() - INTERVAL '1 day'
            ORDER BY symbol, timestamp DESC
        """)
        indices = cursor.fetchall()
        cursor.close()

        return jsonify({
            'data': [dict(row) for row in indices],
            'timestamp': datetime.now().isoformat(),
            'source': 'database'
        })
    except Exception as e:
        logger.error("market_indices_error", error=str(e), exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/market/commodities')
@cache_result(timeout=Config.CACHE_TIMEOUT)
def market_commodities():
    """Get commodities data"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT ON (symbol)
                symbol,
                price,
                change_percent,
                volume,
                timestamp
            FROM preloaded_market_data WHERE data_type IN ('commodity', 'gold', 'oil', 'copper')
            WHERE timestamp > NOW() - INTERVAL '1 day'
            ORDER BY symbol, timestamp DESC
        """)
        commodities = cursor.fetchall()
        cursor.close()

        return jsonify({
            'data': [dict(row) for row in commodities],
            'timestamp': datetime.now().isoformat(),
            'source': 'database'
        })
    except Exception as e:
        logger.error("market_commodities_error", error=str(e), exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/market/forex')
@cache_result(timeout=Config.CACHE_TIMEOUT)
def market_forex():
    """Get forex rates"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT ON (pair)
                pair as symbol,
                base_currency,
                quote_currency,
                mid as rate,
                change_percent,
                timestamp
            FROM preloaded_market_data WHERE data_type = 'forex'
            WHERE timestamp > NOW() - INTERVAL '1 day'
            ORDER BY pair, timestamp DESC
        """)
        forex = cursor.fetchall()
        cursor.close()

        return jsonify({
            'data': [dict(row) for row in forex],
            'timestamp': datetime.now().isoformat(),
            'source': 'database'
        })
    except Exception as e:
        logger.error("market_forex_error", error=str(e), exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/market/crypto')
@cache_result(timeout=Config.CACHE_TIMEOUT)
def market_crypto():
    """Get crypto prices"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT ON (symbol)
                symbol,
                price,
                change_percent_24h,
                volume_24h,
                market_cap,
                timestamp
            FROM preloaded_market_data WHERE data_type = 'crypto'
            WHERE timestamp > NOW() - INTERVAL '1 day'
            ORDER BY symbol, timestamp DESC
        """)
        crypto = cursor.fetchall()
        cursor.close()

        return jsonify({
            'data': [dict(row) for row in crypto],
            'timestamp': datetime.now().isoformat(),
            'source': 'database'
        })
    except Exception as e:
        logger.error("market_crypto_error", error=str(e), exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/market/volatility')
@cache_result(timeout=Config.CACHE_TIMEOUT)
def market_volatility():
    """Get volatility indicators"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                'VIX' as indicator,
                vix as value,
                timestamp
            FROM market_data.volatility_indicators
            WHERE timestamp > NOW() - INTERVAL '1 day'
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        volatility = cursor.fetchall()
        cursor.close()

        return jsonify({
            'data': [dict(row) for row in volatility],
            'timestamp': datetime.now().isoformat(),
            'source': 'database'
        })
    except Exception as e:
        logger.error("market_volatility_error", error=str(e), exc_info=True)
        return jsonify({'error': str(e)}), 500


# ==============================================================================
# Economic Data Endpoints
# ==============================================================================

@app.route('/api/economic/fred')
@cache_result(timeout=Config.CACHE_TIMEOUT)
def economic_fred():
    """Get FRED economic indicators"""
    series_ids = request.args.get('series_ids', '').split(',')

    if not series_ids or series_ids == ['']:
        # Return most common indicators
        series_ids = ['GDP', 'UNRATE', 'CPIAUCSL', 'FEDFUNDS', 'DGS10', 'DFF']

    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT ON (series_id)
                series_id,
                title as series_name,
                value,
                date,
                units
            FROM economic_data.fred_series
            WHERE series_id = ANY(%s)
            ORDER BY series_id, date DESC
        """, (series_ids,))
        fred_data = cursor.fetchall()
        cursor.close()

        return jsonify({
            'data': [dict(row) for row in fred_data],
            'timestamp': datetime.now().isoformat(),
            'source': 'database'
        })
    except Exception as e:
        logger.error("economic_fred_error", error=str(e), exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/economic/fred/<series_id>')
@cache_result(timeout=Config.CACHE_TIMEOUT)
def economic_fred_single(series_id):
    """Get single FRED economic indicator by series ID"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                series_id,
                title as series_name,
                value,
                date,
                units,
                frequency
            FROM economic_data.fred_series
            WHERE series_id = %s
            ORDER BY date DESC
            LIMIT 1
        """, (series_id,))
        fred_data = cursor.fetchone()
        cursor.close()

        if fred_data:
            return jsonify({
                'data': dict(fred_data),
                'timestamp': datetime.now().isoformat(),
                'source': 'database'
            })
        else:
            return jsonify({
                'data': None,
                'message': f'No data found for series {series_id}',
                'timestamp': datetime.now().isoformat()
            }), 404
    except Exception as e:
        logger.error("economic_fred_single_error", series_id=series_id, error=str(e), exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/economic/indicators')
@cache_result(timeout=Config.CACHE_TIMEOUT)
def economic_indicators():
    """Get all economic indicators"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT ON (indicator_name)
                indicator_name,
                value,
                change_percent,
                date,
                source
            FROM economic_data.indicators
            WHERE date > NOW() - INTERVAL '90 days'
            ORDER BY indicator_name, date DESC
        """)
        indicators = cursor.fetchall()
        cursor.close()

        return jsonify({
            'data': [dict(row) for row in indicators],
            'timestamp': datetime.now().isoformat(),
            'source': 'database'
        })
    except Exception as e:
        logger.error("economic_indicators_error", error=str(e), exc_info=True)
        return jsonify({'error': str(e)}), 500


# ==============================================================================
# Analytics Endpoints
# ==============================================================================

@app.route('/api/analytics/correlations')
@cache_result(timeout=Config.CACHE_TIMEOUT)
def analytics_correlations():
    """Get asset correlations"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                asset_1,
                asset_2,
                correlation_60d,
                correlation_30d,
                correlation_7d,
                timestamp
            FROM analytics.correlations
            WHERE timestamp > NOW() - INTERVAL '1 day'
            ORDER BY timestamp DESC
            LIMIT 100
        """)
        correlations = cursor.fetchall()
        cursor.close()

        return jsonify({
            'data': [dict(row) for row in correlations],
            'timestamp': datetime.now().isoformat(),
            'source': 'database'
        })
    except Exception as e:
        logger.error("analytics_correlations_error", error=str(e), exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/sector_rotation')
@cache_result(timeout=Config.CACHE_TIMEOUT)
def analytics_sector_rotation():
    """Get sector rotation analysis"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT ON (sector)
                sector,
                etf_symbol,
                price,
                change_percent_1d,
                change_percent_5d,
                change_percent_1m,
                relative_strength,
                timestamp
            FROM analytics.sector_rotation
            WHERE timestamp > NOW() - INTERVAL '1 day'
            ORDER BY sector, timestamp DESC
        """)
        sectors = cursor.fetchall()
        cursor.close()

        return jsonify({
            'data': [dict(row) for row in sectors],
            'timestamp': datetime.now().isoformat(),
            'source': 'database'
        })
    except Exception as e:
        logger.error("analytics_sector_rotation_error", error=str(e), exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/analytics/sentiment')
@cache_result(timeout=Config.CACHE_TIMEOUT)
def analytics_sentiment():
    """Get market sentiment indicators"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT ON (indicator)
                indicator,
                value,
                interpretation,
                timestamp
            FROM analytics.sentiment_indicators
            WHERE timestamp > NOW() - INTERVAL '1 day'
            ORDER BY indicator, timestamp DESC
        """)
        sentiment = cursor.fetchall()
        cursor.close()

        return jsonify({
            'data': [dict(row) for row in sentiment],
            'timestamp': datetime.now().isoformat(),
            'source': 'database'
        })
    except Exception as e:
        logger.error("analytics_sentiment_error", error=str(e), exc_info=True)
        return jsonify({'error': str(e)}), 500


# ==============================================================================
# Symbol Database Endpoints
# ==============================================================================

@app.route('/api/db/search')
def db_search():
    """Search symbol database"""
    query = request.args.get('query', '')
    limit = int(request.args.get('limit', '10'))

    if not query:
        return jsonify({'error': 'query parameter required'}), 400

    try:
        # Search across all market data tables
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT
                symbol,
                'index' as type
            FROM preloaded_market_data WHERE data_type = 'index' AND symbol ILIKE %s OR name ILIKE %s

            UNION

            SELECT DISTINCT
                symbol,
                'commodity' as type
            FROM preloaded_market_data WHERE data_type IN ('commodity', 'gold', 'oil', 'copper')
            WHERE symbol ILIKE %s OR name ILIKE %s

            UNION

            SELECT DISTINCT
                symbol,
                'crypto' as type
            FROM preloaded_market_data WHERE data_type = 'crypto'
            WHERE symbol ILIKE %s OR name ILIKE %s

            LIMIT %s
        """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%',
              f'%{query}%', f'%{query}%', limit))

        results = cursor.fetchall()
        cursor.close()

        return jsonify({
            'query': query,
            'results': [dict(row) for row in results],
            'count': len(results)
        })
    except Exception as e:
        logger.error("db_search_error", error=str(e), exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/db/stats')
def db_stats():
    """Get database statistics"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(DISTINCT symbol) as total_symbols
            FROM (
                SELECT symbol FROM preloaded_market_data WHERE data_type = 'index'
                UNION
                SELECT symbol FROM preloaded_market_data WHERE data_type IN ('commodity', 'gold', 'oil', 'copper')
                UNION
                SELECT symbol FROM preloaded_market_data WHERE data_type = 'forex'
                UNION
                SELECT symbol FROM preloaded_market_data WHERE data_type = 'crypto'
            ) AS all_symbols
        """)
        stats = cursor.fetchone()
        cursor.close()

        return jsonify({
            'total_symbols': stats['total_symbols'] if stats else 0,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error("db_stats_error", error=str(e), exc_info=True)
        return jsonify({'error': str(e)}), 500


# ==============================================================================
# HTML Page Routes
# ==============================================================================
# Additional Data Endpoints for Pages
# ==============================================================================

@app.route('/api/market/symbol/<symbol>')
@cache_result(timeout=Config.CACHE_TIMEOUT)
def market_symbol(symbol):
    """Get specific market symbol data"""
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Try different tables based on symbol
        # Query unified preloaded_market_data table
        
        for table in tables:
            cursor.execute(f"""
                SELECT DISTINCT ON (symbol)
                symbol,
                    price,
                    change_percent,
                    volume,
                    timestamp
                FROM {table}
                WHERE symbol = %s 
                    AND timestamp > NOW() - INTERVAL '1 day'
                ORDER BY timestamp DESC
                LIMIT 1
            """, (symbol.upper(),))
            
            result = cursor.fetchone()
            if result:
                cursor.close()
                return jsonify({
                    'data': dict(result),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'database'
                })
        
        cursor.close()
        return jsonify({'error': 'Symbol not found'}), 404
        
    except Exception as e:
        logger.error("market_symbol_error", symbol=symbol, error=str(e), exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/yahoo/quote')
def yahoo_quote():
    """Yahoo Finance quote endpoint compatibility"""
    try:
        symbols = request.args.get('symbols', '').split(',')
        results = []
        
        conn = get_db()
        cursor = conn.cursor()
        
        for symbol in symbols:
            if not symbol:
                continue
                
            # Query all market data tables
            cursor.execute("""
                SELECT DISTINCT ON (symbol)
                symbol,
                    price,
                    change_percent,
                    volume,
                    timestamp
                FROM (
                    SELECT symbol,
                price, change_percent, volume, timestamp FROM market_data.indices
                    UNION ALL
                    SELECT symbol,
                price, change_percent, volume, timestamp FROM preloaded_market_data WHERE data_type IN ('commodity', 'gold', 'oil', 'copper')  
                    UNION ALL
                    SELECT symbol,
                price, change_percent_24h as change_percent, NULL as volume, timestamp FROM preloaded_market_data WHERE data_type = 'crypto'
                ) combined_data
                WHERE symbol = %s 
                    AND timestamp > NOW() - INTERVAL '1 day'
                ORDER BY timestamp DESC
                LIMIT 1
            """, (symbol.upper(),))
            
            result = cursor.fetchone()
            if result:
                results.append(dict(result))
        
        cursor.close()
        
        return jsonify({
            'quotes': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error("yahoo_quote_error", error=str(e), exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/yahoo/chart/<symbol>')
@cache_result(timeout=Config.CACHE_TIMEOUT)
def yahoo_chart(symbol):
    """Yahoo Finance chart data compatibility"""
    try:
        interval = request.args.get('interval', '1d')
        range_period = request.args.get('range', '1mo')
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Generate sample data for recent prices
        cursor.execute("""
            SELECT symbol, price, timestamp
            FROM preloaded_market_data WHERE data_type = 'index' AND symbol = %s 
                AND timestamp > NOW() - INTERVAL '30 days'
            ORDER BY timestamp DESC
            LIMIT 100
        """, (symbol.upper(),))
        
        data = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        
        return jsonify({
            'symbol': symbol.upper(),
            'data': data,
            'interval': interval,
            'range': range_period,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error("yahoo_chart_error", symbol=symbol, error=str(e), exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/fred/series')
@cache_result(timeout=Config.CACHE_TIMEOUT)
def fred_series():
    """FRED economic series endpoint"""
    try:
        series_id = request.args.get('series_id')
        search_text = request.args.get('search_text')
        limit = int(request.args.get('limit', '100'))
        
        conn = get_db()
        cursor = conn.cursor()
        
        if series_id:
            cursor.execute("""
                SELECT *
                FROM economic_data.fred_series
                WHERE series_id = %s
                ORDER BY date DESC
                LIMIT 1
            """, (series_id,))
            
            result = cursor.fetchone()
            cursor.close()
            
            return jsonify({
                'series': dict(result) if result else None,
                'timestamp': datetime.now().isoformat()
            })
            
        else:
            # Return list of available series
            cursor.execute("""
                SELECT DISTINCT series_id, title
                FROM economic_data.fred_series
                LIMIT %s
            """, (limit,))
            
            results = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            
            return jsonify({
                'series': results,
                'count': len(results),
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error("fred_series_error", error=str(e), exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/fred/series/observations')
@cache_result(timeout=Config.CACHE_TIMEOUT)
def fred_observations():
    """FRED series observations endpoint"""
    try:
        series_id = request.args.get('series_id')
        limit = int(request.args.get('limit', '100'))
        
        if not series_id:
            return jsonify({'error': 'series_id parameter required'}), 400
            
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT *
            FROM economic_data.fred_series
            WHERE series_id = %s
            ORDER BY date DESC
            LIMIT %s
        """, (series_id, limit))
        
        data = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        
        return jsonify({
            'observations': data,
            'series_id': series_id,
            'count': len(data),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error("fred_observations_error", error=str(e), exc_info=True)
        return jsonify({'error': str(e)}), 500


# Stock market data endpoints for pages
@app.route('/api/stock/<symbol>')
@cache_result(timeout=Config.CACHE_TIMEOUT)
def stock_data(symbol):
    """Get stock data for symbol"""
    return market_symbol(symbol)


@app.route('/api/stock/<symbol>', methods=['POST'])
def stock_data_post(symbol):
    """POST version of stock data"""
    return market_symbol(symbol)


# ==============================================================================

@app.route('/')
def index():
    """Serve main index page"""
    return send_from_directory('/app', 'index.html')


@app.route('/<path:path>')
def serve_file(path):
    """Serve static files"""
    return send_from_directory('/app', path)


# ==============================================================================
# Error Handlers
# ==============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error("internal_server_error", error=str(error), exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500


# ==============================================================================
# Startup
# ==============================================================================

if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║           SPARTAN RESEARCH STATION                           ║
║           Web Server                                          ║
║                                                               ║
║  Database-First Architecture                                 ║
║  ALL data from PostgreSQL (NEVER external APIs)              ║
║  Instant page loads with Redis caching                       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

Starting web server on ports 8888 and 9000...
    """)

    app.run(
        host='0.0.0.0',
        port=8888,
        debug=Config.DEBUG
    )
