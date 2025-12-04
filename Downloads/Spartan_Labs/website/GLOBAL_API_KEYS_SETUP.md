# Global API Keys Configuration - Spartan Labs

## 🌍 System-Wide API Keys Are Now Active!

All your API keys are now configured **globally** across your entire computer. They're accessible from any terminal, any project, and any application.

---

## ✅ Configured API Keys

| API Provider | Status | Coverage | Tier |
|--------------|--------|----------|------|
| **Polygon.io** | ✅ **ACTIVE** | Stocks, ETFs, Indices, Options, Crypto | **PAID** |
| **Marketaux** | ✅ **ACTIVE** | Market News, Sentiment, Quotes | PAID |
| **FRED** | ✅ **ACTIVE** | Economic Data (GDP, Inflation, etc.) | FREE |
| **Twelve Data** | ✅ **ACTIVE** | Stocks, Forex, Crypto, ETFs | FREE TIER |
| **Alpha Vantage** | ⚠️ Not configured | Stocks, Forex, Crypto | - |
| **Finnhub** | ⚠️ Not configured | Stocks, News, Fundamentals | - |

---

## 📂 Configuration Files

### 1. Master Configuration
**Location**: `~/.spartan_api_keys`

This is the **master file** containing all your API keys. It's:
- Loaded automatically when you open a terminal
- Secure (permissions: 600 - only you can read it)
- Version controlled in your dotfiles
- Backed up with your home directory

### 2. System-Wide Script
**Location**: `/etc/profile.d/spartan-api-keys.sh`

This script loads the master configuration for **all users** on the system (if you have multiple user accounts).

### 3. Shell Configuration
**Location**: `~/.bashrc`

Your bash configuration now automatically sources the API keys file on login.

### 4. Project-Level .env
**Location**: `/mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/.env`

The website project also has the keys in `.env` format for compatibility with Python's `python-dotenv` library.

---

## 🔄 How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                  BOOT/LOGIN SEQUENCE                        │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  /etc/profile.d/spartan-api-keys.sh  (system-wide)        │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  ~/.bashrc  (sources ~/.spartan_api_keys)                  │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  ~/.spartan_api_keys  (MASTER API KEYS)                    │
│  ✅ POLYGON_IO_API_KEY                                      │
│  ✅ MARKETAUX_API_KEY                                       │
│  ✅ FRED_API_KEY                                            │
│  ✅ TWELVE_DATA_API_KEY                                     │
│  ✅ DATABASE_URL                                            │
│  ✅ SMTP credentials                                        │
└─────────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│         ALL ENVIRONMENT VARIABLES AVAILABLE                 │
│         In any terminal, any project, any app               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Usage

### Verify Keys Are Loaded

Open any terminal and run:

```bash
spartan_check_keys
```

Output:
```
==========================================
SPARTAN LABS API KEYS STATUS
==========================================

Market Data APIs:
  ✅ Polygon.io
  ✅ Marketaux
  ✅ FRED
  ✅ Twelve Data

Email Configuration:
  ✅ SMTP configured

Database:
  ✅ PostgreSQL configured

==========================================
```

### Check Individual Keys

```bash
echo $POLYGON_IO_API_KEY
echo $FRED_API_KEY
echo $TWELVE_DATA_API_KEY
echo $DATABASE_URL
```

### Use in Python Scripts

```python
import os

# Keys are automatically available from environment
polygon_key = os.getenv('POLYGON_IO_API_KEY')
fred_key = os.getenv('FRED_API_KEY')
twelve_key = os.getenv('TWELVE_DATA_API_KEY')

print(f"Polygon: {polygon_key[:10]}...")
print(f"FRED: {fred_key[:10]}...")
print(f"Twelve Data: {twelve_key[:10]}...")
```

### Use in Bash Scripts

```bash
#!/bin/bash

# Keys are already loaded globally
echo "Using Polygon API: ${POLYGON_IO_API_KEY:0:10}..."

# Make API request
curl "https://api.polygon.io/v2/aggs/ticker/AAPL/prev?apiKey=$POLYGON_IO_API_KEY"
```

### Use in Any Directory

The keys work **from any directory**:

```bash
cd /tmp
echo $POLYGON_IO_API_KEY  # ✅ Works!

cd ~/Documents
echo $FRED_API_KEY  # ✅ Works!

cd /mnt/c/Users/Quantum/Downloads
echo $TWELVE_DATA_API_KEY  # ✅ Works!
```

---

## 🔐 Security

### File Permissions

```bash
# Master keys file (only you can read)
-rw------- 1 spartan spartan  ~/.spartan_api_keys

# System script (all users can execute, but only root can modify)
-rwxr-xr-x 1 root root  /etc/profile.d/spartan-api-keys.sh
```

### Best Practices

✅ **DO**:
- Keep `~/.spartan_api_keys` with 600 permissions
- Backup this file securely
- Use `.gitignore` for API keys in projects
- Rotate keys periodically

❌ **DON'T**:
- Commit API keys to Git repositories
- Share keys with unauthorized users
- Store keys in plain text in public locations
- Use the same keys across different environments (dev/prod)

---

## 🔧 Adding More API Keys

### Option 1: Edit Master File Directly

```bash
nano ~/.spartan_api_keys

# Add your new key:
export NEW_API_KEY="your_key_here"

# Save and reload:
source ~/.spartan_api_keys
```

### Option 2: Append with Echo

