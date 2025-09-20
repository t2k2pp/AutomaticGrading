# PM試験AI採点システム - Webフロントエンド用Dockerfile
FROM node:18-alpine AS builder

# 引数定義
ARG NODE_VERSION=18

# 作業ディレクトリ設定
WORKDIR /app

# package.jsonとpackage-lock.jsonをコピー
COPY src/web/package*.json ./

# 依存関係のインストール（buildに必要なdev dependenciesも含む）
RUN npm install

# ソースコードをコピー
COPY src/web ./

# アプリケーションをビルド
RUN npm run build

# 本番用イメージ
FROM node:18-alpine

WORKDIR /app

# 必要なファイルのみコピー
COPY --from=builder /app/build ./build
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules

# 非rootユーザーを作成
RUN addgroup -g 1001 appuser && adduser -u 1001 -G appuser -s /bin/sh -D appuser
RUN chown -R appuser:appuser /app
USER appuser

# ポート公開
EXPOSE 3000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# デフォルトコマンド
CMD ["npm", "start"]