"""
IPA PM試験構造対応の動作テスト
実際のIPA PM試験問題構造を使用してテスト
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from src.ai_engine.llm.base import ScoringCriteria, LLMScoring, DetailedAnalysis
from src.ai_engine.llm.lmstudio import LMStudioProvider

# 実際のIPA PM試験問題（令和5年度春期）
IPA_PM_SAMPLE_QUESTION = {
    "question_number": "問1",
    "title": "プロジェクトの品質マネジメント",
    "background_text": """あなたは、A社のシステム開発部門に所属するプロジェクトマネージャである。
今回、顧客である B 社から、既存の販売管理システムの機能拡張を依頼された。

B 社の販売管理システムは、受注から売上計上までの業務を支援するシステムである。
システムの利用者は、営業部門の営業担当者 10 名、受注処理を行う受注担当者 3 名、
売上計上処理を行う経理担当者 2 名の合計 15 名である。

今回の機能拡張では、新たに在庫管理機能を追加することになった。
この機能は、商品の入庫、出庫、在庫照会を行うもので、倉庫担当者 5 名が利用する予定である。

プロジェクトの制約条件は以下のとおりである。
・開発期間：6 か月
・開発要員：A 社のシステムエンジニア 4 名、プログラマ 3 名
・予算：3,000 万円
・稼働開始予定日：来年 4 月 1 日（B 社の新会計年度開始日）""",
    "question_text": "このプロジェクトにおいて、品質マネジメントを適切に実施するために重要な活動を三つ挙げ、それぞれについて具体的な内容を述べよ。",
    "sub_questions": None,
    "model_answer": """1. 品質計画の策定
要件定義書、設計書の品質基準を明確化し、レビュー観点と合格基準を設定する。また、テスト計画書において単体テスト、結合テスト、システムテストの品質目標値を定義する。

2. 品質保証活動の実施
各工程でのレビューを実施し、要件定義レビュー、設計レビュー、コードレビューを行う。特に在庫管理機能の追加により既存機能への影響範囲を明確にし、回帰テストを含む包括的なテスト計画を策定する。

3. 品質管理とモニタリング
開発工程での不具合発見率、テスト工程での不具合密度を測定し、品質目標との乖離を監視する。また、ユーザー受入テストでの不具合件数を追跡し、稼働後の品質レベルを予測する。""",
    "grading_intention": "プロジェクトマネージャとしての品質マネジメントに関する知識と、具体的なプロジェクト状況を踏まえた実践的な活動の提案能力を評価する",
    "keywords": ["品質計画", "品質保証", "品質管理", "レビュー", "テスト", "品質目標", "不具合管理"],
    "max_chars": 400,
    "points": 25
}

# テスト用の受験者解答例
SAMPLE_ANSWERS = {
    "excellent": """1. 品質計画の策定
在庫管理機能追加に伴う品質目標を設定し、既存システムとの整合性確保を含む品質基準を明確化する。レビュー基準と合格ラインを事前に定義する。

2. 段階的品質保証
要件定義、設計、実装の各段階でレビューを実施。特に既存の販売管理システムとの連携部分について重点的な検証を行い、回帰テストを含む包括的テスト計画を策定する。

3. 品質監視と改善
開発進捗に応じた品質メトリクス（不具合密度、レビュー指摘事項数）を継続監視し、品質目標からの乖離時は即座に是正措置を実施する。""",

    "good": """1. テスト計画の作成
在庫管理機能のテスト計画を作成し、単体テスト、結合テスト、システムテストの内容を明確にする。

2. レビューの実施
設計書やプログラムのレビューを実施して品質を確保する。特に既存システムへの影響を重点的にチェックする。

