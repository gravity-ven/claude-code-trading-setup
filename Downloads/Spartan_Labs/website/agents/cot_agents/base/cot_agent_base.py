"""
COT Agent Base Class - Tier 1 (Agents 1-30)

Base class for all COT (Commitment of Traders) analysis agents.
These agents fetch, analyze, and calculate COT Index from CFTC.gov data.

NO FAKE DATA: All data must come from real CFTC.gov reports.
"""

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import requests
import time

# Logging will be configured by orchestrator


class COTAgentBase:
    """
    Base class for COT analysis agents (Tier 1, Agents 1-30)

    Responsibilities:
    - Fetch COT data from CFTC.gov
    - Calculate COT Index (0-100 scale)
    - Detect extremes and divergences
    - Generate trade signals based on COT positioning
    """

    def __init__(self, agent_id: int, agent_name: str, symbols: List[str]):
        """
        Initialize COT Agent

        Args:
            agent_id: Unique agent ID (1-30)
            agent_name: Human-readable agent name
            symbols: List of symbols this agent monitors
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.agent_tier = "TIER1_COT"
        self.symbols = symbols

        # Logger with agent context (initialize first)
        self.logger = logging.getLogger(f"Agent{agent_id}")

        # Database connection
        self.db_conn = None
        self.connect_to_database()

        # CFTC data source
        self.cftc_base_url = "https://www.cftc.gov/dea/newcot/"

        # Signal thresholds
        self.STRONG_BULLISH_THRESHOLD = 95
        self.BULLISH_THRESHOLD = 75
        self.BEARISH_THRESHOLD = 25
        self.STRONG_BEARISH_THRESHOLD = 5

        self.logger.info(f"Initialized {self.agent_name} monitoring {len(symbols)} symbols")

    def connect_to_database(self):
        """
        Connect to PostgreSQL database (spartan_research_db)

        RULE: PostgreSQL ONLY - No SQLite allowed
        """
        try:
            self.db_conn = psycopg2.connect(
                dbname=os.getenv('POSTGRES_DB', 'spartan_research_db'),
                user=os.getenv('POSTGRES_USER', 'spartan'),
                password=os.getenv('POSTGRES_PASSWORD', 'spartan'),
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=os.getenv('POSTGRES_PORT', '5432')
            )
            self.logger.info("✅ Connected to PostgreSQL database")
        except Exception as e:
            self.logger.error(f"❌ Database connection failed: {e}")
            raise

    def fetch_cot_data(self, symbol: str) -> Optional[Dict]:
        """
        Fetch latest COT data from CFTC.gov

        NO FAKE DATA: Returns None if fetch fails. Never generates mock data.

        Args:
            symbol: Market symbol (e.g., 'GC' for Gold, 'ES' for S&P)

        Returns:
            Dict with COT data or None on failure
        """
        try:
            # Fetch from CFTC.gov
            # Note: CFTC releases data on Fridays for Tuesday's positions
            # Use weekly files (not annual files - those don't exist anymore)
            url = f"{self.cftc_base_url}f_disagg.txt"  # Disaggregated Futures format

            self.logger.info(f"Fetching COT data for {symbol} from CFTC.gov...")

            # Apply rate limiting (be respectful to CFTC servers)
            time.sleep(2)

            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Parse COT report - pass the original symbol for matching
            data = self.parse_cot_report(response.text, symbol)

            if data:
                self.logger.info(f"✅ Fetched COT data for {symbol}: Commercial Net = {data.get('commercial_net')}")
                return data
            else:
                self.logger.warning(f"⚠️  No data found for {symbol} in COT report")
                return None

        except Exception as e:
            self.logger.error(f"❌ Failed to fetch COT data for {symbol}: {e}")
            # NO FAKE DATA: Return None on error
            return None

    def parse_cot_report(self, report_text: str, cftc_code: str) -> Optional[Dict]:
        """
        Parse CFTC COT report text format (CSV)

        Args:
            report_text: Raw COT report text (CSV format)
            cftc_code: CFTC market code

        Returns:
            Dict with parsed data or None
        """
        try:
            import csv
            from io import StringIO

            # Parse CSV data
            csv_reader = csv.reader(StringIO(report_text))

            # Find the row for our symbol
            for row_num, row in enumerate(csv_reader):
                if len(row) < 10:
                    continue

                # Row format (disaggregated futures):
                # Market_and_Exchange_Names, As_of_Date_In_Form_YYMMDD, ...
                # Positions: Producer/Merchant/Processor/User (commercials)

                market_name = row[0] if len(row) > 0 else ""

                # Match using the symbol name (e.g., "GC" matches "GOLD")
                if self._match_symbol(market_name, cftc_code):
                    try:
                        # Extract key data points
                        # For disaggregated futures: Prod_Merc positions are in columns 8-9
                        # Column 8: Prod/Merc/Proc/User Long
                        # Column 9: Prod/Merc/Proc/User Short

                        if len(row) >= 10:
                            # Clean and parse numeric values (remove spaces and commas)
                            commercial_long_str = row[8].strip().replace(',', '').replace(' ', '')
                            commercial_short_str = row[9].strip().replace(',', '').replace(' ', '')

                            commercial_long = int(commercial_long_str) if commercial_long_str.isdigit() else 0
                            commercial_short = int(commercial_short_str) if commercial_short_str.isdigit() else 0
                            commercial_net = commercial_long - commercial_short

                            data = {
                                'market': market_name,
                                'commercial_long': commercial_long,
                                'commercial_short': commercial_short,
                                'commercial_net': commercial_net,
                                'report_date': row[1] if len(row) > 1 else 'Unknown',
                            }

                            self.logger.info(f"✅ Parsed COT data: {market_name} - Net: {commercial_net:,}")
                            return data
                    except (ValueError, IndexError) as e:
                        self.logger.warning(f"Error parsing row for {market_name}: {e}")
                        continue

            # Not found
            self.logger.warning(f"Symbol {cftc_code} not found in COT report")
            return None

        except Exception as e:
            self.logger.error(f"Error parsing COT report: {e}")
            return None

    def _match_symbol(self, market_name: str, symbol: str) -> bool:
        """Helper to match symbol with market name"""
        # Common mappings
        mappings = {
            'GC': ['GOLD', 'GLD'],
            'SI': ['SILVER', 'SLV'],
            'CL': ['CRUDE', 'OIL', 'WTI'],
            'NG': ['NATURAL GAS', 'NAT GAS'],
            'ES': ['S&P', 'E-MINI S&P'],
            'EUR': ['EURO'],
            'GBP': ['POUND', 'BRITISH'],
            'BTC': ['BITCOIN', 'BTC'],
            'ETH': ['ETHEREUM', 'ETH', 'ETHER'],
        }

        symbol_upper = symbol.upper()
        if symbol_upper in mappings:
            return any(term in market_name.upper() for term in mappings[symbol_upper])

        return symbol_upper in market_name.upper()

    def get_cftc_code(self, symbol: str) -> Optional[str]:
        """
        Map trading symbol to CFTC market code

        Args:
            symbol: Trading symbol (e.g., 'GC', 'ES')

        Returns:
            CFTC code or None
        """
        # Official CFTC market codes
        SYMBOL_TO_CFTC = {
            # Indices
            'ES': '13874+',  # S&P 500 E-mini
            'NQ': '20974+',  # Nasdaq 100 E-mini
            'YM': '12460+',  # Dow Jones E-mini
            'RTY': '23947+', # Russell 2000 E-mini

            # Currencies
            'DX': '09830+',  # US Dollar Index
            'EUR': '09900+', # Euro FX
            'JPY': '09730+', # Japanese Yen
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
            'CL': '06730+',  # Crude Oil WTI
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

            # Crypto Futures (CFTC tracked)
            'BTC': '13374A',  # Bitcoin Futures (CME)
            'ETH': '15062+',  # Ethereum Futures (CME)
        }

        return SYMBOL_TO_CFTC.get(symbol)

    def calculate_cot_index(self, symbol: str) -> Optional[float]:
        """
        Calculate COT Index for a symbol

        Formula: ((Current_Net - Min_Net) / (Max_Net - Min_Net)) × 100

        Args:
            symbol: Market symbol

        Returns:
            COT Index (0-100) or None on failure
        """
        try:
            cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)

            # Use PostgreSQL function (defined in schema)
            cursor.execute("""
                SELECT calculate_cot_index(%s, CURRENT_DATE) AS cot_index
            """, (symbol,))

            result = cursor.fetchone()
            cursor.close()

            if result and result['cot_index'] is not None:
                cot_index = float(result['cot_index'])
                self.logger.info(f"✅ COT Index for {symbol}: {cot_index:.2f}")
                return cot_index
            else:
                self.logger.warning(f"⚠️  No COT Index calculated for {symbol}")
                return None

        except Exception as e:
            self.logger.error(f"❌ Error calculating COT Index for {symbol}: {e}")
            return None

    def classify_cot_signal(self, cot_index: float) -> str:
        """
        Classify COT Index into signal type

        Args:
            cot_index: COT Index value (0-100)

        Returns:
            Signal classification string
        """
        if cot_index > self.STRONG_BULLISH_THRESHOLD:
            return "STRONG_BULLISH"
        elif cot_index > self.BULLISH_THRESHOLD:
            return "BULLISH"
        elif cot_index > self.BEARISH_THRESHOLD:
            return "NEUTRAL"
        elif cot_index > self.STRONG_BEARISH_THRESHOLD:
            return "BEARISH"
        else:
            return "STRONG_BEARISH"

    def store_raw_cot_data(self, symbol: str, cot_data: Dict):
        """
        Store raw COT data to database

        Args:
            symbol: Market symbol
            cot_data: Raw COT data dictionary from CFTC
        """
        try:
            cursor = self.db_conn.cursor()

            # Parse report date (format: YYMMDD)
            report_date_str = cot_data.get('report_date', 'Unknown')
            if report_date_str != 'Unknown' and len(report_date_str) == 6:
                # Convert YYMMDD to YYYY-MM-DD
                year = int('20' + report_date_str[0:2])
                month = int(report_date_str[2:4])
                day = int(report_date_str[4:6])
                report_date = f"{year}-{month:02d}-{day:02d}"
            else:
                report_date = datetime.now().strftime('%Y-%m-%d')

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
                symbol,
                cot_data.get('commercial_long', 0),
                cot_data.get('commercial_short', 0),
                cot_data.get('commercial_net', 0)
            ))

            self.db_conn.commit()
            cursor.close()

            self.logger.info(f"✅ Stored raw COT data for {symbol} (date: {report_date})")

        except Exception as e:
            self.logger.error(f"❌ Error storing raw COT data: {e}")
            self.db_conn.rollback()

    def store_cot_metrics(self, symbol: str, cot_index: float, trend: str):
        """
        Store calculated COT metrics to database

        Args:
            symbol: Market symbol
            cot_index: Calculated COT Index
            trend: Signal classification
        """
        try:
            cursor = self.db_conn.cursor()

            cursor.execute("""
                INSERT INTO cot_calculated_metrics (
                    calculation_date, symbol, cot_index, cot_trend, calculated_by_agent
                )
                VALUES (CURRENT_DATE, %s, %s, %s, %s)
                ON CONFLICT (calculation_date, symbol)
                DO UPDATE SET
                    cot_index = EXCLUDED.cot_index,
                    cot_trend = EXCLUDED.cot_trend,
                    calculated_by_agent = EXCLUDED.calculated_by_agent
            """, (symbol, cot_index, trend, self.agent_id))

            self.db_conn.commit()
            cursor.close()

            self.logger.info(f"✅ Stored COT metrics for {symbol}")

        except Exception as e:
            self.logger.error(f"❌ Error storing COT metrics: {e}")
            self.db_conn.rollback()

    def generate_signal(self, symbol: str, cot_index: float, trend: str) -> Optional[Dict]:
        """
        Generate trade signal based on COT analysis

        Args:
            symbol: Market symbol
            cot_index: COT Index value
            trend: Signal classification

        Returns:
            Signal dict or None
        """
        # Only generate signals for extremes
        if cot_index <= self.STRONG_BEARISH_THRESHOLD or cot_index >= self.STRONG_BULLISH_THRESHOLD:

            direction = "LONG" if cot_index >= self.STRONG_BULLISH_THRESHOLD else "SHORT"
            strength = cot_index if direction == "LONG" else (100 - cot_index)

            signal = {
                'agent_id': self.agent_id,
                'agent_tier': self.agent_tier,
                'agent_name': self.agent_name,
                'symbol': symbol,
                'direction': direction,
                'signal_strength': strength,
                'confidence': min(95, strength),  # Cap at 95%
                'factors': {
                    'cot_index': cot_index,
                    'cot_trend': trend,
                    'is_extreme': True
                }
            }

            self.logger.info(f"🎯 Generated {direction} signal for {symbol} (COT Index: {cot_index:.2f})")
            return signal

        return None

    def run(self):
        """
        Main execution loop for this agent

        Process:
        1. Fetch COT data for assigned symbols
        2. Calculate COT Index
        3. Classify signals
        4. Store to database
        5. Generate trade signals
        """
        self.logger.info(f"🚀 Starting {self.agent_name}")

        for symbol in self.symbols:
            try:
                # Step 1: Fetch COT data (REAL DATA ONLY)
                cot_data = self.fetch_cot_data(symbol)

                if not cot_data:
                    self.logger.warning(f"⚠️  Skipping {symbol} - no COT data available")
                    continue

                # Step 2: Store raw COT data to database
                self.store_raw_cot_data(symbol, cot_data)

                # Step 3: Calculate COT Index
                cot_index = self.calculate_cot_index(symbol)

                if cot_index is None:
                    self.logger.warning(f"⚠️  Skipping {symbol} - COT Index calculation failed")
                    continue

                # Step 4: Classify signal
                trend = self.classify_cot_signal(cot_index)

                # Step 5: Store calculated metrics
                self.store_cot_metrics(symbol, cot_index, trend)

                # Step 6: Generate signal (if extreme)
                signal = self.generate_signal(symbol, cot_index, trend)

                if signal:
                    self.store_signal(signal)

            except Exception as e:
                self.logger.error(f"❌ Error processing {symbol}: {e}")
                continue

        self.logger.info(f"✅ {self.agent_name} completed successfully")

    def store_signal(self, signal: Dict):
        """
        Store generated signal to database

        Args:
            signal: Signal dictionary
        """
        try:
            cursor = self.db_conn.cursor()

            cursor.execute("""
                INSERT INTO agent_signals (
                    agent_id, agent_tier, agent_name, symbol, direction,
                    signal_strength, confidence, factors
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                signal['agent_id'],
                signal['agent_tier'],
                signal['agent_name'],
                signal['symbol'],
                signal['direction'],
                signal['signal_strength'],
                signal['confidence'],
                psycopg2.extras.Json(signal['factors'])
            ))

            self.db_conn.commit()
            cursor.close()

            self.logger.info(f"✅ Stored signal for {signal['symbol']}")

        except Exception as e:
            self.logger.error(f"❌ Error storing signal: {e}")
            self.db_conn.rollback()

    def __del__(self):
        """Cleanup database connection"""
        if self.db_conn:
            self.db_conn.close()
