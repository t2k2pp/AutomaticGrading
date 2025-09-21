"""
UI読み込み問題のデバッグテスト
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_ui_loading():
    """UI読み込み問題をデバッグ"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # コンソールメッセージを監視
        console_messages = []
        def handle_console(msg):
            console_messages.append(f"[{msg.type}] {msg.text}")
            print(f"[CONSOLE {msg.type.upper()}] {msg.text}")

        page.on("console", handle_console)

        # ページエラーを監視
        page_errors = []
        def handle_error(error):
            page_errors.append(str(error))
            print(f"[PAGE ERROR] {error}")

        page.on("pageerror", handle_error)

        try:
            print("[INFO] 受験者画面にアクセス中...")
            await page.goto("http://localhost:3001")
            await page.wait_for_load_state("networkidle")

            print("[INFO] 5秒待機してReactの読み込みを確認...")
            await page.wait_for_timeout(5000)

            # ページソースの確認
            content = await page.content()
            if "root" in content:
                print("[OK] React root要素が存在")
            else:
                print("[ERROR] React root要素が見つからない")

            # React要素の確認
            react_elements = await page.locator("[data-reactroot], #root > *").count()
            print(f"[INFO] React要素数: {react_elements}")

            # 具体的なReactコンポーネントの確認
            navigation = await page.locator("nav, header").count()
            print(f"[INFO] ナビゲーション要素数: {navigation}")

            main_content = await page.locator("main, .MuiContainer-root").count()
            print(f"[INFO] メインコンテンツ要素数: {main_content}")

            # Material-UI要素の確認
            mui_elements = await page.locator("[class*='Mui']").count()
            print(f"[INFO] Material-UI要素数: {mui_elements}")

            # JavaScriptの実行確認
            js_result = await page.evaluate("() => window.React ? 'React loaded' : 'React not loaded'")
            print(f"[INFO] JavaScript実行結果: {js_result}")

            # 待機後の再確認
            print("[INFO] さらに10秒待機...")
            await page.wait_for_timeout(10000)

            final_elements = await page.locator("input, textarea, button").count()
            print(f"[INFO] 最終的なフォーム要素数: {final_elements}")

            # エラー集計
            print(f"\n[SUMMARY] コンソールメッセージ数: {len(console_messages)}")
            print(f"[SUMMARY] ページエラー数: {len(page_errors)}")

            if page_errors:
                print("[ERROR] ページエラー一覧:")
                for error in page_errors:
                    print(f"  - {error}")

        except Exception as e:
            print(f"[ERROR] テスト中にエラー: {str(e)}")
            await page.screenshot(path="debug_ui_loading.png")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_ui_loading())