3. 品質基準の設定
プロジェクトの品質目標を設定し、不具合件数の上限を決めて品質管理を行う。""",

    "poor": """品質管理をしっかりやることが大切です。テストをきちんと行い、バグを見つけて修正します。また、お客様の要望に応えられるように注意深く開発を進めます。"""
}

class TestIPAPMStructure:
    """IPA PM試験構造対応テスト"""

    @pytest.fixture
    def scoring_criteria(self):
        """採点基準のフィクスチャ"""
        return ScoringCriteria(
            question_text=IPA_PM_SAMPLE_QUESTION["question_text"],
            answer_text=SAMPLE_ANSWERS["excellent"],
            background_text=IPA_PM_SAMPLE_QUESTION["background_text"],
            question_number=IPA_PM_SAMPLE_QUESTION["question_number"],
            sub_questions=IPA_PM_SAMPLE_QUESTION.get("sub_questions"),
            model_answer=IPA_PM_SAMPLE_QUESTION["model_answer"],
            grading_intention=IPA_PM_SAMPLE_QUESTION["grading_intention"],
            max_score=IPA_PM_SAMPLE_QUESTION["points"]
        )

    def test_scoring_criteria_structure(self, scoring_criteria):
        """採点基準の構造テスト"""
        assert scoring_criteria.background_text is not None
        assert "A社のシステム開発部門" in scoring_criteria.background_text
        assert scoring_criteria.question_number == "問1"
        assert scoring_criteria.model_answer is not None
        assert scoring_criteria.grading_intention is not None
        assert "品質マネジメント" in scoring_criteria.grading_intention

    def test_build_scoring_prompt_with_background(self):
        """背景情報を含む採点プロンプト構築テスト"""
        from src.ai_engine.llm.base import BaseLLMProvider

        # テスト用の具象クラス作成
        class TestLLMProvider(BaseLLMProvider):
            def _get_provider_type(self):
                return "test"
            async def generate_response(self, prompt: str, **kwargs):
                pass
            async def score_answer(self, criteria: ScoringCriteria):
                pass
            async def health_check(self):
                return True

        provider = TestLLMProvider({})
        criteria = ScoringCriteria(
            question_text=IPA_PM_SAMPLE_QUESTION["question_text"],
            answer_text=SAMPLE_ANSWERS["excellent"],
            background_text=IPA_PM_SAMPLE_QUESTION["background_text"],
            question_number=IPA_PM_SAMPLE_QUESTION["question_number"],
            model_answer=IPA_PM_SAMPLE_QUESTION["model_answer"],
            grading_intention=IPA_PM_SAMPLE_QUESTION["grading_intention"]
        )

        prompt = provider._build_scoring_prompt(criteria)

        # 背景情報が含まれていることを確認
        assert "【背景情報・プロジェクト概要】" in prompt
        assert "A社のシステム開発部門" in prompt
        assert "販売管理システム" in prompt

        # 問題番号が含まれていることを確認
        assert "【問1】" in prompt

        # 設問が含まれていることを確認
        assert "【設問】" in prompt
        assert "品質マネジメントを適切に実施" in prompt

        # 模範解答が含まれていることを確認
        assert "【模範解答】" in prompt
        assert "品質計画の策定" in prompt

        # 出題趣旨が含まれていることを確認
        assert "【出題趣旨】" in prompt
        assert "品質マネジメントに関する知識" in prompt

    @pytest.mark.asyncio
    async def test_lmstudio_scoring_with_ipa_structure(self):
        """LMStudio での IPA 構造対応採点テスト"""
        config = {
            "base_url": "http://host.docker.internal:1234",
            "model": "gemma-3n-e4b-it-text",
            "temperature": 0.1,
            "max_tokens": 2000
        }

        provider = LMStudioProvider(config)

        # 優秀な解答のテスト
        criteria_excellent = ScoringCriteria(
            question_text=IPA_PM_SAMPLE_QUESTION["question_text"],
            answer_text=SAMPLE_ANSWERS["excellent"],
            background_text=IPA_PM_SAMPLE_QUESTION["background_text"],
            question_number=IPA_PM_SAMPLE_QUESTION["question_number"],
            model_answer=IPA_PM_SAMPLE_QUESTION["model_answer"],
            grading_intention=IPA_PM_SAMPLE_QUESTION["grading_intention"]
        )

        # モックレスポンスを使用（実際のAPI呼び出しをシミュレート）
        mock_response = {
            "total_score": 23,
            "aspect_scores": {
                "問題理解の正確性": 5,
                "論理的構成": 4,
                "具体性・実践性": 5,
                "PM知識の活用": 5,
                "文章表現力": 4
            },
            "detailed_analysis": {
                "strengths": [
                    "品質マネジメントの三つの主要活動を適切に特定している",
                    "プロジェクト背景を踏まえた具体的な提案ができている",
                    "在庫管理機能追加という状況を考慮した回帰テスト等の言及がある"
                ],
                "weaknesses": [
                    "品質メトリクスの具体的な数値目標が不明確"
                ],
                "missing_elements": [],
                "specific_issues": []
            },
            "confidence": 0.92,
            "overall_reasoning": "品質マネジメントの基本的な活動を適切に理解し、プロジェクト背景を考慮した実践的な提案ができている。"
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.score_answer(criteria_excellent)

            assert isinstance(result, LLMScoring)
            assert result.total_score >= 20  # 優秀な解答は高得点
            assert result.confidence > 0.8   # 高い信頼度
            assert result.detailed_analysis is not None
            assert len(result.detailed_analysis.strengths) > 0

    def test_question_model_properties(self):
        """問題モデルのプロパティテスト"""
        from src.api.models.question import Question

        # データベースモデルのプロパティをテスト
        question = Question(
            exam_id=1,
            title=IPA_PM_SAMPLE_QUESTION["title"],
            question_number=IPA_PM_SAMPLE_QUESTION["question_number"],
            background_text=IPA_PM_SAMPLE_QUESTION["background_text"],
            question_text=IPA_PM_SAMPLE_QUESTION["question_text"],
            sub_questions=IPA_PM_SAMPLE_QUESTION["sub_questions"],
            model_answer=IPA_PM_SAMPLE_QUESTION["model_answer"],
            max_chars=IPA_PM_SAMPLE_QUESTION["max_chars"],
            points=IPA_PM_SAMPLE_QUESTION["points"],
            grading_intention=IPA_PM_SAMPLE_QUESTION["grading_intention"]
        )

        # full_question_text プロパティのテスト
        full_text = question.full_question_text
        assert "【背景情報・プロジェクト概要】" in full_text
        assert "A社のシステム開発部門" in full_text
        assert "【設問】" in full_text
        assert "品質マネジメントを適切に実施" in full_text

        # has_sub_questions プロパティのテスト
        assert question.has_sub_questions == False  # sub_questions が None

        # display_name プロパティのテスト
        assert question.display_name == "問1: プロジェクトの品質マネジメント"

    @pytest.mark.parametrize("answer_quality,expected_min_score", [
        ("excellent", 20),
        ("good", 15),
        ("poor", 5)
    ])
    @pytest.mark.asyncio
    async def test_scoring_different_answer_qualities(self, answer_quality, expected_min_score):
        """異なる品質の解答の採点テスト"""
        config = {
            "base_url": "http://host.docker.internal:1234",
            "model": "gemma-3n-e4b-it-text"
        }

        provider = LMStudioProvider(config)

        criteria = ScoringCriteria(
            question_text=IPA_PM_SAMPLE_QUESTION["question_text"],
            answer_text=SAMPLE_ANSWERS[answer_quality],
            background_text=IPA_PM_SAMPLE_QUESTION["background_text"],
            question_number=IPA_PM_SAMPLE_QUESTION["question_number"],
            model_answer=IPA_PM_SAMPLE_QUESTION["model_answer"],
            grading_intention=IPA_PM_SAMPLE_QUESTION["grading_intention"]
        )

        # 品質に応じた期待スコアを設定
        expected_scores = {
            "excellent": 23,
            "good": 18,
            "poor": 8
        }

        mock_response = {
            "total_score": expected_scores[answer_quality],
            "aspect_scores": {
                "問題理解の正確性": 5 if answer_quality == "excellent" else 3 if answer_quality == "good" else 1,
                "論理的構成": 4 if answer_quality == "excellent" else 3 if answer_quality == "good" else 2,
                "具体性・実践性": 5 if answer_quality == "excellent" else 4 if answer_quality == "good" else 1,
                "PM知識の活用": 5 if answer_quality == "excellent" else 4 if answer_quality == "good" else 2,
                "文章表現力": 4 if answer_quality == "excellent" else 4 if answer_quality == "good" else 2
            },
            "confidence": 0.9 if answer_quality == "excellent" else 0.8 if answer_quality == "good" else 0.7
        }

        with patch.object(provider, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await provider.score_answer(criteria)

            assert result.total_score >= expected_min_score
            assert result.total_score == expected_scores[answer_quality]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])