# Contributing to Spartan Trading Agent

Thank you for your interest in contributing! This project aims to build a world-class AI-powered trading system.

## Code of Conduct

- Be respectful and professional
- Focus on constructive feedback
- Help others learn and grow
- Prioritize code quality and testing

## How to Contribute

### Reporting Bugs

Found a bug? Please open an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, etc.)
- Relevant logs or error messages

### Suggesting Features

Have an idea? Open an issue with:
- Clear description of the feature
- Use case and benefits
- Proposed implementation (if you have one)
- Any potential challenges

### Contributing Code

1. **Fork the repository**
   ```bash
   git fork https://github.com/gravity-ven/Spartan_Labs.git
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Write clean, documented code
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

4. **Test your changes**
   ```bash
   # Run tests
   pytest tests/

   # Run linter
   ruff check src/

   # Run type checker
   mypy src/
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Open a Pull Request**
   - Describe what changes you made
   - Reference any related issues
   - Explain your testing approach

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/Spartan_Labs.git
cd Spartan_Labs

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies (including dev dependencies)
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

## Code Style

We follow PEP 8 with some modifications:

- Line length: 100 characters
- Use type hints for all functions
- Document all public functions with docstrings
- Use `ruff` for linting
- Use `black` for formatting

Example:

```python
def calculate_position_size(
    portfolio_value: float,
    risk_percent: float,
    entry_price: float,
    stop_loss: float
) -> float:
    """
    Calculate position size based on risk.

    Args:
        portfolio_value: Total portfolio value
        risk_percent: Risk percentage (0.0-1.0)
        entry_price: Entry price per share
        stop_loss: Stop loss price per share

    Returns:
        Number of shares to buy
    """
    risk_amount = portfolio_value * risk_percent
    price_risk = abs(entry_price - stop_loss)
    return risk_amount / price_risk if price_risk > 0 else 0
```

## Testing

All new features must include tests:

```python
import pytest
from src.risk.risk_manager import RiskManager

def test_position_size_calculation():
    """Test position size calculation."""
    risk_manager = RiskManager(config, initial_capital=100000)

    result = risk_manager.validate_trade(
        symbol="AAPL",
        quantity=100,
        price=150.0,
        side="buy",
        current_portfolio_value=100000
    )

    assert result["approved"] == True
    assert result["adjusted_quantity"] <= 100
```

## Adding New Features

### Adding a New Data Connector

1. Create a new file in `src/data/`
2. Inherit from `DataConnector` base class
3. Implement all abstract methods
4. Add configuration to `config/config.yaml`
5. Write tests
6. Update documentation

### Adding a New Strategy

1. Create prompts in `src/core/prompts/`
2. Add strategy type to Claude engine
3. Add configuration to `config/config.yaml`
4. Write backtest
5. Document the strategy

### Adding a New Broker

1. Create a new file in `src/execution/`
2. Inherit from `ExecutionEngine` base class
3. Implement all abstract methods
4. Add configuration to `config/config.yaml`
5. Write tests
6. Update documentation

## Documentation

When adding new features, update:

- README.md (if it affects usage)
- ARCHITECTURE.md (if it affects system design)
- Relevant docs in `docs/`
- Docstrings in code
- Examples if applicable

## Commit Message Guidelines

Use clear, descriptive commit messages:

```
feat: Add Binance crypto connector
fix: Correct position sizing calculation
docs: Update quick start guide
test: Add tests for risk manager
refactor: Simplify Claude prompt building
```

Prefixes:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring
- `perf:` Performance improvement
- `chore:` Maintenance tasks

## Pull Request Guidelines

Good PR:
- Single, focused change
- Clear description
- Tests included
- Documentation updated
- Passes all CI checks
- No merge conflicts

## Areas We Need Help

- [ ] Additional data connectors (Polygon, IEX, etc.)
- [ ] Additional brokers (Binance, Interactive Brokers, etc.)
- [ ] Backtesting framework improvements
- [ ] Web dashboard UI
- [ ] Strategy optimization tools
- [ ] Performance monitoring
- [ ] Documentation and tutorials
- [ ] Test coverage
- [ ] Example strategies

## Questions?

Feel free to:
- Open an issue for discussion
- Join our Discord (coming soon)
- Email the maintainers

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

Thank you for contributing to Spartan Trading Agent! 🚀
