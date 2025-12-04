#!/usr/bin/env python3
"""
Simple Server for Spartan Research Station
Alternative to start_server.py - runs on port 9000
Uses JSON database mode (no PostgreSQL required)
"""

import http.server
import socketserver
import json
import os
from urllib.parse import urlparse, parse_qs
from pathlib import Path

PORT = 9000
DIRECTORY = Path(__file__).parent

class SpartanHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler with API proxies"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

    def end_headers(self):
        """Add CORS headers to all responses"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_GET(self):
        """Handle GET requests with API routing"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        # Database API endpoints
        if path == '/api/db/stats':
            self.handle_db_stats()
        elif path == '/api/db/search':
            self.handle_db_search(parsed_path.query)
        elif path == '/api/db/symbols':
            self.handle_db_symbols(parsed_path.query)
        # Default to static file serving
        else:
            super().do_GET()

    def handle_db_stats(self):
        """Return database statistics"""
        try:
            db_path = DIRECTORY / 'symbols_database.json'
            if db_path.exists():
                with open(db_path, 'r') as f:
                    data = json.load(f)
                    stats = {
                        'total_symbols': data.get('metadata', {}).get('total_symbols', 0),
                        'version': data.get('metadata', {}).get('version', 'Unknown'),
                        'exchanges': len(data.get('metadata', {}).get('exchanges_covered', [])),
                        'countries': len(data.get('metadata', {}).get('countries_covered', []))
                    }
                    self.send_json_response(stats)
            else:
                self.send_json_response({'error': 'Database not found'}, status=404)
        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)

    def handle_db_search(self, query_string):
        """Search symbols database"""
        try:
            params = parse_qs(query_string)
            query = params.get('query', [''])[0].upper()
            limit = int(params.get('limit', ['100'])[0])

            db_path = DIRECTORY / 'symbols_database.json'
            if not db_path.exists():
                self.send_json_response({'error': 'Database not found'}, status=404)
                return

            with open(db_path, 'r') as f:
                data = json.load(f)

            # Search across all asset types
            results = []
            for asset_type in ['stocks', 'futures', 'forex', 'crypto', 'etfs', 'indices']:
                if asset_type in data:
                    for item in data[asset_type]:
                        symbol = item.get('symbol', '')
                        name = item.get('name', '')
                        if query in symbol.upper() or query in name.upper():
                            results.append(item)
                            if len(results) >= limit:
                                break
                if len(results) >= limit:
                    break

            self.send_json_response({'results': results, 'count': len(results)})
        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)

    def handle_db_symbols(self, query_string):
        """Get all symbols with pagination"""
        try:
            params = parse_qs(query_string)
            limit = int(params.get('limit', ['1000'])[0])
            offset = int(params.get('offset', ['0'])[0])

            db_path = DIRECTORY / 'symbols_database.json'
            if not db_path.exists():
                self.send_json_response({'error': 'Database not found'}, status=404)
                return

            with open(db_path, 'r') as f:
                data = json.load(f)

            # Combine all symbols
            all_symbols = []
            for asset_type in ['stocks', 'futures', 'forex', 'crypto', 'etfs', 'indices']:
                if asset_type in data:
                    all_symbols.extend(data[asset_type])

            # Apply pagination
            paginated = all_symbols[offset:offset+limit]

            self.send_json_response({
                'symbols': paginated,
                'total': len(all_symbols),
                'offset': offset,
                'limit': limit
            })
        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)

    def send_json_response(self, data, status=200):
        """Send JSON response"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        """Custom log format"""
        print(f"[Spartan Server] {self.address_string()} - {format % args}")


def main():
    """Start the simple HTTP server"""

    print("=" * 60)
    print(" SPARTAN RESEARCH STATION - SIMPLE SERVER")
    print("=" * 60)
    print()
    print(f"Starting server on port {PORT}...")
    print(f"Serving from: {DIRECTORY}")
    print()

    # Check if symbols database exists
    db_path = DIRECTORY / 'symbols_database.json'
    if db_path.exists():
        print("✓ Symbol database found")
        try:
            with open(db_path, 'r') as f:
                data = json.load(f)
                total = data.get('metadata', {}).get('total_symbols', 0)
                print(f"✓ Database contains {total:,} symbols")
        except:
            print("⚠ Warning: Could not read database file")
    else:
        print("⚠ Warning: Symbol database not found")
        print("  Some features may not work correctly")

    print()
    print("Server URLs:")
    print(f"  Main website:     http://localhost:{PORT}/index.html")
    print(f"  Capital Flow:     http://localhost:{PORT}/global_capital_flow_swing_trading.html")
    print(f"  Database API:     http://localhost:{PORT}/api/db/stats")
    print()
    print("=" * 60)
    print("Server is running. Press Ctrl+C to stop.")
    print("=" * 60)
    print()

    # Start server
    with socketserver.TCPServer(("", PORT), SpartanHTTPRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nServer stopped by user")
            print("=" * 60)


if __name__ == "__main__":
    main()
