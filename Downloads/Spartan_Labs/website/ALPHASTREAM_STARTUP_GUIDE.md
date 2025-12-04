# AlphaStream Omni-Terminal - Startup Guide

## Quick Setup (Auto-Start on Windows Boot)

### Option 1: Silent Startup (Recommended)

**No command window, clean auto-start**

1. Press `Win + R` to open Run dialog
2. Type: `shell:startup` and press Enter
3. Windows Explorer will open the Startup folder
4. **Copy** the file: `START_ALPHASTREAM_TERMINAL_SILENT.vbs`
5. **Paste shortcut** into the Startup folder
6. Done! It will open automatically on next boot

**Location of VBS file:**
```
C:\Users\Quantum\Downloads\Spartan_Labs\website\START_ALPHASTREAM_TERMINAL_SILENT.vbs
```

---

### Option 2: Visible Startup (With Command Window)

**Shows brief command window during launch**

1. Press `Win + R` to open Run dialog
2. Type: `shell:startup` and press Enter
3. **Copy** the file: `START_ALPHASTREAM_TERMINAL.bat`
4. **Paste shortcut** into the Startup folder
5. Done!

**Location of BAT file:**
```
C:\Users\Quantum\Downloads\Spartan_Labs\website\START_ALPHASTREAM_TERMINAL.bat
```

---

### Option 3: Manual Launch (Test Before Auto-Start)

**Test the terminal before setting up auto-start:**

