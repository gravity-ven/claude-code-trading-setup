#!/usr/bin/env python3
"""
Redis-Integrated Data Server for Spartan Research Station
Serves data from Data Guardian Agent's Redis cache
"""

import http.server
import socketserver
import json
import redis
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

PORT = 8889  # Different port to avoid conflict
DIRECTORY = Path(__file__).parent

# Redis connection
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# PostgreSQL connection
def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv('POSTGRES_DB', 'spartan_research_db'),
        user=os.getenv('POSTGRES_USER', 'spartan'),
        password=os.getenv('POSTGRES_PASSWORD', 'spartan'),
        host='localhost',
        port=5432
    )

class RedisDataHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that serves data from Redis cache"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

    def end_headers(self):
        """Add CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json_response(self, data, status=200):
        """Send JSON response"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # Health check
        if path == '/health':
            self.handle_health()
        # Get all cached symbols
        elif path == '/api/market/symbols':
            self.handle_cached_symbols()
        # Get specific symbol data
        elif path.startswith('/api/market/symbol/'):
            symbol = path.split('/')[-1].upper()
            self.handle_symbol_data(symbol)
        # Get all market data
        elif path == '/api/market/data':
            self.handle_all_market_data()
        # Get indices data
        elif path == '/api/market/indices':
            self.handle_indices_data()
        # Get crypto data
        elif path == '/api/market/crypto':
            self.handle_crypto_data()
        # Get economic data
        elif path == '/api/economic/indicators':
            self.handle_economic_data()
        # Cache stats
        elif path == '/api/cache/stats':
            self.handle_cache_stats()
        # Default to static files
        else:
            super().do_GET()

    def handle_health(self):
        """Health check endpoint"""
        try:
            redis_ping = redis_client.ping()
            db_conn = get_db_connection()
            db_conn.close()

            self.send_json_response({
                'status': 'ok',
                'server': 'Redis Data Server',
                'port': PORT,
                'redis': 'connected' if redis_ping else 'disconnected',
                'database': 'connected'
            })
        except Exception as e:
            self.send_json_response({
                'status': 'error',
                'error': str(e)
            }, status=500)

    def handle_cached_symbols(self):
        """Get all symbols currently in Redis cache"""
        try:
            keys = redis_client.keys('market:symbol:*')
            symbols = [key.replace('market:symbol:', '') for key in keys]

            self.send_json_response({
                'symbols': sorted(symbols),
                'count': len(symbols),
                'source': 'redis_cache'
            })
        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)

    def handle_symbol_data(self, symbol):
        """Get data for specific symbol from Redis or PostgreSQL"""
        try:
            # Try Redis first
            redis_key = f'market:symbol:{symbol}'
            cached_data = redis_client.get(redis_key)

            if cached_data:
                data = json.loads(cached_data)
                data['cache_hit'] = 'redis'
                data['timestamp_age'] = self.calculate_age(data.get('timestamp'))
                self.send_json_response(data)
                return

            # Fallback to PostgreSQL
            db_conn = get_db_connection()
            with db_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT symbol, price, change_percent, volume,
                           metadata, timestamp, source
                    FROM preloaded_market_data
                    WHERE symbol = %s
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (symbol,))

                row = cur.fetchone()
                if row:
                    data = dict(row)
                    # Convert timestamp to string
                    if isinstance(data['timestamp'], datetime):
                        data['timestamp'] = data['timestamp'].isoformat()
                    data['cache_hit'] = 'postgresql'
                    data['timestamp_age'] = self.calculate_age(data.get('timestamp'))
                    self.send_json_response(data)
                else:
                    self.send_json_response({
                        'error': f'No data found for {symbol}',
                        'symbol': symbol
                    }, status=404)

            db_conn.close()

        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)

    def handle_all_market_data(self):
        """Get all market data from Redis"""
        try:
            keys = redis_client.keys('market:symbol:*')
            data = {}

            for key in keys:
                symbol = key.replace('market:symbol:', '')
                cached_data = redis_client.get(key)
                if cached_data:
                    data[symbol] = json.loads(cached_data)

            self.send_json_response({
                'data': data,
                'count': len(data),
                'source': 'redis_cache',
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)

    def handle_indices_data(self):
        """Get major indices data"""
        try:
            indices = ['SPY', 'QQQ', 'DIA', 'IWM', 'VTI']
            data = {}

            for symbol in indices:
                redis_key = f'market:symbol:{symbol}'
                cached_data = redis_client.get(redis_key)
                if cached_data:
                    data[symbol] = json.loads(cached_data)

            self.send_json_response({
                'indices': data,
                'count': len(data),
                'source': 'redis_cache'
            })
        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)

    def handle_crypto_data(self):
        """Get crypto data"""
        try:
            cryptos = ['BTC-USD', 'ETH-USD', 'BNB-USD']
            data = {}

            for symbol in cryptos:
                redis_key = f'market:symbol:{symbol}'
                cached_data = redis_client.get(redis_key)
                if cached_data:
                    data[symbol] = json.loads(cached_data)

            self.send_json_response({
                'crypto': data,
                'count': len(data),
                'source': 'redis_cache'
            })
        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)

    def handle_economic_data(self):
        """Get economic indicators from PostgreSQL"""
        try:
            db_conn = get_db_connection()
            with db_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT symbol, price as value, timestamp, source
                    FROM preloaded_market_data
                    WHERE data_type = 'economic'
                    ORDER BY timestamp DESC
                    LIMIT 50
                """)

                rows = cur.fetchall()
                data = {}
                for row in rows:
                    row_dict = dict(row)
                    if isinstance(row_dict['timestamp'], datetime):
                        row_dict['timestamp'] = row_dict['timestamp'].isoformat()
                    data[row_dict['symbol']] = row_dict

                self.send_json_response({
                    'indicators': data,
                    'count': len(data),
                    'source': 'postgresql'
                })

            db_conn.close()
        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)

    def handle_cache_stats(self):
        """Get cache statistics"""
        try:
            keys = redis_client.keys('market:*')

            # Categorize keys
            symbols = [k for k in keys if k.startswith('market:symbol:')]

            # Check data freshness
            fresh_count = 0
            stale_count = 0

            for key in symbols:
                ttl = redis_client.ttl(key)
                if ttl > 600:  # More than 10 minutes remaining
                    fresh_count += 1
                else:
                    stale_count += 1

            self.send_json_response({
                'total_keys': len(keys),
                'symbol_keys': len(symbols),
                'fresh_data': fresh_count,
                'stale_data': stale_count,
                'cache_ttl': '15 minutes',
                'data_guardian': 'active'
            })
        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)

    def calculate_age(self, timestamp_str):
        """Calculate how old the data is"""
        if not timestamp_str:
            return 'unknown'

        try:
            # Handle both ISO format and datetime objects
            if isinstance(timestamp_str, str):
                ts = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                ts = timestamp_str

            # Remove timezone for calculation
            if ts.tzinfo:
                ts = ts.replace(tzinfo=None)

            age = datetime.now() - ts

            if age.total_seconds() < 60:
                return f"{int(age.total_seconds())} seconds"
            elif age.total_seconds() < 3600:
                return f"{int(age.total_seconds() / 60)} minutes"
            elif age.total_seconds() < 86400:
                return f"{int(age.total_seconds() / 3600)} hours"
            else:
                return f"{int(age.total_seconds() / 86400)} days"
        except Exception:
            return 'unknown'

def main():
    """Start the Redis Data Server"""
    print(f"=" * 70)
    print(f"🛡️  REDIS DATA SERVER - Spartan Research Station")
    print(f"=" * 70)
    print(f"Port: {PORT}")
    print(f"Redis: localhost:6379")
    print(f"PostgreSQL: localhost:5432")
    print(f"")
    print(f"Endpoints:")
    print(f"  GET  /health                    - Health check")
    print(f"  GET  /api/market/symbols        - All cached symbols")
    print(f"  GET  /api/market/symbol/{{SYM}}  - Specific symbol data")
    print(f"  GET  /api/market/data           - All market data")
    print(f"  GET  /api/market/indices        - Major indices")
    print(f"  GET  /api/market/crypto         - Crypto data")
    print(f"  GET  /api/economic/indicators   - Economic data")
    print(f"  GET  /api/cache/stats           - Cache statistics")
    print(f"=" * 70)
    print(f"")
    print(f"✅ Server starting on http://localhost:{PORT}")
    print(f"")

    with socketserver.TCPServer(("", PORT), RedisDataHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n🛑 Server stopped by user")
            httpd.shutdown()

if __name__ == '__main__':
    main()
