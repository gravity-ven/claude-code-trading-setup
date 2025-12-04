#!/usr/bin/env python3
"""
Spartan 100 Autonomous COT Stock Research Agents
Main orchestrator script

Runs 100 autonomous agents organized in 4 tiers:
- Tier 1 (1-30):   COT Index calculation and analysis
- Tier 2 (31-55):  Seasonality and cycle analysis
- Tier 3 (56-80):  Confluence models and signal aggregation
- Tier 4 (81-100): Risk management and trade sheet generation

Usage:
    python3 run_100_agents.py              # Run continuously
    python3 run_100_agents.py --single-cycle    # Run once
    python3 run_100_agents.py --demo            # Demo mode (quick test)
"""

import os
import sys
import time
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Add agents directory to path
sys.path.insert(0, str(Path(__file__).parent / 'agents' / 'cot_agents'))

from base.cot_agent_base import COTAgentBase
from base.seasonal_agent_base import SeasonalAgentBase
from base.model_agent_base import ModelAgentBase
from base.risk_agent_base import RiskAgentBase

# Configure logging
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'agents.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('Orchestrator')


class AgentOrchestrator:
    """
    Orchestrates all 100 COT research agents

    Coordinates execution across 4 tiers with proper sequencing
    """

    def __init__(self, demo_mode: bool = False):
        """
        Initialize orchestrator

        Args:
            demo_mode: If True, runs minimal agents for quick testing
        """
        self.demo_mode = demo_mode
        self.agents = {
            'tier1': [],  # COT agents (1-30)
            'tier2': [],  # Seasonal agents (31-55)
            'tier3': [],  # Model agents (56-80)
            'tier4': []   # Risk agents (81-100)
        }

        # Output directories
        self.output_dir = Path(__file__).parent / 'output'
        self.output_dir.mkdir(exist_ok=True)

        logger.info("🚀 Initializing Spartan 100 Agent System")
        self.initialize_agents()

    def initialize_agents(self):
        """Initialize all 100 agents (or subset in demo mode)"""

        if self.demo_mode:
            logger.info("📊 DEMO MODE: Initializing minimal agent subset")
            self.initialize_demo_agents()
        else:
            logger.info("📊 Initializing all 100 agents...")
            self.initialize_all_agents()

        logger.info(f"✅ Initialized {self.get_agent_count()} agents")

    def initialize_demo_agents(self):
        """Initialize minimal agents for demo/testing (1 per tier)"""

        # Tier 1: 1 COT agent for Gold
        class GoldCOTAgent(COTAgentBase):
            def __init__(self):
                super().__init__(agent_id=1, agent_name="Gold_COT_Agent", symbols=['GC'])

        self.agents['tier1'].append(GoldCOTAgent())

        # Tier 2: 1 Seasonal agent
        class MonthlySeasonalAgent(SeasonalAgentBase):
            def __init__(self):
                super().__init__(agent_id=31, agent_name="Monthly_Seasonal_Agent", pattern_type="MONTHLY")

            def run(self):
                self.logger.info(f"🚀 {self.agent_name} analyzing monthly patterns...")
                # Demo: Just log, no actual analysis
                self.logger.info(f"✅ {self.agent_name} completed (demo mode)")

        self.agents['tier2'].append(MonthlySeasonalAgent())

        # Tier 3: 1 Model agent
        class ConfluenceModelAgent(ModelAgentBase):
            def __init__(self):
                super().__init__(agent_id=56, agent_name="Confluence_Model_Agent")

            def run(self):
                self.logger.info(f"🚀 {self.agent_name} calculating confluence scores...")

                # Get top symbols (demo: just use common ones)
                symbols = ['GC', 'SI', 'CL', 'ES', 'EUR']

                for symbol in symbols:
                    score = self.calculate_confluence_score(symbol)
                    if score:
                        self.store_confluence_score(score)

                self.logger.info(f"✅ {self.agent_name} completed")

        self.agents['tier3'].append(ConfluenceModelAgent())

        # Tier 4: 1 Risk agent (trade sheet generator)
        class TradeSheetAgent(RiskAgentBase):
            def __init__(self):
                super().__init__(agent_id=81, agent_name="Trade_Sheet_Generator")

            def run(self):
                self.logger.info(f"🚀 {self.agent_name} generating trade sheet...")

                # Get top opportunities
                opportunities = self.get_top_opportunities(limit=10)

                if opportunities:
                    # Generate trade sheet
                    sheet_date = datetime.now().date()
                    sheet_text = self.generate_trade_sheet_text(sheet_date, opportunities)

                    # Store to database
                    self.store_trade_sheet(sheet_date, sheet_text)

                    # Save to file
                    output_file = Path(__file__).parent / 'output' / 'latest_trade_sheet.txt'
                    output_file.write_text(sheet_text)

                    self.logger.info(f"✅ Trade sheet saved to {output_file}")
                else:
                    self.logger.warning("⚠️  No opportunities found for trade sheet")

                self.logger.info(f"✅ {self.agent_name} completed")

        self.agents['tier4'].append(TradeSheetAgent())

    def initialize_all_agents(self):
        """Initialize all 100 agents (full production mode)"""

        # TODO: Implement full 100-agent initialization
        # For now, use demo agents as placeholder
        logger.warning("⚠️  Full 100-agent initialization not yet implemented - using demo mode")
        self.initialize_demo_agents()

    def get_agent_count(self) -> int:
        """Get total number of initialized agents"""
        return sum(len(tier) for tier in self.agents.values())

    def run_single_cycle(self):
        """
        Run all agents once (single cycle)

        Execution order:
        1. Tier 1 (COT) - Fetch and analyze COT data
        2. Tier 2 (Seasonal) - Analyze seasonality patterns
        3. Tier 3 (Models) - Calculate confluence scores
        4. Tier 4 (Risk) - Generate trade sheets
        """
        logger.info("=" * 70)
        logger.info("🚀 STARTING SINGLE CYCLE")
        logger.info("=" * 70)

        start_time = time.time()

        # Run Tier 1: COT Agents
        logger.info("\n📊 TIER 1: COT Analysis (Agents 1-30)")
        logger.info("-" * 70)
        for agent in self.agents['tier1']:
            try:
                agent.run()
            except Exception as e:
                logger.error(f"❌ {agent.agent_name} failed: {e}")

        # Run Tier 2: Seasonal Agents
        logger.info("\n📅 TIER 2: Seasonality Analysis (Agents 31-55)")
        logger.info("-" * 70)
        for agent in self.agents['tier2']:
            try:
                agent.run()
            except Exception as e:
                logger.error(f"❌ {agent.agent_name} failed: {e}")

        # Run Tier 3: Model Agents
        logger.info("\n🎯 TIER 3: Confluence Models (Agents 56-80)")
        logger.info("-" * 70)
        for agent in self.agents['tier3']:
            try:
                agent.run()
            except Exception as e:
                logger.error(f"❌ {agent.agent_name} failed: {e}")

        # Run Tier 4: Risk Agents
        logger.info("\n💰 TIER 4: Risk Management & Trade Sheets (Agents 81-100)")
        logger.info("-" * 70)
        for agent in self.agents['tier4']:
            try:
                agent.run()
            except Exception as e:
                logger.error(f"❌ {agent.agent_name} failed: {e}")

        elapsed = time.time() - start_time

        logger.info("=" * 70)
        logger.info(f"✅ CYCLE COMPLETED in {elapsed:.2f} seconds")
        logger.info("=" * 70)

    def run_continuously(self, interval_hours: int = 1):
        """
        Run agents continuously on a schedule

        Args:
            interval_hours: Hours between cycles (default 1 hour)
        """
        logger.info(f"🔄 Running continuously (every {interval_hours} hour(s))")
        logger.info("Press Ctrl+C to stop")

        try:
            while True:
                self.run_single_cycle()

                # Wait until next cycle
                next_run = datetime.now() + timedelta(hours=interval_hours)
                logger.info(f"⏰ Next cycle at {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

                time.sleep(interval_hours * 3600)

        except KeyboardInterrupt:
            logger.info("\n🛑 Stopped by user")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Spartan 100 Autonomous COT Stock Research Agents'
    )
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run in demo mode (minimal agents for quick testing)'
    )
    parser.add_argument(
        '--single-cycle',
        action='store_true',
        help='Run single cycle and exit (default: run continuously)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=1,
        help='Hours between cycles in continuous mode (default: 1)'
    )

    args = parser.parse_args()

    # Initialize orchestrator
    orchestrator = AgentOrchestrator(demo_mode=args.demo)

    # Run based on mode
    if args.single_cycle:
        orchestrator.run_single_cycle()
    else:
        orchestrator.run_continuously(interval_hours=args.interval)


if __name__ == '__main__':
    main()
