# Development Workflow - Native Mode (No Docker)

This guide explains how to develop **without Docker** for faster iteration and easier debugging.

## Why Native Development?

**Docker is great for production**, but painful for active development:

| Docker | Native |
|--------|--------|
| 45-85 second startup | 5-10 second startup |
| Container rebuild after changes | Changes take effect immediately |
| `docker exec` for debugging | Direct Python debugger access |
| Preloader blocks entire system | Services run independently |
| Complex logs (`docker-compose logs`) | Direct log files |

**Use native development during active coding, Docker for production/distribution.**

---

## Initial Setup (One-Time)

### 1. Install Dependencies

**Linux/WSL:**
```bash
# Install PostgreSQL and Redis
sudo apt update
sudo apt install postgresql postgresql-contrib redis-server

# Start services
sudo service postgresql start
sudo service redis-server start
```

**macOS:**
```bash
# Install PostgreSQL and Redis
brew install postgresql redis

# Start services
brew services start postgresql
brew services start redis
```

### 2. Create Database

```bash
# Create database
createdb spartan_research_db

# Create user (optional, for security)
createuser spartan

# Grant permissions
psql -d spartan_research_db -c "GRANT ALL PRIVILEGES ON DATABASE spartan_research_db TO spartan;"
```

### 3. Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your API keys
nano .env
```

**Minimum required:**
```bash
FRED_API_KEY=your_key_here
DATABASE_URL=postgresql://localhost:5432/spartan_research_db
```

---

## Daily Development Workflow

### Start All Services

```bash
./START_SPARTAN_DEV.sh
```

**This will:**
1. ✓ Check PostgreSQL and Redis (start if needed)
2. ✓ Activate virtualenv
3. ✓ Start 5 API servers (ports 8888, 5000, 5002, 5003, 5004)
4. ✓ Run data preloader
5. ✓ Start auto-refresh scheduler

**Output:**
```
======================================================================
  SPARTAN RESEARCH STATION IS READY!
======================================================================

  Main Dashboard:     http://localhost:8888/index.html

  API Endpoints:
    Main Server:      http://localhost:8888/health
    Correlation:      http://localhost:5004/health
    ...
======================================================================
```

### Check Status

```bash
./STATUS_SPARTAN_DEV.sh
```

**Shows:**
- Service status (running/stopped)
- Health check results
- Redis cache statistics
- Recent log entries

### Stop All Services

```bash
./STOP_SPARTAN_DEV.sh
```

### Restart All Services

```bash
./RESTART_SPARTAN_DEV.sh
```

---

## Common Development Tasks

### Making Code Changes

**Frontend (JavaScript):**
```bash
# Edit file
nano js/spartan-preloader.js

# Refresh browser - changes take effect IMMEDIATELY
# No restart needed!
```

**Backend (Python):**
```bash
# Edit file
nano start_server.py

# Restart just the main server
kill -9 $(cat .pids/main.pid)
python start_server.py > logs/main_server.log 2>&1 &
echo $! > .pids/main.pid

# OR restart all services
./RESTART_SPARTAN_DEV.sh
```

### Viewing Logs

**All logs:**
```bash
tail -f logs/*.log
```

**Specific service:**
```bash
tail -f logs/main_server.log
tail -f logs/correlation_api.log
tail -f logs/data_refresh.log
```

**Last 50 lines:**
```bash
tail -50 logs/main_server.log
```

### Debugging with Python Debugger

```python
# Add to your code
import pdb; pdb.set_trace()

# Run service in foreground
python start_server.py

# When code hits breakpoint, you get interactive debugger
# (Pdb) print variable_name
# (Pdb) step
# (Pdb) continue
```

### Testing API Endpoints

```bash
# Health checks
curl http://localhost:8888/health
curl http://localhost:5004/health

# Data endpoints
curl http://localhost:8888/api/market/symbol/SPY
curl http://localhost:8888/api/market/complete

# Pretty print JSON
curl -s http://localhost:8888/health | python -m json.tool
```

### Checking Cache

**Redis:**
```bash
# Connect to Redis
redis-cli

# List all keys
KEYS *

# Get specific key
GET market:index:SPY

# Check TTL (time to live)
TTL market:index:SPY

# Clear all cache (use with caution!)
FLUSHALL
```

**PostgreSQL:**
```bash
# Connect to database
psql -d spartan_research_db

# Check recent data
SELECT COUNT(*) FROM preloaded_market_data
WHERE timestamp > NOW() - INTERVAL '1 hour';

# View sample data
SELECT * FROM preloaded_market_data
ORDER BY timestamp DESC LIMIT 5;

# Exit
\q
```

### Force Data Refresh

```bash
# Manual refresh (runs immediately)
source venv/bin/activate
python src/data_preloader.py

# Restart auto-refresh scheduler
kill -9 $(cat .pids/refresh.pid)
python src/data_refresh_scheduler.py > logs/data_refresh.log 2>&1 &
echo $! > .pids/refresh.pid
```

---

## Troubleshooting

### Services Won't Start

**Check if ports are already in use:**
```bash
# Find process using port 8888
lsof -ti:8888

# Kill process
kill -9 $(lsof -ti:8888)

# Or use the stop script (safer)
./STOP_SPARTAN_DEV.sh
```

### PostgreSQL Connection Error

```bash
# Check if PostgreSQL is running
pg_isready

# Start PostgreSQL
sudo service postgresql start  # Linux
brew services start postgresql # macOS

# Check if database exists
psql -l | grep spartan_research_db

# Create if missing
createdb spartan_research_db
```

### Redis Connection Error

```bash
# Check if Redis is running
redis-cli ping

# Should return: PONG

# Start Redis
sudo service redis-server start  # Linux
brew services start redis         # macOS
```

### Data Preloader Fails

```bash
# Check logs
tail -50 logs/data_refresh.log

# Check environment variables
echo $FRED_API_KEY

# Test single source
source venv/bin/activate
python -c "import yfinance as yf; print(yf.Ticker('SPY').history(period='1d'))"
```

### Service Crashes

```bash
# Check logs for errors
tail -50 logs/main_server.log

# Run service in foreground to see errors
source venv/bin/activate
python start_server.py
```

---

## Performance Tips

### Faster Startup

**Skip data preloader on startup** (use cached data):
```bash
# Edit START_SPARTAN_DEV.sh
# Comment out:
# python src/data_preloader.py

# Data will refresh automatically every 15 minutes via scheduler
```

### Reduce Log Verbosity

```bash
# Edit Python files
import logging
logging.basicConfig(level=logging.WARNING)  # Instead of INFO
```

---

## Switching Back to Docker

When ready to test Docker or deploy:

```bash
# Stop native services
./STOP_SPARTAN_DEV.sh

# Start Docker
docker-compose up -d

# Check status
docker-compose ps
```

---

## Summary

**Start:**
```bash
./START_SPARTAN_DEV.sh
```

**Status:**
```bash
./STATUS_SPARTAN_DEV.sh
```

**Stop:**
```bash
./STOP_SPARTAN_DEV.sh
```

**Logs:**
```bash
tail -f logs/*.log
```

**Happy coding!** 🚀
