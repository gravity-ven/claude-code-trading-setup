# Windows Startup Scripts - Troubleshooting & Setup Guide

## 🚨 Why VBScript (.vbs) Files Fail

VBScript files are **frequently blocked** by modern Windows security:

1. **Windows Defender** - Flags .vbs as potential malware
2. **Group Policy** - Enterprises often disable Windows Script Host
3. **UAC Restrictions** - Blocks silent execution without admin approval
4. **Antivirus Software** - Third-party AV blocks .vbs by default
5. **File Associations** - May not be properly linked to wscript.exe

**SOLUTION**: Use PowerShell (.ps1) instead - modern, supported, more reliable.

---

## ✅ Recommended Startup Methods (In Order)

### Method 1: PowerShell Script (BEST - Most Reliable)

**File**: `START_ALPHASTREAM_TERMINAL_SILENT.ps1`

**Features**:
- ✅ Works with Windows Defender enabled
- ✅ No UAC prompts
- ✅ Relative paths (portable)
- ✅ Error checking included
- ✅ Modern Windows support

**Usage**:
```powershell
# Right-click → Run with PowerShell
# OR double-click the .bat wrapper (see below)
```

**First-time setup** (if you get execution policy errors):
```powershell
# Run PowerShell as Administrator, then:
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

---

### Method 2: Batch Wrapper (SILENT - No Console Window)

**File**: `START_ALPHASTREAM_TERMINAL_SILENT.bat`

**Features**:
- ✅ Completely silent (no flashing console)
- ✅ Calls PowerShell script automatically
- ✅ Bypasses execution policy for this script only
- ✅ Double-click to launch

**Usage**:
```
Double-click START_ALPHASTREAM_TERMINAL_SILENT.bat
```

This is the **recommended method** for daily use.

---

### Method 3: Regular Batch File (VISIBLE - Shows Progress)

**File**: `START_ALPHASTREAM_TERMINAL.bat`

**Features**:
- ✅ Shows startup progress
- ✅ No security restrictions
- ✅ Good for troubleshooting
- ✅ Fixed to use relative paths (portable)

**Usage**:
```
Double-click START_ALPHASTREAM_TERMINAL.bat
```

Use this if you want to see what's happening or debug issues.

---

### Method 4: Windows Startup (AUTO-START ON BOOT)

**Goal**: Automatically open AlphaStream Terminal when Windows starts.

#### Option A: Task Scheduler (RECOMMENDED - Most Control)

1. **Open Task Scheduler**:
   - Press `Win + R`
   - Type: `taskschd.msc`
   - Press Enter

2. **Create Basic Task**:
   - Click "Create Basic Task" (right sidebar)
   - Name: `AlphaStream Terminal Startup`
   - Description: `Automatically opens AlphaStream Terminal on login`
   - Click Next

3. **Trigger**:
   - Select "When I log on"
   - Click Next

4. **Action**:
   - Select "Start a program"
   - Click Next

5. **Program/Script**:
   - Browse to: `C:\Users\Quantum\Downloads\Spartan_Labs\website\START_ALPHASTREAM_TERMINAL_SILENT.bat`
   - Leave "Add arguments" blank
   - Click Next

6. **Finish**:
   - Check "Open the Properties dialog when I click Finish"
   - Click Finish

7. **Advanced Settings** (in Properties dialog):
   - **General tab**:
     - ✅ Run whether user is logged on or not
     - ✅ Run with highest privileges (if needed)
   - **Conditions tab**:
     - ❌ Uncheck "Start the task only if the computer is on AC power" (if laptop)
   - **Settings tab**:
     - ✅ Allow task to be run on demand
     - ✅ If the task fails, restart every: 1 minute (try 3 times)
   - Click OK

8. **Test**:
   - Right-click the task → Run
   - Terminal should open in browser

#### Option B: Startup Folder (SIMPLE - Quick Setup)

1. **Open Startup Folder**:
   - Press `Win + R`
   - Type: `shell:startup`
   - Press Enter

2. **Create Shortcut**:
   - Right-click in the Startup folder
   - New → Shortcut
   - Browse to: `C:\Users\Quantum\Downloads\Spartan_Labs\website\START_ALPHASTREAM_TERMINAL_SILENT.bat`
   - Name: `AlphaStream Terminal`
   - Click Finish

3. **Test**:
   - Log out and log back in
   - Terminal should auto-open

**NOTE**: Startup folder method may show a brief console flash. Task Scheduler is cleaner.

---

## 🔧 Troubleshooting

### Issue: PowerShell execution policy error

**Error Message**:
```
File cannot be loaded because running scripts is disabled on this system
```

**Fix**:
```powershell
# Run PowerShell as Administrator, then:
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# Verify:
Get-ExecutionPolicy -List
```

**Explanation**: This allows locally created scripts to run without full admin privileges.

---

### Issue: .vbs file shows security warning

**Error**: Windows Defender blocks execution

**Fix**:
```
❌ DO NOT use .vbs files anymore
✅ Switch to PowerShell (.ps1) method instead
```

**Why**: VBScript is deprecated and increasingly blocked by security software. PowerShell is the modern replacement.

---

### Issue: "File not found" when launching

**Cause**: Hardcoded paths or wrong working directory

**Fix**: Use the updated scripts - they now use relative paths

**Verify**:
```batch
REM Old (BROKEN):
start "" "C:\Users\Quantum\Downloads\Spartan_Labs\website\alphastream_terminal.html"

