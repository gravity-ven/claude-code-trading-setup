# Spartan Research Station - Migration Guide: Windows → macOS

Complete guide for moving your Spartan Research Station from Windows to macOS while maintaining full functionality.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Migration Steps](#migration-steps)
4. [Verification](#verification)
5. [Troubleshooting](#troubleshooting)
6. [Platform Differences](#platform-differences)

---

## 🎯 Overview

This guide covers migrating the entire Spartan Research Station Docker environment from Windows to macOS. The system is fully portable thanks to:

- ✅ Docker containerization
- ✅ Relative path structure (no hardcoded Windows paths)
- ✅ Pre-built Docker images included
- ✅ Cross-platform control scripts

**Migration Time**: ~30-45 minutes (depending on file transfer method)

**Storage Required**: ~2GB for complete setup

---

## ⚙️ Prerequisites

### On macOS (Destination)

1. **Docker Desktop for Mac** (Required)
   - Download: https://www.docker.com/products/docker-desktop/
   - Version: 4.0 or newer
   - After install: Open Docker Desktop and ensure it's running (Docker icon in menu bar)

2. **System Requirements**
   - macOS 11 (Big Sur) or newer
   - 8GB RAM minimum (16GB recommended)
   - 10GB free disk space

3. **Terminal Knowledge** (Basic)
   - You'll use Terminal.app for commands
   - No advanced skills needed - we provide exact commands

### On Windows (Source)

1. **Current working Spartan setup** ✅ (You already have this!)
2. **Docker images exported** ✅ (Already done - in `docker_images_portable/` folder)
3. **Method to transfer files to Mac**:
   - External hard drive / USB stick (Recommended)
   - Cloud storage (Google Drive, OneDrive, Dropbox)
   - Network file sharing
   - Direct cable transfer

---

## 🚀 Migration Steps

### Step 1: Prepare Files on Windows

**Files to Transfer** (All in one folder):

```
Spartan_Labs/website/
├── docker_images_portable/           (607 MB - Pre-built Docker images)
│   ├── spartan_web.tar.gz
│   ├── spartan_preloader.tar.gz
│   ├── spartan_refresh.tar.gz
│   └── LOAD_IMAGES_MACOS.sh
├── src/                              (Source code)
├── js/                               (JavaScript files)
├── css/                              (Stylesheets)
├── db/                               (Database initialization scripts)
├── config/                           (Configuration files)
├── *.html                            (Dashboard pages)
├── docker-compose.spartan.yml        (Container orchestration)
├── Dockerfile.*                      (Container build files)
├── .env                              (Environment variables - IMPORTANT!)
├── requirements.txt                  (Python dependencies)
├── spartan_control.sh               (macOS control script)
└── README.md                         (Documentation)
```

**Total Size**: ~1.5-2GB

**What NOT to Transfer**:
- ❌ `SPARTAN_CONTROL.bat` (Windows only)
- ❌ Windows-specific batch files
- ❌ Any Docker volumes (will be recreated)
- ❌ Log files (`logs/` folder can be skipped)

**How to Transfer**:

**Option A: External Drive / USB (Recommended)**
```
1. Copy entire "website" folder to USB drive
2. Safely eject USB drive from Windows
3. Connect to Mac
4. Copy "website" folder to Mac (e.g., ~/Documents/)
```

**Option B: Cloud Storage**
```
1. Compress "website" folder to .zip (Right-click → Send to → Compressed folder)
2. Upload to Google Drive / OneDrive / Dropbox
3. Download on Mac
4. Unzip to desired location
```

**Option C: Network Transfer**
```
1. Enable File Sharing on Windows
2. Connect Mac to same network
3. Use Finder → Go → Connect to Server
4. Copy "website" folder
```

---

### Step 2: Setup on macOS

#### 2.1 Install Docker Desktop

1. Download Docker Desktop for Mac
2. Open the `.dmg` file
3. Drag Docker to Applications folder
4. Open Docker from Applications
5. Wait for "Docker Desktop is running" in menu bar
6. Test: Open Terminal and run:
   ```bash
   docker --version
   ```
   Should show: `Docker version 24.x.x` or similar

#### 2.2 Place Files

1. Open **Finder**
2. Navigate to where you want Spartan (e.g., `Documents/`)
3. Copy the entire `website` folder from your transfer method
4. Recommended location: `/Users/YourName/Documents/Spartan_Labs/website/`

#### 2.3 Load Docker Images

Open **Terminal** (Applications → Utilities → Terminal):

```bash
# Navigate to the website folder (adjust path if different)
cd ~/Documents/Spartan_Labs/website

# Navigate to docker images directory
cd docker_images_portable

# Make the loader script executable
chmod +x LOAD_IMAGES_MACOS.sh

# Run the loader
./LOAD_IMAGES_MACOS.sh
```

**What this does**:
- Loads 3 pre-built Spartan images (~607MB compressed)
- Downloads base images (PostgreSQL, Redis, Grafana, Prometheus)
- Verifies all images loaded correctly

**Expected output**:
```
✓ Docker Desktop is running
✓ spartan_web loaded
✓ spartan_preloader loaded
✓ spartan_refresh loaded
✓ Base images ready

✓ ALL IMAGES LOADED
```

**Time**: 5-10 minutes (depending on internet speed for base images)

---

### Step 3: Configure Environment

#### 3.1 Check .env File

```bash
# Go back to main website folder
cd ..

# Verify .env file exists
ls -la .env
```

If `.env` file is missing:
```bash
# Copy from example
cp .env.example .env

# Edit the file
nano .env
```

**Important**: Update these keys in `.env`:
```bash
# Your API keys (from Windows setup)
POLYGON_IO_API_KEY=08bqd7Ew8fw1b7QcixwkTea1UvJHdRkD
FRED_API_KEY=your_actual_fred_key_here

# Database (keep these defaults)
POSTGRES_USER=spartan_user
POSTGRES_PASSWORD=spartan_pass_2025
POSTGRES_DB=spartan_research
```

Save and exit (in nano: `Ctrl+X`, then `Y`, then `Enter`)

---

### Step 4: Start Spartan Research Station

#### 4.1 Make Control Script Executable

```bash
chmod +x spartan_control.sh
```

#### 4.2 Launch Control Panel

```bash
./spartan_control.sh
```

**You'll see**:
```
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║        SPARTAN RESEARCH STATION - CONTROL PANEL          ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝

  What would you like to do?

   [1] START   - Start all services
   [2] STOP    - Stop all services
   [3] RESTART - Restart all services
   [4] STATUS  - Check system status
   [5] BUILD   - Rebuild containers
   [6] LOGS    - View logs
   [0] EXIT    - Exit control panel

Enter your choice [0-6]:
```

#### 4.3 Start Services

**Type**: `1` (then press Enter)

**What happens**:
1. Checks Docker Desktop is running ✓
2. Starts all containers (postgres, redis, web, etc.)
3. Waits for services to be ready
4. Shows success message with URL

**Expected output**:
```
[1/3] Checking Docker Desktop...
✓ Docker Desktop is running

[2/3] Starting all services...
✓ Services started successfully

[3/3] Waiting for services to be ready...
✓ Services ready

╔══════════════════════════════════════════════════════════╗
║                    ✓ SYSTEM STARTED                      ║
╚══════════════════════════════════════════════════════════╝

Access your dashboard at:
   http://localhost:8888

Services running:
   • PostgreSQL  (Database)
   • Redis       (Cache)
   • Web Server  (Ports 8888, 9000)
   • Grafana     (Port 3000)
```

**First startup time**: 2-5 minutes (preloader downloads market data)

---

## ✅ Verification

### Test 1: Check System Status

In control panel, select `[4] STATUS`

**Should show**:
```
Docker Desktop Status:
   ✓ Docker Desktop is running

Container Status:
   spartan_postgres   Up   Healthy
   spartan_redis      Up   Healthy
   spartan_web        Up   Healthy
   spartan_preloader  Exited (0)  # Normal - runs once
   spartan_grafana    Up   Healthy

Website Accessibility:
   ✓ Website is accessible at http://localhost:8888
```

### Test 2: Access Dashboard

1. Open **Safari** or **Chrome**
2. Go to: `http://localhost:8888`
3. You should see the Spartan Research Station main page

### Test 3: Check Health Endpoint

In Terminal:
```bash
curl http://localhost:8888/health
```

**Expected response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2025-11-20T..."
}
```

### Test 4: Verify Data Loading

1. In dashboard, navigate to any market data page
2. Check that charts and data are loading
3. If you see "Loading..." indefinitely, check preloader logs:

```bash
docker logs spartan_preloader --tail 50
```

---

## 🛠️ Troubleshooting

### Issue 1: "Docker Desktop is not running"

**Solution**:
```
1. Open Docker Desktop from Applications
2. Wait for Docker icon in menu bar to show "Docker Desktop is running"
3. Try starting Spartan again
```

### Issue 2: Port Already in Use

**Error**: `port 8888 is already in use`

**Solution**:
```bash
# Find process using port 8888
lsof -i :8888

# Kill the process (replace PID with actual process ID)
kill -9 <PID>

# Or use different port: Edit docker-compose.spartan.yml
# Change: "8888:8888" to "8889:8888"
```

### Issue 3: Permission Denied

**Error**: `permission denied` when running scripts

**Solution**:
```bash
chmod +x spartan_control.sh
chmod +x docker_images_portable/LOAD_IMAGES_MACOS.sh
```

### Issue 4: Images Not Loading

**Error**: `image not found` when starting

**Solution**:
```bash
cd docker_images_portable
./LOAD_IMAGES_MACOS.sh
```

### Issue 5: Database Connection Failed

**Error**: `could not connect to database`

**Solution**:
```bash
# Restart just PostgreSQL
docker restart spartan_postgres

# Wait 30 seconds, then restart web
docker restart spartan_web
```

### Issue 6: Preloader Fails

**Error**: `preloader exited with code 1`

**Solution**:
```bash
# Check preloader logs
docker logs spartan_preloader

# Common issue: Invalid API keys
# Edit .env file and add valid keys
nano .env

# Restart system
./spartan_control.sh
# Select [3] RESTART
```

---

## 🔄 Platform Differences

### File Paths

**Windows**:
```
C:\Users\Quantum\Downloads\Spartan_Labs\website\
```

**macOS**:
```
/Users/YourName/Documents/Spartan_Labs/website/
```

### Control Scripts

| Task | Windows | macOS |
|------|---------|-------|
| Start/Stop | `SPARTAN_CONTROL.bat` | `./spartan_control.sh` |
| Terminal | CMD / PowerShell | Terminal.app |
| File Manager | Explorer | Finder |

### Docker Desktop

**Windows**:
- System tray icon (bottom right)
- Settings → Resources → WSL Integration

**macOS**:
- Menu bar icon (top right)
- Settings → Resources → Advanced

### Performance

**Expected performance on Mac**:
- **M1/M2/M3 Macs**: Excellent performance (native ARM)
- **Intel Macs**: Good performance (x86 emulation may be slower)

**Docker resource allocation** (can adjust in Docker Desktop settings):
- **Minimum**: 4GB RAM, 2 CPUs
- **Recommended**: 8GB RAM, 4 CPUs
- **Optimal**: 16GB RAM, 6+ CPUs

---

## 🎓 Quick Reference

### Daily Usage (macOS)

**Start Spartan**:
```bash
cd ~/Documents/Spartan_Labs/website
./spartan_control.sh
# Select [1] START
```

**Stop Spartan**:
```bash
./spartan_control.sh
# Select [2] STOP
```

**Check Status**:
```bash
./spartan_control.sh
# Select [4] STATUS
```

**View Logs**:
```bash
./spartan_control.sh
# Select [6] LOGS
```

### URLs (Same on Both Platforms)

- **Dashboard**: http://localhost:8888
- **Health Check**: http://localhost:8888/health
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090

### API Keys (Transfer from Windows)

Make sure these are copied from your Windows `.env` file to Mac `.env`:
- `POLYGON_IO_API_KEY`
- `FRED_API_KEY`
- Any other API keys you configured

---

## 🎉 Success Criteria

Your migration is complete when:

- ✅ Docker Desktop running on Mac
- ✅ All Docker images loaded successfully
- ✅ `./spartan_control.sh` launches without errors
- ✅ All containers show "Up" and "Healthy" status
- ✅ Dashboard accessible at http://localhost:8888
- ✅ Market data loading correctly
- ✅ No error messages in logs

---

## 📞 Support

If you encounter issues:

1. **Check logs**: `docker logs spartan_web --tail 100`
2. **Check status**: `./spartan_control.sh` → `[4] STATUS`
3. **Restart**: `./spartan_control.sh` → `[3] RESTART`

**Common log locations**:
- Web server: `docker logs spartan_web`
- Database: `docker logs spartan_postgres`
- Preloader: `docker logs spartan_preloader`
- All logs: `./logs/` directory

---

## 🔐 Security Notes

### .env File

**Contains sensitive data**:
- API keys
- Database passwords
- Secret keys

**Never**:
- ❌ Commit to Git
- ❌ Share publicly
- ❌ Upload to cloud without encryption

**Always**:
- ✅ Keep backup in secure location
- ✅ Use different passwords for production
- ✅ Add `.env` to `.gitignore`

---

## 📝 Changelog

### Migration Package Contents

**Version**: 2.0.0
**Date**: November 20, 2025

**Included**:
- ✅ Pre-built Docker images (spartan_web, spartan_preloader, spartan_refresh)
- ✅ Cross-platform docker-compose.yml
- ✅ macOS control script (spartan_control.sh)
- ✅ Image loader script (LOAD_IMAGES_MACOS.sh)
- ✅ Complete source code
- ✅ Configuration files
- ✅ Documentation

**Platform Support**:
- ✅ Windows 10/11 with Docker Desktop
- ✅ macOS 11+ (Big Sur and newer)
- ✅ Linux (Ubuntu 20.04+, Debian, etc.)

---

**🎊 Welcome to Spartan Research Station on macOS!**

The system is now fully portable and can be moved between platforms as needed. All your market intelligence tools are ready to use!
