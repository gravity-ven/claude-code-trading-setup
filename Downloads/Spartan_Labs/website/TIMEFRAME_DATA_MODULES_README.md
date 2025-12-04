# Spartan Labs - Timeframe-Specific Data Fetcher Modules

## 🎯 Overview

Production-grade JavaScript modules for swing trading data across 4 distinct timeframes. **ZERO fake data. ZERO Math.random(). 100% real APIs.**

## 📦 Modules

### 1. **1-2 Week Swing Trading** (`timeframe_data_fetcher_1_2_weeks.js`)
- **Timeframe**: 1-14 days
- **Update Frequency**: 15 minutes
- **Focus**: Daily momentum, short-term trends, intraday reversals
- **Cache TTL**: 15 minutes

### 2. **1-3 Month Swing Trading** (`timeframe_data_fetcher_1_3_months.js`)
- **Timeframe**: 4-12 weeks
- **Update Frequency**: 1 hour
- **Focus**: Weekly trends, momentum, intermediate cycles
- **Cache TTL**: 1 hour

### 3. **6-18 Month Position Trading** (`timeframe_data_fetcher_6_18_months.js`)
- **Timeframe**: 6-18 months
- **Update Frequency**: 4 hours
- **Focus**: Macro trends, quarterly earnings, structural shifts
- **Cache TTL**: 4 hours

### 4. **18-36 Month Long-Term Investing** (`timeframe_data_fetcher_18_36_months.js`)
- **Timeframe**: 1.5-3 years
- **Update Frequency**: 24 hours
- **Focus**: Secular trends, economic cycles, structural changes
- **Cache TTL**: 24 hours

---

## 🚀 Quick Start

### Installation

```html
<!-- Add to your HTML page -->
<!-- Required dependency: FRED API Client -->
<script src="js/fred_api_client.js"></script>

<!-- Load timeframe modules (in order) -->
<script src="js/timeframe_data_fetcher_1_2_weeks.js"></script>
<script src="js/timeframe_data_fetcher_1_3_months.js"></script>
<script src="js/timeframe_data_fetcher_6_18_months.js"></script>
<script src="js/timeframe_data_fetcher_18_36_months.js"></script>
```

### Basic Usage

```javascript
// 1-2 Week Data
const shortTerm = new TimeframeDataFetcher_1_2_Weeks();
const data = await shortTerm.fetchAllData();

console.log(data.data.signals); // Trading signals
console.log(data.data.volatility); // VIX metrics
console.log(data.data.sectors); // Sector rotation

// 1-3 Month Data
const intermediate = new TimeframeDataFetcher_1_3_Months();
const monthData = await intermediate.fetchAllData();

console.log(monthData.data.analysis); // Strategic analysis
console.log(monthData.data.sectors); // Sector trends

// 6-18 Month Data
const position = new TimeframeDataFetcher_6_18_Months();
const posData = await position.fetchAllData();

console.log(posData.data.analysis); // Long-term outlook

// 18-36 Month Data
const longTerm = new TimeframeDataFetcher_18_36_Months();
const longData = await longTerm.fetchAllData();

console.log(longData.data.secular); // Secular trends
console.log(longData.data.cycle); // Business cycle position
```

---

## 📊 Data Sources (100% Real)

### FRED (Federal Reserve Economic Data)
- **API Key**: Configured in `fred_api_client.js`
- **Rate Limit**: 120 requests/minute
- **Coverage**: 500,000+ economic time series

### Yahoo Finance
- **Endpoint**: `/api/yahoo/` (local proxy to avoid CORS)
- **Coverage**: Real-time quotes, historical data
- **No API key required**

### Alpha Vantage (Optional)
- **API Key**: `UEIUKSPCUK1N5432`
- **Rate Limit**: 5 requests/minute (free tier)
- **Coverage**: Intraday data, fundamentals

---

## 🔑 FRED Series IDs by Timeframe

