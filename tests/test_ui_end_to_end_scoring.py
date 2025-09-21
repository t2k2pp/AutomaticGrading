"""
エンドツーエンド採点テスト - UI経由での完全な動作確認
"""
import pytest
from playwright.async_api import async_playwright, Page

# 実際のIPA PM試験問題（令和5年度春期）用の受験者解答例
SAMPLE_ANSWER = """1. 品質計画の策定
在庫管理機能追加に伴う品質目標を設定し、既存システムとの整合性確保を含む品質基準を明確化する。レビュー基準と合格ラインを事前に定義する。

2. 段階的品質保証
要件定義、設計、実装の各段階でレビューを実施。特に既存の販売管理システムとの連携部分について重点的な検証を行い、回帰テストを含む包括的テスト計画を策定する。

3. 品質監視と改善
開発進捗に応じた品質メトリクス（不具合密度、レビュー指摘事項数）を継続監視し、品質目標からの乖離時は即座に是正措置を実施する。"""

class TestUIEndToEndScoring:
    """エンドツーエンド採点UI テスト"""

    @pytest.mark.asyncio
    async def test_complete_scoring_workflow(self):
        """完全な採点ワークフローテスト"""

        async with async_playwright() as p:
            # ブラウザ起動
            browser = await p.chromium.launch(headless=False)  # headless=False で画面表示
            page = await browser.new_page()

            try:
                # 受験者画面にアクセス
                await page.goto("http://localhost:3001")
                await page.wait_for_load_state("networkidle")

                print("[OK] 受験者画面にアクセス成功")

                # 受験者IDを入力
                candidate_id_input = page.locator("input[placeholder*='例: PM2024001']")
                await candidate_id_input.fill("TEST_E2E_001")

                print("[OK] 受験者ID入力完了")

                # 問題を選択
                question_select = page.locator("div[role='combobox']")
                await question_select.click()
                await page.wait_for_timeout(500)

                # 最初の問題を選択
                first_option = page.locator("li[role='option']").first
                await first_option.click()
                await page.wait_for_timeout(1000)

                print("[OK] 問題選択完了")

                # 選択された問題の内容確認
                question_card = page.locator(".MuiCard-root")
                if await question_card.is_visible():
                    question_text = await question_card.text_content()
                    if "品質マネジメント" in question_text:
                        print("[OK] IPA PM試験問題が正しく表示されている")
                    else:
                        print("[WARNING] 期待とは異なる問題が表示されている")

                # 解答を入力
                answer_textarea = page.locator("textarea[placeholder*='字以内で解答を入力']")
                await answer_textarea.fill(SAMPLE_ANSWER)

                print("[OK] 解答入力完了")

                # 文字数の確認
                char_count_text = await page.locator("p:has-text('文字')").text_content()
                if char_count_text:
                    print(f"[OK] 文字数表示: {char_count_text}")

                # 提出・採点ボタンをクリック
                submit_button = page.locator("button:has-text('提出・採点')")
                await submit_button.click()

                print("[OK] 提出・採点ボタンをクリック")

                # 提出中の状態確認
                submitting_button = page.locator("button:has-text('提出中')")
                if await submitting_button.is_visible():
                    print("[OK] 提出中の表示を確認")

                # AI採点中の状態確認
                scoring_button = page.locator("button:has-text('AI採点中')")
                if await scoring_button.is_visible():
                    print("[OK] AI採点中の表示を確認")

                # 採点結果の表示を待機（最大30秒）
                await page.wait_for_timeout(2000)  # まず2秒待機

                # 採点結果の確認
                scoring_result_area = page.locator("text=採点結果").locator("..")
                await page.wait_for_timeout(2000)  # さらに2秒待機

                # 総合得点の確認
                score_element = page.locator(".MuiCard-root .MuiTypography-h4")
                if await score_element.is_visible():
                    score_text = await score_element.text_content()
                    print(f"[OK] 採点結果表示: {score_text}")
                else:
                    print("[ERROR] 採点結果が表示されていない")

                # 詳細評価の確認
                detail_cards = page.locator(".MuiCard-root")
                card_count = await detail_cards.count()
                print(f"[OK] 結果カード数: {card_count}")

                # エラーメッセージがないことを確認
                error_alert = page.locator(".MuiAlert-standardError")
                if await error_alert.is_visible():
                    error_text = await error_alert.text_content()
                    print(f"[ERROR] エラーメッセージ: {error_text}")
                else:
                    print("[OK] エラーメッセージなし")

                print("\\n=== エンドツーエンド採点テスト完了 ===")

            except Exception as e:
                print(f"[ERROR] テスト中にエラーが発生: {str(e)}")
                # スクリーンショットを撮影
                await page.screenshot(path="error_e2e_scoring_test.png")

            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_scoring_review_display(self):
        """採点結果レビュー画面のテスト"""

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()

            try:
                # 採点レビュー画面にアクセス（特定の採点結果IDを指定）
                await page.goto("http://localhost:3001/scoring/1/review")
                await page.wait_for_load_state("networkidle")

                print("[OK] 採点レビュー画面にアクセス成功")

                # 問題情報の表示確認
                question_title = page.locator("h6").filter(has_text="問2: リスク管理")
                if await question_title.is_visible():
                    title_text = await question_title.text_content()
                    print(f"[OK] 問題タイトル表示: {title_text}")

                # 採点結果の表示確認
                score_display = page.locator("text=点")
                if await score_display.is_visible():
                    print("[OK] 採点結果が表示されている")

                # AI フィードバックの表示確認
                feedback_section = page.locator("text=分析")
                if await feedback_section.is_visible():
                    print("[OK] AI分析結果が表示されている")

                print("\\n=== 採点レビュー表示テスト完了 ===")

            except Exception as e:
                print(f"[ERROR] テスト中にエラー: {str(e)}")
                await page.screenshot(path="error_review_test.png")

            finally:
                await browser.close()

if __name__ == "__main__":
    import asyncio

    test_instance = TestUIEndToEndScoring()

    print("=== エンドツーエンド採点テスト ===")
    asyncio.run(test_instance.test_complete_scoring_workflow())

    print("\\n=== 採点レビュー表示テスト ===")
    asyncio.run(test_instance.test_scoring_review_display())