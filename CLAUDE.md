# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment Overview

This is a Windows system root directory (C:\) that serves as a base for various applications and development environments. The system appears to be primarily used for trading applications and development tools.

## Key Applications and Directories

### Trading Applications
- **DAS Trader Pro_x64/** - Professional trading platform
- **Jts/** - Interactive Brokers Java-based trading software
- **SierraChart/** - Advanced charting and trading platform

### Development Tools
- **Python313/** - Python 3.13 installation for development
- **Qt/** - Qt framework for GUI applications

### System Directories
- **Program Files/** and **Program Files (x86)/** - Standard Windows application directories
- **Users/** - User profile directories containing individual development environments
- **Windows/** - Core Windows system files

## Development Context

This system appears to be optimized for algorithmic trading development with multiple trading platforms installed. The presence of Python 3.13 suggests active development in financial applications.

## Important Notes

- This is a system root directory, not a specific code repository
- Individual development projects are likely located in user directories under Users/
- Trading applications may have specific data feeds and API integrations
- Python development should use virtual environments for project isolation

## Common System Operations

### Python Development
```bash
# Navigate to user directory for development work
cd /c/Users/[username]/

# Use Python 3.13 installation
python --version
```

### File Navigation
```bash
# List applications
ls "Program Files"
ls "Program Files (x86)"

# Access user development environments
cd Users/[username]/
```

## Security Considerations

- System contains trading applications that may handle sensitive financial data
- Ensure proper security practices when working with financial APIs
- Be cautious with file permissions in system directories