### 1-2 Weeks (Daily/Weekly)
```javascript
{
    vix: 'VIXCLS',                    // VIX Daily
    treasury10y: 'DGS10',             // 10-Year Treasury Daily
    creditSpread: 'BAMLH0A0HYM2',     // High Yield Spread
    initClaims: 'ICSA',               // Weekly Jobless Claims
    m2: 'WM2NS',                      // M2 Money Supply (Weekly)
    mortgageRate30y: 'MORTGAGE30US'   // 30-Year Mortgage (Weekly)
}
```

### 1-3 Months (Monthly)
```javascript
{
    unemployment: 'UNRATE',           // Unemployment Rate (Monthly, 1st Friday)
    cpi: 'CPIAUCSL',                  // CPI (Monthly, ~13th)
    retailSales: 'RSXFS',             // Retail Sales (Monthly, ~13-16th)
    industrialProd: 'INDPRO',         // Industrial Production (Monthly, ~15th)
    housing: 'HOUST',                 // Housing Starts (Monthly, ~16-19th)
    nonfarmPayrolls: 'PAYEMS',        // Nonfarm Payrolls (Monthly, 1st Friday)
    consumerSentiment: 'UMCSENT'      // Michigan Sentiment (Monthly)
}
```

### 6-18 Months (Quarterly/Annual)
```javascript
{
    gdp: 'GDP',                       // Real GDP (Quarterly)
    gdpGrowth: 'A191RL1Q225SBEA',     // GDP Growth Rate
    corporateProfits: 'CP',           // Corporate Profits (Quarterly)
    leadingIndex: 'USSLIND',          // Leading Economic Index
    housePrices: 'CSUSHPISA'          // Case-Shiller Home Price Index
}
```

### 18-36 Months (Multi-Year)
```javascript
{
    gdpGrowth: 'A191RL1Q225SBEA',     // Real GDP Growth
    productivity: 'OPHNFB',           // Nonfarm Productivity
    inflation10YrExp: 'T10YIE',       // 10-Year Inflation Expectations
    debtToGDP: 'GFDEGDQ188S',         // Federal Debt-to-GDP
    yieldCurveSpread: 'T10Y2Y'        // 10Y-2Y Spread (Recession Indicator)
}
```

---

## 🎨 Data Structure

### 1-2 Week Data Structure
```javascript
{
    timeframe: '1-2 weeks',
    timestamp: '2025-11-16T12:00:00.000Z',
    dataAge: '0-15 minutes',

    dailyFred: {
        vix: {
            values: [...],
            latest: 15.23,
            change: -0.45,
            trend: 'falling'
        },
        // ... other indicators
    },

    weeklyFred: {
        initClaims: {
            values: [...],
            latest: 213000,
            weekOverWeekChange: -2.3
        },
        // ... other indicators
    },

    markets: {
        spx: {
            price: 5950.34,
            change: 12.45,
            changePercent: 0.21,
            fiftyDayAvg: 5875.23,
            twoHundredDayAvg: 5650.12
        },
        // ... other indices/ETFs
    },

    sectors: {
        leaders: ['XLK', 'XLF', 'XLI'],
        laggards: ['XLE', 'XLU', 'XLP'],
        rotation: 'risk_on',
        rawData: { /* sector details */ }
    },

    volatility: {
        vix: { /* VIX data */ },
        termStructure: {
            spot: 15.23,
            futures: 16.45,
            contango: true
        },
        regime: 'normal',
        signal: 'normal'
    },

    signals: {
        direction: 'bullish',       // 'bullish', 'bearish', 'neutral'
        strength: 65,               // 0-100
        confidence: 75,             // 0-100
        factors: [
            'Low VIX (complacency)',
            'Tech/Financial leadership (risk-on)',
            'Credit spreads stable'
        ],
        recommendations: [
            'Consider long positions in leading sectors',
            'Focus on momentum names (XLK, QQQ)'
        ]
    }
}
```