1. Navigate to: `C:\Users\Quantum\Downloads\Spartan_Labs\website\`
2. Double-click: `alphastream_terminal.html`
3. Terminal opens in your default browser

---

## Files Included

### 1. `alphastream_terminal.html`
**The main terminal interface**

- Standalone HTML file (works offline except for data APIs)
- Uses CDN for libraries (Tailwind CSS, Chart.js, Google Fonts)
- No installation required, just open in browser

**Features:**
- Real-time crypto data (CoinGecko API - no key required)
- TradFi market data (AlphaVantage API - requires free key)
- Macro cycle analysis
- Venture capital lifecycle tracker
- Trading strategy planner with logic checks
- Daily routine checklist with progress tracking

---

### 2. `START_ALPHASTREAM_TERMINAL.bat`
**Windows batch script (visible launch)**

- Opens terminal in default browser
- Shows command window briefly
- Good for testing/debugging

**Usage:**
```
Double-click the file or run from command line
```

---

### 3. `START_ALPHASTREAM_TERMINAL_SILENT.vbs`
**Windows VBScript (silent launch)**

- Opens terminal without showing command window
- Clean, professional auto-start
- Recommended for production use

**Usage:**
```
Double-click the file or add to Windows Startup folder
```

---

## Initial Configuration

### Step 1: Get AlphaVantage API Key (Optional - For TradFi Data)

**Free API Key:**
1. Visit: https://www.alphavantage.co/support/#api-key
2. Enter email address
3. Receive free API key (5 calls/minute limit)

**What you get with API key:**
- S&P 500 (SPY) real-time price & sentiment
- US 10-Year Treasury Yield data
- Macro cycle calculations

**What works WITHOUT API key:**
- Bitcoin (BTC) price & 24h change
- Crypto fear/greed sentiment (based on volatility)
- Venture capital lifecycle tracker
- Strategy planner (limited without market data)

---

### Step 2: Configure Terminal (First Launch)

1. Open the terminal (double-click `alphastream_terminal.html`)
2. Click **"SYSTEM SETTINGS"** button (top right)
3. Enter your AlphaVantage API key
4. Click **"SAVE & REBOOT"**
5. Terminal will reload and fetch TradFi data

**Your API key is stored locally in browser localStorage (never leaves your computer)**

---

## Verifying Auto-Start Setup

### Test Without Reboot:

1. Open Task Manager (`Ctrl + Shift + Esc`)
2. Go to **"Startup"** tab
3. Look for `START_ALPHASTREAM_TERMINAL_SILENT.vbs` or `.bat`
4. Status should show **"Enabled"**

### Test With Manual Run:

Before setting auto-start:
1. Double-click `START_ALPHASTREAM_TERMINAL_SILENT.vbs`
2. Browser should open with terminal within 2 seconds
3. If successful, proceed to add to Startup folder

---

## Troubleshooting

### Terminal doesn't open automatically

**Check:**
1. Startup folder location is correct: `shell:startup` (Win + R)
2. Shortcut points to correct file path
3. File extension is `.vbs` or `.bat` (not `.txt`)
4. Windows Startup is enabled (Task Manager → Startup tab)

---

### Crypto data shows "API ERROR"

**Cause:** CoinGecko API might be temporarily unavailable or rate-limited

**Fix:**
1. Wait 60 seconds and refresh page
2. Check internet connection
3. Try opening: https://api.coingecko.com/api/v3/ping in browser
   - Should return: `{"gecko_says":"(V3) To the Moon!"}`

---

### TradFi data shows "WAITING FOR KEY..."

**Cause:** AlphaVantage API key not configured

**Fix:**
1. Click **"SYSTEM SETTINGS"**
2. Enter your free API key from alphavantage.co
3. Click **"SAVE & REBOOT"**

---

### TradFi data shows "API LIMIT"

**Cause:** AlphaVantage free tier is limited to 5 API calls per minute

**Fix:**
1. Wait 60 seconds
2. Refresh page
3. For unlimited calls, upgrade to premium plan at alphavantage.co

---

### Browser shows "File blocked" or security warning

**Cause:** Windows SmartScreen protecting against unknown files

**Fix:**
1. Right-click the `.vbs` or `.bat` file
2. Select **"Properties"**
3. Check **"Unblock"** at bottom of General tab
4. Click **"Apply"** then **"OK"**

---

## Advanced Configuration

### Change Default Browser

Terminal opens in Windows default browser. To change:

1. Windows Settings → Apps → Default apps
2. Search for "Web browser"
3. Select preferred browser (Chrome, Edge, Firefox, Brave, etc.)

---

### Open in Specific Browser

Modify `START_ALPHASTREAM_TERMINAL.bat`:

**For Chrome:**
```batch
start chrome "C:\Users\Quantum\Downloads\Spartan_Labs\website\alphastream_terminal.html"
```

**For Firefox:**
```batch
start firefox "C:\Users\Quantum\Downloads\Spartan_Labs\website\alphastream_terminal.html"
```

**For Edge:**
```batch
start msedge "C:\Users\Quantum\Downloads\Spartan_Labs\website\alphastream_terminal.html"
```

---

### Delay Startup (Open 30 seconds after boot)

Modify `START_ALPHASTREAM_TERMINAL.bat`:

```batch
@echo off
echo Waiting 30 seconds before launching AlphaStream...
timeout /t 30 /nobreak >nul
start "" "C:\Users\Quantum\Downloads\Spartan_Labs\website\alphastream_terminal.html"
```

---

### Open in Fullscreen (Kiosk Mode)

**Chrome Kiosk Mode:**
```batch
start chrome --kiosk "C:\Users\Quantum\Downloads\Spartan_Labs\website\alphastream_terminal.html"
```

**Edge Kiosk Mode:**
```batch
start msedge --kiosk "C:\Users\Quantum\Downloads\Spartan_Labs\website\alphastream_terminal.html"
```

---

## Data Sources & APIs

### Public APIs (No Key Required)

**CoinGecko API:**
- Bitcoin price (BTC-USD)
- 24-hour price change
- Endpoint: `https://api.coingecko.com/api/v3/simple/price`
- Rate limit: ~50 calls/minute (generous)

---

### Premium APIs (Free Tier Available)

**AlphaVantage API:**
- S&P 500 (SPY) quote
- US Treasury yields
- Endpoint: `https://www.alphavantage.co/query`
- Free tier: 5 calls/minute, 500 calls/day
- Sign up: https://www.alphavantage.co/support/#api-key

---

## Privacy & Security

### What Data is Stored Locally?

**LocalStorage (Browser):**
- AlphaVantage API key
- Daily routine checklist progress

