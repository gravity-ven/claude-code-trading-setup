#!/usr/bin/env python3
"""
DATA POINT MASTER ORCHESTRATOR
===============================

Master orchestrator for all individual data point agents.
Manages agent lifecycle, health monitoring, and coordination.

Architecture:
- Each data point has its own dedicated agent
- Master orchestrator monitors health and restarts failed agents
- No shared data points between agents
- Each agent is responsible for ONE data point only
- Continuous 24/7 monitoring with auto-healing
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
import signal
import sys
from pathlib import Path
import json
import redis
import psycopg2
from psycopg2.extras import RealDictCursor

# Import all data point agents
from data_points.spy_agent import SPYAgent
from data_points.qqq_agent import QQQAgent
from data_points.btc_usd_agent import BTCUSDAgent
from data_points.vix_agent import VIXAgent
from data_points.treasury_10y_agent import Treasury10YAgent

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataPointMasterOrchestrator:
    """
    Master orchestrator for individual data point agents
    
    Key Responsibilities:
    1. Start all data point agents with dedicated tasks
    2. Monitor individual agent health
    3. Auto-restart failed agents
    4. Provide system-wide health reporting
    5. Coordinate agent lifecycle management
    """

    def __init__(self):
        """Initialize the master orchestrator"""
        self.agents = {}
        self.agent_tasks = {}
        self.restart_counts = {}
        self.system_start_time = datetime.now()
        
        # Database connections for monitoring
        self.redis_client = None
        self.db_conn = None
        
        # Health monitoring
        self.health_check_interval = 60  # seconds
        self.max_restarts_per_hour = 3
        self.last_restart_times = {}
        
        # Initialize connections
        self._initialize_connections()
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _initialize_connections(self):
        """Initialize Redis and PostgreSQL connections for monitoring"""
        try:
            # Redis connection
            import os
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=0,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            self.redis_client.ping()
            logger.info("✅ Master Orchestrator connected to Redis")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.redis_client = None

        try:
            import os
            db_url = os.getenv(
                'DATABASE_URL',
                'postgresql://spartan:spartan@localhost:5432/spartan_research_db'
            )
            self.db_conn = psycopg2.connect(db_url)
            self.db_conn.autocommit = True
            logger.info("✅ Master Orchestrator connected to PostgreSQL")
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed: {e}")
            self.db_conn = None

    def register_agent(self, agent):
        """Register a data point agent with the orchestrator"""
        agent_id = agent.agent_id
        self.agents[agent_id] = agent
        self.restart_counts[agent_id] = 0
        self.last_restart_times[agent_id] = []
        
        logger.info(f"📝 Registered agent: {agent_id} for {agent.data_point}")

    async def run_agent_with_restart(self, agent_id: str):
        """
        Run an agent with automatic restart on failure
        Implements exponential backoff and restart limits
        """
        agent = self.agents[agent_id]
        restart_delay = 30  # Start with 30 seconds
        max_delay = 300  # Maximum 5 minutes between restarts

        while True:
            try:
                logger.info(f"🚀 Starting {agent_id}...")
                
                # Check restart rate limiting
                if self._is_restart_limited(agent_id):
                    wait_time = 3600  # Wait 1 hour if restart limited
                    logger.error(f"❌ {agent_id} restart limited - waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                    # Reset restart count after waiting
                    self.last_restart_times[agent_id] = []
                    self.restart_counts[agent_id] = 0

                # Run the agent
                await agent.start()

            except Exception as e:
                # Record restart
                restart_time = datetime.now()
                self.restart_counts[agent_id] += 1
                self.last_restart_times[agent_id].append(restart_time)
                
                # Clean up old restart times (keep only last hour)
                one_hour_ago = restart_time.timestamp() - 3600
                self.last_restart_times[agent_id] = [
                    rt for rt in self.last_restart_times[agent_id]
                    if rt.timestamp() > one_hour_ago
                ]
                
                logger.error(f"❌ {agent_id} crashed: {e}")
                logger.error(f"🔄 Restart #{self.restart_counts[agent_id]} for {agent_id}")
                
                # Exponential backoff
                actual_delay = min(restart_delay, max_delay)
                logger.info(f"🔄 Restarting {agent_id} in {actual_delay}s...")
                await asyncio.sleep(actual_delay)
                
                # Increase delay for next restart
                restart_delay = min(restart_delay * 1.5, max_delay)

    def _is_restart_limited(self, agent_id: str) -> bool:
        """Check if an agent is hitting restart rate limits"""
        recent_restarts = len(self.last_restart_times[agent_id])
        return recent_restarts >= self.max_restarts_per_hour

    async def start_all_agents(self):
        """Start all registered agents concurrently"""
        logger.info("=" * 80)
        logger.info("🎯 DATA POINT MASTER ORCHESTRATOR STARTING")
        logger.info("=" * 80)
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info(f"Total agents to start: {len(self.agents)}")
        logger.info("")

        # Create tasks for each agent
        tasks = []
        for agent_id, agent in self.agents.items():
            task = asyncio.create_task(
                self.run_agent_with_restart(agent_id),
                name=f"agent_{agent_id}"
            )
            self.agent_tasks[agent_id] = task
            tasks.append(task)
            
            data_type = agent.data_type.upper()
            logger.info(f"✅ {agent_id.upper()} Agent ({data_type}): {agent.data_point}")

        logger.info("")
        logger.info("🔄 All data point agents running in background...")
        logger.info("=" * 80)

        # Wait for all tasks (they run forever)
        await asyncio.gather(*tasks)

    async def health_monitor(self):
        """Periodic health monitoring for all agents"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                logger.info("🏥 Data Point Agents Health Check")
                
                system_health = await self.get_system_health()
                
                # Log health status for each agent
                healthy_count = 0
                critical_count = 0
                
                for agent_id, health in system_health['agents'].items():
                    status = health['health_status']
                    failures = health['consecutive_failures']
                    
                    if status == 'HEALTHY':
                        healthy_count += 1
                        logger.info(f"✅ {agent_id}: {status}")
                    elif status == 'WARNING':
                        logger.warning(f"⚠️  {agent_id}: {status} ({failures} failures)")
                    else:  # CRITICAL or FAILED
                        critical_count += 1
                        logger.error(f"❌ {agent_id}: {status} ({failures} failures)")
                
                # System-wide summary
                total_agents = len(self.agents)
                system_uptime = system_health['system_uptime_minutes']
                success_rate = system_health['overall_success_rate']
                
                logger.info(f"📊 System Health: {healthy_count}/{total_agents} healthy ({(healthy_count/total_agents)*100:.1f}%)")
                logger.info(f"📊 System Success Rate: {success_rate:.1f}%")
                logger.info(f"📊 System Uptime: {system_uptime:.0f} minutes")
                
                if critical_count > 0:
                    logger.error(f"🚨 {critical_count} agents in CRITICAL state")
                    
                logger.info("-" * 60)
                
                # Store health metrics in Redis for dashboard
                await self._store_health_metrics(system_health)
                
            except Exception as e:
                logger.error(f"❌ Health monitor error: {e}")

    async def get_system_health(self) -> Dict:
        """Get comprehensive system health status"""
        agents_health = {}
        
        total_fetches = 0
        total_successes = 0
        total_failures = 0
        
        for agent_id, agent in self.agents.items():
            health = agent.get_health_status()
            agents_health[agent_id] = health
            
            total_fetches += health['total_fetches']
            total_successes += health['successful_fetches']
            total_failures += health['consecutive_failures']
        
        # Calculate system metrics
        system_uptime_minutes = (datetime.now() - self.system_start_time).total_seconds() / 60
        overall_success_rate = (total_successes / max(1, total_fetches)) * 100
        
        system_health = {
            'system_status': 'HEALTHY' if total_failures == 0 else 'DEGRADED',
            'system_start_time': self.system_start_time.isoformat(),
            'system_uptime_minutes': system_uptime_minutes,
            'total_agents': len(self.agents),
            'overall_success_rate': overall_success_rate,
            'total_fetches': total_fetches,
            'total_successes': total_successes,
            'active_agents': len([a for a in agents_health.values() if a['health_status'] == 'HEALTHY']),
            'critical_agents': len([a for a in agents_health.values() if a['health_status'] in ['CRITICAL', 'FAILED']]),
            'agents': agents_health,
            'last_health_check': datetime.now().isoformat()
        }
        
        return system_health

    async def _store_health_metrics(self, health_data: Dict):
        """Store health metrics in Redis for dashboard access"""
        if not self.redis_client:
            return
            
        try:
            # Store system health summary
            system_key = "orchestrator:system_health"
            self.redis_client.setex(
                system_key,
                300,  # 5 minutes TTL
                json.dumps(health_data)
            )
            
            # Store individual agent health for detailed dashboard
            for agent_id, agent_health in health_data['agents'].items():
                agent_health_key = f"orchestrator:agent_health:{agent_id}"
                self.redis_client.setex(
                    agent_health_key,
                    300,
                    json.dumps(agent_health)
                )
                
        except Exception as e:
            logger.error(f"Failed to store health metrics: {e}")

    async def handle_shutdown(self, signal_name: str):
        """Gracefully shutdown all agents"""
        logger.info(f"\n🛑 Received {signal_name} - Shutting down Data Point Master Orchestrator...")
        
        # Cancel all agent tasks
        for agent_id, task in self.agent_tasks.items():
            if not task.done():
                logger.info(f"🛑 Stopping {agent_id}...")
                task.cancel()
                
                try:
                    # Wait for task to finish with timeout
                    await asyncio.wait_for(task, timeout=10)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    logger.warning(f"⚠️  {agent_id} did not stop gracefully")
        
        # Stop all agents
        for agent_id, agent in self.agents.items():
            try:
                agent.stop()
            except Exception as e:
                logger.error(f"Error stopping {agent_id}: {e}")
        
        # Close connections
        if self.redis_client:
            self.redis_client.close()
        if self.db_conn:
            self.db_conn.close()
            
        logger.info("✅ All agents stopped successfully")
        logger.info("👋 Data Point Master Orchestrator shutdown complete")

    def _signal_handler(self, signum, frame):
        """Signal handler for graceful shutdown"""
        signal_name = 'SIGINT' if signum == signal.SIGINT else 'SIGTERM'
        asyncio.create_task(self.handle_shutdown(signal_name))

    async def start(self):
        """Start the master orchestrator with health monitoring"""
        try:
            # Start all agents
            agents_task = asyncio.create_task(self.start_all_agents())
            
            # Start health monitor
            health_task = asyncio.create_task(self.health_monitor())
            
            # Wait for both tasks
            await asyncio.gather(agents_task, health_task)
            
        except KeyboardInterrupt:
            await self.handle_shutdown('SIGINT')
        except Exception as e:
            logger.error(f"❌ Master orchestrator failed: {e}")
            await self.handle_shutdown('CRASH')


def create_all_agents():
    """Create and register all data point agents"""
    orchestrator = DataPointMasterOrchestrator()
    
    # Register all critical data point agents
    agents_to_register = {
        'spy': SPYAgent(),
        'qqq': QQQAgent(), 
        'btc_usd': BTCUSDAgent(),
        'vix': VIXAgent(),
        'treasury_10y': Treasury10YAgent()
    }
    
    for agent_name, agent in agents_to_register.items():
        orchestrator.register_agent(agent)
    
    logger.info(f"🎯 Registered {len(agents_to_register)} data point agents")
    
    return orchestrator


def main():
    """Main entry point for the data point orchestration system"""
    logger.info("🚀 Starting Data Point Master Orchestrator...")
    logger.info("📊 Each agent manages ONE data point with 24/7 monitoring")
    logger.info("🔄 Auto-healing enabled for all agents")
    
    orchestrator = create_all_agents()
    
    try:
        asyncio.run(orchestrator.start())
    except KeyboardInterrupt:
        logger.info("\n👋 Shutdown requested by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
