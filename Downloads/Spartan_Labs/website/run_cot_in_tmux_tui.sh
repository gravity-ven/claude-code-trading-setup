#!/bin/bash
#
# Runner script for tmux session - TUI VERSION
# This is executed inside the tmux session with beautiful dashboard
#

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Run the TUI dashboard
python3 run_cot_tui.py "$@"

# Keep session alive
echo ""
echo "Press Enter to close this session..."
read -r
