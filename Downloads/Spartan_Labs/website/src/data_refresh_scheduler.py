#!/usr/bin/env python3
"""
Data Refresh Scheduler
Runs every 15 minutes to keep data fresh
"""

import asyncio
import sys
import os
from datetime import datetime
import logging

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.data_preloader import DataPreloader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def refresh_loop():
    """Main refresh loop - runs every 15 minutes"""
    preloader = DataPreloader()

    # Connect once
    await preloader.connect()

    refresh_interval = 900  # 15 minutes

    try:
        while True:
            logger.info(f"🔄 Starting data refresh at {datetime.now()}")

            # Refresh all data
            results = await preloader.preload_all_data()

            # Validate
            is_valid, report = await preloader.validate_data_availability()

            # Update health endpoint
            await preloader.create_health_endpoint_data()

            if is_valid:
                logger.info(f"✅ Refresh complete - {report['success_rate']:.1f}% success")
            else:
                logger.warning(f"⚠️ Refresh completed with warnings - {report['success_rate']:.1f}% success")

            # Sleep until next refresh
            logger.info(f"💤 Sleeping {refresh_interval}s until next refresh...")
            await asyncio.sleep(refresh_interval)

    except KeyboardInterrupt:
        logger.info("Refresh scheduler stopped by user")
    except Exception as e:
        logger.error(f"Refresh scheduler crashed: {e}")
    finally:
        await preloader.close()


if __name__ == "__main__":
    logger.info("🚀 Starting Data Refresh Scheduler")
    logger.info("   Interval: 15 minutes")
    logger.info("   Sources: 13+ data providers")
    asyncio.run(refresh_loop())
