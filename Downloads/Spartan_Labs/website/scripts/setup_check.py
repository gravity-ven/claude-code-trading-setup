#!/usr/bin/env python3
"""
Setup checker for Spartan Trading Agent.

Verifies that all dependencies and API keys are properly configured.
"""

import os
import sys
from pathlib import Path

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def check_python_version():
    """Check if Python version is 3.11+."""
    print(f"{BOLD}Checking Python version...{RESET}")
    version = sys.version_info

    if version.major == 3 and version.minor >= 11:
        print(f"{GREEN}✓ Python {version.major}.{version.minor}.{version.micro}{RESET}")
        return True
    else:
        print(f"{RED}✗ Python 3.11+ required, found {version.major}.{version.minor}.{version.micro}{RESET}")
        return False


def check_dependencies():
    """Check if required packages are installed."""
    print(f"\n{BOLD}Checking dependencies...{RESET}")

    required = [
        "anthropic",
        "pandas",
        "numpy",
        "pydantic",
        "structlog",
        "aiohttp",
        "alpaca",
    ]

    all_installed = True

    for package in required:
        try:
            __import__(package)
            print(f"{GREEN}✓ {package}{RESET}")
        except ImportError:
            print(f"{RED}✗ {package} not installed{RESET}")
            all_installed = False

    if not all_installed:
        print(f"\n{YELLOW}Install missing packages with:{RESET}")
        print("  pip install -r requirements.txt")

    return all_installed


def check_env_file():
    """Check if .env file exists and has required keys."""
    print(f"\n{BOLD}Checking .env file...{RESET}")

    env_path = Path(".env")

    if not env_path.exists():
        print(f"{RED}✗ .env file not found{RESET}")
        print(f"{YELLOW}Create it with:{RESET}")
        print("  cp .env.example .env")
        return False

    print(f"{GREEN}✓ .env file exists{RESET}")

    # Check for required keys
    required_keys = [
        "ANTHROPIC_API_KEY",
    ]

    optional_keys = [
        "ALPACA_API_KEY",
        "ALPACA_API_SECRET",
        "BINANCE_API_KEY",
        "POLYGON_API_KEY",
    ]

    with open(env_path) as f:
        env_content = f.read()

    all_present = True

    print(f"\n{BOLD}Required API keys:{RESET}")
    for key in required_keys:
        if f"{key}=" in env_content and "your_" not in env_content.split(f"{key}=")[1].split()[0]:
            print(f"{GREEN}✓ {key}{RESET}")
        else:
            print(f"{RED}✗ {key} not set{RESET}")
            all_present = False

    print(f"\n{BOLD}Optional API keys:{RESET}")
    for key in optional_keys:
        if f"{key}=" in env_content and "your_" not in env_content.split(f"{key}=")[1].split()[0]:
            print(f"{GREEN}✓ {key}{RESET}")
        else:
            print(f"{YELLOW}○ {key} not set (optional){RESET}")

    return all_present


def check_config_file():
    """Check if config file exists."""
    print(f"\n{BOLD}Checking config file...{RESET}")

    config_path = Path("config/config.yaml")

    if not config_path.exists():
        print(f"{RED}✗ config/config.yaml not found{RESET}")
        return False

    print(f"{GREEN}✓ config/config.yaml exists{RESET}")
    return True


def check_directories():
    """Check if required directories exist."""
    print(f"\n{BOLD}Checking directories...{RESET}")

    required_dirs = [
        "src",
        "config",
        "examples",
        "tests",
        "docs",
    ]

    all_present = True

    for directory in required_dirs:
        if Path(directory).exists():
            print(f"{GREEN}✓ {directory}/{RESET}")
        else:
            print(f"{RED}✗ {directory}/ not found{RESET}")
            all_present = False

    return all_present


def test_anthropic_api():
    """Test Anthropic API connection."""
    print(f"\n{BOLD}Testing Anthropic API connection...{RESET}")

    try:
        import anthropic
        from dotenv import load_dotenv

        load_dotenv()

        api_key = os.getenv("ANTHROPIC_API_KEY")

        if not api_key or api_key.startswith("your_"):
            print(f"{YELLOW}○ Skipping (API key not set){RESET}")
            return None

        client = anthropic.Anthropic(api_key=api_key)

        # Simple test message
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Reply with just 'OK'"}
            ]
        )

        if message.content:
            print(f"{GREEN}✓ Anthropic API working{RESET}")
            return True
        else:
            print(f"{RED}✗ Anthropic API error{RESET}")
            return False

    except Exception as e:
        print(f"{RED}✗ Anthropic API error: {e}{RESET}")
        return False


def main():
    """Run all checks."""
    print(f"\n{BOLD}{'='*50}{RESET}")
    print(f"{BOLD}Spartan Trading Agent - Setup Check{RESET}")
    print(f"{BOLD}{'='*50}{RESET}\n")

    results = {
        "Python Version": check_python_version(),
        "Dependencies": check_dependencies(),
        "Environment File": check_env_file(),
        "Config File": check_config_file(),
        "Directories": check_directories(),
        "Anthropic API": test_anthropic_api(),
    }

    # Summary
    print(f"\n{BOLD}{'='*50}{RESET}")
    print(f"{BOLD}Summary{RESET}")
    print(f"{BOLD}{'='*50}{RESET}\n")

    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)

    for check, result in results.items():
        if result is True:
            print(f"{GREEN}✓{RESET} {check}")
        elif result is False:
            print(f"{RED}✗{RESET} {check}")
        else:
            print(f"{YELLOW}○{RESET} {check} (skipped)")

    print(f"\n{BOLD}Results:{RESET} {GREEN}{passed} passed{RESET}, {RED}{failed} failed{RESET}, {YELLOW}{skipped} skipped{RESET}\n")

    if failed == 0:
        print(f"{GREEN}{BOLD}All checks passed! You're ready to start trading.{RESET}")
        print(f"\n{BOLD}Next steps:{RESET}")
        print("  1. python examples/basic_trading.py")
        print("  2. Read docs/quick_start.md")
        return 0
    else:
        print(f"{RED}{BOLD}Some checks failed. Please fix the issues above.{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
