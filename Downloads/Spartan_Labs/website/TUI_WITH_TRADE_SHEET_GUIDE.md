# COT TUI with Trade Sheet Integration

## What's New

The TUI now displays **investment signals in real-time** directly in the dashboard alongside agent execution status.

---

## Dashboard Layout

```
+--------------------------------------------------------------------------------+
|                    SPARTAN COT AGENTS - Intelligence Dashboard                 |
|                DEMO MODE  |  Started: 19:30:00  |  Elapsed: 3.5s              |
+--------------------------------------------------------------------------------+
|                                                                                |
|  +----------------TIERS----------------+  +------INVESTMENT SIGNALS---------+ |
|  |                                     |  |                                 | |
|  | [DONE] COT Analysis                 |  | BUY RECOMMENDATIONS             | |
|  | Analyzing CFTC reports              |  |                                 | |
|  |   * Fetched GC: Net -61457          |  | 1. GC (Gold) - Confidence: 85%  | |
|  |   * Stored raw COT data for GC      |  |                                 | |
|  |   * COT Index: 50.00                |  |    WHAT TO DO:                  | |
|  |                                     |  |       BUY Gold for upward move  | |
|  | [DONE] Seasonality                  |  |                                 | |
|  | Detecting seasonal patterns         |  |    WHY THIS OPPORTUNITY:        | |
|  |   * Monthly patterns analyzed       |  |       * Commercials BUYING      | |
|  |                                     |  |       * COT Index: 85/100       | |
|  | [DONE] Confluence                   |  |                                 | |
|  | Calculating signal confluence       |  |    RISK LEVEL:                  | |
|  |   * Confluence scores calculated    |  |       LOW - Strong signal       | |
|  |                                     |  |                                 | |
|  | [DONE] Trade Sheets                 |  | OR:                             | |
|  | Generating recommendations          |  |                                 | |
|  |   * Trade sheet generated           |  | NO SIGNALS                      | |
|  |                                     |  | Markets are neutral.            | |
|  +-------------------------------------+  | Building data (Week 1/26)       | |
|                                           |                                 | |
|  +------- Summary --------+               +---------------------------------+ |
|  | COT     | [DONE] | 3 items |                                              |
|  | Season  | [DONE] | 1 item  |                                              |
|  | Conflu  | [DONE] | 1 item  |                                              |
|  | Trades  | [DONE] | 1 item  |                                              |
|  +-------------------------------------+                                      |
|  Logs: tail -f logs/agents.log  |  Refresh: Auto-updates live  |  Ctrl+C exit |
+--------------------------------------------------------------------------------+
```

---

## Key Features

### 1. Real-Time Trade Signals

The **Investment Signals** panel on the right shows:
- ✅ **BUY recommendations** (green) with confidence levels
- ✅ **SELL recommendations** (red) with confidence levels
- ✅ **Plain English explanations** of why to invest
- ✅ **Risk levels** for each opportunity
- ✅ **Auto-updates** as agents generate new signals

### 2. Tier Execution Status

The left panels show agent execution progress:
- **[PENDING]** - Not started yet
- **[RUNNING]** - Currently processing
- **[DONE]** - Completed successfully
- **[FAILED]** - Error occurred

### 3. Live Updates

The TUI automatically refreshes:
- Agent status changes
- New trade signals
- Results from each tier
- Real-time data flow

### 4. Color-Coded Signals

**BUY Recommendations:**
- Header: **Bold Green**
- Symbol: **Bold Cyan** (e.g., "1. GC (Gold)")
- "WHAT TO DO:": **Bold Yellow**
- "WHY THIS OPPORTUNITY:": **Bold Magenta**
- "RISK LEVEL:": **Bold Red**

**SELL Recommendations:**
- Header: **Bold Red**
- Same color coding for sections

**No Signals:**
- "NO SIGNALS": **Bold Yellow**
- Explanation: **Dim White**

---

## Quick Start

### Launch TUI

```bash
# Option 1: New launcher script
./START_TUI_WITH_TRADES.sh

# Option 2: Direct Python execution
python3 run_cot_ascii_tui.py --demo

# Option 3: Production mode (100 agents)
python3 run_cot_ascii_tui.py
```

### What You'll See

**During Execution:**
1. Agents execute tier by tier (1-4)
2. Real-time status updates in left panels
3. Trade sheet appears when Tier 4 completes
4. Investment signals display in right panel

**After Completion:**
- Summary table shows all tiers completed
- Trade signals remain visible
- Press any key or wait 3 seconds to exit

---

## Trade Sheet Display Logic

The TUI intelligently parses the trade sheet:

### When Signals Exist

```
BUY RECOMMENDATIONS
+++++++++++++++++++

1. GC (Gold) - Confidence: 88%

   WHAT TO DO:
      BUY Gold for upward move

   WHY THIS OPPORTUNITY:
      * Commercial traders BUYING heavily
        COT Index: 85.2/100 (bullish)
      * When pros accumulate, prices rise

   RISK LEVEL:
      LOW - Strong institutional signal
```

### When No Signals

```
NO SIGNALS

Markets are neutral.
Building data (Week 1/26)
```

This happens when:
- Markets are not at extremes
- Need more historical data (< 26 weeks)
- No high-confidence opportunities exist

---

## Example Session

