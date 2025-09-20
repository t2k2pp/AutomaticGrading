# Docker環境特化型追加設計書

## 1. コンテナ最適化設計

### 1.1 マルチステージビルドによる最適化

```dockerfile
# AI Engine用最適化Dockerfile
FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04 AS builder

# ビルド段階
RUN apt-get update && apt-get install -y \
    python3.10-dev \
    python3-pip \
    build-essential

WORKDIR /build
COPY requirements_ai.txt .
RUN pip install --user --no-cache-dir -r requirements_ai.txt

# 実行段階
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-distutils \
    && rm -rf /var/lib/apt/lists/*

# ビルド段階から必要なファイルのみコピー
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

WORKDIR /app
COPY src/ai_engine /app/src

# 非rootユーザーで実行
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

CMD ["python3", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 1.2 イメージサイズ削減戦略

```yaml
# docker-compose.override.yml (開発用)
version: '3.9'

services:
  api:
    build:
      target: development  # 開発用ターゲット
      cache_from:
        - pm_scoring_api:latest
        - pm_scoring_api:cache
    volumes:
      - ./src/api:/app/src:cached  # macOS最適化
      - /app/__pycache__  # キャッシュの除外

  ai_engine:
    build:
      args:
        BUILDKIT_INLINE_CACHE: 1  # BuildKitキャッシュ有効化
    environment:
      PYTHONDONTWRITEBYTECODE: 1  # .pycファイル生成抑制
      PYTHONUNBUFFERED: 1  # 出力バッファ無効化
```

## 2. ヘルスチェックとリカバリ機構

### 2.1 包括的ヘルスチェック実装

```python
# src/api/health.py
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from typing import Dict, Any
import redis
import httpx
import time

router = APIRouter()

class HealthChecker:
    def __init__(self, db, redis_client, ai_engine_url):
        self.db = db
        self.redis = redis_client
        self.ai_engine_url = ai_engine_url
        self.start_time = time.time()
    
    async def check_database(self) -> Dict[str, Any]:
        try:
            result = await self.db.execute(text("SELECT 1"))
            return {"status": "healthy", "latency_ms": 0}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def check_redis(self) -> Dict[str, Any]:
        try:
            start = time.time()
            self.redis.ping()
            latency = (time.time() - start) * 1000
            return {"status": "healthy", "latency_ms": latency}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def check_ai_engine(self) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.ai_engine_url}/health")
                if response.status_code == 200:
                    return {"status": "healthy", "model_loaded": True}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
        return {"status": "unhealthy"}
    
    async def get_health_status(self) -> Dict[str, Any]:
        uptime = time.time() - self.start_time
        
        checks = {
            "database": await self.check_database(),
            "redis": await self.check_redis(),
            "ai_engine": await self.check_ai_engine()
        }
        
        overall_status = "healthy"
        if any(check["status"] == "unhealthy" for check in checks.values()):
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "uptime_seconds": uptime,
            "checks": checks,
            "timestamp": time.time()
        }

@router.get("/health")
async def health_check():
    status = await health_checker.get_health_status()
    if status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=status)
    return status

@router.get("/health/live")
async def liveness_probe():
    return {"status": "alive"}

@router.get("/health/ready")
async def readiness_probe():
    status = await health_checker.get_health_status()
    if status["status"] != "healthy":
        raise HTTPException(status_code=503, detail="Not ready")
    return {"status": "ready"}
```

### 2.2 自動リカバリメカニズム

```yaml
# docker-compose.yml追加設定
services:
  api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    deploy:
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s
```

## 3. ボリューム最適化とデータ永続化

### 3.1 ボリューム設定最適化

```yaml
volumes:
  # 名前付きボリューム（永続データ）
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${DATA_DIR:-./data}/postgres
  
  # tmpfsボリューム（高速一時データ）
  ai_cache:
    driver: local
    driver_opts:
      type: tmpfs
      o: size=2g,uid=1000,gid=1000
  
  # NFSボリューム（共有データ）
  shared_models:
    driver: local
    driver_opts:
      type: nfs
      o: addr=nfs-server.local,rw,vers=4
      device: ":/exports/models"
```

### 3.2 バックアップ・リストアシステム

```bash
#!/bin/bash
# backup.sh - 自動バックアップスクリプト

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "データベースのバックアップ..."
docker-compose exec -T postgres pg_dump \
    -U scoring_user \
    -d pm_scoring \
    --verbose \
    --no-owner \
    --no-acl \
    -f /tmp/backup.sql

docker cp pm_scoring_db:/tmp/backup.sql "$BACKUP_DIR/database.sql"

