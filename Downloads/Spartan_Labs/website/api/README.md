# API Directory

This directory contains all API servers for the Spartan Research Station.

## API Servers

- correlation_api.py - Correlation matrix API (port 5004)
- daily_planet_api.py - News and insights API (port 5000)
- swing_dashboard_api.py - Swing trading timeframes API (port 5002)
- garp_api.py - GARP stock screener API (port 5003)
- crypto_composite_api.py - Crypto composite indicators
- cot_api.py - COT (Commitment of Traders) data
- marketaux_api.py - Market news aggregation

## Usage

Each API can be run standalone:
```bash
python -m api.correlation_api
```

Or use the unified startup:
```bash
./START_ALL.sh
```

