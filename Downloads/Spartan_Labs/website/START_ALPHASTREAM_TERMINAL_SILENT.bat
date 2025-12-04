@echo off
REM AlphaStream Omni-Terminal Silent Startup (Batch wrapper for PowerShell)
REM This wrapper ensures PowerShell runs without showing a console window

REM Use PowerShell to run the script silently (hidden window)
powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File "%~dp0START_ALPHASTREAM_TERMINAL_SILENT.ps1"

REM Exit immediately without pausing
exit
