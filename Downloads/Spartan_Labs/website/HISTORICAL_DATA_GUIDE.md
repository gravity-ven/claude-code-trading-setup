# Historical COT Data Download Guide

## Why You Need This

The COT agents require **156 weeks (3 years)** of historical data to:
- Calculate meaningful COT Index (0-100 scale)
- Identify true market extremes
- Generate reliable buy/sell signals
- Detect divergences and patterns

**Without historical data:** System shows "Building data (Week 1/26)" and no signals
**With historical data:** System generates actionable trade recommendations

---

## Quick Start

```bash
# Download 156 weeks (3 years) of CFTC data
./DOWNLOAD_HISTORICAL_COT_DATA.sh
```

**Time:** 3-7 minutes (one-time)
**Data:** 156 weeks × 42+ markets = ~6,500 data points
**Storage:** PostgreSQL (permanent)

---

## What Gets Downloaded

### Markets Covered (42+)

**Indices (4):**
- ES (S&P 500), NQ (Nasdaq 100), YM (Dow Jones), RTY (Russell 2000)

**Currencies (7):**
- DX (US Dollar), EUR, JPY, GBP, AUD, CAD, CHF

**Metals (4):**
- GC (Gold), SI (Silver), HG (Copper), PL (Platinum)

**Energy (4):**
- CL (Crude Oil), NG (Natural Gas), HO (Heating Oil), RB (Gasoline)

**Grains (5):**
- ZC (Corn), ZS (Soybeans), ZW (Wheat), ZL (Soybean Oil), ZM (Soybean Meal)

**Softs (5):**
- SB (Sugar), KC (Coffee), CC (Cocoa), CT (Cotton), OJ (Orange Juice)

**Meats (3):**
- LE (Live Cattle), GF (Feeder Cattle), HE (Lean Hogs)

**Bonds (4):**
- ZN (10Y Treasury), ZB (30Y Treasury), ZF (5Y Treasury), ZT (2Y Treasury)

**Crypto Futures (2):**
- BTC (Bitcoin CME), ETH (Ethereum CME)

---

## How It Works

### Step 1: Download CFTC Files

The script downloads official CFTC data for:
- **2025** (current year)
- **2024** (last year)
- **2023** (2 years ago)

Source: `https://www.cftc.gov/files/dea/history/deacot[YEAR].zip`

### Step 2: Parse COT Reports

Each ZIP contains weekly reports with:
- Commercial trader positions (smart money)
- Long positions (bullish bets)
- Short positions (bearish bets)
- Net positions (overall bias)

### Step 3: Store in PostgreSQL

Data stored in `cot_raw_data` table:
```sql
INSERT INTO cot_raw_data (
    report_date,
    symbol,
    commercial_long,
    commercial_short,
    commercial_net,
    data_source
) VALUES (...);
```

Duplicate protection: `ON CONFLICT (report_date, symbol) DO UPDATE`

### Step 4: Verify Coverage

Script shows data coverage per symbol:
```
✅ GC     - 156 weeks (2022-12-09 to 2025-11-28)
✅ SI     - 156 weeks (2022-12-09 to 2025-11-28)
✅ BTC    - 156 weeks (2022-12-09 to 2025-11-28)
⚠️  ETH   - 52 weeks (2024-01-05 to 2025-11-28)
```

---

## After Download

### COT Index Calculation

With 156 weeks of data, the system can calculate:

```
COT Index = ((Current_Net - Min_Net_156_weeks) / (Max_Net_156_weeks - Min_Net_156_weeks)) × 100
```

**Example (Gold):**
```
Current Net: -61,457 contracts
156-Week Low: -150,000 contracts
156-Week High: +50,000 contracts

COT Index = ((-61,457 - (-150,000)) / (50,000 - (-150,000))) × 100
          = (88,543 / 200,000) × 100
          = 44.3

Interpretation: Neutral (between 25-75)
```

### Signal Generation

**Buy Signals (COT Index > 75):**
- Commercials heavily long
- Institutional accumulation
- Expect upward price movement

**Sell Signals (COT Index < 25):**
- Commercials heavily short
- Institutional distribution
- Expect downward price movement

**Neutral (25-75):**
- No extreme positioning
- Wait for clear setup

---

## Data Retention Policy

### Permanent Storage

**Historical data is NEVER deleted:**
- ✅ All 156 weeks stored permanently
- ✅ Agents add new weekly data (every Friday)
- ✅ Database grows over time (more data = better analysis)
- ✅ No auto-delete triggers

### Weekly Updates

Agents automatically:
1. Fetch new CFTC data every Friday 3:30 PM ET
2. Add to historical database
3. Recalculate COT Index with updated extremes
4. Generate fresh trade signals

**You download historical data ONCE, agents maintain it forever.**

---

## Verification

### Check Data Coverage

```bash
# Show data coverage per symbol
psql -d spartan_research_db -c "
SELECT
    symbol,
    COUNT(*) as weeks,
    MIN(report_date) as earliest,
    MAX(report_date) as latest
FROM cot_raw_data
GROUP BY symbol
ORDER BY weeks DESC;
"
```

### Check Latest Data

