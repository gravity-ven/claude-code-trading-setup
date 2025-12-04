# AlphaStream Omni-Terminal Silent Startup Script (PowerShell)
# Opens the terminal in your default browser without showing a command window
# More reliable than VBScript - works with modern Windows security policies

# Get script directory (works regardless of where it's called from)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$HtmlPath = Join-Path $ScriptDir "alphastream_terminal.html"

# Verify file exists before launching
if (Test-Path $HtmlPath) {
    # Open in default browser without showing console
    Start-Process $HtmlPath
    Write-Host "AlphaStream Terminal launched successfully!" -ForegroundColor Green
} else {
    Write-Host "ERROR: alphastream_terminal.html not found at: $HtmlPath" -ForegroundColor Red
    Write-Host "Please ensure the script is in the correct directory." -ForegroundColor Yellow
    pause
}
