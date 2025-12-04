# When Does It Refresh? - Quick Reference

## Data Update Schedule

### CFTC Data (Source of Truth)
```
WHEN:     Every Friday at 3:30 PM Eastern Time
REFLECTS: Tuesday's market positions (3-day lag is normal)
WHAT:     Professional traders' positions (commercial traders)
```

**This is the REAL data that drives everything.**

### Your Daily Monitor
```
WHEN:     Every 24 hours (once per day)
WHAT:     Checks for new CFTC data and analyzes markets
OUTPUT:   Updated trade sheet with recommendations
```

---

## Simple Timeline

### Monday - Thursday
- **CFTC**: No new data (waiting for Friday)
- **Your Monitor**: Runs daily, uses last Friday's data
- **Action**: Review existing recommendations, plan ahead

### Friday (Most Important Day)
- **3:30 PM ET**: CFTC releases new COT data
- **After 3:30 PM**: Your monitor picks up fresh data
- **Evening**: New trade recommendations generated
- **Action**: CHECK FOR NEW OPPORTUNITIES

### Saturday
- **Morning**: Review Friday's new recommendations
- **Action**: Plan your week's trades

### Sunday
- **Evening**: Final review before markets open Monday
- **Action**: Prepare orders

---

## When to Check Results

### Best Times:
1. **Friday evenings** (after 3:30 PM ET)
   - Fresh CFTC data just released
   - New opportunities appear
   - Best time to discover new setups

2. **Saturday mornings**
   - Review weekly opportunities
   - Research recommended symbols
   - Plan position sizes

3. **Sunday evenings**
   - Final check before markets open
   - Prepare buy/sell orders
   - Set alerts

### Don't Bother Checking:
- **Monday-Thursday**: Data doesn't change
- **Before Friday 3:30 PM**: Waiting for new data
- **Multiple times per day**: Waste of time (data only updates weekly)

---

## What Each Check Shows

### Week 1-4 (Building Phase)
```
Report shows:
  "NO HIGH-CONFIDENCE INVESTMENT OPPORTUNITIES AT THIS TIME"

Why:
  - System is accumulating historical data
  - Need 26 weeks for full analysis
  - This is NORMAL - be patient
```

### Week 5-10 (First Signals)
```
Report shows:
  "FOUND 1-2 INVESTMENT OPPORTUNITIES"

  BUY RECOMMENDATIONS:
  1. GC (Gold) - Confidence: 72%
     WHY: Commercial traders buying heavily
```

### Week 26+ (Full Operation)
```
Report shows:
  "FOUND 5-8 INVESTMENT OPPORTUNITIES"

  BUY RECOMMENDATIONS:
  1. GC (Gold) - Confidence: 95%
  2. SI (Silver) - Confidence: 88%
  3. CL (Oil) - Confidence: 82%

  SELL RECOMMENDATIONS:
  1. EUR (Euro) - Confidence: 91%
  2. ZC (Corn) - Confidence: 76%
```

---

## How the System Works

```
Step 1: CFTC Releases Data (Fridays 3:30 PM ET)
   ↓
Step 2: Your Monitor Checks Daily (every 24 hours)
   ↓
Step 3: If New Data Found → Analyze
   ↓
Step 4: Generate Trade Sheet in Simple English
   ↓
Step 5: Display in TUI Dashboard
```

---

## Reading Your Trade Sheet

### When Opportunities Found:
```
BUY RECOMMENDATIONS (LONG POSITIONS)

1. GC - Confidence: 85%

   WHAT TO DO:
      BUY GC for a potential upward move

   WHY THIS OPPORTUNITY:
      * Commercial traders (smart money) are BUYING heavily
        COT Index: 92.5/100 (bullish)
        When pros buy, prices usually go UP

      * November historically shows strength in this market
        Seasonal patterns favor upward movement

      * Multiple signals align (85% confidence)
        This is NOT a guess - data supports this move

   SIMPLE EXPLANATION:
      Professional traders who move billions are positioning
      for higher prices. History shows this setup works.

   RISK LEVEL:
      LOW - Strong confidence, good setup
```

**In plain English**: "Buy Gold because the professionals are buying."

### When NO Opportunities:
```
NO HIGH-CONFIDENCE INVESTMENT OPPORTUNITIES AT THIS TIME

WHY NO RECOMMENDATIONS?

  1. Market Conditions:
     - Commercial traders (smart money) are not at extreme positions
     - No clear signals of market tops or bottoms
     - Markets are in neutral/consolidation phase
```

**In plain English**: "Don't trade. Wait for better setups."

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│              WHEN IT REFRESHES                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  CFTC Data:        Every Friday, 3:30 PM ET            │
│  Your Monitor:     Every 24 hours (daily)              │
│  Best Check Time:  Friday evenings                     │
│                                                         │
│  First Signals:    Week 5-10                           │
│  Full Operation:   Week 26+                            │
│                                                         │
│  View Results:     cat output/latest_trade_sheet.txt   │
│  Start Monitor:    ./START_DAILY_MONITOR.sh            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Example Weekly Schedule

### Your Routine:
```
Monday:     Nothing to do (using Friday's data)
Tuesday:    Nothing to do (new data comes Friday)
Wednesday:  Nothing to do (waiting for Friday)
Thursday:   Nothing to do (almost there!)

Friday:
  3:30 PM ET → CFTC releases new data
  Evening    → Check your trade sheet
             → New opportunities appear
             → "BUY Gold" or "SELL Oil" recommendations

Saturday:
  Morning    → Review recommendations
             → Research symbols
             → Plan position sizes

Sunday:
  Evening    → Final review
             → Prepare orders for Monday
             → Set price alerts

Monday:
  Market Open → Execute trades based on recommendations
```

---

## Common Questions

### Q: Why check daily if data updates weekly?
**A:** The monitor runs daily to catch Friday's new data ASAP. It's like checking your mailbox daily even though mail only comes once - you want it as soon as it arrives.

### Q: What if I miss Friday's update?
**A:** No problem. The trade sheet stays valid all week. Check Saturday or Sunday.

### Q: How do I know when new data is used?
**A:** The trade sheet shows: "Report Date: Friday, November 29, 2025 at 07:09 PM"

### Q: Should I check multiple times per day?
**A:** No. Once per day is plenty. Data only updates weekly.

### Q: What timezone is 3:30 PM ET?
**A:** Eastern Time (US East Coast). Convert to your local time.

---

## Bottom Line

**When it refreshes**:
- CFTC data: Every Friday at 3:30 PM ET
- Your monitor: Every 24 hours
- Best check time: Friday evenings

**What you get**:
- Simple English recommendations
- "BUY Gold because..." explanations
- Clear confidence scores
- Risk levels

**How to use**:
1. Check Friday evening / Saturday morning
2. Read recommendations in simple English
3. Focus on 80%+ confidence opportunities
4. Act Monday when markets open

---

**Created**: November 29, 2025
**Status**: ✅ Daily monitoring ready
**Next Check**: Friday at 3:30 PM ET + your timezone offset
