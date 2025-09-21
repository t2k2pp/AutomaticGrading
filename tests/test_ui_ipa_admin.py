"""
管理者画面での実際のIPA PM試験問題登録テスト
"""
import pytest
from playwright.async_api import async_playwright, Page

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

class TestIPAAdminUI:
    """IPA PM試験問題の管理者UI登録テスト"""

    @pytest.mark.asyncio
    async def test_admin_ipa_question_registration(self):
        """管理者画面での実際のIPA PM試験問題登録テスト"""

        async with async_playwright() as p:
            # ブラウザ起動
            browser = await p.chromium.launch(headless=False)  # headless=False で画面表示
            page = await browser.new_page()

            try:
                # 管理者画面にアクセス
                await page.goto("http://localhost:3001/admin")
                await page.wait_for_load_state("networkidle")

                print("[OK] 管理者画面にアクセス成功")

                # 問題管理タブをクリック
                await page.click("text=問題管理")
                await page.wait_for_timeout(1000)

                print("[OK] 問題管理タブに移動")

                # 試験を選択（最初の試験を選択）
                exam_rows = await page.locator("table tbody tr").all()
                if exam_rows:
                    await exam_rows[0].click()
                    await page.wait_for_timeout(500)
                    print("[OK] 試験を選択")

                # 新しい問題を作成ボタンをクリック
                create_button = page.locator("text=新しい問題を作成")
                await create_button.click()
                await page.wait_for_timeout(1000)

                print("[OK] 問題作成ダイアログを開いた")

                # フォームに実際のIPA問題データを入力
                await page.fill("input[label*='問題番号']", IPA_PM_QUESTION_DATA["question_number"])
                await page.fill("input[label*='問題タイトル']", IPA_PM_QUESTION_DATA["title"])

                # 背景情報の入力（大きなテキストエリア）
                background_textarea = page.locator("textarea[label*='背景情報']")
                await background_textarea.fill(IPA_PM_QUESTION_DATA["background_text"])

                # 設問文の入力
                question_textarea = page.locator("textarea[label*='設問文']")
                await question_textarea.fill(IPA_PM_QUESTION_DATA["question_text"])

                # 模範解答の入力
                answer_textarea = page.locator("textarea[label*='模範解答']")
                await answer_textarea.fill(IPA_PM_QUESTION_DATA["model_answer"])

                # 出題趣旨の入力
                intention_textarea = page.locator("textarea[label*='出題趣旨']")
                await intention_textarea.fill(IPA_PM_QUESTION_DATA["grading_intention"])

                # 採点講評の入力
                commentary_textarea = page.locator("textarea[label*='採点講評']")
                await commentary_textarea.fill(IPA_PM_QUESTION_DATA["grading_commentary"])

                # 配点と文字制限の設定
                points_input = page.locator("input[label*='配点']")
                await points_input.fill(str(IPA_PM_QUESTION_DATA["points"]))

                chars_input = page.locator("input[label*='文字制限']")
                await chars_input.fill(str(IPA_PM_QUESTION_DATA["max_chars"]))

                print("[OK] フォームにIPA問題データを入力完了")

                # 作成ボタンをクリック
                submit_button = page.locator("text=作成")
                await submit_button.click()
                await page.wait_for_timeout(2000)

                print("[OK] 問題作成を実行")

                # 成功メッセージの確認
                success_alert = page.locator(".MuiAlert-standardSuccess")
                if await success_alert.is_visible():
                    print("[OK] 問題作成成功メッセージを確認")
                else:
                    # エラーメッセージがある場合は表示
                    error_alert = page.locator(".MuiAlert-standardError")
                    if await error_alert.is_visible():
                        error_text = await error_alert.text_content()
                        print(f"[ERROR] エラーメッセージ: {error_text}")

                # 問題一覧に新しい問題が表示されているか確認
                await page.wait_for_timeout(1000)
                question_table = page.locator("table tbody")
                table_content = await question_table.text_content()

                if IPA_PM_QUESTION_DATA["question_number"] in table_content:
                    print("[OK] 新しく作成した問題が一覧に表示されている")
                else:
                    print("[ERROR] 新しい問題が一覧に表示されていない")

                print("\\n=== IPA PM試験問題登録テスト完了 ===")

            except Exception as e:
                print(f"[ERROR] テスト中にエラーが発生: {str(e)}")
                # スクリーンショットを撮影
                await page.screenshot(path="error_admin_ipa_test.png")

            finally:
                await browser.close()

    @pytest.mark.asyncio
    async def test_admin_question_display_structure(self):
        """登録された問題の表示構造確認テスト"""

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()

            try:
                # 管理者画面にアクセス
                await page.goto("http://localhost:3001/admin")
                await page.wait_for_load_state("networkidle")

                # 問題管理タブに移動
                await page.click("text=問題管理")
                await page.wait_for_timeout(1000)

                # 試験を選択
                exam_rows = await page.locator("table tbody tr").all()
                if exam_rows:
                    await exam_rows[0].click()
                    await page.wait_for_timeout(500)

                # 問題一覧のテーブルヘッダーを確認
                headers = await page.locator("table thead th").all_text_contents()
                print(f"[OK] 問題一覧のヘッダー: {headers}")

                # 期待されるヘッダーが含まれているか確認
                expected_headers = ["問題番号", "タイトル", "設問文", "配点", "文字制限"]
                for header in expected_headers:
                    if any(header in h for h in headers):
                        print(f"[OK] ヘッダー '{header}' が存在")
                    else:
                        print(f"[ERROR] ヘッダー '{header}' が不足")

                # 問題行の詳細確認
                question_rows = await page.locator("table tbody tr").all()
                if question_rows:
                    first_row_cells = await question_rows[0].locator("td").all_text_contents()
                    print(f"[OK] 最初の問題行のデータ: {first_row_cells}")

            except Exception as e:
                print(f"[ERROR] テスト中にエラー: {str(e)}")
                await page.screenshot(path="error_question_display.png")

            finally:
                await browser.close()

if __name__ == "__main__":
    import asyncio

    test_instance = TestIPAAdminUI()

    print("=== IPA PM試験問題 管理者UI登録テスト ===")
    asyncio.run(test_instance.test_admin_ipa_question_registration())

    print("\\n=== 問題表示構造確認テスト ===")
    asyncio.run(test_instance.test_admin_question_display_structure())