```bash
$ ./START_TUI_WITH_TRADES.sh

======================================================================
  Spartan COT Agents - TUI with Trade Sheet
======================================================================

Starting real-time dashboard with investment signals...

Features:
  * 4-Tier agent execution
  * Real-time trade signals
  * Auto-refreshing recommendations
  * Pure ASCII interface

Press Ctrl+C to exit at any time

Starting in 3 seconds...

[TUI loads with live updates]

Tier 1: [RUNNING] → Fetching CFTC data...
Tier 1: [DONE] → Stored COT data for GC

Tier 2: [RUNNING] → Analyzing seasonality...
Tier 2: [DONE] → Patterns analyzed

Tier 3: [RUNNING] → Calculating confluence...
Tier 3: [DONE] → Scores calculated

Tier 4: [RUNNING] → Generating trade sheet...
Tier 4: [DONE] → Trade sheet complete

[Trade signals appear in right panel]

BUY RECOMMENDATIONS
1. GC (Gold) - Confidence: 85%
   ...

[Press Ctrl+C or wait 3 seconds to exit]

======================================================================
Execution Complete
======================================================================
```

---

## Continuous Monitoring Mode

For 24/7 monitoring with the TUI, you can combine it with a loop:

```bash
#!/bin/bash
# Run TUI in continuous mode (every 24 hours)

while true; do
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║  CYCLE START - $(date '+%Y-%m-%d %H:%M:%S')                      ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"

    # Run TUI
    python3 -u run_cot_ascii_tui.py --demo

    # Wait 24 hours
    echo ""
    echo "Next cycle in 24 hours..."
    echo "Press Ctrl+C to stop monitoring"
    sleep 86400
done
```

Save as `CONTINUOUS_TUI_MONITOR.sh` and run:

```bash
chmod +x CONTINUOUS_TUI_MONITOR.sh
./CONTINUOUS_TUI_MONITOR.sh
```

---

## Alacritty Integration

To auto-start the TUI with trade sheet in Alacritty:

### Option 1: Update Existing Config

Edit `alacritty_cot_monitor.yml`:

```yaml
shell:
  program: /bin/bash
  args:
    - -c
    - /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/START_TUI_WITH_TRADES.sh
```

### Option 2: New Dedicated Config

Create `alacritty_cot_tui.yml`:

```yaml
window:
  title: "Spartan COT TUI - Live Trade Signals"
  dimensions:
    columns: 140
    lines: 50

shell:
  program: /bin/bash
  args:
    - -c
    - cd /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website && python3 -u run_cot_ascii_tui.py --demo

font:
  size: 11.0

colors:
  # Use the same Spartan color scheme
```

Launch with:

```bash
alacritty --config-file ~/.config/alacritty/alacritty_cot_tui.yml
```

---

## Comparison: Simple Monitor vs TUI

### SIMPLE_DAILY_MONITOR.sh

**Pros:**
- Simple text output
- Easy to scroll back
- Good for logging
- Runs forever in background

**Cons:**
- No real-time status
- Can't see tier progress
- Plain text only

### TUI with Trade Sheet (run_cot_ascii_tui.py)

**Pros:**
- ✅ Real-time agent status
- ✅ Live trade signals in dashboard
- ✅ Color-coded recommendations
- ✅ Visual tier progress
- ✅ Professional appearance

**Cons:**
- Exits after single cycle (unless wrapped in loop)
- Uses screen space (can't scroll back easily)

---

## Recommended Setup

**Best of Both Worlds:**

1. **For Active Monitoring:**
   ```bash
   # Use TUI when you want to watch agents execute
   ./START_TUI_WITH_TRADES.sh
   ```

2. **For Background/24x7:**
   ```bash
   # Use simple monitor for continuous operation
   ./SIMPLE_DAILY_MONITOR.sh
   ```

3. **For Quick Checks:**
   ```bash
   # View latest trade sheet anytime
   cat output/latest_trade_sheet.txt
   ```

---

## Troubleshooting

### TUI Exits Immediately

**Cause:** Agents completed execution

**Solution:** This is normal behavior. For continuous monitoring:
```bash
# Run in loop
while true; do python3 run_cot_ascii_tui.py --demo; sleep 86400; done
```

### Trade Sheet Panel Empty

**Cause:** Trade sheet not yet generated (Tier 4 not started)

**Solution:** Wait for Tier 4 to complete. Panel will show:
- "Waiting for Tier 4 agents..." (during execution)
- "NO SIGNALS" (when no opportunities found)
- Trade recommendations (when signals exist)

### Unicode/Encoding Errors

**Cause:** Terminal doesn't support special characters

**Solution:** This TUI uses pure ASCII (box.ASCII) - should work everywhere

### Colors Not Showing

**Cause:** Terminal doesn't support ANSI colors

**Solution:** Use a modern terminal (Alacritty, iTerm2, Windows Terminal)

---

## Key Files

- **run_cot_ascii_tui.py** - Main TUI script with trade sheet integration
- **START_TUI_WITH_TRADES.sh** - Launcher script
- **output/latest_trade_sheet.txt** - Source for trade signals
- **logs/agents.log** - Detailed agent execution logs

---

## Summary

✅ **TUI now displays trade signals in real-time**
✅ **Investment recommendations visible during execution**
✅ **Color-coded buy/sell signals**
✅ **Plain English explanations**
✅ **Auto-refreshing dashboard**
✅ **Pure ASCII - works everywhere**

**Launch Command:**
```bash
./START_TUI_WITH_TRADES.sh
```

**What You Get:**
- Real-time agent execution status
- Live trade signals displayed in dashboard
- Professional TUI interface
- Simple English investment recommendations

---

**Created:** November 29, 2025
**Status:** ✅ Fully Operational
**Integration:** Trade Sheet + TUI Dashboard Complete
