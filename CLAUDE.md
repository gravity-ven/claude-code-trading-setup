# CLAUDE.md

## Permission Management
```bash
# Simple permission bypass - use when needed
export SKIP_PERMISSIONS=1
```

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment Overview

This is a Windows user directory optimized for algorithmic trading development across multiple platforms including NinjaTrader, Interactive Brokers, and various Python-based trading systems.

## Development Structure

### NinjaTrader 8 Development
- **Main Directory**: `Documents/NinjaTrader 8/bin/Custom/`
- **Solution File**: `Documents/NinjaTrader.Custom.sln`
- **Build**: NinjaTrader compiles automatically when platform is running
- **Languages**: C# (.NET Framework)
- **Architecture**: Indicators inherit from `Indicator` base class, use `OnStateChange()` and `OnBarUpdate()` methods

### Python Trading Projects
- **Directory**: `PycharmProjects/`
- **Key Projects**:
  - `Arbitrage_Nexus/` - Arbitrage trading systems
  - `ib_api/` - Interactive Brokers API integration
  - `yahoo_fin/` - Yahoo Finance data processing
- **Build**: Use `python -m pip install -e .` for local development packages
- **Environment**: Python 3.13+ with virtual environments (`.venv/`)

### Configuration Management
- **Claude Settings**: `.claude/settings.local.json` (read permissions configured)
- **Global Settings**: `Documents/GitHub/Claude_Settings/` - Synced Claude configuration
- **Agent System**: Advanced meta-orchestrator system with specialized trading and programming agents

## Key Development Patterns

### NinjaTrader Indicators
```csharp
// Standard pattern for indicators
public class MyIndicator : Indicator
{
    protected override void OnStateChange()
    {
        if (State == State.SetDefaults)
        {
            // Configuration
        }
        else if (State == State.DataLoaded)
        {
            // Initialization
        }
    }
    
    protected override void OnBarUpdate()
    {
        // Main calculation logic
    }
}
```

### Position Sizing Calculations
- Optimal f calculations use real account data via `Account.All.FirstOrDefault().Executions`
- Base calculation: `positionSize = (optimalF * AccountEquity) / Math.Abs(maxLoss)`
- Risk management typically uses fractional multipliers (25%, 50%, 75% of optimal f)

### Python Trading Architecture
- Projects use `pyproject.toml` for dependency management
- Virtual environments isolated per project
- Common pattern: data collection → analysis → strategy execution

## File Organization

### Important Files
- `optimalf.cs` - Advanced optimal f position sizing indicator using real trading data
- `*.csv` files - Market data exports and analysis results
- `*.log` files - Trading system and application logs

### Trading Data Flow
1. **Data Collection**: Yahoo Finance, Interactive Brokers, NinjaTrader feeds
2. **Analysis**: Python scripts for pattern recognition and statistical analysis  
3. **Execution**: NinjaTrader strategies and indicators for live trading
4. **Monitoring**: Log files and performance tracking

## Common Commands

### Python Development
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/WSL
.venv\Scripts\activate     # Windows

# Install project dependencies
pip install -e .
```

### NinjaTrader Development
- Use Visual Studio or NinjaTrader's built-in editor
- Compilation happens automatically when NinjaTrader platform starts
- Check NinjaTrader Editor Output window for compilation errors

## Special Considerations

### Cross-Platform Development
- Running on WSL2 (Windows Subsystem for Linux)
- Files accessible via `/mnt/c/Users/Quantum/` path structure
- Mix of Windows applications (NinjaTrader, Visual Studio) and Linux tools

### Trading System Integration
- Real-time data feeds require active market connections
- Position sizing calculations depend on live account data
- Risk management systems integrate across multiple trading platforms

### Agent System
- Advanced meta-orchestrator for complex task delegation
- Specialized agents for trading, programming, and system administration
- Token-optimized agent hierarchy for efficient task completion