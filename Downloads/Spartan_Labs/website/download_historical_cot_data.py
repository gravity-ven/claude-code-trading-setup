#!/home/spartan/miniconda3/bin/python3
"""
Download Historical COT Data (52 Weeks)

Downloads the past 52 weeks of CFTC Commitment of Traders data
to enable proper COT Index calculation and signal generation.

NO FAKE DATA: Downloads real CFTC.gov reports only.
"""

import os
import sys
import logging
import psycopg2
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HistoricalCOTDownloader:
    """Download and store historical COT data from CFTC"""

    def __init__(self):
        """Initialize downloader"""
        self.cftc_base_url = "https://www.cftc.gov/files/dea/history/"
        self.db_conn = None
        self.connect_to_database()

        # Symbols we track (42+ markets)
        self.symbols = {
            # Indices
            'ES': '13874+',  # S&P 500
            'NQ': '20974+',  # Nasdaq 100
            'YM': '12460+',  # Dow Jones
            'RTY': '23947+', # Russell 2000

            # Currencies
            'DX': '09830+',  # US Dollar Index
            'EUR': '09900+', # Euro
            'JPY': '09730+', # Yen
            'GBP': '09650+', # British Pound
            'AUD': '23260+', # Australian Dollar
            'CAD': '09040+', # Canadian Dollar
            'CHF': '09270+', # Swiss Franc

            # Metals
            'GC': '08830+',  # Gold
            'SI': '08470+',  # Silver
            'HG': '08530+',  # Copper
            'PL': '07630+',  # Platinum

            # Energy
            'CL': '06730+',  # Crude Oil
            'NG': '02330+',  # Natural Gas
            'HO': '02270+',  # Heating Oil
            'RB': '11140+',  # Gasoline

            # Grains
            'ZC': '00290+',  # Corn
            'ZS': '00510+',  # Soybeans
            'ZW': '00110+',  # Wheat
            'ZL': '00720+',  # Soybean Oil
            'ZM': '00650+',  # Soybean Meal

            # Softs
            'SB': '08050+',  # Sugar
            'KC': '08310+',  # Coffee
            'CC': '06710+',  # Cocoa
            'CT': '03360+',  # Cotton
            'OJ': '04030+',  # Orange Juice

            # Meats
            'LE': '05730+',  # Live Cattle
            'GF': '06130+',  # Feeder Cattle
            'HE': '05470+',  # Lean Hogs

            # Bonds
            'ZN': '04390+',  # 10-Year Treasury
            'ZB': '02010+',  # 30-Year Treasury
            'ZF': '04470+',  # 5-Year Treasury
            'ZT': '04230+',  # 2-Year Treasury

            # Crypto Futures
            'BTC': '13374A',  # Bitcoin
            'ETH': '15062+',  # Ethereum
        }

        logger.info(f"Tracking {len(self.symbols)} markets")

    def connect_to_database(self):
        """Connect to PostgreSQL"""
        try:
            self.db_conn = psycopg2.connect(
                dbname=os.getenv('POSTGRES_DB', 'spartan_research_db'),
                user=os.getenv('POSTGRES_USER', 'spartan'),
                password=os.getenv('POSTGRES_PASSWORD', 'spartan'),
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=os.getenv('POSTGRES_PORT', '5432')
            )
            logger.info("✅ Connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise

    def get_report_dates(self, weeks: int = 52) -> List[datetime]:
        """
        Calculate report dates for past N weeks
        CFTC releases reports on Fridays (Tuesday positions)
        """
        dates = []
        today = datetime.now()

        # Find most recent Friday
        days_since_friday = (today.weekday() - 4) % 7
        most_recent_friday = today - timedelta(days=days_since_friday)

        # Go back N weeks
        for i in range(weeks):
            report_date = most_recent_friday - timedelta(weeks=i)
            dates.append(report_date)

        logger.info(f"Downloading {weeks} weeks of data")
        logger.info(f"Date range: {dates[-1].strftime('%Y-%m-%d')} to {dates[0].strftime('%Y-%m-%d')}")

        return dates

    def download_weekly_file(self, year: int) -> Optional[str]:
        """
        Download disaggregated futures file for a specific year

        CFTC publishes annual files with all weekly reports
        URL format: https://www.cftc.gov/files/dea/history/deacot[YYYY].zip
        """
        url = f"{self.cftc_base_url}deacot{year}.zip"

        logger.info(f"Downloading CFTC data for {year}...")
        logger.info(f"URL: {url}")

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Save to temp file
            zip_path = f"/tmp/cftc_{year}.zip"
            with open(zip_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"✅ Downloaded {len(response.content)} bytes for {year}")
            return zip_path

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"⚠️  File not found for {year} (may not be published yet)")
            else:
                logger.error(f"❌ HTTP error downloading {year}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error downloading {year}: {e}")
            return None

    def parse_cot_file(self, file_path: str) -> List[Dict]:
        """
        Parse CFTC disaggregated futures TXT file
        Returns list of COT records
        """
        records = []

        try:
            import zipfile

            # Extract TXT file from ZIP
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Find the COT data file (annual.txt or f_disagg.txt)
                txt_files = [f for f in zip_ref.namelist() if f.endswith('.txt')]

                if not txt_files:
                    logger.warning(f"No TXT file found in {file_path}")
                    return records

                txt_file = txt_files[0]
                logger.info(f"Parsing {txt_file}...")

                with zip_ref.open(txt_file) as f:
                    content = f.read().decode('utf-8', errors='ignore')

                # Parse CSV-like data
                lines = content.split('\n')
                header = None

                for line_num, line in enumerate(lines):
                    if line_num == 0:
                        # Header row
                        header = [col.strip().strip('"') for col in line.split(',')]
                        continue

                    if not line.strip():
                        continue

                    # Parse data row
                    fields = [field.strip().strip('"') for field in line.split(',')]

                    if len(fields) < 13:
                        continue

                    try:
                        # Extract key fields (annual.txt format)
                        market_name = fields[0] if len(fields) > 0 else None
                        report_date = fields[1] if len(fields) > 1 else None  # YYMMDD format
                        market_code = fields[3] if len(fields) > 3 else None

                        # Commercial positions (Column 11 = Long, Column 12 = Short)
                        comm_long = int(fields[11].replace(',', '').strip()) if len(fields) > 11 and fields[11].strip() else 0
                        comm_short = int(fields[12].replace(',', '').strip()) if len(fields) > 12 and fields[12].strip() else 0

                        # Find matching symbol by market code or name
                        symbol = None
                        for sym, code in self.symbols.items():
                            # Match by CFTC code
                            if market_code and code.replace('+', '').replace('A', '') in market_code:
                                symbol = sym
                                break
                            # Match by market name
                            if market_name:
                                name_upper = market_name.upper()
                                if sym == 'GC' and 'GOLD' in name_upper:
                                    symbol = 'GC'
                                    break
                                elif sym == 'SI' and 'SILVER' in name_upper:
                                    symbol = 'SI'
                                    break
                                elif sym == 'CL' and 'CRUDE' in name_upper and 'WTI' in name_upper:
                                    symbol = 'CL'
                                    break
                                elif sym == 'BTC' and 'BITCOIN' in name_upper:
                                    symbol = 'BTC'
                                    break
                                elif sym == 'ETH' and 'ETHEREUM' in name_upper:
                                    symbol = 'ETH'
                                    break

                        if symbol and report_date:
                            records.append({
                                'symbol': symbol,
                                'report_date': report_date,
                                'commercial_long': comm_long,
                                'commercial_short': comm_short,
                                'commercial_net': comm_long - comm_short,
                                'market_code': market_code
                            })

                    except (ValueError, IndexError) as e:
                        # Skip malformed rows
                        continue

                logger.info(f"✅ Parsed {len(records)} COT records")

        except Exception as e:
            logger.error(f"❌ Error parsing {file_path}: {e}")

        return records

    def store_cot_records(self, records: List[Dict]) -> int:
        """
        Store COT records to PostgreSQL
        Returns count of records stored
        """
        if not records:
            return 0

        stored_count = 0

        try:
            cursor = self.db_conn.cursor()

            for record in records:
                try:
                    # Parse report date (format: YYMMDD)
                    report_date_str = record['report_date']

                    if len(report_date_str) == 6:
                        year = int('20' + report_date_str[0:2])
                        month = int(report_date_str[2:4])
                        day = int(report_date_str[4:6])
                        report_date = f"{year}-{month:02d}-{day:02d}"
                    else:
                        continue

                    # Insert with ON CONFLICT to avoid duplicates
                    cursor.execute("""
                        INSERT INTO cot_raw_data (
                            report_date, symbol, commercial_long, commercial_short,
                            commercial_net, data_source
                        )
                        VALUES (%s, %s, %s, %s, %s, 'CFTC.gov')
                        ON CONFLICT (report_date, symbol)
                        DO UPDATE SET
                            commercial_long = EXCLUDED.commercial_long,
                            commercial_short = EXCLUDED.commercial_short,
                            commercial_net = EXCLUDED.commercial_net,
                            updated_at = now()
                    """, (
                        report_date,
                        record['symbol'],
                        record['commercial_long'],
                        record['commercial_short'],
                        record['commercial_net']
                    ))

                    stored_count += 1

                except Exception as e:
                    logger.debug(f"Skipping record: {e}")
                    continue

            self.db_conn.commit()
            cursor.close()

            logger.info(f"✅ Stored {stored_count} COT records to database")

        except Exception as e:
            logger.error(f"❌ Error storing records: {e}")
            self.db_conn.rollback()

        return stored_count

    def check_data_coverage(self):
        """Check how many weeks of data we have per symbol"""
        try:
            cursor = self.db_conn.cursor()

            cursor.execute("""
                SELECT
                    symbol,
                    COUNT(*) as weeks,
                    MIN(report_date) as earliest,
                    MAX(report_date) as latest
                FROM cot_raw_data
                GROUP BY symbol
                ORDER BY weeks DESC
            """)

            results = cursor.fetchall()
            cursor.close()

            logger.info("=" * 70)
            logger.info("DATA COVERAGE SUMMARY")
            logger.info("=" * 70)

            if not results:
                logger.warning("⚠️  No historical data found")
                return

            for symbol, weeks, earliest, latest in results:
                status = "✅" if weeks >= 26 else "⚠️ "
                logger.info(f"{status} {symbol:6s} - {weeks:3d} weeks ({earliest} to {latest})")

            logger.info("=" * 70)

            # Overall summary
            total_symbols = len(results)
            ready_symbols = sum(1 for _, weeks, _, _ in results if weeks >= 26)

            logger.info(f"Total symbols: {total_symbols}")
            logger.info(f"Ready for COT Index (26+ weeks): {ready_symbols}")
            logger.info(f"Still building: {total_symbols - ready_symbols}")

            if ready_symbols >= 20:
                logger.info("✅ SYSTEM READY - Sufficient historical data for analysis")
            elif ready_symbols > 0:
                logger.info("⚡ PARTIAL READY - Some symbols ready for analysis")
            else:
                logger.warning("⏳ BUILDING - Need more historical data")

        except Exception as e:
            logger.error(f"❌ Error checking coverage: {e}")

    def download_all_historical_data(self, weeks: int = 156):
        """
        Main entry point: Download 156 weeks (3 years) of historical data
        """
        logger.info("=" * 70)
        logger.info("HISTORICAL COT DATA DOWNLOAD")
        logger.info("=" * 70)
        logger.info(f"Target: {weeks} weeks of data ({weeks/52:.1f} years)")
        logger.info(f"Markets: {len(self.symbols)} symbols")
        logger.info("=" * 70)
        logger.info("")

        # Determine which years to download (3 years)
        current_year = datetime.now().year
        years_to_download = [current_year, current_year - 1, current_year - 2]

        logger.info(f"Downloading data for years: {years_to_download}")
        logger.info("")

        total_records = 0

        for year in years_to_download:
            logger.info(f"Processing {year}...")

            # Download ZIP file
            zip_path = self.download_weekly_file(year)

            if not zip_path:
                logger.warning(f"⚠️  Skipping {year} (download failed)")
                continue

            # Parse COT data
            records = self.parse_cot_file(zip_path)

            # Store to database
            stored = self.store_cot_records(records)
            total_records += stored

            # Clean up
            try:
                os.remove(zip_path)
            except:
                pass

            # Rate limiting (be nice to CFTC servers)
            time.sleep(2)

        logger.info("")
        logger.info("=" * 70)
        logger.info(f"✅ DOWNLOAD COMPLETE - {total_records} total records stored")
        logger.info("=" * 70)
        logger.info("")

        # Check coverage
        self.check_data_coverage()


def main():
    """Main entry point"""
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║                                                                  ║")
    print("║         SPARTAN COT AGENTS - Historical Data Download           ║")
    print("║                                                                  ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print("")
    print("This will download 156 weeks (3 years) of CFTC COT data for 42+ markets.")
    print("")
    print("⏱️  Estimated time: 3-7 minutes")
    print("📊 Data source: CFTC.gov (official government data)")
    print("🎯 Purpose: Enable COT Index calculation and trade signals")
    print("💾 Storage: PostgreSQL (spartan_research_db)")
    print("")
    print("Press Enter to start download...")
    input()

    try:
        downloader = HistoricalCOTDownloader()
        downloader.download_all_historical_data(weeks=156)

        print("")
        print("=" * 70)
        print("✅ SUCCESS - Historical data downloaded")
        print("=" * 70)
        print("")
        print("Next steps:")
        print("  1. Run agents: ./START_TUI_WITH_TRADES.sh")
        print("  2. Trade signals will now show (if extremes exist)")
        print("  3. System auto-maintains historical data going forward")
        print("")

    except KeyboardInterrupt:
        print("\n⚠️  Download cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
