@echo off
REM Diagnostic tool launcher
REM Checks system configuration for startup script issues

echo Running startup diagnostics...
echo.

powershell.exe -ExecutionPolicy Bypass -File "%~dp0DIAGNOSE_STARTUP_ISSUES.ps1"

pause
