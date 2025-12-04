#!/usr/bin/env python3
"""
AUTONOMOUS COMPOSITE DATA REFRESH AGENT
========================================

Continuously refreshes composite indicators (recession probability, market narrative).
Runs in a loop to ensure these calculated fields are always available.

These fields require active calculation and expire after 15 minutes.
This agent ensures they're refreshed every 10 minutes to maintain availability.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add agents directory to path
sys.path.insert(0, str(Path(__file__).parent / 'tier1'))

from market_agents import RecessionCalculatorAgent, MarketNarrativeAgent


class CompositeDataRefreshAgent:
    """
    Autonomous agent that continuously refreshes composite indicators.
    """

    def __init__(self):
        self.refresh_interval = 600  # 10 minutes (before 15-min TTL expires)
        self.log_path = Path(__file__).parent.parent / 'composite_refresh.log'

    def log(self, message: str):
        """Log with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)

        with open(self.log_path, 'a') as f:
            f.write(log_message + '\n')

    async def refresh_composite_data(self):
        """Refresh both recession probability and market narrative"""
        self.log("=" * 80)
        self.log("🔄 COMPOSITE DATA REFRESH")
        self.log("=" * 80)

        success_count = 0
        failed = []

        # Refresh Recession Probability
        try:
            recession_agent = RecessionCalculatorAgent()
            await recession_agent.initialize()
            recession_data = await recession_agent.fetch_with_retry()

            if recession_data:
                await recession_agent.store_data(recession_data)
                prob = recession_data.get('probability', 'N/A')
                risk = recession_data.get('risk_level', 'N/A')
                self.log(f"✅ Recession Probability: {prob}% ({risk})")
                success_count += 1
            else:
                failed.append("Recession Probability")
                self.log("❌ Recession Probability: fetch failed")

        except Exception as e:
            failed.append("Recession Probability")
            self.log(f"❌ Recession Probability error: {e}")

        # Refresh Market Narrative
        try:
            narrative_agent = MarketNarrativeAgent()
            await narrative_agent.initialize()
            narrative_data = await narrative_agent.fetch_with_retry()

            if narrative_data:
                await narrative_agent.store_data(narrative_data)
                narrative = narrative_data.get('narrative', 'N/A')
                regime = narrative_data.get('regime', 'N/A')
                self.log(f"✅ Market Narrative: {narrative} ({regime})")
                success_count += 1
            else:
                failed.append("Market Narrative")
                self.log("❌ Market Narrative: fetch failed")

        except Exception as e:
            failed.append("Market Narrative")
            self.log(f"❌ Market Narrative error: {e}")

        # Summary
        self.log("")
        self.log(f"📊 Refresh Summary: {success_count}/2 successful")
        if failed:
            self.log(f"   Failed: {', '.join(failed)}")
        else:
            self.log("   🎉 All composite data refreshed successfully")
        self.log("=" * 80)
        self.log("")

        return success_count == 2

    async def run_forever(self):
        """Run refresh loop continuously"""
        self.log("🚀 Composite Data Refresh Agent started")
        self.log(f"   Refresh interval: {self.refresh_interval}s (10 minutes)")
        self.log(f"   Log file: {self.log_path}")
        self.log("")

        while True:
            try:
                await self.refresh_composite_data()
                await asyncio.sleep(self.refresh_interval)

            except KeyboardInterrupt:
                self.log("\n🛑 Composite refresh agent stopped by user")
                break

            except Exception as e:
                self.log(f"❌ Refresh loop error: {e}")
                await asyncio.sleep(60)  # Wait 1 min on error


async def main():
    """Start the autonomous refresh agent"""
    agent = CompositeDataRefreshAgent()
    await agent.run_forever()


if __name__ == '__main__':
    asyncio.run(main())
