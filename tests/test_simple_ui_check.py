"""
シンプルなUI動作確認テスト
"""
import asyncio
from playwright.async_api import async_playwright

async def simple_ui_test():
    """シンプルなUI確認"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        try:
            # 受験者画面にアクセス
            await page.goto("http://localhost:3001")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(10000)  # 10秒待機（Reactの読み込み完了を待つ）

            print("[OK] 受験者画面にアクセス成功")

            # ページのタイトル確認
            title = await page.title()
            print(f"[OK] ページタイトル: {title}")

            # 受験者IDフィールドをより広範囲に検索
            candidate_inputs = await page.locator("input").all()
            print(f"[INFO] 入力フィールド数: {len(candidate_inputs)}")

            for i, input_elem in enumerate(candidate_inputs):
                placeholder = await input_elem.get_attribute("placeholder")
                print(f"[INFO] 入力フィールド {i+1}: placeholder='{placeholder}'")

                if placeholder and "PM2024001" in placeholder:
                    await input_elem.fill("TEST_E2E_001")
                    print("[OK] 受験者ID入力完了")
                    break

            # Selectボックスの確認
            select_boxes = await page.locator("[role='combobox']").all()
            print(f"[INFO] 選択ボックス数: {len(select_boxes)}")

            if select_boxes:
                await select_boxes[0].click()
                await page.wait_for_timeout(1000)

                # オプションの確認
                options = await page.locator("[role='option']").all()
                print(f"[INFO] 選択肢数: {len(options)}")

                if options:
                    await options[0].click()
                    print("[OK] 問題選択完了")
                    await page.wait_for_timeout(2000)

            # テキストエリアの確認
            textareas = await page.locator("textarea").all()
            print(f"[INFO] テキストエリア数: {len(textareas)}")

            if textareas:
                sample_answer = "テスト解答です。これはエンドツーエンドテストのための解答文です。"
                await textareas[0].fill(sample_answer)
                print("[OK] 解答入力完了")

            # 提出ボタンの確認
            submit_buttons = await page.locator("button").all()
            print(f"[INFO] ボタン数: {len(submit_buttons)}")

            for button in submit_buttons:
                button_text = await button.text_content()
                if "提出" in button_text or "採点" in button_text:
                    print(f"[OK] 提出ボタン発見: {button_text}")
                    await button.click()
                    print("[OK] 提出ボタンクリック完了")
                    break

            # 結果待機
            await page.wait_for_timeout(5000)  # 5秒待機

            # 採点結果エリアの確認
            result_area = page.locator("text=採点結果")
            if await result_area.is_visible():
                print("[OK] 採点結果エリアが表示されている")

                # 点数表示の確認
                score_elements = await page.locator("text=/\\d+.*点/").all()
                for score_elem in score_elements:
                    score_text = await score_elem.text_content()
                    print(f"[OK] 得点表示: {score_text}")
            else:
                print("[INFO] 採点結果はまだ表示されていない")

            print("\\n=== シンプルUIテスト完了 ===")

        except Exception as e:
            print(f"[ERROR] テスト中にエラー: {str(e)}")
            await page.screenshot(path="error_simple_ui_test.png")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(simple_ui_test())