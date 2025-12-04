"""
Data Validation API Endpoints
Provides real-time data validation status and Claude Code bridge status
"""

from flask import Blueprint, jsonify, request
import json
import os
from pathlib import Path
from datetime import datetime
import redis
import psycopg2
from psycopg2.extras import RealDictCursor

data_validation_bp = Blueprint('data_validation', __name__)

# Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://spartan:spartan@localhost:5432/spartan_research_db')

LOGS_DIR = Path(__file__).parent.parent.parent / 'logs'
VALIDATION_FILE = LOGS_DIR / 'data_validation_latest.json'
TRIGGER_FLAG = LOGS_DIR / 'claude_trigger_data_failure.flag'


@data_validation_bp.route('/health/data', methods=['GET'])
def data_health():
    """
    Get current data validation status
    Returns the latest validation results
    """
    try:
        if VALIDATION_FILE.exists():
            with open(VALIDATION_FILE, 'r') as f:
                validation_data = json.load(f)

            # Add file age
            file_age = datetime.now() - datetime.fromisoformat(validation_data['timestamp'])
            validation_data['age_seconds'] = file_age.total_seconds()

            return jsonify({
                'status': 'success',
                'validation': validation_data
            }), 200
        else:
            return jsonify({
                'status': 'warning',
                'message': 'No validation data available yet',
                'validation': None
            }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@data_validation_bp.route('/health/data/summary', methods=['GET'])
def data_health_summary():
    """
    Get a quick summary of data health
    """
    try:
        if VALIDATION_FILE.exists():
            with open(VALIDATION_FILE, 'r') as f:
                validation_data = json.load(f)

            redis_pct = validation_data['redis']['valid_percentage']
            postgres_pct = validation_data['postgres']['valid_percentage']
            critical_failures = len(validation_data['critical_failures'])
            overall_health = validation_data['overall_health']

            return jsonify({
                'status': 'success',
                'summary': {
                    'overall_health': overall_health,
                    'redis_valid_pct': redis_pct,
                    'postgres_valid_pct': postgres_pct,
                    'critical_failures': critical_failures,
                    'timestamp': validation_data['timestamp']
                }
            }), 200
        else:
            return jsonify({
                'status': 'unknown',
                'summary': {
                    'overall_health': 'unknown',
                    'message': 'Validation data not available'
                }
            }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@data_validation_bp.route('/health/data/redis', methods=['GET'])
def redis_health():
    """
    Check Redis connection and data availability
    """
    try:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )

        # Ping Redis
        redis_client.ping()

        # Count keys
        market_keys = len(redis_client.keys('market:*'))
        fred_keys = len(redis_client.keys('fred:*'))
        total_keys = market_keys + fred_keys

        return jsonify({
            'status': 'success',
            'redis': {
                'connected': True,
                'market_keys': market_keys,
                'fred_keys': fred_keys,
                'total_keys': total_keys
            }
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'redis': {
                'connected': False,
                'error': str(e)
            }
        }), 500


@data_validation_bp.route('/health/data/postgres', methods=['GET'])
def postgres_health():
    """
    Check PostgreSQL connection and data freshness
    """
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Count fresh data (< 1 hour old)
        cursor.execute("""
            SELECT
                COUNT(DISTINCT data_source) as source_count,
                COUNT(*) as total_records,
                MAX(timestamp) as latest_update
            FROM preloaded_market_data
            WHERE timestamp > NOW() - INTERVAL '1 hour'
        """)

        result = cursor.fetchone()
        cursor.close()
        conn.close()

        return jsonify({
            'status': 'success',
            'postgres': {
                'connected': True,
                'source_count': result['source_count'],
                'total_records': result['total_records'],
                'latest_update': str(result['latest_update']) if result['latest_update'] else None
            }
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'postgres': {
                'connected': False,
                'error': str(e)
            }
        }), 500


@data_validation_bp.route('/health/data/claude-bridge', methods=['GET'])
def claude_bridge_status():
    """
    Check Claude Code bridge status
    """
    try:
        # Check if trigger flag exists
        trigger_active = TRIGGER_FLAG.exists()

        # Check validation file age
        validation_age = None
        if VALIDATION_FILE.exists():
            file_stat = VALIDATION_FILE.stat()
            validation_age = (datetime.now() - datetime.fromtimestamp(file_stat.st_mtime)).total_seconds()

        # Check watcher script PID
        watcher_pid_file = LOGS_DIR / 'claude_data_watcher.pid'
        watcher_running = False
        if watcher_pid_file.exists():
            try:
                with open(watcher_pid_file, 'r') as f:
                    pid = int(f.read().strip())
                # Check if process is running
                import psutil
                watcher_running = psutil.pid_exists(pid)
            except:
                watcher_running = False

        return jsonify({
            'status': 'success',
            'claude_bridge': {
                'trigger_active': trigger_active,
                'watcher_running': watcher_running,
                'validation_age_seconds': validation_age,
                'logs_dir': str(LOGS_DIR)
            }
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@data_validation_bp.route('/health/data/trigger-claude', methods=['POST'])
def trigger_claude_manual():
    """
    Manually trigger Claude Code intervention
    (For testing or emergency use)
    """
    try:
        # Create trigger flag
        with open(TRIGGER_FLAG, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'triggered_by': 'manual_api_call',
                'note': 'Manual trigger via API'
            }, f, indent=2)

        return jsonify({
            'status': 'success',
            'message': 'Claude Code trigger activated',
            'trigger_file': str(TRIGGER_FLAG),
            'next_steps': [
                'Check logs/claude_data_fix_prompt.txt for the prompt',
                'Run ./logs/trigger_claude_data_fix.sh to launch Claude Code',
                'Or wait for automatic watcher to launch Claude Code'
            ]
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@data_validation_bp.route('/health/data/incidents', methods=['GET'])
def data_incidents():
    """
    Get recent data validation incidents from database
    """
    try:
        limit = request.args.get('limit', 10, type=int)

        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT
                incident_id,
                container_name,
                incident_type,
                severity,
                description,
                auto_healed,
                timestamp
            FROM monitor_incidents
            WHERE incident_type = 'data_validation_failure'
            ORDER BY timestamp DESC
            LIMIT %s
        """, (limit,))

        incidents = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        # Convert timestamps to strings
        for incident in incidents:
            incident['timestamp'] = str(incident['timestamp'])

        return jsonify({
            'status': 'success',
            'incidents': incidents,
            'count': len(incidents)
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'incidents': []
        }), 500


# Register blueprint in main app
def register_data_validation_routes(app):
    """Register data validation routes with Flask app"""
    app.register_blueprint(data_validation_bp, url_prefix='/api')
