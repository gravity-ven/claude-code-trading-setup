# Spartan Research Station - Troubleshooting Guide

## Preloader Validation Failures

### Error

`❌ Data validation failed: Only X% sources succeeded (threshold: 80%)`

### Solution

1. Check which sources failed:
   ```bash
   docker-compose logs spartan-data-preloader | grep "❌"
   ```

2. Verify API keys in `.env` file

3. Test individual source by running preloader with logging

4. Temporarily lower threshold OR disable problematic source

---

## Website Won't Start

### Symptom

`spartan-web` container exits immediately

### Debug

```bash
# Check if preloader completed successfully
docker inspect spartan-data-preloader --format='{{.State.ExitCode}}'
# Should return 0

# If non-zero, fix preloader first
docker-compose logs spartan-data-preloader

# Check web server logs
docker-compose logs spartan-web
```

### Common Fixes

1. Add missing API keys to `.env` (especially `FRED_API_KEY`)
2. Temporarily lower `SUCCESS_THRESHOLD` in `src/data_preloader.py`
3. Disable problematic sources in preloader config
4. Check network connectivity to APIs
5. Verify rate limiting delays are sufficient

---

## Data Staleness

### Symptom

Dashboard shows old data (>15 minutes)

### Debug

```bash
# Check if refresh scheduler is running
docker-compose ps spartan-data-refresh

# Check refresh logs
docker-compose logs spartan-data-refresh | tail -20

# Check Redis cache freshness
docker exec -it spartan-redis redis-cli
> TTL market:index:SPY
# Should show seconds remaining (up to 900 for 15 min)

# Manually trigger refresh
docker-compose restart spartan-data-refresh
```

---

## Data Not Showing on Dashboard

### Steps

1. **Check if preloader ran successfully:**
   ```bash
   docker logs spartan-data-preloader | grep "✅"
   ```

2. **Verify Redis cache:**
   ```bash
   docker exec -it spartan-redis redis-cli
   > KEYS *
   > GET market:index:SPY
   ```

3. **Check PostgreSQL backup:**
   ```bash
   docker exec -it spartan-postgres psql -U spartan -d spartan_research_db \
     -c "SELECT COUNT(*) FROM preloaded_market_data WHERE timestamp > NOW() - INTERVAL '1 hour';"
   ```

4. **Check browser console for JavaScript errors**

---

## Container Keeps Restarting

### Steps

1. **Check logs for the specific container:**
   ```bash
   docker-compose logs -f spartan-research-station
   ```

2. **Check health endpoint:**
   ```bash
   curl http://localhost:8888/health
   ```

3. **Restart with rebuild:**
   ```bash
   docker-compose build spartan-research-station
   docker-compose up -d spartan-research-station
   ```

---

## API Rate Limiting Errors

### Symptom

`429 Too Many Requests` or similar errors in logs

### Solution

1. Increase delay in `REQUEST_DELAYS` dict in `src/data_preloader.py`
2. Verify rate limit decorators are applied to all API calls
3. Check if multiple services are hitting same API simultaneously
4. Consider upgrading to paid API tier if needed

---

## Native Development Issues

### PostgreSQL Connection Errors

```bash
# Check if PostgreSQL is running
psql -V  # Check version
pg_isready  # Check if server is ready

# Start PostgreSQL
# macOS: brew services start postgresql@15
# Linux: sudo systemctl start postgresql
# WSL2: sudo service postgresql start

# Check connection
psql -d spartan_research_db -U spartan

# If database doesn't exist, create it
createdb spartan_research_db
```

---

### Redis Connection Errors

```bash
# Check if Redis is running
redis-cli ping  # Should return "PONG"

# Start Redis
# macOS: brew services start redis
# Linux: sudo systemctl start redis
# WSL2: sudo service redis-server start

# Check Redis data
redis-cli
> KEYS *
> GET market:index:SPY
```

---

### Python Module Import Errors

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt

# Check Python version
python --version  # Should be 3.13+
```

---

### Port Already in Use

```bash
# Find process using port 8888
lsof -i :8888  # macOS/Linux
netstat -ano | findstr :8888  # Windows

# Kill the process
kill -9 <PID>  # macOS/Linux

# Or use a different port
python start_server.py --port 8889
```

---

### Data Preloader Fails on Native Setup

```bash
# Run preloader with verbose logging
python src/data_preloader.py --verbose

# Check environment variables
cat .env | grep FRED_API_KEY

# Test Redis connection
python -c "import redis; r=redis.Redis(); print(r.ping())"

# Test PostgreSQL connection
python -c "import psycopg2; conn=psycopg2.connect('postgresql://spartan:spartan@localhost/spartan_research_db'); print('Connected')"
```

---

## Emergency Procedures

### System Down - Quick Recovery

```bash
# 1. Check services
docker-compose ps

# 2. Restart everything
docker-compose down
docker-compose up -d

# 3. Monitor startup
docker-compose logs -f spartan-data-preloader

# 4. Verify health
curl http://localhost:8888/health
```

---

### Bypass Data Validation (Emergency Only)

```bash
# ONLY use if APIs are down and you need website accessible
# Edit .env:
SKIP_DATA_VALIDATION=true

# Restart
docker-compose restart spartan-data-preloader spartan-web

# WARNING: Website may have NO DATA or stale data
# FIX ASAP and set back to false
```

---

### Database Reset (If Corrupted)

```bash
# Backup first
docker exec spartan-postgres pg_dump -U spartan spartan_research_db > backup.sql

# Drop and recreate
docker exec -it spartan-postgres psql -U spartan -c "DROP DATABASE spartan_research_db;"
docker exec -it spartan-postgres psql -U spartan -c "CREATE DATABASE spartan_research_db;"

# Reinitialize schema
docker exec -it spartan-postgres psql -U spartan -d spartan_research_db -f /docker-entrypoint-initdb.d/init.sql

# Reload data
python src/data_preloader.py
```

---

## Debugging Checklist

When troubleshooting, check these in order:

1. [ ] Preloader exit code = 0?
2. [ ] Redis running and has data?
3. [ ] PostgreSQL running and has data?
4. [ ] API keys configured in .env?
5. [ ] Rate limiting delays sufficient?
6. [ ] Network connectivity to APIs?
7. [ ] Browser console for JS errors?
8. [ ] Docker containers all running?
9. [ ] Health endpoints responding?
10. [ ] Logs showing recent activity?
