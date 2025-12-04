# COT Agents - WSL2 Quick Start Guide

## ✅ WSL2-Native Solution (Recommended)

I've created a **pure WSL2 solution** using **tmux** (terminal multiplexer). No Windows Terminal or X server needed!

---

## 🚀 Quick Start

### 1. Launch Agents (Demo Mode)

```bash
./START_COT_AGENTS_WSL.sh --demo --single-cycle
```

This will:
- ✅ Create a tmux session named `spartan-cot-agents`
- ✅ Run the agents in the background
- ✅ Ask if you want to attach and view live output

### 2. View Agent Output

```bash
./VIEW_COT_AGENTS.sh
```

Or directly:
```bash
tmux attach -t spartan-cot-agents
```

**To detach:** Press `Ctrl+B`, then press `D`

### 3. Stop Agents

```bash
./STOP_COT_AGENTS.sh
```

Or directly:
```bash
tmux kill-session -t spartan-cot-agents
```

---

## 📋 Available Commands

| Command | What It Does |
|---------|--------------|
| `./START_COT_AGENTS_WSL.sh` | Launch agents in tmux session |
| `./VIEW_COT_AGENTS.sh` | Attach to session (view output) |
| `./STOP_COT_AGENTS.sh` | Stop the session |
| `tmux ls` | List all tmux sessions |

---

## 🎯 Usage Modes

### Demo Mode (4 agents, quick test)
```bash
./START_COT_AGENTS_WSL.sh --demo --single-cycle
```

### Single Cycle (run once)
```bash
./START_COT_AGENTS_WSL.sh --single-cycle
```

### Continuous Mode (runs every hour)
```bash
./START_COT_AGENTS_WSL.sh
```

### Custom Interval (every 2 hours)
```bash
./START_COT_AGENTS_WSL.sh --interval 2
```

---

## 💡 Tmux Basics

### What is tmux?

Tmux is a **terminal multiplexer** that lets you:
- Run programs in the background
- Detach and reattach to sessions
- Keep programs running even if you disconnect
- View output in a separate "virtual terminal"

### Common Tmux Commands

```bash
# List all sessions
tmux ls

# Attach to a session
tmux attach -t spartan-cot-agents

# Detach from current session
Press: Ctrl+B, then D

# Kill a session
tmux kill-session -t spartan-cot-agents

# Create new session
tmux new-session -s my-session

# Rename session
tmux rename-session -t old-name new-name
```

### Inside a Tmux Session

| Shortcut | Action |
|----------|--------|
| `Ctrl+B` then `D` | Detach (session keeps running) |
| `Ctrl+B` then `C` | Create new window |
| `Ctrl+B` then `N` | Next window |
| `Ctrl+B` then `P` | Previous window |
| `Ctrl+B` then `[` | Scroll mode (use arrows, `q` to exit) |
| `Ctrl+C` | Stop the program (in this case, agents) |

---

## 📊 What You'll See

When you attach to the session, you'll see:

```
╔════════════════════════════════════════════════════════════════════╗
║        SPARTAN 100 COT AGENTS - Live Output Monitor               ║
╚════════════════════════════════════════════════════════════════════╝

🤖 Starting autonomous agent system...
📁 Working directory: /mnt/c/Users/Quantum/Downloads/Spartan_Labs/website
⏰ Started at: 2025-11-29 17:57:54

────────────────────────────────────────────────────────────────────

Executing: python3 run_100_agents.py --demo --single-cycle

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
✅ CYCLE COMPLETED in 2.10 seconds
======================================================================

────────────────────────────────────────────────────────────────────
✅ Agent execution completed
⏰ Finished at: 2025-11-29 17:57:56

📊 View trade sheet:
   cat output/latest_trade_sheet.txt

📋 View full logs:
   tail -f logs/agents.log

Press Ctrl+B then D to detach, or Ctrl+C to exit
```

---

## 🔧 Workflow Example

### Typical Usage Flow

```bash
# 1. Start the agents
./START_COT_AGENTS_WSL.sh --demo --single-cycle

# When prompted, choose "Y" to attach and watch

# 2. While agents are running, you can:
#    - Watch the output in real-time
#    - Press Ctrl+B then D to detach and do other work
#    - The agents keep running in background

# 3. Later, check on progress
./VIEW_COT_AGENTS.sh

# 4. When done, stop the session
./STOP_COT_AGENTS.sh
```

### Background Operation

```bash
# Start in background (don't attach)
./START_COT_AGENTS_WSL.sh --demo --single-cycle
# Choose "N" when asked to attach

# Do other work...

# Check logs
tail -f logs/agents.log

# View live session later
./VIEW_COT_AGENTS.sh
```

---

## 🆚 Comparison: Solutions

| Solution | Pros | Cons |
|----------|------|------|
| **WSL Tmux** ✅ | Pure WSL2, no dependencies, stable | Need to learn tmux basics |
| Windows Terminal | Native Windows | Requires wt.exe in PATH |
| Alacritty | Fast, pretty | Needs X server on WSL2 |
| Current terminal | Simple | No background operation |

**Recommendation:** Use the **WSL Tmux** solution for WSL2!

---

## 🐛 Troubleshooting

### Session already exists

```bash
# Kill existing session
./STOP_COT_AGENTS.sh

# Restart
./START_COT_AGENTS_WSL.sh --demo --single-cycle
```

### Can't attach to session

```bash
# Check if session exists
tmux ls

# If no sessions, start one
./START_COT_AGENTS_WSL.sh --demo --single-cycle
```

### Agents not producing output

```bash
# Check logs
tail -f logs/agents.log

# Check database connection
psql -d spartan_research_db -c "SELECT 1;"
```

### Need to scroll up in tmux

1. Press `Ctrl+B` then `[`
2. Use arrow keys or Page Up/Down
3. Press `q` to exit scroll mode

---

## 📁 Files Created

**Main launcher:**
- `START_COT_AGENTS_WSL.sh` - Launch agents in tmux

**Helper scripts:**
- `VIEW_COT_AGENTS.sh` - Attach to session
- `STOP_COT_AGENTS.sh` - Stop session

**Documentation:**
- `COT_AGENTS_WSL_QUICKSTART.md` - This guide

---

## 🎓 Next Steps

1. **First time?** Run demo mode:
   ```bash
   ./START_COT_AGENTS_WSL.sh --demo --single-cycle
   ```

2. **View output:**
   ```bash
   ./VIEW_COT_AGENTS.sh
   ```

3. **Check trade sheet:**
   ```bash
   cat output/latest_trade_sheet.txt
   ```

4. **Run full 100 agents:**
   ```bash
   ./START_COT_AGENTS_WSL.sh --single-cycle
   ```

5. **Schedule for weekends:**
   ```bash
   ./install_cot_agents_melbourne.sh
   ```

---

## ✅ Benefits of This Solution

- ✅ **Pure WSL2** - No Windows dependencies
- ✅ **Background operation** - Agents run even if you close terminal
- ✅ **Attach/Detach** - View output anytime
- ✅ **Persistent** - Sessions survive disconnections
- ✅ **No X server needed** - Works on headless WSL2
- ✅ **Professional** - Industry-standard tool (tmux)

---

**Last Updated:** November 29, 2025
**Status:** ✅ Production Ready - WSL2 Native
