# Quick Start - Native Development Mode

**Fast iteration without Docker - changes take effect immediately!**

---

## Setup (One-Time)

```bash
# 1. Install PostgreSQL and Redis
sudo apt install postgresql redis-server  # Linux/WSL
brew install postgresql redis              # macOS

# 2. Start services
sudo service postgresql start && sudo service redis-server start  # Linux
brew services start postgresql redis                               # macOS

# 3. Create database
createdb spartan_research_db

# 4. Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Configure environment
cp .env.example .env
# Edit .env with your FRED_API_KEY
```

---

## Daily Usage

### Start Everything
```bash
./START_SPARTAN_DEV.sh
```

### Check Status
```bash
./STATUS_SPARTAN_DEV.sh
```

### View Logs
```bash
tail -f logs/*.log
```

### Stop Everything
```bash
./STOP_SPARTAN_DEV.sh
```

---

## Making Changes

**JavaScript (Frontend):**
- Edit file → Save → Refresh browser ✓
- Changes take effect immediately!

**Python (Backend):**
```bash
# Edit file → Restart service
kill -9 $(cat .pids/main.pid)
python start_server.py > logs/main_server.log 2>&1 &
echo $! > .pids/main.pid
```

---

## Access Points

- **Dashboard**: http://localhost:8888/index.html
- **Health**: http://localhost:8888/health
- **Logs**: `logs/*.log`

---

## Troubleshooting

**Services won't start?**
```bash
./STOP_SPARTAN_DEV.sh  # Clean slate
./START_SPARTAN_DEV.sh  # Try again
```

**Port already in use?**
```bash
# Kill process on port 8888
kill -9 $(lsof -ti:8888)
```

**Data not loading?**
```bash
# Manual refresh
source venv/bin/activate
python src/data_preloader.py
```

---

## Why Native Development?

| Benefit | Impact |
|---------|--------|
| **5-10 second startup** | vs 45-85 seconds with Docker |
| **Instant JS changes** | No container restart needed |
| **Direct debugging** | Use Python debugger (pdb) |
| **Simple logs** | `tail -f logs/*.log` |
| **Independent services** | Preloader failure doesn't block website |

**Use native for development, Docker for production!**

---

See **DEV_WORKFLOW.md** for detailed documentation.
