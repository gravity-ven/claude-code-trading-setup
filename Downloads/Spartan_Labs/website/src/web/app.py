#!/usr/bin/env python3
"""
Simple Flask Web Server for Spartan Research Station
Basic functionality to serve the main dashboard
"""

import json
from flask import Flask, jsonify, render_template
from flask_cors import CORS
# Optional marketaux import - provide stub if not available
try:
    from marketaux_api import get_news
except ImportError:
    def get_news():
        return {"articles": [], "error": "marketaux_api module not available"}
from http.server import HTTPServer
import socketserver
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import logging
import psycopg
from psycopg.rows import dict_row
from datetime import datetime
from flask import request
from PIL import Image
import io

# Import the DataGuardian (optional)
try:
    from data_guardian import DataGuardian
except ImportError:
    DataGuardian = None  # Will be checked before use

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize YOLO
try:
    from yolo_inference import YOLOInference
    yolo_model = YOLOInference()
except Exception as e:
    logger.error(f"Failed to initialize YOLO: {e}")
    yolo_model = None

# Database configuration
class Config:
    DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/spartan_research_db'
    REDIS_URL = 'redis://localhost:6379/0'
    CACHE_TIMEOUT = 300
    MAX_DB_CONNECTIONS = 50

app.config.from_object(Config)

