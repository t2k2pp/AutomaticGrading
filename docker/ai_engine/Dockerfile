# PM試験AI採点システム - AI Engine用Dockerfile
FROM python:3.10-slim

# 引数定義
ARG PYTHON_VERSION=3.10

# 作業ディレクトリ設定
WORKDIR /app

# システムパッケージのインストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Pythonの依存関係をインストール
COPY requirements_ai.txt .
RUN pip install --no-cache-dir -r requirements_ai.txt

# アプリケーションコードをコピー
COPY src/ai_engine /app/src

# キャッシュディレクトリ作成
RUN mkdir -p /app/cache /app/models /app/logs

# 非rootユーザーを作成
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# デフォルトコマンド
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]