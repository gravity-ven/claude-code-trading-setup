"""
Risk Agent Base Class - Tier 4 (Agents 81-100)

Base class for risk management and trade sheet generation agents.
These agents handle position sizing, risk management, and output generation.
"""

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Dict, Optional, List


class RiskAgentBase:
    """
    Base class for risk/trade sheet agents (Tier 4, Agents 81-100)

    Responsibilities:
    - Position sizing calculations
    - Risk management (max drawdown, stop losses)
    - Trade sheet generation (text, HTML, JSON)
    - Portfolio allocation
    """

    def __init__(self, agent_id: int, agent_name: str):
        """
        Initialize Risk Agent

        Args:
            agent_id: Unique agent ID (81-100)
            agent_name: Human-readable agent name
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.agent_tier = "TIER4_RISK"

        # Logger (initialize first)
        self.logger = logging.getLogger(f"Agent{agent_id}")

        # Database connection
        self.db_conn = None
        self.connect_to_database()

        # Risk parameters (defaults - can be overridden)
        self.MAX_POSITION_SIZE = 5.0  # Max 5% per position
        self.MAX_PORTFOLIO_RISK = 15.0  # Max 15% total portfolio risk
        self.DEFAULT_RISK_PER_TRADE = 1.0  # Risk 1% per trade

        self.logger.info(f"Initialized {self.agent_name}")

    def connect_to_database(self):
        """Connect to PostgreSQL database"""
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

    def get_top_opportunities(self, limit: int = 10) -> List[Dict]:
        """
        Retrieve top-ranked opportunities from confluence scores

        Args:
            limit: Max number of opportunities to return

        Returns:
            List of top opportunities
        """
        try:
            cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT
                    cs.*,
                    cm.cot_index,
                    cm.cot_trend
                FROM confluence_scores cs
                LEFT JOIN cot_calculated_metrics cm ON cs.symbol = cm.symbol
                WHERE cs.score_date >= CURRENT_DATE - INTERVAL '1 day'
                  AND cs.total_score >= 70
                ORDER BY cs.total_score DESC
                LIMIT %s
            """, (limit,))

            opportunities = cursor.fetchall()
            cursor.close()

            return list(opportunities)

        except Exception as e:
            self.logger.error(f"❌ Error fetching opportunities: {e}")
            return []

    def calculate_position_size(self, opportunity: Dict, account_size: float = 100000) -> float:
        """
        Calculate position size based on risk management rules

        Args:
            opportunity: Opportunity dict with score and direction
            account_size: Total account size (default $100k)

        Returns:
            Position size as % of portfolio
        """
        # Base position size on score
        base_size = (opportunity['total_score'] / 100) * self.MAX_POSITION_SIZE

        # Adjust for risk
        risk_adjusted_size = min(base_size, self.MAX_POSITION_SIZE)

        return round(risk_adjusted_size, 2)

    def generate_trade_sheet_text(self, date: datetime.date, opportunities: List[Dict]) -> str:
        """
        Generate plain text trade sheet

        Args:
            date: Sheet date
            opportunities: List of trade opportunities

        Returns:
            Formatted text trade sheet
        """
        lines = []

        # Header
        lines.append("=" * 70)
        lines.append("        SPARTAN 100 AGENT SYSTEM - DAILY TRADE SHEET")
        lines.append(f"                    {date.strftime('%B %d, %Y')}")
        lines.append("=" * 70)
        lines.append("")

        # Market context
        lines.append("MARKET CONTEXT")
        lines.append("-" * 70)
        lines.append(f"  Presidential Cycle: Year {self.get_presidential_cycle_year()}")
        lines.append(f"  COT Breadth: {self.calculate_cot_breadth()}% (Risk-{'On' if self.calculate_cot_breadth() > 0 else 'Off'})")
        lines.append("")

        # Top longs
        longs = [o for o in opportunities if o['consensus_direction'] == 'LONG']
        if longs:
            lines.append("TOP LONG OPPORTUNITIES")
            lines.append("-" * 70)
            for idx, opp in enumerate(longs[:5], 1):
                lines.append(f"#{idx}  {opp['symbol']}")
                lines.append(f"    Score:  {opp['total_score']}/100   Direction: {opp['consensus_direction']}")
                lines.append(f"    COT Index: {opp.get('cot_index', 'N/A')}% ({opp.get('cot_trend', 'N/A')})")
                lines.append(f"    Position: {self.calculate_position_size(opp)}% portfolio")
                lines.append("")

        # Top shorts
        shorts = [o for o in opportunities if o['consensus_direction'] == 'SHORT']
        if shorts:
            lines.append("TOP SHORT OPPORTUNITIES")
            lines.append("-" * 70)
            for idx, opp in enumerate(shorts[:5], 1):
                lines.append(f"#{idx}  {opp['symbol']}")
                lines.append(f"    Score:  {opp['total_score']}/100   Direction: {opp['consensus_direction']}")
                lines.append(f"    COT Index: {opp.get('cot_index', 'N/A')}% ({opp.get('cot_trend', 'N/A')})")
                lines.append(f"    Position: {self.calculate_position_size(opp)}% portfolio")
                lines.append("")

        # Footer
        lines.append("=" * 70)
        lines.append("Source: CFTC.gov (100% Real Data) + Historical Seasonality")
        lines.append("=" * 70)

        return "\n".join(lines)

    def get_presidential_cycle_year(self) -> int:
        """Get current presidential cycle year (1-4)"""
        current_year = datetime.now().year
        years_since_last_election = (current_year - 2024) % 4
        return years_since_last_election + 1

    def calculate_cot_breadth(self) -> int:
        """Calculate % of markets with bullish COT (>75% COT Index)"""
        try:
            cursor = self.db_conn.cursor()

            cursor.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE cot_index > 75) * 100 / COUNT(*) AS breadth_pct
                FROM cot_calculated_metrics
                WHERE calculation_date >= CURRENT_DATE - INTERVAL '7 days'
            """)

            result = cursor.fetchone()
            cursor.close()

            return result[0] if result and result[0] else 0

        except Exception as e:
            self.logger.error(f"❌ Error calculating COT breadth: {e}")
            return 0

    def store_trade_sheet(self, sheet_date: datetime.date, sheet_text: str):
        """
        Store trade sheet to database

        Args:
            sheet_date: Date of trade sheet
            sheet_text: Generated text content
        """
        try:
            cursor = self.db_conn.cursor()

            cursor.execute("""
                INSERT INTO trade_sheets (
                    sheet_date, sheet_text, generated_by_agent
                )
                VALUES (%s, %s, %s)
                ON CONFLICT (sheet_date)
                DO UPDATE SET
                    sheet_text = EXCLUDED.sheet_text,
                    generated_by_agent = EXCLUDED.generated_by_agent,
                    generation_time = NOW()
            """, (sheet_date, sheet_text, self.agent_id))

            self.db_conn.commit()
            cursor.close()

            self.logger.info(f"✅ Stored trade sheet for {sheet_date}")

        except Exception as e:
            self.logger.error(f"❌ Error storing trade sheet: {e}")
            self.db_conn.rollback()

    def run(self):
        """Main execution loop - override in subclasses"""
        raise NotImplementedError("Subclass must implement run() method")

    def __del__(self):
        """Cleanup database connection"""
        if self.db_conn:
            self.db_conn.close()
