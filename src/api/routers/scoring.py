"""
採点APIエンドポイント
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
import logging

from ..database import get_db
from ..services.scoring_service import ScoringService
from ..models.scoring import ScoringResult
from ..models.answer import Answer

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydanticモデル定義
class AnswerSubmissionRequest(BaseModel):
    exam_id: int = Field(..., description="試験ID")
    question_id: int = Field(..., description="問題ID")
    candidate_id: str = Field(..., description="受験者ID（匿名化済み）")
    answer_text: str = Field(..., description="解答文")

    model_config = {
        "json_schema_extra": {
            "example": {
                "exam_id": 1,
                "question_id": 1,
                "candidate_id": "TEST001",
                "answer_text": "プロジェクトメンバーのスキル不足により、設計品質が低下し、テスト工程で多数の不具合が発見されたため。"
            }
        }
    }


class EvaluationRequest(BaseModel):
    answer_id: int = Field(..., description="解答ID")

    model_config = {
        "json_schema_extra": {
            "example": {
                "answer_id": 1
            }
        }
    }


class AnswerResponse(BaseModel):
    id: int
    exam_id: int
    question_id: int
    candidate_id: str
    answer_text: str
    char_count: int
    is_blank: bool
    submitted_at: str

    class Config:
        from_attributes = True


class ScoringResultResponse(BaseModel):
    id: int
    answer_id: int
    status: str
    total_score: Optional[float]
    max_score: Optional[float]
    percentage: Optional[float]
    confidence: Optional[float]
    rule_based_score: Optional[float]
    semantic_score: Optional[float]
    comprehensive_score: Optional[float]
    is_reviewed: bool
    final_score: Optional[float]
    grade: str

    class Config:
        from_attributes = True


@router.get("/")
async def scoring_info():
    """採点API情報"""
    return {
        "message": "PM試験AI採点API",
        "version": "1.0.0",
        "endpoints": [
            "POST /submit - 解答提出",
            "GET /results/{exam_id} - 採点結果取得",
            "POST /evaluate - AI採点実行",
            "GET /result/{result_id} - 採点結果詳細取得"
        ],
        "status": "operational"
    }


@router.post("/submit", response_model=AnswerResponse)
async def submit_answer(
    request: AnswerSubmissionRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """解答提出"""
    try:
        service = ScoringService(db)

        # クライアント情報取得
        ip_address = req.client.host if req.client else None
        user_agent = req.headers.get("user-agent")

        answer = await service.submit_answer(
            exam_id=request.exam_id,
            question_id=request.question_id,
            candidate_id=request.candidate_id,
            answer_text=request.answer_text,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return AnswerResponse(
            id=answer.id,
            exam_id=answer.exam_id,
            question_id=answer.question_id,
            candidate_id=answer.candidate_id,
            answer_text=answer.answer_text,
            char_count=answer.char_count,
            is_blank=answer.is_blank,
            submitted_at=answer.submitted_at.isoformat()
        )

    except Exception as e:
        logger.error(f"解答提出エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"解答提出に失敗しました: {str(e)}"
        )


@router.post("/evaluate", response_model=ScoringResultResponse)
async def evaluate_answer(
    request: EvaluationRequest,
    db: Session = Depends(get_db)
):
    """AI採点実行"""
    try:
        service = ScoringService(db)
        result = await service.evaluate_answer(request.answer_id)

        return ScoringResultResponse(
            id=result.id,
            answer_id=result.answer_id,
            status=result.status.value,
            total_score=result.total_score,
            max_score=result.max_score,
            percentage=result.percentage,
            confidence=result.confidence,
            rule_based_score=result.rule_based_score,
            semantic_score=result.semantic_score,
            comprehensive_score=result.comprehensive_score,
            is_reviewed=result.is_reviewed,
            final_score=result.final_score,
            grade=result.grade
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"AI採点エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI採点に失敗しました: {str(e)}"
        )


@router.get("/results/{exam_id}", response_model=List[ScoringResultResponse])
async def get_results(
    exam_id: int,
    candidate_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """採点結果取得"""
    try:
        service = ScoringService(db)
        results = service.get_scoring_results(exam_id, candidate_id)

        return [
            ScoringResultResponse(
                id=result.id,
                answer_id=result.answer_id,
                status=result.status.value,
                total_score=result.total_score,
                max_score=result.max_score,
                percentage=result.percentage,
                confidence=result.confidence,
                rule_based_score=result.rule_based_score,
                semantic_score=result.semantic_score,
                comprehensive_score=result.comprehensive_score,
                is_reviewed=result.is_reviewed,
                final_score=result.final_score,
                grade=result.grade
            )
            for result in results
        ]

    except Exception as e:
        logger.error(f"採点結果取得エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"採点結果の取得に失敗しました: {str(e)}"
        )


@router.get("/result/{result_id}", response_model=ScoringResultResponse)
async def get_result_detail(
    result_id: int,
    db: Session = Depends(get_db)
):
    """採点結果詳細取得"""
    try:
        service = ScoringService(db)
        result = service.get_scoring_result_by_id(result_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="採点結果が見つかりません"
            )

        return ScoringResultResponse(
            id=result.id,
            answer_id=result.answer_id,
            status=result.status.value,
            total_score=result.total_score,
            max_score=result.max_score,
            percentage=result.percentage,
            confidence=result.confidence,
            rule_based_score=result.rule_based_score,
            semantic_score=result.semantic_score,
            comprehensive_score=result.comprehensive_score,
            is_reviewed=result.is_reviewed,
            final_score=result.final_score,
            grade=result.grade
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"採点結果詳細取得エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"採点結果詳細の取得に失敗しました: {str(e)}"
        )