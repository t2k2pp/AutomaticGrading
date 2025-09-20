"""
管理者APIエンドポイント
試験・問題の登録・管理機能
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ..models.exam import Exam, ExamSeason
from ..models.question import Question

router = APIRouter()


class ExamCreate(BaseModel):
    title: str
    description: Optional[str] = None

class ExamResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class QuestionCreate(BaseModel):
    exam_id: int
    title: str
    text: str
    max_score: int = 25
    char_limit: int = 400

class QuestionUpdate(BaseModel):
    title: Optional[str] = None
    text: Optional[str] = None
    max_score: Optional[int] = None
    char_limit: Optional[int] = None

class QuestionResponse(BaseModel):
    id: int
    exam_id: int
    title: str
    text: str
    max_score: int
    char_limit: int

    class Config:
        from_attributes = True


@router.post("/exams", response_model=ExamResponse)
async def create_exam(exam: ExamCreate, db: Session = Depends(get_db)):
    """試験を作成"""
    try:
        db_exam = Exam(
            title=exam.title,
            description=exam.description,
            year=2024,  # デフォルト値
            season=ExamSeason.SPRING,  # Enumを使用
            created_at=datetime.now()
        )
        db.add(db_exam)
        db.commit()
        db.refresh(db_exam)

        # レスポンス用にデータを辞書で返す
        return {
            "id": db_exam.id,
            "title": db_exam.title,
            "description": db_exam.description,
            "created_at": db_exam.created_at
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"試験作成に失敗しました: {str(e)}")


@router.get("/exams", response_model=List[ExamResponse])
async def get_exams(db: Session = Depends(get_db)):
    """試験一覧を取得"""
    try:
        exams = db.query(Exam).all()
        return [
            {
                "id": exam.id,
                "title": exam.title,
                "description": exam.description,
                "created_at": exam.created_at
            }
            for exam in exams
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"試験一覧取得に失敗しました: {str(e)}")


@router.get("/exams/{exam_id}", response_model=ExamResponse)
async def get_exam(exam_id: int, db: Session = Depends(get_db)):
    """試験詳細を取得"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="試験が見つかりません")
    return exam


@router.post("/questions", response_model=QuestionResponse)
async def create_question(question: QuestionCreate, db: Session = Depends(get_db)):
    """問題を作成"""
    try:
        # 試験の存在確認
        exam = db.query(Exam).filter(Exam.id == question.exam_id).first()
        if not exam:
            raise HTTPException(status_code=404, detail="試験が見つかりません")

        db_question = Question(
            exam_id=question.exam_id,
            title=question.title,
            text=question.text,
            max_score=question.max_score,
            char_limit=question.char_limit
        )
        db.add(db_question)
        db.commit()
        db.refresh(db_question)

        # レスポンス用にデータを辞書で返す
        return {
            "id": db_question.id,
            "exam_id": db_question.exam_id,
            "title": db_question.title,
            "text": db_question.text,
            "max_score": db_question.max_score,
            "char_limit": db_question.char_limit
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"問題作成に失敗しました: {str(e)}")


@router.get("/questions", response_model=List[QuestionResponse])
async def get_questions(exam_id: Optional[int] = None, db: Session = Depends(get_db)):
    """問題一覧を取得"""
    query = db.query(Question)
    if exam_id:
        query = query.filter(Question.exam_id == exam_id)
    return query.all()


@router.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: int, db: Session = Depends(get_db)):
    """問題詳細を取得"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="問題が見つかりません")
    return question


@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(question_id: int, question_update: QuestionUpdate, db: Session = Depends(get_db)):
    """問題を更新"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="問題が見つかりません")

    update_data = question_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(question, field, value)

    db.commit()
    db.refresh(question)
    return question


@router.delete("/questions/{question_id}")
async def delete_question(question_id: int, db: Session = Depends(get_db)):
    """問題を削除"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="問題が見つかりません")

    db.delete(question)
    db.commit()
    return {"message": "問題を削除しました"}


@router.get("/")
async def admin_info():
    """管理者API情報"""
    return {
        "message": "PM試験AI採点システム 管理API",
        "version": "1.0.0",
        "features": [
            "試験作成・管理",
            "問題作成・編集・削除",
            "試験・問題一覧取得"
        ],
        "status": "利用可能"
    }