# Spartan Research Station - API Architecture

## Port Assignments

| Port | Server | File | Purpose |
|------|--------|------|---------|
| 5000 | Daily Planet API | daily_planet_api.py | Market news, highlights, economic calendar |
| 5002 | Swing Dashboard API | swing_dashboard_api.py | FRED data, swing trading indicators |
| 5003 | GARP API | garp_api.py | Growth at Reasonable Price stock screener |
| 5004 | Correlation API | correlation_api.py | Asset correlation matrix |
| 8888 | Main Server | start_server.py | Static files + symbol database API |

## Detailed Endpoints

### Port 5000 - Daily Planet API
Serves: daily_planet.html
