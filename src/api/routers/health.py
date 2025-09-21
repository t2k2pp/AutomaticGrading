"""
ヘルスチェックエンドポイント
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False
import httpx
import time
from typing import Dict, Any
import logging

from ..database import get_db
from ..config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class HealthChecker:
    def __init__(self):
        self.start_time = time.time()
        self.redis_client = None
        self._init_redis()

    def _init_redis(self):
        """Redis接続初期化"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis module not available, skipping Redis initialization")
            return
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL)
        except Exception as e:
            logger.warning(f"Redis接続の初期化に失敗: {e}")

    async def check_database(self, db: Session) -> Dict[str, Any]:
        """データベースヘルスチェック"""
        try:
            start = time.time()
            result = db.execute(text("SELECT 1"))
            latency = (time.time() - start) * 1000
            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "connection": "active"
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "connection": "failed"
            }

    async def check_redis(self) -> Dict[str, Any]:
        """Redisヘルスチェック"""
        if not self.redis_client:
            return {
                "status": "unhealthy",
                "error": "Redis client not initialized"
            }

        try:
            start = time.time()
            self.redis_client.ping()
            latency = (time.time() - start) * 1000
            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "connection": "active"
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "connection": "failed"
            }

    async def check_ai_engine(self) -> Dict[str, Any]:
        """AI Engineヘルスチェック"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.AI_ENGINE_URL}/health")
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "status": "healthy",
                        "url": settings.AI_ENGINE_URL,
                        "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2),
                        "model_status": data.get("model_loaded", "unknown")
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"HTTP {response.status_code}",
                        "url": settings.AI_ENGINE_URL
                    }
        except httpx.TimeoutException:
            return {
                "status": "unhealthy",
                "error": "Connection timeout",
                "url": settings.AI_ENGINE_URL
            }
        except Exception as e:
            logger.error(f"AI Engine health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "url": settings.AI_ENGINE_URL
            }

    async def get_health_status(self, db: Session) -> Dict[str, Any]:
        """総合ヘルスステータス取得"""
        uptime = time.time() - self.start_time

        checks = {
            "database": await self.check_database(db),
            "redis": await self.check_redis(),
            "ai_engine": await self.check_ai_engine()
        }

        # 総合ステータス判定
        healthy_services = sum(1 for check in checks.values() if check["status"] == "healthy")
        total_services = len(checks)

        if healthy_services == total_services:
            overall_status = "healthy"
        elif healthy_services > 0:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"

        return {
            "status": overall_status,
            "uptime_seconds": round(uptime, 2),
            "environment": settings.ENVIRONMENT,
            "version": "1.0.0",
            "timestamp": time.time(),
            "services": checks,
            "summary": {
                "healthy": healthy_services,
                "total": total_services,
                "degraded": total_services - healthy_services
            }
        }


# ヘルスチェッカーインスタンス
health_checker = HealthChecker()


@router.get("/")
async def health_check(db: Session = Depends(get_db)):
    """総合ヘルスチェック"""
    status = await health_checker.get_health_status(db)

    if status["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=status
        )

    return status


@router.get("/live")
async def liveness_probe():
    """Kubernetesライブネスプローブ"""
    return {
        "status": "alive",
        "timestamp": time.time(),
        "uptime_seconds": round(time.time() - health_checker.start_time, 2)
    }


@router.get("/ready")
async def readiness_probe(db: Session = Depends(get_db)):
    """Kubernetesレディネスプローブ"""
    status = await health_checker.get_health_status(db)

    if status["status"] != "healthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )

    return {
        "status": "ready",
        "timestamp": time.time()
    }


@router.get("/metrics")
async def basic_metrics():
    """基本メトリクス"""
    return {
        "uptime_seconds": round(time.time() - health_checker.start_time, 2),
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
        "timestamp": time.time()
    }