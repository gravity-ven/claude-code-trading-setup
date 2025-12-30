# 🍌 Nano Banana W/M Scanner - Complete Guide

## Overview

The **Nano Banana W/M Scanner** is a comprehensive pattern detection system that scans 12,000+ financial instruments for **W (double bottom)** and **M (double top)** chart patterns across multiple asset classes.

---

## 🚀 Features

### Multi-Mode Scanning

The scanner supports **7 scan modes**:

| Mode | Instruments | Data Source |
|------|-------------|-------------|
| **📊 Stocks** | 12,444 stocks | Polygon.io API |
| **📈 ETFs** | 3,000+ ETFs | Polygon.io API |
| **🌾 Futures COT** | 27 futures contracts | CFTC.gov API |
| **₿ Crypto** | 250+ cryptocurrencies | Polygon.io API |
| **💱 Forex** | Major currency pairs | Polygon.io API |
| **🏆 S&P 500** | 500 components | Polygon.io API |
| **💻 NASDAQ 100** | 100 components | Polygon.io API |

### Pattern Detection

#### W Pattern (Double Bottom) - Bullish Signal
```
    /\      /\
   /  \    /  \
  /    \  /    \
 /      \/      \
```
- **Signal**: Bullish reversal
- **Detection**: Second trough higher than first
- **Confirmation**: Price recovery above middle peak
- **Ideal for**: Identifying oversold bounce opportunities

#### M Pattern (Double Top) - Bearish Signal
```
 \      /\      /
  \    /  \    /
   \  /    \  /
    \/      \/
```
- **Signal**: Bearish reversal
- **Detection**: Second peak lower than first
- **Confirmation**: Price breakdown below middle trough
- **Ideal for**: Identifying overbought correction opportunities

### COT (Commitment of Traders) Analysis

For futures markets, the scanner also analyzes **COT Index** patterns:

- **COT Index**: Normalized speculator positioning (0-100)
- **Calculation**: 26-week rolling lookback
- **Interpretation**:
  - **0-20**: Extreme bearish positioning (potential bullish reversal)
  - **80-100**: Extreme bullish positioning (potential bearish reversal)

---

## 🎯 How to Use

### 1. Access the Scanner

**From Main Dashboard**:
- Click on **🍌 Nano Banana Scanner** in the navigation
- Or direct URL: `nano_banana_scanner.html`

### 2. Select Scan Mode

Click one of the scan mode buttons:
- **Scan Stocks** - Full database scan (12,444 instruments)
- **Scan ETFs** - ETF-only scan
- **Scan Futures COT** - COT pattern detection on 27 futures
- **Scan Crypto** - Cryptocurrency scan
- **Scan Forex** - Currency pair scan
- **Scan S&P 500** - S&P 500 components only
- **Scan NASDAQ 100** - NASDAQ 100 components only

### 3. Monitor Scan Progress

- **Progress overlay** shows scan status
- **Current symbol** being scanned
- **Completed / Total** instruments
- **Estimated time remaining**

### 4. Review Results

Results are displayed in a **sortable table**:

| Column | Description |
|--------|-------------|
| **Symbol** | Ticker symbol |
| **Name** | Company/instrument name |
| **Pattern** | W (bullish) or M (bearish) |
| **Signal** | BULLISH or BEARISH |
| **Price** | Current price |
| **Change** | Daily price change % |
| **Volume** | Trading volume |
| **Pattern Depth** | Strength of pattern (higher = stronger) |
| **COT Index** | Speculator positioning (futures only) |
| **Chart** | Mini sparkline visualization |

### 5. Sort & Filter

- **Click column headers** to sort
- **Search box** to filter by symbol/name
- **Category filters** to focus on specific asset types
- **Export** results to CSV (future enhancement)

---

## 📊 Data Sources