**NOT Stored:**
- Market prices (fetched real-time)
- Personal trading data
- Account information

### How to Clear All Data

1. Click **"SYSTEM SETTINGS"**
2. Click **"WIPE DATA"**
3. Confirm by refreshing page

**Or manually:**
1. Press `F12` to open Developer Tools
2. Go to **"Application"** tab
3. Expand **"Local Storage"**
4. Right-click and select **"Clear"**

---

## Features Breakdown

### 1. Market Watch
- **TradFi Sector:** S&P 500 (SPY) price, sentiment, yield curve
- **Crypto Sector:** Bitcoin price, fear/greed index
- **Mini Charts:** Visual price flow indicators

### 2. Macro Cycle
- Real-time economic phase detection (Recovery, Boom, Slowdown, Recession)
- Logic-based asset allocation recommendations
- Calculated using yield curve + equity sentiment

### 3. Venture Lab
- Startup lifecycle stages (Pre-Seed → IPO)
- Valuation ranges per stage
- Founder dilution tracker (visual donut chart)

### 4. Strategy Hub
- Multi-timeframe analysis (Tactical, Seasonal, Macro)
- Real-data logic checks (not simulated)
- Risk-adjusted allocation recommendations

### 5. Routine Protocol (Sidebar)
- Daily & weekly trading checklist
- Progress bar with percentage completion
- Persistent checkbox states (saved in localStorage)

---

## Links & Resources

### Official APIs
- **AlphaVantage:** https://www.alphavantage.co/
- **CoinGecko:** https://www.coingecko.com/en/api
- **Chart.js Docs:** https://www.chartjs.org/docs/
- **Tailwind CSS:** https://tailwindcss.com/

### Startup Folder Locations

**Current User:**
```
C:\Users\Quantum\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
```

**All Users (Admin Required):**
```
C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp
```

**Quick Access (Win + R):**
- `shell:startup` - Current user
- `shell:common startup` - All users

---

## Uninstall / Remove Auto-Start

### Remove from Startup:

1. Press `Win + R`
2. Type: `shell:startup`
3. Delete the shortcut to `START_ALPHASTREAM_TERMINAL_SILENT.vbs` (or `.bat`)
4. Done - won't auto-start anymore

### Delete All Files:

Navigate to and delete:
```
C:\Users\Quantum\Downloads\Spartan_Labs\website\
```

Files to delete:
- `alphastream_terminal.html`
- `START_ALPHASTREAM_TERMINAL.bat`
- `START_ALPHASTREAM_TERMINAL_SILENT.vbs`
- `ALPHASTREAM_STARTUP_GUIDE.md` (this file)

---

## Support & Customization

### Need Help?

Check the troubleshooting section above or:
1. Verify internet connection
2. Test APIs manually in browser
3. Check browser console for errors (F12 → Console tab)

### Want to Customize?

The HTML file is fully self-contained and editable:
1. Open `alphastream_terminal.html` in text editor (VS Code, Notepad++)
2. Modify colors, layout, or data sources
3. Save and refresh browser

**Key sections:**
- **Colors:** Line 27-40 (Tailwind config)
- **Data fetching:** Line 400+ (`fetchCryptoData`, `fetchTradFiData`)
- **Macro logic:** Line 530+ (`updateMacroCycle`)
- **Checklist items:** Line 60+ (HTML `<aside>` section)

---

## Version & Updates

**Version:** 1.0.0
**Last Updated:** November 29, 2025
**Status:** Production Ready

**What's New:**
- Complete financial intelligence dashboard
- Real-time crypto & TradFi data integration
- Macro economic cycle calculator
- Venture capital lifecycle tracker
- Multi-timeframe strategy planner
- Auto-startup capability (Windows)
- Zero dependencies (all CDN-based)

---

**You're all set! The AlphaStream Omni-Terminal is ready to launch on every startup.**

For silent auto-start, add `START_ALPHASTREAM_TERMINAL_SILENT.vbs` to your Windows Startup folder (`shell:startup`).
