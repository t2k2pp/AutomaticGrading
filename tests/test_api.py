"""
API自動テスト
詳細化されたAI採点プロンプトのテスト
"""
import pytest
import httpx
import asyncio
from typing import Dict, Any


class TestScoringAPI:
    """採点API自動テスト"""

    BASE_URL = "http://localhost:8000"

    @pytest.fixture
    def client(self):
        """HTTPクライアント"""
        return httpx.Client(base_url=self.BASE_URL)

    def test_answer_submission(self, client):
        """解答提出テスト"""
        payload = {
            "exam_id": 1,
            "question_id": 1,
            "candidate_id": "AUTO_TEST_001",
            "answer_text": "プロジェクト開始前のリスク分析が形式的で、メンバーの技術レベル把握が不十分だった。設計レビューで品質チェックプロセスが機能せず課題発見が遅れた。"
        }

        response = client.post("/api/scoring/submit", json=payload)

        assert response.status_code == 200
        data = response.json()

        # レスポンス構造の確認
        assert "id" in data
        assert "candidate_id" in data
        assert "answer_text" in data
        assert "char_count" in data
        assert data["candidate_id"] == payload["candidate_id"]
        assert data["answer_text"] == payload["answer_text"]

        return data["id"]  # 後続テストで使用

    def test_detailed_ai_scoring(self, client):
        """詳細化AI採点テスト"""
        # まず解答を提出
        answer_id = self.test_answer_submission(client)

        # AI採点実行
        eval_payload = {"answer_id": answer_id}
        response = client.post("/api/scoring/evaluate", json=eval_payload)

        assert response.status_code == 200
        data = response.json()

        # 基本採点結果の確認
        assert "total_score" in data
        assert "aspect_scores" in data
        assert "confidence" in data
        assert 0 <= data["total_score"] <= 25
        assert 0.0 <= data["confidence"] <= 1.0

        # 詳細化された根拠情報の確認
        self._verify_detailed_analysis(data)
        self._verify_aspect_reasoning(data)
        self._verify_improvement_suggestions(data)
        self._verify_attention_points(data)

        return data

    def _verify_detailed_analysis(self, data: Dict[str, Any]):
        """詳細分析の検証"""
        if "detailed_analysis" in data and data["detailed_analysis"]:
            analysis = data["detailed_analysis"]
            assert "strengths" in analysis
            assert "weaknesses" in analysis
            assert "missing_elements" in analysis
            assert "specific_issues" in analysis

            # リスト形式であることを確認
            assert isinstance(analysis["strengths"], list)
            assert isinstance(analysis["weaknesses"], list)
            assert isinstance(analysis["missing_elements"], list)
            assert isinstance(analysis["specific_issues"], list)

    def _verify_aspect_reasoning(self, data: Dict[str, Any]):
        """観点別詳細評価の検証"""
        if "aspect_reasoning" in data and data["aspect_reasoning"]:
            reasoning = data["aspect_reasoning"]

            # 各観点の詳細情報を確認
            for aspect, details in reasoning.items():
                assert "score" in details
                assert "reasoning" in details
                assert "evidence" in details
                # deduction_pointsはオプショナル

                assert isinstance(details["score"], (int, float))
                assert 0 <= details["score"] <= 5
                assert isinstance(details["reasoning"], str)
                assert isinstance(details["evidence"], str)

    def _verify_improvement_suggestions(self, data: Dict[str, Any]):
        """改善提案の検証"""
        if "improvement_suggestions" in data and data["improvement_suggestions"]:
            suggestions = data["improvement_suggestions"]
            assert isinstance(suggestions, list)
            # 各提案が文字列であることを確認
            for suggestion in suggestions:
                assert isinstance(suggestion, str)
                assert len(suggestion) > 0

    def _verify_attention_points(self, data: Dict[str, Any]):
        """注意点の検証"""
        if "attention_points" in data and data["attention_points"]:
            points = data["attention_points"]
            assert isinstance(points, list)
            # 各注意点が文字列であることを確認
            for point in points:
                assert isinstance(point, str)
                assert len(point) > 0

    def test_confidence_reasoning(self, client):
        """採点確信度の根拠テスト"""
        answer_id = self.test_answer_submission(client)

        eval_payload = {"answer_id": answer_id}
        response = client.post("/api/scoring/evaluate", json=eval_payload)

        assert response.status_code == 200
        data = response.json()

        # 確信度根拠の確認
        if "confidence_reasoning" in data and data["confidence_reasoning"]:
            reasoning = data["confidence_reasoning"]
            assert isinstance(reasoning, str)
            assert len(reasoning) > 0

        # 総合的採点理由の確認
        if "overall_reasoning" in data and data["overall_reasoning"]:
            overall = data["overall_reasoning"]
            assert isinstance(overall, str)
            assert len(overall) > 0

    def test_multiple_answers_scoring(self, client):
        """複数解答の採点一貫性テスト"""
        test_answers = [
            "リスク分析が不十分で、メンバーのスキル把握ができていなかった。",
            "プロジェクト計画段階でのリスク評価が形式的で実効性がなかった。",
            "チームメンバーの技術レベルを正確に把握せずプロジェクトを開始した。"
        ]

        results = []
        for i, answer in enumerate(test_answers):
            payload = {
                "exam_id": 1,
                "question_id": 1,
                "candidate_id": f"CONSISTENCY_TEST_{i+1:03d}",
                "answer_text": answer
            }

            # 解答提出
            submit_response = client.post("/api/scoring/submit", json=payload)
            assert submit_response.status_code == 200
            answer_id = submit_response.json()["id"]

            # AI採点
            eval_response = client.post("/api/scoring/evaluate", json={"answer_id": answer_id})
            assert eval_response.status_code == 200

            results.append(eval_response.json())

        # 採点結果の一貫性確認
        scores = [result["total_score"] for result in results]
        confidences = [result["confidence"] for result in results]

        # スコアが合理的な範囲内であることを確認
        assert all(0 <= score <= 25 for score in scores)
        assert all(0.0 <= conf <= 1.0 for conf in confidences)

        # 詳細分析が全て含まれていることを確認
        for result in results:
            self._verify_detailed_analysis(result)

        return results


@pytest.mark.asyncio
async def test_health_check():
    """ヘルスチェック（非同期）"""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get("/health/")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


if __name__ == "__main__":
    # 直接実行時の簡易テスト
    client = httpx.Client(base_url="http://localhost:8000")
    test_instance = TestScoringAPI()

    print("🧪 API自動テスト実行中...")

    try:
        # 解答提出テスト
        print("✅ 解答提出テスト")
        answer_id = test_instance.test_answer_submission(client)

        # 詳細AI採点テスト
        print("✅ 詳細AI採点テスト")
        result = test_instance.test_detailed_ai_scoring(client)

        print(f"📊 採点結果: {result['total_score']}/25点 (確信度: {result['confidence']:.2f})")

        if result.get("detailed_analysis"):
            analysis = result["detailed_analysis"]
            print(f"💪 優れた点: {len(analysis.get('strengths', []))}件")
            print(f"⚠️  改善点: {len(analysis.get('weaknesses', []))}件")

        print("✅ 全てのAPIテストが成功しました！")

    except Exception as e:
        print(f"❌ テスト失敗: {str(e)}")
        raise
    finally:
        client.close()