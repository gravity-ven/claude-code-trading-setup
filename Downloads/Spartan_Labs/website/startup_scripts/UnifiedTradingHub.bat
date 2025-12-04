@echo off
REM Unified Trading Hub Silent Launcher
REM Batch wrapper for PowerShell script
powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File "%~dp0UnifiedTradingHub.ps1"
exit
