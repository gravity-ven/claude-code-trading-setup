# Pyrefly Type Checking Guide - Spartan Research Station

**Pyrefly** is Meta's ultra-fast Python type checker and language server (written in Rust). It provides real-time type checking, code completion, and IDE integration.

---

## 🚀 Quick Start

### Command-Line Usage

```bash
# Check a single file
pyrefly check src/data_preloader.py

# Check entire project
pyrefly check .

# Watch mode (re-check on file changes)
pyrefly check --watch .

# Strict mode (for critical code)
pyrefly check --strict src/data_preloader.py

# Generate HTML report
pyrefly check --html-report pyrefly-report.html .
```

---

## 🎯 Pre-Commit Hook

**Automatic type checking is now enabled on every commit!**

The pre-commit hook will:
1. ✅ Run Pyrefly on all staged Python files
2. ✅ Apply strict checking to critical financial code
3. ✅ Block dangerous patterns (float for money, SQLite usage, fake data)
4. ✅ Ensure PostgreSQL-only and NO FAKE DATA policies

### Bypass Hook (Emergency Only)

```bash
# NOT RECOMMENDED - only for urgent fixes
git commit --no-verify -m "Emergency fix"
```

---

## 📝 Type Annotation Patterns

### Basic Type Hints

```python
from typing import Optional, List, Dict, Decimal
from datetime import datetime

# Function with return type
def get_market_data(symbol: str) -> Optional[Dict[str, float]]:
    """Fetch market data for symbol."""
    return {"price": 150.25, "volume": 1000000}

# Async function
async def fetch_data(url: str) -> str:
    """Fetch data from API."""
    return "data"

# Class with typed attributes
class MarketData:
    symbol: str
    price: Decimal  # Use Decimal for money!
    timestamp: datetime

    def __init__(self, symbol: str, price: Decimal):
        self.symbol = symbol
        self.price = price
        self.timestamp = datetime.now()
```

### Financial Code - CRITICAL

```python
from decimal import Decimal
from typing import Optional

# ✅ CORRECT - Use Decimal for money
def calculate_position_size(
    account_equity: Decimal,
    risk_percent: Decimal,
    stop_loss: Decimal
) -> Optional[int]:
    """Calculate position size with proper types."""
    if stop_loss <= 0:
        return None

    risk_amount = account_equity * (risk_percent / Decimal('100'))
    position_size = int(risk_amount / stop_loss)
    return position_size


# ❌ WRONG - Never use float for money!
def bad_calculate_position_size(
    account_equity: float,  # ❌ WRONG!
    risk_percent: float,    # ❌ WRONG!
    stop_loss: float        # ❌ WRONG!
) -> int:
    # This will cause rounding errors in financial calculations
    return int((account_equity * risk_percent) / stop_loss)
```

### API Endpoints

```python
from typing import Dict, Any, Optional
from flask import Flask, jsonify, Response
import json

app = Flask(__name__)

# Typed API endpoint
@app.route('/api/market/<symbol>')
def get_symbol_data(symbol: str) -> Response:
    """Get market data for symbol with proper typing."""
    data: Optional[Dict[str, Any]] = fetch_from_cache(symbol)

    if data is None:
        return jsonify({'error': 'No data available'}), 404

    return jsonify(data), 200


def fetch_from_cache(symbol: str) -> Optional[Dict[str, Any]]:
    """Fetch from Redis cache."""
    # Return None if not found (NO FAKE DATA!)
    return None
```

### Database Operations

```python
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor

def query_market_data(
    symbol: str,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Query market data from PostgreSQL."""
    conn = psycopg2.connect(
        "postgresql://spartan:spartan@localhost/spartan_research_db"
    )

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            "SELECT * FROM preloaded_market_data WHERE symbol = %s LIMIT %s",
            (symbol, limit)
        )
        results: List[Dict[str, Any]] = cursor.fetchall()

    conn.close()
    return results
```

---

## 🔧 VS Code Integration

### Installation

**Method 1: Extension Marketplace**
1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "Pyrefly"
4. Click "Install" on the official Facebook Pyrefly extension

**Method 2: Command Line** (Windows)
```powershell
# From Windows (not WSL)
code --install-extension facebook.pyrefly
```

### Features

Once installed, Pyrefly provides:
- ✅ **Real-time type checking** - errors show as you type
- ✅ **Hover tooltips** - see type information on hover
- ✅ **Auto-completion** - intelligent code suggestions
- ✅ **Go to definition** - jump to type definitions
- ✅ **Inline errors** - type errors highlighted in editor

