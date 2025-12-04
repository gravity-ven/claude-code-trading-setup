#!/usr/bin/env python3
"""
Autonomous Agent Orchestrator
==============================

Launches and manages the swarm of autonomous data agents.

Features:
- Launches all Tier 1 critical agents
- Health monitoring and status dashboard
- Automatic restart on failure
- Graceful shutdown
- Performance metrics
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.tier1.market_agents import (
    SPYAgent,
    DollarIndexAgent,
    Treasury10YAgent,
    GoldAgent,
    OilAgent,
    VIXAgent,
    BitcoinAgent,
    EthereumAgent,
    SolanaAgent,
    AUDJPYAgent,
    HYGAgent,
    Treasury3MAgent,
    RecessionCalculatorAgent,
    MarketNarrativeAgent
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Orchestrator")


class AgentOrchestrator:
    """
    Manages the lifecycle of all autonomous agents.

    Responsibilities:
    1. Launch all agents
    2. Monitor health
    3. Restart failed agents
    4. Provide status dashboard
    5. Graceful shutdown
    """

    def __init__(self):
        self.agents = []
        self.agent_tasks = []
        self.running = False
        self.start_time = None

    def create_tier1_agents(self) -> List:
        """Create all Tier 1 critical agents"""
        return [
            # Market Data Agents (yfinance)
            SPYAgent(),              # Agent 1
            DollarIndexAgent(),      # Agent 2
            GoldAgent(),             # Agent 4
            OilAgent(),              # Agent 5
            BitcoinAgent(),          # Agent 7
            EthereumAgent(),         # Agent 8
            SolanaAgent(),           # Agent 9
            AUDJPYAgent(),           # Agent 10
            HYGAgent(),              # Agent 11

            # FRED Data Agents
            Treasury10YAgent(),      # Agent 3
            Treasury3MAgent(),       # Agent 12
            VIXAgent(),              # Agent 6

            # Composite Agents
            RecessionCalculatorAgent(),  # Agent 13
            MarketNarrativeAgent(),      # Agent 14
        ]

    async def launch_agents(self):
        """Launch all agents concurrently"""
        logger.info("🚀 Launching Tier 1 critical agents...")

        # Create agent instances
        self.agents = self.create_tier1_agents()

        # Create tasks for each agent
        self.agent_tasks = [
            asyncio.create_task(agent.run())
            for agent in self.agents
        ]

        logger.info(f"✅ Launched {len(self.agents)} agents")

        # Print agent list
        for i, agent in enumerate(self.agents, 1):
            logger.info(
                f"  {i:2d}. {agent.name:25s} | "
                f"Symbol: {agent.symbol:15s} | "
                f"Source: {agent.source:10s} | "
                f"Interval: {agent.update_interval:4d}s | "
                f"Critical: {'YES' if agent.critical else 'NO'}"
            )

    async def monitor_health(self):
        """Monitor agent health and restart if needed"""
        while self.running:
            try:
                # Check each agent
                failed_agents = []
                for agent in self.agents:
                    if agent.consecutive_failures >= 5:
                        failed_agents.append(agent)

                # Log health summary every 5 minutes
                if int(asyncio.get_event_loop().time()) % 300 == 0:
                    self.print_health_dashboard()

                # Wait before next check
                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"❌ Health monitor error: {e}")
                await asyncio.sleep(60)

    def print_health_dashboard(self):
        """Print health status dashboard"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        uptime_hours = uptime / 3600

        logger.info("=" * 100)
        logger.info(f"📊 AGENT HEALTH DASHBOARD | Uptime: {uptime_hours:.1f} hours")
        logger.info("=" * 100)

        for agent in self.agents:
            status = agent.health_status

            # Status emoji
            if status['consecutive_failures'] == 0:
                status_emoji = "✅"
            elif status['consecutive_failures'] < 3:
                status_emoji = "⚠️ "
            else:
                status_emoji = "❌"

            logger.info(
                f"{status_emoji} {agent.name:25s} | "
                f"Success: {status['success_rate']:.1%} | "
                f"Fetches: {status['successful_fetches']:4d}/{status['total_fetches']:4d} | "
                f"Failures: {status['consecutive_failures']:2d} | "
                f"Last: {status['last_success'] or 'Never'}"
            )

        logger.info("=" * 100)

    async def run(self):
        """Main orchestrator loop"""
        self.running = True
        self.start_time = datetime.utcnow()

        logger.info("=" * 100)
        logger.info("🤖 SPARTAN RESEARCH STATION - AUTONOMOUS AGENT ORCHESTRATOR")
        logger.info("=" * 100)
        logger.info(f"Start Time: {self.start_time.isoformat()}")
        logger.info(f"Mode: Tier 1 Critical Agents (14 agents)")
        logger.info("=" * 100)

        # Launch agents
        await self.launch_agents()

        # Start health monitor
        health_task = asyncio.create_task(self.monitor_health())

        # Wait for all agents
        try:
            await asyncio.gather(*self.agent_tasks, health_task)
        except KeyboardInterrupt:
            logger.info("🛑 Received shutdown signal")
        except Exception as e:
            logger.error(f"❌ Orchestrator error: {e}")

    def shutdown(self):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down agents...")

        self.running = False

        # Stop all agents
        for agent in self.agents:
            agent.stop()

        # Print final health dashboard
        self.print_health_dashboard()

        logger.info("✅ All agents stopped")


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Main entry point"""
    orchestrator = AgentOrchestrator()

    # Handle shutdown signals
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        orchestrator.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run orchestrator
    try:
        await orchestrator.run()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt")
    finally:
        orchestrator.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Exiting...")
