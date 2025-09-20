"""
React UI Playwrightテスト
ユーザー体験の自動テスト
"""
import pytest
from playwright.async_api import async_playwright, Page, Browser
import asyncio


class TestScoringUI:
    """採点UI自動テスト"""

    BASE_URL = "http://localhost:3002"

    @pytest.fixture
    async def browser(self):
        """ブラウザ起動"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # デバッグ時はheadless=False
            yield browser
            await browser.close()

    @pytest.fixture
    async def page(self, browser):
        """ページ作成"""
        page = await browser.new_page()
        yield page
        await page.close()

    async def test_answer_submission_flow(self, page: Page):
        """解答提出フロー全体テスト"""
        # トップページアクセス
        await page.goto(self.BASE_URL)
        await page.wait_for_load_state("networkidle")

        # 解答・採点ページに移動
        await page.click('text="解答・採点"')
        await page.wait_for_load_state("networkidle")

        # フォーム入力
        candidate_id = "UI_AUTO_TEST_001"
        answer_text = "プロジェクト開始前のリスク分析が形式的で、メンバーの技術レベル把握が不十分だった。設計レビューで品質チェックプロセスが機能せず課題発見が遅れた。"

        # 受験者ID入力
        await page.fill('input[placeholder*="例: PM2024001"]', candidate_id)

        # 問題選択（デフォルトの問題1を使用）
        problem_selector = page.locator('div[role="combobox"]').first()
        await problem_selector.click()
        await page.click('text="問題1: リスク管理"')

        # 解答入力
        await page.fill('textarea[placeholder*="40字以内で解答"]', answer_text)

        # 文字数確認
        char_count = await page.locator('text*="字"').text_content()
        assert "31/40文字" in char_count  # 正確な文字数カウント

        # 提出・採点ボタンクリック
        submit_button = page.locator('button:has-text("提出・採点")')
        await submit_button.click()

        # 採点結果の表示を待機
        await page.wait_for_selector('text*="採点結果"', timeout=30000)

        # 採点結果の検証
        await self._verify_scoring_results(page)

        return True

    async def _verify_scoring_results(self, page: Page):
        """採点結果の検証"""
        # スコア表示の確認
        score_element = page.locator('text*="点"').first()
        await score_element.wait_for(timeout=5000)

        # 詳細情報の表示確認
        details_elements = [
            'text*="問題理解の正確性"',
            'text*="論理的構成"',
            'text*="具体性・実践性"',
            'text*="PM知識の活用"',
            'text*="文章表現力"'
        ]

        for detail in details_elements:
            await page.wait_for_selector(detail, timeout=5000)

    async def test_input_validation(self, page: Page):
        """入力バリデーションテスト"""
        await page.goto(f"{self.BASE_URL}/answer")
        await page.wait_for_load_state("networkidle")

        # 文字数制限テスト
        long_text = "あ" * 50  # 40文字制限を超過
        await page.fill('textarea[placeholder*="40字以内"]', long_text)

        # 提出ボタンが無効になることを確認
        submit_button = page.locator('button:has-text("提出・採点")')
        await page.wait_for_timeout(1000)  # UI更新を待機

        is_disabled = await submit_button.is_disabled()
        assert is_disabled, "40文字を超える場合、提出ボタンが無効になるべき"

        # 文字数を適切に修正
        valid_text = "リスク評価不十分とメンバーのスキル不足により設計品質問題が発生"
        await page.fill('textarea[placeholder*="40字以内"]', valid_text)

        # 提出ボタンが有効になることを確認
        await page.wait_for_timeout(1000)
        is_enabled = not await submit_button.is_disabled()
        assert is_enabled, "40文字以内の場合、提出ボタンが有効になるべき"

    async def test_navigation_flow(self, page: Page):
        """ナビゲーション動作テスト"""
        await page.goto(self.BASE_URL)

        # 各ページへのナビゲーション確認
        navigation_tests = [
            ("ダッシュボード", "/"),
            ("解答・採点", "/answer"),
            ("採点一覧", "/scoring")
        ]

        for nav_text, expected_path in navigation_tests:
            await page.click(f'text="{nav_text}"')
            await page.wait_for_load_state("networkidle")

            current_url = page.url
            assert expected_path in current_url, f"{nav_text}ナビゲーションが正しく動作していない"

    async def test_responsive_design(self, page: Page):
        """レスポンシブデザインテスト"""
        await page.goto(f"{self.BASE_URL}/answer")

        # デスクトップサイズ
        await page.set_viewport_size({"width": 1200, "height": 800})
        await page.wait_for_timeout(500)

        # モバイルサイズ
        await page.set_viewport_size({"width": 375, "height": 667})
        await page.wait_for_timeout(500)

        # 主要要素が表示されることを確認
        main_elements = [
            'text="解答入力"',
            'input[placeholder*="受験者ID"]',
            'textarea[placeholder*="解答"]',
            'button:has-text("提出・採点")'
        ]

        for element in main_elements:
            is_visible = await page.locator(element).is_visible()
            assert is_visible, f"モバイルサイズで{element}が表示されていない"

    async def test_error_handling(self, page: Page):
        """エラーハンドリングテスト"""
        await page.goto(f"{self.BASE_URL}/answer")

        # 空の解答での提出試行
        await page.fill('input[placeholder*="受験者ID"]', "ERROR_TEST_001")
        # 解答を空のまま提出ボタンをクリック

        submit_button = page.locator('button:has-text("提出・採点")')
        is_disabled = await submit_button.is_disabled()
        assert is_disabled, "空の解答では提出ボタンが無効になるべき"

    async def test_accessibility(self, page: Page):
        """アクセシビリティテスト"""
        await page.goto(f"{self.BASE_URL}/answer")

        # キーボードナビゲーション
        await page.keyboard.press("Tab")  # 受験者ID
        await page.keyboard.press("Tab")  # 問題選択
        await page.keyboard.press("Tab")  # 解答入力

        # 現在のフォーカス要素が解答入力であることを確認
        focused_element = await page.evaluate("document.activeElement.tagName")
        assert focused_element in ["TEXTAREA", "INPUT"], "キーボードナビゲーションが適切に動作していない"

        # ARIA属性の確認
        form_elements = await page.locator('input, textarea, button').all()
        for element in form_elements:
            # 各要素にアクセシブルな名前があることを確認
            accessible_name = await element.get_attribute("aria-label") or await element.get_attribute("placeholder")
            assert accessible_name, "フォーム要素にアクセシブルな名前がない"


async def run_ui_tests():
    """UI自動テスト実行"""
    print("🎭 React UI 自動テスト実行中...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        test_instance = TestScoringUI()

        try:
            print("✅ 解答提出フロー全体テスト")
            await test_instance.test_answer_submission_flow(page)

            print("✅ 入力バリデーションテスト")
            await test_instance.test_input_validation(page)

            print("✅ ナビゲーション動作テスト")
            await test_instance.test_navigation_flow(page)

            print("✅ レスポンシブデザインテスト")
            await test_instance.test_responsive_design(page)

            print("✅ エラーハンドリングテスト")
            await test_instance.test_error_handling(page)

            print("✅ アクセシビリティテスト")
            await test_instance.test_accessibility(page)

            print("🎉 全てのUIテストが成功しました！")

        except Exception as e:
            print(f"❌ UIテスト失敗: {str(e)}")
            raise
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(run_ui_tests())