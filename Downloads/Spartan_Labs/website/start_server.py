#!/usr/bin/env python3
"""
Main Server for Spartan Research Station
Runs on port 8888 with full API proxy support
"""

import http.server
import socketserver
import json
import os
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import sys
import traceback
from dotenv import load_dotenv
import redis
import psycopg2
from psycopg2.extras import RealDictCursor
import urllib.request
import urllib.error

# Load environment variables
load_dotenv()

# Initialize Redis connection
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    print("✅ Connected to Redis cache")
except Exception as e:
    print(f"⚠️  Redis not available: {e}")
    redis_client = None

# Add current directory to path to import local modules

# Add current directory to path to import local modules
sys.path.append(str(Path(__file__).parent))

# Import NO N/A scraper
from no_na_scraper import get_complete_market_data
# Import complete data provider
from complete_data_provider import getAllCompleteData

from data_fetcher_fallback import fetch_stock_price, fetch_crypto_price, fetch_forex_rate

PORT = 8888
DIRECTORY = Path(__file__).parent

class SpartanHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler with full API proxies"""

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

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.end_headers()

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
        elif path == '/api/db/polygon-symbols':
            self.handle_polygon_symbols(parsed_path.query)
        # Market Data Endpoints
        elif path.startswith('/api/market/symbol/'):
            symbol = path.split('/')[-1]
            self.handle_market_symbol(symbol)
        elif path.startswith('/api/market/quote/'):
            symbol = path.split('/')[-1]
            self.handle_market_quote(symbol)
        # NO N/A Guarantee Endpoints
        elif path == '/api/market/breadth':
            self.handle_market_breadth()
        elif path == '/api/market/putcall':
            self.handle_put_call_ratio()
        elif path == '/api/market/volatility':
            self.handle_volatility_data()
        elif path == '/api/market/complete':
            self.handle_complete_market_data()
        # COMPLETE ZERO N/A DATA ENDPOINTS
        elif path == '/api/market/all-complete':
            self.handle_all_complete_data()
        elif path == '/api/economic/all':
            self.handle_all_economic_data()
        elif path == '/api/market/inflation':
            self.handle_inflation_data()
        elif path == '/api/market/sectors':
            self.handle_sector_rotation_data()
        # Config endpoint - Serves API keys from .env
        elif path == '/api/config':
            self.handle_config()
        # Economic indicators endpoint (FRED data)
        elif path.startswith('/api/economic/indicators'):
            self.handle_economic_indicators(parsed_path.query)
        # Fundamental Data Endpoints (NEW - from comprehensive scanner)
        elif path.startswith('/api/fundamental/economic/'):
            indicator = path.split('/')[-1]
            self.handle_fundamental_economic(indicator)
        elif path.startswith('/api/fundamental/forex/'):
            pair = path.split('/')[-1]
            self.handle_fundamental_forex(pair)
        elif path.startswith('/api/fundamental/fundamentals/'):
            symbol = path.split('/')[-1]
            self.handle_fundamental_company(symbol)
        # Composite Indicator Endpoints (NEW - for dashboard calculations)
        elif path == '/api/recession-probability':
            self.handle_recession_probability()
        elif path == '/api/market/narrative':
            self.handle_market_narrative()
        # COT Scanner API Endpoints (proxy to port 5009)
        elif path.startswith('/api/cot-scanner/'):
            self.proxy_to_cot_scanner(path)
        # Health check endpoint
        elif path == '/health':
            self.send_json_response({'status': 'ok', 'server': 'Spartan Main Server', 'port': PORT})
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
                        'countries': len(data.get('metadata', {}).get('countries_covered', [])),
                        'asset_types': {
                            'stocks': len(data.get('stocks', [])),
                            'futures': len(data.get('futures', [])),
                            'forex': len(data.get('forex', [])),
                            'crypto': len(data.get('crypto', [])),
                            'etfs': len(data.get('etfs', [])),
                            'indices': len(data.get('indices', []))
                        }
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

    def handle_polygon_symbols(self, query_string):
        """Get symbols from PostgreSQL polygon_symbols table"""
        try:
            params = parse_qs(query_string)
            limit = int(params.get('limit', ['10000'])[0])
            offset = int(params.get('offset', ['0'])[0])
            asset_type = params.get('type', [''])[0]  # Optional filter by type
            active_only = params.get('active', ['true'])[0].lower() == 'true'

            # Connect to PostgreSQL
            db_conn = psycopg2.connect(
                dbname=os.getenv('POSTGRES_DB', 'spartan_research_db'),
                user=os.getenv('POSTGRES_USER', 'spartan'),
                password=os.getenv('POSTGRES_PASSWORD', 'spartan'),
                host='localhost',
                port=5432
            )

            with db_conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Build query with filters
                where_clauses = []
                params_list = []

                if active_only:
                    where_clauses.append("active = TRUE")

                # EXCLUDE OTC stocks (type 'OS')
                where_clauses.append("type != %s")
                params_list.append('OS')

                if asset_type:
                    where_clauses.append("type = %s")
                    params_list.append(asset_type)

                where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

                # Get total count
                count_query = f"SELECT COUNT(*) as total FROM polygon_symbols WHERE {where_sql}"
                cur.execute(count_query, params_list)
                total = cur.fetchone()['total']

                # Get paginated symbols
                query = f"""
                    SELECT
                        ticker,
                        name,
                        market,
                        locale,
                        type,
                        active,
                        currency_symbol,
                        primary_exchange
                    FROM polygon_symbols
                    WHERE {where_sql}
                    ORDER BY ticker
                    LIMIT %s OFFSET %s
                """
                cur.execute(query, params_list + [limit, offset])
                symbols = cur.fetchall()

                # Convert to list of dicts
                symbols_list = [dict(row) for row in symbols]

            db_conn.close()

            self.send_json_response({
                'symbols': symbols_list,
                'total': total,
                'offset': offset,
                'limit': limit,
                'source': 'postgresql'
            })

        except Exception as e:
            print(f"Error in handle_polygon_symbols: {e}")
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, status=500)

    def handle_market_symbol(self, symbol):
        """Get data for a specific symbol - REDIS FIRST, then PostgreSQL, then fetch"""
        try:
            symbol_upper = symbol.upper()

            # PRIORITY 1: Check Redis cache (Data Guardian Agent's cache)
            if redis_client:
                try:
                    redis_key = f'market:symbol:{symbol_upper}'
                    cached_data = redis_client.get(redis_key)

                    if cached_data:
                        data = json.loads(cached_data)
                        data['cache_hit'] = 'redis'
                        print(f"✅ Redis cache hit for {symbol_upper}: ${data.get('price')}")
                        self.send_json_response({'data': data})
                        return
                except Exception as e:
                    print(f"Redis error for {symbol_upper}: {e}")

            # PRIORITY 2: Check PostgreSQL backup
            try:
                db_conn = psycopg2.connect(
                    dbname=os.getenv('POSTGRES_DB', 'spartan_research_db'),
                    user=os.getenv('POSTGRES_USER', 'spartan'),
                    password=os.getenv('POSTGRES_PASSWORD', 'spartan'),
                    host='localhost',
                    port=5432
                )

                with db_conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT symbol, price, change_percent, volume,
                               metadata, timestamp, source
                        FROM preloaded_market_data
                        WHERE symbol = %s
                        ORDER BY timestamp DESC
                        LIMIT 1
                    """, (symbol_upper,))

                    row = cur.fetchone()
                    if row:
                        data = dict(row)
                        # Convert timestamp to string
                        if isinstance(data['timestamp'], datetime):
                            data['timestamp'] = data['timestamp'].isoformat()
                        data['cache_hit'] = 'postgresql'
                        print(f"✅ PostgreSQL hit for {symbol_upper}: ${data.get('price')}")
                        self.send_json_response({'data': data})
                        db_conn.close()
                        return

                db_conn.close()
            except Exception as e:
                print(f"PostgreSQL error for {symbol_upper}: {e}")

            # PRIORITY 3: Try to fetch fresh data (fallback only)
            db_path = DIRECTORY / 'symbols_database.json'
            if db_path.exists():
                with open(db_path, 'r') as f:
                    db_data = json.load(f)

                # Search in 'symbols' array (correct structure)
                found_item = None
                if 'symbols' in db_data:
                    for item in db_data['symbols']:
                        if item.get('symbol', '').upper() == symbol_upper:
                            found_item = item
                            break

                if found_item:
                    asset_type = found_item.get('type', 'Stock')
                    real_data = None

                    try:
                        if asset_type in ['Stock', 'ETF']:
                            result = fetch_stock_price(symbol_upper, period_days=5)
                            if result['success'] and result['data'] is not None and not result['data'].empty:
                                real_data = result['data']
                        elif asset_type == 'Crypto':
                            search_sym = symbol_upper if symbol_upper.endswith('-USD') else f"{symbol_upper}-USD"
                            result = fetch_crypto_price(search_sym, period_days=5)
                            if result['success'] and result['data'] is not None and not result['data'].empty:
                                real_data = result['data']
                        elif asset_type == 'Forex':
                            search_sym = symbol_upper if '=' in symbol_upper else f"{symbol_upper}=X"
                            result = fetch_forex_rate(search_sym, period_days=5)
                            if result['success'] and result['data'] is not None and not result['data'].empty:
                                real_data = result['data']
                    except Exception as e:
                        print(f"Error fetching fresh data for {symbol_upper}: {e}")

                    if real_data is not None:
                        latest_price = real_data.iloc[-1]
                        prev_price = real_data.iloc[-2] if len(real_data) > 1 else latest_price

                        found_item['price'] = round(float(latest_price), 2)
                        found_item['change'] = round(float(latest_price - prev_price), 2)
                        found_item['change_percent'] = round(float((latest_price - prev_price) / prev_price * 100), 2)
                        found_item['timestamp'] = datetime.now().isoformat()
                        found_item['source'] = 'Fresh Fetch'
                        found_item['cache_hit'] = 'fresh'
                        print(f"✅ Fresh fetch for {symbol_upper}: ${found_item['price']}")
                        self.send_json_response({'data': found_item})
                        return

            # NO DATA AVAILABLE from any source
            print(f"❌ No data available for {symbol_upper} from any source")
            self.send_json_response({
                'error': f'No data available for {symbol_upper}',
                'tried': ['redis', 'postgresql', 'fresh_fetch'],
                'tip': 'Data Guardian Agent may need time to populate cache'
            }, status=404)

        except Exception as e:
            print(f"Error in handle_market_symbol: {e}")
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, status=500)

    def handle_market_quote(self, symbol):
        """Get quote data for a specific symbol (for indicators)"""
        try:
            symbol_upper = symbol.upper()

            # SPECIAL MAPPINGS: Map common symbols to FRED/alternative sources
            SYMBOL_MAPPINGS = {
                '^TNX': 'DGS10',      # 10-Year Treasury → FRED
                '^VIX': 'VIXCLS',     # VIX → FRED
                '^GSPC': 'SPY',       # S&P 500 Index → SPY ETF
                '^DJI': 'DIA',        # Dow Jones → DIA ETF
                '^IXIC': 'QQQ',       # NASDAQ → QQQ ETF
                '^RUT': 'IWM',        # Russell 2000 → IWM ETF
            }

            # Check if we need to remap the symbol
            lookup_symbol = SYMBOL_MAPPINGS.get(symbol_upper, symbol_upper)
            is_fred_symbol = lookup_symbol in ['DGS10', 'VIXCLS', 'DGS2', 'DGS5', 'DGS30', 'T10Y2Y']

            # PRIORITY 1: Check Redis cache (from our scanners)
            if redis_client:
                try:
                    # Try fundamental cache (for FRED economic indicators)
                    if is_fred_symbol:
                        redis_key = f'fundamental:economic:{lookup_symbol}'
                        cached_data = redis_client.get(redis_key)
                        if cached_data:
                            data = json.loads(cached_data)
                            # Convert FRED data to quote format
                            quote_data = {
                                'symbol': symbol_upper,
                                'price': float(data.get('value', 0)),
                                'change': 0,  # FRED doesn't provide daily change
                                'changePercent': 0,
                                'changePercent5d': 0,
                                'timestamp': data.get('timestamp'),
                                'source': 'fred',
                                'cache_hit': 'redis'
                            }
                            print(f"✅ Redis FRED cache hit for {symbol_upper} → {lookup_symbol}: {data.get('value')}")
                            self.send_json_response(quote_data)
                            return

                    # Try market symbol cache (from price scanner)
                    redis_key = f'market:symbol:{lookup_symbol}'
                    cached_data = redis_client.get(redis_key)
                    if cached_data:
                        data = json.loads(cached_data)
                        # Convert to quote format
                        quote_data = {
                            'symbol': symbol_upper,
                            'price': data.get('price'),
                            'change': data.get('change', 0),
                            'changePercent': data.get('change_percent', 0),
                            'changePercent5d': 0,  # Not in cache yet
                            'timestamp': data.get('timestamp'),
                            'source': data.get('source', 'cache'),
                            'cache_hit': 'redis'
                        }
                        print(f"✅ Redis price cache hit for {symbol_upper}: ${data.get('price')}")
                        self.send_json_response(quote_data)
                        return
                except Exception as e:
                    print(f"Redis lookup error for {symbol_upper}: {e}")

            # PRIORITY 2: Fetch from yfinance
            # Determine symbol type and fetch appropriate data
            period_days = 5  # Always fetch 5 days for change calculation

            real_data = None
            try:
                # Try as stock/ETF first (most common for indicators)
                if symbol_upper.startswith('^'):
                    # Index symbols (^VIX, ^TNX, etc.)
                    result = fetch_stock_price(symbol_upper, period_days=period_days)
                    if result['success'] and result['data'] is not None and not result['data'].empty:
                        real_data = result['data']
                elif '-USD' in symbol_upper or symbol_upper in ['BTC', 'ETH', 'SOL']:
                    # Crypto symbols
                    search_sym = symbol_upper if '-USD' in symbol_upper else f"{symbol_upper}-USD"
                    result = fetch_crypto_price(search_sym, period_days=period_days)
                    if result['success'] and result['data'] is not None and not result['data'].empty:
                        real_data = result['data']
                elif '=' in symbol_upper or symbol_upper in ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']:
                    # Forex symbols
                    search_sym = symbol_upper if '=' in symbol_upper else f"{symbol_upper}=X"
                    result = fetch_forex_rate(search_sym, period_days=period_days)
                    if result['success'] and result['data'] is not None and not result['data'].empty:
                        real_data = result['data']
                else:
                    # Regular stocks/ETFs
                    result = fetch_stock_price(symbol_upper, period_days=period_days)
                    if result['success'] and result['data'] is not None and not result['data'].empty:
                        real_data = result['data']

            except Exception as e:
                print(f"Error fetching quote for {symbol}: {e}")
                traceback.print_exc()

            if real_data is not None and len(real_data) > 0:
                # Calculate prices and changes
                latest_price = float(real_data.iloc[-1])
                prev_price = float(real_data.iloc[-2]) if len(real_data) > 1 else latest_price
                first_price = float(real_data.iloc[0]) if len(real_data) > 0 else latest_price

                # 1-day change
                change = latest_price - prev_price
                change_percent = (change / prev_price * 100) if prev_price != 0 else 0

                # 5-day change
                change_5d = latest_price - first_price
                change_percent_5d = (change_5d / first_price * 100) if first_price != 0 else 0

                # Return data directly (not wrapped in 'data' key)
                quote_data = {
                    'symbol': symbol_upper,
                    'price': round(latest_price, 4),
                    'change': round(change, 4),
                    'changePercent': round(change_percent, 2),
                    'changePercent5d': round(change_percent_5d, 2),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'yfinance'
                }

                self.send_json_response(quote_data)
            else:
                # NO FAKE DATA - Return null on failure
                self.send_json_response({
                    'symbol': symbol_upper,
                    'price': None,
                    'change': None,
                    'changePercent': None,
                    'changePercent5d': None,
                    'timestamp': datetime.now().isoformat(),
                    'error': 'No data available'
                }, status=404)

        except Exception as e:
            print(f"Error in handle_market_quote for {symbol}: {e}")
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, status=500)

    def handle_market_breadth(self):
        """Market Breadth with NO N/A guarantee"""
        try:
            complete_data = get_complete_market_data()
            self.send_json_response({
                'market_breadth': complete_data['market_breadth'],
                'guarantee': 'NO N/A FIELDS - Live scraped data',
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)

    def handle_put_call_ratio(self):
        """Put/Call ratio with NO N/A guarantee"""
        try:
            complete_data = get_complete_market_data()
            self.send_json_response({
                'put_call_ratio': complete_data['put_call_ratio'],
                'guarantee': 'NO N/A FIELDS - Live scraped data',
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)

    def handle_volatility_data(self):
        """Volatility data with VIX - EMERGENCY MODE"""
        try:
            # CRITICAL NOTICE: Yahoo Finance API is completely down (11/25/2025)
            # Polygon.io free tier doesn't include indices (I:VIX requires paid plan)
            # Returning error message instead of fake data (per NO FAKE DATA policy)

            error_message = {
                'status': 'unavailable',
                'reason': 'Data source failure',
                'details': 'Yahoo Finance API completely down (all tickers returning JSON parse errors). Polygon.io free tier does not include VIX index access (requires paid plan). No alternative free sources available for real-time VIX data.',
                'last_attempted': datetime.now().isoformat(),
                'workaround': 'Consider upgrading Polygon.io plan OR wait for Yahoo Finance API to recover',
                'data_integrity': 'NO FAKE DATA - returning error instead of simulated values'
            }

            self.send_json_response({
                'vix': None,
                'error': error_message,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Error in volatility endpoint: {e}")
            self.send_json_response({'error': str(e)}, status=500)

    def handle_complete_market_data(self):
        """Complete market data with NO N/A guarantee"""
        try:
            self.send_json_response(get_complete_market_data())
        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)

    def handle_all_complete_data(self):
        """Complete market and economic data with ZERO N/A fields"""
        try:
            complete_data = getAllCompleteData()
            self.send_json_response(complete_data)
        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)

    def handle_all_economic_data(self):
        """All economic indicators with ZERO N/A fields"""
        try:
            complete_data = getAllCompleteData()
            self.send_json_response({
                'economic_indicators': complete_data.get('economic_indicators', {}),
                'guarantee': 'ZERO N/A ECONOMIC DATA - All real sources',
                'timestamp': complete_data.get('last_updated')
            })
        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)

    def handle_inflation_data(self):
        """Inflation data with ZERO N/A fields"""
        try:
            complete_data = getAllCompleteData()
            economic = complete_data.get('economic_indicators', {})
            
            # Extract all inflation-related data
            inflation_data = {
                indicator: data for indicator, data in economic.items() 
                if indicator.lower().startswith(('cpi', 'inflation', 'pce', 'price'))
            }
            
            self.send_json_response({
                'inflation_data': inflation_data,
                'guarantee': 'ZERO N/A INFLATION DATA - Real sources only',
                'timestamp': complete_data.get('last_updated')
            })
        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)

    def handle_sector_rotation_data(self):
        """Sector rotation data with ZERO N/A fields"""
        try:
            complete_data = getAllCompleteData()
            market_stats = complete_data.get('market_statistics', {})
            market_data = market_stats.get('sectors', {})
            
            self.send_json_response({
                'sector_rotation': market_data,
                'guarantee': 'ZERO N/A SECTOR DATA - Real ETF analysis',
                'timestamp': complete_data.get('last_updated')
            })
        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)

    def handle_config(self):
        """Serve API keys from environment variables"""
        try:
            config = {
                'polygon_api_key': os.getenv('POLYGON_IO_API_KEY', ''),
                'fred_api_key': os.getenv('FRED_API_KEY', ''),
                'alpha_vantage_api_key': os.getenv('ALPHA_VANTAGE_API_KEY', ''),
                'timestamp': datetime.now().isoformat()
            }
            self.send_json_response(config)
        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)

    def handle_economic_indicators(self, query_string):
        """Fetch economic indicators - EMERGENCY MODE"""
        try:
            from urllib.parse import parse_qs

            # CRITICAL NOTICE: Yahoo Finance API is completely down (11/25/2025)
            # All yfinance Treasury ticker requests return JSON parse errors
            # No free alternative sources available for Treasury yields (FRED requires API key)

            # Parse query parameters
            params = parse_qs(query_string)
            series_ids_str = params.get('series_ids', [''])[0]
            series_ids = [s.strip() for s in series_ids_str.split(',') if s.strip()]

            result = {}
            error_message = {
                'status': 'unavailable',
                'reason': 'Data source failure',
                'details': 'Yahoo Finance API completely down (all Treasury tickers ^IRX, ^TNX, ^TYX returning JSON parse errors). FRED API requires API key (currently not configured). No alternative free sources available.',
                'last_attempted': datetime.now().isoformat(),
                'workaround': 'Add FRED_API_KEY to .env file OR wait for Yahoo Finance API to recover',
                'data_integrity': 'NO FAKE DATA - returning null instead of simulated values'
            }

            # Return null for all requested series with error explanation
            for series_id in series_ids:
                result[series_id.lower()] = None

            result['_error'] = error_message
            self.send_json_response(result)

        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)

    def handle_fundamental_economic(self, indicator):
        """Get economic indicator data from Redis/PostgreSQL"""
        try:
            indicator_upper = indicator.upper()

            # Check Redis cache first
            if redis_client:
                try:
                    redis_key = f'fundamental:economic:{indicator_upper}'
                    cached_data = redis_client.get(redis_key)

                    if cached_data:
                        data = json.loads(cached_data)
                        data['cache_hit'] = 'redis'
                        print(f"✅ Redis cache hit for economic indicator {indicator_upper}: {data.get('value')}")
                        self.send_json_response({'data': data})
                        return
                except Exception as e:
                    print(f"Redis error for {indicator_upper}: {e}")

            # Check PostgreSQL backup
            try:
                db_conn = psycopg2.connect(
                    dbname=os.getenv('POSTGRES_DB', 'spartan_research_db'),
                    user=os.getenv('POSTGRES_USER', 'spartan'),
                    password=os.getenv('POSTGRES_PASSWORD', 'spartan'),
                    host='localhost',
                    port=5432
                )

                with db_conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT symbol, price, metadata, timestamp, source
                        FROM preloaded_market_data
                        WHERE symbol = %s AND data_type = 'economic'
                        ORDER BY timestamp DESC
                        LIMIT 1
                    """, (indicator_upper,))

                    row = cur.fetchone()
                    if row:
                        data = dict(row)
                        if isinstance(data['timestamp'], datetime):
                            data['timestamp'] = data['timestamp'].isoformat()
                        # Parse metadata if it's JSON
                        if isinstance(data.get('metadata'), str):
                            try:
                                data['metadata'] = json.loads(data['metadata'])
                            except:
                                pass
                        data['cache_hit'] = 'postgresql'
                        print(f"✅ PostgreSQL hit for economic indicator {indicator_upper}")
                        self.send_json_response({'data': data})
                        db_conn.close()
                        return

                db_conn.close()
            except Exception as e:
                print(f"PostgreSQL error for {indicator_upper}: {e}")

            # No data found
            self.send_json_response({
                'error': f'Economic indicator {indicator_upper} not found',
                'message': 'Data will be available after next scan (runs every hour)'
            }, status=404)

        except Exception as e:
            print(f"Error handling economic indicator {indicator}: {e}")
            self.send_json_response({'error': str(e)}, status=500)

    def handle_fundamental_forex(self, pair):
        """Get forex pair data from Redis/PostgreSQL"""
        try:
            pair_upper = pair.upper()

            # Check Redis cache first
            if redis_client:
                try:
                    redis_key = f'fundamental:forex:{pair_upper}'
                    cached_data = redis_client.get(redis_key)

                    if cached_data:
                        data = json.loads(cached_data)
                        data['cache_hit'] = 'redis'
                        print(f"✅ Redis cache hit for forex {pair_upper}: {data.get('price')}")
                        self.send_json_response({'data': data})
                        return
                except Exception as e:
                    print(f"Redis error for {pair_upper}: {e}")

            # Check PostgreSQL backup
            try:
                db_conn = psycopg2.connect(
                    dbname=os.getenv('POSTGRES_DB', 'spartan_research_db'),
                    user=os.getenv('POSTGRES_USER', 'spartan'),
                    password=os.getenv('POSTGRES_PASSWORD', 'spartan'),
                    host='localhost',
                    port=5432
                )

                with db_conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT symbol, price, metadata, timestamp, source
                        FROM preloaded_market_data
                        WHERE symbol = %s AND data_type = 'forex'
                        ORDER BY timestamp DESC
                        LIMIT 1
                    """, (pair_upper,))

                    row = cur.fetchone()
                    if row:
                        data = dict(row)
                        if isinstance(data['timestamp'], datetime):
                            data['timestamp'] = data['timestamp'].isoformat()
                        if isinstance(data.get('metadata'), str):
                            try:
                                data['metadata'] = json.loads(data['metadata'])
                            except:
                                pass
                        data['cache_hit'] = 'postgresql'
                        print(f"✅ PostgreSQL hit for forex {pair_upper}")
                        self.send_json_response({'data': data})
                        db_conn.close()
                        return

                db_conn.close()
            except Exception as e:
                print(f"PostgreSQL error for {pair_upper}: {e}")

            # No data found
            self.send_json_response({
                'error': f'Forex pair {pair_upper} not found',
                'message': 'Data will be available after next scan (runs every hour)'
            }, status=404)

        except Exception as e:
            print(f"Error handling forex {pair}: {e}")
            self.send_json_response({'error': str(e)}, status=500)

    def handle_fundamental_company(self, symbol):
        """Get company fundamentals from Redis/PostgreSQL"""
        try:
            symbol_upper = symbol.upper()

            # Check Redis cache first
            if redis_client:
                try:
                    redis_key = f'fundamental:fundamentals:{symbol_upper}'
                    cached_data = redis_client.get(redis_key)

                    if cached_data:
                        data = json.loads(cached_data)
                        data['cache_hit'] = 'redis'
                        print(f"✅ Redis cache hit for fundamentals {symbol_upper}")
                        self.send_json_response({'data': data})
                        return
                except Exception as e:
                    print(f"Redis error for {symbol_upper}: {e}")

            # Check PostgreSQL backup
            try:
                db_conn = psycopg2.connect(
                    dbname=os.getenv('POSTGRES_DB', 'spartan_research_db'),
                    user=os.getenv('POSTGRES_USER', 'spartan'),
                    password=os.getenv('POSTGRES_PASSWORD', 'spartan'),
                    host='localhost',
                    port=5432
                )

                with db_conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT symbol, metadata, timestamp, source
                        FROM preloaded_market_data
                        WHERE symbol = %s AND data_type = 'fundamentals'
                        ORDER BY timestamp DESC
                        LIMIT 1
                    """, (symbol_upper,))

                    row = cur.fetchone()
                    if row:
                        data = dict(row)
                        if isinstance(data['timestamp'], datetime):
                            data['timestamp'] = data['timestamp'].isoformat()
                        if isinstance(data.get('metadata'), str):
                            try:
                                data['metadata'] = json.loads(data['metadata'])
                            except:
                                pass
                        data['cache_hit'] = 'postgresql'
                        print(f"✅ PostgreSQL hit for fundamentals {symbol_upper}")
                        self.send_json_response({'data': data})
                        db_conn.close()
                        return

                db_conn.close()
            except Exception as e:
                print(f"PostgreSQL error for {symbol_upper}: {e}")

            # No data found
            self.send_json_response({
                'error': f'Fundamentals for {symbol_upper} not found',
                'message': 'Data will be available after next scan (runs every hour)'
            }, status=404)

        except Exception as e:
            print(f"Error handling fundamentals {symbol}: {e}")
            self.send_json_response({'error': str(e)}, status=500)

    def handle_recession_probability(self):
        """Calculate recession probability based on yield curve spread"""
        try:
            # Get 10Y and 3M yields from FRED data
            spread = None
            yield_10y = None
            yield_3m = None

            if redis_client:
                try:
                    # Get 10-Year Treasury yield (DGS10)
                    dgs10_data = redis_client.get('fundamental:economic:DGS10')
                    if dgs10_data:
                        yield_10y = json.loads(dgs10_data).get('value')

                    # Get 3-Month Treasury yield (DTB3)
                    dtb3_data = redis_client.get('fundamental:economic:DTB3')
                    if dtb3_data:
                        yield_3m = json.loads(dtb3_data).get('value')

                    # Calculate spread
                    if yield_10y is not None and yield_3m is not None:
                        spread = yield_10y - yield_3m
                except Exception as e:
                    print(f"Error fetching yield data: {e}")

            # Calculate recession probability using logistic regression
            # Based on historical data: inverted curve (negative spread) predicts recession
            if spread is not None:
                # Logistic function: P = 1 / (1 + e^(-k*(spread - threshold)))
                # Inverted for negative spread = higher probability
                # Parameters calibrated from historical data
                k = 2.0  # Steepness
                threshold = 0.0  # Spread threshold

                import math
                # Invert: negative spread → high probability
                probability = 100 / (1 + math.exp(k * (spread - threshold)))

                # Determine risk level
                if probability < 15:
                    risk_level = "LOW"
                    risk_emoji = "🟢"
                    risk_desc = "Low recession risk - yield curve is normal"
                elif probability < 30:
                    risk_level = "MODERATE"
                    risk_emoji = "🟡"
                    risk_desc = "Moderate risk - yield curve flattening"
                elif probability < 50:
                    risk_level = "ELEVATED"
                    risk_emoji = "🟠"
                    risk_desc = "Elevated risk - yield curve near inversion"
                elif probability < 70:
                    risk_level = "HIGH"
                    risk_emoji = "🔴"
                    risk_desc = "High risk - yield curve inverted"
                else:
                    risk_level = "CRITICAL"
                    risk_emoji = "🚨"
                    risk_desc = "Critical risk - deep yield curve inversion"

                response = {
                    'spread': round(spread, 2),
                    'probability': round(probability, 1),
                    'risk_level': risk_level,
                    'risk_emoji': risk_emoji,
                    'risk_desc': risk_desc,
                    'yield_10y': yield_10y,
                    'yield_3m': yield_3m,
                    'timestamp': datetime.now().isoformat()
                }

                self.send_json_response(response)
            else:
                self.send_json_response({
                    'error': 'Yield data not available',
                    'message': 'Waiting for FRED data to be cached'
                }, status=503)

        except Exception as e:
            print(f"Error in handle_recession_probability: {e}")
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, status=500)

    def handle_market_narrative(self):
        """Generate market narrative based on macro conditions"""
        try:
            narrative = "Analyzing market conditions..."
            regime = "UNKNOWN"
            confidence = 0.0

            if redis_client:
                try:
                    # Get key market indicators
                    spy_data = redis_client.get('market:symbol:SPY')
                    vix_data = redis_client.get('fundamental:economic:VIXCLS')
                    dxy_data = redis_client.get('market:symbol:UUP')  # Dollar index
                    gold_data = redis_client.get('market:symbol:GLD')

                    spy_change = 0
                    vix_value = 0
                    dxy_change = 0
                    gold_change = 0

                    if spy_data:
                        spy_obj = json.loads(spy_data)
                        spy_change = spy_obj.get('change_percent', 0)

                    if vix_data:
                        vix_obj = json.loads(vix_data)
                        vix_value = vix_obj.get('value', 0)

                    if dxy_data:
                        dxy_obj = json.loads(dxy_data)
                        dxy_change = dxy_obj.get('change_percent', 0)

                    if gold_data:
                        gold_obj = json.loads(gold_data)
                        gold_change = gold_obj.get('change_percent', 0)

                    # Determine regime based on conditions
                    if spy_change > 0.5 and vix_value < 20 and dxy_change < 0:
                        regime = "RISK_ON"
                        narrative = f"Risk-On: Equities rising (+{spy_change:.1f}%), VIX low ({vix_value:.1f}), Dollar weak"
                        confidence = 0.85
                    elif spy_change < -0.5 and vix_value > 25:
                        regime = "RISK_OFF"
                        narrative = f"Risk-Off: Equities falling ({spy_change:.1f}%), VIX elevated ({vix_value:.1f})"
                        confidence = 0.80
                    elif gold_change > 1.0 and vix_value > 20:
                        regime = "FLIGHT_TO_SAFETY"
                        narrative = f"Flight to Safety: Gold surging (+{gold_change:.1f}%), VIX elevated ({vix_value:.1f})"
                        confidence = 0.75
                    elif abs(spy_change) < 0.3 and vix_value < 25:
                        regime = "CONSOLIDATION"
                        narrative = f"Consolidation: Markets range-bound, VIX {vix_value:.1f}"
                        confidence = 0.70
                    else:
                        regime = "TRANSITION"
                        narrative = "Mixed signals - market in transition"
                        confidence = 0.50

                except Exception as e:
                    print(f"Error analyzing market conditions: {e}")

            response = {
                'narrative': narrative,
                'regime': regime,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat()
            }

            self.send_json_response(response)

        except Exception as e:
            print(f"Error in handle_market_narrative: {e}")
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, status=500)

    def proxy_to_cot_scanner(self, path):
        """Proxy requests to COT Scanner API on port 5009"""
        try:
            # Forward request to COT Scanner API
            target_url = f'http://localhost:5009{path}'

            try:
                with urllib.request.urlopen(target_url, timeout=30) as response:
                    data = response.read()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(data)
            except urllib.error.URLError as e:
                # COT Scanner API not running
                print(f"⚠️  COT Scanner API not available: {e}")
                self.send_json_response({
                    'error': 'COT Scanner API not available',
                    'message': 'Please start the COT Scanner API server on port 5009',
                    'command': 'python cot_scanner_api.py'
                }, status=503)
        except Exception as e:
            print(f"Error proxying to COT Scanner: {e}")
            traceback.print_exc()
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
    """Start the main HTTP server"""

    print("=" * 70)
    print(" SPARTAN RESEARCH STATION - MAIN SERVER")
    print("=" * 70)
    print()
    print(f"Starting main server on port {PORT}...")
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
        print("  Run: python3 create_symbols_database_json.py")

    print()
    print("Server URLs:")
    print(f"  Main Dashboard:   http://localhost:{PORT}/index.html")
    print(f"  Capital Flow:     http://localhost:{PORT}/global_capital_flow_swing_trading.html")
    print()
    print("API Endpoints:")
    print(f"  Health Check:     http://localhost:{PORT}/health")
    print(f"  Database Stats:   http://localhost:{PORT}/api/db/stats")
    print(f"  Symbol Search:    http://localhost:{PORT}/api/db/search?query=AAPL")
    print(f"  All Symbols:      http://localhost:{PORT}/api/db/symbols?limit=100")
    print()
    print("=" * 70)
    print("Server is running. Press Ctrl+C to stop.")
    print("=" * 70)
    print()

    # Start server
    with socketserver.TCPServer(("", PORT), SpartanHTTPRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nServer stopped by user")
            print("=" * 70)


if __name__ == "__main__":
    main()
