# COT Agents - Quick Start Guide

## Launch COT Agents in a New Terminal Window

I've created **two launcher scripts** for you to run the 100 COT agents with live output in a separate terminal window.

---

## Option 1: Windows Terminal (Recommended for WSL2)

```bash
./START_COT_AGENTS_TERMINAL.sh
```

**What it does:**
- Opens a new Windows Terminal tab/window
- Runs the COT agents with live colorized output
- Shows real-time progress as agents execute

**Usage modes:**
```bash
# Demo mode (4 agents, quick test)
./START_COT_AGENTS_TERMINAL.sh --demo

# Single cycle (run once)
./START_COT_AGENTS_TERMINAL.sh --demo --single-cycle

# Continuous mode (runs every hour)
./START_COT_AGENTS_TERMINAL.sh
```

---

## Option 2: Alacritty Terminal

```bash
./START_COT_AGENTS_ALACRITTY.sh
```

**Requirements:**
- Alacritty must be installed
- X server (VcXsrv/WSLg) if on WSL2

**Install Alacritty:**
- Windows: Download from https://github.com/alacritty/alacritty/releases
- Linux: `cargo install alacritty` or `sudo apt install alacritty`

---

## Option 3: Current Terminal (No New Window)

```bash
python3 run_100_agents.py --demo --single-cycle
```

Runs agents directly in your current terminal (no separate window).

---

## Troubleshooting

### "wt.exe not found" or Terminal doesn't open

**Solution 1: Add Windows Terminal to PATH**
```bash
# Find wt.exe location
cmd.exe /c "where wt.exe"

# Add to PATH in ~/.bashrc
export PATH="$PATH:/mnt/c/Users/YourUser/AppData/Local/Microsoft/WindowsApps"
source ~/.bashrc
```

**Solution 2: Use full path**

Edit `START_COT_AGENTS_TERMINAL.sh` and replace `wt.exe` with full path:
```bash
/mnt/c/Users/Quantum/AppData/Local/Microsoft/WindowsApps/wt.exe
```

**Solution 3: Use current terminal**
```bash
python3 run_100_agents.py --demo
```

### Alacritty not working on WSL2

You need an X server running:

1. **Install VcXsrv** (Windows): https://sourceforge.net/projects/vcxsrv/
2. **Start VcXsrv** with "Disable access control" checked
3. **Set DISPLAY in WSL:**
   ```bash
   export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
   ```
4. **Then try again:**
   ```bash
   ./START_COT_AGENTS_ALACRITTY.sh --demo
   ```

### Agents run but no output

Check logs:
```bash
tail -f logs/agents.log
```

### Permission denied

```bash
chmod +x START_COT_AGENTS_TERMINAL.sh
chmod +x START_COT_AGENTS_ALACRITTY.sh
```

---

## What You'll See

When you run the launcher, you'll see a new terminal window with:

```
╔════════════════════════════════════════════════════════════════════╗
║        SPARTAN 100 COT AGENTS - Live Output Monitor               ║
╚════════════════════════════════════════════════════════════════════╝

🤖 Starting autonomous agent system...
📁 Working directory: /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website
⏰ Started at: 2025-11-29 06:45:00

────────────────────────────────────────────────────────────────────

🚀 Initializing Spartan 100 Agent System
📊 DEMO MODE: Initializing minimal agent subset
✅ Initialized 4 agents

======================================================================
🚀 STARTING SINGLE CYCLE
======================================================================

📊 TIER 1: COT Analysis (Agents 1-30)
----------------------------------------------------------------------
🚀 Gold_COT_Agent analyzing GC futures...
✅ Gold_COT_Agent completed

📅 TIER 2: Seasonality Analysis (Agents 31-55)
----------------------------------------------------------------------
🚀 Monthly_Seasonal_Agent analyzing monthly patterns...
✅ Monthly_Seasonal_Agent completed

🎯 TIER 3: Confluence Models (Agents 56-80)
----------------------------------------------------------------------
🚀 Confluence_Model_Agent calculating confluence scores...
✅ Confluence_Model_Agent completed

💰 TIER 4: Risk Management & Trade Sheets (Agents 81-100)
----------------------------------------------------------------------
🚀 Trade_Sheet_Generator generating trade sheet...
✅ Trade sheet saved to output/latest_trade_sheet.txt

======================================================================
✅ CYCLE COMPLETED in 12.34 seconds
======================================================================
```

---

## Next Steps

1. **First time?** Run demo mode:
   ```bash
   ./START_COT_AGENTS_TERMINAL.sh --demo --single-cycle
   ```

2. **Works?** View the trade sheet:
   ```bash
   cat output/latest_trade_sheet.txt
   ```

3. **Ready for production?** Run full 100 agents:
   ```bash
   ./START_COT_AGENTS_TERMINAL.sh --single-cycle
   ```

4. **Schedule it?** Install Melbourne weekend schedule:
   ```bash
   ./install_cot_agents_melbourne.sh
   ```

---

## Files Created

- `START_COT_AGENTS_TERMINAL.sh` - Windows Terminal launcher
- `START_COT_AGENTS_ALACRITTY.sh` - Alacritty launcher
- `run_cot_agents_live.sh` - Runner script (auto-created)
- `QUICKSTART_COT_AGENTS.md` - This guide

---

**Last Updated:** November 29, 2025
