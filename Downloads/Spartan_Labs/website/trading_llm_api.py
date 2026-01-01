#!/usr/bin/env python3
"""
Trading LLM API - Flask server for Trading AI Agent System
Port: 9005

Integrates with Spartan Labs infrastructure:
- Barometers API (Port 9001)
- CFTC COT API (Port 5001)
- Breakthrough Insights API (Port 5003)
- Macro Regime Tracker (Port 9002)

PLATINUM RULE ENFORCED: All data from verified sources only
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from functools import wraps
import threading
import time

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor

# Import the Trading LLM Engine
from trading_llm_engine import (
    TradingLLMEngine,
    TradingSignal,
    AssetClass,
    SignalType,
    TimeHorizon,
    get_engine
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configuration
API_PORT = int(os.getenv('TRADING_LLM_PORT', 9005))
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'spartan_website_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

# Global engine instance
engine: Optional[TradingLLMEngine] = None

# Cache for expensive operations
_cache = {}
_cache_lock = threading.Lock()


def get_db_connection():
    """Get PostgreSQL connection"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None


def cache_response(ttl_seconds: int = 60):
    """Decorator to cache API responses"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            cache_key = f"{f.__name__}:{str(args)}:{str(kwargs)}"
            now = datetime.now()

            with _cache_lock:
                if cache_key in _cache:
                    cached_time, cached_value = _cache[cache_key]
                    if now - cached_time < timedelta(seconds=ttl_seconds):
                        return cached_value

            result = f(*args, **kwargs)

            with _cache_lock:
                _cache[cache_key] = (now, result)

            return result
        return wrapped
    return decorator


# =============================================================================
# HEALTH & STATUS ENDPOINTS
# =============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    global engine

    status = {
        'service': 'Trading LLM API',
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'components': {
            'engine': engine is not None,
            'database': False,
            'barometers_api': False,
            'cot_api': False
        }
    }

    # Check database
    conn = get_db_connection()
    if conn:
        status['components']['database'] = True
        conn.close()

    # Check dependent APIs
    if engine:
        barometer_data = engine.get_barometer_data()
        status['components']['barometers_api'] = barometer_data is not None

        cot_data = engine.get_cot_data('ES', weeks=1)
        status['components']['cot_api'] = cot_data is not None

    all_healthy = all(status['components'].values())
    status['status'] = 'healthy' if all_healthy else 'degraded'

    return jsonify(status), 200 if all_healthy else 503


@app.route('/api/status', methods=['GET'])
def api_status():
    """Detailed API status"""
    global engine

    context = engine.build_market_context() if engine else None

    return jsonify({
        'api': 'Trading LLM API',
        'port': API_PORT,
        'uptime': 'running',
        'market_context': context.to_dict() if context else None,
        'capabilities': [
            'futures_analysis',
            'forex_analysis',
            'stock_analysis',
            'bond_analysis',
            'market_scan',
            'ai_reasoning'
        ],
        'data_sources': [
            'Barometers API (Port 9001)',
            'CFTC COT API (Port 5001)',
            'Breakthrough Insights (Port 5003)',
            'Macro Regime Tracker (Port 9002)'
        ]
    })


# =============================================================================
# MARKET CONTEXT ENDPOINTS
# =============================================================================

@app.route('/api/context', methods=['GET'])
@cache_response(ttl_seconds=60)
def get_market_context():
    """Get current market context from all data sources"""
    global engine

    if not engine:
        return jsonify({'error': 'Engine not initialized'}), 500

    force_refresh = request.args.get('refresh', 'false').lower() == 'true'
    context = engine.build_market_context(force_refresh=force_refresh)

    if not context:
        return jsonify({'error': 'Failed to build market context'}), 500

    return jsonify({
        'success': True,
        'context': context.to_dict(),
        'summary': {
            'risk_level': context.risk_status,
            'score': context.composite_score,
            'mode': context.market_mode,
            'vix': context.vix_level
        }
    })


@app.route('/api/context/summary', methods=['GET'])
@cache_response(ttl_seconds=30)
def get_context_summary():
    """Get condensed market context summary"""
    global engine

    if not engine:
        return jsonify({'error': 'Engine not initialized'}), 500

    context = engine.build_market_context()

    if not context:
        return jsonify({'error': 'Failed to build market context'}), 500

    # Determine overall bias
    if context.composite_score >= 70 and context.market_mode == 'Risk-On':
        overall_bias = 'BULLISH'
    elif context.composite_score <= 30 or context.market_mode == 'Risk-Off':
        overall_bias = 'BEARISH'
    else:
        overall_bias = 'NEUTRAL'

    return jsonify({
        'overall_bias': overall_bias,
        'risk_status': context.risk_status,
        'composite_score': context.composite_score,
        'market_mode': context.market_mode,
        'vix': context.vix_level,
        'growth': context.growth_regime,
        'inflation': context.inflation_regime,
        'timestamp': context.timestamp.isoformat()
    })


# =============================================================================
# SIGNAL GENERATION ENDPOINTS
# =============================================================================

@app.route('/api/analyze/futures/<symbol>', methods=['GET'])
def analyze_futures(symbol: str):
    """Analyze a futures contract"""
    global engine

    if not engine:
        return jsonify({'error': 'Engine not initialized'}), 500

    signal = engine.analyze_futures(symbol.upper())

    if not signal:
        return jsonify({'error': f'Analysis failed for {symbol}'}), 500

    return jsonify({
        'success': True,
        'signal': signal.to_dict()
    })


@app.route('/api/analyze/forex/<pair>', methods=['GET'])
def analyze_forex(pair: str):
    """Analyze a forex pair"""
    global engine

    if not engine:
        return jsonify({'error': 'Engine not initialized'}), 500

    signal = engine.analyze_forex(pair.upper())

    if not signal:
        return jsonify({'error': f'Analysis failed for {pair}'}), 500

    return jsonify({
        'success': True,
        'signal': signal.to_dict()
    })


@app.route('/api/analyze/stock/<symbol>', methods=['GET'])
def analyze_stock(symbol: str):
    """Analyze a stock"""
    global engine

    if not engine:
        return jsonify({'error': 'Engine not initialized'}), 500

    signal = engine.analyze_stock(symbol.upper())

    if not signal:
        return jsonify({'error': f'Analysis failed for {symbol}'}), 500

    return jsonify({
        'success': True,
        'signal': signal.to_dict()
    })


@app.route('/api/analyze/bonds/<symbol>', methods=['GET'])
def analyze_bonds(symbol: str):
    """Analyze bonds/treasuries"""
    global engine

    if not engine:
        return jsonify({'error': 'Engine not initialized'}), 500

    signal = engine.analyze_bonds(symbol.upper())

    if not signal:
        return jsonify({'error': f'Analysis failed for {symbol}'}), 500

    return jsonify({
        'success': True,
        'signal': signal.to_dict()
    })


@app.route('/api/analyze', methods=['POST'])
def analyze_symbol():
    """
    Generic analysis endpoint
    Body: {"symbol": "AAPL", "asset_class": "stocks"}
    """
    global engine

    if not engine:
        return jsonify({'error': 'Engine not initialized'}), 500

    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    symbol = data.get('symbol', '').upper()
    asset_class = data.get('asset_class', 'stocks').lower()

    if not symbol:
        return jsonify({'error': 'Symbol required'}), 400

    # Route to appropriate analyzer
    signal = None
    if asset_class == 'futures':
        signal = engine.analyze_futures(symbol)
    elif asset_class == 'forex':
        signal = engine.analyze_forex(symbol)
    elif asset_class == 'stocks':
        signal = engine.analyze_stock(symbol)
    elif asset_class == 'bonds':
        signal = engine.analyze_bonds(symbol)
    else:
        return jsonify({'error': f'Unknown asset class: {asset_class}'}), 400

    if not signal:
        return jsonify({'error': f'Analysis failed for {symbol}'}), 500

    return jsonify({
        'success': True,
        'signal': signal.to_dict()
    })


# =============================================================================
# MARKET SCAN ENDPOINTS
# =============================================================================

@app.route('/api/scan', methods=['GET'])
@cache_response(ttl_seconds=300)
def scan_all_markets():
    """Scan all markets for trading opportunities"""
    global engine

    if not engine:
        return jsonify({'error': 'Engine not initialized'}), 500

    results = engine.scan_all_markets()

    # Convert signals to dicts
    formatted_results = {}
    total_signals = 0

    for asset_class, signals in results.items():
        formatted_results[asset_class] = [s.to_dict() for s in signals]
        total_signals += len(signals)

    return jsonify({
        'success': True,
        'total_signals': total_signals,
        'timestamp': datetime.now().isoformat(),
        'results': formatted_results
    })


@app.route('/api/scan/<asset_class>', methods=['GET'])
def scan_asset_class(asset_class: str):
    """Scan a specific asset class"""
    global engine

    if not engine:
        return jsonify({'error': 'Engine not initialized'}), 500

    asset_class = asset_class.lower()
    valid_classes = ['futures', 'forex', 'stocks', 'bonds']

    if asset_class not in valid_classes:
        return jsonify({'error': f'Invalid asset class. Use: {valid_classes}'}), 400

    # Scan all and filter
    results = engine.scan_all_markets()
    signals = results.get(asset_class, [])

    return jsonify({
        'success': True,
        'asset_class': asset_class,
        'signal_count': len(signals),
        'signals': [s.to_dict() for s in signals]
    })


@app.route('/api/top-signals', methods=['GET'])
@cache_response(ttl_seconds=120)
def get_top_signals():
    """Get top trading signals across all asset classes"""
    global engine

    if not engine:
        return jsonify({'error': 'Engine not initialized'}), 500

    limit = request.args.get('limit', 10, type=int)
    min_confidence = request.args.get('min_confidence', 60, type=int)

    results = engine.scan_all_markets()

    # Flatten and filter all signals
    all_signals = []
    for signals in results.values():
        for signal in signals:
            if signal.confidence >= min_confidence:
                all_signals.append(signal)

    # Sort by confidence
    all_signals.sort(key=lambda x: x.confidence, reverse=True)
    top_signals = all_signals[:limit]

    return jsonify({
        'success': True,
        'total_found': len(all_signals),
        'returned': len(top_signals),
        'min_confidence': min_confidence,
        'signals': [s.to_dict() for s in top_signals]
    })


# =============================================================================
# AI ANALYSIS ENDPOINTS
# =============================================================================

@app.route('/api/ai-analysis', methods=['POST'])
def get_ai_analysis():
    """
    Get detailed AI analysis using Claude API
    Body: {"symbol": "ES", "asset_class": "futures"}
    """
    global engine

    if not engine:
        return jsonify({'error': 'Engine not initialized'}), 500

    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    symbol = data.get('symbol', '').upper()
    asset_class = data.get('asset_class', 'stocks')

    if not symbol:
        return jsonify({'error': 'Symbol required'}), 400

    analysis = engine.get_ai_analysis(symbol, asset_class)

    return jsonify({
        'success': True,
        'symbol': symbol,
        'asset_class': asset_class,
        'analysis': analysis,
        'timestamp': datetime.now().isoformat()
    })


# =============================================================================
# TRADE LOGGING ENDPOINTS
# =============================================================================

@app.route('/api/trades', methods=['GET'])
def get_trades():
    """Get logged trades"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        limit = request.args.get('limit', 50, type=int)
        symbol = request.args.get('symbol')

        query = """
            SELECT * FROM trading_llm_trades
            WHERE 1=1
        """
        params = []

        if symbol:
            query += " AND symbol = %s"
            params.append(symbol.upper())

        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        cursor.execute(query, params)
        trades = cursor.fetchall()

        return jsonify({
            'success': True,
            'count': len(trades),
            'trades': trades
        })

    except Exception as e:
        logger.error(f"Failed to fetch trades: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/trades', methods=['POST'])
def log_trade():
    """Log a new trade"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    try:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO trading_llm_trades (
                symbol, asset_class, signal_type, entry_price,
                stop_loss, take_profit, position_size, confidence,
                reasoning, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data.get('symbol', '').upper(),
            data.get('asset_class', 'stocks'),
            data.get('signal_type', 'buy'),
            data.get('entry_price'),
            data.get('stop_loss'),
            data.get('take_profit'),
            data.get('position_size', 0),
            data.get('confidence', 0),
            data.get('reasoning', ''),
            'open'
        ))

        trade_id = cursor.fetchone()[0]
        conn.commit()

        return jsonify({
            'success': True,
            'trade_id': trade_id,
            'message': 'Trade logged successfully'
        })

    except Exception as e:
        logger.error(f"Failed to log trade: {e}")
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/trades/<int:trade_id>/close', methods=['POST'])
def close_trade(trade_id: int):
    """Close a trade with exit details"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400

    try:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE trading_llm_trades
            SET exit_price = %s,
                pnl = %s,
                status = 'closed',
                closed_at = NOW()
            WHERE id = %s
        """, (
            data.get('exit_price'),
            data.get('pnl', 0),
            trade_id
        ))

        conn.commit()

        return jsonify({
            'success': True,
            'trade_id': trade_id,
            'message': 'Trade closed'
        })

    except Exception as e:
        logger.error(f"Failed to close trade: {e}")
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# =============================================================================
# PERFORMANCE METRICS ENDPOINTS
# =============================================================================

@app.route('/api/performance', methods=['GET'])
def get_performance():
    """Get trading performance metrics"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get overall stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_trades,
                COUNT(CASE WHEN status = 'closed' THEN 1 END) as closed_trades,
                COUNT(CASE WHEN status = 'closed' AND pnl > 0 THEN 1 END) as winning_trades,
                COUNT(CASE WHEN status = 'closed' AND pnl < 0 THEN 1 END) as losing_trades,
                COALESCE(SUM(CASE WHEN status = 'closed' THEN pnl ELSE 0 END), 0) as total_pnl,
                COALESCE(AVG(CASE WHEN status = 'closed' THEN pnl ELSE NULL END), 0) as avg_pnl,
                COALESCE(AVG(confidence), 0) as avg_confidence
            FROM trading_llm_trades
        """)

        stats = cursor.fetchone()

        # Calculate win rate
        win_rate = 0
        if stats['closed_trades'] > 0:
            win_rate = (stats['winning_trades'] / stats['closed_trades']) * 100

        # Get by asset class
        cursor.execute("""
            SELECT
                asset_class,
                COUNT(*) as trades,
                COALESCE(SUM(CASE WHEN status = 'closed' THEN pnl ELSE 0 END), 0) as pnl
            FROM trading_llm_trades
            GROUP BY asset_class
        """)

        by_asset_class = cursor.fetchall()

        return jsonify({
            'success': True,
            'overall': {
                'total_trades': stats['total_trades'],
                'closed_trades': stats['closed_trades'],
                'winning_trades': stats['winning_trades'],
                'losing_trades': stats['losing_trades'],
                'win_rate': round(win_rate, 2),
                'total_pnl': float(stats['total_pnl']),
                'avg_pnl': float(stats['avg_pnl']),
                'avg_confidence': float(stats['avg_confidence'])
            },
            'by_asset_class': by_asset_class
        })

    except Exception as e:
        logger.error(f"Failed to get performance: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


# =============================================================================
# STATIC FILE SERVING
# =============================================================================

@app.route('/trading-llm')
@app.route('/trading-llm/')
def serve_trading_llm_page():
    """Serve the Trading LLM dashboard"""
    return send_from_directory('.', 'trading_llm.html')


# =============================================================================
# INITIALIZATION
# =============================================================================

def init_database():
    """Initialize database tables for Trading LLM"""
    conn = get_db_connection()
    if not conn:
        logger.warning("Database not available - trades will not be persisted")
        return False

    try:
        cursor = conn.cursor()

        # Create trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trading_llm_trades (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                asset_class VARCHAR(20) NOT NULL,
                signal_type VARCHAR(20) NOT NULL,
                entry_price DECIMAL(20, 8),
                exit_price DECIMAL(20, 8),
                stop_loss DECIMAL(20, 8),
                take_profit DECIMAL(20, 8),
                position_size DECIMAL(10, 4),
                confidence INTEGER,
                reasoning TEXT,
                pnl DECIMAL(20, 8) DEFAULT 0,
                status VARCHAR(20) DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP,
                metadata JSONB
            )
        """)

        # Create signals history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trading_llm_signals (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(20) NOT NULL,
                asset_class VARCHAR(20) NOT NULL,
                signal_type VARCHAR(20) NOT NULL,
                confidence INTEGER,
                reasoning TEXT,
                supporting_factors JSONB,
                risk_factors JSONB,
                data_sources JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trading_llm_trades(symbol);
            CREATE INDEX IF NOT EXISTS idx_trades_status ON trading_llm_trades(status);
            CREATE INDEX IF NOT EXISTS idx_trades_created ON trading_llm_trades(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_signals_symbol ON trading_llm_signals(symbol);
            CREATE INDEX IF NOT EXISTS idx_signals_created ON trading_llm_signals(created_at DESC);
        """)

        conn.commit()
        logger.info("Database tables initialized successfully")
        return True

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def main():
    """Main entry point"""
    global engine

    print("=" * 60)
    print("TRADING LLM API - Starting...")
    print("=" * 60)

    # Initialize database
    print("\n1. Initializing database...")
    if init_database():
        print("   ✓ Database tables ready")
    else:
        print("   ⚠ Database not available (trades won't persist)")

    # Initialize engine
    print("\n2. Initializing Trading LLM Engine...")
    engine = TradingLLMEngine()
    print("   ✓ Engine initialized")

    # Test market context
    print("\n3. Building initial market context...")
    context = engine.build_market_context()
    if context:
        print(f"   ✓ Context built: Score={context.composite_score}, Status={context.risk_status}")
    else:
        print("   ⚠ Context not available (dependent APIs may be down)")

    print(f"\n4. Starting API server on port {API_PORT}...")
    print(f"   Dashboard: http://localhost:{API_PORT}/trading-llm")
    print(f"   API Docs:  http://localhost:{API_PORT}/api/health")
    print("\n" + "=" * 60)

    # Run Flask
    app.run(host='0.0.0.0', port=API_PORT, debug=False, threaded=True)


if __name__ == '__main__':
    main()
