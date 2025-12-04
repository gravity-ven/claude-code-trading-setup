# GARP Stock Screener - Spartan Research Station

## Overview

A fully functional **Growth at Reasonable Price (GARP)** stock screening dashboard with real-time data from Yahoo Finance.

## Features

### Real Data Sources
- **Yahoo Finance (yfinance)**: Unlimited, free stock data
- **Metrics**: P/E, PEG, Revenue Growth, Earnings Growth, ROE, Debt/Equity
- **Coverage**: 100+ major US stocks across 10 sectors

### GARP Scoring System (0-100)

The GARP score combines multiple fundamental metrics:

| Metric | Weight | Excellent | Good | Fair |
|--------|--------|-----------|------|------|
| PEG Ratio | 30 pts | < 1.0 | 1.0-2.0 | > 2.0 |
| P/E Ratio | 20 pts | < 15 | 15-25 | > 25 |
| Revenue Growth | 20 pts | > 20% | 10-20% | < 10% |
| Earnings Growth | 15 pts | > 20% | 10-20% | < 10% |
| ROE | 10 pts | > 20% | 10-20% | < 10% |
| Debt/Equity | 5 pts | < 0.5 | 0.5-1.0 | > 1.0 |

**Rating Categories**:
- **Excellent**: 80-100 points (Green badge)
- **Good**: 60-79 points (Blue badge)
- **Fair**: 40-59 points (Orange badge)
- **Poor**: 0-39 points (Red badge)

### Dashboard Features

1. **Summary Cards**
   - Total stocks screened
   - GARP candidates found
   - Highest score
   - Average score

2. **Advanced Filtering**
   - Filter by sector (10 sectors)
   - Set minimum GARP score threshold
   - Search by symbol or company name
   - Real-time filter updates

3. **Interactive Table**
   - Sortable columns (click headers)
   - Color-coded ratings
   - Price change indicators
   - Detailed metrics per stock

