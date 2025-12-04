# PERMANENT FIX FOR VBS STARTUP SCRIPTS
# Replaces all failing VBScript files with modern PowerShell versions
# Run this script as Administrator for best results

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                            ║" -ForegroundColor Cyan
Write-Host "║        STARTUP SCRIPTS - PERMANENT VBS FIX                ║" -ForegroundColor Cyan
Write-Host "║                                                            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Get script directory and startup folder
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$StartupFolder = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"

Write-Host "Script Directory: $ScriptDir" -ForegroundColor Yellow
Write-Host "Startup Folder:   $StartupFolder" -ForegroundColor Yellow
Write-Host ""

# Check if running as Administrator
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $IsAdmin) {
    Write-Host "⚠️  WARNING: Not running as Administrator" -ForegroundColor Yellow
    Write-Host "   Some operations may require elevated permissions" -ForegroundColor Yellow
    Write-Host ""
}

# Step 1: Check PowerShell Execution Policy
Write-Host "[Step 1/6] Checking PowerShell execution policy..." -NoNewline
$Policy = Get-ExecutionPolicy -Scope CurrentUser
if ($Policy -eq "RemoteSigned" -or $Policy -eq "Unrestricted" -or $Policy -eq "Bypass") {
    Write-Host " OK ($Policy)" -ForegroundColor Green
} else {
    Write-Host " NEEDS FIX ($Policy)" -ForegroundColor Yellow
    $Response = Read-Host "`nWould you like to fix the execution policy now? (Y/N)"
    if ($Response -eq "Y" -or $Response -eq "y") {
        try {
            Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
            Write-Host "✅ Execution policy updated to RemoteSigned" -ForegroundColor Green
        } catch {
            Write-Host "❌ Failed to update policy. Please run as Administrator." -ForegroundColor Red
            Write-Host "   Manual fix: Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned" -ForegroundColor Yellow
            pause
            exit 1
        }
    }
}
Write-Host ""

# Step 2: List VBS files to be replaced
Write-Host "[Step 2/6] Scanning for VBS files in Startup folder..." -ForegroundColor Cyan
$VbsFiles = @(
    "debian-trading-hub.vbs",
    "FileSystemIndexer.vbs",
    "UnifiedTradingHub.vbs",
    "wezterm-trading-hub.vbs"
)

$FoundVbs = @()
foreach ($vbs in $VbsFiles) {
    $vbsPath = Join-Path $StartupFolder $vbs
    if (Test-Path $vbsPath) {
        $FoundVbs += $vbs
        Write-Host "  ❌ Found: $vbs" -ForegroundColor Red
    }
}

if ($FoundVbs.Count -eq 0) {
    Write-Host "  ✅ No VBS files found (already cleaned up)" -ForegroundColor Green
} else {
    Write-Host "  Found $($FoundVbs.Count) VBS file(s) to replace" -ForegroundColor Yellow
}
Write-Host ""

# Step 3: Verify PowerShell scripts exist
Write-Host "[Step 3/6] Verifying PowerShell replacement scripts..." -ForegroundColor Cyan
$PowerShellScripts = @(
    "debian-trading-hub.ps1",
    "FileSystemIndexer.ps1",
    "UnifiedTradingHub.ps1",
    "wezterm-trading-hub.ps1"
)

$MissingScripts = @()
foreach ($ps1 in $PowerShellScripts) {
    $ps1Path = Join-Path $ScriptDir $ps1
    if (Test-Path $ps1Path) {
        Write-Host "  ✅ $ps1" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $ps1 - MISSING" -ForegroundColor Red
        $MissingScripts += $ps1
    }
}

if ($MissingScripts.Count -gt 0) {
    Write-Host "`n❌ ERROR: Missing PowerShell scripts. Cannot proceed." -ForegroundColor Red
    Write-Host "   Please ensure all .ps1 files are in: $ScriptDir" -ForegroundColor Yellow
    pause
    exit 1
}
Write-Host ""

# Step 4: Backup old VBS files
Write-Host "[Step 4/6] Backing up old VBS files..." -ForegroundColor Cyan
$BackupDir = Join-Path $ScriptDir "vbs_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
if ($FoundVbs.Count -gt 0) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    foreach ($vbs in $FoundVbs) {
        $vbsPath = Join-Path $StartupFolder $vbs
        $backupPath = Join-Path $BackupDir $vbs
        try {
            Copy-Item -Path $vbsPath -Destination $backupPath -Force
            Write-Host "  ✅ Backed up: $vbs" -ForegroundColor Green
        } catch {
            Write-Host "  ⚠️  Could not backup: $vbs ($($_.Exception.Message))" -ForegroundColor Yellow
        }
    }
    Write-Host "  Backup location: $BackupDir" -ForegroundColor Yellow
} else {
    Write-Host "  No files to backup" -ForegroundColor Gray
}
Write-Host ""