### Polygon.io API
- **Real-time price data** for stocks, ETFs, crypto, forex
- **Historical OHLCV data** for pattern detection
- **Rate limit**: 5 requests/second (free tier)
- **API Key**: Configured in environment

### CFTC.gov API
- **Official COT reports** (updated weekly on Fridays)
- **Legacy & Disaggregated data** for futures positioning
- **27 futures markets** covered
- **100% real data** - no simulations

### Yahoo Finance (Fallback)
- **Backup price source** via yfinance library
- **Free, no API key required**
- **Used when Polygon.io quota exceeded**

---

## 🔬 Technical Details

### Pattern Detection Algorithm

```python
def detect_w_pattern(prices: list, window: int = 15) -> dict:
    """
    Detect W (double bottom) pattern.

    Args:
        prices: List of closing prices (most recent last)
        window: Days to scan for pattern (default 15)

    Returns:
        {
            'pattern': 'W',
            'signal': 'BULLISH',
            'pattern_depth': float,  # Strength metric
            'first_trough': float,
            'second_trough': float,
            'middle_peak': float
        }
    """
    # Find local minima (troughs) and maxima (peaks)
    troughs = find_local_minima(prices)
    peaks = find_local_maxima(prices)

    # Check for double bottom with second trough higher
    if len(troughs) >= 2 and len(peaks) >= 1:
        if troughs[-1] > troughs[-2]:  # Second trough higher
            if prices[-1] > peaks[-1]:  # Recovery confirmed
                depth = (peaks[-1] - troughs[-2]) / troughs[-2]
                return {
                    'pattern': 'W',
                    'signal': 'BULLISH',
                    'pattern_depth': depth * 100
                }
```

### COT Index Calculation

```python
def calculate_cot_index(net_positions: list, lookback: int = 26) -> float:
    """
    Calculate COT Index (0-100 normalized positioning).

    Args:
        net_positions: List of net speculator positions
        lookback: Weeks of historical data for normalization

    Returns:
        COT Index value (0-100)
    """
    current = net_positions[-1]
    min_pos = min(net_positions[-lookback:])
    max_pos = max(net_positions[-lookback:])

    if max_pos == min_pos:
        return 50.0

    cot_index = ((current - min_pos) / (max_pos - min_pos)) * 100
    return round(cot_index, 2)
```

---

## 🎨 Visual Elements

### Pattern Card Display

Each detected pattern is displayed with:
- **🟢 Green border** for W patterns (bullish)
- **🔴 Red border** for M patterns (bearish)
- **Symbol & name** prominently displayed
- **Current price & change %** with color coding
- **Pattern strength bar** (visual depth indicator)
- **Mini sparkline chart** of recent price action

### COT Index Bars

For futures markets:
- **Red → Yellow → Green** gradient (0 to 100)
- **0-20**: Deep red (extreme bearish)
- **40-60**: Yellow (neutral)
- **80-100**: Bright green (extreme bullish)

---

## 🔧 Configuration

### Environment Variables

Required API keys (in `.env` or environment):

```bash
# Polygon.io (required for stocks/ETFs/crypto/forex)
POLYGON_API_KEY=your_polygon_api_key_here

# FRED (optional - for economic data enrichment)
FRED_API_KEY=your_fred_api_key_here
```

### Symbols Database

The scanner loads instruments from `symbols_database.json`:
- **12,444 instruments** total
- **Stocks**: NYSE, NASDAQ, AMEX
- **ETFs**: Major and thematic ETFs
- **Auto-updates**: Via polygon sync (weekly)

---

## 📈 Use Cases

### 1. Swing Trading Setup Scanner

**Workflow**:
1. Run **Scan S&P 500** at market close
2. Filter for **W patterns** (bullish setups)
3. Review **pattern depth** (look for 5%+ depth)
4. Check **volume confirmation**
5. Add to watchlist for next day entry

**Expected Results**:
- 5-15 potential setups daily
- Best success on oversold bounces
- Entry: Above middle peak confirmation

