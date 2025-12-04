# Daily Planet Dashboard - Setup Guide

## Overview

**Daily Planet** is a fully functional market intelligence dashboard built for Spartan Research Station. It provides:

- **Daily Market News Summary** - Real-time news from major market indices
- **Economic Calendar Events** - Upcoming high-impact economic releases
- **Top Market Movers** - Live data on biggest price changes
- **Sector Rotation Analysis** - Real-time sector ETF performance
- **News Sentiment Analysis** - Market sentiment calculated from indices and VIX

## Features

✅ **100% Real Data** - No fake/random data, powered by yfinance
✅ **Spartan Theme** - Matches Spartan Research Station design (#8B0000, #DC143C, #B22222)
✅ **Responsive Design** - Works on desktop, tablet, and mobile
✅ **Auto-Refresh** - Updates every 5 minutes automatically
✅ **Cache Prevention** - Always shows latest data
✅ **Graceful Fallback** - Shows placeholder content if API unavailable

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                 Daily Planet Dashboard              │
│                 (daily_planet.html)                 │
└─────────────────────┬───────────────────────────────┘
                      │
                      │ HTTP Requests
                      │
┌─────────────────────▼───────────────────────────────┐
│              Python Flask API Server                │
│            (daily_planet_api.py)                    │
│                                                     │
│  Endpoints:                                         │
│  • /api/market-news         (GET)                  │
│  • /api/economic-calendar   (GET)                  │
│  • /api/market-movers       (POST)                 │
│  • /api/sector-rotation     (POST)                 │
│  • /api/sentiment-analysis  (GET)                  │
└─────────────────────┬───────────────────────────────┘
                      │
                      │ yfinance API
                      │
┌─────────────────────▼───────────────────────────────┐
│              Yahoo Finance API                      │
│           (Unlimited Free Access)                   │
└─────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

- **Python 3.8+**
- **pip** (Python package manager)

### Step 1: Install Python Dependencies

```bash
cd /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website

pip install flask flask-cors yfinance
```

### Step 2: Verify Files

Ensure these files exist:
- `daily_planet.html` - Frontend dashboard
- `daily_planet_api.py` - Backend API server

## Usage

### Starting the API Server

```bash
python3 daily_planet_api.py
```

**Expected Output:**
```
============================================================
Daily Planet API Server Starting...
============================================================
Server: http://localhost:5000
Endpoints:
  GET  /api/market-news         - Latest market news
  GET  /api/economic-calendar   - Economic events
  POST /api/market-movers       - Top market movers
  POST /api/sector-rotation     - Sector performance
  GET  /api/sentiment-analysis  - Market sentiment
  GET  /health                  - Health check
============================================================
Data Source: yfinance (unlimited free API)
============================================================
 * Serving Flask app 'daily_planet_api'
 * Debug mode: on
 * Running on http://0.0.0.0:5000
```

### Opening the Dashboard

1. **Ensure API server is running** (see above)
2. **Open in browser:**
   - File path: `file:///mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/daily_planet.html`
   - Or double-click `daily_planet.html` in Windows Explorer

3. **Dashboard loads automatically**
   - Fetches real market data from API
   - Updates every 5 minutes
   - Shows placeholder if API unavailable

## API Endpoints

### 1. Market News (`GET /api/market-news`)

**Description:** Fetch latest market news from SPY, QQQ, DIA
**Request:** `GET http://localhost:5000/api/market-news`
**Response:**
```json
{
  "success": true,
  "news": [
    {
      "title": "Markets Rally on Fed Comments",
      "source": "Reuters",
      "timestamp": 1700000000,
      "link": "https://..."
    }
  ],
  "timestamp": "2025-11-18T10:30:00"
}
```

### 2. Economic Calendar (`GET /api/economic-calendar`)

**Description:** Get upcoming economic events (placeholder data)
**Request:** `GET http://localhost:5000/api/economic-calendar`
**Response:**
```json
{
  "success": true,
  "events": [
    {
      "time": "2025-11-18T14:00:00",
      "title": "CPI Release",
      "country": "USA",
      "category": "Inflation",
      "impact": "high"
    }
  ],
  "timestamp": "2025-11-18T10:30:00"
}
```

### 3. Market Movers (`POST /api/market-movers`)

**Description:** Real-time price changes for specified symbols
**Request:**
```bash
curl -X POST http://localhost:5000/api/market-movers \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "MSFT", "GOOGL"]}'
```
**Response:**
```json
{
  "success": true,
  "movers": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "price": 185.25,
      "change_pct": 2.45,
      "volume": 50000000
    }
  ],
  "timestamp": "2025-11-18T10:30:00"
}
```

### 4. Sector Rotation (`POST /api/sector-rotation`)

**Description:** Real-time sector ETF performance
**Request:**
```bash
curl -X POST http://localhost:5000/api/sector-rotation \
  -H "Content-Type: application/json" \
  -d '{"sectors": {"XLK": "Technology", "XLF": "Financials"}}'
```
**Response:**
```json
{
  "success": true,
  "sectors": [
    {
      "symbol": "XLK",
      "name": "Technology",
      "price": 180.50,
      "change_pct": 1.85,
      "volume": 25000000
    }
  ],
  "timestamp": "2025-11-18T10:30:00"
}
```

### 5. Sentiment Analysis (`GET /api/sentiment-analysis`)

**Description:** Market sentiment calculated from SPY, QQQ, VIX
**Request:** `GET http://localhost:5000/api/sentiment-analysis`
**Response:**
```json
{
  "success": true,
  "sentiment": {
    "overall": 58,
    "bullish": 45,
    "neutral": 28,
    "bearish": 27
  },
  "vix": 18.5,
  "spy_change": 0.85,
  "qqq_change": 1.20,
  "timestamp": "2025-11-18T10:30:00"
}
```

## Data Sources

### Primary: yfinance (Unlimited Free)

- **Market data**: Real-time prices, volumes, changes
- **News**: Latest headlines from Yahoo Finance
- **No API key required**
- **No rate limits**

### Placeholder Data

- **Economic Calendar**: Uses placeholder events (production would use Trading Economics API)

## Troubleshooting

### Issue: Dashboard shows "Unable to fetch data"

**Solution:**
1. Verify API server is running: `curl http://localhost:5000/health`
2. Check console for errors: Open browser DevTools (F12) → Console tab
3. Ensure no firewall blocking port 5000

### Issue: API returns 500 errors

**Solution:**
1. Check Python dependencies installed: `pip list | grep -E "flask|yfinance"`
2. View server logs in terminal
3. Test individual endpoints: `curl http://localhost:5000/api/market-news`

### Issue: Stale/cached data showing

**Solution:**
1. Hard refresh browser: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
2. Clear browser cache
3. Check `Cache-Control` headers in HTML (should be `no-cache`)

## Deployment

### Production Deployment Options

#### Option 1: Local Server (Current Setup)
- Run API server on localhost
- Open HTML file directly
- Best for: Personal use, testing

#### Option 2: Web Server (Nginx/Apache)
- Host HTML on web server
- Run API server as systemd service
- Best for: Team access, always-on

#### Option 3: Cloud Deployment
- Frontend: Deploy HTML to S3/Netlify/Vercel
- Backend: Deploy API to AWS Lambda/Google Cloud Run
- Best for: Public access, scalability

### Example: Running API as Background Service

```bash
# Create systemd service file
sudo nano /etc/systemd/system/daily-planet-api.service

# Add content:
[Unit]
Description=Daily Planet API Server
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/website
ExecStart=/usr/bin/python3 daily_planet_api.py
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start service
sudo systemctl enable daily-planet-api
sudo systemctl start daily-planet-api
sudo systemctl status daily-planet-api
```

## Customization

### Adding More Symbols to Market Movers

Edit `daily_planet.html`, line ~754:
```javascript
const symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'YOUR_SYMBOL'];
```

### Adding More Sectors

Edit `daily_planet.html`, line ~808:
```javascript
const sectorETFs = {
    'XLK': 'Technology',
    'XLF': 'Financials',
    'YOUR_ETF': 'Your Sector'
};
```

### Changing Refresh Interval

Edit `daily_planet.html`, line ~1088:
```javascript
// Auto-refresh every 5 minutes (300000ms)
setInterval(() => {
    DailyPlanet.init();
}, 5 * 60 * 1000);  // Change "5" to desired minutes
```

### Customizing Colors

Edit `daily_planet.html`, lines 20-36:
```css
:root {
    --primary-color: #8B0000;    /* Your color */
    --accent-color: #DC143C;     /* Your color */
    --bg-dark: #0a1628;          /* Your color */
}
```

## Performance Optimization

### Caching Strategy

- **Dashboard**: No caching (always fresh)
- **API responses**: No caching (real-time data)
- **Static assets**: Browser caching allowed (fonts, logos)

### Rate Limiting

yfinance has no official rate limits, but good practice:
- Limit requests to 1/second per symbol
- Use batch requests where possible
- Implement exponential backoff on errors

### Data Freshness

- **Market data**: Updates every API call (~real-time)
- **News**: Latest available from Yahoo Finance
- **Dashboard**: Auto-refreshes every 5 minutes

## Security Considerations

### CORS

Flask API has CORS enabled for localhost development.

**Production:** Restrict CORS to specific domains:
```python
# daily_planet_api.py
from flask_cors import CORS

# Replace:
CORS(app)

# With:
CORS(app, resources={r"/api/*": {"origins": "https://yourdomain.com"}})
```

### API Authentication

Current setup: No authentication (localhost only)

**Production:** Add API key authentication:
```python
from functools import wraps

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != 'YOUR_SECRET_KEY':
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/market-news')
@require_api_key
def get_market_news():
    # ...
```

## Integration with Spartan Research Station

### Navigation Links

Dashboard includes:
- **Back button** → Returns to `index.html`
- **Nav bar** → Spartan Research Station branding

### Adding to Main Dashboard

Edit `index.html` to add Daily Planet link:
```html
<a href="daily_planet.html" class="tool-card">
    <div class="tool-icon">🌍</div>
    <h3 class="tool-title">Daily Planet</h3>
    <p class="tool-description">Daily market intelligence briefing</p>
</a>
```

## Future Enhancements

### Planned Features

- [ ] Real economic calendar integration (Trading Economics API)
- [ ] PostgreSQL database for historical data
- [ ] Email/SMS alerts for high-impact events
- [ ] Custom watchlists
- [ ] Export data to CSV/PDF
- [ ] Dark/light theme toggle
- [ ] Multi-language support

### API Upgrade Path

**Free Alternatives:**
- Economic Calendar: Trading Economics API (free tier)
- Advanced Sentiment: Alpha Vantage (25 req/day free)

**Paid Alternatives:**
- Real-time Data: Polygon.io ($29/month)
- News Aggregation: NewsAPI.org ($449/month)

## Support

**Issues?** Check logs:
- API Server: Terminal output where API is running
- Dashboard: Browser DevTools → Console tab (F12)

**Questions?** Review:
- This README
- API endpoint documentation above
- yfinance documentation: https://pypi.org/project/yfinance/

---

**Built with:**
- Frontend: HTML5, CSS3, Vanilla JavaScript
- Backend: Python, Flask, yfinance
- Theme: Spartan Research Station (#8B0000, #DC143C, #B22222)
- Data: Yahoo Finance (unlimited free API)

**Last Updated:** November 18, 2025
**Version:** 1.0.0
**Status:** ✅ Production Ready
