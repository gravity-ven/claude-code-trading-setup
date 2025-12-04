# Spartan Autonomous System Guide

## Overview

The **Spartan Autonomous System** provides complete self-starting, self-monitoring, and self-healing capabilities for the Spartan Research Station. It integrates Claude Code for advanced autonomous diagnosis and fixing of complex issues.

## Quick Start

```bash
# Start the entire system (one command)
./START_SPARTAN_AUTONOMOUS.sh

# Check status anytime
./STATUS_SPARTAN_AUTONOMOUS.sh

# Restart everything
./RESTART_SPARTAN_AUTONOMOUS.sh

# Stop everything
./STOP_SPARTAN_AUTONOMOUS.sh
```

## What It Does

### Phase 1: Environment Validation ✅

Automatically checks and starts:
- ✅ PostgreSQL database
- ✅ Redis cache
- ✅ Database schema
- ✅ Python virtual environment
- ✅ Environment variables
- ✅ Claude Code CLI (if available)

### Phase 2: Service Startup 🚀

Starts all services automatically:
- ✅ Main Web Server (port 8888)
- ✅ Correlation API (port 5004)
- ✅ Daily Planet API (port 5000)
- ✅ Swing Dashboard API (port 5002)
- ✅ GARP API (port 5003)

### Phase 3: Data Loading 📊

- ✅ Runs data preloader (30-60 seconds)
- ✅ Starts 15-minute auto-refresh scheduler
- ✅ Validates data freshness

### Phase 4: Autonomous Monitoring 🤖

**Background Health Monitor**:
- Checks all services every 60 seconds
- Auto-restarts failed services
- Clears Redis cache when needed
- Triggers data refresh on failures
- Logs all activities

**Claude Code Integration** (if installed):
- Monitors health monitor logs
- Detects critical failures
- Automatically launches Claude Code with context
- Creates detailed issue summaries
- Provides autonomous diagnosis and fixing

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  START_SPARTAN_AUTONOMOUS.sh                │
│                                                             │
│  Phase 1: Environment → Phase 2: Services                  │
│  Phase 3: Data        → Phase 4: Monitoring                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                ┌─────────────────────────────┐
                │  Autonomous Health Monitor   │
                │  (logs/autonomous_health_monitor.sh)
                │                              │
                │  • Checks services (60s)     │
                │  • Auto-restarts failures    │
                │  • Clears cache              │
                │  • Refreshes data            │
                └─────────────────────────────┘
                              │
                              ▼
                ┌─────────────────────────────┐
                │  Claude Code Watcher         │
                │  (logs/claude_code_watcher.sh)
                │                              │
                │  • Monitors for critical     │
                │  • Creates issue summaries   │
                │  • Launches Claude Code      │
                │  • Provides full context     │
                └─────────────────────────────┘
```

## Self-Healing Capabilities

### Level 1: Automatic Service Restart

When a service fails health check:
1. Monitor detects failure
2. Automatically restarts the service
3. Verifies health after restart
4. Logs action

### Level 2: Cache and Data Refresh

When multiple failures occur:
1. Clears Redis cache
2. Triggers emergency data preload
3. Restarts all affected services
4. Validates data freshness

### Level 3: Claude Code Integration

When critical issues persist:
1. Detects pattern of failures
2. Creates comprehensive issue summary:
   - Recent logs (last 50 entries)
   - Service status (all processes)
   - Database status (data freshness)
   - Redis status (cache stats)
3. Launches Claude Code with full context
4. Claude Code diagnoses and fixes autonomously
5. 5-minute cooldown to prevent spam

## Usage Examples

### Start the System

```bash
./START_SPARTAN_AUTONOMOUS.sh
```

**What happens:**
- Environment validated
- Services started
- Data loaded
- Monitoring activated
- Terminal shows live health logs

**Safe to close terminal** - All services run in background!

### Check System Status

```bash
./STATUS_SPARTAN_AUTONOMOUS.sh
```

**Shows:**
- Infrastructure status (PostgreSQL, Redis)
- Web services status (all 5 APIs)
- Background services (refresh, monitor, Claude watcher)
- Database data freshness
- Recent activity (last 10 log entries)
- Quick health test
- Overall system health summary

### Restart System

```bash
./RESTART_SPARTAN_AUTONOMOUS.sh
```

**Process:**
1. Stops all services gracefully
2. Waits 3 seconds
3. Starts everything fresh
4. Re-initializes monitoring

### Stop System

```bash
./STOP_SPARTAN_AUTONOMOUS.sh
```

**Stops:**
- All web services
- Background monitoring
- Data refresh scheduler
- Claude Code watcher
- Clears all port locks

## Monitoring and Logs

### Log Files (in `logs/` directory)

**Service Logs:**
- `main_server.log` - Main web server
- `correlation_api.log` - Correlation API
- `daily_planet_api.log` - Daily Planet API
- `swing_api.log` - Swing Dashboard API
- `garp_api.log` - GARP API

**System Logs:**
- `data_preloader.log` - Initial data loading
- `data_refresh.log` - 15-minute refresh cycles
- `health_monitor.log` - Autonomous health checks
- `claude_watcher.log` - Claude Code integration
- `autonomous_monitor.log` - Master log

**Monitoring Commands:**

```bash
# Watch health monitor live
tail -f logs/health_monitor.log

