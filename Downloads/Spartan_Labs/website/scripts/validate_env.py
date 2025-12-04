#!/usr/bin/env python3
"""
Environment Configuration Validator
Checks API keys and provides guidance on required vs optional keys
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class EnvValidator:
    """Validates environment configuration and API keys"""

    # Placeholder values that indicate an API key is not configured
    PLACEHOLDER_VALUES = [
        'your_',
        'placeholder',
        'insert_',
        'add_your_',
        'get_from_',
    ]

    def __init__(self, env_file: Path = None):
        """Initialize validator"""
        self.env_file = env_file or Path(__file__).parent.parent / '.env'
        self.validation_results = {
            'critical': [],
            'recommended': [],
            'optional': [],
            'configured': [],
            'missing': []
        }

    def is_placeholder(self, value: str) -> bool:
        """Check if a value is a placeholder"""
        if not value:
            return True

        value_lower = value.lower()

        # Check for common placeholder patterns
        for placeholder in self.PLACEHOLDER_VALUES:
            if placeholder in value_lower:
                return True

        # Check if it's too short to be a real API key (except for testing values)
        if len(value) < 10 and not value.startswith('test'):
            return True

        return False

    def validate_fred_key(self, key: str) -> Tuple[bool, str]:
        """Validate FRED API key format"""
        if self.is_placeholder(key):
            return False, "Missing - Get free key at https://fred.stlouisfed.org/docs/api/api_key.html"

        # FRED keys are 32 characters, alphanumeric
        if len(key) != 32:
            return False, f"Invalid format - FRED keys are exactly 32 characters (found {len(key)})"

        if not re.match(r'^[a-zA-Z0-9]+$', key):
            return False, "Invalid format - FRED keys contain only letters and numbers"

        return True, "Valid FRED API key configured"

    def validate_polygon_key(self, key: str) -> Tuple[bool, str]:
        """Validate Polygon.io API key"""
        if self.is_placeholder(key):
            return False, "Missing"

        # Polygon keys are typically 32 characters
        if len(key) < 20:
            return False, f"Potentially invalid - key seems too short ({len(key)} chars)"

        return True, "Configured"

    def check_api_keys(self) -> Dict:
        """Check all API keys and categorize by importance"""

        # Load environment variables from .env file
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()

        # Critical keys (but system has fallbacks)
        fred_key = os.getenv('FRED_API_KEY', '')
        fred_valid, fred_msg = self.validate_fred_key(fred_key)

        self.validation_results['critical'].append({
            'name': 'FRED_API_KEY',
            'valid': fred_valid,
            'message': fred_msg,
            'priority': 'HIGHLY RECOMMENDED',
            'fallback': 'yfinance treasury yields (limited economic data)'
        })

        # Recommended keys
        recommended_keys = [
            ('POLYGON_IO_API_KEY', 'Polygon.io', 'Real-time market data'),
            ('ALPHA_VANTAGE_API_KEY', 'Alpha Vantage', 'Stock/Forex/Crypto data'),
        ]

        for key_name, service, description in recommended_keys:
            key_value = os.getenv(key_name, '')
            is_valid = not self.is_placeholder(key_value)

            if key_name == 'POLYGON_IO_API_KEY':
                is_valid, msg = self.validate_polygon_key(key_value)
            else:
                msg = 'Configured' if is_valid else 'Missing'

            self.validation_results['recommended'].append({
                'name': key_name,
                'valid': is_valid,
                'message': msg,
                'service': service,
                'description': description
            })

        # Optional keys (nice to have)
        optional_keys = [
            'FINNHUB_API_KEY',
            'TWELVE_DATA_API_KEY',
            'IEX_CLOUD_API_KEY',
            'TIINGO_API_KEY',
            'CRYPTOCOMPARE_API_KEY',
            'NEWS_API_KEY',
            'QUANDL_API_KEY',
            'BLS_API_KEY',
        ]

        for key_name in optional_keys:
            key_value = os.getenv(key_name, '')
            is_valid = not self.is_placeholder(key_value)

            self.validation_results['optional'].append({
                'name': key_name,
                'valid': is_valid,
                'configured': is_valid
            })

        return self.validation_results

    def print_report(self):
        """Print validation report to console"""
        print("\n" + "=" * 80)
        print(f"{Colors.HEADER}{Colors.BOLD}🔍 SPARTAN LABS - API KEY VALIDATION REPORT{Colors.ENDC}")
        print("=" * 80 + "\n")

        # Critical keys section
        print(f"{Colors.BOLD}🔴 CRITICAL: ECONOMIC DATA{Colors.ENDC}")
        print("-" * 80)

        for key_info in self.validation_results['critical']:
            status_color = Colors.OKGREEN if key_info['valid'] else Colors.WARNING
            status_symbol = "✅" if key_info['valid'] else "⚠️"

            print(f"{status_symbol} {Colors.BOLD}{key_info['name']}{Colors.ENDC}: "
                  f"{status_color}{key_info['message']}{Colors.ENDC}")

            if not key_info['valid']:
                print(f"   Priority: {Colors.WARNING}{key_info['priority']}{Colors.ENDC}")
                print(f"   Fallback: {key_info['fallback']}")

        print()

        # Recommended keys section
        print(f"{Colors.BOLD}🟡 RECOMMENDED: ENHANCED DATA SOURCES{Colors.ENDC}")
        print("-" * 80)

        configured_count = sum(1 for k in self.validation_results['recommended'] if k['valid'])
        total_recommended = len(self.validation_results['recommended'])

        print(f"Configured: {configured_count}/{total_recommended}")
        print()

        for key_info in self.validation_results['recommended']:
            status_color = Colors.OKGREEN if key_info['valid'] else Colors.OKCYAN
            status_symbol = "✅" if key_info['valid'] else "⭕"

            print(f"{status_symbol} {key_info['name']}: {status_color}{key_info['message']}{Colors.ENDC}")

        print()

        # Optional keys section
        print(f"{Colors.BOLD}🟢 OPTIONAL: ADDITIONAL DATA SOURCES{Colors.ENDC}")
        print("-" * 80)

        configured_optional = sum(1 for k in self.validation_results['optional'] if k['valid'])
        total_optional = len(self.validation_results['optional'])

        print(f"Configured: {configured_optional}/{total_optional}")

        if configured_optional > 0:
            print(f"{Colors.OKGREEN}Configured optional keys:{Colors.ENDC}")
            for key_info in self.validation_results['optional']:
                if key_info['valid']:
                    print(f"  ✅ {key_info['name']}")

        print()

        # Summary and recommendations
        print("=" * 80)
        print(f"{Colors.BOLD}📋 SUMMARY & RECOMMENDATIONS{Colors.ENDC}")
        print("=" * 80)

        fred_configured = self.validation_results['critical'][0]['valid']

        if not fred_configured:
            print(f"\n{Colors.WARNING}⚠️  RECOMMENDATION: Configure FRED API Key{Colors.ENDC}")
            print(f"   The system will work without it, but you'll get better economic data.")
            print(f"   Takes only 2 minutes:")
            print(f"   1. Visit: {Colors.OKCYAN}https://fred.stlouisfed.org/docs/api/api_key.html{Colors.ENDC}")
            print(f"   2. Fill out the simple form")
            print(f"   3. Copy your 32-character key to .env")
            print()

        print(f"\n{Colors.OKGREEN}✅ System Status: READY TO START{Colors.ENDC}")
        print(f"\n   The Spartan Research Station uses yfinance as its PRIMARY data source.")
        print(f"   yfinance requires NO API keys and provides:")
        print(f"   • US & Global Stock Indices")
        print(f"   • Commodities (Gold, Oil, Copper)")
        print(f"   • Cryptocurrencies")
        print(f"   • Forex pairs")
        print(f"   • Treasury yields")
        print(f"   • Sector ETFs")
        print(f"   • Volatility (VIX)")
        print()

        if fred_configured:
            print(f"   {Colors.OKGREEN}FRED API configured - Full economic data available{Colors.ENDC}")
        else:
            print(f"   {Colors.WARNING}FRED API not configured - Using treasury yield fallback{Colors.ENDC}")

        print()
        print(f"   To start the system: {Colors.BOLD}./START_SPARTAN.sh{Colors.ENDC}")
        print()

        print("=" * 80 + "\n")

    def should_block_startup(self) -> bool:
        """
        Determine if startup should be blocked
        Returns: False (never block - system works without API keys!)
        """
        # IMPORTANT: We never block startup because yfinance works without API keys
        # The data preloader has its own validation logic
        return False


def main():
    """Main validation entry point"""
    validator = EnvValidator()

    # Check API keys
    validator.check_api_keys()

    # Print report
    validator.print_report()

    # Exit with appropriate code
    if validator.should_block_startup():
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
