"""
総合評価採点（モック実装）
"""
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class ComprehensiveScoring:
    """総合評価採点クラス（モック実装）"""

    def __init__(self):
        self.weight = 0.3  # 総合スコアでの重み

    def score(self, answer: str, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """総合評価採点実行（モック）"""
        try:
            points = question_data.get("points", 100)

            # 1. プロジェクトマネジメント観点での評価
            pm_perspective = self._evaluate_pm_perspective(answer)

            # 2. 実務的妥当性の評価
            practical_validity = self._evaluate_practical_validity(answer)

            # 3. 完全性の評価
            completeness = self._evaluate_completeness(answer, question_data)

            # 総合スコア算出
            comprehensive_score = (
                pm_perspective * 0.4 +
                practical_validity * 0.4 +
                completeness * 0.2
            )

            final_score = comprehensive_score * points

            details = {
                "pm_perspective": pm_perspective,
                "practical_validity": practical_validity,
                "completeness": completeness,
                "method": "mock_comprehensive_analysis"
            }

            return {
                "score": final_score,
                "max_score": points,
                "percentage": comprehensive_score * 100,
                "confidence": 0.6,  # モック実装なので中程度の信頼度
                "details": details,
                "reasons": self._generate_reasons(details)
            }

        except Exception as e:
            logger.error(f"総合評価採点エラー: {e}")
            return {
                "score": 0,
                "max_score": question_data.get("points", 100),
                "percentage": 0,
                "confidence": 0,
                "details": {"error": str(e)},
                "reasons": ["総合評価採点でエラーが発生しました"]
            }

    def _evaluate_pm_perspective(self, answer: str) -> float:
        """プロジェクトマネジメント観点での評価"""
        score = 0.3  # 基本点

        # PM用語の使用
        pm_terms = [
            "プロジェクト", "マネジメント", "ステークホルダー", "リスク",
            "スケジュール", "品質", "コスト", "スコープ", "要件",
            "工程", "フェーズ", "マイルストーン", "レビュー"
        ]

        term_count = sum(1 for term in pm_terms if term in answer)
        if term_count >= 3:
            score += 0.4
        elif term_count >= 2:
            score += 0.3
        elif term_count >= 1:
            score += 0.2

        # 管理的視点の表現
        management_expressions = [
            "管理", "計画", "統制", "監視", "制御", "調整",
            "予防", "対策", "改善", "最適化"
        ]

        if any(expr in answer for expr in management_expressions):
            score += 0.2

        # 問題解決の視点
        problem_solving = [
            "原因", "要因", "解決", "対応", "改善", "防止"
        ]

        if any(ps in answer for ps in problem_solving):
            score += 0.1

        return min(score, 1.0)

    def _evaluate_practical_validity(self, answer: str) -> float:
        """実務的妥当性の評価"""
        score = 0.4  # 基本点

        # 具体性
        concrete_expressions = [
            "具体的", "明確", "詳細", "例えば", "実際に",
            "現実的", "実用的", "実践的"
        ]

        if any(expr in answer for expr in concrete_expressions):
            score += 0.2

        # 実装可能性
        implementation_terms = [
            "実施", "実行", "導入", "適用", "運用", "活用"
        ]

        if any(term in answer for term in implementation_terms):
            score += 0.2

        # 定量的要素
        quantitative_indicators = [
            "時間", "工数", "コスト", "期間", "工期", "人数",
            "頻度", "回数", "割合", "率"
        ]

        if any(indicator in answer for indicator in quantitative_indicators):
            score += 0.2

        return min(score, 1.0)

    def _evaluate_completeness(self, answer: str, question_data: Dict[str, Any]) -> float:
        """完全性の評価"""
        max_chars = question_data.get("max_chars", 40)
        char_count = len(answer)

        # 文字数に基づく完全性評価
        if char_count >= max_chars * 0.8:
            length_score = 1.0
        elif char_count >= max_chars * 0.6:
            length_score = 0.8
        elif char_count >= max_chars * 0.4:
            length_score = 0.6
        else:
            length_score = 0.3

        # 論理的完結性
        logical_completeness = 0.5

        # 文の終わり方
        if answer.endswith("。") or answer.endswith("た。") or answer.endswith("ため。"):
            logical_completeness += 0.3

        # 主語述語の関係
        if ("が" in answer or "は" in answer) and ("た" in answer or "る" in answer):
            logical_completeness += 0.2

        return (length_score + min(logical_completeness, 1.0)) / 2

    def _generate_reasons(self, details: Dict[str, Any]) -> List[str]:
        """採点理由生成"""
        reasons = []

        # PM観点
        pm_score = details.get("pm_perspective", 0)
        if pm_score > 0.7:
            reasons.append("プロジェクトマネジメントの観点から適切")
        elif pm_score > 0.4:
            reasons.append("プロジェクトマネジメントの観点から概ね適切")
        else:
            reasons.append("プロジェクトマネジメントの観点が不足")

        # 実務的妥当性
        practical_score = details.get("practical_validity", 0)
        if practical_score > 0.7:
            reasons.append("実務的に妥当な内容")
        elif practical_score > 0.4:
            reasons.append("実務的妥当性は概ね確保されている")
        else:
            reasons.append("実務的妥当性に課題がある")

        # 完全性
        completeness_score = details.get("completeness", 0)
        if completeness_score > 0.7:
            reasons.append("回答として完結している")
        elif completeness_score > 0.4:
            reasons.append("回答として概ね完結している")
        else:
            reasons.append("回答の完結性に課題がある")

        reasons.append("※総合評価採点はモック実装です")

        return reasons