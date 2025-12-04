# Spartan COT Agents - Persistent Market Monitor

## What This Is

A **continuous market monitoring system** that:
- ✅ Runs FOREVER (until you stop it)
- ✅ Analyzes markets using real CFTC API data
- ✅ Shows trade sheet INLINE in the dashboard
- ✅ Updates on your schedule (1 hour, 6 hours, 24 hours, etc.)
- ✅ NO FAKE DATA - Real CFTC.gov data only

---

## How to Start

### Quick Start (Demo Mode)
```bash
# Run with 4 agents, check every hour
./START_MONITOR.sh --demo
```

### Production Mode
```bash
# Run all 100 agents, check every hour
./START_MONITOR.sh

# Or customize interval (6 hours)
./START_MONITOR.sh --interval 6
```

---

## What You See

### Live Dashboard Layout

```
======================================================================
SPARTAN COT AGENTS - Continuous Market Monitoring

DEMO MODE | Uptime: 2h 15m | Cycles: 3 | Next cycle in: 42m 18s
======================================================================

+---- COT ----+  +-- Season --+  +-- Signals -+  +-- Trades --+
| [ACTIVE]    |  | [DONE]     |  | [WAIT]     |  | [WAIT]     |
| CFTC Data   |  | Patterns   |  | Confluence |  | Opportunities
|             |  |            |  |            |  |            |
| * Fetching  |  | * Dec bull |  |            |  |            |
| * Gold: -61k|  | * Q4 rally |  |            |  |            |
+-------------+  +------------+  +------------+  +------------+

+---------------------- Trade Opportunities (2) ---------------------+
|                                                                    |
|  Symbol | Direction | Confidence | Setup                          |
|  -------+-----------+------------+--------------------------------|
|  GC     | LONG      | 85%        | Commercial net short extreme   |
|  SI     | LONG      | 78%        | Q4 seasonal strength          |
|                                                                    |
|  Last updated: 2025-11-29 19:15:30                                |
+--------------------------------------------------------------------+

Press Ctrl+C to stop | Interval: 1h | Logs: tail -f logs/agents.log
======================================================================
```

---

## Key Features

### 1. Continuous Monitoring
- Runs cycles on schedule (default: 1 hour)
- Counts cycles: "Cycles: 3" shows 3 complete runs
- Shows next cycle countdown: "Next cycle in: 42m 18s"

### 2. Inline Trade Sheet
```
Trade Opportunities (2)
Symbol | Direction | Confidence | Setup
GC     | LONG      | 85%        | Commercial net short extreme
SI     | LONG      | 78%        | Q4 seasonal strength
```

**What this shows**:
- **Symbol**: Market ticker (GC = Gold, SI = Silver)
- **Direction**: LONG or SHORT
- **Confidence**: 0-100% (based on COT extremes + seasonality)
- **Setup**: Why the opportunity exists

### 3. Real-Time Tier Status
Each tier shows:
- **[WAIT]** - Waiting to start
- **[ACTIVE]** - Currently processing
- **[DONE]** - Completed

### 4. Uptime Tracking
- Shows how long system has been running
- Tracks total cycles executed
- Displays time until next cycle

---

## Intervals (Schedule)

### Default: 1 Hour
```bash
./START_MONITOR.sh --demo
```
- Checks market every hour
- Good for active monitoring
- Uses more API calls

### 6 Hours (Recommended)
```bash
./START_MONITOR.sh --demo --interval 6
```
- Checks 4 times per day
- Balances freshness vs API limits
- Good for swing trading

### 24 Hours (Daily)
```bash
./START_MONITOR.sh --demo --interval 24
```
- Once per day
- Minimal API usage
- Good for position trading

### Custom
```bash
# Every 12 hours
./START_MONITOR.sh --demo --interval 12

# Every 2 hours
./START_MONITOR.sh --demo --interval 2
```

---

## How It Works

