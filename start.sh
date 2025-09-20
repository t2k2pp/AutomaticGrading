#!/bin/bash

# ========================================
# PM試験AI採点システム - 起動スクリプト
# ========================================

set -e

echo "================================================"
echo "PM試験AI採点システム - システム起動"
echo "================================================"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 環境確認
if [ ! -f ".env" ]; then
    echo "エラー: .envファイルが見つかりません。setup.shを先に実行してください。"
    exit 1
fi

echo -e "${YELLOW}システムを起動中...${NC}"

# Docker Composeで起動
docker-compose up -d

echo -e "\n${YELLOW}起動状況を確認中...${NC}"
sleep 10

# ヘルスチェック
echo -e "\n${YELLOW}ヘルスチェック実行中...${NC}"
for i in {1..30}; do
    if curl -f http://localhost:8000/health/live >/dev/null 2>&1; then
        echo -e "${GREEN}✓ APIサーバーが正常に起動しました${NC}"
        break
    fi
    echo "API起動待機中... ($i/30)"
    sleep 2
done

echo -e "\n${GREEN}================================================${NC}"
echo -e "${GREEN}システムが起動しました！${NC}"
echo -e "${GREEN}================================================${NC}"

echo -e "\n${YELLOW}アクセス先:${NC}"
echo "- API: http://localhost:8000"
echo "- Web: http://localhost:3000"
echo "- 統合: http://localhost:8080"
echo "- API ドキュメント: http://localhost:8000/docs"
echo "- Flower (Celery監視): http://localhost:5555"

if docker-compose ps | grep -q "development"; then
    echo "- pgAdmin (開発): http://localhost:5050"
    echo "- Jupyter (開発): http://localhost:8888"
fi

echo -e "\n${YELLOW}ログ確認:${NC}"
echo "./logs.sh でリアルタイムログを確認できます"

echo -e "\n${YELLOW}停止方法:${NC}"
echo "./stop.sh でシステムを停止できます"