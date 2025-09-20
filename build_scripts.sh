#!/bin/bash

# ========================================
# 1. 初回セットアップスクリプト (setup.sh)
# ========================================
cat > setup.sh << 'SCRIPT_END'
#!/bin/bash
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

# 必要なディレクトリの作成
echo -e "\n${YELLOW}2. ディレクトリ構造の作成...${NC}"
directories=(
    "src/api"
    "src/ai_engine"
    "src/web"
    "docker/postgres/init"
    "docker/ai_engine"
    "docker/api"
    "docker/web"
    "docker/jupyter"
    "docker/nginx/conf.d"
    "config"
    "models"
    "data/input"
    "data/output"
    "logs/api"
    "logs/ai"
    "logs/celery"
    "notebooks"
)

for dir in "${directories[@]}"; do
    mkdir -p "$dir"
    echo "  ✓ $dir"
done

# 環境変数ファイルの作成
echo -e "\n${YELLOW}3. 環境変数ファイルの作成...${NC}"
if [ ! -f .env ]; then
    cat > .env << 'ENV_END'
# データベース設定
DB_USER=scoring_user
DB_PASSWORD=scoring_pass_change_in_production
DB_NAME=pm_scoring

# API設定
SECRET_KEY=your-secret-key-change-in-production-$(openssl rand -hex 32)
ENVIRONMENT=development
LOG_LEVEL=INFO

# AI設定
AI_MODEL=gpt-4
GPU_DEVICE=0

# 開発ツール設定
PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=admin
JUPYTER_TOKEN=scoring2024

# その他
API_URL=http://localhost:8000
NODE_ENV=development
ENV_END
    echo -e "${GREEN}✓ .env ファイルを作成しました${NC}"
else
    echo -e "${YELLOW}✓ .env ファイルは既に存在します${NC}"
fi

# Dockerfileの作成
echo -e "\n${YELLOW}4. Dockerfileの作成...${NC}"

# AI Engine Dockerfile
cat > docker/ai_engine/Dockerfile << 'DOCKERFILE_END'
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

ARG PYTHON_VERSION=3.10

RUN apt-get update && apt-get install -y \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-pip \
    python${PYTHON_VERSION}-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements_ai.txt .
RUN pip install --no-cache-dir -r requirements_ai.txt

COPY src/ai_engine /app/src

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]
DOCKERFILE_END

# API Dockerfile
cat > docker/api/Dockerfile << 'DOCKERFILE_END'
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements_api.txt .
RUN pip install --no-cache-dir -r requirements_api.txt

COPY src/api /app/src

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
DOCKERFILE_END

# Web Dockerfile
cat > docker/web/Dockerfile << 'DOCKERFILE_END'
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
DOCKERFILE_END

# Jupyter Dockerfile
cat > docker/jupyter/Dockerfile << 'DOCKERFILE_END'
FROM jupyter/datascience-notebook:latest

USER root

RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

USER jovyan

COPY requirements_jupyter.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements_jupyter.txt

WORKDIR /home/jovyan
DOCKERFILE_END

echo -e "${GREEN}✓ Dockerfileを作成しました${NC}"

# Requirements.txtの作成
echo -e "\n${YELLOW}5. Requirementsファイルの作成...${NC}"

cat > requirements_ai.txt << 'REQ_END'
torch>=2.0.0
transformers>=4.35.0
langchain>=0.1.0
sentence-transformers>=2.2.0
numpy>=1.24.0
pandas>=2.0.0
scikit-learn>=1.3.0
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
python-multipart>=0.0.6
REQ_END

cat > requirements_api.txt << 'REQ_END'
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
alembic>=1.12.0
psycopg2-binary>=2.9.0
redis>=5.0.0
celery>=5.3.0
pydantic>=2.5.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
httpx>=0.25.0
REQ_END

cat > requirements_jupyter.txt << 'REQ_END'
numpy>=1.24.0
pandas>=2.0.0
matplotlib>=3.7.0
seaborn>=0.12.0
scikit-learn>=1.3.0
plotly>=5.17.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
REQ_END

echo -e "${GREEN}✓ Requirementsファイルを作成しました${NC}"

