#!/usr/bin/env python3
"""
Trading LLM Self-Improvement System
Recursive learning loop with bidirectional agent/skill integration

Features:
- Learns from trade outcomes to improve signal quality
- Bidirectional agent communication (consumes and produces)
- Skill accumulation and evolution
- Meta-cognition for strategy adaptation
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import hashlib
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class TradingSkill:
    """A learned trading skill"""
    name: str
    description: str
    category: str  # pattern_recognition, risk_management, timing, etc.
    power_level: float  # 0-100, increases with successful application
    success_rate: float  # Historical success rate
    applications: int  # Number of times applied
    last_applied: Optional[datetime] = None
    synergies: List[str] = field(default_factory=list)  # Skills that work well together
    contraindications: List[str] = field(default_factory=list)  # Skills that conflict
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'last_applied': self.last_applied.isoformat() if self.last_applied else None
        }


@dataclass
class LearningOutcome:
    """Outcome from a learning cycle"""
    trade_id: int
    symbol: str
    signal_type: str
    predicted_confidence: float
    actual_outcome: str  # 'win', 'loss', 'breakeven'
    pnl: float
    pnl_percent: float
    market_context_at_entry: Dict
    market_context_at_exit: Dict
    factors_that_worked: List[str]
    factors_that_failed: List[str]
    learned_patterns: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


class AgentMessage:
    """Message for inter-agent communication"""
    def __init__(
        self,
        sender: str,
        receiver: str,
        message_type: str,
        content: Dict,
        priority: int = 5,
        requires_response: bool = False
    ):
        self.id = hashlib.md5(f"{sender}{receiver}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        self.sender = sender
        self.receiver = receiver
        self.message_type = message_type
        self.content = content
        self.priority = priority
        self.requires_response = requires_response
        self.timestamp = datetime.now()
        self.response = None
        self.processed = False

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'sender': self.sender,
            'receiver': self.receiver,
            'message_type': self.message_type,
            'content': self.content,
            'priority': self.priority,
            'requires_response': self.requires_response,
            'timestamp': self.timestamp.isoformat(),
            'processed': self.processed
        }


class SelfImprovementEngine:
    """
    Recursive self-improvement engine for the Trading LLM

    Capabilities:
    1. Learn from trade outcomes
    2. Evolve skills based on success/failure
    3. Communicate bidirectionally with other agents
    4. Apply meta-cognition to improve strategies
    5. Compound learnings across sessions
    """

    KNOWLEDGE_FILE = os.path.expanduser("~/.claude/knowledge/trading_llm_skills.json")
    LEARNINGS_FILE = os.path.expanduser("~/.claude/learnings/trading_llm_learnings.json")

    # Known agents in the ecosystem
    KNOWN_AGENTS = [
        'BreakthroughAgent',
        'DiscoveryAgent',
        'PatternAgent',
        'TimingAgent',
        'TradingLLM',
        'RiskManager',
        'MarketScanner'
    ]

    def __init__(self):
        self.skills: Dict[str, TradingSkill] = {}
        self.learnings: List[LearningOutcome] = []
        self.message_queue: List[AgentMessage] = []
        self.agent_connections: Dict[str, bool] = {}
        self.meta_insights: List[Dict] = []

        # Performance tracking
        self.performance_by_skill: Dict[str, Dict] = defaultdict(lambda: {'wins': 0, 'losses': 0, 'pnl': 0})
        self.performance_by_context: Dict[str, Dict] = defaultdict(lambda: {'wins': 0, 'losses': 0, 'pnl': 0})

        # Load existing knowledge
        self._load_knowledge()
        self._initialize_core_skills()

        logger.info("Self-Improvement Engine initialized")

    def _load_knowledge(self):
        """Load persisted knowledge from disk"""
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.KNOWLEDGE_FILE), exist_ok=True)
        os.makedirs(os.path.dirname(self.LEARNINGS_FILE), exist_ok=True)

        # Load skills
        if os.path.exists(self.KNOWLEDGE_FILE):
            try:
                with open(self.KNOWLEDGE_FILE, 'r') as f:
                    data = json.load(f)
                    for name, skill_data in data.get('skills', {}).items():
                        self.skills[name] = TradingSkill(
                            name=skill_data['name'],
                            description=skill_data['description'],
                            category=skill_data['category'],
                            power_level=skill_data['power_level'],
                            success_rate=skill_data['success_rate'],
                            applications=skill_data['applications'],
                            synergies=skill_data.get('synergies', []),
                            contraindications=skill_data.get('contraindications', []),
                            metadata=skill_data.get('metadata', {})
                        )
                    self.meta_insights = data.get('meta_insights', [])
                logger.info(f"Loaded {len(self.skills)} skills from knowledge base")
            except Exception as e:
                logger.error(f"Failed to load knowledge: {e}")

    def _save_knowledge(self):
        """Persist knowledge to disk"""
        try:
            data = {
                'skills': {name: skill.to_dict() for name, skill in self.skills.items()},
                'meta_insights': self.meta_insights[-100:],  # Keep last 100 insights
                'last_updated': datetime.now().isoformat()
            }
            with open(self.KNOWLEDGE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.skills)} skills to knowledge base")
        except Exception as e:
            logger.error(f"Failed to save knowledge: {e}")

    def _initialize_core_skills(self):
        """Initialize core trading skills if not already present"""
        core_skills = [
            TradingSkill(
                name="barometer_reading",
                description="Interpret composite risk score for market direction",
                category="macro_analysis",
                power_level=50,
                success_rate=0.5,
                applications=0,
                synergies=["regime_classification", "risk_sizing"],
                contraindications=[]
            ),
            TradingSkill(
                name="cot_analysis",
                description="Analyze COT positioning for institutional bias",
                category="positioning",
                power_level=50,
                success_rate=0.5,
                applications=0,
                synergies=["commercial_tracking", "sentiment_reading"],
                contraindications=[]
            ),
            TradingSkill(
                name="regime_classification",
                description="Classify growth/inflation/liquidity regimes",
                category="macro_analysis",
                power_level=50,
                success_rate=0.5,
                applications=0,
                synergies=["barometer_reading", "asset_rotation"],
                contraindications=[]
            ),
            TradingSkill(
                name="risk_sizing",
                description="Calculate optimal position sizes based on risk",
                category="risk_management",
                power_level=50,
                success_rate=0.5,
                applications=0,
                synergies=["drawdown_control", "volatility_adjustment"],
                contraindications=["aggressive_sizing"]
            ),
            TradingSkill(
                name="pattern_recognition",
                description="Identify chart and statistical patterns",
                category="technical_analysis",
                power_level=50,
                success_rate=0.5,
                applications=0,
                synergies=["timing_optimization", "breakout_detection"],
                contraindications=[]
            ),
            TradingSkill(
                name="multi_asset_correlation",
                description="Track and trade intermarket relationships",
                category="intermarket",
                power_level=50,
                success_rate=0.5,
                applications=0,
                synergies=["regime_classification", "risk_parity"],
                contraindications=[]
            )
        ]

        for skill in core_skills:
            if skill.name not in self.skills:
                self.skills[skill.name] = skill

    # =========================================================================
    # LEARNING LOOP
    # =========================================================================

    def learn_from_trade(self, trade_outcome: Dict) -> LearningOutcome:
        """
        Learn from a completed trade

        This is the core learning loop:
        1. Analyze what factors contributed to outcome
        2. Update skill power levels based on success/failure
        3. Extract new patterns for future use
        4. Generate meta-insights for strategy improvement
        """
        # Determine outcome
        pnl = trade_outcome.get('realized_pnl', 0)
        if pnl > 0:
            outcome = 'win'
        elif pnl < 0:
            outcome = 'loss'
        else:
            outcome = 'breakeven'

        # Analyze contributing factors
        factors_worked = []
        factors_failed = []

        # Check which skills were applied
        reasoning = trade_outcome.get('reasoning', '')
        for skill_name, skill in self.skills.items():
            if skill_name.replace('_', ' ') in reasoning.lower():
                if outcome == 'win':
                    factors_worked.append(skill_name)
                    self._strengthen_skill(skill_name, 1.5)
                elif outcome == 'loss':
                    factors_failed.append(skill_name)
                    self._weaken_skill(skill_name, 0.8)

        # Extract learned patterns
        learned_patterns = self._extract_patterns(trade_outcome, outcome)

        # Create learning outcome
        learning = LearningOutcome(
            trade_id=trade_outcome.get('id', 0),
            symbol=trade_outcome.get('symbol', ''),
            signal_type=trade_outcome.get('signal_type', ''),
            predicted_confidence=trade_outcome.get('confidence', 0),
            actual_outcome=outcome,
            pnl=pnl,
            pnl_percent=trade_outcome.get('realized_pnl_percent', 0),
            market_context_at_entry=trade_outcome.get('entry_context', {}),
            market_context_at_exit=trade_outcome.get('exit_context', {}),
            factors_that_worked=factors_worked,
            factors_that_failed=factors_failed,
            learned_patterns=learned_patterns
        )

        self.learnings.append(learning)

        # Generate meta-insight
        self._generate_meta_insight(learning)

        # Persist knowledge
        self._save_knowledge()

        logger.info(f"Learned from trade: {outcome} on {learning.symbol}")
        return learning

    def _strengthen_skill(self, skill_name: str, factor: float = 1.1):
        """Strengthen a skill after successful application"""
        if skill_name in self.skills:
            skill = self.skills[skill_name]
            skill.applications += 1
            skill.power_level = min(100, skill.power_level * factor)

            # Update success rate
            total = skill.applications
            old_success = skill.success_rate * (total - 1)
            skill.success_rate = (old_success + 1) / total

            skill.last_applied = datetime.now()
            logger.info(f"Strengthened skill {skill_name}: power={skill.power_level:.1f}")

    def _weaken_skill(self, skill_name: str, factor: float = 0.95):
        """Weaken a skill after failed application"""
        if skill_name in self.skills:
            skill = self.skills[skill_name]
            skill.applications += 1
            skill.power_level = max(10, skill.power_level * factor)

            # Update success rate
            total = skill.applications
            old_success = skill.success_rate * (total - 1)
            skill.success_rate = old_success / total

            skill.last_applied = datetime.now()
            logger.info(f"Weakened skill {skill_name}: power={skill.power_level:.1f}")

    def _extract_patterns(self, trade: Dict, outcome: str) -> List[str]:
        """Extract patterns from trade for future learning"""
        patterns = []

        context = trade.get('entry_context', {})

        # Pattern: Risk status at entry
        risk_status = context.get('risk_status', '')
        if risk_status:
            pattern = f"{outcome}_when_{risk_status.lower()}_risk"
            patterns.append(pattern)
            self.performance_by_context[risk_status][f"{outcome}s"] = \
                self.performance_by_context[risk_status].get(f"{outcome}s", 0) + 1

        # Pattern: Market mode at entry
        market_mode = context.get('market_mode', '')
        if market_mode:
            pattern = f"{outcome}_in_{market_mode.lower().replace('-', '_')}_mode"
            patterns.append(pattern)

        # Pattern: VIX level at entry
        vix = context.get('vix_level', 0)
        if vix < 15:
            vix_cat = 'low_vix'
        elif vix < 25:
            vix_cat = 'normal_vix'
        else:
            vix_cat = 'high_vix'
        patterns.append(f"{outcome}_with_{vix_cat}")

        # Pattern: Asset class performance
        asset_class = trade.get('asset_class', '')
        if asset_class:
            patterns.append(f"{asset_class}_{outcome}")

        return patterns

    def _generate_meta_insight(self, learning: LearningOutcome):
        """Generate meta-level insights for strategy improvement"""
        # Look for repeated patterns in recent learnings
        recent = self.learnings[-20:]  # Last 20 trades

        # Count pattern occurrences
        pattern_counts = defaultdict(lambda: {'wins': 0, 'losses': 0})
        for l in recent:
            for p in l.learned_patterns:
                if 'win' in p:
                    base_pattern = p.replace('win_', '')
                    pattern_counts[base_pattern]['wins'] += 1
                elif 'loss' in p:
                    base_pattern = p.replace('loss_', '')
                    pattern_counts[base_pattern]['losses'] += 1

        # Generate insights from patterns
        for pattern, counts in pattern_counts.items():
            total = counts['wins'] + counts['losses']
            if total >= 3:  # Need at least 3 occurrences
                win_rate = counts['wins'] / total
                if win_rate >= 0.7:
                    insight = {
                        'type': 'high_probability_setup',
                        'pattern': pattern,
                        'win_rate': win_rate,
                        'sample_size': total,
                        'recommendation': f"Increase position size when {pattern.replace('_', ' ')}",
                        'timestamp': datetime.now().isoformat()
                    }
                    self.meta_insights.append(insight)
                    logger.info(f"Meta-insight: {insight['recommendation']}")
                elif win_rate <= 0.3:
                    insight = {
                        'type': 'avoid_setup',
                        'pattern': pattern,
                        'win_rate': win_rate,
                        'sample_size': total,
                        'recommendation': f"Reduce or avoid trading when {pattern.replace('_', ' ')}",
                        'timestamp': datetime.now().isoformat()
                    }
                    self.meta_insights.append(insight)
                    logger.info(f"Meta-insight: {insight['recommendation']}")

    # =========================================================================
    # AGENT COMMUNICATION (Bidirectional)
    # =========================================================================

    def send_message(
        self,
        receiver: str,
        message_type: str,
        content: Dict,
        priority: int = 5,
        requires_response: bool = False
    ) -> AgentMessage:
        """Send a message to another agent"""
        message = AgentMessage(
            sender='TradingLLM',
            receiver=receiver,
            message_type=message_type,
            content=content,
            priority=priority,
            requires_response=requires_response
        )
        self.message_queue.append(message)
        logger.info(f"Message sent to {receiver}: {message_type}")
        return message

    def receive_message(self, message: AgentMessage) -> Optional[Dict]:
        """
        Receive and process a message from another agent

        Supported message types:
        - signal_request: Request for trading signal
        - pattern_alert: Alert about detected pattern
        - risk_warning: Risk management warning
        - skill_share: Share a skill definition
        - learning_share: Share a learning outcome
        - context_update: Market context update
        """
        message.processed = True

        if message.message_type == 'signal_request':
            return self._handle_signal_request(message)
        elif message.message_type == 'pattern_alert':
            return self._handle_pattern_alert(message)
        elif message.message_type == 'risk_warning':
            return self._handle_risk_warning(message)
        elif message.message_type == 'skill_share':
            return self._handle_skill_share(message)
        elif message.message_type == 'learning_share':
            return self._handle_learning_share(message)
        elif message.message_type == 'context_update':
            return self._handle_context_update(message)
        else:
            logger.warning(f"Unknown message type: {message.message_type}")
            return None

    def _handle_signal_request(self, message: AgentMessage) -> Dict:
        """Handle a request for trading signal from another agent"""
        symbol = message.content.get('symbol')
        asset_class = message.content.get('asset_class')

        # This would call the main engine's analyze methods
        return {
            'status': 'received',
            'symbol': symbol,
            'message': f"Signal request received for {symbol}. Processing..."
        }

    def _handle_pattern_alert(self, message: AgentMessage) -> Dict:
        """Handle a pattern alert from another agent (e.g., PatternAgent)"""
        pattern = message.content.get('pattern')
        symbol = message.content.get('symbol')
        confidence = message.content.get('confidence', 50)

        # Log the pattern for consideration in next signal
        logger.info(f"Pattern alert from {message.sender}: {pattern} on {symbol}")

        # Could evolve a skill based on pattern type
        if pattern and 'fibonacci' in pattern.lower():
            if 'fibonacci_analysis' not in self.skills:
                self.skills['fibonacci_analysis'] = TradingSkill(
                    name='fibonacci_analysis',
                    description=f"Learned from {message.sender}",
                    category='technical_analysis',
                    power_level=40 + (confidence * 0.2),
                    success_rate=0.5,
                    applications=1
                )

        return {'status': 'acknowledged', 'action': 'pattern_logged'}

    def _handle_risk_warning(self, message: AgentMessage) -> Dict:
        """Handle a risk warning from RiskManager"""
        warning_type = message.content.get('warning_type')
        severity = message.content.get('severity', 'medium')

        if severity == 'high':
            # Reduce position sizing skill power temporarily
            if 'risk_sizing' in self.skills:
                self.skills['risk_sizing'].metadata['risk_multiplier'] = 0.5
                logger.warning(f"Risk warning received - reducing position sizes")

        return {'status': 'acknowledged', 'action': 'risk_adjusted'}

    def _handle_skill_share(self, message: AgentMessage) -> Dict:
        """Receive a skill from another agent"""
        skill_data = message.content.get('skill')
        if skill_data:
            skill_name = skill_data.get('name')
            if skill_name and skill_name not in self.skills:
                self.skills[skill_name] = TradingSkill(
                    name=skill_name,
                    description=skill_data.get('description', f"Learned from {message.sender}"),
                    category=skill_data.get('category', 'shared'),
                    power_level=skill_data.get('power_level', 40),
                    success_rate=skill_data.get('success_rate', 0.5),
                    applications=0,
                    metadata={'source_agent': message.sender}
                )
                logger.info(f"Learned new skill from {message.sender}: {skill_name}")
                self._save_knowledge()
                return {'status': 'skill_learned', 'skill': skill_name}

        return {'status': 'skill_rejected', 'reason': 'invalid_skill_data'}

    def _handle_learning_share(self, message: AgentMessage) -> Dict:
        """Receive a learning from another agent"""
        learning_data = message.content.get('learning')
        if learning_data:
            # Extract patterns from shared learning
            patterns = learning_data.get('patterns', [])
            for pattern in patterns:
                logger.info(f"Received pattern from {message.sender}: {pattern}")

            return {'status': 'learning_received'}

        return {'status': 'learning_rejected'}

    def _handle_context_update(self, message: AgentMessage) -> Dict:
        """Handle market context update"""
        context = message.content.get('context', {})

        # Could trigger re-evaluation of open positions
        risk_status = context.get('risk_status')
        if risk_status == 'RED':
            logger.warning("Context update: Market risk is RED")

        return {'status': 'context_acknowledged'}

    def broadcast_learning(self, learning: LearningOutcome):
        """Broadcast a learning to all known agents"""
        for agent in self.KNOWN_AGENTS:
            if agent != 'TradingLLM':
                self.send_message(
                    receiver=agent,
                    message_type='learning_share',
                    content={
                        'learning': {
                            'outcome': learning.actual_outcome,
                            'patterns': learning.learned_patterns,
                            'factors_worked': learning.factors_that_worked,
                            'factors_failed': learning.factors_that_failed
                        }
                    },
                    priority=3
                )

    def request_skill_from_agent(self, agent: str, skill_category: str):
        """Request a skill from another agent"""
        self.send_message(
            receiver=agent,
            message_type='skill_request',
            content={'category': skill_category},
            priority=5,
            requires_response=True
        )

    # =========================================================================
    # SKILL EVOLUTION
    # =========================================================================

    def evolve_skills(self):
        """
        Periodic skill evolution based on accumulated learnings

        This is the recursive improvement loop:
        1. Analyze skill performance
        2. Create compound skills from synergies
        3. Deprecate underperforming skills
        4. Generate new skills from patterns
        """
        logger.info("Running skill evolution cycle...")

        # 1. Analyze skill performance
        for skill_name, skill in list(self.skills.items()):
            if skill.applications >= 10:  # Enough data
                if skill.success_rate >= 0.7 and skill.power_level < 90:
                    # Promote high-performing skill
                    skill.power_level = min(100, skill.power_level * 1.2)
                    logger.info(f"Promoted skill {skill_name} to power {skill.power_level:.1f}")

                elif skill.success_rate <= 0.3 and skill.power_level > 20:
                    # Demote underperforming skill
                    skill.power_level = max(10, skill.power_level * 0.7)
                    logger.info(f"Demoted skill {skill_name} to power {skill.power_level:.1f}")

        # 2. Create compound skills from synergies
        for skill_name, skill in list(self.skills.items()):
            if skill.power_level >= 70 and skill.synergies:
                for synergy in skill.synergies:
                    if synergy in self.skills:
                        synergy_skill = self.skills[synergy]
                        if synergy_skill.power_level >= 70:
                            # Create compound skill
                            compound_name = f"{skill_name}_{synergy}_compound"
                            if compound_name not in self.skills:
                                self.skills[compound_name] = TradingSkill(
                                    name=compound_name,
                                    description=f"Compound of {skill_name} and {synergy}",
                                    category="compound",
                                    power_level=(skill.power_level + synergy_skill.power_level) / 2,
                                    success_rate=(skill.success_rate + synergy_skill.success_rate) / 2,
                                    applications=0,
                                    synergies=[skill_name, synergy],
                                    metadata={'parent_skills': [skill_name, synergy]}
                                )
                                logger.info(f"Created compound skill: {compound_name}")

        # 3. Generate new skills from meta-insights
        for insight in self.meta_insights[-10:]:  # Recent insights
            if insight['type'] == 'high_probability_setup':
                pattern = insight['pattern']
                skill_name = f"pattern_{pattern}"
                if skill_name not in self.skills:
                    self.skills[skill_name] = TradingSkill(
                        name=skill_name,
                        description=f"High-probability pattern: {pattern}",
                        category="learned_pattern",
                        power_level=50 + (insight['win_rate'] * 30),
                        success_rate=insight['win_rate'],
                        applications=insight['sample_size'],
                        metadata={'source': 'meta_insight'}
                    )
                    logger.info(f"Created pattern skill: {skill_name}")

        self._save_knowledge()
        logger.info(f"Skill evolution complete. Total skills: {len(self.skills)}")

    def get_best_skills_for_context(self, context: Dict, limit: int = 5) -> List[TradingSkill]:
        """Get the most relevant skills for current market context"""
        scored_skills = []

        risk_status = context.get('risk_status', 'YELLOW')
        market_mode = context.get('market_mode', 'unknown')

        for skill in self.skills.values():
            score = skill.power_level * skill.success_rate

            # Boost skills that match context
            if 'risk' in skill.name.lower() and risk_status == 'RED':
                score *= 1.3
            if 'regime' in skill.name.lower():
                score *= 1.2
            if skill.category == 'compound':
                score *= 1.1  # Prefer compound skills

            scored_skills.append((score, skill))

        scored_skills.sort(key=lambda x: x[0], reverse=True)
        return [s[1] for s in scored_skills[:limit]]

    # =========================================================================
    # REPORTING
    # =========================================================================

    def get_skill_report(self) -> Dict:
        """Get a report of all skills and their status"""
        skills_by_category = defaultdict(list)
        for skill in self.skills.values():
            skills_by_category[skill.category].append(skill.to_dict())

        return {
            'total_skills': len(self.skills),
            'by_category': dict(skills_by_category),
            'top_performers': [
                s.to_dict() for s in sorted(
                    self.skills.values(),
                    key=lambda x: x.power_level * x.success_rate,
                    reverse=True
                )[:5]
            ],
            'recent_meta_insights': self.meta_insights[-5:]
        }

    def get_learning_report(self) -> Dict:
        """Get a report of recent learnings"""
        recent = self.learnings[-20:]

        wins = [l for l in recent if l.actual_outcome == 'win']
        losses = [l for l in recent if l.actual_outcome == 'loss']

        return {
            'total_learnings': len(self.learnings),
            'recent_win_rate': len(wins) / len(recent) if recent else 0,
            'avg_pnl': sum(l.pnl for l in recent) / len(recent) if recent else 0,
            'common_winning_factors': self._get_common_factors(wins, 'factors_that_worked'),
            'common_losing_factors': self._get_common_factors(losses, 'factors_that_failed'),
            'learned_patterns': list(set(p for l in recent for p in l.learned_patterns))[:10]
        }

    def _get_common_factors(self, learnings: List[LearningOutcome], field: str) -> List[str]:
        """Get most common factors from learnings"""
        factor_counts = defaultdict(int)
        for l in learnings:
            for f in getattr(l, field, []):
                factor_counts[f] += 1

        sorted_factors = sorted(factor_counts.items(), key=lambda x: x[1], reverse=True)
        return [f[0] for f in sorted_factors[:5]]


# Singleton instance
_improvement_engine: Optional[SelfImprovementEngine] = None


def get_improvement_engine() -> SelfImprovementEngine:
    """Get or create the singleton improvement engine"""
    global _improvement_engine
    if _improvement_engine is None:
        _improvement_engine = SelfImprovementEngine()
    return _improvement_engine


if __name__ == "__main__":
    # Test the engine
    engine = SelfImprovementEngine()

    print("=" * 60)
    print("SELF-IMPROVEMENT ENGINE - Test")
    print("=" * 60)

    # Test skill report
    print("\n1. Skill Report:")
    report = engine.get_skill_report()
    print(f"   Total skills: {report['total_skills']}")
    for cat, skills in report['by_category'].items():
        print(f"   - {cat}: {len(skills)} skills")

    # Test learning from a trade
    print("\n2. Learning from trade...")
    outcome = engine.learn_from_trade({
        'id': 1,
        'symbol': 'ES',
        'signal_type': 'buy',
        'confidence': 75,
        'realized_pnl': 500,
        'realized_pnl_percent': 2.5,
        'reasoning': 'barometer reading showed green, cot analysis bullish',
        'entry_context': {
            'risk_status': 'GREEN',
            'market_mode': 'Risk-On',
            'vix_level': 14
        },
        'exit_context': {
            'risk_status': 'GREEN',
            'market_mode': 'Risk-On',
            'vix_level': 13
        }
    })
    print(f"   Outcome: {outcome.actual_outcome}")
    print(f"   Patterns learned: {outcome.learned_patterns}")

    # Test skill evolution
    print("\n3. Evolving skills...")
    engine.evolve_skills()

    # Test agent messaging
    print("\n4. Agent messaging...")
    msg = engine.send_message(
        receiver='PatternAgent',
        message_type='signal_request',
        content={'symbol': 'EURUSD', 'asset_class': 'forex'}
    )
    print(f"   Sent message: {msg.id} to {msg.receiver}")

    # Receive a pattern alert
    alert = AgentMessage(
        sender='PatternAgent',
        receiver='TradingLLM',
        message_type='pattern_alert',
        content={
            'pattern': 'fibonacci_retracement_61.8',
            'symbol': 'EURUSD',
            'confidence': 72
        }
    )
    response = engine.receive_message(alert)
    print(f"   Received pattern alert: {response}")

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
