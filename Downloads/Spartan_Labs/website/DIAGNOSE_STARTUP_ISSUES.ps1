# Startup Script Diagnostic Tool
# Automatically checks for common issues preventing scripts from running

Write-Host "`n=== AlphaStream Terminal Startup Diagnostics ===" -ForegroundColor Cyan
Write-Host "Checking system configuration...`n" -ForegroundColor Yellow

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Issues = @()
$Fixes = @()

# Test 1: Check if HTML file exists
Write-Host "[1/7] Checking HTML file..." -NoNewline
$HtmlPath = Join-Path $ScriptDir "alphastream_terminal.html"
if (Test-Path $HtmlPath) {
    Write-Host " OK" -ForegroundColor Green
} else {
    Write-Host " FAILED" -ForegroundColor Red
    $Issues += "HTML file not found at: $HtmlPath"
    $Fixes += "Ensure alphastream_terminal.html is in the same directory as startup scripts"
}

# Test 2: Check PowerShell execution policy
Write-Host "[2/7] Checking PowerShell execution policy..." -NoNewline
$Policy = Get-ExecutionPolicy -Scope CurrentUser
if ($Policy -eq "RemoteSigned" -or $Policy -eq "Unrestricted" -or $Policy -eq "Bypass") {
    Write-Host " OK ($Policy)" -ForegroundColor Green
} else {
    Write-Host " ISSUE ($Policy)" -ForegroundColor Yellow
    $Issues += "PowerShell execution policy is too restrictive: $Policy"
    $Fixes += "Run in Admin PowerShell: Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned"
}

# Test 3: Check if default browser is set
Write-Host "[3/7] Checking default browser..." -NoNewline
try {
    $DefaultBrowser = (Get-ItemProperty "HKCU:\Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice" -ErrorAction SilentlyContinue).ProgId
    if ($DefaultBrowser) {
        Write-Host " OK ($DefaultBrowser)" -ForegroundColor Green
    } else {
        Write-Host " WARNING" -ForegroundColor Yellow
        $Issues += "No default browser detected"
        $Fixes += "Set a default browser: Settings → Apps → Default apps"
    }
} catch {
    Write-Host " WARNING" -ForegroundColor Yellow
}

# Test 4: Check Windows Script Host (for VBS compatibility)
Write-Host "[4/7] Checking Windows Script Host..." -NoNewline
$WScriptPath = "$env:SystemRoot\System32\wscript.exe"
if (Test-Path $WScriptPath) {
    Write-Host " OK" -ForegroundColor Green
} else {
    Write-Host " MISSING" -ForegroundColor Red
    $Issues += "Windows Script Host not found (needed for .vbs files)"
    $Fixes += "Use PowerShell scripts instead of VBScript (.vbs)"
}

# Test 5: Check for antivirus interference
Write-Host "[5/7] Checking Windows Defender status..." -NoNewline
try {
    $DefenderStatus = Get-MpPreference -ErrorAction SilentlyContinue
    if ($DefenderStatus) {
        $ExclusionPaths = $DefenderStatus.ExclusionPath
        if ($ExclusionPaths -contains $ScriptDir) {
            Write-Host " OK (Excluded)" -ForegroundColor Green
        } else {
            Write-Host " ACTIVE (No exclusion)" -ForegroundColor Yellow
            $Issues += "This directory not excluded from Windows Defender"
            $Fixes += "Consider adding exclusion: Settings → Windows Security → Virus & threat protection → Exclusions"
        }
    } else {
        Write-Host " N/A" -ForegroundColor Gray
    }
} catch {
    Write-Host " N/A" -ForegroundColor Gray
}

# Test 6: Check file permissions
Write-Host "[6/7] Checking file permissions..." -NoNewline
try {
    $Acl = Get-Acl $ScriptDir
    $CurrentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    $HasPermissions = $false
    foreach ($Access in $Acl.Access) {
        if ($Access.IdentityReference -eq $CurrentUser -and $Access.FileSystemRights -match "Read") {
            $HasPermissions = $true
            break
        }
    }
    if ($HasPermissions) {
        Write-Host " OK" -ForegroundColor Green
    } else {
        Write-Host " WARNING" -ForegroundColor Yellow
        $Issues += "May have insufficient permissions on directory"
    }
} catch {
    Write-Host " OK" -ForegroundColor Green
}

# Test 7: Test actual browser launch
Write-Host "[7/7] Testing browser launch..." -NoNewline
try {
    # Try to launch but immediately close (just testing if command works)
    $TestFile = [System.IO.Path]::GetTempFileName() + ".html"
    "<html><body>Test</body></html>" | Out-File -FilePath $TestFile -Encoding UTF8
    Start-Process $TestFile
    Start-Sleep -Seconds 1
    Remove-Item $TestFile -Force -ErrorAction SilentlyContinue
    Write-Host " OK" -ForegroundColor Green
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    $Issues += "Cannot launch default browser: $_"
    $Fixes += "Check default browser settings and file associations"
}

# Summary
Write-Host "`n=== DIAGNOSTIC SUMMARY ===" -ForegroundColor Cyan

if ($Issues.Count -eq 0) {
    Write-Host "`nNo issues found! Your system is configured correctly." -ForegroundColor Green
    Write-Host "`nRecommended startup method:" -ForegroundColor Yellow
    Write-Host "  Double-click: START_ALPHASTREAM_TERMINAL_SILENT.bat" -ForegroundColor White
} else {
    Write-Host "`nFound $($Issues.Count) issue(s):" -ForegroundColor Yellow
    for ($i = 0; $i -lt $Issues.Count; $i++) {
        Write-Host "`n  Issue $($i + 1):" -ForegroundColor Red
        Write-Host "    $($Issues[$i])" -ForegroundColor White
        Write-Host "  Fix:" -ForegroundColor Green
        Write-Host "    $($Fixes[$i])" -ForegroundColor White
    }
}

# Quick fix option for execution policy
if ($Policy -ne "RemoteSigned" -and $Policy -ne "Unrestricted") {
    Write-Host "`n=== QUICK FIX AVAILABLE ===" -ForegroundColor Cyan
    $Response = Read-Host "`nWould you like to fix the PowerShell execution policy now? (Y/N)"
    if ($Response -eq "Y" -or $Response -eq "y") {
        try {
            Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
            Write-Host "Execution policy updated successfully!" -ForegroundColor Green
        } catch {
            Write-Host "Failed to update policy. Please run PowerShell as Administrator and try again." -ForegroundColor Red
        }
    }
}

Write-Host "`nFor detailed troubleshooting, see: WINDOWS_STARTUP_GUIDE.md" -ForegroundColor Cyan
Write-Host "`n=== Diagnostics Complete ===" -ForegroundColor Cyan

# Keep window open
Write-Host "`nPress any key to exit..." -NoNewline
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
