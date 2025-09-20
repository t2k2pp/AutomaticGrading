"""
採点サービス
"""
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import httpx
import asyncio
from datetime import datetime

from ..models.answer import Answer
from ..models.question import Question
from ..models.scoring import ScoringResult, ScoringStatus, ScoringMethod
from ..config import settings

logger = logging.getLogger(__name__)


class ScoringService:
    """採点サービスクラス"""

    def __init__(self, db: Session):
        self.db = db
        self.ai_engine_url = settings.AI_ENGINE_URL

    async def submit_answer(
        self,
        exam_id: int,
        question_id: int,
        candidate_id: str,
        answer_text: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Answer:
        """解答提出"""
        try:
            # 既存解答チェック
            existing_answer = self.db.query(Answer).filter(
                Answer.exam_id == exam_id,
                Answer.question_id == question_id,
                Answer.candidate_id == candidate_id
            ).first()

            if existing_answer:
                # 解答更新
                existing_answer.answer_text = answer_text
                existing_answer.char_count = len(answer_text)
                existing_answer.is_blank = not bool(answer_text.strip())
                existing_answer.updated_at = datetime.utcnow()
                answer = existing_answer
            else:
                # 新規解答作成
                answer = Answer(
                    exam_id=exam_id,
                    question_id=question_id,
                    candidate_id=candidate_id,
                    answer_text=answer_text,
                    char_count=len(answer_text),
                    is_blank=not bool(answer_text.strip()),
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                self.db.add(answer)

            self.db.commit()
            self.db.refresh(answer)

            logger.info(f"解答提出完了: candidate={candidate_id}, question={question_id}")
            return answer

        except Exception as e:
            self.db.rollback()
            logger.error(f"解答提出エラー: {e}")
            raise

    async def evaluate_answer(self, answer_id: int) -> ScoringResult:
        """AI採点実行"""
        answer = self.db.query(Answer).filter(Answer.id == answer_id).first()
        if not answer:
            raise ValueError(f"解答が見つかりません: {answer_id}")

        # 既存の採点結果チェック
        existing_result = self.db.query(ScoringResult).filter(
            ScoringResult.answer_id == answer_id,
            ScoringResult.status == ScoringStatus.COMPLETED
        ).first()

        if existing_result:
            logger.info(f"既存の採点結果を返します: {answer_id}")
            return existing_result

        # 新規採点結果作成
        scoring_result = ScoringResult(
            answer_id=answer_id,
            status=ScoringStatus.PENDING,
            scoring_method=ScoringMethod.COMPREHENSIVE,
            scoring_started_at=datetime.utcnow()
        )
        self.db.add(scoring_result)
        self.db.commit()

        try:
            # AI採点実行
            scoring_result.status = ScoringStatus.IN_PROGRESS
            self.db.commit()

            scores = await self._perform_ai_scoring(answer)

            # 結果更新
            scoring_result.total_score = scores.get("total_score", 0)
            scoring_result.max_score = scores.get("max_score", 100)
            scoring_result.percentage = scores.get("percentage", 0)
            scoring_result.confidence = scores.get("confidence", 0)

            scoring_result.rule_based_score = scores.get("rule_based_score")
            scoring_result.semantic_score = scores.get("semantic_score")
            scoring_result.comprehensive_score = scores.get("comprehensive_score")

            scoring_result.scoring_details = scores.get("details")
            scoring_result.scoring_reasons = scores.get("reasons")
            scoring_result.suggestions = scores.get("suggestions")

            scoring_result.model_name = scores.get("model_name")
            scoring_result.temperature = scores.get("temperature")
            scoring_result.tokens_used = scores.get("tokens_used")
            scoring_result.processing_time_ms = scores.get("processing_time_ms")

            scoring_result.status = ScoringStatus.COMPLETED
            scoring_result.scoring_completed_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(scoring_result)

            logger.info(f"AI採点完了: answer_id={answer_id}, score={scoring_result.total_score}")
            return scoring_result

        except Exception as e:
            scoring_result.status = ScoringStatus.FAILED
            self.db.commit()
            logger.error(f"AI採点エラー: {e}")
            raise

    async def _perform_ai_scoring(self, answer: Answer) -> Dict[str, Any]:
        """AI Engine による採点実行"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ai_engine_url}/score",
                    json={
                        "answer_text": answer.answer_text,
                        "question_data": {
                            "question_text": answer.question.question_text,
                            "model_answer": answer.question.model_answer,
                            "keywords": answer.question.keyword_list,
                            "grading_intention": answer.question.grading_intention,
                            "max_chars": answer.question.max_chars,
                            "points": answer.question.points
                        }
                    }
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    raise Exception(f"AI Engine error: {response.status_code}")

        except httpx.TimeoutException:
            logger.error("AI Engine timeout")
            # フォールバック: ルールベース採点のみ
            return await self._fallback_scoring(answer)
        except Exception as e:
            logger.error(f"AI Engine error: {e}")
            return await self._fallback_scoring(answer)

    async def _fallback_scoring(self, answer: Answer) -> Dict[str, Any]:
        """フォールバック採点（ルールベースのみ）"""
        # 簡単なキーワードマッチング
        score = 0
        max_score = answer.question.points
        keywords = answer.question.keyword_list

        for keyword in keywords:
            if keyword in answer.answer_text:
                score += max_score * 0.2  # キーワード1つにつき20%

        score = min(score, max_score)
        percentage = (score / max_score) * 100

        return {
            "total_score": score,
            "max_score": max_score,
            "percentage": percentage,
            "confidence": 0.6,  # 低い信頼度
            "rule_based_score": score,
            "semantic_score": None,
            "comprehensive_score": None,
            "details": {"method": "fallback_keyword_matching"},
            "reasons": [f"キーワードマッチングによる採点"],
            "suggestions": ["AI Engineとの接続を確認してください"],
            "model_name": "fallback",
            "temperature": None,
            "tokens_used": 0,
            "processing_time_ms": 100
        }

    def get_scoring_results(self, exam_id: int, candidate_id: Optional[str] = None) -> List[ScoringResult]:
        """採点結果取得"""
        query = self.db.query(ScoringResult).join(Answer).filter(Answer.exam_id == exam_id)

        if candidate_id:
            query = query.filter(Answer.candidate_id == candidate_id)

        return query.all()

    def get_scoring_result_by_id(self, result_id: int) -> Optional[ScoringResult]:
        """採点結果ID指定取得"""
        return self.db.query(ScoringResult).filter(ScoringResult.id == result_id).first()