# Watch Claude watcher
tail -f logs/claude_watcher.log

# Watch all logs
tail -f logs/*.log

# View last 50 health events
tail -n 50 logs/health_monitor.log

# Search for errors
grep -i "error\|failed" logs/*.log
```

## Health Check Endpoints

Test manually:

```bash
# Main server
curl http://localhost:8888/health

# Correlation API
curl http://localhost:5004/health

# Daily Planet API
curl http://localhost:5000/health

# Swing Dashboard API
curl http://localhost:5002/api/swing-dashboard/health

# GARP API
curl http://localhost:5003/api/health
```

## Process Management

### View Running Processes

```bash
# All Spartan processes
ps aux | grep -E 'start_server|correlation|daily_planet|swing|garp|autonomous|claude_watcher'

# Just web services
ps aux | grep -E 'start_server|correlation_api|daily_planet_api|swing_dashboard_api|garp_api'

# Just monitors
ps aux | grep -E 'autonomous_health_monitor|claude_code_watcher'
```

### PID Files

Process IDs stored in `.pids/`:
- `.pids/main.pid` - Main server
- `.pids/correlation.pid` - Correlation API
- `.pids/daily_planet.pid` - Daily Planet API
- `.pids/swing.pid` - Swing Dashboard API
- `.pids/garp.pid` - GARP API
- `.pids/refresh.pid` - Data refresh scheduler
- `.pids/monitor.pid` - Health monitor
- `.pids/claude_watcher.pid` - Claude watcher

### Manual Service Control

```bash
# Restart single service
kill -9 $(cat .pids/main.pid)
python start_server.py > logs/main_server.log 2>&1 &
echo $! > .pids/main.pid

# Check if service is running
if ps -p $(cat .pids/main.pid) > /dev/null; then
    echo "Running"
else
    echo "Not running"
fi
```

## Claude Code Integration

### Requirements

```bash
# Install Claude Code CLI
curl -fsSL https://claude.ai/install.sh | sh

# Verify installation
claude --version
```

### How It Works

1. **Monitoring Phase:**
   - `claude_code_watcher.sh` monitors `health_monitor.log`
   - Detects critical failures (🚨 marker)

2. **Issue Summary Phase:**
   - Creates timestamped issue summary: `logs/issue_summary_<timestamp>.txt`
   - Contains:
     - Recent logs (50 lines)
     - Process status
     - Database status
     - Redis status

3. **Claude Activation Phase:**
   - Launches Claude Code CLI with message:
     ```
     URGENT: Spartan Research Station has encountered critical issues.
     Please analyze the issue summary at <path> and fix the problems.
     The system has auto-healing enabled but needs advanced diagnosis.
     Focus on: 1) Data loading issues, 2) API failures, 3) Database connection problems.
     Fix autonomously.
     ```

4. **Cooldown Phase:**
   - 5-minute cooldown to prevent multiple Claude launches
   - Allows Claude Code time to diagnose and fix

### Manual Claude Trigger

If you want to manually launch Claude Code for diagnosis:

```bash
# Create issue summary manually
./STATUS_SPARTAN_AUTONOMOUS.sh > logs/manual_issue_summary.txt

# Launch Claude Code
claude chat --message "Please analyze the Spartan Research Station status in logs/manual_issue_summary.txt and fix any issues autonomously."
```

## Troubleshooting

### System Won't Start

**Check PostgreSQL:**
```bash
pg_isready
sudo service postgresql start  # Linux/WSL
brew services start postgresql  # macOS
```

**Check Redis:**
```bash
redis-cli ping
sudo service redis-server start  # Linux/WSL
brew services start redis  # macOS
```

**Check ports are free:**
```bash
lsof -i :8888
lsof -i :5000
# Kill if needed: kill -9 <PID>
```

### Data Preloader Fails

**Check API keys:**
```bash
cat .env | grep FRED_API_KEY
```

**Run manually:**
```bash
source venv/bin/activate
python src/data_preloader.py
```

**View errors:**
```bash
tail -f logs/data_preloader.log
```

### Services Keep Restarting

**Check health monitor log:**
```bash
tail -f logs/health_monitor.log
```

**Check database connection:**
```bash
psql -d spartan_research_db -c "SELECT COUNT(*) FROM preloaded_market_data;"
```

**Check Redis:**
```bash
redis-cli KEYS 'market:*'
redis-cli GET market:index:SPY
```

### Claude Code Not Activating

**Verify installation:**
```bash
which claude
claude --version
```

**Check watcher is running:**
```bash
ps aux | grep claude_code_watcher
cat .pids/claude_watcher.pid
```

**View watcher logs:**
```bash
tail -f logs/claude_watcher.log
```

## Advanced Configuration

### Adjust Health Check Interval

Edit `START_SPARTAN_AUTONOMOUS.sh`:

```bash
# Change this line in autonomous_health_monitor.sh section
sleep 60  # Default: check every 60 seconds

# To:
sleep 30  # Check every 30 seconds
```

### Adjust Failure Threshold

Edit `START_SPARTAN_AUTONOMOUS.sh`:

```bash
# Change this line in autonomous_health_monitor.sh section
MAX_FAILURES=3  # Default: auto-heal after 3 failures

# To:
MAX_FAILURES=1  # Auto-heal immediately on first failure
```

### Adjust Claude Cooldown

Edit `START_SPARTAN_AUTONOMOUS.sh`:

```bash
# Change this line in claude_code_watcher.sh section
sleep 300  # Default: 5 minute cooldown

# To:
sleep 600  # 10 minute cooldown
```

## Integration with Other Scripts

### Use with Docker

The autonomous system is designed for **native development** mode. For Docker:

```bash
# Use Docker-specific scripts instead
./START_SPARTAN.sh  # Docker version
docker-compose up -d
```

### Use with Existing Dev Scripts

The autonomous system **replaces** these scripts:
- ~~`START_SPARTAN_DEV.sh`~~ → Use `START_SPARTAN_AUTONOMOUS.sh`
- ~~`STOP_SPARTAN_DEV.sh`~~ → Use `STOP_SPARTAN_AUTONOMOUS.sh`
- ~~`RESTART_SPARTAN_DEV.sh`~~ → Use `RESTART_SPARTAN_AUTONOMOUS.sh`

Additional features in autonomous version:
- ✅ Auto-healing
- ✅ Continuous monitoring
- ✅ Claude Code integration
- ✅ Better error handling

## System Requirements

**Operating System:**
- Linux (Ubuntu, Debian, etc.)
- macOS
- Windows WSL2

**Dependencies:**
- PostgreSQL 13+
- Redis 6.0+
- Python 3.13+
- Claude Code CLI (optional but recommended)

**Resources:**
- 2GB RAM minimum (4GB recommended)
- 1GB disk space
- Active internet connection (for data APIs)

## Performance

**Startup Time:**
- Environment validation: 5-10 seconds
- Service startup: 10-15 seconds
- Data preloading: 30-60 seconds
- **Total: 45-85 seconds to fully operational**

**Runtime Resources:**
- PostgreSQL: ~100MB RAM
- Redis: ~20MB RAM
- Web services: ~150MB RAM each
- Monitors: ~50MB RAM each
- **Total: ~700MB RAM**

**Network:**
- Data preload: ~5-10MB download
- Refresh cycles: ~1-2MB per 15 minutes
- **Total: ~100MB per day**

## Security Considerations

**API Keys:**
- Store in `.env` file (not committed to git)
- Never share API keys
- Rotate keys periodically

**Database:**
- Local PostgreSQL only (not exposed to internet)
- Strong password in production

**Monitoring:**
- Health monitor only checks localhost
- Claude Code runs locally (not cloud-based)

**Logs:**
- May contain sensitive data
- Located in `logs/` directory (gitignored)
- Clean up periodically

## Support

**Documentation:**
- Main README: `README.md`
- Architecture: `ARCHITECTURE.md`
- Data Preloader: `DATA_PRELOADER_GUIDE.md`
- Claude Integration: `CLAUDE_AUTONOMOUS_MODE.md`

**Logs for Debugging:**
```bash
# Create support bundle
tar -czf support_bundle.tar.gz logs/ .pids/ .env
# Send to support (remove sensitive data first!)
```

**Status Report:**
```bash
./STATUS_SPARTAN_AUTONOMOUS.sh > status_report.txt
# Share status_report.txt for support
```

---

## Summary

The Spartan Autonomous System provides a **complete hands-off experience** for running the Spartan Research Station:

✅ **Self-Starting** - Validates environment and starts all services automatically
✅ **Self-Monitoring** - Continuous health checks every 60 seconds
✅ **Self-Healing** - Auto-restarts services, clears cache, refreshes data
✅ **Claude Code Integration** - Advanced diagnosis and fixing for complex issues
✅ **Production-Ready** - Robust error handling and logging

**One command to start everything:**
```bash
./START_SPARTAN_AUTONOMOUS.sh
```

**Safe to close terminal** - All services run in background with autonomous monitoring!

---

**Last Updated:** November 23, 2025
**Version:** 1.0.0
**Status:** Production Ready
