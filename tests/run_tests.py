#!/usr/bin/env python3
"""
テスト実行スクリプト
APIテストとUIテストを自動実行
"""
import subprocess
import sys
import asyncio
from pathlib import Path


def run_api_tests():
    """APIテスト実行"""
    print("🔧 APIテスト実行中...")
    try:
        # 直接Pythonモジュールとして実行
        from test_api import TestScoringAPI
        import httpx

        client = httpx.Client(base_url="http://localhost:8000")
        test_instance = TestScoringAPI()

        # 基本テスト実行
        print("✅ 解答提出テスト")
        test_instance.test_answer_submission(client)

        print("✅ 詳細AI採点テスト")
        result = test_instance.test_detailed_ai_scoring(client)

        print("✅ 確信度根拠テスト")
        test_instance.test_confidence_reasoning(client)

        print("✅ 複数解答一貫性テスト")
        test_instance.test_multiple_answers_scoring(client)

        client.close()
        print("🎉 APIテスト完了!")
        return True

    except Exception as e:
        print(f"❌ APIテスト失敗: {str(e)}")
        return False


async def run_ui_tests():
    """UIテスト実行"""
    print("🎭 UIテスト実行中...")
    try:
        from test_ui import run_ui_tests
        await run_ui_tests()
        print("🎉 UIテスト完了!")
        return True

    except Exception as e:
        print(f"❌ UIテスト失敗: {str(e)}")
        return False


def check_services():
    """サービス稼働確認"""
    print("🔍 サービス稼働確認中...")
    import httpx

    try:
        # API サーバー確認
        with httpx.Client() as client:
            api_response = client.get("http://localhost:8000/health/")
            assert api_response.status_code == 200
            print("✅ APIサーバー稼働中")

            # React UI 確認
            ui_response = client.get("http://localhost:3002/")
            assert ui_response.status_code == 200
            print("✅ React UI稼働中")

        return True

    except Exception as e:
        print(f"❌ サービス確認失敗: {str(e)}")
        print("💡 Docker サービスが起動していることを確認してください")
        return False


async def main():
    """メイン実行"""
    print("🚀 PM試験AI採点システム - 自動テスト開始")
    print("=" * 50)

    # サービス稼働確認
    if not check_services():
        print("❌ サービスが稼働していません。テストを中止します。")
        sys.exit(1)

    results = []

    # APIテスト実行
    api_result = run_api_tests()
    results.append(("API", api_result))

    print("-" * 50)

    # UIテスト実行
    ui_result = await run_ui_tests()
    results.append(("UI", ui_result))

    print("-" * 50)

    # 結果サマリー
    print("📊 テスト結果サマリー")
    for test_type, success in results:
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"  {test_type}テスト: {status}")

    all_success = all(result[1] for result in results)
    if all_success:
        print("🎉 全てのテストが成功しました！")
        return 0
    else:
        print("❌ 一部のテストが失敗しました。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)