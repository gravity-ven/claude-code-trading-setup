#!/usr/bin/env python3
"""
Populate FRED Database with Real Economic Data
==============================================================================
Fetches key economic indicators from FRED API
==============================================================================
"""

import os
import sys
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://spartan_user:spartan_pass_2025@localhost:5432/spartan_research')
FRED_API_KEY = os.getenv('FRED_API_KEY', 'abcdefghijklmnopqrstuvwxyz123456')

# Key FRED series to populate
FRED_SERIES = {
    # Sentiment & Consumer
    'UMCSENT': 'University of Michigan Consumer Sentiment',
    'CONSUMER': 'Consumer Confidence Index',

    # Employment
    'UNRATE': 'Unemployment Rate',
    'PAYEMS': 'All Employees: Total Nonfarm',
    'ICSA': 'Initial Claims',
    'MANEMP': 'Manufacturing Employment',

    # GDP & Growth
    'GDP': 'Gross Domestic Product',
    'GDPC1': 'Real Gross Domestic Product',
    'INDPRO': 'Industrial Production Index',
    'IPMAN': 'Industrial Production: Manufacturing',

    # Inflation
    'CPIAUCSL': 'Consumer Price Index',
    'PPIACO': 'Producer Price Index',
    'PCEPILFE': 'Core PCE Price Index',

    # Interest Rates
    'FEDFUNDS': 'Federal Funds Rate',
    'DFF': 'Effective Federal Funds Rate',
    'DGS10': '10-Year Treasury Rate',
    'DGS2': '2-Year Treasury Rate',
    'T10Y2Y': '10Y-2Y Treasury Spread',

    # Money Supply
    'M2SL': 'M2 Money Stock',
    'M1SL': 'M1 Money Stock',

    # Housing
    'HOUST': 'Housing Starts',
    'MORTGAGE30US': '30-Year Mortgage Rate',

    # Retail & Sales
    'RSXFS': 'Retail Sales',
    'TOTALSL': 'Total Vehicle Sales',
}


def get_db():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def fetch_fred_series(series_id, api_key):
    """Fetch latest value for a FRED series"""
    try:
        # FRED API endpoint
        url = f"https://api.stlouisfed.org/fred/series/observations"
        params = {
            'series_id': series_id,
            'api_key': api_key,
            'file_type': 'json',
            'sort_order': 'desc',
            'limit': 1
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('observations'):
                obs = data['observations'][0]
                return {
                    'date': obs['date'],
                    'value': float(obs['value']) if obs['value'] != '.' else None
                }

        logger.warning("fred_fetch_failed", series_id=series_id, status=response.status_code)
        return None

    except Exception as e:
        logger.error("fred_fetch_error", series_id=series_id, error=str(e))
        return None


def fetch_fred_metadata(series_id, api_key):
    """Fetch metadata for a FRED series"""
    try:
        url = f"https://api.stlouisfed.org/fred/series"
        params = {
            'series_id': series_id,
            'api_key': api_key,
            'file_type': 'json'
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('seriess'):
                series = data['seriess'][0]
                return {
                    'title': series.get('title'),
                    'units': series.get('units'),
                    'frequency': series.get('frequency'),
                    'seasonal_adjustment': series.get('seasonal_adjustment'),
                    'last_updated': series.get('last_updated')
                }

        return None

    except Exception as e:
        logger.error("fred_metadata_error", series_id=series_id, error=str(e))
        return None


def populate_fred_data():
    """Populate FRED data into database"""
    logger.info("populating_fred_data", series_count=len(FRED_SERIES))

    conn = get_db()
    cursor = conn.cursor()

    inserted = 0
    failed = 0

    for series_id, series_name in FRED_SERIES.items():
        try:
            logger.info("fetching_series", series_id=series_id, name=series_name)

            # Fetch metadata
            metadata = fetch_fred_metadata(series_id, FRED_API_KEY)
            if not metadata:
                logger.warning("no_metadata", series_id=series_id)
                metadata = {
                    'title': series_name,
                    'units': 'Index',
                    'frequency': 'Monthly',
                    'seasonal_adjustment': 'Not Seasonally Adjusted',
                    'last_updated': None
                }

            # Fetch latest observation
            observation = fetch_fred_series(series_id, FRED_API_KEY)
            if not observation or observation['value'] is None:
                logger.warning("no_observation", series_id=series_id)
                failed += 1
                continue

            # Insert into database
            cursor.execute("""
                INSERT INTO economic_data.fred_series
                (series_id, date, value, title, frequency, units, seasonal_adjustment, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (series_id, date) DO UPDATE
                SET value = EXCLUDED.value,
                    title = EXCLUDED.title,
                    last_updated = EXCLUDED.last_updated
            """, (
                series_id,
                observation['date'],
                observation['value'],
                metadata['title'],
                metadata['frequency'],
                metadata['units'],
                metadata['seasonal_adjustment'],
                metadata.get('last_updated')
            ))

            logger.info("series_inserted",
                       series_id=series_id,
                       value=observation['value'],
                       date=observation['date'])

            inserted += 1

        except Exception as e:
            logger.error("series_insert_failed", series_id=series_id, error=str(e))
            failed += 1

    conn.commit()
    cursor.close()
    conn.close()

    logger.info("fred_population_complete", inserted=inserted, failed=failed)

    return inserted, failed


def verify_data():
    """Verify FRED data in database"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM economic_data.fred_series")
    count = cursor.fetchone()['count']

    cursor.execute("""
        SELECT series_id, title, value, date
        FROM economic_data.fred_series
        ORDER BY date DESC, series_id
        LIMIT 10
    """)

    sample = cursor.fetchall()

    cursor.close()
    conn.close()

    logger.info("verification_complete", total_rows=count, sample_count=len(sample))

    return count, sample


def main():
    """Main execution"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║           SPARTAN RESEARCH STATION                           ║
║           FRED Data Population Script                        ║
║                                                               ║
║  Populating FRED database with real economic data           ║
║  Source: Federal Reserve Economic Data (FRED API)           ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)

    if FRED_API_KEY == 'abcdefghijklmnopqrstuvwxyz123456':
        print("\n⚠️  WARNING: Using placeholder FRED API key")
        print("Get a free API key at: https://fred.stlouisfed.org/docs/api/api_key.html")
        print("Continuing anyway (API may fail)...\n")

    try:
        print(f"Fetching {len(FRED_SERIES)} FRED series...")
        inserted, failed = populate_fred_data()

        print(f"\n✅ Inserted: {inserted} series")
        print(f"❌ Failed: {failed} series")

        if inserted > 0:
            print("\nVerifying data...")
            count, sample = verify_data()

            print(f"\nTotal rows in database: {count}")
            print(f"\nSample data (latest {len(sample)} records):")
            for row in sample:
                print(f"  {row['series_id']:15} {row['title'][:40]:40} = {row['value']:>10.2f} ({row['date']})")

            print("\n✅ FRED data population complete!")
            print(f"API endpoint now available: http://localhost:8888/api/economic/fred/<series_id>")

        return 0 if failed == 0 else 1

    except Exception as e:
        logger.error("population_failed", error=str(e), exc_info=True)
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
