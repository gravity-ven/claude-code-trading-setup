# Emergency Bypass Mode - Real-World Usage Example

## Scenario: Yahoo Finance API Down

**Date**: November 20, 2025 (example)

**Problem**: Yahoo Finance API is experiencing outages. The data preloader is failing with 0% success rate, blocking website startup.

**Error Logs**:
```
❌ US_Indices: Failed
❌ Global_Indices: Failed
❌ Gold: Failed
...
Success Rate: 0.0%
❌ Data validation FAILED - Website should NOT start
❌ DATA PRELOAD FAILED - DO NOT START WEBSITE
```

**Impact**: Website won't start. Docker dependency chain blocks `spartan-web` container.

---

## Step-by-Step Solution

### Step 1: Verify the Issue

```bash
# Check preloader logs
docker-compose logs spartan-data-preloader

# Look for validation failure
docker-compose logs spartan-data-preloader | grep "validation FAILED"

# Check which sources failed
docker-compose logs spartan-data-preloader | grep "❌"
```

**Output**:
```
❌ US_Indices: JSON decode error (attempt 3/3)
❌ Global_Indices: JSON decode error (attempt 3/3)
❌ Data validation FAILED - Website should NOT start
💡 HINT: Set SKIP_DATA_VALIDATION=true to bypass (emergency only)
```

**Diagnosis**: All yfinance sources failing → likely Yahoo Finance API issue.

---

### Step 2: Activate Bypass Mode

```bash
# Navigate to project directory
cd /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website

# Edit .env file
nano .env

# Add this line:
SKIP_DATA_VALIDATION=true

# Add a comment explaining why (optional but recommended)
# EMERGENCY: Yahoo Finance API down 2025-11-20 14:30 UTC
# Bypass enabled temporarily to unblock website startup
# TODO: Disable after Yahoo Finance recovers
SKIP_DATA_VALIDATION=true

# Save and exit (Ctrl+X, Y, Enter)
```

**Alternative (command line)**:
```bash
echo "SKIP_DATA_VALIDATION=true" >> .env
```

---

### Step 3: Restart Services

```bash
# Stop all services
docker-compose down

# Start services (preloader will now bypass validation)
docker-compose up -d

# Watch logs to confirm bypass activated
docker-compose logs -f spartan-data-preloader
```

**Expected Output**:
```
======================================================================
🚨 EMERGENCY BYPASS MODE ACTIVE 🚨
======================================================================
Data validation is DISABLED via SKIP_DATA_VALIDATION=true
Website will start regardless of data availability
This is a TEMPORARY workaround - fix data sources ASAP!
======================================================================
⚠️  WARNING: 0% data success rate - website will have NO DATA!
✅ Validation BYPASSED - Website will start (with warnings)
```

---

### Step 4: Verify Website Started

```bash
# Check if website is running
curl http://localhost:8888/health

# Check Docker containers
docker-compose ps
```

**Expected Output**:
```
NAME                           STATUS
spartan-postgres               Up (healthy)
spartan-redis                  Up (healthy)
spartan-data-preloader         Exited (0)  ← Exit code 0 = success!
spartan-research-station       Up (healthy)
```

Website is now accessible at http://localhost:8888

---

### Step 5: Set Reminder to Disable Bypass

```bash
# Set calendar reminder for 4 hours from now
echo "Check if Yahoo Finance is back up, disable SKIP_DATA_VALIDATION" | at now + 4 hours

# Or create a reminder file
echo "REMINDER: Disable SKIP_DATA_VALIDATION after Yahoo Finance recovers" > DISABLE_BYPASS_REMINDER.txt
```

---

### Step 6: Monitor Yahoo Finance Status

```bash
# Check Yahoo Finance status page
curl -s https://status.yahoo.com/ | grep -i "degraded\|outage\|issue"

# Test yfinance manually
python3 -c "import yfinance as yf; print(yf.Ticker('SPY').history(period='1d'))"

# If successful:
#                  Open   High    Low  Close      Volume
# Date
# 2025-11-20  450.2  451.5  449.8  450.9  95000000
```

---

### Step 7: Disable Bypass Mode (After Fix)

```bash
# Edit .env file
nano .env

# Change:
SKIP_DATA_VALIDATION=true

# To:
SKIP_DATA_VALIDATION=false

# Or delete the line entirely (defaults to false)

# Save and exit
```

---

### Step 8: Restart with Normal Validation

```bash
# Stop services
docker-compose down

# Start services (validation re-enabled)
docker-compose up -d

# Check preloader logs
docker-compose logs spartan-data-preloader
```

**Expected Output**:
```
✅ US_Indices: Success
✅ Global_Indices: Success
✅ Gold: Success
...
Success Rate: 100.0%
✅ Data validation PASSED - Website ready to start
✅ DATA PRELOAD COMPLETE - READY TO START WEBSITE
```

---

### Step 9: Verify Normal Operation

```bash
# Check website health
curl http://localhost:8888/health

# Check data availability
curl http://localhost:8888/health/data

# Verify dashboards have data
curl -s http://localhost:8888 | grep "No data available"
# (Should return nothing if data loaded successfully)
```

