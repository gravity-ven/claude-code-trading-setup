@echo off
title Spartan Research - Setup Hourly Refresh

:: SETUP HOURLY DATA REFRESH USING WINDOWS TASK SCHEDULER
:: This creates a task that runs every hour to update market data

echo.
echo ================================================================
echo   SPARTAN RESEARCH STATION - Hourly Refresh Setup
echo ================================================================
echo.
echo This will create a Windows Task Scheduler task to refresh
echo market data every hour using Polygon.io API.
echo.
echo Task Name: SpartanHourlyRefresh
echo Schedule: Every 1 hour
echo.
pause

:: Get the current directory
set "SCRIPT_DIR=%~dp0"
set "REFRESH_SCRIPT=%SCRIPT_DIR%hourly_refresh.sh"

echo.
echo Creating scheduled task...
echo.

:: Create the task
schtasks /create /tn "SpartanHourlyRefresh" /tr "wsl bash -c 'cd \"%SCRIPT_DIR%\" && ./hourly_refresh.sh'" /sc hourly /ru "%USERNAME%" /f

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
echo   SUCCESS - Hourly Refresh Enabled
echo ================================================================
echo.
echo Task: SpartanHourlyRefresh
echo Schedule: Every 1 hour
echo Status: Enabled
echo.
echo The system will now automatically refresh market data every hour
echo using the Polygon.io API.
echo.
echo To view the task:
echo   - Open Task Scheduler
echo   - Look for "SpartanHourlyRefresh"
echo.
echo To manually run refresh now:
echo   - Double-click: hourly_refresh.sh
echo   - Or run: schtasks /run /tn "SpartanHourlyRefresh"
echo.
echo To disable:
echo   - schtasks /change /tn "SpartanHourlyRefresh" /disable
echo.
echo To remove:
echo   - schtasks /delete /tn "SpartanHourlyRefresh" /f
echo.
echo ================================================================
echo.
pause
