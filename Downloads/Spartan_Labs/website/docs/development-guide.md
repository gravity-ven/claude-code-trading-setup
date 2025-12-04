# Spartan Research Station - Development Guide

## Common Development Tasks

### 1. Adding New Data Source

**Steps:**

1. **Edit `src/data_preloader.py`:**

```python
async def preload_new_source(self):
    """Fetch new data source"""
    try:
        # CRITICAL: Apply rate limiting
        rate_limit('api_name')

        # Fetch data using REAL API (no fake data)
        data = await fetch_from_real_api()

        # Cache in Redis (15-min TTL)
        await self.redis_client.set(
            f'data:new_source',
            json.dumps(data),
            ex=self.cache_ttl
        )

        # Backup to PostgreSQL
        await self.save_to_db('new_source', data)

        return True
    except Exception as e:
        logger.error(f"Failed to fetch new source: {e}")
        return False  # Don't raise - allows other sources to continue

# Add to preload_all_data()
results["New_Source"] = await self.preload_new_source()
```

2. **Add rate limiting configuration:**

```python
# At top of file
REQUEST_DELAYS = {
    # ...existing delays...
    'api_name': 5.0,  # 5 seconds between requests
}
```

3. **Update validation threshold calculation to include new source**

4. **Test:**
```bash
docker exec spartan-data-preloader python src/data_preloader.py
```

---

### 2. Modifying Frontend JavaScript

**Pattern (three-tier cache):**

```javascript
// 1. Check IndexedDB first
const cachedData = await window.SpartanData.get('symbol:SPY');
if (cachedData && isFresh(cachedData)) {
    return cachedData;
}

// 2. Fetch from API (checks Redis → PostgreSQL internally)
const freshData = await fetch('/api/market/symbol/SPY');

// 3. Store in IndexedDB for next time
await window.SpartanData.store('symbol:SPY', freshData);
```

**Rules:**
1. Never add `Math.random()` or fake data
2. Always use three-tier cache pattern
3. Preserve existing data validation logic
4. Test locally: `docker-compose restart spartan-research-station`

---

### 3. Modifying Python API Servers

**Rules:**
1. Use `async`/`await` for all I/O operations
2. Always validate API responses before caching
3. Return `None` on errors (never fake data)
4. Add comprehensive error logging
5. Apply rate limiting for external APIs
6. Test endpoint: `curl http://localhost:{port}/health`

**Example:**

```python
from flask import Flask, jsonify
import yfinance as yf

app = Flask(__name__)

@app.route('/api/data/<symbol>')
def get_symbol_data(symbol):
    try:
        # Fetch real data
        ticker = yf.Ticker(symbol)
        data = ticker.history(period='1d')

        # Validate response
        if data.empty:
            return jsonify({'error': 'No data available'}), 404

        # Return real data
        return jsonify({
            'symbol': symbol,
            'price': float(data['Close'][-1]),
            'timestamp': data.index[-1].isoformat()
        })
    except Exception as e:
        # Log error
        app.logger.error(f"Error fetching {symbol}: {e}")

        # Return error (NO fake data)
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})
```

---

### 4. Add New API Endpoint

**In `start_server.py`, add to `SpartanHTTPRequestHandler`:**

```python
def do_GET(self):
    if path == '/api/new-endpoint':
        self.handle_new_endpoint()

def handle_new_endpoint(self):
    # ALWAYS follow three-tier cache pattern
    # 1. Check Redis
    if redis_client:
        cached = redis_client.get('data:new')
        if cached:
            return self.send_json_response(json.loads(cached))

    # 2. Check PostgreSQL
    # 3. Fetch fresh (yfinance/API)
    # 4. Return null if all fail (NO FAKE DATA)
```

---

### 5. Fix Data Freshness Issue

```bash
# Check what's stale
redis-cli KEYS 'market:*' | xargs -I {} sh -c 'echo {}; redis-cli TTL {}'

# Manually refresh all data
python src/data_preloader.py

# Or restart refresh scheduler
docker-compose restart spartan-data-refresh
```

---

### 6. Debug "No Data Available" on Dashboard

```bash
# 1. Check Redis
redis-cli GET market:symbol:SPY

# 2. Check PostgreSQL
psql -d spartan_research_db -U spartan -c \
  "SELECT * FROM preloaded_market_data WHERE symbol='SPY' ORDER BY timestamp DESC LIMIT 1;"

# 3. Test yfinance directly
python -c "import yfinance as yf; print(yf.Ticker('SPY').history(period='1d'))"

# 4. Check preloader logs
docker-compose logs spartan-data-preloader | grep SPY
```

---

### 7. Fix API Rate Limit

```python
# Edit src/data_preloader.py
REQUEST_DELAYS = {
    'polygon': 13.0,        # Increase from 12.0
    'alpha_vantage': 15.0,  # Increase from 13.0
}

# Then restart
docker-compose restart spartan-data-preloader spartan-data-refresh
```

---

## Critical Rules

### 1. NO FAKE DATA (Absolute)

```
❌ FORBIDDEN: Math.random(), mock data, simulated values
✅ REQUIRED: Real APIs only (yfinance, FRED, Alpha Vantage)
✅ ON ERROR: Return NULL/None, never generate fake fallback data
```

**Why**: Users make financial decisions based on this data. Integrity over availability.

---

### 2. PostgreSQL Only

```
✅ ALLOWED: PostgreSQL 13+ ONLY
❌ FORBIDDEN: SQLite, MySQL, MongoDB
```

**Databases:**
- `spartan_research_db` - Main database
- `spartan_trading_db` - Trading agent (separate project)

---

### 3. Preserve index.html Structure

The `index.html` file (2,051 lines) contains the complete flashcard navigation system. **DO NOT modify, simplify, or replace** this file unless specifically requested by the user.

---

### 4. Rate Limiting Required

**ALWAYS** apply rate limiting when adding new data sources to prevent API blocks:
- Add delays to `REQUEST_DELAYS` dict in `src/data_preloader.py`
- Use `rate_limit(api_name)` before each API call
- Test with `docker exec spartan-data-preloader python src/data_preloader.py`

---

## Git Workflow

**Commits:**
- Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`
- Include co-author: `Co-Authored-By: Claude <noreply@anthropic.com>`

**Before Pushing:**
1. Test locally with Docker: `docker-compose up -d`
2. Run health checks: `curl http://localhost:8888/health`
3. Verify data preloader succeeds: `docker-compose logs spartan-data-preloader | grep "✅"`
4. Check git status: `git status`

---

## Key File Locations

### When debugging, check these first

- `logs/autonomous_healing_*.log` - What agents fixed automatically
- `logs/trigger_claude_data_fix.json` - Agent escalations (if exists)
- `logs/data_validation_latest.json` - Data health status
- `.env` - API keys configuration
- `src/data_preloader.py` - Data fetching logic
- `start_server.py` - API endpoint handlers
- `docker-compose.yml` - Container orchestration

### When modifying

- `src/data_preloader.py` - Add data sources, adjust rate limits
- `start_server.py` - Add API endpoints
- `agents/website_data_validator_agent.py` - Modify autonomous healing logic
- `js/spartan-preloader.js` - Frontend cache logic
- `index.html` - Dashboard UI (preserve structure unless explicitly requested)
