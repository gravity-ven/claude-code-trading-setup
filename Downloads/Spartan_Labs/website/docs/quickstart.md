# Spartan Research Station - Quick Start Guide

## Native Development Workflow (Recommended)

### 1. Install Dependencies (One-Time Setup)

**macOS:**
```bash
brew install postgresql@15 redis
brew services start postgresql@15
brew services start redis
```

**Linux:**
```bash
sudo apt install postgresql-15 redis-server
sudo systemctl start postgresql redis
```

**Windows WSL2:**
```bash
sudo apt install postgresql redis-server
sudo service postgresql start
sudo service redis-server start
```

### 2. Database Setup

```bash
# Create database and user
createdb spartan_research_db
psql -d spartan_research_db -c "CREATE USER spartan WITH PASSWORD 'spartan';"
psql -d spartan_research_db -c "GRANT ALL PRIVILEGES ON DATABASE spartan_research_db TO spartan;"
```

### 3. Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your FRED_API_KEY (optional but recommended)
# Get free key at: https://fred.stlouisfed.org/docs/api/api_key.html
```

### 5. Load Data & Start Server

```bash
# Run data preloader (loads market data)
python src/data_preloader.py

# Start the main web server
python start_server.py
# Server runs on http://localhost:8888
```

### 6. Optional: Start API Microservices

```bash
# In separate terminals
python correlation_api.py       # Port 5004
python daily_planet_api.py      # Port 5000
python swing_dashboard_api.py   # Port 5002
python garp_api.py              # Port 5003
```

---

## Docker Workflow (Alternative)

### Quick Start

```bash
# Start entire system with Docker
./START_SPARTAN.sh
```

### Manual Docker Control

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View all logs
docker-compose logs -f

# Restart specific service
docker-compose restart spartan-web

# Rebuild after dependency changes
docker-compose build spartan-web
```

### Data Management

```bash
# Force data refresh
docker-compose restart spartan-data-preloader

# Check preloader status
docker-compose logs spartan-data-preloader
```

### Health Checks

```bash
# Main server health
curl http://localhost:8888/health

# Data validation status
curl http://localhost:8888/health/data

# Database access
docker exec -it spartan-postgres psql -U spartan -d spartan_research_db

# Redis access
docker exec -it spartan-redis redis-cli
```

---

## Common Commands

### Native Development

```bash
# Check PostgreSQL is running
psql -d spartan_research_db -c "SELECT version();"

# Check Redis is running
redis-cli ping  # Should return "PONG"

# View database tables
psql -d spartan_research_db -c "\dt"

# Check preloaded data
psql -d spartan_research_db -c "SELECT COUNT(*) FROM preloaded_market_data;"

# View Redis cache keys
redis-cli KEYS '*'

# Get cached market data
redis-cli GET market:index:SPY

# Manually refresh data
python src/data_preloader.py

# Run with auto-refresh (every 15 minutes)
python src/data_refresh_scheduler.py
```

---

## Testing

### Native Development Tests

```bash
# Test data preloader
python src/data_preloader.py

# Test main server health
curl http://localhost:8888/health

# Test API endpoints (if running)
curl http://localhost:5004/health          # Correlation API
curl http://localhost:5000/health          # Daily Planet API
curl http://localhost:5002/api/swing-dashboard/health    # Swing API
curl http://localhost:5003/api/health      # GARP API

# Test database connection
python -c "import psycopg2; conn=psycopg2.connect('postgresql://spartan:spartan@localhost/spartan_research_db'); print('✅ Database connected')"

# Check data freshness in PostgreSQL
psql -d spartan_research_db -U spartan -c "SELECT COUNT(*) FROM preloaded_market_data WHERE timestamp > NOW() - INTERVAL '1 hour';"

# Check Redis cache
redis-cli KEYS '*'
redis-cli GET market:index:SPY

# Test yfinance data fetching
python -c "import yfinance as yf; spy=yf.Ticker('SPY'); print(spy.history(period='1d'))"

# Run unit tests (if available)
pytest tests/
```

### Docker Tests

```bash
# Test data preloader directly
docker exec spartan-data-preloader python src/data_preloader.py

# Test specific API endpoint
curl http://localhost:5004/health          # Correlation API
curl http://localhost:5000/health          # Daily Planet API
curl http://localhost:5002/api/swing-dashboard/health    # Swing API
curl http://localhost:5003/api/health      # GARP API

# Check PostgreSQL data freshness
docker exec -it spartan-postgres psql -U spartan -d spartan_research_db \
  -c "SELECT COUNT(*) FROM preloaded_market_data WHERE timestamp > NOW() - INTERVAL '1 hour';"

# Check Redis cache
docker exec -it spartan-redis redis-cli KEYS '*'
docker exec -it spartan-redis redis-cli GET market:index:SPY
```

---

## Environment Variables

**Required Environment Variables** (`.env`):

```bash
# Essential (required for startup)
FRED_API_KEY=your_fred_key                    # Economic data

# Optional (for enhanced data coverage)
ALPHA_VANTAGE_API_KEY=your_av_key
POLYGON_IO_API_KEY=your_polygon_key
TWELVE_DATA_API_KEY=your_td_key
FINNHUB_API_KEY=your_finnhub_key

# Monitor Agent (optional - currently disabled)
ANTHROPIC_API_KEY=sk-ant-...                  # For Claude AI diagnosis

# Database (auto-configured in Docker)
DATABASE_URL=postgresql://spartan:spartan@postgres:5432/spartan_research_db
POSTGRES_USER=spartan
POSTGRES_PASSWORD=spartan
POSTGRES_DB=spartan_research_db
```

---

## Native vs Docker: When to Use Each

**Use Native Development When:**
- Developing locally and want fast iteration
- Debugging Python code directly
- Don't want Docker overhead
- Running on resource-constrained machine
- Need direct access to PostgreSQL/Redis

**Use Docker When:**
- Deploying to production
- Need consistent environment across team
- Want isolated services
- Testing full microservices architecture
- Need autonomous monitoring agent

---

## Performance Characteristics

### Startup Time
- Infrastructure (PostgreSQL + Redis): 5-10 seconds
- Data Preloader: 30-60 seconds (13+ sources with rate limiting)
- Web Server: 5-10 seconds
- **Total**: 45-85 seconds to fully operational

### Resource Usage
- PostgreSQL: 1-5% CPU, 100MB RAM
- Redis: <1% CPU, 20MB RAM
- Web Server: 2-10% CPU, 150MB RAM
- **Total**: ~10% CPU, ~500MB RAM
