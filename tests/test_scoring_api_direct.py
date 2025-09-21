"""
採点API直接テスト
"""
import pytest
import asyncio
import httpx

# 実際のIPA PM試験問題（令和5年度春期）
IPA_PM_QUESTION_DATA = {
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
    "model_answer": """1. 品質計画の策定
要件定義書、設計書の品質基準を明確化し、レビュー観点と合格基準を設定する。また、テスト計画書において単体テスト、結合テスト、システムテストの品質目標値を定義する。

2. 品質保証活動の実施
各工程でのレビューを実施し、要件定義レビュー、設計レビュー、コードレビューを行う。特に在庫管理機能の追加により既存機能への影響範囲を明確にし、回帰テストを含む包括的なテスト計画を策定する。

3. 品質管理とモニタリング
開発工程での不具合発見率、テスト工程での不具合密度を測定し、品質目標との乖離を監視する。また、ユーザー受入テストでの不具合件数を追跡し、稼働後の品質レベルを予測する。""",
    "points": 25,
    "max_chars": 400,
    "grading_intention": "プロジェクトマネージャとしての品質マネジメントに関する知識と、具体的なプロジェクト状況を踏まえた実践的な活動の提案能力を評価する",
    "grading_commentary": "在庫管理機能追加というプロジェクト背景を考慮し、既存システムとの整合性確保や回帰テストの重要性を言及できているかを特に評価する",
    "keywords": "品質計画,品質保証,品質管理,レビュー,テスト,品質目標,不具合管理,回帰テスト"
}

SAMPLE_ANSWER = """1. 品質計画の策定
在庫管理機能追加に伴う品質目標を設定し、既存システムとの整合性確保を含む品質基準を明確化する。レビュー基準と合格ラインを事前に定義する。

2. 段階的品質保証
要件定義、設計、実装の各段階でレビューを実施。特に既存の販売管理システムとの連携部分について重点的な検証を行い、回帰テストを含む包括的テスト計画を策定する。

3. 品質監視と改善
開発進捗に応じた品質メトリクス（不具合密度、レビュー指摘事項数）を継続監視し、品質目標からの乖離時は即座に是正措置を実施する。"""

class TestScoringAPIDirect:
    """採点API直接テスト"""

    @pytest.mark.asyncio
    async def test_scoring_api_endpoints(self):
        """採点API直接エンドポイントテスト"""

        async with httpx.AsyncClient() as client:

            print("[OK] 採点API直接テスト開始")

            # 1. API情報確認
            try:
                response = await client.get("http://localhost:8000/api/scoring/")
                assert response.status_code == 200
                api_info = response.json()
                print(f"[OK] API情報取得成功: {api_info['message']}")
            except Exception as e:
                print(f"[ERROR] API情報取得失敗: {e}")
                return

            # 2. 解答提出
            submission_data = {
                "exam_id": 1,
                "question_id": 1,
                "candidate_id": "TEST001",
                "answer_text": SAMPLE_ANSWER
            }

            try:
                response = await client.post(
                    "http://localhost:8000/api/scoring/submit",
                    json=submission_data
                )
                assert response.status_code == 200
                answer_response = response.json()
                answer_id = answer_response["id"]
                print(f"[OK] 解答提出成功: answer_id = {answer_id}")
                print(f"    受験者ID: {answer_response['candidate_id']}")
                print(f"    文字数: {answer_response['char_count']}")
            except Exception as e:
                print(f"[ERROR] 解答提出失敗: {e}")
                return

            # 3. AI採点実行
            evaluation_data = {
                "answer_id": answer_id
            }

            try:
                response = await client.post(
                    "http://localhost:8000/api/scoring/evaluate",
                    json=evaluation_data
                )
                print(f"[INFO] AI採点レスポンス: status={response.status_code}")
                if response.status_code == 200:
                    scoring_result = response.json()
                    print(f"[OK] AI採点実行成功:")
                    print(f"    総合得点: {scoring_result['total_score']}/{scoring_result['max_score']}")
                    print(f"    達成率: {scoring_result['percentage']:.1f}%")
                    print(f"    信頼度: {scoring_result['confidence']:.3f}")
                    print(f"    評価: {scoring_result['grade']}")
                    print(f"    採点状況: {scoring_result['status']}")
                else:
                    error_content = response.text
                    print(f"[ERROR] AI採点失敗: {error_content}")
            except Exception as e:
                print(f"[ERROR] AI採点実行失敗: {e}")

            print("[OK] 採点API直接テスト完了")

if __name__ == "__main__":
    asyncio.run(TestScoringAPIDirect().test_scoring_api_endpoints())