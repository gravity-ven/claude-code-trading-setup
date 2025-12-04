@echo off
title Spartan Research - Setup 15-Minute Refresh

:: SETUP 15-MINUTE DATA REFRESH USING WINDOWS TASK SCHEDULER
:: This creates a task that runs every 15 minutes for more "live" data

echo.
echo ================================================================
echo   SPARTAN RESEARCH STATION - 15-Minute Refresh Setup
echo ================================================================
echo.
echo This will create a Windows Task Scheduler task to refresh
echo market data every 15 MINUTES using Polygon.io API.
echo.
echo This gives you more "live" feeling data compared to hourly.
echo.
echo Task Name: Spartan15MinRefresh
echo Schedule: Every 15 minutes
echo.
pause

:: Get the current directory
set "SCRIPT_DIR=%~dp0"
set "REFRESH_SCRIPT=%SCRIPT_DIR%refresh_15min.sh"

echo.
echo Creating scheduled task...
echo.

:: Create the task (every 15 minutes)
schtasks /create /tn "Spartan15MinRefresh" /tr "wsl bash -c 'cd \"%SCRIPT_DIR%\" && ./refresh_15min.sh'" /sc minute /mo 15 /ru "%USERNAME%" /f

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to create scheduled task!
    echo.
    echo Try running this script as Administrator.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo   SUCCESS - 15-Minute Refresh Enabled
echo ================================================================
echo.
echo Task: Spartan15MinRefresh
echo Schedule: Every 15 minutes
echo Status: Enabled
echo.
echo The system will now automatically refresh market data every
echo 15 minutes using the Polygon.io API.
echo.
echo This updates 4x more frequently than hourly refresh!
echo.
echo To view the task:
echo   - Open Task Scheduler
echo   - Look for "Spartan15MinRefresh"
echo.
echo To manually run refresh now:
echo   - Double-click: refresh_15min.sh
echo   - Or run: schtasks /run /tn "Spartan15MinRefresh"
echo.
echo To disable:
echo   - schtasks /change /tn "Spartan15MinRefresh" /disable
echo.
echo To remove:
echo   - schtasks /delete /tn "Spartan15MinRefresh" /f
echo.
echo NOTE: With 5 API calls every 15 minutes, you're using
echo       20 calls/hour, well under the 300 calls/hour limit.
echo.
echo ================================================================
echo.
pause
