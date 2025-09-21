"""
PM試験AI採点システム - FastAPIメインアプリケーション
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
import time
from contextlib import asynccontextmanager

from .config import settings
from .database import engine, Base
from .routers import health, scoring, admin, batch_upload, export
from .models import exam, question, answer, scoring as scoring_models

# ロギング設定
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時処理
    logger.info("PM採点システムを起動中...")

    # データベーステーブル作成
    Base.metadata.create_all(bind=engine)
    logger.info("データベーステーブルを初期化しました")

    # 初期データ投入
    try:
        from .database import SessionLocal
        from .utils.init_data import create_initial_data

        db = SessionLocal()
        init_result = create_initial_data(db)
        logger.info(f"初期データ投入結果: {init_result['message']}")
        db.close()
    except Exception as e:
        logger.error(f"初期データ投入エラー: {e}")

    yield

    # 終了時処理
    logger.info("PM採点システムを停止中...")


# FastAPIアプリケーション初期化
app = FastAPI(
    title="PM試験AI採点システム",
    description="IPAプロジェクトマネージャ試験の記述式問題AI一次採点システム",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001", "http://localhost:3002", "http://127.0.0.1:3002"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# セキュリティミドルウェア
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.example.com"]
    )


# リクエスト処理時間計測ミドルウェア
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# グローバル例外ハンドラ
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "システムエラーが発生しました",
            "detail": str(exc) if settings.ENVIRONMENT == "development" else None
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


# ルーター登録
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(scoring.router, prefix="/api/scoring", tags=["Scoring"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(batch_upload.router, prefix="/api/batch-upload", tags=["Batch Upload"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "PM試験AI採点システム",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs" if settings.ENVIRONMENT == "development" else "disabled"
    }


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower()
    )