#!/usr/bin/env python3
"""
Spartan Labs Website Monitor Agent
Autonomously monitors Docker containers and fixes issues using Claude AI
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import yaml
import aiohttp
import docker
import psycopg2
from psycopg2.extras import RealDictCursor
import structlog
from anthropic import AsyncAnthropic

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class WebsiteMonitorAgent:
    """Autonomous website monitoring agent with self-healing capabilities"""

    def __init__(self, config_path: str = "agents/website_monitor/config.yaml"):
        """Initialize the website monitor agent"""
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.docker_client = docker.from_env()
        self.db_conn = None
        self.claude_client = None
        self.restart_history: Dict[str, List[datetime]] = {}
        self.is_running = False

        # Initialize Claude if enabled
        if self.config["claude"]["enabled"]:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                self.claude_client = AsyncAnthropic(api_key=api_key)
                self.logger.info("claude_initialized", model=self.config["claude"]["model"])
            else:
                self.logger.warning("claude_disabled", reason="no_api_key")

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

    def _setup_logging(self) -> structlog.BoundLogger:
        """Setup structured logging"""
        log_level = self.config["logging"]["level"]

        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.add_log_level,
                structlog.processors.JSONRenderer(),
            ],
            logger_factory=structlog.PrintLoggerFactory(),
        )

        logger = structlog.get_logger()
        return logger

    async def connect_database(self) -> None:
        """Connect to PostgreSQL database for incident tracking"""
        if not self.config["database"]["enabled"]:
            return

        try:
            self.db_conn = psycopg2.connect(
                self.config["database"]["connection_string"]
            )
            self.logger.info("database_connected")
            await self._create_tables()
        except Exception as e:
            self.logger.error("database_connection_failed", error=str(e))

    async def _create_tables(self) -> None:
        """Create database tables if they don't exist"""
        create_incidents_table = """
        CREATE TABLE IF NOT EXISTS monitor_incidents (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            container_name VARCHAR(100) NOT NULL,
            incident_type VARCHAR(50) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            description TEXT,
            auto_healed BOOLEAN DEFAULT FALSE,
            healing_action VARCHAR(100),
            resolution_time_seconds FLOAT,
            metadata JSONB
        );
        """

        create_health_metrics_table = """
        CREATE TABLE IF NOT EXISTS monitor_health_metrics (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            container_name VARCHAR(100) NOT NULL,
            status VARCHAR(20) NOT NULL,
            response_time_ms FLOAT,
            memory_usage_mb FLOAT,
            cpu_percent FLOAT,
            restart_count INT DEFAULT 0
        );
        """

        create_healing_actions_table = """
        CREATE TABLE IF NOT EXISTS monitor_healing_actions (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            container_name VARCHAR(100) NOT NULL,
            action_type VARCHAR(50) NOT NULL,
            success BOOLEAN NOT NULL,
            error_message TEXT,
            claude_reasoning TEXT,
            execution_time_seconds FLOAT
        );
        """

        create_container_stats_table = """
        CREATE TABLE IF NOT EXISTS monitor_container_stats (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            container_name VARCHAR(100) NOT NULL,
            uptime_seconds BIGINT,
            total_restarts INT DEFAULT 0,
            total_incidents INT DEFAULT 0,
            auto_heal_success_rate FLOAT,
            last_health_check TIMESTAMPTZ
        );
        """

        tables = [
            create_incidents_table,
            create_health_metrics_table,
            create_healing_actions_table,
            create_container_stats_table,
        ]

        cursor = self.db_conn.cursor()
        for table_sql in tables:
            cursor.execute(table_sql)
        self.db_conn.commit()
        cursor.close()

        self.logger.info("database_tables_created")

    async def check_container_health(self, container_config: dict) -> Tuple[bool, str, dict]:
        """
        Check health of a single container

        Returns:
            (is_healthy, status_message, metrics)
        """
        container_name = container_config["name"]

        try:
            # Get container from Docker
            container = self.docker_client.containers.get(container_name)

            # Check if container is running
            if container.status != "running":
                return False, f"Container not running (status: {container.status})", {}

            # Get container stats
            stats = container.stats(stream=False)
            memory_usage_mb = stats["memory_stats"].get("usage", 0) / (1024 * 1024)
            cpu_percent = self._calculate_cpu_percent(stats)

            metrics = {
                "memory_usage_mb": memory_usage_mb,
                "cpu_percent": cpu_percent,
                "status": container.status,
            }

            # Check HTTP health endpoint if configured
            if container_config.get("health_endpoint"):
                endpoint = container_config["health_endpoint"]
                is_healthy, response_time = await self._check_http_endpoint(endpoint)

                metrics["response_time_ms"] = response_time

                if not is_healthy:
                    return False, f"Health endpoint failed: {endpoint}", metrics

            # Check Docker health status
            health = container.attrs.get("State", {}).get("Health", {})
            if health:
                docker_health_status = health.get("Status", "none")
                if docker_health_status == "unhealthy":
                    return False, "Docker health check failed", metrics

            return True, "Healthy", metrics

        except docker.errors.NotFound:
            return False, f"Container '{container_name}' not found", {}
        except Exception as e:
            self.logger.error("health_check_failed", container=container_name, error=str(e))
            return False, f"Health check error: {str(e)}", {}

    async def _check_http_endpoint(self, endpoint: str) -> Tuple[bool, float]:
        """Check HTTP endpoint health"""
        start_time = datetime.now()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    endpoint,
                    timeout=aiohttp.ClientTimeout(total=self.config["monitoring"]["health_check_timeout"])
                ) as response:
                    response_time = (datetime.now() - start_time).total_seconds() * 1000
                    return response.status == 200, response_time
        except asyncio.TimeoutError:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            return False, response_time
        except Exception as e:
            self.logger.debug("http_check_failed", endpoint=endpoint, error=str(e))
            return False, 0.0

    def _calculate_cpu_percent(self, stats: dict) -> float:
        """Calculate CPU usage percentage from Docker stats"""
        try:
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                       stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                          stats["precpu_stats"]["system_cpu_usage"]
            cpu_count = stats["cpu_stats"].get("online_cpus", 1)

            if system_delta > 0:
                return (cpu_delta / system_delta) * cpu_count * 100.0
            return 0.0
        except (KeyError, ZeroDivisionError):
            return 0.0

    async def diagnose_with_claude(
        self, container_name: str, status_message: str, metrics: dict, logs: str
    ) -> dict:
        """Use Claude AI to diagnose the issue and recommend fixes"""
        if not self.claude_client:
            return {"diagnosis": "Claude not available", "recommended_action": "restart_container"}

        prompt = f"""You are an expert DevOps engineer diagnosing a container health issue.

**Container**: {container_name}
**Status**: {status_message}
**Metrics**: {json.dumps(metrics, indent=2)}

**Recent Logs** (last 100 lines):
```
{logs}
```

**Task**: Analyze this issue and provide:
1. Root cause diagnosis
2. Recommended healing action (choose from: restart_container, clear_cache, reset_connections, check_dependencies, manual_intervention)
3. Urgency level (critical, high, medium, low)
4. Confidence level (0-100%)

Respond in JSON format:
{{
  "diagnosis": "brief explanation of root cause",
  "recommended_action": "action_name",
  "urgency": "level",
  "confidence": 85,
  "reasoning": "detailed reasoning"
}}
"""

        try:
            message = await self.claude_client.messages.create(
                model=self.config["claude"]["model"],
                max_tokens=self.config["claude"]["max_tokens"],
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text
            diagnosis = json.loads(response_text)

            self.logger.info(
                "claude_diagnosis",
                container=container_name,
                action=diagnosis.get("recommended_action"),
                confidence=diagnosis.get("confidence"),
            )

            return diagnosis

        except Exception as e:
            self.logger.error("claude_diagnosis_failed", error=str(e))
            return {
                "diagnosis": f"Claude error: {str(e)}",
                "recommended_action": "restart_container",
                "urgency": "medium",
                "confidence": 50,
            }

    async def heal_container(
        self, container_name: str, action: str, diagnosis: dict
    ) -> bool:
        """Execute healing action on container"""
        self.logger.info("healing_attempt", container=container_name, action=action)

        start_time = datetime.now()
        success = False
        error_message = None

        try:
            if action == "restart_container":
                success = await self._restart_container(container_name)

            elif action == "clear_cache":
                # Execute cache clearing command inside container
                container = self.docker_client.containers.get(container_name)
                container.exec_run("sh -c 'rm -rf /tmp/* /var/tmp/*'")
                success = True

            elif action == "reset_connections":
                # Restart the container to reset connections
                success = await self._restart_container(container_name)

            elif action == "check_dependencies":
                # Check dependent containers (postgres, redis)
                success = await self._check_and_fix_dependencies(container_name)

            else:
                self.logger.warning("unknown_action", action=action)
                error_message = f"Unknown action: {action}"

        except Exception as e:
            self.logger.error("healing_failed", container=container_name, error=str(e))
            error_message = str(e)

        # Log healing action to database
        execution_time = (datetime.now() - start_time).total_seconds()
        await self._log_healing_action(
            container_name, action, success, error_message, diagnosis, execution_time
        )

        return success

    async def _restart_container(self, container_name: str) -> bool:
        """Restart a container with rate limiting"""
        # Check restart rate limiting
        if not self._can_restart(container_name):
            self.logger.warning(
                "restart_rate_limited",
                container=container_name,
                reason="too_many_restarts_in_hour",
            )
            return False

        try:
            container = self.docker_client.containers.get(container_name)
            container.restart(timeout=10)

            # Record restart
            if container_name not in self.restart_history:
                self.restart_history[container_name] = []
            self.restart_history[container_name].append(datetime.now())

            self.logger.info("container_restarted", container=container_name)
            return True

        except Exception as e:
            self.logger.error("restart_failed", container=container_name, error=str(e))
            return False

    def _can_restart(self, container_name: str) -> bool:
        """Check if container can be restarted based on rate limits"""
        # Get max restarts per hour from config
        container_config = self._get_container_config(container_name)
        max_restarts = container_config.get("max_restarts_per_hour", 3)

        # Get restart history for this container
        if container_name not in self.restart_history:
            return True

        # Filter restarts in the last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_restarts = [
            ts for ts in self.restart_history[container_name] if ts > one_hour_ago
        ]

        return len(recent_restarts) < max_restarts

    def _get_container_config(self, container_name: str) -> dict:
        """Get configuration for specific container"""
        for container in self.config["monitoring"]["containers"]:
            if container["name"] == container_name:
                return container
        return {}

    async def _check_and_fix_dependencies(self, container_name: str) -> bool:
        """Check and fix dependent containers (postgres, redis)"""
        dependencies = {
            "spartan-research-station": ["spartan-postgres", "spartan-redis"],
            "spartan-correlation-api": ["spartan-postgres"],
            "spartan-daily-planet-api": ["spartan-postgres"],
            "spartan-swing-api": ["spartan-postgres"],
            "spartan-garp-api": ["spartan-postgres"],
        }

        if container_name not in dependencies:
            return True

        all_healthy = True
        for dep_name in dependencies[container_name]:
            dep_config = self._get_container_config(dep_name)
            is_healthy, status, metrics = await self.check_container_health(dep_config)

            if not is_healthy:
                self.logger.warning(
                    "dependency_unhealthy",
                    container=container_name,
                    dependency=dep_name,
                    status=status,
                )
                # Try to heal the dependency
                await self._restart_container(dep_name)
                all_healthy = False

        return all_healthy

    async def _log_healing_action(
        self,
        container_name: str,
        action: str,
        success: bool,
        error_message: Optional[str],
        diagnosis: dict,
        execution_time: float,
    ) -> None:
        """Log healing action to database"""
        if not self.db_conn:
            return

        try:
            cursor = self.db_conn.cursor()
            cursor.execute(
                """
                INSERT INTO monitor_healing_actions
                (container_name, action_type, success, error_message, claude_reasoning, execution_time_seconds)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    container_name,
                    action,
                    success,
                    error_message,
                    diagnosis.get("reasoning"),
                    execution_time,
                ),
            )
            self.db_conn.commit()
            cursor.close()
        except Exception as e:
            self.logger.error("log_healing_action_failed", error=str(e))

    async def _log_incident(
        self,
        container_name: str,
        incident_type: str,
        severity: str,
        description: str,
        auto_healed: bool,
        healing_action: Optional[str],
    ) -> None:
        """Log incident to database"""
        if not self.db_conn:
            return

        try:
            cursor = self.db_conn.cursor()
            cursor.execute(
                """
                INSERT INTO monitor_incidents
                (container_name, incident_type, severity, description, auto_healed, healing_action)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (container_name, incident_type, severity, description, auto_healed, healing_action),
            )
            self.db_conn.commit()
            cursor.close()
        except Exception as e:
            self.logger.error("log_incident_failed", error=str(e))

    async def _log_health_metrics(
        self, container_name: str, status: str, metrics: dict
    ) -> None:
        """Log health metrics to database"""
        if not self.db_conn:
            return

        try:
            cursor = self.db_conn.cursor()
            cursor.execute(
                """
                INSERT INTO monitor_health_metrics
                (container_name, status, response_time_ms, memory_usage_mb, cpu_percent)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    container_name,
                    status,
                    metrics.get("response_time_ms"),
                    metrics.get("memory_usage_mb"),
                    metrics.get("cpu_percent"),
                ),
            )
            self.db_conn.commit()
            cursor.close()
        except Exception as e:
            self.logger.error("log_metrics_failed", error=str(e))

    def _get_container_logs(self, container_name: str, tail: int = 100) -> str:
        """Get recent container logs"""
        try:
            container = self.docker_client.containers.get(container_name)
            logs = container.logs(tail=tail, timestamps=True).decode("utf-8")
            return logs
        except Exception as e:
            return f"Failed to get logs: {str(e)}"

    async def monitor_loop(self) -> None:
        """Main monitoring loop"""
        self.logger.info("monitor_loop_started", interval=self.config["monitoring"]["interval_seconds"])

        while self.is_running:
            for container_config in self.config["monitoring"]["containers"]:
                container_name = container_config["name"]

                # Check health
                is_healthy, status_message, metrics = await self.check_container_health(
                    container_config
                )

                # Log metrics
                await self._log_health_metrics(
                    container_name, "healthy" if is_healthy else "unhealthy", metrics
                )

                if is_healthy:
                    self.logger.debug("container_healthy", container=container_name)
                else:
                    self.logger.warning(
                        "container_unhealthy",
                        container=container_name,
                        status=status_message,
                        metrics=metrics,
                    )

                    # Log incident
                    await self._log_incident(
                        container_name,
                        "health_check_failed",
                        "critical" if container_config.get("critical") else "warning",
                        status_message,
                        False,
                        None,
                    )

                    # Auto-heal if enabled
                    if (
                        self.config["healing"]["auto_heal_enabled"]
                        and container_config.get("auto_restart")
                    ):
                        # Get container logs for diagnosis
                        logs = self._get_container_logs(container_name)

                        # Diagnose with Claude if available
                        diagnosis = await self.diagnose_with_claude(
                            container_name, status_message, metrics, logs
                        )

                        # Execute healing action
                        recommended_action = diagnosis.get("recommended_action", "restart_container")
                        healing_success = await self.heal_container(
                            container_name, recommended_action, diagnosis
                        )

                        # Update incident log
                        if healing_success:
                            self.logger.info(
                                "auto_heal_success",
                                container=container_name,
                                action=recommended_action,
                            )

            # Wait for next check interval
            await asyncio.sleep(self.config["monitoring"]["interval_seconds"])

    async def start(self) -> None:
        """Start the monitoring agent"""
        self.logger.info("starting_website_monitor_agent", version=self.config["version"])

        # Connect to database
        await self.connect_database()

        # Start monitoring loop
        self.is_running = True
        await self.monitor_loop()

    async def stop(self) -> None:
        """Stop the monitoring agent"""
        self.logger.info("stopping_website_monitor_agent")
        self.is_running = False

        # Close database connection
        if self.db_conn:
            self.db_conn.close()


async def main():
    """Main entry point"""
    config_path = os.path.join(
        os.path.dirname(__file__), "config.yaml"
    )

    agent = WebsiteMonitorAgent(config_path)

    try:
        await agent.start()
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        await agent.stop()
    except Exception as e:
        print(f"Fatal error: {e}")
        await agent.stop()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
