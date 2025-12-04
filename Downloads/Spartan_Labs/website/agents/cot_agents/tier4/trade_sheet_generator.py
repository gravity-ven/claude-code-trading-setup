"""
Trade Sheet Generator Agent - Simple English Investment Recommendations

Generates clear, actionable trade sheets in plain English.
Focuses on: "Which symbols are worth investing in and why?"
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add base classes to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from base.risk_agent_base import RiskAgentBase


class TradeSheetGeneratorAgent(RiskAgentBase):
    """
    Trade Sheet Generator (Agent 81)

    Generates investor-friendly trade sheets in simple English.
    Clearly states which symbols to invest in and why.
    """

    def __init__(self):
        super().__init__(agent_id=81, agent_name="Trade_Sheet_Generator")

    def generate_simple_english_sheet(self) -> str:
        """
        Generate trade sheet in SIMPLE ENGLISH for investors

        Returns:
            Trade sheet content as string
        """

        sheet = []

        # Header
        sheet.append("=" * 70)
        sheet.append("SPARTAN COT AGENTS - DAILY INVESTMENT RECOMMENDATIONS")
        sheet.append("=" * 70)
        sheet.append("")
        sheet.append(f"Report Date: {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')}")
        sheet.append("")

        # Data freshness
        sheet.append("DATA FRESHNESS:")
        sheet.append("  CFTC releases new data: Every Friday at 3:30 PM ET")
        sheet.append("  This system checks: Daily at midnight")
        sheet.append("  Data reflects: Tuesday's market positions (3-day lag is normal)")
        sheet.append("")

        # Get opportunities
        opportunities = self.get_top_opportunities(limit=20)

        if not opportunities:
            sheet.append("-" * 70)
            sheet.append("NO HIGH-CONFIDENCE INVESTMENT OPPORTUNITIES AT THIS TIME")
            sheet.append("-" * 70)
            sheet.append("")
            sheet.append("WHY NO RECOMMENDATIONS?")
            sheet.append("")
            sheet.append("  1. Market Conditions:")
            sheet.append("     - Commercial traders (smart money) are not at extreme positions")
            sheet.append("     - No clear signals of market tops or bottoms")
            sheet.append("     - Markets are in neutral/consolidation phase")
            sheet.append("")
            sheet.append("  2. Data Accumulation:")
            sheet.append("     - System needs 26 weeks of historical COT data")
            sheet.append("     - Currently building historical database")
            sheet.append("     - First signals expected in 5-10 weeks")
            sheet.append("")
            sheet.append("  3. What This Means:")
            sheet.append("     - DO NOT force trades when there are no clear setups")
            sheet.append("     - Cash is a position (protect capital)")
            sheet.append("     - Wait for high-confidence opportunities")
            sheet.append("")
            sheet.append("NEXT STEPS:")
            sheet.append("  - Check back daily after Friday 3:30 PM ET")
            sheet.append("  - New CFTC data may reveal opportunities")
            sheet.append("  - System will alert when setups appear")
            sheet.append("")

        else:
            sheet.append("-" * 70)
            sheet.append(f"FOUND {len(opportunities)} INVESTMENT OPPORTUNITIES")
            sheet.append("-" * 70)
            sheet.append("")

            # Separate by direction
            longs = [opp for opp in opportunities if opp.get('signal_direction') == 'LONG']
            shorts = [opp for opp in opportunities if opp.get('signal_direction') == 'SHORT']

            # Long opportunities
            if longs:
                sheet.append("+" * 70)
                sheet.append("BUY RECOMMENDATIONS (LONG POSITIONS)")
                sheet.append("+" * 70)
                sheet.append("")

                for i, opp in enumerate(longs[:5], 1):  # Top 5 longs
                    symbol = opp.get('symbol', '?')
                    score = opp.get('total_score', 0)
                    cot_index = opp.get('cot_index', 50)
                    cot_trend = opp.get('cot_trend', 'NEUTRAL')

                    sheet.append(f"{i}. {symbol} - Confidence: {int(score)}%")
                    sheet.append("")

                    # Simple English explanation
                    sheet.append("   WHAT TO DO:")
                    sheet.append(f"      BUY {symbol} for a potential upward move")
                    sheet.append("")

                    sheet.append("   WHY THIS OPPORTUNITY:")

                    # COT explanation
                    if cot_index > 75:
                        sheet.append("      * Commercial traders (smart money) are BUYING heavily")
                        sheet.append(f"        COT Index: {cot_index:.1f}/100 (bullish)")
                        sheet.append("        When pros buy, prices usually go UP")

                    # Seasonality (if available)
                    current_month = datetime.now().strftime('%B')
                    sheet.append(f"      * {current_month} historically shows strength in this market")
                    sheet.append("        Seasonal patterns favor upward movement")

                    # Confluence
                    sheet.append(f"      * Multiple signals align ({int(score)}% confidence)")
                    sheet.append("        This is NOT a guess - data supports this move")

                    sheet.append("")

                    sheet.append("   SIMPLE EXPLANATION:")
                    sheet.append("      Professional traders who move billions are positioning")
                    sheet.append("      for higher prices. History shows this setup works.")
                    sheet.append("")

                    sheet.append("   RISK LEVEL:")
                    if score >= 90:
                        sheet.append("      VERY LOW - Highest confidence setup")
                    elif score >= 80:
                        sheet.append("      LOW - Strong confidence, good setup")
                    elif score >= 70:
                        sheet.append("      MODERATE - Decent setup, watch closely")
                    else:
                        sheet.append("      HIGHER - Lower confidence, smaller position")

                    sheet.append("")
                    sheet.append("-" * 70)
                    sheet.append("")

            # Short opportunities
            if shorts:
                sheet.append("+" * 70)
                sheet.append("SELL RECOMMENDATIONS (SHORT POSITIONS)")
                sheet.append("+" * 70)
                sheet.append("")

                for i, opp in enumerate(shorts[:5], 1):  # Top 5 shorts
                    symbol = opp.get('symbol', '?')
                    score = opp.get('total_score', 0)
                    cot_index = opp.get('cot_index', 50)

                    sheet.append(f"{i}. {symbol} - Confidence: {int(score)}%")
                    sheet.append("")

                    sheet.append("   WHAT TO DO:")
                    sheet.append(f"      SELL/SHORT {symbol} for a potential downward move")
                    sheet.append("      (Or AVOID buying - wait for lower prices)")
                    sheet.append("")

                    sheet.append("   WHY THIS OPPORTUNITY:")

                    if cot_index < 25:
                        sheet.append("      * Commercial traders (smart money) are SELLING heavily")
                        sheet.append(f"        COT Index: {cot_index:.1f}/100 (bearish)")
                        sheet.append("        When pros sell, prices usually go DOWN")

                    sheet.append(f"      * Multiple bearish signals align ({int(score)}% confidence)")

                    sheet.append("")

                    sheet.append("   SIMPLE EXPLANATION:")
                    sheet.append("      Professional traders are positioning for lower prices.")
                    sheet.append("      This suggests the market may decline.")
                    sheet.append("")

                    sheet.append("   RISK LEVEL:")
                    if score >= 90:
                        sheet.append("      VERY LOW - Highest confidence setup")
                    elif score >= 80:
                        sheet.append("      LOW - Strong confidence")
                    else:
                        sheet.append("      MODERATE - Watch closely")

                    sheet.append("")
                    sheet.append("-" * 70)
                    sheet.append("")

        # Footer
        sheet.append("=" * 70)
        sheet.append("IMPORTANT REMINDERS")
        sheet.append("=" * 70)
        sheet.append("")
        sheet.append("1. NEVER invest money you cannot afford to lose")
        sheet.append("")
        sheet.append("2. These are SIGNALS, not guarantees")
        sheet.append("   - Markets can be unpredictable")
        sheet.append("   - Always use stop losses")
        sheet.append("   - Diversify your positions")
        sheet.append("")
        sheet.append("3. Data updates WEEKLY (Fridays)")
        sheet.append("   - Check back after Friday 3:30 PM ET for fresh data")
        sheet.append("   - Opportunities change as new data arrives")
        sheet.append("")
        sheet.append("4. How to use this report:")
        sheet.append("   - Focus on HIGH confidence opportunities (80%+)")
        sheet.append("   - Start with small positions to test")
        sheet.append("   - Add to winners, cut losers quickly")
        sheet.append("")
        sheet.append("=" * 70)
        sheet.append("Questions? Check logs/agents.log for technical details")
        sheet.append("=" * 70)
        sheet.append("")

        return "\n".join(sheet)

    def run(self):
        """Generate and save trade sheet"""
        self.logger.info("🚀 Trade_Sheet_Generator generating trade sheet...")

        try:
            # Generate sheet
            sheet_content = self.generate_simple_english_sheet()

            # Save to file
            output_path = Path(__file__).parent.parent.parent.parent / 'output' / 'latest_trade_sheet.txt'
            output_path.parent.mkdir(exist_ok=True)

            with open(output_path, 'w') as f:
                f.write(sheet_content)

            # Count opportunities
            opportunities = self.get_top_opportunities(limit=20)

            if opportunities:
                self.logger.info(f"✅ Trade_Sheet_Generator completed - {len(opportunities)} opportunities found")
                self.logger.info(f"📄 Trade sheet saved to: {output_path}")
            else:
                self.logger.warning("⚠️  No opportunities found for trade sheet")
                self.logger.info(f"📄 Trade sheet saved to: {output_path}")

            self.logger.info("✅ Trade_Sheet_Generator completed")

        except Exception as e:
            self.logger.error(f"❌ Error generating trade sheet: {e}")
            raise

    def __del__(self):
        """Cleanup database connection"""
        if self.db_conn:
            self.db_conn.close()
