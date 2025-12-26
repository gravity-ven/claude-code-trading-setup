@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo   SIERRA CHART GENIUS WEB DASHBOARD
echo ========================================
echo.
echo 1. Starting Background Engine (Port 5050)...
start "" "C:\Python313\pythonw.exe" server.py

echo 2. Waiting for server initialization...
timeout /t 3 /nobreak >nul

echo 3. Launching Browser...
start http://localhost:5050

echo.
echo Dashboard is now running in your browser.
echo You can close this window.
timeout /t 2 >nul
exit
