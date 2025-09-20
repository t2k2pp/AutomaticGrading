"""
AI採点エンジン - メインアプリケーション
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from contextlib import asynccontextmanager

from .config import settings
from .llm.manager import llm_manager
from .llm import LLMProvider, ScoringCriteria

# ロギング設定
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    logger.info("AI採点エンジンを起動中...")

    # LLMプロバイダー初期化
    try:
        # LMStudioプロバイダーの初期化
        lmstudio_config = {
            "base_url": settings.LMSTUDIO_URL,
            "model": settings.LMSTUDIO_MODEL,
            "timeout": 120,
            "max_tokens": 2000,
            "temperature": 0.1
        }

        if await llm_manager.initialize_provider(LLMProvider.LMSTUDIO, lmstudio_config):
            logger.info("LMStudio プロバイダーを初期化しました")
            app.state.llm_available = True
        else:
            logger.warning("LMStudio プロバイダーの初期化に失敗しました")
            app.state.llm_available = False

    except Exception as e:
        logger.error(f"LLM初期化エラー: {e}")
        app.state.llm_available = False

    yield

    logger.info("AI採点エンジンを停止中...")


# FastAPIアプリケーション初期化
app = FastAPI(
    title="PM試験AI採点エンジン",
    description="IPAプロジェクトマネージャ試験AI採点エンジン",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    lifespan=lifespan
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # AI Engineは内部利用のため
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import time


class ScoringRequest(BaseModel):
    """採点リクエスト"""
    answer_text: str = Field(..., description="解答文")
    question_data: Dict[str, Any] = Field(..., description="問題データ")

    class Config:
        schema_extra = {
            "example": {
                "answer_text": "プロジェクトメンバーのスキル不足により、設計品質が低下し、テスト工程で多数の不具合が発見されたため。",
                "question_data": {
                    "question_text": "プロジェクトでリスクが顕在化した理由を40字以内で述べよ。",
                    "model_answer": "要員のスキル不足により、設計段階での品質問題が見過ごされ、後工程で大規模な手戻りが発生したため。",
                    "keywords": ["スキル不足", "品質問題", "手戻り"],
                    "grading_intention": "リスク管理の理解度を評価する",
                    "max_chars": 40,
                    "points": 25
                }
            }
        }


class ScoringResponse(BaseModel):
    """採点レスポンス"""
    total_score: float
    max_score: float
    percentage: float
    confidence: float
    rule_based_score: Optional[float]
    semantic_score: Optional[float]
    comprehensive_score: Optional[float]
    details: Dict[str, Any]
    reasons: List[str]
    suggestions: List[str]
    model_name: str
    temperature: Optional[float]
    tokens_used: int
    processing_time_ms: int


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "PM試験AI採点エンジン",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "llm_available": getattr(app.state, 'llm_available', False)
    }


@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    llm_available = getattr(app.state, 'llm_available', False)

    # LLMプロバイダーの状態をチェック
    provider_status = {}
    if llm_available:
        try:
            provider_status = await llm_manager.health_check_all()
        except Exception:
            provider_status = {}

    return {
        "status": "healthy",
        "llm_available": llm_available,
        "providers": provider_status,
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time()
    }


@app.post("/score", response_model=ScoringResponse)
async def score_answer(request: ScoringRequest):
    """解答採点"""
    start_time = time.time()

    try:
        if not getattr(app.state, 'llm_available', False):
            raise HTTPException(
                status_code=503,
                detail="LLMサービスが利用できません。LMStudioが起動していることを確認してください。"
            )

        # LLMによる採点
        criteria = ScoringCriteria(
            question_text=request.question_data.get("question_text", ""),
            answer_text=request.answer_text,
            max_score=request.question_data.get("points", 25)
        )

        llm_result = await llm_manager.score_answer(criteria)

        # レスポンス形式に変換
        processing_time = int((time.time() - start_time) * 1000)

        result = {
            "total_score": llm_result.total_score,
            "max_score": criteria.max_score,
            "percentage": (llm_result.total_score / criteria.max_score) * 100,
            "confidence": llm_result.confidence,
            "rule_based_score": None,  # LLMでは使用しない
            "semantic_score": None,    # LLMでは使用しない
            "comprehensive_score": llm_result.total_score,  # LLMスコアを総合スコアとする
            "details": {
                "method": "llm_scoring",
                "provider": llm_manager.get_provider().provider_type.value,
                "aspect_scores": llm_result.aspect_scores,
                "reasoning": llm_result.reasoning
            },
            "reasons": [llm_result.detailed_feedback],
            "suggestions": [],  # LLMからの提案があれば追加
            "model_name": llm_manager.get_provider().config.get("model", "unknown"),
            "temperature": llm_manager.get_provider().config.get("temperature"),
            "tokens_used": 0,  # 実装時に追加
            "processing_time_ms": processing_time
        }

        return ScoringResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"採点エラー: {e}")
        raise HTTPException(status_code=500, detail=f"採点処理に失敗しました: {str(e)}")




if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower()
    )