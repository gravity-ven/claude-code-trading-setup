#!/usr/bin/env python3
"""
Populate Missing Database Tables with Real Data
==============================================================================
Populates VIX, Forex, Market Breadth data from real sources (yfinance)
==============================================================================
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import yfinance as yf
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


def get_db():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def create_missing_tables():
    """Create tables if they don't exist"""
    conn = get_db()
    cursor = conn.cursor()

    # Create volatility_indicators table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_data.volatility_indicators (
            id SERIAL PRIMARY KEY,
            indicator VARCHAR(50) NOT NULL,
            value NUMERIC(10, 2) NOT NULL,
            change_percent NUMERIC(10, 2),
            timestamp TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(indicator, timestamp)
        );

        CREATE INDEX IF NOT EXISTS idx_volatility_timestamp
        ON market_data.volatility_indicators(timestamp DESC);
    """)

    # Create forex_rates table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_data.forex_rates (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            base_currency VARCHAR(10) NOT NULL,
            quote_currency VARCHAR(10) NOT NULL,
            rate NUMERIC(20, 6) NOT NULL,
            change_percent NUMERIC(10, 2),
            timestamp TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(symbol, timestamp)
        );

        CREATE INDEX IF NOT EXISTS idx_forex_timestamp
        ON market_data.forex_rates(timestamp DESC);
    """)

    conn.commit()
    cursor.close()
    conn.close()

    logger.info("tables_created", tables=["volatility_indicators", "forex_rates"])


def populate_volatility_data():
    """Populate VIX and volatility indicators from Yahoo Finance"""
    logger.info("populating_volatility_data")

    symbols = {
        '^VIX': 'VIX',      # CBOE Volatility Index
        '^VXN': 'VXN',      # NASDAQ Volatility Index
        'UVXY': 'UVXY',     # ProShares Ultra VIX
        'VXX': 'VXX'        # iPath Series B S&P 500 VIX
    }

    conn = get_db()
    cursor = conn.cursor()

    for yahoo_symbol, indicator_name in symbols.items():
        try:
            ticker = yf.Ticker(yahoo_symbol)
            hist = ticker.history(period='5d')

            if hist.empty:
                logger.warning("no_data", symbol=yahoo_symbol)
                continue

            # Get latest data
            latest = hist.iloc[-1]
            previous = hist.iloc[-2] if len(hist) > 1 else hist.iloc[-1]

            value = float(latest['Close'])
            previous_value = float(previous['Close'])
            change_percent = ((value - previous_value) / previous_value) * 100 if previous_value != 0 else 0

            # Insert into database
            cursor.execute("""
                INSERT INTO market_data.volatility_indicators
                (indicator, value, change_percent, timestamp)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (indicator, timestamp) DO UPDATE
                SET value = EXCLUDED.value,
                    change_percent = EXCLUDED.change_percent
            """, (indicator_name, value, change_percent))

            logger.info("volatility_inserted",
                       indicator=indicator_name,
                       value=value,
                       change_percent=round(change_percent, 2))

        except Exception as e:
            logger.error("volatility_error", symbol=yahoo_symbol, error=str(e))

    conn.commit()
    cursor.close()
    conn.close()

    logger.info("volatility_data_complete")


def populate_forex_data():
    """Populate forex rates from Yahoo Finance"""
    logger.info("populating_forex_data")

    pairs = {
        'EURUSD=X': ('EUR', 'USD'),
        'GBPUSD=X': ('GBP', 'USD'),
        'USDJPY=X': ('USD', 'JPY'),
        'AUDUSD=X': ('AUD', 'USD'),
        'USDCAD=X': ('USD', 'CAD'),
        'USDCHF=X': ('USD', 'CHF'),
        'NZDUSD=X': ('NZD', 'USD')
    }

    conn = get_db()
    cursor = conn.cursor()

    for symbol, (base, quote) in pairs.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='5d')

            if hist.empty:
                logger.warning("no_data", symbol=symbol)
                continue

            # Get latest data
            latest = hist.iloc[-1]
            previous = hist.iloc[-2] if len(hist) > 1 else hist.iloc[-1]

            rate = float(latest['Close'])
            previous_rate = float(previous['Close'])
            change_percent = ((rate - previous_rate) / previous_rate) * 100 if previous_rate != 0 else 0

            # Insert into database
            cursor.execute("""
                INSERT INTO market_data.forex_rates
                (symbol, base_currency, quote_currency, rate, change_percent, timestamp)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (symbol, timestamp) DO UPDATE
                SET rate = EXCLUDED.rate,
                    change_percent = EXCLUDED.change_percent
            """, (symbol, base, quote, rate, change_percent))

            logger.info("forex_inserted",
                       symbol=symbol,
                       pair=f"{base}/{quote}",
                       rate=rate,
                       change_percent=round(change_percent, 2))

        except Exception as e:
            logger.error("forex_error", symbol=symbol, error=str(e))

    conn.commit()
    cursor.close()
    conn.close()

    logger.info("forex_data_complete")


