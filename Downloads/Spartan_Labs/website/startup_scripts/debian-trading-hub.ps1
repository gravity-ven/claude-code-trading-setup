# DEBIAN WSL TRADING HUB STARTUP (PowerShell version)
# Runs silently in background - ALL AGENTS IN DEBIAN WSL
# Replacement for debian-trading-hub.vbs

# Launch WSL Debian with startup script
Start-Process -FilePath "wsl.exe" -ArgumentList "-d", "Debian", "-e", "bash", "-c", "/home/spartan/debian-startup-master.sh" -WindowStyle Hidden -NoNewWindow

Write-Host "Debian Trading Hub started successfully!" -ForegroundColor Green
