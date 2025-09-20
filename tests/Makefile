# PM試験AI採点システム - テスト実行
.PHONY: install test api-test ui-test clean help

# デフォルトターゲット
help:
	@echo "PM試験AI採点システム - テストコマンド"
	@echo ""
	@echo "利用可能なコマンド:"
	@echo "  make install    - テスト依存関係インストール"
	@echo "  make test       - 全テスト実行"
	@echo "  make api-test   - APIテストのみ実行"
	@echo "  make ui-test    - UIテストのみ実行"
	@echo "  make clean      - テスト結果クリア"

# 依存関係インストール
install:
	@echo "📦 テスト依存関係をインストール中..."
	pip install -r requirements.txt
	playwright install chromium

# 全テスト実行
test:
	@echo "🚀 全テスト実行中..."
	python run_tests.py

# APIテストのみ
api-test:
	@echo "🔧 APIテストのみ実行中..."
	python test_api.py

# UIテストのみ
ui-test:
	@echo "🎭 UIテストのみ実行中..."
	python test_ui.py

# pytest使用（オプション）
pytest:
	@echo "🧪 pytest実行中..."
	pytest -v test_api.py test_ui.py

# クリア
clean:
	@echo "🧹 テスト結果をクリア中..."
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
	rm -rf .pytest_cache