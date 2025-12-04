# Spartan COT Agents - Live TUI Dashboard

**Beautiful real-time terminal interface with live updates**

---

## 🚀 Quick Start

### Launch Live TUI

```bash
# Run with real agents (parses actual log output)
./START_LIVE_TUI.sh --demo

# Run with simulated data (for testing/demo)
./START_LIVE_TUI.sh --simulate

# Production mode (all 100 agents)
./START_LIVE_TUI.sh
```

---

## 📊 What You'll See

### Live Dashboard Layout

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│         ⚔️  SPARTAN COT AGENTS  •  Intelligence Dashboard      │
│                                                                │
│  🎮 DEMO MODE  •  Started: 2025-11-29 18:45:30  •  Elapsed: 5.2s│
└────────────────────────────────────────────────────────────────┘

╭───── 📊 COT Analysis ─────╮  ╭───── 📅 Seasonality ─────╮
│                           │  │                          │
│ ✅ Analyzing CFTC reports  │  │ ⏳ Waiting to start...   │
│                           │  │                          │
│ Results:                  │  │                          │
│  • Fetching COT data...   │  │                          │
│  • ✅ Gold (GC): -61,457   │  │                          │
│  • ✅ COT Index: 50.00     │  │                          │
╰───────────────────────────╯  ╰──────────────────────────╯

╭───── 🎯 Confluence ───────╮  ╭───── 💰 Trade Sheets ────╮
│                           │  │                          │
│ ⏳ Waiting to start...    │  │ ⏳ Waiting to start...   │
│                           │  │                          │
╰───────────────────────────╯  ╰──────────────────────────╯

╭────────────────── Execution Summary ──────────────────────╮
│                                                           │
│ Tier               │ Status        │ Findings             │
│────────────────────┼───────────────┼─────────────────────│
│ 📊 COT Analysis    │ ✅ Completed  │ 1 items              │
│ 📅 Seasonality     │ ⏳ Pending    │ No data yet          │
│ 🎯 Confluence      │ ⏳ Pending    │ No data yet          │
│ 💰 Trade Sheets    │ ⏳ Pending    │ No data yet          │
│                                                           │
│ 📋 Logs: tail -f logs/agents.log  •  Trade Sheet: ./SHOW_TRADE_SHEET.sh │
╰───────────────────────────────────────────────────────────╯
```

---

## 🎨 Features

### Real-Time Updates
- **Live status tracking** - Watch agents progress through all 4 tiers
- **Dynamic panels** - Status changes from ⏳ Pending → ⚡ Running → ✅ Completed
- **Result streaming** - See results as they come in from agent logs

### Beautiful Design
- **Color-coded indicators**:
  - 🔵 Cyan = Headers
  - 🟢 Green = Success
  - 🟡 Yellow = Running
  - ⚪ White = Info
  - 🔴 Red = Errors

- **Panel borders**:
  - COT Analysis: Cyan
  - Seasonality: Yellow
  - Confluence: Magenta
  - Trade Sheets: Green

### Plain English Results
- No technical jargon
- Clear, actionable messages
- Human-readable summaries

---

## 📖 How It Works

### Tier Progression

**1. Initialization**
- All tiers show ⏳ Pending
- Dashboard displays "Waiting to start..."

**2. Tier 1: COT Analysis** ⚡
- Status changes to ⚡ Running
- Live results stream:
  ```
  • Fetching COT data from CFTC.gov...
  • ✅ Gold (GC): Commercial Net = -61,457
  • ✅ Stored raw COT data for GC
  • ✅ COT Index calculated: 50.00 (neutral)
  ```
- Changes to ✅ Completed

**3. Tier 2: Seasonality** ⚡
- Automatically starts when Tier 1 completes
- Shows seasonal patterns:
  ```
  • Analyzing monthly patterns...
  • ✅ December shows bullish bias in precious metals
  • ✅ Q4 rally pattern identified
  ```

**4. Tier 3: Confluence** ⚡
- Combines signals from Tiers 1 & 2
- Calculates confidence scores:
  ```
  • Calculating confluence scores...
  • ✅ Confluence score: 65/100 (moderate)
  • Need COT extreme for high confidence
  ```

**5. Tier 4: Trade Sheets** ⚡
- Generates actionable recommendations
- If no opportunities:
  ```
  • ⚠️ No high-confidence setups at this time
  • COT Index is neutral (need < 5 or > 95)
  • System needs 26 weeks of data for extremes
  ```

---

## 🎯 Two Modes

### Real Mode (Default)
```bash
./START_LIVE_TUI.sh --demo
```

**How it works**:
- Spawns actual `run_100_agents.py` process
- Parses stdout/stderr logs in real-time
- Extracts interesting messages (✅, ⚠️, ❌)
- Updates panels as data comes in

**Use when**: Running actual COT analysis

### Simulate Mode (Testing)
```bash
./START_LIVE_TUI.sh --simulate
```

**How it works**:
- Simulates agent execution with delays
- Shows pre-defined sample results
- No actual CFTC API calls

**Use when**:
- Testing the TUI interface
- Demonstrating the system
- No internet connection

---

## 🔧 Customization

### Adjust Refresh Rate

Edit `run_cot_live_tui.py`:

```python
with Live(
    self.generate_layout(),
    console=console,
    screen=True,
    refresh_per_second=4  # Change this (default: 4 FPS)
) as live:
```

Higher = smoother updates, more CPU
Lower = less CPU, choppier updates

### Change Result Limit

Show more/fewer results per tier:

```python
# In create_tier_panel method
for result in results[:8]:  # Change 8 to show more/fewer
    content.append(f"  • {result}\n", style="dim white")
