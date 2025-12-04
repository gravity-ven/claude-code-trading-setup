# Spartan Research Station - Agent Integration Guide

## Trigger File System

### Purpose

Agents write structured JSON files when they need Claude Code intervention.

**Location**: `logs/trigger_claude_data_fix.json`

### Trigger Format

```json
{
  "timestamp": "2025-11-27T10:30:00Z",
  "agent": "data_validator_agent",
  "issue_type": "api_key_missing",
  "severity": "high",
  "details": {
    "missing_key": "FRED_API_KEY",
    "impact": "Economic indicators unavailable",
    "affected_symbols": ["DGS10", "DTB3", "CPIAUCSL", "UNRATE"]
  },
  "attempted_fixes": [
    "Checked .env file - key not found",
    "Checked environment variables - not set",
    "Attempted fallback to yfinance - partial success"
  ],
  "recommended_action": "Add FRED_API_KEY to .env file. Get free key at: https://fred.stlouisfed.org/docs/api/api_key.html",
  "escalation_reason": "Cannot proceed without API credentials"
}
```

### Watcher Script

`logs/claude_code_watcher.sh` (optional):

```bash
#!/bin/bash
# Watches for trigger files and alerts Claude Code

while true; do
    if [ -f logs/trigger_claude_data_fix.json ]; then
        echo "🚨 AGENT ESCALATION DETECTED"
        cat logs/trigger_claude_data_fix.json
        # Optional: Send notification (Slack, email, etc.)
        # claude_code --file logs/trigger_claude_data_fix.json
    fi
    sleep 60
done
```

---

## Autonomous Resolution Logs

### Purpose

Track what agents fixed automatically (for learning/auditing).

**Location**: `logs/autonomous_healing_*.log`

### Log Format

```
[2025-11-27 10:15:30] ✅ AUTO-FIX: Restored SPY to Redis from PostgreSQL (cache miss)
[2025-11-27 10:16:45] ✅ AUTO-FIX: Created alias ^TNX → economic:DGS10 (symbol mapping)
[2025-11-27 10:20:00] ⚡ AUTO-ADJUST: Increased polygon delay 12s → 18s (rate limit)
[2025-11-27 10:25:00] ✅ AUTO-FIX: Triggered data refresh for 3 stale symbols
[2025-11-27 10:30:00] ❌ ESCALATION: Missing FRED_API_KEY → trigger_claude_data_fix.json
```

---

## Agent Decision Matrix

### When to Auto-Fix vs Escalate

| Issue Type | Agent Can Fix? | Action | Escalate? |
|------------|----------------|--------|-----------|
| Cache miss (data in PostgreSQL) | ✅ Yes | Copy to Redis | No |
| Stale data (< 1 hour old) | ✅ Yes | Trigger refresh | No |
| Rate limit error | ✅ Yes | Increase delay, retry | No |
| Symbol mapping mismatch | ✅ Yes | Create Redis alias | No |
| API key missing | ❌ No | Log error | **Yes** |
| API key invalid | ❌ No | Log error | **Yes** |
| PostgreSQL down | ❌ No | Alert | **Yes** |
| Redis down | ❌ No | Alert | **Yes** |
| All data sources fail | ❌ No | Emergency mode | **Yes** |
| Disk space < 10% | ❌ No | Alert | **Yes** |

---

## Autonomous Troubleshooting Patterns

### Scenario 1: Stale Data Detected

**Agent Decision Tree:**

```
1. Check Redis TTL → Expired?
   YES → Trigger immediate data refresh
   NO  → Check PostgreSQL backup

2. Check PostgreSQL freshness → Data < 20 min old?
   YES → Copy to Redis (restore cache)
   NO  → Trigger data preloader

3. Data preloader fails?
   YES → Check API keys in .env
   NO  → Success, cache restored

4. API keys missing/invalid?
   YES → Write trigger for Claude Code: "API key issue, needs manual config"
   NO  → Check rate limiting (last_request_times)

5. Rate limit exceeded?
   YES → Increase delay in REQUEST_DELAYS dict
   NO  → Log unknown error, escalate to Claude Code
```

### Scenario 2: Redis Cache Miss

**Agent Actions:**

```python
# Autonomous fix (no human intervention)
def fix_cache_miss(symbol):
    # 1. Check PostgreSQL for recent data
    recent = get_from_postgres(symbol, max_age_minutes=20)

    if recent:
        # Restore to Redis
        redis_client.setex(f'market:symbol:{symbol}', 900, json.dumps(recent))
        log(f"✅ Restored {symbol} to Redis from PostgreSQL")
        return True

    # 2. Trigger fresh fetch via data_preloader
    trigger_data_refresh([symbol])
    log(f"⚡ Triggered refresh for {symbol}")
    return True
```