### 2. Futures COT Reversal Scanner

**Workflow**:
1. Run **Scan Futures COT** weekly (after Friday COT report)
2. Look for **W patterns with COT Index < 20** (extreme bearish positioning + bullish pattern)
3. Or **M patterns with COT Index > 80** (extreme bullish positioning + bearish pattern)
4. Plan contrarian trades

**Expected Results**:
- 1-3 high-probability setups per week
- Ideal for major reversals
- Combine with fundamental catalysts

### 3. High-Growth Stock Discovery

**Workflow**:
1. Run **Scan Stocks** on Monday morning
2. Filter for **W patterns**
3. Cross-reference with **high volume** (>1M shares)
4. Check fundamental metrics (earnings, revenue growth)
5. Build long-term positions

**Expected Results**:
- 20-40 potential candidates
- Focus on growth sectors (tech, biotech)
- Hold for 3-6 months

### 4. Crypto Bottom Fishing

**Workflow**:
1. Run **Scan Crypto** during market dips
2. Filter for **W patterns**
3. Look for **pattern depth > 10%** (strong reversal)
4. Enter on confirmation (close above middle peak)

**Expected Results**:
- 5-10 crypto candidates
- High risk/reward ratio
- Ideal for volatile markets

---

## ⚡ Performance Tips

### Optimize Scan Speed

1. **Use specific modes** instead of full stock scan
2. **S&P 500 / NASDAQ 100** modes scan faster (fewer instruments)
3. **Close browser tabs** to free memory
4. **Check API quota** before large scans

### API Rate Limits

| Provider | Free Tier | Paid Tier |
|----------|-----------|-----------|
| **Polygon.io** | 5 req/sec | 100 req/sec |
| **CFTC.gov** | Unlimited | N/A |
| **Yahoo Finance** | Unlimited | N/A |

**Strategy**: Use CFTC for futures, Polygon for stocks/ETFs, Yahoo as fallback.

---

## 🐛 Troubleshooting

### "API quota exceeded"

**Solution**:
- Wait 1 minute and retry
- Or switch to S&P 500 / NASDAQ 100 mode (smaller scan)
- Or upgrade to Polygon.io paid plan

### "No patterns detected"

**Possible reasons**:
1. **Market conditions** - sideways markets have fewer patterns
2. **Pattern window too short** - try increasing to 21 days
3. **Pattern strength threshold** - lower the depth requirement

### "Data fetch failed"

**Check**:
1. API keys configured correctly
2. Internet connection active
3. API services operational (check status pages)

---

## 📚 Educational Resources

### Understanding W/M Patterns

- **W Pattern**: Also called "double bottom" or "Adam & Eve bottom"
- **M Pattern**: Also called "double top" or "Adam & Eve top"
- **Timeframes**: Work on daily, weekly, and intraday charts
- **Confirmation**: Always wait for price breakout confirmation

### COT Data Interpretation

- **Commercials**: Hedgers (producers/consumers) - contrarian indicator
- **Non-Commercials**: Speculators (hedge funds) - trend indicator
- **COT Index**: Normalized positioning for easy comparison
- **Best use**: Major reversals at extremes (0-20 or 80-100)

### Recommended Reading

1. **Technical Analysis of the Financial Markets** by John Murphy
2. **Encyclopedia of Chart Patterns** by Thomas Bulkowski
3. **Commitment of Traders Bible** by Stephen Briese
4. **How to Make Money in Stocks** by William O'Neil

---

## 🔐 Security & Privacy

- **API keys**: Stored in environment variables, never exposed to client
- **Rate limiting**: Automatic throttling to prevent quota abuse
- **Data privacy**: No user trading data stored
- **HTTPS**: All API calls encrypted

---

## 🚀 Future Enhancements

### Planned Features

