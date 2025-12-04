@echo off
REM Launch COT Agents in new window
REM Usage: start_cot_agents.bat [args]

cd /d "%~dp0"

echo ====================================================================
echo   Spartan COT Agents - Windows Launcher
echo ====================================================================
echo.
echo Starting agents with arguments: %*
echo.

REM Start in new window
start "Spartan COT Agents" wsl python3 run_100_agents.py %*

echo.
echo ====================================================================
echo   Agents launched in new window!
echo ====================================================================
echo.
echo View logs:  wsl tail -f logs/agents.log
echo.
pause
