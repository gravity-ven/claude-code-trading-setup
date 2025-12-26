@echo off
cd /d "%~dp0"
echo Activating Sierra Chart Auto-Launcher...
echo This will run in the background and open the dashboard whenever Sierra Chart starts.
start "" "C:\Python313\pythonw.exe" auto_launcher.py
echo.
echo DONE. You can close this window.
timeout /t 3 >nul
exit