### Cycle Flow

**1. Tier 1: COT Analysis** (5-10 seconds)
- Fetches latest CFTC.gov data
- Calculates COT Index
- Stores to database

**2. Tier 2: Seasonality** (2-3 seconds)
- Analyzes time-of-year patterns
- Identifies seasonal strength

**3. Tier 3: Confluence** (1-2 seconds)
- Combines COT + Seasonality
- Calculates confidence scores

**4. Tier 4: Trade Sheets** (1-2 seconds)
- Generates opportunities (if found)
- Updates trade sheet file
- **Dashboard displays it automatically**

**Total cycle time**: ~10-15 seconds

**Then waits** until next interval (1 hour, 6 hours, etc.)

### Trade Sheet Integration

When Tier 4 completes:
1. Writes `output/latest_trade_sheet.txt`
2. TUI automatically loads it
3. Parses opportunities
4. Displays in dashboard

**You see results immediately** - no need to open separate files!

---

## When Trade Opportunities Appear

### Currently (Week 1)
```
Trade Opportunities (0)

Waiting for trade opportunities...

CFTC data updates weekly (Fridays 3:30 PM ET)
System needs 26 weeks of data for extremes

Last check: 19:15:30
```

**Why no opportunities?**
- Only 1 week of CFTC data (need 26 for extremes)
- COT Index is neutral (50.0)
- No extreme positioning detected

### After 5-10 Weeks
```
Trade Opportunities (1)

Symbol | Direction | Confidence | Setup
GC     | LONG      | 72%        | Commercial net short + Dec seasonality
```

**First opportunities start appearing** as historical range builds.

### After 26+ Weeks (Full Operation)
```
Trade Opportunities (5)

Symbol | Direction | Confidence | Setup
GC     | LONG      | 95%        | Commercial net short extreme
SI     | LONG      | 88%        | Commercial covering + Q4 rally
CL     | SHORT     | 82%        | Commercial net long extreme
EUR    | LONG      | 76%        | Commercial accumulation
ZC     | SHORT     | 71%        | Commercial distribution
```

**System fully operational** - multiple high-confidence setups weekly.

---

## Stopping the Monitor

### Clean Stop
Press `Ctrl+C` once:
```
Monitoring stopped by user

======================================================================
Monitoring Complete - Ran 12 cycles
======================================================================
```

### Force Kill (if frozen)
Press `Ctrl+C` twice or use:
```bash
pkill -f run_cot_monitor_tui
```

---

## Running in Background

### Option 1: tmux (Recommended)
```bash
# Start in tmux
tmux new -s cot-monitor

# Run monitor
./START_MONITOR.sh --demo --interval 6

# Detach: Ctrl+B, then D

# Re-attach later
tmux attach -t cot-monitor
```

### Option 2: nohup
```bash
# Run in background
nohup ./START_MONITOR.sh --demo --interval 6 > monitor.log 2>&1 &

# Check if running
ps aux | grep run_cot_monitor

# Stop
pkill -f run_cot_monitor
```

### Option 3: systemd Service (Advanced)
```bash
# Create service file
sudo cp agents/spartan-agents.service /etc/systemd/system/

# Start service
sudo systemctl start spartan-agents

# Check status
sudo systemctl status spartan-agents

# Auto-start on boot
sudo systemctl enable spartan-agents
```

---

## API Key Usage

The system uses these APIs:

### CFTC.gov (Free, Public)
- **Usage**: Once per cycle
- **Rate limit**: ~2 requests/second (we use 1 every 2 seconds)
- **Data**: COT reports (updated weekly)

### yfinance (Free, Public)
- **Usage**: For seasonality backtesting (optional)
- **Rate limit**: ~2000 requests/hour
- **Data**: Historical price data

### FRED (Free, requires key)
- **Usage**: Economic data (optional)
- **Rate limit**: 120 requests/minute
- **Key**: Set `FRED_API_KEY` in `.env`