### Settings

VS Code settings are already configured in `.vscode/settings.json`:
- Strict type checking enabled
- Pyrefly as default language server
- Type hints in editor
- Format on save enabled

---

## ⚙️ Configuration

### Project Config (`pyproject.toml`)

The project is configured with:
- **Strict mode**: All functions must have type annotations
- **Financial safety**: Warns on float usage in money calculations
- **PostgreSQL enforcement**: Blocks SQLite imports
- **Performance**: Parallel type checking enabled

### Custom Rules

**Financial Code Safety**:
```toml
[tool.pyrefly.financial]
prefer_decimal_for_money = true
warn_float_in_financial = true
```

**Database Policy**:
```toml
[tool.pyrefly.database]
check_sql_params = true
check_db_connections = true
```

**Cache Operations**:
```toml
[tool.pyrefly.cache]
check_cache_operations = true
check_serialization = true
```

---

## 🛡️ Safety Policies Enforced

### 1. NO FAKE DATA

```python
# ❌ BLOCKED by pre-commit hook
import random
price = random.uniform(100, 200)  # Fake data!

# ✅ ALLOWED
import yfinance as yf
price = yf.Ticker("SPY").history(period="1d")["Close"][-1]
```

### 2. PostgreSQL Only

```python
# ❌ BLOCKED by pre-commit hook
import sqlite3
conn = sqlite3.connect("database.db")

# ✅ ALLOWED
import psycopg2
conn = psycopg2.connect("postgresql://...")
```

### 3. Decimal for Money

```python
# ❌ WARNING from Pyrefly
def calculate_profit(buy: float, sell: float) -> float:
    return sell - buy  # Float precision errors!

# ✅ CORRECT
from decimal import Decimal
def calculate_profit(buy: Decimal, sell: Decimal) -> Decimal:
    return sell - buy  # Exact decimal arithmetic
```

---

## 📊 Type Checking Reports

### Generate HTML Report

```bash
pyrefly check --html-report pyrefly-report.html .
# Open pyrefly-report.html in browser
```

### CI/CD Integration

```yaml
# .github/workflows/type-check.yml
name: Type Check

on: [push, pull_request]

jobs:
  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install Pyrefly
        run: pip install pyrefly

      - name: Run type check
        run: pyrefly check --strict .

      - name: Generate report
        if: always()
        run: pyrefly check --html-report pyrefly-report.html .

      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: type-check-report
          path: pyrefly-report.html
```

---

## 🐛 Common Errors & Fixes

### Error: Missing return type annotation

```python
# ❌ ERROR
def get_price(symbol):
    return 100.0

# ✅ FIX
def get_price(symbol: str) -> float:
    return 100.0
```

### Error: Incompatible types

```python
# ❌ ERROR
def process_data(data: List[int]) -> None:
    data.append("string")  # Type error!

# ✅ FIX
def process_data(data: List[int]) -> None:
    data.append(42)  # Correct type
```

### Error: Optional not handled

```python
# ❌ ERROR
def get_user(id: int) -> Optional[User]:
    return None

user = get_user(1)
print(user.name)  # Error: user might be None!

# ✅ FIX
user = get_user(1)
if user is not None:
    print(user.name)  # Safe
```

---

## 🔥 Performance Comparison

**Pyrefly vs mypy** (on large codebase):

| Type Checker | Time | Speedup |
|--------------|------|---------|
| mypy         | 120s | 1x      |
| Pyrefly      | 2s   | **60x faster** |

**Pyrefly benefits**:
- Written in Rust (native speed)
- Parallel type checking
- Incremental checking (only changed files)
- Optimized for large codebases

---

## 📚 Resources

- **Official Docs**: https://pyrefly.org/en/docs/
- **GitHub**: https://github.com/facebook/pyrefly
- **PyPI**: https://pypi.org/project/pyrefly/
- **Blog**: https://pyrefly.org/blog/

---

## 🎯 Quick Cheat Sheet

```bash
# Basic commands
pyrefly check .                    # Check entire project
pyrefly check --watch .            # Watch mode
pyrefly check --strict file.py     # Strict mode

# Reports
pyrefly check --html-report report.html .
pyrefly check --junit-xml report.xml .

# Configuration
pyrefly --version                  # Show version
pyrefly --help                     # Show help

# Git integration
git commit                         # Runs Pyrefly automatically
git commit --no-verify             # Skip type check (emergency)
```

---

**Status**: ✅ Fully configured for Spartan Research Station
**Last Updated**: November 28, 2025
