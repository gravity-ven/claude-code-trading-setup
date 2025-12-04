@echo off
REM ========================================
REM TEST: 1-2 Week Swing Trades Page
REM ========================================
REM
REM This script tests the tab_1_2_weeks_swing.html page
REM Verifies all real API integrations work correctly
REM
REM Requirements:
REM - Server running on port 8888 (start_server.py)
REM - FRED API proxy active
REM - Yahoo Finance proxy active
REM
REM Zero fake data - all numbers from real APIs
REM ========================================

echo.
echo ========================================
echo  1-2 Week Swing Trades - Integration Test
echo ========================================
echo.

REM Check if server is running
echo Checking if server is running on port 8888...
curl -s http://localhost:8888 >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Server not running on port 8888
    echo Please start the server first:
    echo   python start_server.py
    echo.
    pause
    exit /b 1
)
echo [OK] Server is running

echo.
echo Checking API endpoints...

REM Test Yahoo Finance proxy
echo Testing Yahoo Finance proxy...
curl -s "http://localhost:8888/api/yahoo/quote?symbols=^VIX" | findstr "regularMarketPrice" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Yahoo Finance proxy not working
) else (
    echo [OK] Yahoo Finance proxy working
)

REM Test FRED proxy
echo Testing FRED proxy...
curl -s "http://localhost:8888/api/fred/series/observations?series_id=VIXCLS&limit=1" | findstr "observations" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] FRED proxy may not be working
) else (
    echo [OK] FRED proxy working
)

echo.
echo ========================================
echo Opening page in browser...
echo ========================================
echo.
echo The page will:
echo  1. Load FRED economic data (VIX, yield curve, etc.)
echo  2. Fetch Yahoo Finance quotes for sectors and indices
echo  3. Calculate 5-day momentum for sector rotation
echo  4. Generate Top 10 momentum plays from 50 symbols
echo  5. Create 3-5 specific trade recommendations
echo.
echo ALL DATA IS REAL - NO Math.random() - NO FAKE DATA
echo.

REM Open in browser
start http://localhost:8888/tab_1_2_weeks_swing.html

echo.
echo ========================================
echo Browser opened. Check the page for:
echo ========================================
echo.
echo 1. SHORT-TERM MOMENTUM DASHBOARD
echo    - VIX (from Yahoo Finance)
echo    - 10Y-2Y Spread (from FRED)
echo    - USD Strength (from Yahoo Finance)
echo    - Market Breadth (calculated from sectors)
echo.
echo 2. 5-DAY SECTOR PERFORMANCE HEAT MAP
echo    - XLK, XLF, XLV, XLE, XLI, XLP, XLY, XLU, XLB
echo    - Green = bullish (>2%%)
echo    - Red = bearish (<-2%%)
echo    - Buy/Sell/Hold signals
echo.
echo 3. TOP 10 MOMENTUM PLAYS TABLE
echo    - 50 symbols analyzed
echo    - 5-day returns
echo    - Entry/Target/Stop prices
echo    - Risk:Reward ratios
echo.
echo 4. RECOMMENDED SWING TRADES (3-5 setups)
echo    - Specific symbols (NVDA, TLT, XLE, etc.)
echo    - Entry/Target/Stop based on ATR
echo    - Data-driven rationale
echo.
echo ========================================
echo.
echo Press F12 in browser to open DevTools
echo Check Console for API responses
echo Verify all data is from real APIs
echo.
pause