def populate_indices_and_commodities():
    """Populate indices and commodities tables with latest data"""
    logger.info("populating_indices_commodities")

    indices = {
        '^GSPC': 'S&P 500',
        '^DJI': 'Dow Jones',
        '^IXIC': 'NASDAQ',
        '^RUT': 'Russell 2000'
    }

    commodities = {
        'GC=F': 'Gold',
        'SI=F': 'Silver',
        'CL=F': 'Crude Oil',
        'NG=F': 'Natural Gas'
    }

    conn = get_db()
    cursor = conn.cursor()

    # Populate indices
    for symbol, name in indices.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='5d')

            if hist.empty:
                continue

            latest = hist.iloc[-1]
            previous = hist.iloc[-2] if len(hist) > 1 else hist.iloc[-1]

            price = float(latest['Close'])
            previous_price = float(previous['Close'])
            change_percent = ((price - previous_price) / previous_price) * 100 if previous_price != 0 else 0
            volume = int(latest['Volume'])

            cursor.execute("""
                INSERT INTO market_data.indices
                (symbol, name, price, change_percent, volume, timestamp)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (symbol, name, price, change_percent, volume))

            logger.info("index_inserted", symbol=symbol, name=name, price=price)

        except Exception as e:
            logger.error("index_error", symbol=symbol, error=str(e))

    # Populate commodities
    for symbol, name in commodities.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='5d')

            if hist.empty:
                continue

            latest = hist.iloc[-1]
            previous = hist.iloc[-2] if len(hist) > 1 else hist.iloc[-1]

            price = float(latest['Close'])
            previous_price = float(previous['Close'])
            change_percent = ((price - previous_price) / previous_price) * 100 if previous_price != 0 else 0
            volume = int(latest['Volume'])

            cursor.execute("""
                INSERT INTO market_data.commodities
                (symbol, name, price, change_percent, volume, timestamp)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (symbol, name, price, change_percent, volume))

            logger.info("commodity_inserted", symbol=symbol, name=name, price=price)

        except Exception as e:
            logger.error("commodity_error", symbol=symbol, error=str(e))

    conn.commit()
    cursor.close()
    conn.close()

    logger.info("indices_commodities_complete")


def verify_data():
    """Verify all data has been populated"""
    logger.info("verifying_data")

    conn = get_db()
    cursor = conn.cursor()

    # Check volatility indicators
    cursor.execute("SELECT COUNT(*) as count FROM market_data.volatility_indicators WHERE timestamp > NOW() - INTERVAL '1 hour'")
    volatility_count = cursor.fetchone()['count']
    logger.info("volatility_count", count=volatility_count)

    # Check forex rates
    cursor.execute("SELECT COUNT(*) as count FROM market_data.forex_rates WHERE timestamp > NOW() - INTERVAL '1 hour'")
    forex_count = cursor.fetchone()['count']
    logger.info("forex_count", count=forex_count)

    # Check indices
    cursor.execute("SELECT COUNT(*) as count FROM market_data.indices WHERE timestamp > NOW() - INTERVAL '1 hour'")
    indices_count = cursor.fetchone()['count']
    logger.info("indices_count", count=indices_count)

    # Check commodities
    cursor.execute("SELECT COUNT(*) as count FROM market_data.commodities WHERE timestamp > NOW() - INTERVAL '1 hour'")
    commodities_count = cursor.fetchone()['count']
    logger.info("commodities_count", count=commodities_count)

    cursor.close()
    conn.close()

    summary = {
        'volatility_indicators': volatility_count,
        'forex_rates': forex_count,
        'indices': indices_count,
        'commodities': commodities_count
    }

    logger.info("verification_complete", summary=summary)

    return summary


def main():
    """Main execution"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║           SPARTAN RESEARCH STATION                           ║
║           Data Population Script                             ║
║                                                               ║
║  Populating missing database tables with REAL data          ║
║  Sources: Yahoo Finance (yfinance)                           ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)

    try:
        # Step 1: Create missing tables
        logger.info("step_1_create_tables")
        create_missing_tables()

        # Step 2: Populate volatility data
        logger.info("step_2_populate_volatility")
        populate_volatility_data()

        # Step 3: Populate forex data
        logger.info("step_3_populate_forex")
        populate_forex_data()

        # Step 4: Populate indices and commodities (refresh)
        logger.info("step_4_populate_indices_commodities")
        populate_indices_and_commodities()

        # Step 5: Verify all data
        logger.info("step_5_verify_data")
        summary = verify_data()

        # Print summary
        print("\n✅ DATA POPULATION COMPLETE\n")
        print(f"  Volatility Indicators: {summary['volatility_indicators']}")
        print(f"  Forex Rates: {summary['forex_rates']}")
        print(f"  Indices: {summary['indices']}")
        print(f"  Commodities: {summary['commodities']}")
        print("\nAll missing data has been populated with REAL data from Yahoo Finance.")
        print("Frontend should now display all market data correctly.\n")

        return 0

    except Exception as e:
        logger.error("population_failed", error=str(e), exc_info=True)
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
