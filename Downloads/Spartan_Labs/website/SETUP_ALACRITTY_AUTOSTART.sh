#!/bin/bash
#
# One-Step Setup for Alacritty Auto-Start
# Run this once to configure everything
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║     SPARTAN COT MONITOR - Alacritty Auto-Start Setup            ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "This will configure Alacritty to auto-start the COT monitor."
echo ""

# Step 1: Create config directory
echo "Step 1: Creating Alacritty config directory..."
mkdir -p ~/.config/alacritty
echo "✅ Created: ~/.config/alacritty"
echo ""

# Step 2: Copy config file
echo "Step 2: Installing Alacritty config..."
cp alacritty_cot_monitor.yml ~/.config/alacritty/alacritty_cot.yml
echo "✅ Installed: ~/.config/alacritty/alacritty_cot.yml"
echo ""

# Step 3: Make scripts executable
echo "Step 3: Making scripts executable..."
chmod +x START_ON_ALACRITTY.sh
chmod +x SIMPLE_DAILY_MONITOR.sh
echo "✅ Scripts are executable"
echo ""

# Step 4: Test the startup script
echo "Step 4: Testing startup script..."
if [ -x START_ON_ALACRITTY.sh ]; then
    echo "✅ START_ON_ALACRITTY.sh is ready"
else
    echo "❌ START_ON_ALACRITTY.sh not executable!"
    exit 1
fi
echo ""

# Step 5: Create Windows desktop shortcut (instructions)
echo "═══════════════════════════════════════════════════════════════════"
echo "SETUP COMPLETE!"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "✅ Alacritty config installed"
echo "✅ Startup scripts ready"
echo ""
echo "NEXT STEPS:"
echo ""
echo "Option 1: Launch Now (Test)"
echo "  Run this command:"
echo "    alacritty --config-file ~/.config/alacritty/alacritty_cot.yml"
echo ""
echo "Option 2: Create Desktop Shortcut (Windows)"
echo "  1. Right-click on your Desktop"
echo "  2. New → Shortcut"
echo "  3. Location: wsl.exe alacritty --config-file ~/.config/alacritty/alacritty_cot.yml"
echo "  4. Name: COT Monitor"
echo "  5. Click Finish"
echo ""
echo "Option 3: Add to Windows Startup (Auto-start on boot)"
echo "  1. Press Win+R"
echo "  2. Type: shell:startup"
echo "  3. Press Enter"
echo "  4. Copy Launch_COT_Monitor.bat to that folder"
echo ""
echo "Option 4: Use Provided .bat File"
echo "  Double-click: Launch_COT_Monitor.bat"
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "FILES CREATED:"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "  ~/.config/alacritty/alacritty_cot.yml  - Alacritty config"
echo "  START_ON_ALACRITTY.sh                  - Startup script"
echo "  Launch_COT_Monitor.bat                 - Windows launcher"
echo "  ALACRITTY_SETUP.md                     - Complete guide"
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "QUICK TEST:"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
read -p "Test launch now? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Launching Alacritty with COT Monitor..."
    echo ""
    alacritty --config-file ~/.config/alacritty/alacritty_cot.yml &
    echo ""
    echo "✅ Alacritty launched!"
    echo "   The monitor should be running now."
    echo ""
else
    echo ""
    echo "Setup complete. Launch when ready with:"
    echo "  alacritty --config-file ~/.config/alacritty/alacritty_cot.yml"
    echo ""
fi

echo "═══════════════════════════════════════════════════════════════════"
echo "For detailed instructions, see: ALACRITTY_SETUP.md"
echo "═══════════════════════════════════════════════════════════════════"
