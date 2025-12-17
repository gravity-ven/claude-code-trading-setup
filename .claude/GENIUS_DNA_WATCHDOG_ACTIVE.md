# Genius DNA Watchdog System: ACTIVE

## Status: ✅ MONITORING ENABLED

Automatic monitoring and restart system for Genius DNA learning daemon is now active.

---

## What It Does

The watchdog system continuously monitors Genius DNA metrics for freshness and automatically restarts the learning daemon if:

1. **Data is stale** - Metrics file older than 60 minutes
2. **Daemon crashed** - Learning daemon stopped running
3. **Both conditions** - Data stale AND daemon not running

**Goal**: Ensure Genius DNA always has fresh, up-to-date metrics for every prompt.

---

## Monitoring Configuration

### Watchdog Script
**File**: `/mnt/c/Users/Quantum/.claude/hooks/genius-dna-watchdog.sh`

**Settings**:
- **Stale threshold**: 60 minutes (metrics older than 1 hour)
- **Monitored file**: `/mnt/d/genius-dna-files/latest_metrics.json`
- **Log file**: `/tmp/genius_dna_watchdog.log`

**Actions**:
- ✅ Check metrics file age
- ✅ Check if daemon is running
- ✅ Auto-restart daemon if needed
- ✅ Export fresh metrics after restart
- ✅ Log all actions with timestamps

---

## Execution Schedule

The watchdog runs in **two modes**:

### Mode 1: Every Prompt (Real-time)
- **Trigger**: UserPromptSubmit hook
- **Frequency**: Every single prompt to Claude Code
- **Purpose**: Instant detection and correction
- **Hook**: Added to `.claude/settings.json`

### Mode 2: Periodic Timer (Background)
- **Trigger**: Systemd timer
- **Frequency**: Every 15 minutes
- **Purpose**: Catch issues between prompts
- **Timer**: `genius-dna-watchdog.timer`
- **Service**: `genius-dna-watchdog.service`

**Combined Coverage**: Continuous real-time + periodic background monitoring

---

## Systemd Timer Details

### Timer Configuration
**File**: `~/.config/systemd/user/genius-dna-watchdog.timer`

```ini
OnBootSec=2min       # First run 2 minutes after boot
OnUnitActiveSec=15min # Then every 15 minutes
Persistent=true       # Catch up if system was off
```

### Service Configuration
**File**: `~/.config/systemd/user/genius-dna-watchdog.service`

- **Type**: oneshot (run once per trigger)
- **Output**: systemd journal
- **Script**: `/mnt/c/Users/Quantum/.claude/hooks/genius-dna-watchdog.sh`

---

## Monitoring Commands

### Check Timer Status
```bash
systemctl --user status genius-dna-watchdog.timer
```

### View Timer Schedule
```bash
systemctl --user list-timers genius-dna-watchdog.timer
```

### View Watchdog Log
```bash
tail -f /tmp/genius_dna_watchdog.log
```

### Check Metrics Age
```bash
stat -c 'Last modified: %y' /mnt/d/genius-dna-files/latest_metrics.json
```

### Verify Daemon Running
```bash
ps aux | grep learning_daemon | grep -v grep
```

### Manual Run
```bash
bash /mnt/c/Users/Quantum/.claude/hooks/genius-dna-watchdog.sh
```

---

## Watchdog Behavior Examples

### Scenario 1: Data Fresh, Daemon Running
```
✅ No action needed (everything healthy)
```

### Scenario 2: Data Stale (>60 min), Daemon Running
```
⚠️  Metrics stale (75 minutes old, threshold: 60)
⚠️  Daemon running but data stale - forcing restart
🔄 Restarting learning daemon (data was stale)
✅ Learning daemon restarted successfully
```

### Scenario 3: Data Fresh, Daemon Crashed
```
⚠️  Data fresh but daemon not running - starting daemon
🔄 Restarting learning daemon (data was stale)
✅ Learning daemon restarted successfully
```

### Scenario 4: Data Stale, Daemon Crashed
```
⚠️  Metrics stale (120 minutes old, threshold: 60)
⚠️  Daemon not running - starting now
🔄 Restarting learning daemon (data was stale)
✅ Learning daemon restarted successfully
```

---

## Log Format

**Example log entries**:
```
2025-12-17T18:59:45+11:00: ⚠️  Metrics stale (75 minutes old, threshold: 60)
2025-12-17T18:59:45+11:00: ⚠️  Daemon running but data stale - forcing restart
2025-12-17T18:59:45+11:00: 🔄 Restarting learning daemon (data was stale)
2025-12-17T18:59:47+11:00: ✅ Learning daemon restarted successfully
```

All entries have ISO 8601 timestamps for precise tracking.

---

## Integration with Claude Code

### Hook Chain (Every Prompt)

