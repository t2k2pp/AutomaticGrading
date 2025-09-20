# PM試験AI採点システム - APIサーバー用Dockerfile
FROM python:3.10-slim

# 作業ディレクトリ設定
WORKDIR /app

# システムパッケージのインストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Pythonの依存関係をインストール
COPY requirements_api.txt .
RUN pip install --no-cache-dir -r requirements_api.txt

# アプリケーションコードをコピー
COPY src/api /app/src
COPY src/api/__init__.py /app/src/__init__.py

# 非rootユーザーを作成
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# デフォルトコマンド
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]