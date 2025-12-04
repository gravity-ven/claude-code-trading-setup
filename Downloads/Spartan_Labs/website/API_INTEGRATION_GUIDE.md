# Spartan Labs - Timeframe Data Modules API Integration Guide

## 🎯 Complete Integration Roadmap

This guide shows you **exactly** how to integrate the timeframe-specific data modules into your trading application.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Module Integration](#module-integration)
4. [Real API Endpoints](#real-api-endpoints)
5. [Example Implementations](#example-implementations)
6. [PostgreSQL Setup](#postgresql-setup)
7. [Production Deployment](#production-deployment)

---

## 1. Prerequisites

### Required Files
```
website/
├── js/
│   ├── fred_api_client.js              ✅ REQUIRED
│   ├── timeframe_data_fetcher_1_2_weeks.js
│   ├── timeframe_data_fetcher_1_3_months.js
│   ├── timeframe_data_fetcher_6_18_months.js
│   └── timeframe_data_fetcher_18_36_months.js
├── start_server.py                      ✅ REQUIRED (Port 8888)
└── simple_server.py                     ✅ ALTERNATIVE (Port 9000)
```

### Required Python Packages
```bash
pip install flask flask-cors requests pandas psycopg2-binary
```

### Optional: PostgreSQL
```bash
# Install PostgreSQL 13+
# Windows: https://www.postgresql.org/download/windows/
# WSL: sudo apt install postgresql

# Create database
createdb spartan_research
```

---

## 2. Server Setup

### Option A: Full-Featured Server (Port 8888)
```bash
# Start main server with all API proxies
python3 start_server.py
```

**Features**:
- FRED API proxy (`/api/fred/*`)
- Yahoo Finance proxy (`/api/yahoo/*`)
- BLS.gov proxy (`/api/bls/*`)
- PostgreSQL database API (`/api/db/*`)
- CORS enabled
- Cache-control headers

### Option B: Simple Server (Port 9000)
```bash
# Start simple JSON-based server
python3 simple_server.py
```

**Features**:
- Static file serving
- JSON database mode (no PostgreSQL required)
- Basic API endpoints
- CORS enabled

### Verify Server
```bash
# Test server status
curl http://localhost:8888/api/server/status

# Expected response:
{
    "status": "ok",
    "timestamp": "2025-11-16T12:00:00",
    "platform": "Linux",
    "python_version": "3.13.0"
}
```

---

## 3. Module Integration

### Step 1: Include Dependencies
```html
<!DOCTYPE html>
<html>
<head>
    <title>Swing Trading Dashboard</title>
</head>
<body>
    <!-- FRED API Client (REQUIRED) -->
    <script src="js/fred_api_client.js"></script>

    <!-- Timeframe Modules -->
    <script src="js/timeframe_data_fetcher_1_2_weeks.js"></script>
    <script src="js/timeframe_data_fetcher_1_3_months.js"></script>
    <script src="js/timeframe_data_fetcher_6_18_months.js"></script>
    <script src="js/timeframe_data_fetcher_18_36_months.js"></script>

    <!-- Your application code -->
    <script src="app.js"></script>
</body>
</html>
```

### Step 2: Initialize Modules
```javascript
// app.js

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Initializing Spartan Trading Dashboard...');

    // Initialize all timeframe fetchers
    const fetchers = {
        shortTerm: new TimeframeDataFetcher_1_2_Weeks(),
        intermediate: new TimeframeDataFetcher_1_3_Months(),
        position: new TimeframeDataFetcher_6_18_Months(),
        longTerm: new TimeframeDataFetcher_18_36_Months()
    };

    console.log('✅ All modules loaded');

    // Fetch data for active timeframe
    await loadTimeframeData('shortTerm');
});

async function loadTimeframeData(timeframe) {
    const fetcher = fetchers[timeframe];

    console.log(`📊 Loading ${timeframe} data...`);

    try {
        const result = await fetcher.fetchAllData();

        if (result.success) {
            console.log('✅ Data loaded:', result.data);
            displayData(result.data);
        } else {
            console.error('❌ Failed to load data:', result.error);
            showError(result.error);
        }
    } catch (error) {
        console.error('❌ Exception:', error);
        showError(error.message);
    }
}

function displayData(data) {
    // Update UI with data
    document.getElementById('timeframe').textContent = data.timeframe;
    document.getElementById('timestamp').textContent = data.timestamp;

    // Display signals
    if (data.signals) {
        document.getElementById('direction').textContent = data.signals.direction;
        document.getElementById('strength').textContent = data.signals.strength;
        document.getElementById('confidence').textContent = data.signals.confidence;
    }
}

function showError(message) {
    document.getElementById('error').textContent = message;
    document.getElementById('error').style.display = 'block';
}
```

---

## 4. Real API Endpoints

### FRED API Proxy

#### Get Series Observations
```javascript
// Via proxy (no CORS issues)
const response = await fetch('/api/fred/series/observations?series_id=GDP');
const data = await response.json();

console.log(data.observations);
```

#### Get Series Metadata
```javascript
const response = await fetch('/api/fred/series?series_id=UNRATE');
const data = await response.json();

console.log(data.seriess[0]);
// {
//   id: "UNRATE",
//   title: "Unemployment Rate",
//   units: "Percent",
//   frequency: "Monthly",
//   seasonal_adjustment: "Seasonally Adjusted",
//   observation_start: "1948-01-01",
//   observation_end: "2025-10-01",
//   last_updated: "2025-11-01 07:44:01-05"
// }
```

#### Search Series
```javascript
const response = await fetch('/api/fred/series/search?search_text=inflation&limit=10');
const data = await response.json();

console.log(data.seriess);
```

### Yahoo Finance Proxy

#### Get Quote
```javascript
const response = await fetch('/api/yahoo/quote?symbols=AAPL,MSFT,GOOGL');
const data = await response.json();

console.log(data.quoteResponse.result);
// [
//   {
//     symbol: "AAPL",
//     regularMarketPrice: 189.50,
//     regularMarketChange: 2.35,
//     regularMarketChangePercent: 1.26,
//     regularMarketVolume: 45231000,
//     ...
//   }
// ]
```

#### Get Chart Data
```javascript
const response = await fetch('/api/yahoo/chart/SPY?interval=1d&range=3mo');
const data = await response.json();

const chart = data.chart.result[0];
console.log(chart.timestamp);  // Unix timestamps
console.log(chart.indicators.quote[0].close);  // Closing prices
```

### Database API

#### Search Symbols
```javascript
const response = await fetch('/api/db/search?query=AAPL&limit=100');
const data = await response.json();

console.log(data.results);
// [
//   {
//     symbol: "AAPL",
//     name: "Apple Inc.",
//     exchange: "NASDAQ",
//     sector: "Technology",
//     marketCap: "3.5T"
//   }
// ]
```

#### Get Database Stats
```javascript
const response = await fetch('/api/db/stats');
const data = await response.json();

console.log(data);
// {
//   total_symbols: 13000,
//   stocks: 12200,
//   futures: 43,
//   forex: 41,
//   crypto: 250,
//   etfs: 100,
//   indices: 18
// }
```

---

## 5. Example Implementations

### Example 1: Simple Trading Signals Dashboard

```html
<!DOCTYPE html>
<html>
<head>
    <title>Trading Signals</title>
    <style>
        .signal-box {
            padding: 20px;
            margin: 10px;
            border-radius: 8px;
        }
        .bullish { background: #00ff88; color: #000; }
        .bearish { background: #ff6b6b; color: #fff; }
        .neutral { background: #ffa500; color: #000; }
    </style>
</head>
<body>
    <h1>1-2 Week Trading Signals</h1>

    <div id="signal-box" class="signal-box">
        <h2 id="direction">Loading...</h2>
        <p>Strength: <span id="strength">--</span>/100</p>
        <p>Confidence: <span id="confidence">--</span>/100</p>
        <ul id="factors"></ul>
        <h3>Recommendations:</h3>
        <ul id="recommendations"></ul>
    </div>

    <script src="js/fred_api_client.js"></script>
    <script src="js/timeframe_data_fetcher_1_2_weeks.js"></script>

    <script>
        async function loadSignals() {
            const fetcher = new TimeframeDataFetcher_1_2_Weeks();
            const result = await fetcher.fetchAllData();

            if (result.success) {
                const signals = result.data.signals;

                // Update direction with color coding
                const box = document.getElementById('signal-box');
                box.className = `signal-box ${signals.direction}`;

                document.getElementById('direction').textContent =
                    signals.direction.toUpperCase();
                document.getElementById('strength').textContent = signals.strength;
                document.getElementById('confidence').textContent = signals.confidence;

                // Populate factors
                const factorsList = document.getElementById('factors');
                factorsList.innerHTML = '';
                signals.factors.forEach(factor => {
                    const li = document.createElement('li');
                    li.textContent = factor;
                    factorsList.appendChild(li);
                });

                // Populate recommendations
                const recList = document.getElementById('recommendations');
                recList.innerHTML = '';
                signals.recommendations.forEach(rec => {
                    const li = document.createElement('li');
                    li.textContent = rec;
                    recList.appendChild(li);
                });
            }
        }

        loadSignals();
        setInterval(loadSignals, 15 * 60 * 1000); // Refresh every 15 minutes
    </script>
</body>
</html>
```

### Example 2: Multi-Timeframe Dashboard

```javascript
// Multi-timeframe analysis
async function analyzeAllTimeframes() {
    const timeframes = {
        '1-2 weeks': new TimeframeDataFetcher_1_2_Weeks(),
        '1-3 months': new TimeframeDataFetcher_1_3_Months(),
        '6-18 months': new TimeframeDataFetcher_6_18_Months(),
        '18-36 months': new TimeframeDataFetcher_18_36_Months()
    };

    const results = {};

    for (const [name, fetcher] of Object.entries(timeframes)) {
        console.log(`📊 Analyzing ${name}...`);
        const data = await fetcher.fetchAllData();

        if (data.success) {
            results[name] = {
                signals: data.data.signals || data.data.analysis,
                timestamp: data.data.timestamp
            };
        }
    }

    return results;
}

// Usage
analyzeAllTimeframes().then(results => {
    console.log('All Timeframes:', results);

    // Check alignment across timeframes
    const shortTerm = results['1-2 weeks'].signals.direction;
    const intermediate = results['1-3 months'].analysis.marketTrend;
    const longTerm = results['6-18 months'].analysis.marketPhase;

    if (shortTerm === 'bullish' && intermediate === 'bullish' && longTerm === 'bull_market') {
        console.log('✅ STRONG BULL SIGNAL - All timeframes aligned');
    }
});
```

### Example 3: Economic Dashboard

```javascript
// Economic cycle tracker
async function trackEconomicCycle() {
    const longTerm = new TimeframeDataFetcher_18_36_Months();
    const data = await longTerm.fetchAllData();

    if (data.success) {
        const cycle = data.data.cycle;

        console.log('=== ECONOMIC CYCLE ANALYSIS ===');
        console.log(`Phase: ${cycle.phase}`);
        console.log(`Unemployment: ${cycle.unemployment.current}%`);
        console.log(`Unemployment Trend: ${cycle.unemployment.trend}`);
        console.log(`Leading Indicators: ${cycle.leadingIndicators.signal}`);

        if (cycle.yieldCurve.inverted) {
            console.log('⚠️  RECESSION WARNING: Yield curve inverted');
            console.log(`   Inversion Duration: ${cycle.yieldCurve.inversionDuration} months`);
            console.log(`   Recession Probability: ${cycle.yieldCurve.recessionProbability}`);
        }

        // Strategic recommendations
        const analysis = data.data.analysis;
        console.log('\n=== STRATEGIC RECOMMENDATIONS ===');
        analysis.strategicRecommendations.forEach(rec => {
            console.log(`- ${rec}`);
        });
    }
}
```

---

## 6. PostgreSQL Setup

### Database Schema
```sql
-- Create database
CREATE DATABASE spartan_research;

-- Connect to database
\c spartan_research

-- Create timeframe data table
CREATE TABLE timeframe_data (
    id SERIAL PRIMARY KEY,
    timeframe VARCHAR(50) NOT NULL,
    data_type VARCHAR(50) NOT NULL,  -- 'signals', 'markets', 'economic', etc.
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_timeframe ON timeframe_data(timeframe);
CREATE INDEX idx_data_type ON timeframe_data(data_type);
CREATE INDEX idx_created_at ON timeframe_data(created_at DESC);

-- Create function to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
CREATE TRIGGER update_timeframe_data_updated_at
BEFORE UPDATE ON timeframe_data
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
```

### Python Integration
```python
# save_to_database.py
import psycopg2
import json
from psycopg2.extras import RealDictCursor

def save_timeframe_data(timeframe, data_type, data):
    """Save timeframe data to PostgreSQL"""
    conn = psycopg2.connect(
        dbname="spartan_research",
        user="postgres",
        password="spartan123",
        host="localhost",
        port="5432"
    )

    cursor = conn.cursor()

    # Insert or update
    cursor.execute("""
        INSERT INTO timeframe_data (timeframe, data_type, data)
        VALUES (%s, %s, %s)
        ON CONFLICT (timeframe, data_type)
        DO UPDATE SET
            data = EXCLUDED.data,
            updated_at = NOW()
    """, (timeframe, data_type, json.dumps(data)))

    conn.commit()
    cursor.close()
    conn.close()

def get_timeframe_data(timeframe, data_type):
    """Retrieve timeframe data from PostgreSQL"""
    conn = psycopg2.connect(
        dbname="spartan_research",
        user="postgres",
        password="spartan123",
        host="localhost",
        port="5432"
    )

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT data, created_at, updated_at
        FROM timeframe_data
        WHERE timeframe = %s AND data_type = %s
        ORDER BY updated_at DESC
        LIMIT 1
    """, (timeframe, data_type))

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result
```

### API Endpoint
```python
# In start_server.py
from flask import Flask, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

@app.route('/api/timeframe/<timeframe>/<data_type>', methods=['GET'])
def get_timeframe_data(timeframe, data_type):
    try:
        conn = psycopg2.connect(
            dbname="spartan_research",
            user="postgres",
            password="spartan123",
            host="localhost",
            port="5432"
        )

        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT data, created_at, updated_at
            FROM timeframe_data
            WHERE timeframe = %s AND data_type = %s
            ORDER BY updated_at DESC
            LIMIT 1
        """, (timeframe, data_type))

        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            return jsonify({
                'success': True,
                'data': result['data'],
                'created_at': result['created_at'].isoformat(),
                'updated_at': result['updated_at'].isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Data not found'
            }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

---

## 7. Production Deployment

### Environment Variables
```bash
# .env
FRED_API_KEY=a6137538793a55227cbae2119e1573f5
ALPHA_VANTAGE_API_KEY=UEIUKSPCUK1N5432
DATABASE_URL=postgresql://postgres:spartan123@localhost:5432/spartan_research
PORT=8888
CACHE_TTL=900
```

### Load Environment Variables
```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

FRED_API_KEY = os.getenv('FRED_API_KEY')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
PORT = int(os.getenv('PORT', 8888))
CACHE_TTL = int(os.getenv('CACHE_TTL', 900))
```

### Systemd Service (Linux)
```ini
# /etc/systemd/system/spartan-server.service
[Unit]
Description=Spartan Research Server
After=network.target postgresql.service

[Service]
Type=simple
User=spartan
WorkingDirectory=/home/spartan/website
Environment="PATH=/home/spartan/website/venv/bin"
ExecStart=/home/spartan/website/venv/bin/python3 start_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable spartan-server
sudo systemctl start spartan-server
sudo systemctl status spartan-server
```

### Docker Deployment
```dockerfile
# Dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8888

CMD ["python3", "start_server.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  spartan-server:
    build: .
    ports:
      - "8888:8888"
    environment:
      - FRED_API_KEY=${FRED_API_KEY}
      - DATABASE_URL=postgresql://postgres:spartan123@db:5432/spartan_research
    depends_on:
      - db
    volumes:
      - ./data:/app/data

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=spartan_research
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=spartan123
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

```bash
# Deploy with Docker
docker-compose up -d
```

---

## 🎯 Next Steps

1. ✅ Start server (`python3 start_server.py`)
2. ✅ Test API endpoints (`curl http://localhost:8888/api/server/status`)
3. ✅ Load modules in HTML page
4. ✅ Fetch data (`await fetcher.fetchAllData()`)
5. ✅ Display results in UI
6. ✅ Set up PostgreSQL (optional)
7. ✅ Deploy to production

---

**Last Updated**: 2025-11-16
**Support**: Check browser console for detailed error logs
**Zero Fake Data**: Guaranteed - all data from real APIs
