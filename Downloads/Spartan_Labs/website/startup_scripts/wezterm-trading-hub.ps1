# WEZTERM TRADING HUB STARTUP (PowerShell version)
# Launches WezTerm with all trading agents in separate tabs
# Runs in normal window mode
# Replacement for wezterm-trading-hub.vbs

$WezTermPath = "C:\Program Files\WezTerm\wezterm.exe"
$ConfigPath = "C:\Users\Quantum\.local\share\wezterm-trading-hub-startup.lua"

if (Test-Path $WezTermPath) {
    Start-Process -FilePath $WezTermPath -ArgumentList "start", "--config-file", $ConfigPath -WindowStyle Normal
    Write-Host "WezTerm Trading Hub launched successfully!" -ForegroundColor Green
} else {
    Write-Host "ERROR: WezTerm not found at: $WezTermPath" -ForegroundColor Red
    Write-Host "Please install WezTerm or update the path." -ForegroundColor Yellow
}