# Step 5: Install new PowerShell scripts
Write-Host "[Step 5/6] Installing PowerShell scripts to Startup folder..." -ForegroundColor Cyan
$BatchFiles = @(
    "debian-trading-hub.bat",
    "FileSystemIndexer.bat",
    "UnifiedTradingHub.bat",
    "wezterm-trading-hub.bat"
)

$InstalledCount = 0
foreach ($bat in $BatchFiles) {
    $batSource = Join-Path $ScriptDir $bat
    $ps1Source = Join-Path $ScriptDir ($bat -replace '\.bat$', '.ps1')
    $batDest = Join-Path $StartupFolder $bat
    $ps1Dest = Join-Path $StartupFolder ($bat -replace '\.bat$', '.ps1')

    try {
        # Copy both .bat and .ps1 files
        Copy-Item -Path $batSource -Destination $batDest -Force
        Copy-Item -Path $ps1Source -Destination $ps1Dest -Force
        Write-Host "  ✅ Installed: $bat + .ps1" -ForegroundColor Green
        $InstalledCount++
    } catch {
        Write-Host "  ❌ Failed to install: $bat ($($_.Exception.Message))" -ForegroundColor Red
    }
}
Write-Host "  Installed $InstalledCount of $($BatchFiles.Count) script pairs" -ForegroundColor Green
Write-Host ""

# Step 6: Remove old VBS files
Write-Host "[Step 6/6] Removing old VBS files..." -ForegroundColor Cyan
if ($FoundVbs.Count -gt 0) {
    Write-Host "  About to delete $($FoundVbs.Count) VBS file(s) from Startup folder" -ForegroundColor Yellow
    $Response = Read-Host "  Proceed with deletion? (Y/N)"
    if ($Response -eq "Y" -or $Response -eq "y") {
        foreach ($vbs in $FoundVbs) {
            $vbsPath = Join-Path $StartupFolder $vbs
            try {
                Remove-Item -Path $vbsPath -Force
                Write-Host "  ✅ Deleted: $vbs" -ForegroundColor Green
            } catch {
                Write-Host "  ❌ Failed to delete: $vbs ($($_.Exception.Message))" -ForegroundColor Red
                Write-Host "     You may need to delete this manually" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "  Skipped deletion (VBS files still present)" -ForegroundColor Yellow
        Write-Host "  You can manually delete them later from: $StartupFolder" -ForegroundColor Gray
    }
} else {
    Write-Host "  No VBS files to remove" -ForegroundColor Gray
}
Write-Host ""

# Summary
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                                                            ║" -ForegroundColor Green
Write-Host "║                  INSTALLATION COMPLETE                     ║" -ForegroundColor Green
Write-Host "║                                                            ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "✅ PowerShell scripts installed: $InstalledCount" -ForegroundColor Green
Write-Host "✅ Startup folder: $StartupFolder" -ForegroundColor Green
if ($FoundVbs.Count -gt 0) {
    Write-Host "✅ VBS backup: $BackupDir" -ForegroundColor Green
}
Write-Host ""
Write-Host "What happens now:" -ForegroundColor Cyan
Write-Host "  1. Next time you log in to Windows, the new .bat files will run" -ForegroundColor White
Write-Host "  2. They will silently launch PowerShell scripts" -ForegroundColor White
Write-Host "  3. No more VBS security errors!" -ForegroundColor White
Write-Host ""
Write-Host "Testing:" -ForegroundColor Cyan
Write-Host "  You can test each startup script by running the .bat files in:" -ForegroundColor White
Write-Host "  $StartupFolder" -ForegroundColor Yellow
Write-Host ""
Write-Host "Troubleshooting:" -ForegroundColor Cyan
Write-Host "  If a script doesn't work, check:" -ForegroundColor White
Write-Host "    1. PowerShell execution policy (already set to RemoteSigned)" -ForegroundColor White
Write-Host "    2. File paths in the .ps1 scripts are correct" -ForegroundColor White
Write-Host "    3. Required programs (WSL, Python, WezTerm) are installed" -ForegroundColor White
Write-Host ""

# Optional: Test scripts
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Gray
$TestResponse = Read-Host "Would you like to test the startup scripts now? (Y/N)"
if ($TestResponse -eq "Y" -or $TestResponse -eq "y") {
    Write-Host "`nTesting startup scripts..." -ForegroundColor Cyan
    Write-Host ""

    foreach ($bat in $BatchFiles) {
        $batPath = Join-Path $StartupFolder $bat
        Write-Host "Testing: $bat" -ForegroundColor Yellow
        try {
            Start-Process -FilePath $batPath -WindowStyle Hidden
            Write-Host "  ✅ Launched successfully" -ForegroundColor Green
            Start-Sleep -Seconds 2
        } catch {
            Write-Host "  ❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }

    Write-Host "`nAll scripts tested. Check if they started correctly." -ForegroundColor Cyan
    Write-Host "(Look for: WSL terminal, File indexer process, WezTerm windows)" -ForegroundColor Gray
}

Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Gray
Write-Host "Press any key to exit..." -NoNewline
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
