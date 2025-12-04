# Install Nerd Fonts on Windows (for Windows Terminal)

Since you're using WSL2, you need to install Nerd Fonts **on Windows side** for Windows Terminal to display them properly.

## Quick Install (Recommended)

### Option 1: Scoop (Easiest)

```powershell
# In PowerShell (Windows)
scoop bucket add nerd-fonts
scoop install FiraCode-NF JetBrainsMono-NF Meslo-NF
```

### Option 2: Manual Download

1. **Download fonts**:
   - FiraCode: https://github.com/ryanoasis/nerd-fonts/releases/download/v3.1.1/FiraCode.zip
   - JetBrainsMono: https://github.com/ryanoasis/nerd-fonts/releases/download/v3.1.1/JetBrainsMono.zip
   - Meslo: https://github.com/ryanoasis/nerd-fonts/releases/download/v3.1.1/Meslo.zip

2. **Extract** each .zip file

3. **Install fonts**:
   - Select all `.ttf` files
   - Right-click → "Install for all users"
   - Wait for installation to complete

4. **Restart Windows Terminal**

## Configure Windows Terminal

1. Open Windows Terminal
2. Press `Ctrl+,` to open settings
3. Click "Open JSON file" (bottom left)
4. Add this to your WSL profile:

```json
{
  "profiles": {
    "list": [
      {
        "name": "Debian (WSL)",
        "font": {
          "face": "FiraCode Nerd Font Mono",
          "size": 11,
          "weight": "normal"
        },
        "colorScheme": "Spartan"
      }
    ]
  },
  "schemes": [
    {
      "name": "Spartan",
      "background": "#0a0e14",
      "foreground": "#b3b1ad",
      "black": "#01060e",
      "red": "#ea6c73",
      "green": "#91b362",
      "yellow": "#f9af4f",
      "blue": "#53bdfa",
      "purple": "#fae994",
      "cyan": "#90e1c6",
      "white": "#c7c7c7",
      "brightBlack": "#686868",
      "brightRed": "#f07178",
      "brightGreen": "#c2d94c",
      "brightYellow": "#ffb454",
      "brightBlue": "#59c2ff",
      "brightPurple": "#ffee99",
      "brightCyan": "#95e6cb",
      "brightWhite": "#ffffff",
      "cursorColor": "#ffcc66",
      "selectionBackground": "#33415e"
    }
  ]
}
```

Or use the complete configuration in: `WINDOWS_TERMINAL_NERD_FONTS.json`

## Test Your Setup

After installing and configuring, restart Windows Terminal and run:

```bash
nerd-test
```

You should see icons like:   ⚡

If you see empty boxes, the fonts aren't installed correctly on Windows.

## Troubleshooting

### Icons appear as boxes
- **Problem**: Fonts installed in WSL but not Windows
- **Solution**: Install fonts on Windows side (see steps above)

### Font not appearing in dropdown
- **Problem**: Font name incorrect
- **Solution**: Use exact names:
  - `FiraCode Nerd Font Mono`
  - `JetBrainsMono Nerd Font Mono`
  - `MesloLGS Nerd Font Mono`

### Terminal looks weird after config
- **Problem**: JSON syntax error
- **Solution**: Validate JSON at https://jsonlint.com

## What's Already Done in WSL

✅ Nerd Fonts installed in WSL: `~/.local/share/fonts/NerdFonts/`
✅ Starship prompt configured: `~/.config/starship.toml`
✅ Alacritty config created: `~/.config/alacritty/alacritty.toml`
✅ Custom bash prompt: `~/.bash_prompt_nerd`
✅ `.bashrc` updated with Starship integration

## Next Steps

1. Install fonts on Windows (above)
2. Configure Windows Terminal (above)
3. Restart Windows Terminal
4. Open new WSL tab
5. You'll see the beautiful Starship prompt with icons!

## Quick Links

- **Nerd Fonts**: https://www.nerdfonts.com/
- **Starship Prompt**: https://starship.rs/
- **Icon Cheat Sheet**: https://www.nerdfonts.com/cheat-sheet
- **Windows Terminal Docs**: https://learn.microsoft.com/en-us/windows/terminal/

---

**Status**: WSL configuration complete ✅
**Remaining**: Install fonts on Windows and configure Windows Terminal
