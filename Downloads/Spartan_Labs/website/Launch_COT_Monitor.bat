@echo off
REM ============================================================================
REM Launch Spartan COT Monitor in Alacritty
REM Double-click this file to start the monitor
REM ============================================================================

echo Starting Spartan COT Monitor...
echo.

REM Launch Alacritty with custom config
wsl.exe alacritty --config-file ~/.config/alacritty/alacritty_cot.yml

REM If the above doesn't work, try this instead:
REM wsl.exe bash -c "cd /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website && alacritty --config-file alacritty_cot_monitor.yml"
