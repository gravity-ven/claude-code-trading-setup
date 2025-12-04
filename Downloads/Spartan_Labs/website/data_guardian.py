#!/usr/bin/env python3
"""
Spartan Research Station - Data Guardian Agent
Ensures all required data for a page is available before rendering.

Author: Spartan Labs
Date: November 25, 2025
"""

from typing import List, Dict, Any
from data_fetcher_fallback import data_fetcher
import logging

logger = logging.getLogger(__name__)

class DataGuardian:
    """
    An agent that verifies the availability of all necessary data for a webpage
    by checking primary and fallback sources.
    """

    def __init__(self, data_requirements: List[Dict[str, Any]]):
        """
        Initializes the DataGuardian with a list of data requirements for a page.

        Args:
            data_requirements: A list of dictionaries, where each dictionary
                               represents a data requirement with keys like 'symbol',
                               'data_type', 'period_days', etc.
        """
        self.data_requirements = data_requirements
        self.fetched_data = {}
        self.all_data_available = False

    def verify_data_availability(self) -> bool:
        """
        Iterates through data requirements, fetches data using the fallback system,
        and checks if all data is successfully retrieved.

        Returns:
            bool: True if all data was fetched successfully, False otherwise.
        """
        logger.info("Data Guardian: Verifying data availability...")
        all_successful = True

        for requirement in self.data_requirements:
            symbol = requirement.get('symbol')
            if not symbol:
                logger.error("Data Guardian: Skipping requirement with no symbol.")
                all_successful = False
                continue

            logger.info(f"Data Guardian: Fetching data for {symbol}...")
            result = data_fetcher.fetch_with_fallback(**requirement)

            if result['success']:
                logger.info(f"Data Guardian: ✓ Successfully fetched data for {symbol} from {result['source']}.")
                self.fetched_data[symbol] = result['data']
            else:
                logger.error(f"Data Guardian: ✗ Failed to fetch data for {symbol} after trying all sources.")
                all_successful = False
                self.fetched_data[symbol] = None

        self.all_data_available = all_successful
        logger.info(f"Data Guardian: Verification complete. All data available: {self.all_data_available}")
        return self.all_data_available

def guardian_test():
    """
    A simple test function to demonstrate the DataGuardian's functionality.
    """
    print("--- Running Data Guardian Test ---")

    # 1. Define the data needed for a hypothetical 'market overview' page
    market_overview_requirements = [
        {'symbol': 'AAPL', 'data_type': 'stock', 'period_days': 30},
        {'symbol': 'BTC-USD', 'data_type': 'crypto', 'period_days': 30},
        {'symbol': 'EURUSD=X', 'data_type': 'forex', 'period_days': 30},
    ]

    # 2. Create a DataGuardian instance for the page
    guardian = DataGuardian(market_overview_requirements)

    # 3. Verify data availability
    if guardian.verify_data_availability():
        print("\nSUCCESS: All data for the market overview page is available.")
        # You can now access the data via guardian.fetched_data
        aapl_data = guardian.fetched_data.get('AAPL')
        if aapl_data is not None:
            print(f"  - AAPL data points: {len(aapl_data)}")
            print(f"  - Last AAPL price: {aapl_data.iloc[-1]:.2f}")
    else:
        print("\nFAILURE: Could not retrieve all data for the market overview page.")
        print("  - The application should show a 'data unavailable' message.")

    print("\n--- Testing with a failing symbol ---")

    # 4. Test with a symbol that is likely to fail
    failing_requirements = [
        {'symbol': 'NONEXISTENT_SYMBOL_XYZ', 'data_type': 'stock', 'period_days': 30},
    ]
    failing_guardian = DataGuardian(failing_requirements)

    if not failing_guardian.verify_data_availability():
        print("\nSUCCESS: The guardian correctly identified that the data is unavailable.")
    else:
        print("\nFAILURE: The guardian should have failed for a non-existent symbol.")

    print("\n--- Data Guardian Test Complete ---")


if __name__ == '__main__':
    # Configure logging for the test
    logging.basicConfig(level=logging.INFO)
    guardian_test()
