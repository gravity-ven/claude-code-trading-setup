# UNIFIED TRADING HUB (PowerShell version)
# Launches WezTerm with ALL trading, news, and pattern agents in separate tabs
# Consolidates: Universal Patterns, Asian Session, News Agents, System Agents
# Replacement for UnifiedTradingHub.vbs

$WezTermPath = "C:\Program Files\WezTerm\wezterm.exe"
$ConfigPath = "C:\Users\Quantum\.local\share\wezterm-unified-trading-hub.lua"

if (Test-Path $WezTermPath) {
    Start-Process -FilePath $WezTermPath -ArgumentList "start", "--config-file", $ConfigPath -WindowStyle Normal
    Write-Host "Unified Trading Hub launched successfully!" -ForegroundColor Green
} else {
    Write-Host "ERROR: WezTerm not found at: $WezTermPath" -ForegroundColor Red
    Write-Host "Please install WezTerm or update the path." -ForegroundColor Yellow
}
