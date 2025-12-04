# Emergency Bypass Mode

## Overview

The **Emergency Bypass Mode** allows the Spartan Research Station website to start even when data validation fails (0% success rate). This is a **temporary workaround** to unblock website startup during API/data source outages.

---

## ⚠️ WARNING

**This mode should ONLY be used temporarily!**

- Website will start with **NO DATA** or **PARTIAL DATA**
- Dashboards may show empty charts/tables
- Users will see "No data available" errors
- **FIX THE ROOT CAUSE IMMEDIATELY** after enabling

---

## When to Use

Use bypass mode only in these scenarios:

1. ✅ **Yahoo Finance is down** - yfinance API temporarily unavailable
2. ✅ **Rate limiting issues** - Too many requests blocking data fetch
3. ✅ **API outages** - FRED, Alpha Vantage, or other sources down
4. ✅ **Network issues** - Temporary connectivity problems
5. ✅ **Emergency demo** - Need to show website UI urgently

**DO NOT use for**:

- ❌ Production deployments (fix data sources first!)
- ❌ Long-term operation (degrades user experience)
- ❌ Avoiding configuration work (configure API keys properly)

---

## How to Activate

### Option 1: Environment Variable (Recommended)

Add to your `.env` file:

```bash
SKIP_DATA_VALIDATION=true
```

Then restart:

```bash
docker-compose down
docker-compose up -d
```

### Option 2: Command Line Override

```bash
SKIP_DATA_VALIDATION=true docker-compose up -d
```

### Option 3: Docker Compose Override

Create `docker-compose.override.yml`:

```yaml
services:
  spartan-data-preloader:
    environment:
      - SKIP_DATA_VALIDATION=true
```

Then start normally:

```bash
docker-compose up -d
```

---

## How It Works

### Normal Operation (Bypass Disabled)

```
Data Preloader
  ↓
Fetch 13+ data sources (yfinance, FRED, etc.)
  ↓
Validate: Need 80%+ success + critical sources OK
  ↓
  ├─ ✅ PASS → Website starts (exit code 0)
  └─ ❌ FAIL → Website BLOCKED (exit code 1)
```

### Emergency Mode (Bypass Enabled)

```
Data Preloader
  ↓
Fetch 13+ data sources (yfinance, FRED, etc.)
  ↓
Check SKIP_DATA_VALIDATION=true
  ↓
  ✅ BYPASS → Force validation pass (exit code 0)
  ↓
Website starts (even with 0% data success)
  ⚠️  Logs show prominent warnings
```

---

## What You'll See

### Log Output (Bypass Active)

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

### Website Behavior

- ✅ Website **WILL START** on port 8888
- ✅ UI navigation **WILL WORK**
- ⚠️  Charts/tables **MAY BE EMPTY**
- ⚠️  "No data available" errors **LIKELY**
- ⚠️  Real-time updates **MAY FAIL**

---

## Deactivation (Critical!)

**After fixing data sources**, disable bypass mode:

### Step 1: Remove Environment Variable

Edit `.env` file:

```bash
# Change from:
SKIP_DATA_VALIDATION=true

# To:
SKIP_DATA_VALIDATION=false
# Or delete the line entirely (defaults to false)
```

### Step 2: Restart Services

```bash
docker-compose down
docker-compose up -d
```

### Step 3: Verify Normal Operation

Check preloader logs:

```bash
docker-compose logs spartan-data-preloader
```

Should see:

```
✅ Data validation PASSED - Website ready to start
```

**NOT**:

```
🚨 EMERGENCY BYPASS MODE ACTIVE 🚨
```

---

## Troubleshooting

### Issue: Website still won't start with bypass enabled

**Solution**: Check if environment variable is being passed:

```bash
docker exec spartan-data-preloader env | grep SKIP_DATA_VALIDATION
```

Should show:

```
SKIP_DATA_VALIDATION=true
```

If not visible:

1. Ensure `.env` file is in website root directory
2. Rebuild container: `docker-compose build spartan-data-preloader`
3. Restart: `docker-compose up -d`

### Issue: Bypass mode won't disable

**Solution**: Ensure you're setting to `false`, not removing:

```bash
# Correct (explicitly false)
SKIP_DATA_VALIDATION=false

# Also correct (defaults to false if not set)
# SKIP_DATA_VALIDATION=true  ← commented out

# WRONG (will stay enabled!)
SKIP_DATA_VALIDATION=  ← empty value
```

