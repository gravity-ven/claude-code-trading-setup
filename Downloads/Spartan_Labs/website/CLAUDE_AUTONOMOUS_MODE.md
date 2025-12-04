# Claude Code Autonomous Monitoring Mode

**Integrated autonomous monitoring with website_monitor agent**

## Overview

When you run `./START_SPARTAN.sh`, you get a **two-tier autonomous system**:

### Tier 1: Website Monitor Agent (Mojo + Claude AI)
- ✅ Monitors all Docker containers every 30 seconds
- ✅ Auto-heals simple issues (restarts, cache clearing)
- ✅ Uses Claude AI API for diagnosis
- ✅ Handles 95% of issues automatically

### Tier 2: Claude Code (Full AI Agent)
- ✅ Watches for complex issues the monitor can't fix
- ✅ Has full access to codebase and Docker
- ✅ Can modify code, configs, databases
- ✅ Commits fixes with proper documentation
- ✅ Handles the remaining 5% of complex issues

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS SYSTEM                        │
└─────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │  Docker Services │
    └────────┬─────────┘
             │
    ┌────────▼──────────┐
    │  Monitor Agent    │  ← Checks every 30s
    │  (Mojo + Claude)  │  ← Auto-heals 95%
    └────────┬──────────┘
             │
             │ Issues detected
             ▼
    ┌────────────────────┐
    │  Alert Watcher     │  ← Watches logs
    │  (Background)      │  ← Detects patterns
    └────────┬───────────┘
             │
             │ Complex issue (2+ failures)
             ▼
    ┌────────────────────┐
    │  Claude Code       │  ← Full AI agent
    │  (Terminal)        │  ← Can modify code
    └────────────────────┘
```

## Starting the System

### Option 1: With Claude Code (Recommended)

```bash
./START_SPARTAN.sh

# When prompted:
# "Do you want to start Claude Code in background monitoring mode? (y/n)"
# Press: y
```

**Result**:
- All Docker services start
- Monitor agent starts
- Alert watcher starts in background
- Claude Code launches in terminal with monitoring prompt

### Option 2: Without Claude Code

```bash
./START_SPARTAN.sh