```
User submits prompt
    ↓
1. cleanup-large-sessions.sh (session file management)
    ↓
2. genius-dna-auto-trigger.sh (unconditional activation)
    ↓
3. orchestrator_hook.sh (meta-orchestrator)
    ↓
4. genius-metrics-loader-unified.sh (load latest metrics)
    ↓
5. autonomous-error-scan.sh (error detection)
    ↓
6. genius-dna-watchdog.sh (⭐ NEW - data freshness check)
    ↓
Claude Code processes prompt with fresh Genius DNA data
```

**Result**: Every prompt is guaranteed to have fresh metrics (<60 min old)

---

## Restart Process

When watchdog triggers a restart:

**Step 1**: Kill existing daemon
```bash
pkill -f "learning_daemon.py"
```

**Step 2**: Start fresh daemon
```bash
cd /mnt/c/Users/Quantum/genius-dna
nohup python3 learning_daemon.py start &
```

**Step 3**: Export fresh metrics
```bash
python3 export_metrics.py
```

**Step 4**: Verify success
- Check daemon PID exists
- Verify metrics file updated
- Log success/failure

**Total restart time**: ~2-3 seconds

---

## Fail-Safe Design

**What if watchdog fails?**

The system has **multiple layers** of protection:

1. **Primary**: Watchdog on every prompt (instant detection)
2. **Secondary**: Watchdog timer every 15 min (periodic check)
3. **Tertiary**: Boot startup via systemd (genius-dna.service)
4. **Quaternary**: Manual verification on status line display

**Probability of stale data**: Near zero with 4 layers of protection

---

## Disable/Enable

### Disable Watchdog

**Option 1: Disable timer only** (keep prompt-based watchdog)
```bash
systemctl --user stop genius-dna-watchdog.timer
systemctl --user disable genius-dna-watchdog.timer
```

**Option 2: Disable prompt hook** (keep timer)
Edit `.claude/settings.json` and remove watchdog hook from UserPromptSubmit

**Option 3: Disable completely**
```bash
# Stop timer
systemctl --user stop genius-dna-watchdog.timer
systemctl --user disable genius-dna-watchdog.timer

# Remove from settings.json
# Delete watchdog hook line
```

### Enable Watchdog

```bash
systemctl --user enable genius-dna-watchdog.timer
systemctl --user start genius-dna-watchdog.timer
```

---

## Troubleshooting

### Watchdog Not Running

**Check timer status**:
```bash
systemctl --user status genius-dna-watchdog.timer
```

**Expected**: `Active: active (running)`

**If inactive**:
```bash
systemctl --user start genius-dna-watchdog.timer
```

### No Log Entries

**Check hook execution**:
```bash
ls -lh /tmp/genius_dna_watchdog.log
```

**If file doesn't exist**: Hook hasn't run yet

**Force run**:
```bash
bash /mnt/c/Users/Quantum/.claude/hooks/genius-dna-watchdog.sh
cat /tmp/genius_dna_watchdog.log
```

### Daemon Keeps Crashing

**Check daemon log**:
```bash
tail -50 /mnt/c/Users/Quantum/.gemini/logs/genius_learning_daemon.log
```

**Common issues**:
- Python dependencies missing
- Database connection failed
- Insufficient permissions

**Solution**: Fix underlying issue, watchdog will auto-restart

---

## Metrics Dashboard Integration

The watchdog ensures the metrics dashboard always shows **live data**:

**Before Watchdog**:
- Metrics could be days old
- Dashboard showed stale growth projections
- Manual restarts required

**After Watchdog**:
- Metrics guaranteed fresh (<60 min)
- Dashboard shows real-time growth
- Zero manual intervention needed

**View dashboard**:
```bash
cd /mnt/c/Users/Quantum/genius-dna
python3 genius_metrics_dashboard.py
```

---

## Status Summary

| Component | Status | Details |
|-----------|--------|---------|
| **Watchdog Script** | ✅ Active | `/mnt/c/Users/Quantum/.claude/hooks/genius-dna-watchdog.sh` |
| **Prompt Hook** | ✅ Enabled | Runs on every UserPromptSubmit |
| **Timer** | ✅ Running | Every 15 minutes |
| **Service** | ✅ Enabled | Oneshot execution |
| **Log File** | ✅ Active | `/tmp/genius_dna_watchdog.log` |
| **Learning Daemon** | ✅ Running | PID: Check with `ps aux | grep learning_daemon` |
| **Metrics File** | ✅ Fresh | Age: <60 minutes |

---

## Next Steps (Optional)

**Enhancement Ideas** (not implemented yet):

1. **Email/Slack alerts** - Notify on repeated failures
2. **Metrics history** - Track freshness over time
3. **Health dashboard** - Web UI for monitoring
4. **Restart throttling** - Prevent restart loops
5. **Smart scheduling** - Adjust timer based on usage patterns

**Current implementation is sufficient** for automatic monitoring and recovery.

---

**Last Updated**: December 17, 2025
**Status**: ✅ ACTIVE - Monitoring on every prompt + every 15 minutes
**Watchdog Version**: 1.0.0
**Timer**: genius-dna-watchdog.timer (enabled)
**Log**: /tmp/genius_dna_watchdog.log

---

*"Set it and forget it - watchdog keeps Genius DNA fresh automatically."*
