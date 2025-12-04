@echo off
REM WezTerm Trading Hub Silent Launcher
REM Batch wrapper for PowerShell script
powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File "%~dp0wezterm-trading-hub.ps1"
exit
