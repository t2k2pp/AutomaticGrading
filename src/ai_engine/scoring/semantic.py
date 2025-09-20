"""
意味理解採点（モック実装）
"""
from typing import Dict, Any, List
import logging
import random

logger = logging.getLogger(__name__)


class SemanticScoring:
    """意味理解採点クラス（モック実装）"""

    def __init__(self):
        self.weight = 0.4  # 総合スコアでの重み

    def score(self, answer: str, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """意味理解採点実行（モック）"""
        try:
            model_answer = question_data.get("model_answer", "")
            grading_intention = question_data.get("grading_intention", "")
            points = question_data.get("points", 100)

            # モック実装: 実際のLLM/embedding処理の代わりに
            # 簡単な類似度計算とランダム要素を組み合わせ

            # 1. 語彙的類似度（簡易版）
            lexical_similarity = self._calculate_lexical_similarity(answer, model_answer)

            # 2. 意味的妥当性（モック）
            semantic_validity = self._mock_semantic_validity(answer, grading_intention)

            # 3. 論理的整合性（モック）
            logical_consistency = self._mock_logical_consistency(answer)

            # 総合スコア算出
            semantic_score = (
                lexical_similarity * 0.4 +
                semantic_validity * 0.4 +
                logical_consistency * 0.2
            )

            final_score = semantic_score * points

            details = {
                "lexical_similarity": lexical_similarity,
                "semantic_validity": semantic_validity,
                "logical_consistency": logical_consistency,
                "method": "mock_semantic_analysis"
            }

            return {
                "score": final_score,
                "max_score": points,
                "percentage": semantic_score * 100,
                "confidence": 0.7,  # モック実装なので中程度の信頼度
                "details": details,
                "reasons": self._generate_reasons(details)
            }

        except Exception as e:
            logger.error(f"意味理解採点エラー: {e}")
            return {
                "score": 0,
                "max_score": question_data.get("points", 100),
                "percentage": 0,
                "confidence": 0,
                "details": {"error": str(e)},
                "reasons": ["意味理解採点でエラーが発生しました"]
            }

    def _calculate_lexical_similarity(self, answer: str, model_answer: str) -> float:
        """語彙的類似度計算（簡易版）"""
        if not answer or not model_answer:
            return 0.0

        # 単語レベルでの重複計算
        answer_words = set(answer)
        model_words = set(model_answer)

        if not model_words:
            return 0.0

        intersection = answer_words & model_words
        similarity = len(intersection) / len(model_words)

        return min(similarity * 1.5, 1.0)  # 多少補正

    def _mock_semantic_validity(self, answer: str, grading_intention: str) -> float:
        """意味的妥当性評価（モック）"""
        # 実際の実装では、LLMを使用して出題趣旨との合致度を評価

        # 長さベースの簡易評価
        if len(answer) < 10:
            return 0.3
        elif len(answer) < 20:
            return 0.6
        else:
            return 0.8 + random.uniform(0, 0.2)  # 模擬的なバリエーション

    def _mock_logical_consistency(self, answer: str) -> float:
        """論理的整合性評価（モック）"""
        # 実際の実装では、論理構造の分析を行う

        score = 0.5  # 基本点

        # 論理的接続詞の存在
        logical_connectors = ["ため", "により", "したがって", "そのため", "結果"]
        if any(conn in answer for conn in logical_connectors):
            score += 0.2

        # 否定的・肯定的表現のバランス
        if "ない" in answer or "しない" in answer:
            score += 0.1

        # 具体性
        if "具体的" in answer or "例えば" in answer:
            score += 0.2

        return min(score, 1.0)

    def _generate_reasons(self, details: Dict[str, Any]) -> List[str]:
        """採点理由生成"""
        reasons = []

        # 語彙的類似度
        lex_sim = details.get("lexical_similarity", 0)
        if lex_sim > 0.7:
            reasons.append("模範解答との語彙的類似度が高い")
        elif lex_sim > 0.4:
            reasons.append("模範解答との語彙的類似度は中程度")
        else:
            reasons.append("模範解答との語彙的類似度が低い")

        # 意味的妥当性
        sem_val = details.get("semantic_validity", 0)
        if sem_val > 0.7:
            reasons.append("出題趣旨に適合している")
        elif sem_val > 0.4:
            reasons.append("出題趣旨にある程度適合している")
        else:
            reasons.append("出題趣旨との適合度が低い")

        # 論理的整合性
        log_cons = details.get("logical_consistency", 0)
        if log_cons > 0.7:
            reasons.append("論理的に整合性がある")
        elif log_cons > 0.4:
            reasons.append("論理的整合性はある程度保たれている")
        else:
            reasons.append("論理的整合性に課題がある")

        reasons.append("※意味理解採点はモック実装です")

        return reasons