```

### Modify Tier Colors

Edit the `tier_info` dictionary:

```python
tier_info = {
    1: ('📊 COT Analysis', 'cyan', 'Description...'),     # Change 'cyan'
    2: ('📅 Seasonality', 'yellow', 'Description...'),    # Change 'yellow'
    3: ('🎯 Confluence', 'magenta', 'Description...'),    # Change 'magenta'
    4: ('💰 Trade Sheets', 'green', 'Description...'),    # Change 'green'
}
```

Available colors: cyan, yellow, magenta, green, red, blue, white

---

## 💡 Tips

### Best Terminal Settings

**Font**: Use monospace fonts (Consolas, Fira Code, JetBrains Mono)
**Size**: Minimum 120x30 characters
**Colors**: Enable 256-color or true-color support

### WSL2 Optimization

```bash
# For better rendering in WSL2
export TERM=xterm-256color

# Add to ~/.bashrc for permanent
echo 'export TERM=xterm-256color' >> ~/.bashrc
```

### tmux Usage (Optional)

Run in tmux for detachable sessions:

```bash
# Start tmux
tmux new -s cot-tui

# Run TUI
./START_LIVE_TUI.sh --demo

# Detach (keep running)
Ctrl+B, then D

# Re-attach later
tmux attach -t cot-tui
```

---

## 🐛 Troubleshooting

### "required file not found"
```bash
# Fix line endings
dos2unix START_LIVE_TUI.sh
# Or
sed -i 's/\r$//' START_LIVE_TUI.sh
```

### Garbled output
- Terminal too small (need minimum 120x30)
- Font not monospace
- Color support disabled

**Fix**:
```bash
# Check terminal size
tput cols  # Should be >= 120
tput lines # Should be >= 30

# Check color support
tput colors  # Should be 256 or more
```

### Results not updating
- Check if agents are actually running:
  ```bash
  tail -f logs/agents.log
  ```
- Verify Python Rich library installed:
  ```bash
  pip install rich
  ```

### Panel borders look weird
- Use a terminal with Unicode support
- Try different terminal emulator (Windows Terminal, iTerm2, Alacritty)

---

## 📊 Comparison: Old vs New TUI

### Old TUI (run_cot_tui.py)
- Static output
- No live updates
- Results shown after completion

### New TUI (run_cot_live_tui.py) ✅
- **Live updates** - Real-time panel changes
- **Dynamic status** - Pending → Running → Completed
- **Streaming results** - See progress as it happens
- **Rich formatting** - Beautiful panels and tables
- **Interactive** - Ctrl+C to exit cleanly

---

## 🚀 Quick Commands Reference

```bash
# Launch live TUI (recommended)
./START_LIVE_TUI.sh --demo

# Simulate for testing
./START_LIVE_TUI.sh --simulate

# Run in background (tmux)
tmux new -s cot-tui -d "./START_LIVE_TUI.sh --demo"
tmux attach -t cot-tui

# Direct Python execution
python3 run_cot_live_tui.py --demo
python3 run_cot_live_tui.py --simulate

# After completion, view results
./SHOW_TRADE_SHEET.sh
tail -f logs/agents.log
```

---

## 📁 Files

### Main Files
- `run_cot_live_tui.py` - Live TUI Python script
- `START_LIVE_TUI.sh` - Launcher script
- `LIVE_TUI_GUIDE.md` - This guide

### Supporting Files
- `run_cot_tui.py` - Original static TUI (deprecated)
- `run_100_agents.py` - Agent orchestrator
- `logs/agents.log` - Detailed execution logs

---

## ✅ Summary

**What You Have**:
- ✅ Beautiful live TUI with real-time updates
- ✅ 4-tier panel layout (COT, Seasonality, Confluence, Trade Sheets)
- ✅ Color-coded status indicators
- ✅ Plain English results
- ✅ Summary table showing progress
- ✅ Two modes: Real and Simulated

**How to Use**:
1. Run `./START_LIVE_TUI.sh --demo`
2. Watch agents execute in real-time
3. See results update live in each panel
4. View final summary when complete

**Next Steps**:
- Use `--simulate` mode to see it in action
- Use `--demo` mode to run actual agents
- Customize colors/refresh rate as needed

---

**Created**: November 29, 2025
**Status**: ✅ Production Ready
**Technology**: Python Rich library + Live display

*Enjoy your beautiful TUI dashboard!* ⚔️
