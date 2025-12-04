# Nerd Fonts Setup Complete

## Installation Summary

✅ **186 Nerd Fonts installed successfully** in `~/.local/share/fonts/NerdFonts/`

### Installed Font Families

1. **FiraCode Nerd Font** (18 variants)
   - Best for: Coding with ligatures
   - Supports: Programming ligatures (→, ===, !=, etc.)

2. **JetBrains Mono Nerd Font** (96 variants)
   - Best for: Clean, modern development
   - Supports: All weights and styles

3. **Meslo LG Nerd Font** (72 variants)
   - Best for: Classic terminal aesthetics
   - Supports: Powerline, devicons

## Configuration Instructions

### Windows Terminal (Recommended for WSL2)

1. Open Windows Terminal
2. Press `Ctrl+,` to open settings
3. Add to your WSL profile:

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
        }
      }
    ]
  }
}
```

### Alacritty

Create `~/.config/alacritty/alacritty.yml`:

```yaml
font:
  normal:
    family: "FiraCode Nerd Font Mono"
    style: Regular
  bold:
    family: "FiraCode Nerd Font Mono"
    style: Bold
  italic:
    family: "FiraCode Nerd Font Mono"
    style: Italic
  size: 12.0
```

Or for TOML format (`alacritty.toml`):

```toml
[font]
size = 12.0

[font.normal]
family = "FiraCode Nerd Font Mono"
style = "Regular"

[font.bold]
family = "FiraCode Nerd Font Mono"
style = "Bold"
```

### VSCode

Add to `settings.json` (`Ctrl+,` → search "settings.json"):

```json
{
  "terminal.integrated.fontFamily": "FiraCode Nerd Font Mono",
  "editor.fontFamily": "FiraCode Nerd Font",
  "editor.fontLigatures": true,
  "terminal.integrated.fontSize": 13
}
```

### tmux

Add to `~/.tmux.conf`:

```bash
# Nerd Fonts support
set-option -g status-left " #[fg=brightwhite] #S"
set-option -g status-right "#[fg=brightwhite]  %H:%M "
```

## Font Names Reference

Use these exact names in your terminal configuration:

**Mono fonts** (fixed-width, recommended for terminals):
- `FiraCode Nerd Font Mono`
- `JetBrainsMono Nerd Font Mono`
- `MesloLGS Nerd Font Mono`

**Regular fonts** (proportional):
- `FiraCode Nerd Font`
- `JetBrainsMono Nerd Font`
- `MesloLGS Nerd Font`

## Testing Your Setup

After configuring your terminal, test with:

```bash
echo -e "\n=== NERD FONT ICON TEST ===\n"
echo -e "  Folder"
echo -e "  Git branch"
echo -e "  Lock"
echo -e "  Python"
echo -e "  Linux"
echo -e "⚡  Lightning"
echo -e "  Check"
echo -e "  Database"
```

You should see icons instead of empty boxes.

## Powerline/Oh-My-Posh/Starship Support

These fonts include all glyphs needed for:

- ✅ Powerline
- ✅ Oh My Posh
- ✅ Starship prompt
- ✅ Vim/Neovim devicons
- ✅ Ranger file manager icons
- ✅ tmux status bars

## Troubleshooting

### Icons appear as boxes or empty spaces

**WSL2 Issue**: Fonts are installed in WSL, but Windows Terminal needs to access them on Windows side.

**Solution**: Install fonts on Windows:

1. Download fonts again on Windows:
   - Visit: https://www.nerdfonts.com/font-downloads
   - Download: FiraCode Nerd Font, JetBrains Mono Nerd Font

2. Extract and install:
   - Right-click `.ttf` files
   - Select "Install for all users"

3. Restart Windows Terminal

### Font not appearing in dropdown

- Make sure you used exact font name (e.g., `FiraCode Nerd Font Mono`)
- Restart your terminal/editor
- Check font cache: `fc-cache -fv`

### Ligatures not working

- Ensure you're using the non-Mono variant: `FiraCode Nerd Font`
- Enable ligatures in editor settings
- VSCode: `"editor.fontLigatures": true`

## Recommended Font Sizes

- **FiraCode**: 11-13pt
- **JetBrains Mono**: 12-14pt
- **Meslo**: 11-12pt

## Additional Resources

- **Nerd Fonts Website**: https://www.nerdfonts.com/
- **Cheat Sheet**: https://www.nerdfonts.com/cheat-sheet
- **Font Patcher**: https://github.com/ryanoasis/nerd-fonts#font-patcher

## Installation Location

```
~/.local/share/fonts/NerdFonts/
├── FiraCodeNerdFont-*.ttf (18 files)
├── JetBrainsMonoNerdFont-*.ttf (96 files)
└── MesloLG*NerdFont-*.ttf (72 files)
```

## Verify Installation

```bash
# List all installed Nerd Fonts
fc-list | grep -i "nerd"

# Count installed fonts
fc-list | grep -i "nerd" | wc -l
# Should show: 186

# Check specific font
fc-list | grep -i "firacode.*nerd"
```

## Next Steps

1. Configure your primary terminal (Windows Terminal recommended)
2. Install a Powerline/Starship prompt
3. Configure vim/neovim with devicons
4. Enjoy beautiful terminal aesthetics!

---

**Installed**: November 29, 2025
**Location**: `~/.local/share/fonts/NerdFonts/`
**Total Fonts**: 186
