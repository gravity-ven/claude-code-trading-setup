#!/usr/bin/env python3
"""
AGENT DATA ROUTER
================

Routes data requests to the running agent system.
Acts as a bridge between the main server (port 8888) and agent system (port 8890).
"""

import http.server
import socketserver
import json
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
import os
import sys
import traceback

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

PORT = 8891
AGENT_API_BASE = "http://localhost:8890"
AGENT_TIMEOUT = 5  # seconds

class AgentDataRouter(http.server.SimpleHTTPRequestHandler):
    """Router that forwards requests to the agent system"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)

    def end_headers(self):
        """Add CORS headers to all responses"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        """Route GET requests to agent system"""
        parsed_path = self.path
        
        # Route agent-specific endpoints
        if parsed_path.startswith('/api/data/point/'):
            symbol = parsed_path.split('/')[-1]
            self.route_to_agent(f'/api/data/point/{symbol}')
        elif parsed_path == '/api/data/market-summary':
            self.route_to_agent('/api/data/market-summary')
        elif parsed_path == '/api/data/points':
            self.route_to_agent('/api/data/points')
        elif parsed_path.startswith('/api/agents/'):
            self.route_to_agent(parsed_path)  # Direct pass-through
        else:
            # For non-agent endpoints, return 404
            self.send_response(404)
            self.end_headers()

    def route_to_agent(self, agent_path):
        """Forward request to agent system"""
        try:
            full_url = f"{AGENT_API_BASE}{agent_path}"
            
            # Make request to agent system
            request = urllib.request.Request(full_url)
            request.add_header('User-Agent', 'Spartan-Agent-Router/1.0')
            
            with urllib.request.urlopen(request, timeout=AGENT_TIMEOUT) as response:
                if response.status == 200:
                    data = response.read().decode('utf-8')
                    
                    # Return agent response
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(data.encode())
                else:
                    self.send_response(response.status)
                    self.end_headers()
                    self.wfile.write(response.read())
                    
        except urllib.error.URLError as e:
            if e.reason.errno == 111:  # Connection refused
                # Agent system not running
                self.send_response(503)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                
                error_response = {
                    'error': 'Agent system not available',
                    'message': 'Data point agents are not running',
                    'solution': 'Start the agent system with ./START_DATA_POINT_AGENTS.sh',
                    'timestamp': datetime.now().isoformat()
                }
                self.wfile.write(json.dumps(error_response).encode())
            else:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
                
        except Exception as e:
            print(f"Agent router error: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def log_message(self, format, *args):
        """Override to suppress default logging"""
        pass  # Suppress logging for cleaner output


def main():
    """Start the agent data router"""
    print("=" * 60)
    print("🔄 AGENT DATA ROUTER")
    print("=" * 60)
    print(f"Starting agent data router on port {PORT}")
    print(f"Forwarding to agent system: {AGENT_API_BASE}")
    print()
    print("Available routes:")
    print("  /api/data/point/{symbol} - Get data from specific agent")
    print("  /api/data/market-summary - Market overview")
    print("  /api/data/points - All agent data")
    print("  /api/agents/* - Agent system endpoints")
    print("=" * 60)
    
    try:
        with socketserver.TCPServer(("", PORT), AgentDataRouter) as httpd:
            print(f"✅ Agent Data Router running on http://localhost:{PORT}")
            print("🔄 Forwarding data requests to agent system...")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Agent Data Router stopped")
    except Exception as e:
        print(f"❌ Failed to start router: {e}")


if __name__ == '__main__':
    main()