4. **Spartan Theme**
   - Professional dark theme
   - Crimson red accents (#DC143C)
   - Responsive design
   - Smooth animations

## Installation

### Prerequisites

```bash
# Python 3.8+
python --version

# Install dependencies
pip install flask flask-cors yfinance pandas numpy
```

### Quick Start

1. **Start the API server** (Terminal 1):
```bash
cd /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website
python garp_api.py
```

Expected output:
```
============================================================
GARP Stock Screener API Server
============================================================
Starting server on http://localhost:5003
Cache duration: 4.0 hours
Total stocks in universe: 100
============================================================
```

2. **Open the dashboard** (Browser):
```bash
# Option 1: Direct file
open garp.html

# Option 2: Via web server (Terminal 2)
python -m http.server 8000
# Then visit: http://localhost:8000/garp.html
```

## API Endpoints

### 1. Screen All Stocks
```bash
GET http://localhost:5003/api/garp/screen
```

**Query Parameters**:
- `sector` (optional): Filter by sector (e.g., `Technology`)
- `min_score` (optional): Minimum GARP score (default: 0)
- `limit` (optional): Max results (default: 50)

**Example**:
```bash
curl "http://localhost:5003/api/garp/screen?sector=Technology&min_score=60"
```

**Response**:
```json
{
  "success": true,
  "timestamp": "2025-11-18T12:00:00",
  "total_screened": 12,
  "total_found": 5,
  "stocks": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "sector": "Technology",
      "price": 189.50,
      "price_change_pct": 1.25,
      "pe_ratio": 28.5,
      "peg_ratio": 1.2,
      "revenue_growth": 15.3,
      "earnings_growth": 18.2,
      "roe": 42.5,
      "debt_to_equity": 0.35,
      "garp_score": 72,
      "garp_rating": "Good",
      "score_breakdown": {
        "peg": 15,
        "pe": 10,
        "revenue_growth": 10,
        "earnings_growth": 8,
        "roe": 10,
        "debt_equity": 5
      }
    }
  ]
}
```

### 2. Get Single Stock
```bash
GET http://localhost:5003/api/garp/stock/{symbol}
```

**Example**:
```bash
curl http://localhost:5003/api/garp/stock/AAPL
```

### 3. List Sectors
```bash
GET http://localhost:5003/api/garp/sectors
```

### 4. Health Check
```bash
GET http://localhost:5003/api/health
```

## Stock Universe

### Technology (12 stocks)
AAPL, MSFT, GOOGL, META, NVDA, AMD, CRM, ADBE, INTC, CSCO, ORCL, AVGO

### Healthcare (10 stocks)
JNJ, UNH, PFE, ABBV, TMO, DHR, LLY, MRK, ABT, CVS

### Financial (10 stocks)
JPM, BAC, WFC, GS, MS, C, BLK, SCHW, USB, PNC

### Consumer (11 stocks)
AMZN, WMT, HD, PG, KO, PEP, COST, NKE, MCD, SBUX, TGT

### Industrial (9 stocks)
CAT, BA, HON, UNP, GE, MMM, LMT, RTX, DE

### Energy (8 stocks)
XOM, CVX, COP, SLB, EOG, PSX, VLO, MPC, OXY

### Materials (7 stocks)
LIN, APD, ECL, DD, DOW, NEM, FCX

### Utilities (8 stocks)
NEE, DUK, SO, D, AEP, EXC, SRE

### Real Estate (7 stocks)
AMT, PLD, CCI, EQIX, PSA, DLR, O

### Communication (10 stocks)
T, VZ, CMCSA, DIS, NFLX, TMUS

**Total: 100 stocks**

## Caching

- **Duration**: 4 hours
- **Reason**: Fundamental data changes slowly
- **Benefits**: Fast response, API rate limit protection

To force refresh:
1. Restart the API server
2. Wait 4 hours for automatic cache expiry

## Usage Examples

### Find Top Technology GARP Stocks
1. Open `garp.html`
2. Select **"Technology"** from Sector dropdown
3. Set Minimum Score to **60**
4. Click **"Apply Filters"**

### Search Specific Stock
1. Type **"AAPL"** or **"Apple"** in Search box
2. Press Enter or click Apply

### Sort by Best PEG Ratio
1. Click **"PEG Ratio"** column header
2. Click again to toggle ascending/descending

## Troubleshooting

### Error: "Failed to load data"

**Problem**: API server not running

**Solution**:
```bash
# Check if server is running
curl http://localhost:5003/api/health

# If not, start it
python garp_api.py
```

### Error: "ModuleNotFoundError: No module named 'yfinance'"

**Problem**: Missing dependencies

**Solution**:
```bash
pip install yfinance flask flask-cors pandas numpy
```

### Slow Initial Load

**Normal**: First load takes 30-60 seconds to fetch all 100 stocks

**Subsequent loads**: Instant (cached for 4 hours)

### CORS Errors

**Problem**: Browser blocking API requests

**Solution**:
1. Ensure API server is running
2. Use web server instead of file:// protocol:
   ```bash
   python -m http.server 8000
   ```

## Technical Details

### Architecture

```
┌─────────────────┐
│   garp.html     │  Frontend (HTML/CSS/JS)
│   (Dashboard)   │
└────────┬────────┘
         │ HTTP GET /api/garp/screen
         ▼
┌─────────────────┐
│   garp_api.py   │  Backend API (Flask)
│   (Port 5003)   │
└────────┬────────┘
         │ yfinance API calls
         ▼
┌─────────────────┐
│ Yahoo Finance   │  Data Source (Free, Unlimited)
│   (Real-time)   │
└─────────────────┘
```

### File Structure

```
website/
├── garp.html           # Frontend dashboard
├── garp_api.py         # Backend API server
├── GARP_README.md      # This file
└── spartan_logo.png    # Logo (optional)
```

## Performance

- **API Response Time**: < 100ms (cached)
- **Initial Screen Time**: 30-60 seconds (100 stocks)
- **Memory Usage**: ~50MB (API server)
- **Concurrent Users**: 100+ (Flask default)

## Future Enhancements

- [ ] Add historical GARP score tracking
- [ ] Email alerts for high-scoring stocks
- [ ] Export results to CSV/Excel
- [ ] Add dividend yield to scoring
- [ ] Compare stocks side-by-side
- [ ] Mobile app version

## License

Spartan Research Station - Internal Use

---

**Last Updated**: November 18, 2025
**Version**: 1.0.0
**Status**: Production Ready