- [ ] **Multi-timeframe analysis** (daily + weekly patterns)
- [ ] **Pattern strength scoring** (ML-based confidence)
- [ ] **Backtesting engine** (historical performance)
- [ ] **Real-time alerts** (WebSocket notifications)
- [ ] **Mobile app** (iOS/Android native)
- [ ] **Export to TradingView** (chart integration)
- [ ] **Custom watchlists** (save favorite setups)
- [ ] **Pattern breakout tracker** (track pattern outcomes)

### Integrations

- [ ] **TradingView** - One-click chart viewing
- [ ] **Alpaca/IBKR** - Direct trade execution
- [ ] **Discord/Telegram** - Pattern alerts
- [ ] **Google Sheets** - Export results
- [ ] **Email notifications** - Daily digest

---

## 📞 Support

### Getting Help

1. **Documentation**: This file
2. **Code**: `nano_banana_scanner.html` (fully commented)
3. **Python scanner**: `cot_pattern_scanner.py` (CLI version)
4. **Issues**: Check browser console for errors

### Common Questions

**Q: How often should I run scans?**
A: Daily for stocks/ETFs, weekly for futures COT.

**Q: What's a good pattern depth threshold?**
A: 5%+ for stocks, 10%+ for crypto, 15+ for COT Index.

**Q: Can I automate scans?**
A: Yes, use `cot_pattern_scanner.py` in cron jobs.

**Q: Are results guaranteed?**
A: No - patterns are probabilities, not certainties. Always use risk management.

---

## 📄 License

This scanner is part of the **Spartan Research Station** platform.

**Usage**: Free for personal trading and research.
**Redistribution**: Prohibited without permission.
**Data**: Provided "as-is" - trade at your own risk.

---

## 🎯 Quick Start Checklist

- [ ] Verify `POLYGON_API_KEY` configured in `.env`
- [ ] Open `nano_banana_scanner.html` in browser
- [ ] Click **"Scan S&P 500"** for first test
- [ ] Review results table
- [ ] Sort by **Pattern Depth** (highest first)
- [ ] Check **mini charts** for visual confirmation
- [ ] Add interesting setups to watchlist
- [ ] Backtest patterns before live trading

---

## 📊 Example Output

```
╔══════════════════════════════════════════════════════════════╗
║           NANO BANANA W/M PATTERN SCANNER                    ║
╚══════════════════════════════════════════════════════════════╝

Scan Mode: S&P 500 Components
Scan Time: 2025-12-30 18:15:00
Instruments Scanned: 500
Patterns Detected: 18

╔════════╦═══════════╦═════════╦════════╦═══════════╦═════════╗
║ Symbol ║  Pattern  ║  Signal ║  Price ║  Change % ║  Depth  ║
╠════════╬═══════════╬═════════╬════════╬═══════════╬═════════╣
║  AAPL  ║     W     ║ BULLISH ║ 195.34 ║   +2.1%   ║  6.8%   ║
║  MSFT  ║     W     ║ BULLISH ║ 378.12 ║   +1.5%   ║  5.4%   ║
║  NVDA  ║     M     ║ BEARISH ║ 495.67 ║   -1.2%   ║  7.3%   ║
║  GOOGL ║     W     ║ BULLISH ║ 141.23 ║   +3.4%   ║  8.1%   ║
║  AMZN  ║     W     ║ BULLISH ║ 178.45 ║   +2.8%   ║  6.2%   ║
╚════════╩═══════════╩═════════╩════════╩═══════════╩═════════╝

✅ W Patterns (Bullish): 14
❌ M Patterns (Bearish): 4

💡 Top 3 Setups:
1. GOOGL - W Pattern (8.1% depth) + Volume spike
2. NVDA - M Pattern (7.3% depth) + Resistance breakdown
3. AAPL - W Pattern (6.8% depth) + Earnings catalyst
```

---

**Last Updated**: December 30, 2025
**Version**: 2.0.0
**Author**: Spartan Research Station
**Platform**: Nano Banana W/M Scanner
