# Auto-Start COT Monitor on Alacritty

## Quick Setup (Choose One Method)

### Method 1: Dedicated Alacritty Instance (Recommended)

**Step 1**: Create Alacritty config directory
```bash
# In WSL
mkdir -p ~/.config/alacritty
```

**Step 2**: Copy the config file
```bash
cp alacritty_cot_monitor.yml ~/.config/alacritty/alacritty_cot.yml
```

**Step 3**: Create desktop shortcut (Windows)

Create a file: `C:\Users\Quantum\Desktop\COT Monitor.bat`

```batch
@echo off
wsl.exe alacritty --config-file ~/.config/alacritty/alacritty_cot.yml
```

**Step 4**: Double-click the shortcut

Alacritty opens and auto-starts the monitor!

---

### Method 2: Default Alacritty Config

**Step 1**: Edit your main Alacritty config
```bash
# Open config
nano ~/.config/alacritty/alacritty.yml
```

**Step 2**: Add this to the `shell:` section
```yaml
shell:
  program: /bin/bash
  args:
    - -c
    - /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/START_ON_ALACRITTY.sh
```

**Step 3**: Save and restart Alacritty

Now **every** Alacritty window runs the monitor!

---

### Method 3: Bash Profile Auto-Start

**Step 1**: Edit your `.bashrc`
```bash
nano ~/.bashrc
```

**Step 2**: Add this at the end
```bash
# Auto-start COT Monitor
if [ -z "$COT_MONITOR_STARTED" ]; then
    export COT_MONITOR_STARTED=1
    cd /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website
    ./SIMPLE_DAILY_MONITOR.sh
fi
```

**Step 3**: Save and restart Alacritty

Monitor starts automatically!

---

### Method 4: Windows Startup (Boot-time)

**Step 1**: Create startup script

Save as: `C:\Users\Quantum\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\start_cot_monitor.vbs`

```vbscript
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "wsl.exe alacritty --config-file ~/.config/alacritty/alacritty_cot.yml", 0
Set WshShell = Nothing
```

**Step 2**: Restart Windows

Monitor starts automatically when you log in!

---

## Comparison of Methods

| Method | When It Starts | Good For |
|--------|----------------|----------|
| **Method 1** | When you click shortcut | Best - dedicated monitor window |
| **Method 2** | Every Alacritty window | If you want it always |
| **Method 3** | Every bash session | Simple setup |
| **Method 4** | Windows startup | True 24/7 monitoring |

---

## Recommended: Method 1 + Method 4

1. **Method 1**: Quick access via desktop shortcut
2. **Method 4**: Auto-starts on Windows boot

This gives you both convenience and 24/7 monitoring!

---

## What You'll See

When Alacritty opens:

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║           SPARTAN COT AGENTS - Daily Market Monitor             ║
║                                                                  ║
║  Analyzing markets using real CFTC data (professional traders)  ║
║  Updates: Every 24 hours                                         ║
║  Press Ctrl+C to stop                                            ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

Starting in 3 seconds...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CYCLE #1 - 2025-11-29 19:30:00
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Running COT analysis...
✅ Fetched COT data for GC: Commercial Net = -61457
✅ Cycle #1 complete!

[Trade sheet displayed here...]

Waiting 24 hours until next check...
Next cycle in: 23 hours 59 minutes
```

---

## Customization

### Change Window Title
Edit `alacritty_cot_monitor.yml`:
```yaml
window:
  title: "Your Custom Title"
```

### Change Font Size
```yaml
font:
  size: 14.0  # Bigger text
```

### Change Colors
The config includes a "Spartan" dark theme. Modify as needed.

---

## Troubleshooting

### Alacritty doesn't start the monitor

**Check 1**: Is the path correct?
```bash
# Verify script exists
ls -lh /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/START_ON_ALACRITTY.sh

# Check it's executable
chmod +x /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/START_ON_ALACRITTY.sh
```

**Check 2**: Config file in right place?
```bash
# Should be here:
ls ~/.config/alacritty/alacritty_cot.yml
```

**Check 3**: Test the script manually
```bash
/mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/START_ON_ALACRITTY.sh
```

### Monitor exits immediately

**Cause**: Error in script

**Fix**: Check logs
```bash
tail -f /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/logs/agents.log
```

### Want to run a normal Alacritty too

**Solution**: Use Method 1 (dedicated config)

Regular Alacritty:
```bash
alacritty
```

Monitor Alacritty:
```bash
alacritty --config-file ~/.config/alacritty/alacritty_cot.yml
```

### Windows Startup doesn't work

**Check**: Startup folder location
```
C:\Users\Quantum\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\
```

**Alternative**: Use Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: At startup
4. Action: Start program
5. Program: `wsl.exe`
6. Arguments: `alacritty --config-file ~/.config/alacritty/alacritty_cot.yml`

---

## Stopping the Monitor

### Temporary Stop
Press `Ctrl+C` in the Alacritty window

### Close Window
Click the X button (monitor stops)

### Disable Auto-Start
- **Method 1**: Don't click the shortcut
- **Method 2**: Remove `shell:` section from config
- **Method 3**: Comment out `.bashrc` lines
- **Method 4**: Delete startup script

---

## Advanced: Multiple Monitors

Run different monitors simultaneously:

**Monitor 1**: Daily (24 hours)
```bash
alacritty --config-file ~/.config/alacritty/alacritty_cot.yml
```

**Monitor 2**: Hourly (testing)
```bash
# Create alacritty_cot_hourly.yml with different interval
alacritty --config-file ~/.config/alacritty/alacritty_cot_hourly.yml
```

---

## Quick Reference Commands

```bash
# Create config directory
mkdir -p ~/.config/alacritty

# Copy config
cp alacritty_cot_monitor.yml ~/.config/alacritty/alacritty_cot.yml

# Make script executable
chmod +x START_ON_ALACRITTY.sh

# Test manually
./START_ON_ALACRITTY.sh

# Launch with custom config
alacritty --config-file ~/.config/alacritty/alacritty_cot.yml

# View trade sheet while running
cat output/latest_trade_sheet.txt

# Check if running (in another terminal)
ps aux | grep SIMPLE_DAILY_MONITOR
```

---

## Files Created

1. ✅ `START_ON_ALACRITTY.sh` - Startup script
2. ✅ `alacritty_cot_monitor.yml` - Alacritty config
3. ✅ `ALACRITTY_SETUP.md` - This guide

---

## Summary

**Best Setup** (Method 1 + 4):

1. **Desktop shortcut** for quick access
2. **Windows startup** for 24/7 monitoring

**Quick Start**:
```bash
# 1. Make executable
chmod +x START_ON_ALACRITTY.sh

# 2. Copy config
mkdir -p ~/.config/alacritty
cp alacritty_cot_monitor.yml ~/.config/alacritty/alacritty_cot.yml

# 3. Create desktop shortcut
# Save as: C:\Users\Quantum\Desktop\COT Monitor.bat
# Contents: wsl.exe alacritty --config-file ~/.config/alacritty/alacritty_cot.yml

# 4. Double-click shortcut!
```

Monitor auto-starts, runs forever, analyzes markets daily with real CFTC data.

---

**Created**: November 29, 2025
**Status**: ✅ Ready for Alacritty auto-start
**Supports**: WSL2 + Windows Alacritty
