"""
ルールベース採点
"""
import re
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class RuleBasedScoring:
    """ルールベース採点クラス"""

    def __init__(self):
        self.weight = 0.3  # 総合スコアでの重み

    def score(self, answer: str, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """ルールベース採点実行"""
        try:
            model_answer = question_data.get("model_answer", "")
            keywords = question_data.get("keywords", [])
            max_chars = question_data.get("max_chars", 40)
            points = question_data.get("points", 100)

            # 基本スコア算出
            score = 0
            details = {}

            # 1. キーワードマッチング (60%)
            keyword_score, keyword_details = self._evaluate_keywords(answer, keywords)
            score += keyword_score * 0.6

            # 2. 文字数チェック (20%)
            length_score, length_details = self._evaluate_length(answer, max_chars)
            score += length_score * 0.2

            # 3. 必須要素チェック (20%)
            structure_score, structure_details = self._evaluate_structure(answer, model_answer)
            score += structure_score * 0.2

            # スコアの正規化
            final_score = min(score * points, points)

            details.update({
                "keyword_evaluation": keyword_details,
                "length_evaluation": length_details,
                "structure_evaluation": structure_details
            })

            return {
                "score": final_score,
                "max_score": points,
                "percentage": (final_score / points) * 100,
                "confidence": 0.8,  # ルールベースは高い信頼度
                "details": details,
                "reasons": self._generate_reasons(keyword_details, length_details, structure_details)
            }

        except Exception as e:
            logger.error(f"ルールベース採点エラー: {e}")
            return {
                "score": 0,
                "max_score": question_data.get("points", 100),
                "percentage": 0,
                "confidence": 0,
                "details": {"error": str(e)},
                "reasons": ["採点処理でエラーが発生しました"]
            }

    def _evaluate_keywords(self, answer: str, keywords: List[str]) -> tuple:
        """キーワード評価"""
        if not keywords:
            return 1.0, {"matched": [], "total": 0, "score": 1.0}

        matched_keywords = []
        for keyword in keywords:
            if keyword in answer:
                matched_keywords.append(keyword)

        match_ratio = len(matched_keywords) / len(keywords)

        # 段階的評価
        if match_ratio >= 0.8:
            score = 1.0
        elif match_ratio >= 0.6:
            score = 0.8
        elif match_ratio >= 0.4:
            score = 0.6
        elif match_ratio >= 0.2:
            score = 0.4
        else:
            score = 0.2

        return score, {
            "matched": matched_keywords,
            "total": len(keywords),
            "match_ratio": match_ratio,
            "score": score
        }

    def _evaluate_length(self, answer: str, max_chars: int) -> tuple:
        """文字数評価"""
        char_count = len(answer)

        if char_count == 0:
            return 0.0, {"char_count": 0, "max_chars": max_chars, "score": 0.0, "status": "empty"}

        if char_count <= max_chars:
            # 適切な長さ
            if char_count >= max_chars * 0.7:
                score = 1.0
                status = "optimal"
            elif char_count >= max_chars * 0.5:
                score = 0.9
                status = "good"
            else:
                score = 0.7
                status = "short"
        else:
            # 文字数超過
            excess_ratio = (char_count - max_chars) / max_chars
            if excess_ratio <= 0.1:
                score = 0.9
                status = "slightly_over"
            elif excess_ratio <= 0.3:
                score = 0.7
                status = "over"
            else:
                score = 0.5
                status = "significantly_over"

        return score, {
            "char_count": char_count,
            "max_chars": max_chars,
            "score": score,
            "status": status
        }

    def _evaluate_structure(self, answer: str, model_answer: str) -> tuple:
        """構造・論理性評価"""
        score = 0.5  # 基本点

        # 基本的な文構造チェック
        if self._has_proper_sentence_structure(answer):
            score += 0.2

        # 因果関係の表現チェック
        if self._has_causal_expressions(answer):
            score += 0.2

        # 専門用語の使用チェック
        if self._has_technical_terms(answer):
            score += 0.1

        return min(score, 1.0), {
            "has_proper_structure": self._has_proper_sentence_structure(answer),
            "has_causal_expressions": self._has_causal_expressions(answer),
            "has_technical_terms": self._has_technical_terms(answer),
            "score": min(score, 1.0)
        }

    def _has_proper_sentence_structure(self, text: str) -> bool:
        """適切な文構造かチェック"""
        # 句読点の使用
        if "、" in text or "。" in text:
            return True
        # 文末が適切か
        if text.endswith("。") or text.endswith("た。") or text.endswith("る。"):
            return True
        return False

    def _has_causal_expressions(self, text: str) -> bool:
        """因果関係表現のチェック"""
        causal_patterns = [
            "ため", "により", "によって", "原因", "理由", "結果",
            "したがって", "そのため", "なので", "ので"
        ]
        return any(pattern in text for pattern in causal_patterns)

    def _has_technical_terms(self, text: str) -> bool:
        """技術用語・専門用語のチェック"""
        technical_terms = [
            "プロジェクト", "システム", "開発", "設計", "要件", "テスト",
            "品質", "リスク", "マネジメント", "工程", "レビュー", "検証"
        ]
        return any(term in text for term in technical_terms)

    def _generate_reasons(self, keyword_details: Dict, length_details: Dict, structure_details: Dict) -> List[str]:
        """採点理由生成"""
        reasons = []

        # キーワード評価の理由
        kw = keyword_details
        if kw["total"] > 0:
            reasons.append(f"キーワード: {len(kw['matched'])}/{kw['total']}個マッチ")
            if kw["matched"]:
                reasons.append(f"マッチしたキーワード: {', '.join(kw['matched'])}")

        # 文字数評価の理由
        length = length_details
        if length["status"] == "optimal":
            reasons.append("文字数: 適切")
        elif length["status"] == "over":
            reasons.append(f"文字数: 超過 ({length['char_count']}/{length['max_chars']}字)")
        elif length["status"] == "short":
            reasons.append(f"文字数: やや短い ({length['char_count']}/{length['max_chars']}字)")

        # 構造評価の理由
        struct = structure_details
        if struct["has_causal_expressions"]:
            reasons.append("因果関係が明確")
        if struct["has_technical_terms"]:
            reasons.append("専門用語を適切に使用")

        return reasons