### Scenario 3: API Rate Limit Hit

**Agent Auto-Resolution:**

```python
# Detect rate limit error patterns
RATE_LIMIT_ERRORS = [
    "429 Too Many Requests",
    "Rate limit exceeded",
    "API rate limit"
]

def handle_rate_limit(api_name, error_msg):
    # Auto-adjust delays
    current_delay = REQUEST_DELAYS.get(api_name, 2.0)
    new_delay = current_delay * 1.5  # Increase by 50%

    # Update in-memory config
    REQUEST_DELAYS[api_name] = new_delay

    # Persist to config file (for next restart)
    update_preloader_config(api_name, new_delay)

    log(f"⚡ Auto-adjusted {api_name} delay: {current_delay}s → {new_delay}s")

    # Wait and retry
    time.sleep(new_delay)
    return retry_request(api_name)
```

### Scenario 4: Symbol Mapping Mismatch

**Common Issue**: Frontend expects `^TNX`, Redis has `economic:DGS10`

**Agent Auto-Fix:**

```python
SYMBOL_MAPPINGS = {
    '^TNX': 'economic:DGS10',   # 10Y Treasury
    '^IRX': 'economic:DTB3',    # 3M Treasury
    '^VIX': 'economic:VIXCLS',  # VIX
}

def create_redis_alias(frontend_symbol, redis_key):
    # Get data from actual Redis key
    data = redis_client.get(redis_key)

    if data:
        # Create alias with frontend symbol
        alias_key = f'market:symbol:{frontend_symbol}'
        redis_client.setex(alias_key, 900, data)
        log(f"✅ Created alias: {frontend_symbol} → {redis_key}")
```

---

## Data Validation Checklist (For Agents)

### Pre-Startup Validation (`src/data_preloader.py`)

- [ ] 80%+ data sources succeed
- [ ] Critical symbols present: SPY, QQQ, DIA, IWM, ^VIX
- [ ] Redis connection healthy
- [ ] PostgreSQL connection healthy
- [ ] All data has valid timestamps (within 24 hours)
- [ ] No `null` values in critical fields (price, symbol, timestamp)

### Runtime Validation (`agents/website_data_validator_agent.py`)

- [ ] Data freshness < 20 minutes
- [ ] Redis TTL > 0 for all cached keys
- [ ] PostgreSQL has backup data
- [ ] No orphaned Redis keys (data exists but expired)
- [ ] Symbol mappings cover all frontend requirements

### Health Check Endpoints

```bash
# Main server health
curl http://localhost:8888/health
# Response: {"status": "ok", "server": "Spartan Main Server"}

# Data validation status
curl http://localhost:8888/health/data
# Response: {"fresh_symbols": 150, "stale_symbols": 3, "missing_symbols": 0}

# Redis health
redis-cli PING
# Response: PONG

# PostgreSQL health
psql -d spartan_research_db -c "SELECT COUNT(*) FROM preloaded_market_data WHERE timestamp > NOW() - INTERVAL '1 hour';"
```

---

## Claude Code Response Protocol

### When You Receive a Trigger File

**1. Read the trigger file:**
```bash
cat logs/trigger_claude_data_fix.json
```

**2. Assess severity:**
- `low`: Can wait, fix during next maintenance
- `medium`: Fix within 1 hour
- `high`: Fix immediately
- `critical`: System down, fix now

**3. Apply fix (examples):**

**Missing API Key:**
```bash
# Guide user to get key
echo "Get free FRED API key at: https://fred.stlouisfed.org/docs/api/api_key.html"
echo "Add to .env file: FRED_API_KEY=your_key_here"
# After user provides key, test it
python -c "import os; from fredapi import Fred; fred=Fred(os.getenv('FRED_API_KEY')); print(fred.get_series('DGS10').tail())"
```

**PostgreSQL Connection Issue:**
```bash
# Check if PostgreSQL is running
pg_isready
# Restart if needed
sudo systemctl restart postgresql
# Or in Docker
docker-compose restart spartan-postgres
```

**Redis Connection Issue:**
```bash
# Check Redis
redis-cli PING
# Restart if needed
sudo systemctl restart redis
# Or in Docker
docker-compose restart spartan-redis
```

**4. Verify fix worked:**
```bash
# Run data preloader
python src/data_preloader.py
# Check for success
echo $?  # Should be 0
```

**5. Clear trigger file (after fix verified):**
```bash
mv logs/trigger_claude_data_fix.json logs/resolved/trigger_$(date +%Y%m%d_%H%M%S).json
```

**6. Update agent if needed:**
- If issue was preventable, update agent logic
- Add new auto-fix pattern to agent code
- Document in autonomous_healing_*.log
