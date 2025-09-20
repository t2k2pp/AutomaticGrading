#!/bin/bash

# ========================================
# PM試験AI採点システム - ビルドスクリプト
# ========================================

set -e

echo "================================================"
echo "PM試験AI採点システム - Dockerイメージビルド"
echo "================================================"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Dockerイメージをビルド中...${NC}"

# 既存のイメージとコンテナをクリーンアップ
echo -e "\n${YELLOW}1. クリーンアップ...${NC}"
docker-compose down --remove-orphans
docker system prune -f

# イメージのビルド
echo -e "\n${YELLOW}2. イメージビルド...${NC}"
docker-compose build --no-cache

echo -e "\n${GREEN}✓ ビルドが完了しました${NC}"
echo -e "\n次のコマンドでシステムを起動してください:"
echo "./start.sh"