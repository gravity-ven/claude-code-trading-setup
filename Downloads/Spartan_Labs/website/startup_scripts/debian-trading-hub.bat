@echo off
REM Debian Trading Hub Silent Launcher
REM Batch wrapper for PowerShell script
powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File "%~dp0debian-trading-hub.ps1"
exit
