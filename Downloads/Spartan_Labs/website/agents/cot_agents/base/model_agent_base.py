"""
Model Agent Base Class - Tier 3 (Agents 56-80)

Base class for confluence model agents.
These agents aggregate signals and generate confluence scores.
"""

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Dict, Optional, List


class ModelAgentBase:
    """
    Base class for model/confluence agents (Tier 3, Agents 56-80)

    Responsibilities:
    - Aggregate signals from Tier 1 (COT) and Tier 2 (Seasonal)
    - Calculate confluence scores (0-100)
    - Rank opportunities by priority
    - Generate consensus direction
    """

    def __init__(self, agent_id: int, agent_name: str):
        """
        Initialize Model Agent

        Args:
            agent_id: Unique agent ID (56-80)
            agent_name: Human-readable agent name
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.agent_tier = "TIER3_MODEL"

        # Logger (initialize first)
        self.logger = logging.getLogger(f"Agent{agent_id}")

        # Database connection
        self.db_conn = None
        self.connect_to_database()

        # Score weights
        self.WEIGHTS = {
            'cot_score': 40,  # 40% weight
            'seasonal_score': 30,  # 30% weight
            'technical_score': 20,  # 20% weight
            'fundamental_score': 10  # 10% weight
        }

        self.logger.info(f"Initialized {self.agent_name}")

    def connect_to_database(self):
        """Connect to PostgreSQL database"""
        try:
            self.db_conn = psycopg2.connect(
                dbname=os.getenv('POSTGRES_DB', 'spartan_research_db'),
                user=os.getenv('POSTGRES_USER', 'spartan'),
                password=os.getenv('POSTGRES_PASSWORD', 'spartan'),
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=os.getenv('POSTGRES_PORT', '5432')
            )
            self.logger.info("✅ Connected to PostgreSQL database")
        except Exception as e:
            self.logger.error(f"❌ Database connection failed: {e}")
            raise

    def get_active_cot_signals(self, symbol: str) -> List[Dict]:
        """
        Retrieve active COT signals for a symbol

        Args:
            symbol: Market symbol

        Returns:
            List of active COT signals
        """
        try:
            cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT *
                FROM agent_signals
                WHERE symbol = %s
                  AND agent_tier = 'TIER1_COT'
                  AND status = 'ACTIVE'
                  AND signal_date >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY signal_strength DESC
            """, (symbol,))

            signals = cursor.fetchall()
            cursor.close()

            return list(signals)

        except Exception as e:
            self.logger.error(f"❌ Error fetching COT signals: {e}")
            return []

    def get_active_seasonal_signals(self, symbol: str) -> List[Dict]:
        """
        Retrieve active seasonal patterns for a symbol

        Args:
            symbol: Market symbol

        Returns:
            List of active seasonal patterns
        """
        try:
            cursor = self.db_conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute("""
                SELECT *
                FROM seasonal_patterns
                WHERE symbol = %s
                  AND is_active = TRUE
                ORDER BY confidence_score DESC
            """, (symbol,))

            patterns = cursor.fetchall()
            cursor.close()

            return list(patterns)

        except Exception as e:
            self.logger.error(f"❌ Error fetching seasonal patterns: {e}")
            return []

    def calculate_confluence_score(self, symbol: str) -> Optional[Dict]:
        """
        Calculate confluence score by aggregating all signal types

        Args:
            symbol: Market symbol

        Returns:
            Dict with confluence score details
        """
        try:
            # Get signals from different tiers
            cot_signals = self.get_active_cot_signals(symbol)
            seasonal_signals = self.get_active_seasonal_signals(symbol)

            if not cot_signals and not seasonal_signals:
                return None

            # Calculate component scores
            cot_score = self.calculate_cot_score(cot_signals)
            seasonal_score = self.calculate_seasonal_score(seasonal_signals)

            # Weighted total score
            total_score = int(
                (cot_score * self.WEIGHTS['cot_score'] / 100) +
                (seasonal_score * self.WEIGHTS['seasonal_score'] / 100)
            )

            # Grade the score
            score_grade = self.grade_score(total_score)

            # Determine consensus direction
            consensus = self.determine_consensus(cot_signals, seasonal_signals)

            # Recommended action
            action = self.recommend_action(total_score, consensus)

            return {
                'symbol': symbol,
                'total_score': total_score,
                'score_grade': score_grade,
                'cot_score': cot_score,
                'seasonal_score': seasonal_score,
                'consensus_direction': consensus,
                'recommended_action': action,
                'num_bullish_signals': len([s for s in cot_signals if s['direction'] == 'LONG']),
                'num_bearish_signals': len([s for s in cot_signals if s['direction'] == 'SHORT'])
            }

        except Exception as e:
            self.logger.error(f"❌ Error calculating confluence score: {e}")
            return None

    def calculate_cot_score(self, signals: List[Dict]) -> int:
        """Calculate COT component score (0-100)"""
        if not signals:
            return 50  # Neutral

        # Average signal strength
        avg_strength = sum(s['signal_strength'] for s in signals) / len(signals)
        return int(avg_strength)

    def calculate_seasonal_score(self, patterns: List[Dict]) -> int:
        """Calculate seasonal component score (0-100)"""
        if not patterns:
            return 50  # Neutral

        # Weight by confidence
        total_confidence = sum(p['confidence_score'] for p in patterns)
        if total_confidence == 0:
            return 50

        weighted_score = sum(
            p['confidence_score'] * (p['win_rate'] / 100)
            for p in patterns
        )

        return int((weighted_score / total_confidence) * 100)

    def determine_consensus(self, cot_signals: List[Dict], seasonal_signals: List[Dict]) -> str:
        """Determine consensus direction from all signals"""
        bullish_count = len([s for s in cot_signals if s['direction'] == 'LONG'])
        bearish_count = len([s for s in cot_signals if s['direction'] == 'SHORT'])

        if bullish_count > bearish_count:
            return 'LONG'
        elif bearish_count > bullish_count:
            return 'SHORT'
        else:
            return 'NEUTRAL'

    def recommend_action(self, total_score: int, consensus: str) -> str:
        """Generate recommended action based on score and consensus"""
        if total_score >= 85:
            return f'STRONG_{consensus}'
        elif total_score >= 70:
            return consensus
        elif total_score >= 50:
            return 'WATCHLIST'
        else:
            return 'AVOID'

    def grade_score(self, score: int) -> str:
        """Convert numeric score to letter grade"""
        if score >= 95:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 85:
            return 'B+'
        elif score >= 80:
            return 'B'
        elif score >= 75:
            return 'C+'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

    def store_confluence_score(self, score: Dict):
        """Store confluence score to database"""
        try:
            cursor = self.db_conn.cursor()

            cursor.execute("""
                INSERT INTO confluence_scores (
                    score_date, symbol, total_score, score_grade,
                    cot_score, seasonal_score,
                    num_bullish_signals, num_bearish_signals,
                    consensus_direction, recommended_action,
                    calculated_by_agent
                )
                VALUES (NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (score_date, symbol)
                DO UPDATE SET
                    total_score = EXCLUDED.total_score,
                    score_grade = EXCLUDED.score_grade,
                    cot_score = EXCLUDED.cot_score,
                    seasonal_score = EXCLUDED.seasonal_score,
                    num_bullish_signals = EXCLUDED.num_bullish_signals,
                    num_bearish_signals = EXCLUDED.num_bearish_signals,
                    consensus_direction = EXCLUDED.consensus_direction,
                    recommended_action = EXCLUDED.recommended_action
            """, (
                score['symbol'],
                score['total_score'],
                score['score_grade'],
                score['cot_score'],
                score['seasonal_score'],
                score['num_bullish_signals'],
                score['num_bearish_signals'],
                score['consensus_direction'],
                score['recommended_action'],
                self.agent_id
            ))

            self.db_conn.commit()
            cursor.close()

            self.logger.info(f"✅ Stored confluence score for {score['symbol']}: {score['total_score']}/100 ({score['score_grade']})")

        except Exception as e:
            self.logger.error(f"❌ Error storing confluence score: {e}")
            self.db_conn.rollback()

    def run(self):
        """Main execution loop - override in subclasses"""
        raise NotImplementedError("Subclass must implement run() method")

    def __del__(self):
        """Cleanup database connection"""
        if self.db_conn:
            self.db_conn.close()