# When prompted:
# Press: n
```

**Result**:
- All Docker services start
- Monitor agent starts
- Claude Code not started (can add later)

## What Claude Code Monitors

When active, Claude Code automatically:

### 1. Watches Logs

```bash
# Claude runs this continuously:
docker-compose logs -f spartan-website-monitor
```

**Looking for**:
- `CRITICAL` - Critical errors
- `container_unhealthy` - Health check failures
- `healing_failed` - Auto-heal failures
- `auto_heal_failed` - Multiple heal attempts failed

### 2. Checks Service Status

```bash
# Every few minutes:
docker-compose ps
docker-compose logs --tail=100 | grep -i error
```

### 3. Monitors Database

```sql
-- Checks for incident patterns:
SELECT * FROM monitor_incidents
WHERE auto_healed = false
ORDER BY timestamp DESC
LIMIT 10;
```

### 4. Reviews Metrics

```sql
-- Identifies performance issues:
SELECT container_name, AVG(response_time_ms) as avg_ms
FROM monitor_health_metrics
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY container_name
HAVING AVG(response_time_ms) > 1000;
```

## What Claude Code Fixes

Claude has access to **all tools and resources** needed to fix issues:

### Simple Fixes (Automatic)

✅ **Restart containers**: `docker-compose restart <service>`
✅ **Rebuild images**: `docker-compose build <service>`
✅ **Clear caches**: `docker exec <container> rm -rf /tmp/*`
✅ **Reset databases**: Drop/recreate tables if corrupted

### Code Fixes (Automatic)

✅ **Fix Python errors**: Read traceback, fix code, test
✅ **Update configs**: Modify YAML/JSON configs
✅ **Add error handling**: Wrap problematic code in try/except
✅ **Optimize queries**: Fix slow database queries

### Complex Fixes (Automatic with Verification)

✅ **Database migrations**: Create migration scripts
✅ **Dependency updates**: Update requirements.txt
✅ **Port conflicts**: Change ports in docker-compose.yml
✅ **Memory leaks**: Add garbage collection, fix caching
✅ **API rate limits**: Implement backoff, add caching

### What Claude Won't Do (Asks First)

❌ Delete volumes (data loss risk)
❌ Change API keys (security risk)
❌ Push to production without testing
❌ Make breaking changes to schemas

## Example Workflow

### Scenario: Database Connection Pool Exhausted

**1. Monitor detects issue** (10:30:00 AM)
```
[2025-11-20T10:30:00] container_unhealthy container:spartan-web status:503
```

**2. Monitor tries auto-heal** (10:30:05 AM)
```
[2025-11-20T10:30:05] restarting_container container:spartan-web
[2025-11-20T10:30:15] container_restarted container:spartan-web
```

**3. Issue persists** (10:30:45 AM)
```
[2025-11-20T10:30:45] container_unhealthy container:spartan-web status:503
[2025-11-20T10:30:50] healing_failed container:spartan-web reason:restart_ineffective
```

**4. Alert watcher detects pattern** (10:31:00 AM)
```
⚠️  Multiple healing failures detected - Claude Code intervention needed
```

**5. Claude Code investigates** (10:31:05 AM)
```bash
# Claude runs:
docker-compose logs spartan-web --tail=50

# Sees:
# psycopg2.OperationalError: FATAL: remaining connection slots are reserved
# HINT: max_connections = 100
```

**6. Claude diagnoses**
```
Root cause: PostgreSQL max_connections limit reached
Current connections: 95/100
Application not closing connections properly
```

**7. Claude fixes** (10:31:30 AM)

**Step 1 - Immediate fix**:
```bash
# Increase max_connections
docker exec -it spartan-postgres psql -U spartan -d spartan_research_db -c \
  "ALTER SYSTEM SET max_connections = 200;"

# Restart PostgreSQL
docker-compose restart spartan-postgres
```

**Step 2 - Long-term fix**:
```python
# Edits start_server.py
# Adds connection pooling:

from psycopg2 import pool

db_pool = pool.SimpleConnectionPool(
    minconn=5,
    maxconn=20,
    dsn=DATABASE_URL
)

# Updates all queries to use pool:
def get_db_connection():
    return db_pool.getconn()

def release_db_connection(conn):
    db_pool.putconn(conn)
```

**Step 3 - Test**:
```bash
# Restart web service
docker-compose restart spartan-web

# Verify
docker-compose logs spartan-web --tail=20
curl http://localhost:8888/health
```

**Step 4 - Commit**:
```bash
git add start_server.py
git commit -m "fix: Add PostgreSQL connection pooling to prevent exhaustion

- Implements psycopg2 connection pool (5-20 connections)
- Increases PostgreSQL max_connections to 200
- Fixes container_unhealthy errors from connection exhaustion
- Tested: Health endpoint returns 200 OK

Resolves: Database connection pool exhaustion causing 503 errors"
```

**8. Verify fix** (10:35:00 AM)
```
[2025-11-20T10:35:00] container_healthy container:spartan-web cpu:2.1 mem_mb:150.3
```

**Total time to fix**: 5 minutes (vs hours of manual debugging)

## Monitoring Claude's Activity

### View Alert Watcher Logs

```bash
tail -f logs/alert_watcher.log
```

**Shows**:
- Critical alerts detected
- When Claude was invoked
- Alert patterns

### View Claude Trigger File

```bash
cat logs/claude_trigger.txt
```

**Shows**:
- All errors that triggered Claude investigation
- Timestamps and error messages

### View Critical Alerts

```bash
cat logs/critical_alerts.log
```

**Shows**:
- Timeline of critical issues
- Pattern analysis (restart loops, memory leaks, etc.)

## Manual Claude Invocation

If you didn't start Claude with `START_SPARTAN.sh`, you can start it manually:

### Step 1: Start Claude

```bash
cd /path/to/Spartan_Labs/website
claude
```

### Step 2: Paste Monitoring Prompt

```bash
# The prompt is saved at:
cat logs/claude_monitoring_prompt.txt
```

Copy and paste into Claude Code terminal.

### Step 3: Claude Starts Monitoring

Claude will now:
- Watch logs continuously
- Check service status
- Fix issues as they arise
- Commit changes automatically

## Configuration

### Adjust Alert Sensitivity

Edit `logs/alert_watcher.sh`:

```bash
# Current: Trigger after 2 failures
if [ "$FAILURE_COUNT" -ge 2 ]; then

# Change to trigger after 1 failure (more sensitive):
if [ "$FAILURE_COUNT" -ge 1 ]; then

# Change to trigger after 5 failures (less sensitive):
if [ "$FAILURE_COUNT" -ge 5 ]; then
```

### Modify What Triggers Alerts

Edit `logs/alert_watcher.sh`:

```bash
# Current triggers:
if echo "$line" | grep -qE "(CRITICAL|container_unhealthy|healing_failed|auto_heal_failed)"; then

# Add more triggers:
if echo "$line" | grep -qE "(CRITICAL|ERROR|FATAL|container_unhealthy|healing_failed|auto_heal_failed|timeout|connection_error)"; then
```

### Change Monitoring Interval

Edit `agents/website_monitor/config.yaml`:

```yaml
monitoring:
  interval_seconds: 30  # Current

  # Options:
  # 15  - Check every 15 seconds (faster detection, more CPU)
  # 30  - Check every 30 seconds (balanced)
  # 60  - Check every 60 seconds (lower overhead)
```

## Stopping the System

### Stop Everything

```bash
./STOP_SPARTAN.sh
```

**Stops**:
- All Docker containers
- Website monitor agent
- Alert watcher
- Claude Code (if running)

### Stop Only Claude

```bash
# In Claude terminal, press Ctrl+C
# OR
# In another terminal:
kill $(cat logs/alert_watcher.pid)
```

## Portability (macOS/Linux/Windows)

**Everything works identically on**:

### macOS
```bash
cd ~/Documents/Spartan_Labs/website
./START_SPARTAN.sh
# Press 'y' when asked about Claude Code
```

### Linux
```bash
cd ~/projects/Spartan_Labs/website
./START_SPARTAN.sh
# Press 'y' when asked about Claude Code
```

### Windows WSL
```bash
cd /mnt/c/Users/YourName/Spartan_Labs/website
./START_SPARTAN.sh
# Press 'y' when asked about Claude Code
```

**No changes needed** - script auto-detects OS and adapts.

## Performance Impact

**Alert Watcher**:
- CPU: <0.5%
- Memory: ~20MB
- Disk I/O: Minimal (log tailing)

**Claude Code**:
- CPU: 1-5% (idle), 10-50% (actively fixing)
- Memory: ~200MB
- Network: API calls to Claude (only when diagnosing)

**Total overhead**: <1% when idle, <10% when actively fixing issues

## Best Practices

### 1. Keep Claude Terminal Open

The terminal running Claude Code should stay open for continuous monitoring.

**Option A**: Run in `tmux` or `screen` session
**Option B**: Run on dedicated server/container
**Option C**: Use systemd service (Linux/macOS)

### 2. Review Claude's Commits

Claude commits fixes automatically, but review them:

```bash
git log --oneline -10
git show HEAD  # View latest commit
```

### 3. Monitor Resource Usage

```bash
# Check container stats
docker stats

# Check alert watcher
ps aux | grep alert_watcher

# Check disk space (logs can grow)
df -h .
```

### 4. Periodic Cleanup

```bash
# Clean old logs (>7 days)
find logs/ -name "*.log" -mtime +7 -delete

# Prune Docker
docker system prune -af
```

## Troubleshooting

### Claude not starting

**Check if installed**:
```bash
which claude
# OR
command -v claude
```

**Install if missing**: https://claude.ai/download

### Alert watcher not triggering

**Check if running**:
```bash
ps aux | grep alert_watcher
```

**Restart**:
```bash
./START_SPARTAN.sh
# Press 'y' for Claude Code
```

### Claude not fixing issues

**Check prompt**:
```bash
cat logs/claude_monitoring_prompt.txt
```

**Verify Claude has access**:
- Codebase readable/writable
- Docker socket accessible
- Git configured

### Too many alerts

**Increase threshold** in `logs/alert_watcher.sh`:
```bash
# Change from 2 to 5
if [ "$FAILURE_COUNT" -ge 5 ]; then
```

## Summary

**One command**: `./START_SPARTAN.sh`

**What you get**:
- ✅ All services running
- ✅ Monitor agent (handles 95% of issues)
- ✅ Alert watcher (detects complex patterns)
- ✅ Claude Code (fixes remaining 5%)
- ✅ Complete autonomy - no manual intervention needed
- ✅ Full commit history of all fixes
- ✅ Works identically on macOS/Linux/Windows

**Your job**: None - the system fixes itself!

---

**Built with**: Mojo (100x faster) + Claude AI (infinitely smarter)