# Database connection
def get_db():
    try:
        conn = psycopg.connect(
            Config.DATABASE_URL,
            row_factory=dict_row
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

# Cache decorator
def cache_result(timeout=300):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = f"cache:{f.__name__}:{str(args)}:{str(kwargs)}"
            try:
                r = get_redis()
                cached = r.get(cache_key)
                if cached:
                    logger.debug(f"cache_hit: {f.__name__} cache_key: {cache_key}")
                    # Return cached data as-is (Flask Response object)
                    if isinstance(cached_data, dict):
                        return jsonify(cached_data)
                    elif isinstance(cached_data, str):
                        return jsonify(cached_data) 
                    # For Flask Response object, extract the JSON data
                    if hasattr(cached_data, 'get_json'):
                        return cached_data.get_json()
                    # If result is a Flask Response object
                    if isinstance(cached_data, tuple):  # (response, status_code)
                        cache_data = response[0].get_json() if response and isinstance(response[0], str) else None
                r.setex(cache_key, timeout, json.dumps(cache_data))
                logger.debug(f"cache_set: {f.__name__} cache_key: {cache_key}")
                logger.debug(f"cache_set timeout: {timeout}")
            except Exception as e:
                logger.warning(f"cache_write_error: {e}")
                # Continue without cache
            
            return result
        return decorated_function

@app.route('/api/yolo/detect', methods=['POST'])
def detect_objects():
    """
    Endpoint for YOLO object detection.
    Expects an image file in the request.
    """
    if not yolo_model:
        return jsonify({'error': 'YOLO model not initialized'}), 500

    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        # Read image file
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Run detection
        detections = yolo_model.detect_objects(image)
        
        return jsonify({
            'status': 'success',
            'detections': detections
        })
    except Exception as e:
        logger.error(f"Detection endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    """Serve main index page with live data"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get market data directly from database
        cursor.execute("""
            SELECT 
                symbol,
                name,
                price,
                change_percent,
                volume,
                timestamp
            FROM market_data.indices
            WHERE timestamp > NOW() - INTERVAL '1 day'
            ORDER BY timestamp DESC
            LIMIT 10
        """)
        indices = cursor.fetchall()
        cursor.close()
        
        # Create live dashboard section
        dashboard_html = '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <title>Spartan Research Station - Live Dashboard</title>
            <style>
                body {
                    background: linear-gradient(135deg, #1a1f3a, #2d41520, #1a1f3a, #0a0e27);
                    color: #ffffff;
                    margin: 0;
                    padding: 20px;
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                }
                .live-dashboard {
                    background: rgba(15, 15, 15, 0.95);
                    border-radius: 12px;
                    padding: 25px;
                    box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
                }
                .metric {
                    display: inline-block;
                    padding: 12px;
                    border-radius: 6px;
                    background: rgba(0, 255, 0, 0.1);
                    min-width: 120px;
                    text-align: center;
                    margin: 0 5px;
                }
                .metric .value {
                    font-weight: 700;
                    font-size: 18px;
                    display: block;
                    text-align: center;
                }
                .status.healthy { 
                    background: rgba(0, 255, 0, 0.1);
                    color: #28a745;
                    border: 1px solid rgba(0, 255, 0, 0.1);
                }
                .status.failed {
                    background: rgba(255, 0, 0, 0.1);
                    color: #dc3545;
                    border: 1px solid rgba(255, 0, 0, 0.1);
                }
                
                .live-metrics {
                    display: flex;
                    justify-content: space-between;
                    margin: 0 10px;
                    min-width: 250px;
                }
                
                .live-metrics .metric {
                    margin-right: 8px;
                }
            </style>
            </head>
            <body>
                <div class="live-dashboard">
                    <h1>🚀 Spartan Research Station</h1>
                    <div class="status healthy">✅ System Healthy</div>
                    
                    <div class="section">
                        <h2>📊 Market Intelligence</h2>
                        <div class="metrics dashboard-grid">
                            <div class="metric" id="indices-metric">
                                <span class="value">❌</span>
                                <span class="label">Market Indices</span>
                            </div>
                            <div class="metric" id="commodities-metric">
                                <span class="value">❌</span>
                                <span class="label">Commodities</span>
                            </div>
                            <div class="metric" id="forex-metric">
                                <span class="value">❌</span>
                                <span class="label">Forex</span>
                            </div>
                            <div class="metric" id="crypto-metric">
                                <span class="value">❌</span>
                                <span class="label">Crypto</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="section">
                        <h2>💰 Economic Intelligence</h2>
                        <div class="metrics dashboard-grid">
                            <div class="metric">
                                <span class="value">❌</span>
                                <span class="label">Economic Indicators</span>
                            </div>
                            <div class="metric">
                                <span class="value">❌</span>
                                <span class="label">All Indicators</span>
                            </div>
                            <div class="metric">
                                <span class="value">❌</span>
                                <span class="label">FRED Series</span>
                            </div>
                        </div>
                    
                    <div class="section">
                        <h2>📊 Database Schema</h2>
                        <div class="metrics dashboard-grid">
                            <div class="metric">
                                <span class="value">❌</span>
                                <span class="label">Total Symbols</span>
                            </div>
                            <div class="metric">
                                <span class="value">❌</span>
                                <span class="label">Countries</span>
                            </div>
                            <div class="metric">
                                <span class="value">❌</span>
                                <span class="label">Asset Types</span>
                            </div>
                        </div>
                        
                        <div class="section">
                            <h2>🔄 Analytics</h2>
                            <div class="metrics dashboard-grid">
                                <div class="metric">
                                    <span class="value">❌</span>
                                    <span class="label">Correlations</span>
                                </div>
                                <div class="metric">
                                    <span class="value">❌</span>
                                    <span class="label">Sector Rotation</span>
                                </div>
                                <div class="metric">
                                    <span class="value">❌</span>
                                    <span class="label">Sentiment</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="section">
                            <h2>🛠️ Status</h2>
                            <div class="metrics dashboard-grid">
                                <div class="metric">
                                    <span class="value">❌</span>
                                    <span class="label">Connection</span>
                                </div>
                                <div class="metric">
                                    <span class="value">❌</span>
                                    <span class="label">Redis Cache</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="section">
                            <h2>⚠️ Compatibility</h2>
                            <div class="status warning">
                                <span>Yahoo Finance API Not Available</span>
                                <p>Yahoo Finance endpoints require proper API setup.</p>
                            </div>
                        </div>
                        
                        <div class="section">
                            <h2>Cached Status</h2>
                            <div class="metrics dashboard-grid">
                                <div class="metric">
                                    <span class="value">Live</span>
                                    <span class="label">Cache Status</span>
                                </div>
                                <div class="metric">
                                    <span class="value">❌</span>
                                    <span class="label">Real Data Available</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p>Last Updated: <span id="current-time">NOW</span></p>
                    </div>
                </div>
                
            </body>
            
            <script>
                async function loadLiveStats() {
                    try:
                        const health = await fetch('http://localhost:8888/health').json();
                        database_status = await fetch('http://localhost:8888/api/db/stats').json();
                        
                        document.getElementById('db-stats-value').textContent = database_status['total_symbols'];
                        document.getElementById('current-time').textContent = new Date().toISOString();
                        document.getElementById('cache-status').textContent = database_status.get('refresh_status', {}).get('refresh_status', {});
                        
                        if (health['status'] === 'healthy'):
                            document.getElementById('connection-status').textContent = '✅ Database and Redis connected';
                        else:
                            document.getElementById('connection-status').textContent = '❌ Database or Redis connection issue';
                    } catch (e) {
                        document.getElementById('connection-status').textContent = f'❌ DB/Redis Error: {e}';
                    }
                }
                
                loadLiveStats();
                
                // Test basic symbol data
                async function testSymbolData(symbol):
                    try:
                        const response = await fetch(`http://localhost:8888/api/market/symbol/${symbol}`);
                        const data = await response.json();
                        if data and 'data' in data:
                            document.getElementById(`test-${symbol}`).textContent = f'✅ {data['name']} (${data['price'] if 'price' in data else 'N/A'})';
                        return True;
                    return False;
                    } catch (e) {
                        document.getElementById(`test-${symbol}`).textContent = f'❌ Connection Error: {e}';
                        return False;
                    }
                
                // Test FRED economic data
                const testFreds = ['GDP', 'UNRATE', 'CPIAUCSL', 'FEDFUNDS'];
                for series in testFreds:
                    success, _ = test_symbol_data(series);
                    if success:
                        document.getElementById(`test-${series}`).textContent = f'✅ {series['title']} ({series['value']})';
                    else:
                        document.getElementById(`test-${series}`).textContent = f'❌ {series} - No data';
                
                // Test correlations
                success, _ = test_symbol_data('SPY');
                if success: document.getElementById('test-SPY').textContent = f'✅ {data['name']}';
                else: document.getElementById('test-SPY').textContent = f'❌ SPY not found';
                
            except (e) {
                console.error(f'Page load error: {e}');
            }
            
        window.addEventListener('DOMContentLoaded', loadLiveStats);
        </script>
    </body>
    </html>
'''
        
        return dashboard_html
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        return "An error occurred", 500

@app.route('/guardian-test')
def guardian_test():
    """
    A test route to demonstrate the DataGuardian's functionality.
    """
    # 1. Define the data needed for this page
    page_requirements = [
        {'symbol': 'AAPL', 'data_type': 'stock', 'period_days': 30},
        {'symbol': 'GOOG', 'data_type': 'stock', 'period_days': 30},
        {'symbol': 'BTC-USD', 'data_type': 'crypto', 'period_days': 30},
        # Add a symbol that is likely to fail to test the guardian
        {'symbol': 'NONEXISTENT_SYMBOL_XYZ', 'data_type': 'stock', 'period_days': 30},
    ]

    # 2. Create a DataGuardian instance for the page
    guardian = DataGuardian(page_requirements)

    # 3. Verify data availability
    all_data_available = guardian.verify_data_availability()

    # 4. Render the page with the fetched data or an error message
    return render_template(
        'guardian_test.html',
        all_data_available=all_data_available,
        fetched_data=guardian.fetched_data
    )

@app.route('/api/news')
def news():
    """Serve news data"""
    news_data = get_news()
    return jsonify(news_data)

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static HTML files"""
    from flask import send_from_directory
    import os

    # Get the directory where app.py is located
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Check if file exists
    file_path = os.path.join(base_dir, filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(base_dir, filename)
    else:
        return "File not found", 404


# ============================================================================
# SIERRA SCANNER AI - INTEGRATED ROUTES
# ============================================================================
# Part of Nano Banana Scanner suite
# ULTIMATE RULE: Maximum Profits. Minimum Losses. Minimum Drawdown.

# Initialize Sierra Scanner (lazy loading)
sierra_scanner = None

def get_sierra_scanner():
    """Get or initialize the Sierra Scanner instance"""
    global sierra_scanner
    if sierra_scanner is None:
        try:
            from sierra_scanner_ai import SierraScannerAI
            sierra_scanner = SierraScannerAI()
            logger.info("Sierra Scanner AI initialized")
        except ImportError as e:
            logger.warning(f"Sierra Scanner AI module not available: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize Sierra Scanner: {e}")
            return None
    return sierra_scanner


@app.route('/api/sierra-scanner/health', methods=['GET'])
def sierra_health():
    """Sierra Scanner health check"""
    scanner = get_sierra_scanner()
    return jsonify({
        'status': 'healthy' if scanner else 'unavailable',
        'service': 'Sierra Scanner AI',
        'integrated': True,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/sierra-scanner/status', methods=['GET'])
def sierra_status():
    """Get Sierra Scanner status"""
    scanner = get_sierra_scanner()
    if not scanner:
        return jsonify({
            'is_running': False,
            'sierra_chart_detected': False,
            'scan_count': 0,
            'last_scan': None,
            'symbols_tracked': 0,
            'symbols': [],
            'error': 'Scanner not initialized'
        })
    return jsonify(scanner.get_status())


@app.route('/api/sierra-scanner/recommendations', methods=['GET'])
def sierra_recommendations():
    """Get current recommendations for all symbols"""
    scanner = get_sierra_scanner()
    if not scanner:
        return jsonify({
            'recommendations': {},
            'timestamp': datetime.now().isoformat(),
            'error': 'Scanner not initialized'
        })

    recommendations = scanner.get_recommendations()

    # Count signals by type
    buy_count = sum(1 for r in recommendations.values() if r.get('signal') == 'BUY')
    sell_count = sum(1 for r in recommendations.values() if r.get('signal') == 'SELL')
    hold_count = sum(1 for r in recommendations.values() if r.get('signal') == 'HOLD')

    return jsonify({
        'recommendations': recommendations,
        'summary': {
            'total': len(recommendations),
            'buy': buy_count,
            'sell': sell_count,
            'hold': hold_count
        },
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/sierra-scanner/symbol/<symbol>', methods=['GET'])
def sierra_symbol_detail(symbol):
    """Get detailed analysis for a specific symbol"""
    scanner = get_sierra_scanner()
    if not scanner:
        return jsonify({'error': 'Scanner not initialized'}), 503

    if symbol not in scanner.state.symbols:
        return jsonify({'error': 'Symbol not found'}), 404

    state = scanner.state.symbols[symbol]
    return jsonify({
        'symbol': symbol,
        'current_recommendation': state.last_analysis.to_dict() if state.last_analysis else None,
        'win_rate': state.win_rate,
        'total_predictions': state.total_predictions,
        'correct_predictions': state.correct_predictions,
        'analyses_count': len(state.analyses)
    })


@app.route('/api/sierra-scanner/start', methods=['POST'])
def sierra_start():
    """Start the Sierra Scanner"""
    scanner = get_sierra_scanner()
    if not scanner:
        return jsonify({'status': 'error', 'message': 'Scanner not initialized'}), 503

    scanner.start()
    return jsonify({'status': 'started', 'message': 'Sierra Scanner AI started'})


@app.route('/api/sierra-scanner/stop', methods=['POST'])
def sierra_stop():
    """Stop the Sierra Scanner"""
    scanner = get_sierra_scanner()
    if not scanner:
        return jsonify({'status': 'error', 'message': 'Scanner not initialized'}), 503

    scanner.stop()
    return jsonify({'status': 'stopped', 'message': 'Sierra Scanner AI stopped'})


@app.route('/api/sierra-scanner/scan', methods=['POST'])
def sierra_force_scan():
    """Force an immediate scan"""
    scanner = get_sierra_scanner()
    if not scanner:
        return jsonify({'status': 'error', 'message': 'Scanner not initialized'}), 503

    if not scanner.state.is_running:
        return jsonify({'status': 'error', 'message': 'Scanner not running. Start it first.'}), 400

    # Trigger immediate scan
    scanner._perform_scan()

    return jsonify({
        'status': 'success',
        'message': 'Scan completed',
        'scan_count': scanner.state.scan_count,
        'symbols_tracked': len(scanner.state.symbols)
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8889, debug=False)