echo "Redisのバックアップ..."
docker-compose exec -T redis redis-cli SAVE
docker cp pm_scoring_redis:/data/dump.rdb "$BACKUP_DIR/redis.rdb"

echo "アップロードファイルのバックアップ..."
docker run --rm \
    -v pm_scoring_uploaded_files:/data \
    -v "$PWD/$BACKUP_DIR":/backup \
    alpine tar czf /backup/uploads.tar.gz -C /data .

echo "設定ファイルのバックアップ..."
tar czf "$BACKUP_DIR/config.tar.gz" .env docker-compose.yml

echo "バックアップ完了: $BACKUP_DIR"
```

## 4. 開発・ステージング・本番環境の切り替え

### 4.1 環境別構成ファイル

```yaml
# docker-compose.prod.yml
version: '3.9'

services:
  api:
    image: ${REGISTRY_URL}/pm-scoring-api:${VERSION:-latest}
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
    environment:
      ENVIRONMENT: production
      LOG_LEVEL: WARNING
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "10"
    
  ai_engine:
    image: ${REGISTRY_URL}/pm-scoring-ai:${VERSION:-latest}
    deploy:
      replicas: 2
      placement:
        constraints:
          - node.labels.gpu == true
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
  
  nginx:
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./ssl:/etc/nginx/ssl:ro
      - ./docker/nginx/nginx.prod.conf:/etc/nginx/nginx.conf:ro
```

### 4.2 環境切り替えスクリプト

```python
# deploy.py - 環境別デプロイメントスクリプト
import os
import sys
import subprocess
from enum import Enum

class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class DockerDeployer:
    def __init__(self, environment: Environment):
        self.env = environment
        self.compose_files = self._get_compose_files()
    
    def _get_compose_files(self):
        files = ["docker-compose.yml"]
        
        if self.env == Environment.DEVELOPMENT:
            files.append("docker-compose.override.yml")
        elif self.env == Environment.STAGING:
            files.append("docker-compose.staging.yml")
        elif self.env == Environment.PRODUCTION:
            files.append("docker-compose.prod.yml")
        
        return files
    
    def deploy(self):
        # 環境変数の設定
        os.environ['ENVIRONMENT'] = self.env.value
        
        # Docker Composeコマンドの構築
        cmd = ["docker-compose"]
        for f in self.compose_files:
            cmd.extend(["-f", f])
        
        # ビルドとデプロイ
        if self.env == Environment.PRODUCTION:
            # 本番環境はイメージをプルして起動
            subprocess.run(cmd + ["pull"])
            subprocess.run(cmd + ["up", "-d", "--remove-orphans"])
        else:
            # 開発/ステージングはビルドして起動
            subprocess.run(cmd + ["build"])
            subprocess.run(cmd + ["up", "-d"])
        
        # ヘルスチェック
        self._wait_for_healthy()
    
    def _wait_for_healthy(self):
        import time
        import requests
        
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get("http://localhost:8000/health")
                if response.status_code == 200:
                    print(f"✓ システムが正常に起動しました ({self.env.value})")
                    return
            except:
                pass
            
            time.sleep(2)
            print(f"待機中... ({i+1}/{max_retries})")
        
        print("✗ 起動タイムアウト")
        sys.exit(1)

if __name__ == "__main__":
    env_name = sys.argv[1] if len(sys.argv) > 1 else "development"
    env = Environment(env_name)
    deployer = DockerDeployer(env)
    deployer.deploy()
```

## 5. スケーリング対応

### 5.1 水平スケーリング設定

```yaml
# docker-compose.scale.yml
version: '3.9'

services:
  api:
    deploy:
      replicas: ${API_REPLICAS:-3}
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      restart_policy:
        condition: any
        delay: 5s
        max_attempts: 3
  
  celery_worker:
    deploy:
      replicas: ${WORKER_REPLICAS:-5}
    environment:
      CELERY_CONCURRENCY: 2  # 各ワーカーの並行度を下げる
  
  # HAProxyロードバランサー
  haproxy:
    image: haproxy:2.8-alpine
    volumes:
      - ./docker/haproxy/haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro
    ports:
      - "8080:8080"  # API用ロードバランサー
      - "8404:8404"  # HAProxy統計画面
    depends_on:
      - api
    networks:
      - scoring_network
```

### 5.2 オートスケーリング設定

```python
# autoscaler.py - 負荷に応じた自動スケーリング
import docker
import psutil
import time
from typing import Dict