```bash
# Show most recent COT data
psql -d spartan_research_db -c "
SELECT
    symbol,
    report_date,
    commercial_net
FROM cot_raw_data
WHERE report_date = (SELECT MAX(report_date) FROM cot_raw_data)
ORDER BY symbol;
"
```

### Check Total Records

```bash
# Count total historical records
psql -d spartan_research_db -c "
SELECT
    COUNT(*) as total_records,
    COUNT(DISTINCT symbol) as symbols,
    COUNT(DISTINCT report_date) as weeks,
    MIN(report_date) as earliest,
    MAX(report_date) as latest
FROM cot_raw_data;
"
```

Expected output (after download):
```
total_records | symbols | weeks | earliest   | latest
--------------+---------+-------+------------+------------
     6,500+   |   42    |  156  | 2022-12-09 | 2025-11-28
```

---

## Troubleshooting

### "File not found for [YEAR]"

**Cause:** CFTC hasn't published 2025 data yet (early in year)

**Solution:** Script auto-skips missing years, downloads what's available

### "Database connection failed"

**Cause:** PostgreSQL not running

**Solution:**
```bash
# Start PostgreSQL
sudo service postgresql start

# Verify
psql -d spartan_research_db -c "SELECT version();"
```

### "No data for symbol X"

**Cause:** CFTC doesn't track that market or uses different code

**Solution:** Only markets in `symbols` dict are tracked (see list above)

### Download Interrupted

**Cause:** Network error or timeout

**Solution:** Re-run script - it skips duplicates automatically
```bash
./DOWNLOAD_HISTORICAL_COT_DATA.sh
```

---

## Expected Output

```
╔══════════════════════════════════════════════════════════════════╗
║         SPARTAN COT AGENTS - Historical Data Download           ║
╚══════════════════════════════════════════════════════════════════╝

This will download 156 weeks (3 years) of CFTC COT data for 42+ markets.

⏱️  Estimated time: 3-7 minutes
📊 Data source: CFTC.gov (official government data)
🎯 Purpose: Enable COT Index calculation and trade signals
💾 Storage: PostgreSQL (spartan_research_db)

Press Enter to start download...

======================================================================
HISTORICAL COT DATA DOWNLOAD
======================================================================
Target: 156 weeks of data (3.0 years)
Markets: 38 symbols
======================================================================

Downloading data for years: [2025, 2024, 2023]

Processing 2025...
Downloading CFTC data for 2025...
URL: https://www.cftc.gov/files/dea/history/deacot2025.zip
✅ Downloaded 2,456,789 bytes for 2025
Parsing f_disagg.txt...
✅ Parsed 2,150 COT records
✅ Stored 2,150 COT records to database

Processing 2024...
Downloading CFTC data for 2024...
✅ Downloaded 12,345,678 bytes for 2024
✅ Parsed 2,200 COT records
✅ Stored 2,200 COT records to database

Processing 2023...
Downloading CFTC data for 2023...
✅ Downloaded 11,987,654 bytes for 2023
✅ Parsed 2,180 COT records
✅ Stored 2,180 COT records to database

======================================================================
✅ DOWNLOAD COMPLETE - 6,530 total records stored
======================================================================

DATA COVERAGE SUMMARY
======================================================================
✅ GC     - 156 weeks (2022-12-09 to 2025-11-28)
✅ SI     - 156 weeks (2022-12-09 to 2025-11-28)
✅ CL     - 156 weeks (2022-12-09 to 2025-11-28)
✅ BTC    - 156 weeks (2022-12-09 to 2025-11-28)
✅ ETH    - 156 weeks (2022-12-09 to 2025-11-28)
... (all symbols shown)
======================================================================
Total symbols: 38
Ready for COT Index (26+ weeks): 38
Still building: 0
✅ SYSTEM READY - Sufficient historical data for analysis
```

---

## Next Steps

### 1. Run Agents

```bash
# Launch TUI with trade signals
./START_TUI_WITH_TRADES.sh
```

### 2. View Trade Signals

You should now see actual recommendations:

```
BUY RECOMMENDATIONS

1. GC (Gold) - Confidence: 85%

   WHAT TO DO:
      BUY Gold futures for upward move

   WHY THIS OPPORTUNITY:
      * Commercial traders (smart money) heavily long
        COT Index: 85.2/100 (bullish)
      * When institutions accumulate, prices rise

   RISK LEVEL:
      LOW - Strong institutional signal
```

### 3. Daily Monitoring

```bash
# Auto-runs every 24 hours
./SIMPLE_DAILY_MONITOR.sh
```

---

## Summary

✅ **One-time setup:** Download 156 weeks of historical data
✅ **Permanent storage:** Data retained forever in PostgreSQL
✅ **Auto-maintained:** Agents add new data weekly
✅ **Ready for signals:** COT Index calculation enabled
✅ **Real data only:** NO FAKE DATA - CFTC.gov official reports

**Run once:**
```bash
./DOWNLOAD_HISTORICAL_COT_DATA.sh
```

**Then enjoy automated trade signals forever.**

---

**Created:** November 29, 2025
**Data Range:** 156 weeks (3 years)
**Markets:** 42+ (indices, forex, commodities, bonds, crypto)
**Source:** CFTC.gov (U.S. Government)
**Status:** ✅ Ready to Use