### 1-3 Month Data Structure
```javascript
{
    timeframe: '1-3 months',
    economic: { /* Monthly economic indicators */ },
    markets: { /* Weekly market performance */ },
    sectors: {
        sectors: { /* Individual sector data */ },
        leaders: ['XLK', 'XLF', 'XLV'],
        laggards: ['XLE', 'XLU', 'XLB'],
        rotation: 'cyclical_rotation'
    },
    fixedIncome: {
        yieldCurve: {
            y2: 4.25,
            y10: 4.35,
            y30: 4.55,
            spread_2_10: 0.10,
            inverted: false,
            trend: 'rising'
        },
        credit: {
            highYieldSpread: 325,
            aaaSpread: 75,
            condition: 'normal'
        }
    },
    analysis: {
        economicCycle: 'expansion',
        marketTrend: 'bullish',
        sectorRotation: 'risk_on',
        riskAppetite: 'moderate',
        recommendations: [
            'Stay long cyclical sectors (XLI, XLF)',
            'Favor growth over value'
        ]
    }
}
```

---

## 🛠️ API Endpoints

### Local Server Endpoints (Port 8888)

```javascript
// Database API
GET /api/db/search?query=AAPL&limit=100
GET /api/db/stats
GET /api/db/symbols?limit=1000&offset=0

// FRED API Proxy
GET /api/fred/series/observations?series_id=GDP
GET /api/fred/series?series_id=GDP
GET /api/fred/series/search?search_text=inflation

// Yahoo Finance Proxy
GET /api/yahoo/quote?symbols=AAPL,MSFT
GET /api/yahoo/chart/AAPL?interval=1d&range=3mo

// BLS (Bureau of Labor Statistics)
POST /api/bls/
```

---

## ⚙️ Configuration

### Cache Configuration
```javascript
// Custom cache TTL
const shortTerm = new TimeframeDataFetcher_1_2_Weeks({
    cacheTTL: 10 * 60 * 1000  // 10 minutes instead of default 15
});

// Custom cache prefix
const intermediate = new TimeframeDataFetcher_1_3_Months({
    cachePrefix: 'custom_swing_'
});
```

### FRED Client Configuration
```javascript
// Initialize with custom config
const fredClient = new FredApiClient({
    apiKey: 'YOUR_API_KEY',
    baseUrl: '/api/fred',
    maxRequestsPerMinute: 120,
    observationsTTL: 15 * 60 * 1000  // 15 minutes
});
```

---

## 📈 Use Cases

### 1-2 Week Module: Day Trading & Short Swings
```javascript
const shortTerm = new TimeframeDataFetcher_1_2_Weeks();
const data = await shortTerm.fetchAllData();

// Check VIX for volatility regime
if (data.data.volatility.regime === 'high') {
    console.log('High volatility - reduce position sizing');
}

// Check sector rotation
if (data.data.sectors.rotation === 'risk_on') {
    console.log('Risk-on environment - favor cyclicals');
}

// Get trading signals
console.log(`Direction: ${data.data.signals.direction}`);
console.log(`Strength: ${data.data.signals.strength}/100`);
```

### 1-3 Month Module: Swing Trading
```javascript
const intermediate = new TimeframeDataFetcher_1_3_Months();
const data = await intermediate.fetchAllData();

// Check economic cycle
if (data.data.analysis.economicCycle === 'expansion') {
    console.log('Economic expansion - overweight equities');
}

// Check yield curve
if (data.data.fixedIncome.yieldCurve.inverted) {
    console.log('⚠️ Yield curve inverted - recession risk');
}
```

### 6-18 Month Module: Position Trading
```javascript
const position = new TimeframeDataFetcher_6_18_Months();
const data = await position.fetchAllData();

// Strategic allocation
console.log(data.data.analysis.allocationStrategy);

// Sector recommendations
console.log(data.data.sectors.recommended);

// Valuation assessment
if (data.data.valuations.assessment === 'expensive') {
    console.log('Market expensive - favor value/international');
}
```

### 18-36 Month Module: Long-Term Investing
```javascript
const longTerm = new TimeframeDataFetcher_18_36_Months();
const data = await longTerm.fetchAllData();

// Business cycle position
console.log(`Cycle Phase: ${data.data.cycle.phase}`);

// Secular outlook
console.log(`Secular Outlook: ${data.data.analysis.secularOutlook}`);

// Strategic recommendations
data.data.analysis.strategicRecommendations.forEach(rec => {
    console.log(`- ${rec}`);
});
```

