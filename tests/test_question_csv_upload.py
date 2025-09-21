"""
問題登録CSV機能のテスト
管理者がCSVで問題を一括登録する機能を検証
"""
import asyncio
from playwright.async_api import async_playwright
import os

async def test_question_csv_upload():
    """問題登録CSV機能をテスト"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        try:
            print("[INFO] 管理者画面にアクセス中...")
            await page.goto("http://localhost:3000/admin")
            await page.wait_for_load_state("networkidle")

            # CSV一括登録タブをクリック
            print("[INFO] CSV一括登録タブを選択...")
            csv_tab = page.locator("text=CSV一括登録")
            await csv_tab.click()
            await page.wait_for_timeout(1000)

            # CSV形式の要件が表示されているか確認
            print("[INFO] CSV要件表示の確認...")
            requirements_text = await page.locator("text=CSV形式の要件").count()
            if requirements_text > 0:
                print("[OK] CSV形式の要件が表示されています")
            else:
                print("[ERROR] CSV形式の要件が表示されていません")

            # 試験名入力フィールドの確認
            print("[INFO] 試験名入力フィールドの確認...")
            exam_name_field = page.locator("input[placeholder*='例：2024年度']")
            await exam_name_field.fill("2024年度テスト用PM試験")
            print("[OK] 試験名を入力しました")

            # CSVファイル選択ボタンの確認
            print("[INFO] ファイル選択ボタンの確認...")
            file_button = page.locator("text=CSVファイルを選択")
            if await file_button.count() > 0:
                print("[OK] ファイル選択ボタンが存在します")
            else:
                print("[ERROR] ファイル選択ボタンが見つかりません")

            # CSVファイルをアップロード
            print("[INFO] CSVファイルをアップロード中...")
            csv_file_path = os.path.abspath("test_data/questions.csv")
            if os.path.exists(csv_file_path):
                # ファイル入力要素を探してファイルを設定
                file_input = page.locator("input[type='file']")
                await file_input.set_input_files(csv_file_path)

                print(f"[OK] CSVファイルを選択しました: {csv_file_path}")

                # ファイル名が表示されているか確認
                await page.wait_for_timeout(1000)
                selected_file_text = page.locator("text=選択済み:")
                if await selected_file_text.count() > 0:
                    print("[OK] 選択されたファイル名が表示されています")
                else:
                    print("[WARNING] ファイル名表示が見つかりません")

                # アップロード実行ボタンをクリック
                print("[INFO] アップロード実行...")
                upload_button = page.locator("text=アップロード実行")
                await upload_button.click()

                # アップロード処理の監視
                print("[INFO] アップロード処理を監視中...")

                # 成功メッセージまたはエラーメッセージを待機
                await page.wait_for_timeout(5000)

                # 処理状況の確認
                status_section = page.locator("text=処理状況")
                if await status_section.count() > 0:
                    print("[OK] アップロード処理状況が表示されています")

                    # アップロードIDの確認
                    upload_id_text = page.locator("text=アップロードID:")
                    if await upload_id_text.count() > 0:
                        print("[OK] アップロードIDが表示されています")

                    # ステータスの確認
                    status_text = page.locator("text=ステータス:")
                    if await status_text.count() > 0:
                        print("[OK] ステータスが表示されています")

                # 完了まで待機（最大30秒）
                print("[INFO] 処理完了を待機中...")
                for i in range(10):
                    await page.wait_for_timeout(3000)

                    # 成功メッセージをチェック
                    success_alert = page.locator(".MuiAlert-standardSuccess")
                    if await success_alert.count() > 0:
                        print("[OK] アップロードが成功しました")
                        break

                    # エラーメッセージをチェック
                    error_alert = page.locator(".MuiAlert-standardError")
                    if await error_alert.count() > 0:
                        print("[ERROR] アップロードでエラーが発生しました")
                        error_text = await error_alert.text_content()
                        print(f"[ERROR] エラー内容: {error_text}")
                        break

                    print(f"[INFO] 待機中... ({i+1}/10)")

                # 試験管理タブで結果確認
                print("[INFO] 試験管理タブで結果確認...")
                exam_tab = page.locator("text=試験管理")
                await exam_tab.click()
                await page.wait_for_timeout(2000)

                # 作成された試験が表示されているか確認
                test_exam = page.locator("text=2024年度テスト用PM試験")
                if await test_exam.count() > 0:
                    print("[OK] 新しい試験が作成されています")

                    # 試験を選択
                    await test_exam.click()
                    await page.wait_for_timeout(1000)

                    # 問題管理タブで問題確認
                    print("[INFO] 問題管理タブで問題確認...")
                    question_tab = page.locator("text=問題管理")
                    await question_tab.click()
                    await page.wait_for_timeout(2000)

                    # 問題が登録されているか確認
                    questions_table = page.locator("table")
                    question_rows = page.locator("table tbody tr")
                    question_count = await question_rows.count()

                    if question_count > 0:
                        print(f"[OK] {question_count}件の問題が登録されています")

                        # 問題内容の確認
                        for i in range(min(3, question_count)):
                            row = question_rows.nth(i)
                            question_number = await row.locator("td").nth(1).text_content()
                            title = await row.locator("td").nth(2).text_content()
                            print(f"[INFO] 問題{i+1}: {question_number} - {title}")
                    else:
                        print("[ERROR] 問題が登録されていません")
                else:
                    print("[ERROR] 新しい試験が作成されていません")

            else:
                print(f"[ERROR] CSVファイルが見つかりません: {csv_file_path}")

            print("\n[SUMMARY] 問題登録CSV機能テスト完了")

        except Exception as e:
            print(f"[ERROR] テスト中にエラー: {str(e)}")
            await page.screenshot(path="test_question_csv_upload_error.png")

        finally:
            await browser.close()

async def test_api_directly():
    """APIを直接テスト"""
    import requests

    print("\n[INFO] API直接テスト開始...")

    try:
        # CSVファイルを読み込み
        csv_file_path = os.path.abspath("test_data/questions.csv")
        if not os.path.exists(csv_file_path):
            print(f"[ERROR] CSVファイルが見つかりません: {csv_file_path}")
            return

        # プレビューAPIをテスト
        print("[INFO] プレビューAPIをテスト...")
        with open(csv_file_path, 'rb') as f:
            files = {'file': ('questions.csv', f, 'text/csv')}
            response = requests.post(
                'http://localhost:8000/api/admin/questions/csv/preview',
                files=files
            )

        if response.status_code == 200:
            preview_data = response.json()
            print(f"[OK] プレビュー成功: {preview_data['total_rows']}行のデータ")
            print(f"[INFO] 検出された問題: {preview_data['detected_issues']}")
            print(f"[INFO] カラムマッピング: {preview_data['column_mapping']}")
        else:
            print(f"[ERROR] プレビューAPI失敗: {response.status_code}")
            print(f"[ERROR] レスポンス: {response.text}")

        # アップロードAPIをテスト
        print("[INFO] アップロードAPIをテスト...")
        with open(csv_file_path, 'rb') as f:
            files = {'file': ('questions.csv', f, 'text/csv')}
            data = {'exam_name': 'API直接テスト試験'}
            response = requests.post(
                'http://localhost:8000/api/admin/questions/csv/execute',
                files=files,
                data=data
            )

        if response.status_code == 200:
            upload_result = response.json()
            print(f"[OK] アップロード開始成功")
            print(f"[INFO] アップロードID: {upload_result['upload_id']}")
            print(f"[INFO] メッセージ: {upload_result['message']}")

            # ステータス確認
            upload_id = upload_result['upload_id']
            for i in range(5):
                await asyncio.sleep(2)
                status_response = requests.get(
                    f'http://localhost:8000/api/admin/questions/csv/status/{upload_id}'
                )
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"[INFO] ステータス確認 {i+1}: {status_data['status']}")
                    if status_data['status'] == 'completed':
                        print("[OK] アップロード完了")
                        break
        else:
            print(f"[ERROR] アップロードAPI失敗: {response.status_code}")
            print(f"[ERROR] レスポンス: {response.text}")

    except Exception as e:
        print(f"[ERROR] API直接テスト中にエラー: {str(e)}")

if __name__ == "__main__":
    print("問題登録CSV機能テスト開始")
    print("=" * 50)

    # UIテストを実行
    asyncio.run(test_question_csv_upload())

    # APIテストを実行
    asyncio.run(test_api_directly())