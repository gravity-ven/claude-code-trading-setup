#!/usr/bin/env python3
"""
MASTER AGENT ORCHESTRATOR
=========================

Manages all specialized data agents, ensuring each runs continuously
and data is always fresh and genuine.

Agents Managed:
1. Recession Indicators Agent - 7 recession indicators
2. Market Data Agent - Stocks, ETFs, commodities
3. Crypto Intelligence Agent - Bitcoin, Ethereum, on-chain metrics

Each agent runs in its own async task.
Master orchestrator monitors health and restarts failed agents.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from recession_indicators_agent import RecessionIndicatorsAgent
from market_data_agent import MarketDataAgent
from crypto_intelligence_agent import CryptoIntelligenceAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MasterAgentOrchestrator:
    """Orchestrates all data agents"""

    def __init__(self):
        self.agents = {
            'recession': RecessionIndicatorsAgent(),
            'market': MarketDataAgent(),
            'crypto': CryptoIntelligenceAgent()
        }

        self.agent_tasks = {}
        self.restart_count = {}

    async def run_agent_with_restart(self, name: str, agent):
        """Run an agent with automatic restart on failure"""
        self.restart_count[name] = 0

        while True:
            try:
                logger.info(f"🚀 Starting {name} agent...")
                await agent.run_forever()

            except Exception as e:
                self.restart_count[name] += 1
                logger.error(f"❌ {name} agent crashed: {e}")
                logger.info(f"🔄 Restarting {name} agent (restart #{self.restart_count[name]})")

                # Exponential backoff
                wait_time = min(60, 5 * (2 ** min(self.restart_count[name], 5)))
                await asyncio.sleep(wait_time)

    async def run_all_agents(self):
        """Start all agents concurrently"""
        logger.info("=" * 80)
        logger.info("🎯 MASTER AGENT ORCHESTRATOR STARTING")
        logger.info("=" * 80)
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info(f"Agents to start: {len(self.agents)}")
        logger.info("")

        # Create tasks for each agent
        tasks = []
        for name, agent in self.agents.items():
            task = asyncio.create_task(
                self.run_agent_with_restart(name, agent),
                name=f"{name}_agent"
            )
            self.agent_tasks[name] = task
            tasks.append(task)
            logger.info(f"✅ {name.upper()} Agent task created")

        logger.info("")
        logger.info("🔄 All agents running in background...")
        logger.info("=" * 80)

        # Wait for all tasks (they run forever)
        await asyncio.gather(*tasks)

    async def health_check(self):
        """Periodic health check of all agents"""
        while True:
            await asyncio.sleep(300)  # Check every 5 minutes

            logger.info("🏥 HEALTH CHECK")
            for name, task in self.agent_tasks.items():
                if task.done():
                    logger.error(f"❌ {name} agent task is done (should be running)")
                    # Task will be restarted by run_agent_with_restart
                else:
                    logger.info(f"✅ {name} agent: RUNNING")

    async def start(self):
        """Start orchestrator with health monitoring"""
        # Start all agents
        agents_task = asyncio.create_task(self.run_all_agents())

        # Start health monitor
        health_task = asyncio.create_task(self.health_check())

        # Wait for both
        await asyncio.gather(agents_task, health_task)


def main():
    """Main entry point"""
    orchestrator = MasterAgentOrchestrator()

    try:
        asyncio.run(orchestrator.start())
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down Master Agent Orchestrator...")
        sys.exit(0)


if __name__ == '__main__':
    main()
