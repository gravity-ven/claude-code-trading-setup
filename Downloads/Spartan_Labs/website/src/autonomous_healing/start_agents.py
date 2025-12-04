#!/usr/bin/env python3
"""
SPARTAN LABS - AUTONOMOUS HEALING SYSTEM STARTUP
=================================================

Main entry point to start all AI agents for autonomous error detection
and self-healing.

Usage:
    python3 start_agents.py [--config CONFIG_FILE]

Author: Spartan Labs
Version: 1.0.0
"""

import asyncio
import argparse
import sys
import signal
import yaml
import logging
from pathlib import Path
from datetime import datetime

from ai_agents import AgentOrchestrator
from error_monitor import ErrorDetectionEngine
from healing_engine import AutonomousHealingEngine
from alert_system import AlertManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('/mnt/c/Users/Quantum/Downloads/Spartan_Labs/website/logs/autonomous_healing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AutonomousHealingSystem:
    """Main system controller."""

    def __init__(self, config_path: str = 'config/healing_config.yaml'):
        self.config_path = config_path
        self.config = None
        self.orchestrator = None
        self.is_running = False

    def load_config(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"✅ Configuration loaded from {self.config_path}")
        except FileNotFoundError:
            logger.error(f"❌ Config file not found: {self.config_path}")
            logger.info("Creating default configuration...")
            self.create_default_config()
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)

    def create_default_config(self):
        """Create default configuration file."""
        default_config = {
            'database': {
                'dbname': 'spartan_research_db',
                'user': 'spartan_user',
                'password': 'secure_password',
                'host': 'localhost',
                'port': 5432
            },
            'monitoring': {
                'check_interval': 30,
                'enable_predictive_failures': True,
                'endpoints': [
                    {
                        'source': 'yahoo_finance',
                        'endpoint': '/quote',
                        'url': 'http://localhost:5002/api/yahoo/quote',
                        'priority': 'high',
                        'timeout': 10.0,
                        'check_interval': 60
                    },
                    {
                        'source': 'fred_api',
                        'endpoint': '/series',
                        'url': 'http://localhost:5002/api/fred/series',
                        'priority': 'high',
                        'timeout': 10.0,
                        'check_interval': 300
                    },
                    {
                        'source': 'polygon_io',
                        'endpoint': '/v2/aggs',
                        'url': 'http://localhost:5002/api/polygon/aggs',
                        'priority': 'medium',
                        'timeout': 5.0,
                        'check_interval': 120
                    }
                ]
            },
            'healing': {
                'enable_auto_healing': True,
                'max_retry_attempts': 3,
                'exponential_backoff_base': 1.0,
                'cache_ttl_seconds': 900,
                'enable_fallback_chains': True
            },
            'learning': {
                'enable_nested_learning': True,
                'outer_layer_update_interval': 86400,  # 24 hours
                'inner_layer_update_interval': 3600,   # 1 hour
                'min_samples_for_learning': 10,
                'confidence_threshold': 0.80
            },
            'alerts': {
                'enable_web_ui': True,
                'enable_email': False,
                'enable_sms': False,
                'email': {
                    'smtp_host': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'from_email': 'alerts@spartanlabs.com',
                    'recipients': ['admin@spartanlabs.com']
                },
                'sms': {
                    'provider': 'twilio',
                    'account_sid': '',
                    'auth_token': '',
                    'recipients': []
                },
                'websocket_url': 'ws://localhost:8888/ws/health'
            }
        }

        # Create config directory if needed
        Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)

        logger.info(f"✅ Default configuration created at {self.config_path}")

    async def start(self):
        """Start autonomous healing system."""
        logger.info("=" * 80)
        logger.info("SPARTAN LABS - AUTONOMOUS HEALING SYSTEM")
        logger.info("=" * 80)
        logger.info(f"Starting at: {datetime.now().isoformat()}")
        logger.info("")

        # Load configuration
        self.load_config()

        # Validate database connection
        logger.info("🔍 Validating database connection...")
        db_config = self.config['database']

        try:
            import psycopg2
            conn = psycopg2.connect(**db_config)
            conn.close()
            logger.info("✅ Database connection successful")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            logger.error("Please ensure PostgreSQL is running and configuration is correct")
            return

        # Initialize components
        logger.info("🔧 Initializing system components...")

        self.orchestrator = AgentOrchestrator(db_config)

        # Start orchestrator
        logger.info("🚀 Starting Agent Orchestrator...")
        await self.orchestrator.start()

        self.is_running = True

        logger.info("")
        logger.info("✅ AUTONOMOUS HEALING SYSTEM OPERATIONAL")
        logger.info("")
        logger.info("System Status:")
        logger.info(f"  - Monitoring Agent: ACTIVE")
        logger.info(f"  - Diagnosis Agent: ACTIVE")
        logger.info(f"  - Healing Coordinator: ACTIVE")
        logger.info(f"  - Learning Agent: ACTIVE")
        logger.info("")
        logger.info(f"Monitoring {len(self.config['monitoring']['endpoints'])} endpoints")
        logger.info(f"Check interval: {self.config['monitoring']['check_interval']}s")
        logger.info("")
        logger.info("Dashboard: http://localhost:8888/health-dashboard")
        logger.info("Logs: /logs/autonomous_healing.log")
        logger.info("")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 80)

        # Run indefinitely
        try:
            while self.is_running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Shutdown signal received")

    async def stop(self):
        """Stop autonomous healing system gracefully."""
        logger.info("")
        logger.info("🛑 Stopping Autonomous Healing System...")

        self.is_running = False

        if self.orchestrator:
            await self.orchestrator.stop()

        logger.info("✅ System stopped gracefully")
        logger.info(f"Stopped at: {datetime.now().isoformat()}")


# Global system instance for signal handling
system_instance = None


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {sig}")
    if system_instance:
        asyncio.create_task(system_instance.stop())


async def main():
    """Main entry point."""
    global system_instance

    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Spartan Labs Autonomous Healing System'
    )
    parser.add_argument(
        '--config',
        default='config/healing_config.yaml',
        help='Path to configuration file'
    )
    args = parser.parse_args()

    # Create system instance
    system_instance = AutonomousHealingSystem(config_path=args.config)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start system
    try:
        await system_instance.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await system_instance.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        sys.exit(1)
