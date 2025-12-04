@echo off
REM VBS Startup Scripts - Permanent Fix Installer
REM Run this to replace failing VBScript files with PowerShell versions

echo.
echo ===================================================================
echo       VBS STARTUP SCRIPTS - PERMANENT FIX INSTALLER
echo ===================================================================
echo.
echo This script will:
echo   1. Replace all failing .vbs files with PowerShell versions
echo   2. Backup your old VBS files (just in case)
echo   3. Install new .bat + .ps1 scripts to Windows Startup
echo   4. Fix PowerShell execution policy if needed
echo.
echo RECOMMENDED: Run as Administrator for best results
echo              (Right-click -^> Run as Administrator)
echo.
pause

REM Run PowerShell installation script
powershell.exe -ExecutionPolicy Bypass -File "%~dp0INSTALL_FIXED_STARTUP_SCRIPTS.ps1"

echo.
pause
