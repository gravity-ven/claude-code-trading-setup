@echo off
REM AlphaStream Omni-Terminal Startup Script
REM Opens the terminal in your default browser

echo Starting AlphaStream Omni-Terminal...

REM Open in default browser (using relative path)
start "" "%~dp0alphastream_terminal.html"

echo AlphaStream Terminal launched successfully!
timeout /t 2 >nul