### Alpha Vantage (Free tier)
- **Usage**: Real-time quotes (optional)
- **Rate limit**: 5 requests/minute (free tier)
- **Key**: Set `ALPHA_VANTAGE_KEY` in `.env`

**Current system uses**: CFTC.gov only (no key needed)

**To add others**: Set keys in `.env` file

---

## Comparison: Monitor vs Single-Run

### Single-Run TUI (`./START_LIVE_TUI.sh --demo`)
- ❌ Runs once and exits
- ❌ No continuous monitoring
- ✅ Quick check
- ✅ Good for testing

### Persistent Monitor (`./START_MONITOR.sh --demo`)
- ✅ Runs forever
- ✅ Continuous market analysis
- ✅ Trade sheet inline
- ✅ Tracks uptime and cycles
- ✅ Good for production

---

## Troubleshooting

### Monitor exits immediately
**Cause**: Python error or missing dependencies

**Fix**:
```bash
# Check logs
tail -f logs/agents.log

# Verify dependencies
pip install rich psycopg2-binary requests
```

### No trade opportunities after many cycles
**Normal if**:
- Less than 26 weeks of data accumulated
- No extreme COT positioning currently
- Markets are in neutral range

**Check**:
```bash
# How much data do we have?
psql -d spartan_research_db -c "SELECT COUNT(DISTINCT report_date) AS weeks FROM cot_raw_data WHERE symbol = 'GC';"

# If less than 26, keep accumulating weekly data
```

### High CPU usage
**Cause**: Refresh rate too high

**Fix**: Lower refresh in `run_cot_monitor_tui.py`:
```python
refresh_per_second=2  # Change to 1 or 0.5
```

### Trade sheet not updating
**Check**:
```bash
# Does file exist?
ls -lh output/latest_trade_sheet.txt

# Check permissions
chmod 644 output/latest_trade_sheet.txt

# Check if agents completed Tier 4
tail -f logs/agents.log | grep "TIER 4"
```

---

## Files

### Main Files
- `run_cot_monitor_tui.py` - Persistent monitor TUI
- `START_MONITOR.sh` - Launcher script
- `PERSISTENT_MONITOR_GUIDE.md` - This guide

### Output Files
- `output/latest_trade_sheet.txt` - Trade opportunities
- `logs/agents.log` - Detailed execution logs

### Configuration
- `.env` - API keys (optional)
- `run_100_agents.py` - Agent orchestrator

---

## Quick Reference

```bash
# Start monitor (demo, 1 hour)
./START_MONITOR.sh --demo

# Start monitor (demo, 6 hours)
./START_MONITOR.sh --demo --interval 6

# Start monitor (production, 1 hour)
./START_MONITOR.sh

# Run in background (tmux)
tmux new -s cot
./START_MONITOR.sh --demo --interval 6
# Ctrl+B, D to detach

# Stop monitor
Ctrl+C

# Check logs
tail -f logs/agents.log

# View trade sheet
cat output/latest_trade_sheet.txt
```

---

## Summary

**What you have**:
- ✅ Continuous market monitoring
- ✅ Trade sheet integrated in dashboard
- ✅ Runs forever (until you stop it)
- ✅ Real CFTC data only
- ✅ Customizable intervals
- ✅ Uptime and cycle tracking

**How to use**:
1. Run `./START_MONITOR.sh --demo --interval 6`
2. Watch it analyze markets every 6 hours
3. Trade opportunities appear in dashboard
4. Press Ctrl+C to stop

**Next steps**:
- Run for 26 weeks to build full historical range
- Adjust interval based on your trading style
- Set up background service for 24/7 monitoring

---

**Created**: November 29, 2025
**Status**: ✅ Ready for continuous monitoring
**Data**: REAL CFTC.gov only - NO FAKE DATA

*Your markets. Monitored. Continuously.* ⚔️
