"""
採点統合クラス
"""
import asyncio
from typing import Dict, Any, List
import logging
import numpy as np

from .rule_based import RuleBasedScoring
from .semantic import SemanticScoring
from .comprehensive import ComprehensiveScoring
from ..config import settings

logger = logging.getLogger(__name__)


class ScoringIntegrator:
    """採点統合クラス"""

    def __init__(self):
        self.rule_based = RuleBasedScoring()
        self.semantic = SemanticScoring()
        self.comprehensive = ComprehensiveScoring()

        # 重み設定（設計書に従う）
        self.weights = {
            "rule_based": 0.3,
            "semantic": 0.4,
            "comprehensive": 0.3
        }

    async def score(self, answer_text: str, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """統合採点実行"""
        try:
            # 各採点手法を並行実行
            rule_result, semantic_result, comprehensive_result = await asyncio.gather(
                self._run_rule_based(answer_text, question_data),
                self._run_semantic(answer_text, question_data),
                self._run_comprehensive(answer_text, question_data),
                return_exceptions=True
            )

            # エラーハンドリング
            if isinstance(rule_result, Exception):
                logger.error(f"ルールベース採点エラー: {rule_result}")
                rule_result = self._get_fallback_result(question_data)

            if isinstance(semantic_result, Exception):
                logger.error(f"意味理解採点エラー: {semantic_result}")
                semantic_result = self._get_fallback_result(question_data)

            if isinstance(comprehensive_result, Exception):
                logger.error(f"総合評価採点エラー: {comprehensive_result}")
                comprehensive_result = self._get_fallback_result(question_data)

            # スコア統合
            integrated_result = self._integrate_scores(
                rule_result, semantic_result, comprehensive_result, question_data
            )

            return integrated_result

        except Exception as e:
            logger.error(f"統合採点エラー: {e}")
            return self._get_emergency_fallback(question_data)

    async def _run_rule_based(self, answer_text: str, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """ルールベース採点実行"""
        return self.rule_based.score(answer_text, question_data)

    async def _run_semantic(self, answer_text: str, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """意味理解採点実行"""
        return self.semantic.score(answer_text, question_data)

    async def _run_comprehensive(self, answer_text: str, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """総合評価採点実行"""
        return self.comprehensive.score(answer_text, question_data)

    def _integrate_scores(
        self,
        rule_result: Dict[str, Any],
        semantic_result: Dict[str, Any],
        comprehensive_result: Dict[str, Any],
        question_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """スコア統合"""
        points = question_data.get("points", 100)

        # 各手法のスコア取得
        rule_score = rule_result.get("score", 0)
        semantic_score = semantic_result.get("score", 0)
        comprehensive_score = comprehensive_result.get("score", 0)

        # 重み付き平均
        total_score = (
            rule_score * self.weights["rule_based"] +
            semantic_score * self.weights["semantic"] +
            comprehensive_score * self.weights["comprehensive"]
        )

        # 信頼度計算
        scores = [
            rule_result.get("percentage", 0) / 100,
            semantic_result.get("percentage", 0) / 100,
            comprehensive_result.get("percentage", 0) / 100
        ]

        confidence = self._calculate_confidence(scores)
        percentage = (total_score / points) * 100

        # 統合された採点理由
        all_reasons = []
        all_reasons.extend(rule_result.get("reasons", []))
        all_reasons.extend(semantic_result.get("reasons", []))
        all_reasons.extend(comprehensive_result.get("reasons", []))

        # 改善提案生成
        suggestions = self._generate_suggestions(
            rule_result, semantic_result, comprehensive_result
        )

        return {
            "total_score": total_score,
            "max_score": points,
            "percentage": percentage,
            "confidence": confidence,
            "rule_based_score": rule_score,
            "semantic_score": semantic_score,
            "comprehensive_score": comprehensive_score,
            "details": {
                "rule_based": rule_result.get("details", {}),
                "semantic": semantic_result.get("details", {}),
                "comprehensive": comprehensive_result.get("details", {}),
                "integration": {
                    "weights": self.weights,
                    "method": "weighted_average"
                }
            },
            "reasons": all_reasons,
            "suggestions": suggestions,
            "model_name": "integrated_scoring_engine",
            "temperature": settings.TEMPERATURE,
            "tokens_used": 0  # モック実装のため
        }

    def _calculate_confidence(self, scores: List[float]) -> float:
        """信頼度計算"""
        if not scores or len(scores) < 2:
            return 0.5

        # スコアの分散を計算
        variance = np.var(scores)

        # 分散が小さいほど信頼度が高い
        # 最大分散は0.25（0と1の間の分散）なので、それで正規化
        max_variance = 0.25
        confidence = 1 - min(variance / max_variance, 1.0)

        # 最低信頼度を0.3、最高を0.9に調整
        confidence = 0.3 + (confidence * 0.6)

        return round(confidence, 2)

    def _generate_suggestions(
        self,
        rule_result: Dict[str, Any],
        semantic_result: Dict[str, Any],
        comprehensive_result: Dict[str, Any]
    ) -> List[str]:
        """改善提案生成"""
        suggestions = []

        # 各スコアの評価に基づく提案
        rule_score = rule_result.get("percentage", 0)
        semantic_score = semantic_result.get("percentage", 0)
        comprehensive_score = comprehensive_result.get("percentage", 0)

        if rule_score < 60:
            suggestions.append("キーワードをより多く含めることを検討してください")
            suggestions.append("文字数制限を意識して回答してください")

        if semantic_score < 60:
            suggestions.append("出題趣旨により適合した内容を心がけてください")
            suggestions.append("論理的な文章構成を意識してください")

        if comprehensive_score < 60:
            suggestions.append("プロジェクトマネジメントの観点を強化してください")
            suggestions.append("より実務的で具体的な内容を含めてください")

        # 全体的なスコアが低い場合
        avg_score = (rule_score + semantic_score + comprehensive_score) / 3
        if avg_score < 50:
            suggestions.append("模範解答を参考に、より包括的な回答を心がけてください")

        return suggestions

    def _get_fallback_result(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """フォールバック結果"""
        points = question_data.get("points", 100)
        return {
            "score": points * 0.5,  # 中間的なスコア
            "max_score": points,
            "percentage": 50,
            "confidence": 0.3,
            "details": {"method": "fallback"},
            "reasons": ["採点処理でエラーが発生したため、フォールバック結果を使用"]
        }

    def _get_emergency_fallback(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """緊急時フォールバック"""
        points = question_data.get("points", 100)
        return {
            "total_score": 0,
            "max_score": points,
            "percentage": 0,
            "confidence": 0,
            "rule_based_score": 0,
            "semantic_score": 0,
            "comprehensive_score": 0,
            "details": {"error": "統合採点システムエラー"},
            "reasons": ["採点システムでエラーが発生しました"],
            "suggestions": ["システム管理者に連絡してください"],
            "model_name": "emergency_fallback",
            "temperature": None,
            "tokens_used": 0
        }