# Nginx設定ファイルの作成
echo -e "\n${YELLOW}6. Nginx設定ファイルの作成...${NC}"

cat > docker/nginx/nginx.conf << 'NGINX_END'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    keepalive_timeout 65;
    gzip on;

    include /etc/nginx/conf.d/*.conf;
}
NGINX_END

cat > docker/nginx/conf.d/default.conf << 'NGINX_CONF_END'
upstream api {
    server api:8000;
}

upstream web {
    server web:3000;
}

server {
    listen 80;
    server_name localhost;
    client_max_body_size 100M;

    location /api/ {
        proxy_pass http://api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location / {
        proxy_pass http://web/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX_CONF_END

echo -e "${GREEN}✓ Nginx設定ファイルを作成しました${NC}"

# PostgreSQL初期化スクリプトの作成
echo -e "\n${YELLOW}7. データベース初期化スクリプトの作成...${NC}"

cat > docker/postgres/init/01_init.sql << 'SQL_END'
-- PM採点システム データベース初期化スクリプト

-- 拡張機能の有効化
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- スキーマの作成
CREATE SCHEMA IF NOT EXISTS scoring;

-- テーブルの作成
CREATE TABLE IF NOT EXISTS scoring.exams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    year INTEGER NOT NULL,
    season VARCHAR(10) NOT NULL,
    question_number VARCHAR(10) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, season, question_number)
);

CREATE TABLE IF NOT EXISTS scoring.questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exam_id UUID REFERENCES scoring.exams(id) ON DELETE CASCADE,
    sub_question_id VARCHAR(20) NOT NULL,
    question_text TEXT NOT NULL,
    max_chars INTEGER,
    max_points INTEGER NOT NULL,
    model_answer TEXT,
    grading_intention TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scoring.candidates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_number VARCHAR(20) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scoring.answers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id UUID REFERENCES scoring.candidates(id) ON DELETE CASCADE,
    question_id UUID REFERENCES scoring.questions(id) ON DELETE CASCADE,
    answer_text TEXT,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(candidate_id, question_id)
);

CREATE TABLE IF NOT EXISTS scoring.scoring_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    answer_id UUID REFERENCES scoring.answers(id) ON DELETE CASCADE,
    ai_score DECIMAL(5, 2),
    human_score DECIMAL(5, 2),
    confidence DECIMAL(3, 2),
    scoring_details JSONB,
    ai_scored_at TIMESTAMP WITH TIME ZONE,
    human_scored_at TIMESTAMP WITH TIME ZONE,
    scorer_id VARCHAR(50),
    is_final BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- インデックスの作成
CREATE INDEX idx_exams_year_season ON scoring.exams(year, season);
CREATE INDEX idx_questions_exam_id ON scoring.questions(exam_id);
CREATE INDEX idx_answers_candidate_id ON scoring.answers(candidate_id);
CREATE INDEX idx_answers_question_id ON scoring.answers(question_id);
CREATE INDEX idx_scoring_results_answer_id ON scoring.scoring_results(answer_id);
CREATE INDEX idx_scoring_results_confidence ON scoring.scoring_results(confidence);

-- 更新トリガーの作成
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_exams_updated_at BEFORE UPDATE ON scoring.exams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scoring_results_updated_at BEFORE UPDATE ON scoring.scoring_results
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 初期データの投入（サンプル）
INSERT INTO scoring.exams (year, season, question_number) VALUES 
    (2024, 'autumn', '問1'),
    (2024, 'autumn', '問2'),
    (2024, 'autumn', '問3');

GRANT ALL PRIVILEGES ON SCHEMA scoring TO scoring_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA scoring TO scoring_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA scoring TO scoring_user;
SQL_END

echo -e "${GREEN}✓ データベース初期化スクリプトを作成しました${NC}"

# Gitignoreファイルの作成
echo -e "\n${YELLOW}8. .gitignoreファイルの作成...${NC}"

cat > .gitignore << 'GITIGNORE_END'
# 環境変数
.env
.env.local
.env.production

# ログ
logs/
*.log

# データ
data/
uploaded_files/
models/*.bin
models/*.pt
models/*.pth

# キャッシュ
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.coverage
htmlcov/

# IDEファイル
.idea/
.vscode/
*.swp
*.swo
*~

# OS関連
.DS_Store
Thumbs.db

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Jupyter
.ipynb_checkpoints/

# Docker volumes（開発時は除外しない場合もある）
# postgres_data/
# redis_data/
GITIGNORE_END

echo -e "${GREEN}✓ .gitignoreファイルを作成しました${NC}"

echo -e "\n${GREEN}================================================"
echo "セットアップが完了しました！"
echo "================================================${NC}"
echo ""
echo "次のステップ:"
echo "1. 必要に応じて .env ファイルを編集してください"
echo "2. ./build.sh を実行してDockerイメージをビルドしてください"
echo "3. ./start.sh を実行してシステムを起動してください"
echo ""
echo "アクセスURL:"
echo "  - Webインターフェース: http://localhost:3000"
echo "  - API: http://localhost:8000"
echo "  - API Documentation: http://localhost:8000/docs"
echo "  - Flower (Celery): http://localhost:5555"
echo "  - pgAdmin: http://localhost:5050"
echo "  - Jupyter: http://localhost:8888"
echo ""
SCRIPT_END

chmod +x setup.sh

# ========================================
# 2. ビルドスクリプト (build.sh)
# ========================================
cat > build.sh << 'SCRIPT_END'
#!/bin/bash
set -e

echo "================================================"
echo "PM試験AI採点システム - Dockerイメージビルド"
echo "================================================"

# 色付き出力の定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ビルド対象の選択
if [ "$1" == "--production" ]; then
    echo -e "${YELLOW}本番環境用イメージをビルドします${NC}"
    COMPOSE_PROFILES=""
else
    echo -e "${YELLOW}開発環境用イメージをビルドします${NC}"
    COMPOSE_PROFILES="--profile development"
fi

# 古いイメージのクリーンアップ（オプション）
if [ "$1" == "--clean" ] || [ "$2" == "--clean" ]; then
    echo -e "${YELLOW}古いイメージをクリーンアップします...${NC}"
    docker-compose down -v
    docker system prune -f
fi

# Dockerイメージのビルド
echo -e "${YELLOW}Dockerイメージをビルドしています...${NC}"
docker-compose build --no-cache $COMPOSE_PROFILES

# ビルド結果の確認
echo -e "\n${GREEN}ビルドが完了しました！${NC}"
docker-compose images

echo -e "\n${GREEN}================================================"
echo "ビルドが正常に完了しました"
echo "================================================${NC}"
echo ""
echo "次のステップ: ./start.sh を実行してシステムを起動してください"
SCRIPT_END

chmod +x build.sh

# ========================================
# 3. 起動スクリプト (start.sh)
# ========================================
cat > start.sh << 'SCRIPT_END'
#!/bin/bash
set -e

echo "================================================"
echo "PM試験AI採点システム - 起動"
echo "================================================"

# 色付き出力の定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Docker Desktopの確認
if ! docker info &> /dev/null; then
    echo -e "${RED}Docker Desktopが起動していません。起動してから再実行してください。${NC}"
    exit 1
fi

# 起動モードの選択
MODE="development"
COMPOSE_PROFILES="--profile development"

if [ "$1" == "--production" ]; then
    MODE="production"
    COMPOSE_PROFILES=""
    echo -e "${YELLOW}本番モードで起動します${NC}"
elif [ "$1" == "--minimal" ]; then
    MODE="minimal"
    COMPOSE_PROFILES=""
    echo -e "${YELLOW}最小構成で起動します${NC}"
    SERVICES="postgres redis api"
else
    echo -e "${YELLOW}開発モードで起動します${NC}"
    SERVICES=""
fi

# コンテナの起動
echo -e "${YELLOW}コンテナを起動しています...${NC}"

if [ -z "$SERVICES" ]; then
    docker-compose $COMPOSE_PROFILES up -d
else
    docker-compose up -d $SERVICES
fi

# 起動確認
echo -e "\n${YELLOW}起動状態を確認しています...${NC}"
sleep 5

# ヘルスチェック
echo -e "\n${YELLOW}ヘルスチェック...${NC}"

# PostgreSQLの確認
if docker-compose exec -T postgres pg_isready -U scoring_user > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ PostgreSQL: 正常${NC}"
else
    echo -e "  ${RED}✗ PostgreSQL: 異常${NC}"
fi

# Redisの確認
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Redis: 正常${NC}"
else
    echo -e "  ${RED}✗ Redis: 異常${NC}"
fi

# APIの確認
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ API: 正常${NC}"
else
    echo -e "  ${YELLOW}△ API: 起動中...${NC}"
fi

# 実行中のコンテナ一覧
echo -e "\n${YELLOW}実行中のコンテナ:${NC}"
docker-compose ps

echo -e "\n${GREEN}================================================"
echo "システムが起動しました！"
echo "================================================${NC}"
echo ""
echo "アクセスURL:"
echo "  - Webインターフェース: http://localhost:3000"
echo "  - API: http://localhost:8000"
echo "  - API Documentation: http://localhost:8000/docs"

if [ "$MODE" == "development" ]; then
    echo "  - Flower (Celery): http://localhost:5555"
    echo "  - pgAdmin: http://localhost:5050 (admin@example.com / admin)"
    echo "  - Jupyter: http://localhost:8888 (token: scoring2024)"
fi

echo ""
echo "ログを確認: docker-compose logs -f [service_name]"
echo "停止: ./stop.sh"
SCRIPT_END

chmod +x start.sh

# ========================================
# 4. 停止スクリプト (stop.sh)
# ========================================
cat > stop.sh << 'SCRIPT_END'
#!/bin/bash
set -e

echo "================================================"
echo "PM試験AI採点システム - 停止"
echo "================================================"

# 色付き出力の定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 停止オプションの処理
if [ "$1" == "--clean" ]; then
    echo -e "${RED}警告: データを含むすべてのボリュームが削除されます！${NC}"
    echo -n "続行しますか？ (y/N): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}コンテナとボリュームを削除しています...${NC}"
        docker-compose down -v
        echo -e "${GREEN}✓ クリーンアップが完了しました${NC}"
    else
        echo "キャンセルしました"
        exit 0
    fi
else
    echo -e "${YELLOW}コンテナを停止しています...${NC}"
    docker-compose down
    echo -e "${GREEN}✓ コンテナを停止しました${NC}"
fi

# 停止確認
echo -e "\n${YELLOW}停止状態を確認しています...${NC}"
docker-compose ps

echo -e "\n${GREEN}================================================"
echo "システムを停止しました"
echo "================================================${NC}"
echo ""
echo "再起動: ./start.sh"
echo "データを含めて削除: ./stop.sh --clean"
SCRIPT_END

chmod +x stop.sh

# ========================================
# 5. ログ確認スクリプト (logs.sh)
# ========================================
cat > logs.sh << 'SCRIPT_END'
#!/bin/bash

echo "================================================"
echo "PM試験AI採点システム - ログ確認"
echo "================================================"

if [ -z "$1" ]; then
    echo "使用方法: ./logs.sh [service_name]"
    echo ""
    echo "利用可能なサービス:"
    echo "  - postgres    (データベース)"
    echo "  - redis       (キャッシュ)"
    echo "  - ai_engine   (AI推論)"
    echo "  - api         (FastAPI)"
    echo "  - web         (フロントエンド)"
    echo "  - nginx       (リバースプロキシ)"
    echo "  - celery_worker (非同期タスク)"
    echo "  - all         (すべてのサービス)"
    echo ""
    echo "例: ./logs.sh api"
    echo "    ./logs.sh all"
    exit 1
fi

if [ "$1" == "all" ]; then
    docker-compose logs -f
else
    docker-compose logs -f "$1"
fi
SCRIPT_END

chmod +x logs.sh

echo "すべてのスクリプトファイルを作成しました:"
echo "  - setup.sh   : 初回セットアップ"
echo "  - build.sh   : Dockerイメージのビルド"
echo "  - start.sh   : システム起動"
echo "  - stop.sh    : システム停止"
echo "  - logs.sh    : ログ確認"