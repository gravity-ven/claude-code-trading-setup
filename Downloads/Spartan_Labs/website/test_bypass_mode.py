#!/usr/bin/env python3
"""
Test script to verify SKIP_DATA_VALIDATION bypass mode works correctly
"""

import os
import sys

# Add src to path
sys.path.insert(0, 'src')

# Mock the validation results to simulate 0% success
class MockPreloader:
    def __init__(self):
        self.validation_results = {
            'US_Indices': False,
            'Global_Indices': False,
            'Gold': False,
            'Oil': False,
            'Copper': False,
            'Bitcoin': False,
            'Major_Forex': False,
            'US_Treasuries': False,
            'Global_Bonds': False,
            'FRED_Economic': False,
            'Volatility': False,
            'Sector_ETFs': False,
            'Correlation_Matrix': False,
        }

print("=" * 70)
print("EMERGENCY BYPASS MODE TEST")
print("=" * 70)

# Test 1: Bypass mode disabled (should fail validation)
print("\n📋 TEST 1: Bypass mode DISABLED (normal operation)")
print("-" * 70)

os.environ['SKIP_DATA_VALIDATION'] = 'false'

# Import after setting env var
from data_preloader import DataPreloader
import asyncio

async def test_without_bypass():
    preloader = DataPreloader()
    preloader.validation_results = MockPreloader().validation_results

    # Should fail with 0% success rate
    is_valid, report = await preloader.validate_data_availability()

    print(f"\nValidation Result: {'✅ PASSED' if is_valid else '❌ FAILED'}")
    print(f"Success Rate: {report['success_rate']:.1f}%")
    print(f"Expected: FAILED (0% success)")

    assert is_valid == False, "ERROR: Should have failed validation!"
    print("✅ TEST 1 PASSED: Validation correctly failed with 0% success\n")

asyncio.run(test_without_bypass())

# Test 2: Bypass mode enabled (should pass validation)
print("\n📋 TEST 2: Bypass mode ENABLED (emergency mode)")
print("-" * 70)

os.environ['SKIP_DATA_VALIDATION'] = 'true'

# Reload module to pick up new env var
import importlib
import data_preloader
importlib.reload(data_preloader)
from data_preloader import DataPreloader as DataPreloaderBypass

async def test_with_bypass():
    preloader = DataPreloaderBypass()
    preloader.validation_results = MockPreloader().validation_results

    # Should PASS despite 0% success rate
    is_valid, report = await preloader.validate_data_availability()

    print(f"\nValidation Result: {'✅ PASSED' if is_valid else '❌ FAILED'}")
    print(f"Success Rate: {report['success_rate']:.1f}%")
    print(f"Bypass Mode Active: {report.get('bypass_mode', False)}")
    print(f"Expected: PASSED (bypass mode active)")

    assert is_valid == True, "ERROR: Should have passed validation with bypass!"
    assert report.get('bypass_mode') == True, "ERROR: Bypass mode flag not set!"
    print("✅ TEST 2 PASSED: Bypass mode correctly overrides validation\n")

asyncio.run(test_with_bypass())

# Test 3: Environment variable variations
print("\n📋 TEST 3: Environment variable case sensitivity")
print("-" * 70)

test_cases = [
    ('true', True),
    ('True', True),
    ('TRUE', True),
    ('false', False),
    ('False', False),
    ('FALSE', False),
    ('1', False),  # Only "true" should work
    ('yes', False),
]

for value, expected in test_cases:
    os.environ['SKIP_DATA_VALIDATION'] = value

    import importlib
    importlib.reload(data_preloader)
    from data_preloader import DataPreloader as TestPreloader

    async def test_env_var():
        preloader = TestPreloader()
        preloader.validation_results = MockPreloader().validation_results
        is_valid, report = await preloader.validate_data_availability()
        return is_valid

    result = asyncio.run(test_env_var())

    if result == expected:
        print(f"  ✅ SKIP_DATA_VALIDATION={value} → {result} (expected {expected})")
    else:
        print(f"  ❌ SKIP_DATA_VALIDATION={value} → {result} (expected {expected})")
        sys.exit(1)

print("\n✅ TEST 3 PASSED: All environment variable variations work correctly\n")

print("=" * 70)
print("🎉 ALL TESTS PASSED!")
print("=" * 70)
print("\nBypass mode implementation is working correctly.")
print("\nTo activate in production:")
print("  1. Set SKIP_DATA_VALIDATION=true in .env file")
print("  2. Restart docker-compose")
print("  3. Website will start regardless of data availability")
print("\n⚠️  WARNING: This is for emergency use only!")
print("    Fix data sources ASAP and set back to false.\n")