---

## Alternative Scenario: Need Website NOW

**Situation**: Demo in 5 minutes, website won't start, no time to troubleshoot.

**Quick Activation**:

```bash
# One-line activation
echo "SKIP_DATA_VALIDATION=true" >> .env && docker-compose down && docker-compose up -d

# Wait 30 seconds
sleep 30

# Check website
curl http://localhost:8888
```

**Result**: Website starts immediately (even with no data).

**Warning**: Dashboards may show "No data available" - inform demo audience.

**After Demo**: Disable bypass IMMEDIATELY!

```bash
sed -i 's/SKIP_DATA_VALIDATION=true/SKIP_DATA_VALIDATION=false/' .env
docker-compose restart
```

---

## Troubleshooting Real Issues

### Issue 1: Bypass mode not activating

**Symptoms**:
```
❌ Data validation FAILED - Website should NOT start
```

(No bypass warning shown)

**Solution**:

```bash
# Check if environment variable is set
docker exec spartan-data-preloader env | grep SKIP_DATA_VALIDATION

# If not shown or shows "false":
# 1. Verify .env file has the variable
cat .env | grep SKIP_DATA_VALIDATION

# 2. Rebuild container
docker-compose build spartan-data-preloader

# 3. Restart
docker-compose up -d spartan-data-preloader
```

---

### Issue 2: Website still shows "No data available"

**Symptoms**: Website starts, but all dashboards empty.

**This is EXPECTED behavior** when bypass is active!

**Check what data IS available**:

```bash
# See successful sources
docker-compose logs spartan-data-preloader | grep "✅"

# Check Redis cache
docker exec -it spartan-redis redis-cli
> KEYS market:*
> GET market:index:SPY

# Check PostgreSQL
docker exec -it spartan-postgres psql -U spartan -d spartan_research_db
> SELECT COUNT(*) FROM preloaded_market_data;
```

**Solutions**:

1. **Some data available**: Check specific dashboards (some may work)
2. **Zero data**: Wait for API to recover, then disable bypass
3. **Emergency**: Use cached/stale data from previous runs (if available)

---

### Issue 3: Can't disable bypass mode

**Symptoms**: Set `SKIP_DATA_VALIDATION=false`, but bypass still active.

**Common mistakes**:

```bash
# WRONG: Empty value
SKIP_DATA_VALIDATION=

# WRONG: Commented out incorrectly
#SKIP_DATA_VALIDATION=true  ← Still reads as "true"!

# CORRECT: Explicit false
SKIP_DATA_VALIDATION=false

# ALSO CORRECT: Delete line entirely (defaults to false)
```

**Solution**:

```bash
# Method 1: Set explicitly to false
sed -i 's/SKIP_DATA_VALIDATION=.*/SKIP_DATA_VALIDATION=false/' .env

# Method 2: Delete the line
sed -i '/SKIP_DATA_VALIDATION/d' .env

# Then restart
docker-compose restart spartan-data-preloader
```

---

## Real-World Timing

### Typical Outage Resolution

```
14:00 - Yahoo Finance API starts failing
14:05 - Website won't start (validation fails)
14:10 - Activate bypass mode
14:15 - Website running (no data)
14:30 - Yahoo Finance recovers
14:35 - Disable bypass mode
14:40 - Website running (full data)
```

**Total bypass duration**: 30 minutes

---

## Best Practices Summary

1. ✅ **Document why** - Add comment to .env explaining reason
2. ✅ **Set reminder** - Disable within 4-24 hours max
3. ✅ **Monitor status** - Check API status pages regularly
4. ✅ **Test after fix** - Verify data loading before disabling bypass
5. ✅ **Communicate** - Inform users of limited data (if public-facing)

---

## When NOT to Use

❌ **Don't use for**:
- "I don't want to configure API keys"
  → **Solution**: Configure FRED API key (2 minutes, free)

- "Website too slow to start"
  → **Solution**: Optimize data preloader, not bypass validation

- "Production deployment without testing"
  → **Solution**: Test data sources in staging first

- "Permanent solution"
  → **Solution**: Implement multi-source fallbacks, caching

---

## Emergency Contact Card

```
╔══════════════════════════════════════════════════════════════════╗
║                    EMERGENCY BYPASS MODE                         ║
║                      QUICK COMMANDS                              ║
╚══════════════════════════════════════════════════════════════════╝

ACTIVATE:
  echo "SKIP_DATA_VALIDATION=true" >> .env
  docker-compose restart

DEACTIVATE:
  sed -i 's/SKIP_DATA_VALIDATION=true/SKIP_DATA_VALIDATION=false/' .env
  docker-compose restart

CHECK STATUS:
  docker-compose logs spartan-data-preloader | grep "BYPASS"

VERIFY DATA:
  docker-compose logs spartan-data-preloader | grep "Success Rate"

TEST YFINANCE:
  python3 -c "import yfinance as yf; print(yf.Ticker('SPY').info)"

FULL DOCS:
  cat EMERGENCY_BYPASS_MODE.md
```

---

**Remember**: This is an emergency tool. Use sparingly, disable quickly!
