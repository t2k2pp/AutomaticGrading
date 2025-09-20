#!/bin/bash

# ========================================
# PM試験AI採点システム - 初回セットアップ
# ========================================

set -e

echo "================================================"
echo "PM試験AI採点システム - 初回セットアップ"
echo "================================================"

# 色付き出力の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# OSの判定
OS_TYPE="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="mac"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    OS_TYPE="windows"
fi

echo -e "${GREEN}検出されたOS: $OS_TYPE${NC}"

# Docker Desktopの確認
echo -e "\n${YELLOW}1. Docker Desktopの確認...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Dockerがインストールされていません。Docker Desktopをインストールしてください。${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}Docker Desktopが起動していません。起動してから再実行してください。${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker Desktopが正常に動作しています${NC}"
docker version

# .envファイルの作成
echo -e "\n${YELLOW}2. 環境設定ファイルの作成...${NC}"
if [ ! -f ".env" ]; then
    echo "cp .env.example .env"
    cp .env.example .env
    echo -e "${GREEN}✓ .envファイルを作成しました${NC}"
    echo -e "${YELLOW}注意: .envファイルでデータベースパスワードやAPIキーを設定してください${NC}"
else
    echo -e "${GREEN}✓ .envファイルは既に存在します${NC}"
fi

# 必要なディレクトリの作成
echo -e "\n${YELLOW}3. ディレクトリ構造の確認...${NC}"
directories=(
    "data/input"
    "data/output"
    "logs/api"
    "logs/ai"
    "logs/celery"
    "models"
    "notebooks"
)

for dir in "${directories[@]}"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        echo "Created: $dir"
    fi
done

echo -e "${GREEN}✓ ディレクトリ構造を確認しました${NC}"

# Dockerネットワークの作成
echo -e "\n${YELLOW}4. Dockerネットワークの作成...${NC}"
if ! docker network ls | grep -q "scoring_network"; then
    docker network create scoring_network
    echo -e "${GREEN}✓ Dockerネットワークを作成しました${NC}"
else
    echo -e "${GREEN}✓ Dockerネットワークは既に存在します${NC}"
fi

# 権限設定（Linux/Mac用）
if [[ "$OS_TYPE" == "linux" ]] || [[ "$OS_TYPE" == "mac" ]]; then
    echo -e "\n${YELLOW}5. 権限設定...${NC}"
    chmod +x build.sh start.sh stop.sh logs.sh
    echo -e "${GREEN}✓ スクリプトに実行権限を付与しました${NC}"
fi

# セットアップ完了
echo -e "\n${GREEN}================================================${NC}"
echo -e "${GREEN}セットアップが完了しました！${NC}"
echo -e "${GREEN}================================================${NC}"

echo -e "\n${YELLOW}次のステップ:${NC}"
echo "1. .envファイルでAPIキーなどの設定を行ってください"
echo "2. ./build.sh でDockerイメージをビルドしてください"
echo "3. ./start.sh でシステムを起動してください"

echo -e "\n${YELLOW}アクセス先:${NC}"
echo "- API: http://localhost:8000"
echo "- Web: http://localhost:3000"
echo "- 統合: http://localhost:8080"
echo "- API ドキュメント: http://localhost:8000/docs"
echo "- Flower (Celery監視): http://localhost:5555"
echo "- pgAdmin (開発時): http://localhost:5050"
echo "- Jupyter (開発時): http://localhost:8888"

echo -e "\n${GREEN}セットアップが正常に完了しました。${NC}"