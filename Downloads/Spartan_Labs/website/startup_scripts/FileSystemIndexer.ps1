# File System Indexer Startup Script (PowerShell version)
# Starts the file system indexer service silently in the background
# Replacement for FileSystemIndexer.vbs

# Path to the indexer service
$IndexerPath = "$env:USERPROFILE\.claude\filesystem_indexer_service.py"

# Check if the script exists
if (Test-Path $IndexerPath) {
    # Run Python script hidden in background
    Start-Process -FilePath "python" -ArgumentList "`"$IndexerPath`"" -WindowStyle Hidden -NoNewWindow
    Write-Host "File System Indexer started successfully!" -ForegroundColor Green
} else {
    Write-Host "WARNING: Indexer not found at: $IndexerPath" -ForegroundColor Yellow
    Write-Host "Skipping File System Indexer startup." -ForegroundColor Yellow
}