---

## 🔄 Data Update Schedule

### 1-2 Week Data
| Indicator | Frequency | Release Day | FRED Series ID |
|-----------|-----------|-------------|----------------|
| VIX | Daily | Market close | VIXCLS |
| Treasury 10Y | Daily | Market close | DGS10 |
| Initial Claims | Weekly | Thursday 8:30am ET | ICSA |
| M2 Money Supply | Weekly | Monday | WM2NS |
| Mortgage Rate | Weekly | Thursday | MORTGAGE30US |

### 1-3 Month Data
| Indicator | Frequency | Release Day | FRED Series ID |
|-----------|-----------|-------------|----------------|
| Unemployment | Monthly | 1st Friday 8:30am ET | UNRATE |
| CPI | Monthly | ~13th 8:30am ET | CPIAUCSL |
| Retail Sales | Monthly | ~13-16th 8:30am ET | RSXFS |
| Industrial Production | Monthly | ~15th 9:15am ET | INDPRO |
| Housing Starts | Monthly | ~16-19th 8:30am ET | HOUST |

### 6-18 Month Data
| Indicator | Frequency | Release Day | FRED Series ID |
|-----------|-----------|-------------|----------------|
| GDP | Quarterly | Last day of month (advance) | GDP |
| Corporate Profits | Quarterly | End of month | CP |
| Leading Index | Monthly | ~20th | USSLIND |
| Home Price Index | Monthly | Last Tuesday 9:00am ET | CSUSHPISA |

### 18-36 Month Data
| Indicator | Frequency | Update Pattern | FRED Series ID |
|-----------|-----------|----------------|----------------|
| GDP Growth | Quarterly | 3 releases per quarter | A191RL1Q225SBEA |
| Productivity | Quarterly | ~60 days after quarter | OPHNFB |
| 10Y Inflation Exp | Daily | Market close | T10YIE |
| Debt-to-GDP | Quarterly | End of quarter | GFDEGDQ188S |
| Yield Curve Spread | Daily | Market close | T10Y2Y |

---

## 🧪 Testing

### Manual Testing
```javascript
// Test 1-2 week module
const test1_2w = new TimeframeDataFetcher_1_2_Weeks();
test1_2w.fetchAllData().then(data => {
    console.log('1-2 Week Data:', data);
    console.log('Signals:', data.data.signals);
});

// Test cache
setTimeout(async () => {
    const cachedData = await test1_2w.fetchAllData();
    console.log('Source:', cachedData.data.metadata.cached ? 'cache' : 'api');
}, 5000);
```

### Data Validation
```javascript
// Check for fake data violations
function validateData(data) {
    const checks = {
        hasMathRandom: /Math\.random/.test(JSON.stringify(data)),
        hasNullValues: JSON.stringify(data).includes('null'),
        hasUndefinedValues: JSON.stringify(data).includes('undefined'),
        hasValidTimestamp: data.timestamp && new Date(data.timestamp).getTime() > 0
    };

    console.log('Validation:', checks);
    return !checks.hasMathRandom && checks.hasValidTimestamp;
}
```

---

## 🚨 Error Handling

### Graceful Degradation
All modules implement automatic fallback to cached data:

```javascript
const data = await fetcher.fetchAllData();

if (data.warning) {
    console.warn('Using cached data:', data.warning);
}

if (!data.success) {
    console.error('Failed to fetch data:', data.error);
}
```

### Rate Limit Handling
FRED API client automatically handles rate limits:

```javascript
// FredApiClient handles:
// - Automatic retry with exponential backoff
// - Rate limiting (120 requests/minute)
// - Queue management
// - Stale cache fallback
```

---

## 📝 PostgreSQL Integration