REM New (FIXED):
start "" "%~dp0alphastream_terminal.html"
```

The `%~dp0` variable means "the directory where this batch file is located".

---

### Issue: Antivirus blocks startup script

**Symptoms**: Script fails silently, no browser opens

**Fix**:
1. Add exclusion in Windows Defender:
   - Open Windows Security
   - Virus & threat protection
   - Manage settings
   - Exclusions → Add an exclusion
   - Add folder: `C:\Users\Quantum\Downloads\Spartan_Labs\website\`

2. If using third-party antivirus:
   - Add the same folder to exclusions/whitelist
   - Or switch to PowerShell method (less likely to be blocked)

---

### Issue: Task Scheduler task shows "Running" but nothing happens

**Causes**:
1. Wrong working directory
2. Script trying to show GUI when running as background service
3. Permissions issue

**Fix**:
1. Edit task properties
2. In "Actions" tab, edit the action
3. Set "Start in (optional)": `C:\Users\Quantum\Downloads\Spartan_Labs\website\`
4. In "General" tab:
   - Change to "Run only when user is logged on" (for GUI apps)
5. Test again

---

## 📋 File Summary

| File | Purpose | Silent? | Recommended? |
|------|---------|---------|--------------|
| `START_ALPHASTREAM_TERMINAL_SILENT.ps1` | PowerShell script (modern) | No* | ⭐ Yes |
| `START_ALPHASTREAM_TERMINAL_SILENT.bat` | Batch wrapper (calls PS1 silently) | Yes | ⭐⭐ BEST |
| `START_ALPHASTREAM_TERMINAL.bat` | Batch script (visible) | No | For debugging |
| `START_ALPHASTREAM_TERMINAL_SILENT.vbs` | VBScript (deprecated) | Yes | ❌ DO NOT USE |

*PowerShell script isn't silent by itself, but the .bat wrapper makes it silent.

---

## 🎯 Quick Start (New User)

**Just want it to work? Do this:**

1. **Double-click**: `START_ALPHASTREAM_TERMINAL_SILENT.bat`
   - If it works → You're done!
   - If you get an error → Continue to step 2

2. **Fix PowerShell execution policy** (one-time):
   - Press `Win + X` → Windows Terminal (Admin)
   - Run: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`
   - Type `Y` and press Enter
   - Close terminal

3. **Try again**: Double-click `START_ALPHASTREAM_TERMINAL_SILENT.bat`
   - Should work now

4. **Optional - Auto-start on boot**:
   - Press `Win + R` → `shell:startup` → Enter
   - Drag `START_ALPHASTREAM_TERMINAL_SILENT.bat` into this folder
   - Done! Will auto-open on next login

---

## 🚀 Advanced: Custom Delay Before Launch

Want to delay the startup (e.g., wait 30 seconds after login)?

**Edit the PowerShell script**:
```powershell
# Add this line at the top of START_ALPHASTREAM_TERMINAL_SILENT.ps1:
Start-Sleep -Seconds 30
```

Or use Task Scheduler trigger delay:
1. Edit task → Triggers → Edit trigger
2. Delay task for: `30 seconds`

---

## 🔐 Security Notes

**Why these scripts are safe**:
- Only open a local HTML file (no network access)
- No system modifications
- No data collection
- No privilege escalation
- Open source (you can read the code)

**What they DO NOT do**:
- ❌ Access the internet (except via the HTML page itself)
- ❌ Modify system files
- ❌ Install software
- ❌ Run background processes
- ❌ Collect personal data

---

## 📞 Still Having Issues?

If none of the above works:

1. **Check Windows Event Viewer**:
   - Press `Win + X` → Event Viewer
   - Windows Logs → Application
   - Look for errors related to PowerShell or Task Scheduler

2. **Try manual PowerShell execution**:
   ```powershell
   cd "C:\Users\Quantum\Downloads\Spartan_Labs\website\"
   .\START_ALPHASTREAM_TERMINAL_SILENT.ps1
   ```
   - Any errors will show here

3. **Verify file exists**:
   ```powershell
   Test-Path "C:\Users\Quantum\Downloads\Spartan_Labs\website\alphastream_terminal.html"
   ```
   - Should return `True`

4. **Check default browser**:
   - Settings → Apps → Default apps
   - Ensure a browser is set as default for .html files

---

**Last Updated**: November 30, 2025
**Status**: Production Ready
**PowerShell Version**: 5.1+ (included in Windows 10/11)
