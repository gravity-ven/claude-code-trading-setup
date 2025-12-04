# Market Highlights API

Backend API server for the Spartan Research Station Market Highlights Dashboard.

## Features

- Real-time market data from yfinance API
- NO FAKE DATA - All data from actual markets
- Fast batch fetching for multiple symbols
- CORS enabled for frontend integration

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Start the API server
python highlights_api.py
```

Server will run on: http://localhost:5000

## Endpoints

### Single Symbol Data
```
GET /api/highlights/symbol/<SYMBOL>

Example: http://localhost:5000/api/highlights/symbol/AAPL

Response:
{
  "symbol": "AAPL",
  "name": "Apple Inc.",
  "price": 150.25,
  "change": 2.50,
  "changePercent": 1.69,
  "volume": 52341000,
  "timestamp": "2025-11-18T10:30:00"
}
```

### Batch Symbol Data
```
POST /api/highlights/batch

Body:
{
  "symbols": ["AAPL", "MSFT", "GOOGL"]
}

Response:
{
  "data": [...],
  "errors": [],
  "timestamp": "2025-11-18T10:30:00"
}
```

### Health Check
```
GET /api/highlights/health

Response:
{
  "status": "healthy",
  "service": "Market Highlights API",
  "timestamp": "2025-11-18T10:30:00",
  "data_source": "yfinance (real market data)"
}
```

## Data Source

- **Primary**: yfinance (unlimited requests)
- **Data Type**: Real-time market quotes
- **Coverage**: All major US stocks and ETFs

## Integration with Frontend

The highlights.html dashboard is configured to connect to this API automatically.

1. Start the API server: `python highlights_api.py`
2. Open highlights.html in a browser
3. Dashboard will fetch real-time data every 60 seconds

## NO FAKE DATA Policy

This API serves ONLY real market data. If a symbol cannot be fetched, it will return NULL or error - never fake data.