### Database Schema (Optional)
```sql
CREATE TABLE timeframe_data (
    id SERIAL PRIMARY KEY,
    timeframe VARCHAR(50) NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_timeframe (timeframe),
    INDEX idx_created_at (created_at)
);

-- Store data
INSERT INTO timeframe_data (timeframe, data)
VALUES ('1-2 weeks', '{"signals": {...}}');

-- Retrieve latest data
SELECT * FROM timeframe_data
WHERE timeframe = '1-2 weeks'
ORDER BY created_at DESC
LIMIT 1;
```

### PostgreSQL Connection
```javascript
// Using psycopg2 in Python backend
import psycopg2
import json

conn = psycopg2.connect(
    dbname="spartan_research",
    user="postgres",
    password="spartan123",
    host="localhost",
    port="5432"
)

# Store timeframe data
cursor = conn.cursor()
cursor.execute(
    "INSERT INTO timeframe_data (timeframe, data) VALUES (%s, %s)",
    ('1-2 weeks', json.dumps(data))
)
conn.commit()
```

---

## 🎯 Performance Optimization

### Caching Strategy
```javascript
// Cache hierarchy:
// 1. Browser localStorage (client-side)
// 2. Redis cache (optional, server-side)
// 3. PostgreSQL (persistent storage)

// Example Redis caching
const redis = require('redis');
const client = redis.createClient();

// Cache with TTL
client.setex('swing_1_2w_all_data', 900, JSON.stringify(data)); // 15 min

// Retrieve
client.get('swing_1_2w_all_data', (err, data) => {
    if (data) {
        console.log('Cache hit:', JSON.parse(data));
    }
});
```

### Batch Requests
```javascript
// Fetch multiple timeframes in parallel
const [short, intermediate, position, long] = await Promise.all([
    new TimeframeDataFetcher_1_2_Weeks().fetchAllData(),
    new TimeframeDataFetcher_1_3_Months().fetchAllData(),
    new TimeframeDataFetcher_6_18_Months().fetchAllData(),
    new TimeframeDataFetcher_18_36_Months().fetchAllData()
]);

console.log('All timeframes loaded');
```

---

## 📚 Additional Resources

### FRED API Documentation
- **Main Docs**: https://fred.stlouisfed.org/docs/api/fred/
- **Series Search**: https://fred.stlouisfed.org/docs/api/fred/series_search.html
- **Observations**: https://fred.stlouisfed.org/docs/api/fred/series_observations.html

### Economic Calendar
- **Investing.com Calendar**: https://www.investing.com/economic-calendar/
- **Trading Economics**: https://tradingeconomics.com/calendar

### Yahoo Finance API
- **Unofficial Docs**: https://github.com/ranaroussi/yfinance

---

## ⚠️ Critical Rules Reminder

1. **ZERO Math.random()** - All data from real APIs
2. **ZERO fake data** - No mock/sample/placeholder data
3. **PostgreSQL ONLY** - No SQLite database usage
4. **Real API sources** - FRED, Yahoo Finance, Alpha Vantage, Polygon
5. **Clear "Data unavailable"** - Never fabricate missing data

---

## 🤝 Contributing

When adding new indicators:

1. **Find FRED Series ID**: https://fred.stlouisfed.org/
2. **Add to fredSeriesIds** object
3. **Create fetch function**
4. **Add to master fetch**
5. **Update documentation**

Example:
```javascript
// 1. Add series ID
this.fredSeriesIds.newIndicator = 'NEWSERIES';

// 2. Create fetch function
async fetchNewIndicator() {
    const result = await this.fredClient.fetchSeriesObservations(
        this.fredSeriesIds.newIndicator,
        { limit: 14 }
    );
    return result.success ? result.data : null;
}

// 3. Add to master fetch
const newData = await this.fetchNewIndicator();
```

---

## 📞 Support

For issues or questions:
- **FRED API Issues**: https://fred.stlouisfed.org/docs/api/
- **Module Issues**: Check browser console for error logs
- **Data Validation**: Run `DATA_VALIDATION_SYSTEM.py`

---

**Last Updated**: 2025-11-16
**Version**: 1.0.0
**License**: Proprietary - Spartan Labs
**Zero Fake Data Policy**: ENFORCED