class AutoScaler:
    def __init__(self, service_name: str, min_replicas: int = 1, max_replicas: int = 10):
        self.client = docker.from_env()
        self.service_name = service_name
        self.min_replicas = min_replicas
        self.max_replicas = max_replicas
        self.scale_up_threshold = 80  # CPU使用率
        self.scale_down_threshold = 20
        
    def get_metrics(self) -> Dict[str, float]:
        containers = self.client.containers.list(
            filters={"label": f"com.docker.compose.service={self.service_name}"}
        )
        
        if not containers:
            return {"cpu": 0, "memory": 0}
        
        total_cpu = 0
        total_memory = 0
        
        for container in containers:
            stats = container.stats(stream=False)
            # CPU使用率の計算
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                       stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                          stats['precpu_stats']['system_cpu_usage']
            cpu_percent = (cpu_delta / system_delta) * 100.0
            
            total_cpu += cpu_percent
            total_memory += stats['memory_stats']['usage']
        
        avg_cpu = total_cpu / len(containers)
        avg_memory = total_memory / len(containers) / (1024 * 1024)  # MB
        
        return {"cpu": avg_cpu, "memory": avg_memory, "replicas": len(containers)}
    
    def scale(self, replicas: int):
        subprocess.run([
            "docker-compose", "scale", 
            f"{self.service_name}={replicas}"
        ])
    
    def auto_scale(self):
        while True:
            metrics = self.get_metrics()
            current_replicas = int(metrics['replicas'])
            
            if metrics['cpu'] > self.scale_up_threshold:
                new_replicas = min(current_replicas + 1, self.max_replicas)
                if new_replicas > current_replicas:
                    print(f"スケールアップ: {current_replicas} → {new_replicas}")
                    self.scale(new_replicas)
            
            elif metrics['cpu'] < self.scale_down_threshold:
                new_replicas = max(current_replicas - 1, self.min_replicas)
                if new_replicas < current_replicas:
                    print(f"スケールダウン: {current_replicas} → {new_replicas}")
                    self.scale(new_replicas)
            
            time.sleep(30)  # 30秒ごとにチェック
```

## 6. モニタリングとロギング

### 6.1 統合モニタリングスタック

```yaml
# docker-compose.monitoring.yml
version: '3.9'

services:
  # Prometheus（メトリクス収集）
  prometheus:
    image: prom/prometheus:latest
    container_name: pm_scoring_prometheus
    volumes:
      - ./docker/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    ports:
      - "9090:9090"
    networks:
      - scoring_network
  
  # Grafana（可視化）
  grafana:
    image: grafana/grafana:latest
    container_name: pm_scoring_grafana
    environment:
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-admin}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./docker/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./docker/grafana/datasources:/etc/grafana/provisioning/datasources
    ports:
      - "3001:3000"
    networks:
      - scoring_network
  
  # Loki（ログ収集）
  loki:
    image: grafana/loki:latest
    container_name: pm_scoring_loki
    ports:
      - "3100:3100"
    volumes:
      - ./docker/loki/loki-config.yml:/etc/loki/local-config.yaml
      - loki_data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - scoring_network
  
  # Promtail（ログ転送）
  promtail:
    image: grafana/promtail:latest
    container_name: pm_scoring_promtail
    volumes:
      - ./docker/promtail/promtail-config.yml:/etc/promtail/config.yml
      - /var/run/docker.sock:/var/run/docker.sock
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    command: -config.file=/etc/promtail/config.yml
    networks:
      - scoring_network
  
  # Node Exporter（ホストメトリクス）
  node_exporter:
    image: prom/node-exporter:latest
    container_name: pm_scoring_node_exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--path.rootfs=/rootfs'
    networks:
      - scoring_network
  
  # cAdvisor（コンテナメトリクス）
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: pm_scoring_cadvisor
    ports:
      - "8081:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker:/var/lib/docker:ro
      - /dev/disk:/dev/disk:ro
    devices:
      - /dev/kmsg
    networks:
      - scoring_network

volumes:
  prometheus_data:
  grafana_data:
  loki_data:
```

### 6.2 アプリケーションメトリクス実装

```python
# metrics.py - Prometheusメトリクスエクスポート
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Request, Response
import time

