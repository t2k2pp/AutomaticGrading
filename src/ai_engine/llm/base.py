"""
LLM統合の抽象化レイヤー
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from enum import Enum


class LLMProvider(str, Enum):
    """サポートするLLMプロバイダー"""
    LMSTUDIO = "lmstudio"
    OLLAMA = "ollama"
    GEMINI = "gemini"
    AZURE_OPENAI = "azure_openai"


class LLMResponse(BaseModel):
    """LLMからのレスポンス統一フォーマット"""
    content: str
    provider: LLMProvider
    model: str
    usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None


class ScoringCriteria(BaseModel):
    """採点基準"""
    question_text: str
    answer_text: str
    max_score: int = 25
    scoring_aspects: List[str] = [
        "問題理解の正確性",
        "論理的構成",
        "具体性・実践性",
        "PM知識の活用",
        "文章表現力"
    ]


class AspectDetail(BaseModel):
    """観点別詳細評価"""
    score: float
    reasoning: str
    evidence: str
    deduction_points: Optional[str] = None


class DetailedAnalysis(BaseModel):
    """詳細分析結果"""
    strengths: List[str]
    weaknesses: List[str]
    missing_elements: List[str]
    specific_issues: List[str]


class LLMScoring(BaseModel):
    """LLMによる採点結果（詳細版）"""
    total_score: float
    aspect_scores: Dict[str, float]

    # 従来の基本項目（後方互換性のため保持）
    detailed_feedback: str
    confidence: float
    reasoning: str

    # 新しい詳細項目
    detailed_analysis: Optional[DetailedAnalysis] = None
    aspect_reasoning: Optional[Dict[str, AspectDetail]] = None
    improvement_suggestions: Optional[List[str]] = None
    confidence_reasoning: Optional[str] = None
    overall_reasoning: Optional[str] = None
    attention_points: Optional[List[str]] = None


class BaseLLMProvider(ABC):
    """LLMプロバイダーの基底クラス"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_type = self._get_provider_type()

    @abstractmethod
    def _get_provider_type(self) -> LLMProvider:
        """プロバイダータイプを返す"""
        pass

    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs) -> LLMResponse:
        """テキスト生成"""
        pass

    @abstractmethod
    async def score_answer(self, criteria: ScoringCriteria) -> LLMScoring:
        """解答採点"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """ヘルスチェック"""
        pass

    def _build_scoring_prompt(self, criteria: ScoringCriteria) -> str:
        """採点用プロンプトを構築"""
        return f"""
あなたはIPAプロジェクトマネージャ試験の専門採点者です。
2次採点者が1次採点結果を適切に確認・修正できるよう、詳細な根拠と分析を提供してください。

【問題】
{criteria.question_text}

【受験者の解答】
{criteria.answer_text}

【採点基準】
以下の観点から評価してください：
{chr(10).join(f"- {aspect}" for aspect in criteria.scoring_aspects)}

【採点要求】
1. 各観点について、具体的な評価理由を明記
2. 減点箇所の詳細な説明
3. 解答の優れた点と改善点を明確に区別
4. 採点の根拠となる具体的箇所を引用
5. 2次採点者が判断しやすい構造化された分析

【出力形式】
JSON形式で以下を出力してください：
{{
    "total_score": 数値（0-25）,
    "aspect_scores": {{
        "問題理解の正確性": 数値（0-5）,
        "論理的構成": 数値（0-5）,
        "具体性・実践性": 数値（0-5）,
        "PM知識の活用": 数値（0-5）,
        "文章表現力": 数値（0-5）
    }},
    "detailed_analysis": {{
        "strengths": ["解答の優れた点1", "解答の優れた点2"],
        "weaknesses": ["改善が必要な点1", "改善が必要な点2"],
        "missing_elements": ["不足している要素1", "不足している要素2"],
        "specific_issues": ["具体的な問題箇所1", "具体的な問題箇所2"]
    }},
    "aspect_reasoning": {{
        "問題理解の正確性": {{
            "score": 数値（0-5）,
            "reasoning": "詳細な評価理由",
            "evidence": "根拠となる解答箇所の引用",
            "deduction_points": "減点理由（該当する場合）"
        }},
        "論理的構成": {{
            "score": 数値（0-5）,
            "reasoning": "詳細な評価理由",
            "evidence": "根拠となる解答箇所の引用",
            "deduction_points": "減点理由（該当する場合）"
        }},
        "具体性・実践性": {{
            "score": 数値（0-5）,
            "reasoning": "詳細な評価理由",
            "evidence": "根拠となる解答箇所の引用",
            "deduction_points": "減点理由（該当する場合）"
        }},
        "PM知識の活用": {{
            "score": 数値（0-5）,
            "reasoning": "詳細な評価理由",
            "evidence": "根拠となる解答箇所の引用",
            "deduction_points": "減点理由（該当する場合）"
        }},
        "文章表現力": {{
            "score": 数値（0-5）,
            "reasoning": "詳細な評価理由",
            "evidence": "根拠となる解答箇所の引用",
            "deduction_points": "減点理由（該当する場合）"
        }}
    }},
    "improvement_suggestions": ["改善提案1", "改善提案2", "改善提案3"],
    "confidence": 数値（0.0-1.0）,
    "confidence_reasoning": "採点確信度の根拠",
    "overall_reasoning": "総合的な採点理由と2次採点者への助言",
    "attention_points": ["2次採点時に特に注意すべき点1", "2次採点時に特に注意すべき点2"]
}}

※PMBOKガイドやIPAの採点基準に基づいて、厳格かつ公正に評価してください。
※2次採点者が迅速かつ正確に判断できるよう、明確で構造化された分析を提供してください。
"""


class LLMFactory:
    """LLMプロバイダーファクトリー"""

    _providers: Dict[LLMProvider, type] = {}

    @classmethod
    def register(cls, provider_type: LLMProvider, provider_class: type):
        """プロバイダーを登録"""
        cls._providers[provider_type] = provider_class

    @classmethod
    def create(cls, provider_type: LLMProvider, config: Dict[str, Any]) -> BaseLLMProvider:
        """プロバイダーインスタンスを作成"""
        if provider_type not in cls._providers:
            raise ValueError(f"未サポートのプロバイダー: {provider_type}")

        provider_class = cls._providers[provider_type]
        return provider_class(config)

    @classmethod
    def get_available_providers(cls) -> List[LLMProvider]:
        """利用可能なプロバイダー一覧を取得"""
        return list(cls._providers.keys())