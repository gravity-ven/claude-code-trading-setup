@echo off
REM ===================================================================
REM Spartan Labs - COT Daily Email Setup (Windows Task Scheduler)
REM ===================================================================
REM This script creates a scheduled task to run the COT emailer daily
REM ===================================================================

echo.
echo ========================================================================
echo SPARTAN LABS - COT DAILY EMAIL SETUP
echo ========================================================================
echo.

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator!
    echo.
    echo Right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo [OK] Running as Administrator
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set PYTHON_SCRIPT=%SCRIPT_DIR%cot_daily_emailer.py

REM Find Python executable
where python >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Python not found in PATH!
    echo.
    echo Please install Python 3.13+ or add it to your PATH
    echo Download: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo [OK] Python found:
python --version
echo.

REM Check if COT script exists
if not exist "%PYTHON_SCRIPT%" (
    echo ERROR: COT emailer script not found!
    echo Expected location: %PYTHON_SCRIPT%
    echo.
    pause
    exit /b 1
)

echo [OK] COT script found: %PYTHON_SCRIPT%
echo.

REM Install required Python packages
echo Installing required Python packages...
echo.
pip install matplotlib pandas numpy requests python-dotenv
echo.

REM Prompt for email time
echo ========================================================================
echo SCHEDULE CONFIGURATION
echo ========================================================================
echo.
echo What time should the COT report be sent daily?
echo Default: 08:00 AM (8:00)
echo.
set /p EMAIL_TIME="Enter time (HH:MM format, 24-hour): "

if "%EMAIL_TIME%"=="" (
    set EMAIL_TIME=08:00
    echo Using default time: 08:00 AM
)

echo.
echo ========================================================================
echo CREATING SCHEDULED TASK
echo ========================================================================
echo.

REM Delete existing task if it exists
schtasks /query /tn "SpartanLabs_COT_Daily" >nul 2>&1
if %errorLevel% equ 0 (
    echo Removing existing task...
    schtasks /delete /tn "SpartanLabs_COT_Daily" /f >nul 2>&1
)

REM Create the scheduled task with catch-up feature
REM The /RL HIGHEST ensures it runs even if computer was off at scheduled time
schtasks /create ^
    /tn "SpartanLabs_COT_Daily" ^
    /tr "python \"%PYTHON_SCRIPT%\"" ^
    /sc daily ^
    /st %EMAIL_TIME% ^
    /ru SYSTEM ^
    /rl HIGHEST ^
    /f

REM Enable "Run task as soon as possible after a scheduled start is missed"
REM This ensures that if computer is off at 8 AM, it will run when computer turns on
powershell -Command "$task = Get-ScheduledTask -TaskName 'SpartanLabs_COT_Daily'; $task.Settings.StartWhenAvailable = $true; $task | Set-ScheduledTask"

if %errorLevel% neq 0 (
    echo.
    echo ERROR: Failed to create scheduled task!
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================================================
echo SUCCESS! COT Daily Email Configured
echo ========================================================================
echo.
echo Task Name: SpartanLabs_COT_Daily
echo Schedule:  Every day at %EMAIL_TIME%
echo Script:    %PYTHON_SCRIPT%
echo.
echo ✅ CATCH-UP ENABLED: If your computer is off at %EMAIL_TIME%, the task
echo    will run automatically as soon as the computer turns on.
echo    This ensures you always get your daily COT report!
echo.
echo ========================================================================
echo IMPORTANT NEXT STEPS
echo ========================================================================
echo.
echo 1. CREATE GMAIL APP PASSWORD:
echo    - Go to: https://myaccount.google.com/security
echo    - Enable 2-Step Verification
echo    - Search for "App passwords"
echo    - Create password for "Mail"
echo    - Copy the 16-character code
echo.
echo 2. UPDATE .env FILE:
echo    - Open: %SCRIPT_DIR%.env
echo    - Find line: SMTP_PASSWORD=YOUR_16_CHAR_APP_PASSWORD_HERE
echo    - Replace with your App Password (no spaces)
echo    - Example: SMTP_PASSWORD=abcdabcdabcdabcd
echo.
echo 3. TEST THE SCRIPT:
echo    - Run: python "%PYTHON_SCRIPT%"
echo    - Check your email: naga.kvv@gmail.com
echo.
echo 4. VIEW/MANAGE SCHEDULED TASK:
echo    - Open: Task Scheduler (search in Windows)
echo    - Navigate to: Task Scheduler Library
echo    - Find: SpartanLabs_COT_Daily
echo.
echo ========================================================================
echo.

pause