# メトリクス定義
request_count = Counter(
    'http_requests_total', 
    'Total HTTP requests', 
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

active_scoring_tasks = Gauge(
    'active_scoring_tasks',
    'Number of active scoring tasks'
)

scoring_accuracy = Histogram(
    'scoring_accuracy',
    'Scoring accuracy compared to human scores',
    buckets=[0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0]
)

# ミドルウェア
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

# メトリクスエンドポイント
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## 7. セキュリティ強化

### 7.1 コンテナセキュリティ設定

```yaml
# docker-compose.security.yml
version: '3.9'

services:
  api:
    security_opt:
      - no-new-privileges:true
      - apparmor:docker-default
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
    tmpfs:
      - /tmp
      - /var/run
    user: "1000:1000"
    environment:
      PYTHONDONTWRITEBYTECODE: 1
  
  postgres:
    security_opt:
      - no-new-privileges:true
    environment:
      POSTGRES_INITDB_ARGS: "--auth-local=scram-sha-256 --auth-host=scram-sha-256"
    volumes:
      - postgres_data:/var/lib/postgresql/data:Z  # SELinux対応
    secrets:
      - db_password
  
  # Secrets定義
secrets:
  db_password:
    file: ./secrets/db_password.txt
  api_key:
    file: ./secrets/api_key.txt
  jwt_secret:
    file: ./secrets/jwt_secret.txt
```

### 7.2 ネットワークセグメンテーション

```yaml
networks:
  frontend_network:
    driver: bridge
    internal: false
    ipam:
      config:
        - subnet: 172.28.1.0/24
  
  backend_network:
    driver: bridge
    internal: true  # 外部アクセス禁止
    ipam:
      config:
        - subnet: 172.28.2.0/24
  
  database_network:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.28.3.0/24

services:
  nginx:
    networks:
      - frontend_network
  
  api:
    networks:
      - frontend_network
      - backend_network
  
  postgres:
    networks:
      - database_network
  
  ai_engine:
    networks:
      - backend_network
```

## 8. CI/CD統合

### 8.1 GitHub Actions設定

```yaml
# .github/workflows/docker-ci.yml
name: Docker CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Run tests
        run: |
          docker-compose -f docker-compose.test.yml up --abort-on-container-exit
          docker-compose -f docker-compose.test.yml down
  
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push Docker images
        uses: docker/build-push-action@v4
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

## 9. トラブルシューティングガイド

### 9.1 一般的な問題と解決策

| 問題 | 症状 | 解決策 |
|-----|------|--------|
| コンテナが起動しない | `docker-compose up`でエラー | 1. `docker-compose logs [service]`でログ確認<br>2. `.env`ファイルの確認<br>3. ポート競合の確認 |
| メモリ不足 | コンテナがOOMKillerで終了 | 1. Docker Desktop設定でメモリ増加<br>2. `deploy.resources.limits`調整 |
| GPU認識しない | AI Engineエラー | 1. `nvidia-docker2`インストール確認<br>2. `docker run --gpus all nvidia/cuda nvidia-smi`で確認 |
| データベース接続エラー | API起動失敗 | 1. PostgreSQLのヘルスチェック<br>2. 接続文字列の確認<br>3. ネットワーク設定確認 |
| ビルドが遅い | イメージビルドに時間がかかる | 1. BuildKitの有効化<br>2. マルチステージビルド使用<br>3. `.dockerignore`の最適化 |

### 9.2 デバッグコマンド集

```bash
# コンテナ内部調査
docker-compose exec api /bin/bash
docker-compose exec postgres psql -U scoring_user -d pm_scoring

# ログ調査
docker-compose logs --tail=100 -f api
docker logs $(docker ps -q -f name=pm_scoring_api)

# リソース使用状況
docker stats
docker system df
docker-compose top

# ネットワーク調査
docker network inspect pm_scoring_scoring_network
docker-compose exec api ping postgres

# ボリューム調査
docker volume ls
docker volume inspect pm_scoring_postgres_data

# クリーンアップ
docker system prune -a --volumes
docker-compose down --rmi all --volumes --remove-orphans
```

## 10. パフォーマンスチューニング

### 10.1 データベース最適化

```sql
-- PostgreSQL設定最適化
ALTER SYSTEM SET shared_buffers = '2GB';
ALTER SYSTEM SET effective_cache_size = '6GB';
ALTER SYSTEM SET maintenance_work_mem = '512MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '10MB';
ALTER SYSTEM SET min_wal_size = '1GB';
ALTER SYSTEM SET max_wal_size = '4GB';
```

### 10.2 Redisチューニング

```conf
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
```

## まとめ

この追加設計により、Docker環境での採点システムは以下の特徴を持ちます：

1. **高可用性**: ヘルスチェックと自動リカバリ
2. **スケーラビリティ**: 水平スケーリングとオートスケーリング
3. **可観測性**: 包括的なモニタリングとロギング
4. **セキュリティ**: コンテナセキュリティとネットワーク分離
5. **運用効率**: CI/CD統合と自動化
6. **パフォーマンス**: 最適化とチューニング

これらの機能により、開発から本番運用まで、信頼性の高い採点システムの構築が可能になります。