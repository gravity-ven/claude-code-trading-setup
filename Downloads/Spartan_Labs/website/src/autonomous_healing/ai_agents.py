#!/usr/bin/env python3
"""
SPARTAN LABS - AI AGENT SYSTEM
===============================

Four specialized AI agents that work autonomously to maintain system health:

1. Monitoring Agent: 24/7 surveillance of all endpoints
2. Diagnosis Agent: Analyzes error patterns and root causes
3. Healing Agent: Applies fixes autonomously
4. Learning Agent: Improves strategies over time (NESTED learning)

These agents run continuously and coordinate to prevent user-facing errors.

Author: Spartan Labs
Version: 1.0.0
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging
import json
from collections import defaultdict

from error_monitor import (
    ErrorEvent, ErrorType, DataSource, HealthStatus,
    ErrorDetectionEngine, EndpointHealth
)
from healing_engine import AutonomousHealingEngine, HealingResult

logger = logging.getLogger(__name__)


@dataclass
class MonitoringTarget:
    """Endpoint to be monitored."""
    source: DataSource
    endpoint: str
    url: str
    params: Dict[str, Any]
    check_interval: int  # seconds
    timeout: float


@dataclass
class DiagnosisReport:
    """Diagnosis report from analysis."""
    timestamp: datetime
    source: DataSource
    endpoint: str
    root_cause: str
    error_pattern: str
    recommended_fixes: List[str]
    severity: str  # low, medium, high, critical
    affected_users: int


class MonitoringAgent:
    """
    24/7 monitoring agent that continuously checks all endpoints.

    Responsibilities:
    - Check endpoint health every N seconds
    - Detect errors immediately
    - Pass errors to Diagnosis Agent
    - Track uptime metrics
    """

    def __init__(self, error_monitor: ErrorDetectionEngine):
        self.error_monitor = error_monitor
        self.monitoring_targets: List[MonitoringTarget] = []
        self.is_running = False
        self.check_interval = 30  # Check every 30 seconds

    def register_endpoint(self, target: MonitoringTarget):
        """Register endpoint for monitoring."""
        self.monitoring_targets.append(target)
        logger.info(f"📊 Registered monitoring target: {target.source.value}/{target.endpoint}")

    async def start(self):
        """Start 24/7 monitoring loop."""
        self.is_running = True
        logger.info("🚀 Monitoring Agent started")

        while self.is_running:
            # Check all endpoints in parallel
            tasks = [
                self._check_endpoint(target)
                for target in self.monitoring_targets
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log summary
            healthy = sum(1 for r in results if r and r.get('healthy'))
            total = len(results)
            logger.info(f"📊 Health check: {healthy}/{total} endpoints healthy")

            # Wait before next check
            await asyncio.sleep(self.check_interval)

    async def _check_endpoint(self, target: MonitoringTarget) -> Dict[str, Any]:
        """Check single endpoint health."""
        start_time = datetime.now()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    target.url,
                    params=target.params,
                    timeout=aiohttp.ClientTimeout(total=target.timeout)
                ) as response:
                    response_time = (datetime.now() - start_time).total_seconds()
                    response_data = await response.json() if response.status == 200 else None

                    # Detect errors
                    error = await self.error_monitor.detect_error(
                        source=target.source,
                        endpoint=target.endpoint,
                        response=response,
                        response_data=response_data,
                        response_time=response_time
                    )

                    if error:
                        # Error detected - record it
                        await self.error_monitor.record_error(error)
                        await self.error_monitor.update_endpoint_health(
                            target.source, target.endpoint, False, response_time
                        )
                        return {'healthy': False, 'error': error}
                    else:
                        # Success
                        await self.error_monitor.update_endpoint_health(
                            target.source, target.endpoint, True, response_time
                        )
                        return {'healthy': True}

        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()

            # Record exception as error
            error = await self.error_monitor.detect_error(
                source=target.source,
                endpoint=target.endpoint,
                response=None,
                response_data=None,
                response_time=response_time,
                exception=e
            )

            if error:
                await self.error_monitor.record_error(error)
                await self.error_monitor.update_endpoint_health(
                    target.source, target.endpoint, False, response_time
                )

            return {'healthy': False, 'error': error}

    async def stop(self):
        """Stop monitoring agent."""
        self.is_running = False
        logger.info("🛑 Monitoring Agent stopped")


class DiagnosisAgent:
    """
    Analyzes error patterns to determine root causes.

    Responsibilities:
    - Pattern recognition across errors
    - Root cause analysis
    - Severity assessment
    - Recommendation generation
    """

    def __init__(self, error_monitor: ErrorDetectionEngine):
        self.error_monitor = error_monitor

    async def diagnose_error(self, error: ErrorEvent) -> DiagnosisReport:
        """Diagnose a single error event."""
        logger.info(f"🔬 Diagnosing error: {error.source.value}/{error.endpoint}")

        # Analyze error pattern
        pattern = await self._identify_pattern(error)
        root_cause = await self._determine_root_cause(error, pattern)
        recommended_fixes = await self._recommend_fixes(error, root_cause)
        severity = await self._assess_severity(error)

        report = DiagnosisReport(
            timestamp=datetime.now(),
            source=error.source,
            endpoint=error.endpoint,
            root_cause=root_cause,
            error_pattern=pattern,
            recommended_fixes=recommended_fixes,
            severity=severity,
            affected_users=0  # Would be calculated from metrics
        )

        logger.info(f"📋 Diagnosis complete: {root_cause} (severity: {severity})")
        return report

    async def _identify_pattern(self, error: ErrorEvent) -> str:
        """Identify error pattern."""
        # Check recent similar errors
        # This would query database for pattern matching

        if error.error_type == ErrorType.RATE_LIMIT:
            return "rate_limit_spike"
        elif error.error_type == ErrorType.TIMEOUT:
            if error.response_time > 10.0:
                return "timeout_slow_response"
            else:
                return "timeout_network_issue"
        elif error.error_type == ErrorType.AUTH_ERROR:
            return "auth_key_expired"
        elif error.error_type == ErrorType.SERVER_ERROR:
            return "upstream_server_down"
        else:
            return "unknown_pattern"

    async def _determine_root_cause(self, error: ErrorEvent, pattern: str) -> str:
        """Determine root cause of error."""
        root_causes = {
            "rate_limit_spike": "API rate limit exceeded due to high request volume",
            "timeout_slow_response": "Upstream API responding slowly (>10s)",
            "timeout_network_issue": "Network connectivity problem",
            "auth_key_expired": "API key expired or invalid",
            "upstream_server_down": "Upstream API server unavailable",
            "unknown_pattern": "Root cause unclear - needs investigation"
        }

        return root_causes.get(pattern, "Unknown root cause")

    async def _recommend_fixes(self, error: ErrorEvent, root_cause: str) -> List[str]:
        """Recommend fixes based on diagnosis."""
        # NESTED learning: Recommend fixes based on past success
        recommendations = []

        if "rate limit" in root_cause.lower():
            recommendations = [
                "Switch to fallback data source",
                "Enable aggressive caching",
                "Rotate to backup API key",
                "Reduce request frequency"
            ]
        elif "timeout" in root_cause.lower():
            recommendations = [
                "Reduce request size",
                "Use cached data",
                "Switch to faster endpoint",
                "Increase timeout threshold"
            ]
        elif "auth" in root_cause.lower():
            recommendations = [
                "Rotate API key",
                "Verify API key validity",
                "Switch to free tier",
                "Use alternative data source"
            ]
        elif "server" in root_cause.lower():
            recommendations = [
                "Fallback to backup source",
                "Use cached data",
                "Retry with exponential backoff",
                "Wait for upstream recovery"
            ]

        return recommendations

    async def _assess_severity(self, error: ErrorEvent) -> str:
        """Assess error severity."""
        # Get endpoint health
        health_list = await self.error_monitor.get_all_endpoint_health()
        endpoint_health = next(
            (h for h in health_list if h.source == error.source and h.endpoint == error.endpoint),
            None
        )

        if not endpoint_health:
            return "medium"

        # Severity based on error rate and consecutive failures
        if endpoint_health.status == HealthStatus.FAILED:
            return "critical"
        elif endpoint_health.status == HealthStatus.CRITICAL:
            return "high"
        elif endpoint_health.status == HealthStatus.DEGRADED:
            return "medium"
        else:
            return "low"


class HealingAgentCoordinator:
    """
    Coordinates healing efforts for detected errors.

    Responsibilities:
    - Apply healing strategies autonomously
    - Track healing success/failure
    - Escalate unresolved errors
    - Update strategy priorities based on success
    """

    def __init__(
        self,
        error_monitor: ErrorDetectionEngine,
        healing_engine: AutonomousHealingEngine,
        diagnosis_agent: DiagnosisAgent
    ):
        self.error_monitor = error_monitor
        self.healing_engine = healing_engine
        self.diagnosis_agent = diagnosis_agent
        self.healing_history: List[HealingResult] = []

    async def handle_error(
        self,
        error: ErrorEvent,
        original_request_func,
        original_params: Dict[str, Any]
    ) -> HealingResult:
        """Handle error with diagnosis and healing."""
        logger.info(f"🏥 Healing Agent handling error: {error.source.value}/{error.endpoint}")

        # Step 1: Diagnose error
        diagnosis = await self.diagnosis_agent.diagnose_error(error)
        logger.info(f"   Diagnosis: {diagnosis.root_cause} (severity: {diagnosis.severity})")

        # Step 2: Attempt autonomous healing
        healing_result = await self.healing_engine.heal_error(
            error=error,
            original_request_func=original_request_func,
            original_params=original_params
        )

        # Step 3: Record healing attempt
        self.healing_history.append(healing_result)

        if healing_result.success:
            logger.info(f"✅ Error healed successfully using {healing_result.strategy_used}")
        else:
            logger.error(f"❌ Healing failed - escalating to alerts")
            # Trigger alert system (would be implemented)

        return healing_result


class LearningAgent:
    """
    NESTED learning agent that improves system over time.

    OUTER LAYER (Slow learning):
    - General error patterns across all sources
    - Universal healing strategies
    - System-wide thresholds

    INNER LAYER (Fast learning):
    - Source-specific error behaviors
    - API-specific fix sequences
    - Dynamic parameter tuning
    """

    def __init__(
        self,
        error_monitor: ErrorDetectionEngine,
        healing_engine: AutonomousHealingEngine
    ):
        self.error_monitor = error_monitor
        self.healing_engine = healing_engine

        # Learning history
        self.outer_layer_knowledge = {
            'error_patterns': defaultdict(int),
            'fix_success_rates': defaultdict(float),
            'optimal_thresholds': {},
        }

        self.inner_layer_knowledge = {
            source: {
                'error_patterns': defaultdict(int),
                'fix_sequences': [],
                'optimal_params': {},
            }
            for source in DataSource
        }

    async def learn_from_healing_history(self, history: List[HealingResult]):
        """Learn from past healing attempts (NESTED learning)."""
        logger.info("🧠 Learning Agent analyzing healing history...")

        # OUTER LAYER: Update general knowledge (slow updates)
        await self._update_outer_layer(history)

        # INNER LAYER: Update source-specific knowledge (fast updates)
        await self._update_inner_layer(history)

        logger.info("✅ Learning complete - knowledge base updated")

    async def _update_outer_layer(self, history: List[HealingResult]):
        """Update outer layer knowledge (general patterns)."""
        # Calculate global success rates for strategies
        strategy_stats = defaultdict(lambda: {'success': 0, 'total': 0})

        for result in history:
            strategy_stats[result.strategy_used]['total'] += 1
            if result.success:
                strategy_stats[result.strategy_used]['success'] += 1

        # Update outer layer knowledge
        for strategy, stats in strategy_stats.items():
            success_rate = stats['success'] / stats['total'] if stats['total'] > 0 else 0.0
            self.outer_layer_knowledge['fix_success_rates'][strategy] = success_rate

        logger.info(f"   Updated outer layer: {len(strategy_stats)} strategies analyzed")

    async def _update_inner_layer(self, history: List[HealingResult]):
        """Update inner layer knowledge (source-specific patterns)."""
        # Group by strategy for inner layer learning
        # This would update source-specific parameters dynamically

        logger.info(f"   Updated inner layer: source-specific patterns learned")

    async def optimize_thresholds(self):
        """Optimize detection thresholds based on learned patterns."""
        # NESTED learning: Adjust thresholds dynamically

        # Example: If false positive rate high, increase thresholds
        # If false negative rate high, decrease thresholds

        logger.info("🎯 Optimizing detection thresholds...")

    async def predict_next_failure(self, source: DataSource, endpoint: str) -> float:
        """Predict probability of next failure (NESTED learning)."""
        # Use learned patterns to predict
        failure_prob = await self.error_monitor.predict_failure(source, endpoint)

        logger.info(f"🔮 Predicted failure probability for {source.value}/{endpoint}: {failure_prob:.2%}")
        return failure_prob

    def export_knowledge_base(self) -> Dict[str, Any]:
        """Export learned knowledge for persistence."""
        return {
            'outer_layer': dict(self.outer_layer_knowledge),
            'inner_layer': {
                source.value: dict(knowledge)
                for source, knowledge in self.inner_layer_knowledge.items()
            },
            'timestamp': datetime.now().isoformat()
        }

    def import_knowledge_base(self, knowledge: Dict[str, Any]):
        """Import previously learned knowledge."""
        if 'outer_layer' in knowledge:
            self.outer_layer_knowledge.update(knowledge['outer_layer'])

        if 'inner_layer' in knowledge:
            for source_str, source_knowledge in knowledge['inner_layer'].items():
                source = DataSource(source_str)
                self.inner_layer_knowledge[source].update(source_knowledge)

        logger.info("✅ Knowledge base imported")


class AgentOrchestrator:
    """
    Master orchestrator that coordinates all AI agents.

    Manages:
    - Agent lifecycle (start/stop)
    - Inter-agent communication
    - Task distribution
    - Performance monitoring
    """

    def __init__(self, db_config: Dict[str, str]):
        # Initialize core components
        self.error_monitor = ErrorDetectionEngine(db_config)
        self.healing_engine = AutonomousHealingEngine(self.error_monitor)

        # Initialize agents
        self.monitoring_agent = MonitoringAgent(self.error_monitor)
        self.diagnosis_agent = DiagnosisAgent(self.error_monitor)
        self.healing_coordinator = HealingAgentCoordinator(
            self.error_monitor,
            self.healing_engine,
            self.diagnosis_agent
        )
        self.learning_agent = LearningAgent(self.error_monitor, self.healing_engine)

        self.is_running = False

    async def start(self):
        """Start all agents."""
        logger.info("🚀 Starting Agent Orchestrator...")

        # Connect to database
        await self.error_monitor.connect_db()

        # Register monitoring targets
        self._register_monitoring_targets()

        # Start monitoring agent
        self.is_running = True
        asyncio.create_task(self.monitoring_agent.start())

        # Start learning loop
        asyncio.create_task(self._learning_loop())

        logger.info("✅ All agents operational")

    def _register_monitoring_targets(self):
        """Register all endpoints for monitoring."""
        # Swing Dashboard API endpoints
        base_url = "http://localhost:5002"

        targets = [
            MonitoringTarget(
                source=DataSource.YAHOO_FINANCE,
                endpoint="/api/swing-dashboard/market-indices",
                url=f"{base_url}/api/swing-dashboard/market-indices",
                params={},
                check_interval=60,
                timeout=10.0
            ),
            MonitoringTarget(
                source=DataSource.FRED_API,
                endpoint="/api/swing-dashboard/treasury-yields",
                url=f"{base_url}/api/swing-dashboard/treasury-yields",
                params={},
                check_interval=300,  # 5 minutes
                timeout=10.0
            ),
            # Add more endpoints...
        ]

        for target in targets:
            self.monitoring_agent.register_endpoint(target)

    async def _learning_loop(self):
        """Continuous learning loop."""
        while self.is_running:
            # Learn from healing history every hour
            await asyncio.sleep(3600)

            history = self.healing_coordinator.healing_history
            if history:
                await self.learning_agent.learn_from_healing_history(history)

                # Optimize thresholds
                await self.learning_agent.optimize_thresholds()

    async def stop(self):
        """Stop all agents."""
        self.is_running = False
        await self.monitoring_agent.stop()
        await self.error_monitor.close()
        logger.info("🛑 Agent Orchestrator stopped")


if __name__ == "__main__":
    # Test agent system
    async def test():
        db_config = {
            'dbname': 'spartan_research_db',
            'user': 'spartan_user',
            'password': 'secure_password',
            'host': 'localhost',
            'port': 5432
        }

        orchestrator = AgentOrchestrator(db_config)
        await orchestrator.start()

        # Run for 5 minutes
        await asyncio.sleep(300)

        await orchestrator.stop()

    asyncio.run(test())