### Issue: Data still failing after fixing sources

**Symptoms**:

- Bypass disabled
- Data sources fixed
- Still getting validation failures

**Solution**: Check individual source logs:

```bash
docker-compose logs spartan-data-preloader | grep "❌"
```

Identify which sources are still failing:

```bash
docker-compose logs spartan-data-preloader | grep "Failed Sources:"
```

Common fixes:

1. **yfinance rate limiting**:
   - Wait 5-10 minutes between retries
   - Check Yahoo Finance status: https://status.yahoo.com/

2. **FRED API key**:
   - Verify key is 32 characters
   - Check key validity: https://fred.stlouisfed.org/docs/api/api_key.html

3. **Network issues**:
   - Test connectivity: `docker exec spartan-data-preloader ping -c 3 query1.finance.yahoo.com`
   - Check firewall/proxy settings

---

## Testing Bypass Mode

Run the test script to verify bypass mode works:

```bash
cd /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website
python3 test_bypass_mode.py
```

Expected output:

```
======================================================================
🎉 ALL TESTS PASSED!
======================================================================

Bypass mode implementation is working correctly.
```

---

## Technical Implementation

### Modified Files

1. **src/data_preloader.py**
   - Added bypass check in `validate_data_availability()`
   - Forces `is_valid = True` when `SKIP_DATA_VALIDATION=true`
   - Adds `bypass_mode` flag to validation report

2. **docker-compose.yml**
   - Added `SKIP_DATA_VALIDATION` environment variable
   - Defaults to `false` (normal operation)

3. **.env.example**
   - Documented `SKIP_DATA_VALIDATION` variable
   - Added usage warnings

### Code Logic

```python
# Check for bypass mode
skip_validation = os.getenv('SKIP_DATA_VALIDATION', 'false').lower() == 'true'

if skip_validation:
    # Log prominent warnings
    logger.warning("🚨 EMERGENCY BYPASS MODE ACTIVE 🚨")

    # Force validation to pass
    is_valid = True
    validation_report['bypass_mode'] = True

    # Exit code 0 (success) → website starts
    sys.exit(0)
```

---

## FAQ

### Q: Will the website have ANY data with bypass enabled?

**A**: Depends on which sources succeeded. Check preloader logs:

```bash
docker-compose logs spartan-data-preloader | grep "✅"
```

Even 1-2 successful sources will provide **some** data.

### Q: Can I use this in production?

**A**: **NO!** This is emergency-only. Users will see broken dashboards.

### Q: How long should bypass mode be active?

**A**: **Minutes to hours**, not days. Fix data sources immediately.

### Q: What if I forget to disable it?

**A**: Website will continue running with stale/no data. Users will complain about missing data. **Set a reminder to disable within 24 hours!**

### Q: Is there a safer alternative?

**A**: Yes! Fix the root cause instead:

1. **Wait for API to recover** (if temporary outage)
2. **Add API keys** (FRED, Alpha Vantage, Polygon.io)
3. **Implement caching** (serve stale data temporarily)
4. **Use backup data sources** (multiple providers)

---

## Best Practices

1. ✅ **Document why enabled**: Add comment in `.env` file

   ```bash
   # EMERGENCY: yfinance down 2025-11-20, bypass enabled temporarily
   SKIP_DATA_VALIDATION=true
   ```

2. ✅ **Set reminder**: Disable within 24 hours

   ```bash
   # Set calendar reminder to disable bypass mode
   echo "Disable SKIP_DATA_VALIDATION" | at now + 24 hours
   ```

3. ✅ **Monitor logs**: Check what data **is** available

   ```bash
   docker-compose logs -f spartan-data-preloader
   ```

4. ✅ **Communicate to users**: Inform them of limited data availability

5. ✅ **Fix root cause**: Don't rely on bypass long-term

---

## Related Documentation

- **DATA_PRELOADER_GUIDE.md** - Full preloader documentation
- **NO_API_KEY_START.md** - Starting with zero API keys
- **FREE_DATA_SOURCES.md** - Alternative data sources

---

**Last Updated**: November 20, 2025
**Status**: Tested and verified working
**Emergency Contact**: Check logs first, then fix data sources!