```bash
echo 'export NEW_API_KEY="your_key_here"' >> ~/.spartan_api_keys
source ~/.spartan_api_keys
```

### Option 3: Use the Provided Template

The master file has commented templates for common APIs:

```bash
# Just uncomment and add your key:
# export ALPHA_VANTAGE_API_KEY="your_key"
# ↓
export ALPHA_VANTAGE_API_KEY="actual_key_here"
```

---

## 🧪 Testing

### Test New Terminal

1. Open a **new terminal window**
2. Run: `echo $POLYGON_IO_API_KEY`
3. Should display your key

### Test System Reboot (WSL2)

```bash
# Restart WSL2
wsl --shutdown
# Wait 10 seconds
wsl

# Check keys
spartan_check_keys
```

### Test Python Import

```bash
python3 -c "import os; print('Polygon:', os.getenv('POLYGON_IO_API_KEY')[:10])"
```

---

## 📊 API Key Coverage Summary

With your current configuration, you have **EXCELLENT** data coverage:

### ✅ Market Data (Polygon.io - PAID)
- ✅ US Stocks (NYSE, NASDAQ)
- ✅ ETFs (all major ones)
- ✅ Indices (SPY, QQQ, DIA, IWM, etc.)
- ✅ Options chains
- ✅ Crypto (BTC, ETH, etc.)
- ⚠️ Forex (requires higher tier)

### ✅ Economic Data (FRED - FREE)
- ✅ GDP, Inflation, Unemployment
- ✅ Interest Rates
- ✅ Money Supply
- ✅ Consumer Sentiment
- ✅ 800,000+ economic time series!

### ✅ Forex + International (Twelve Data - FREE TIER)
- ✅ Forex pairs (EUR/USD, GBP/USD, etc.)
- ✅ International stocks
- ✅ Crypto
- ✅ ETFs
- ⚠️ Rate limited (800 API calls/day on free tier)

### ✅ News + Sentiment (Marketaux - PAID)
- ✅ Real-time market news
- ✅ Sentiment analysis
- ✅ Market quotes

---

## 🛠️ Troubleshooting

### Keys Not Loading

**Problem**: `echo $POLYGON_IO_API_KEY` returns empty

**Solution**:
```bash
# Manually source the file
source ~/.spartan_api_keys

# Check for errors
bash -x ~/.spartan_api_keys

# Verify file exists
ls -la ~/.spartan_api_keys

# Check bashrc includes it
grep "spartan_api_keys" ~/.bashrc
```

### Permission Denied

**Problem**: Can't read `~/.spartan_api_keys`

**Solution**:
```bash
chmod 600 ~/.spartan_api_keys
```

### System Script Not Loading

**Problem**: Keys don't load system-wide

**Solution**:
```bash
# Check system script
ls -la /etc/profile.d/spartan-api-keys.sh

# Reinstall if needed
sudo cp ~/.spartan_api_keys /etc/profile.d/spartan-api-keys.sh
sudo chmod 755 /etc/profile.d/spartan-api-keys.sh
```

---

## 📝 Maintenance

### Backup Your Keys

```bash
# Backup to secure location
cp ~/.spartan_api_keys ~/Dropbox/backups/spartan-keys-$(date +%Y%m%d).bak

# Or to Windows user directory
cp ~/.spartan_api_keys /mnt/c/Users/Quantum/Documents/spartan-keys-backup.txt
```

### Update a Key

```bash
# Edit the master file
nano ~/.spartan_api_keys

# Change the key value
export POLYGON_IO_API_KEY="new_key_here"

# Reload
source ~/.spartan_api_keys

# Verify
echo $POLYGON_IO_API_KEY
```

### Rotate Keys Periodically

Best practice: Rotate API keys every 90 days

```bash
# 1. Get new keys from provider dashboards
# 2. Update ~/.spartan_api_keys
# 3. Update ~/.env files in projects
# 4. Test before removing old keys
# 5. Revoke old keys from dashboards
```

---

## 🎯 Integration with Data Guardian Agent

The **Data Guardian Agent** automatically uses these global keys:

1. **Detects keys on startup** from environment variables
2. **Prioritizes sources** based on which keys are available
3. **Adapts strategy** if keys are added/removed
4. **No restart needed** - just reload with new keys

To use new keys with Data Guardian:

```bash
# 1. Add key to ~/.spartan_api_keys
# 2. Reload environment
source ~/.spartan_api_keys

# 3. Restart Data Guardian (it will detect new keys)
pkill -f data_guardian_agent.py
python3 data_guardian_agent.py &
```

---

## 📚 Related Files

- `~/.spartan_api_keys` - Master API keys
- `~/.bashrc` - Shell configuration
- `/etc/profile.d/spartan-api-keys.sh` - System-wide loader
- `.env` - Project-specific copy (for python-dotenv)
- `data_guardian_agent.py` - Uses these keys automatically

---

## ✨ Benefits

✅ **Single Source of Truth**: All keys in one place
✅ **Global Access**: Works from any directory/project
✅ **Automatic Loading**: No manual sourcing needed
✅ **Secure**: Proper file permissions
✅ **Version Controlled**: Easy to backup/restore
✅ **Portable**: Move to new system by copying one file
✅ **Validated**: Built-in `spartan_check_keys` command

---

**Last Updated**: November 25, 2025
**Status**: ✅ Fully Operational
**Total API Keys**: 4 active, 2 optional

Your Spartan Labs ecosystem now has **enterprise-grade API key management**! 🚀
