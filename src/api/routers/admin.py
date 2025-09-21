"""
管理者APIエンドポイント
試験・問題の登録・管理機能
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import csv
import io
import logging

from ..database import get_db, SessionLocal
from ..models.exam import Exam, ExamSeason
from ..models.question import Question
from ..auth.admin_auth import AdminAuth

router = APIRouter()
logger = logging.getLogger(__name__)


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
    question_number: str
    background_text: str
    question_text: str
    sub_questions: Optional[List[str]] = None
    model_answer: str
    max_chars: int = 400
    points: int = 25
    grading_intention: Optional[str] = None
    grading_commentary: Optional[str] = None
    keywords: Optional[List[str]] = None

class QuestionUpdate(BaseModel):
    title: Optional[str] = None
    question_number: Optional[str] = None
    background_text: Optional[str] = None
    question_text: Optional[str] = None
    sub_questions: Optional[List[str]] = None
    model_answer: Optional[str] = None
    max_chars: Optional[int] = None
    points: Optional[int] = None
    grading_intention: Optional[str] = None
    grading_commentary: Optional[str] = None
    keywords: Optional[List[str]] = None

class QuestionResponse(BaseModel):
    id: int
    exam_id: int
    title: str
    question_number: str
    background_text: str
    question_text: str
    sub_questions: Optional[List[str]]
    model_answer: str
    max_chars: int
    points: int
    grading_intention: Optional[str]
    grading_commentary: Optional[str]
    keywords: Optional[List[str]]
    has_sub_questions: bool
    display_name: str

    class Config:
        from_attributes = True


class QuestionCSVPreview(BaseModel):
    """問題CSV プレビュー"""
    total_rows: int
    sample_data: List[Dict[str, str]]
    column_mapping: Dict[str, str]
    detected_issues: List[str]


class QuestionCSVUploadStatus(BaseModel):
    """問題CSV アップロード状況"""
    upload_id: str
    status: str  # "uploading", "processing", "completed", "error"
    total_count: int
    processed_count: int
    success_count: int
    error_count: int
    progress_percentage: int
    message: str
    errors: List[str] = []


@router.post("/exams", response_model=ExamResponse)
async def create_exam(
    exam: ExamCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(AdminAuth.require_admin_auth)
):
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
async def get_exams(
    db: Session = Depends(get_db),
    _: bool = Depends(AdminAuth.require_admin_auth)
):
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
async def get_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(AdminAuth.require_admin_auth)
):
    """試験詳細を取得"""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="試験が見つかりません")
    return exam


@router.post("/questions", response_model=QuestionResponse)
async def create_question(
    question: QuestionCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(AdminAuth.require_admin_auth)
):
    """問題を作成"""
    try:
        # 試験の存在確認
        exam = db.query(Exam).filter(Exam.id == question.exam_id).first()
        if not exam:
            raise HTTPException(status_code=404, detail="試験が見つかりません")

        db_question = Question(
            exam_id=question.exam_id,
            title=question.title,
            question_number=question.question_number,
            background_text=question.background_text,
            question_text=question.question_text,
            sub_questions=question.sub_questions,
            model_answer=question.model_answer,
            max_chars=question.max_chars,
            points=question.points,
            grading_intention=question.grading_intention,
            grading_commentary=question.grading_commentary,
            keywords=question.keywords
        )
        db.add(db_question)
        db.commit()
        db.refresh(db_question)

        # レスポンス用にデータを辞書で返す
        return {
            "id": db_question.id,
            "exam_id": db_question.exam_id,
            "title": db_question.title,
            "question_number": db_question.question_number,
            "background_text": db_question.background_text,
            "question_text": db_question.question_text,
            "sub_questions": db_question.sub_questions,
            "model_answer": db_question.model_answer,
            "max_chars": db_question.max_chars,
            "points": db_question.points,
            "grading_intention": db_question.grading_intention,
            "grading_commentary": db_question.grading_commentary,
            "keywords": db_question.keywords,
            "has_sub_questions": db_question.has_sub_questions,
            "display_name": db_question.display_name
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"問題作成に失敗しました: {str(e)}")


@router.get("/questions", response_model=List[QuestionResponse])
async def get_questions(
    exam_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: bool = Depends(AdminAuth.require_admin_auth)
):
    """問題一覧を取得"""
    query = db.query(Question)
    if exam_id:
        query = query.filter(Question.exam_id == exam_id)
    return query.all()


@router.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(AdminAuth.require_admin_auth)
):
    """問題詳細を取得"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="問題が見つかりません")
    return question


@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: int,
    question_update: QuestionUpdate,
    db: Session = Depends(get_db),
    _: bool = Depends(AdminAuth.require_admin_auth)
):
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
async def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(AdminAuth.require_admin_auth)
):
    """問題を削除"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="問題が見つかりません")

    db.delete(question)
    db.commit()
    return {"message": "問題を削除しました"}


@router.post("/questions/csv/preview")
async def preview_questions_csv_upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: bool = Depends(AdminAuth.require_admin_auth)
) -> QuestionCSVPreview:
    """
    問題CSVファイルの内容をプレビュー表示
    管理者が確認してから実際のアップロードを実行
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="CSVファイルを選択してください。他のファイル形式は対応していません。"
        )

    try:
        # CSVファイルを読み取り
        content = await file.read()
        csv_content = content.decode('utf-8-sig')  # BOM付きUTF-8に対応

        # CSV解析
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(csv_reader)

        if not rows:
            raise HTTPException(
                status_code=400,
                detail="CSVファイルにデータが含まれていません。"
            )

        # カラム名の検出と推定
        fieldnames = csv_reader.fieldnames or []
        column_mapping = _detect_question_column_mapping(fieldnames)

        # データ品質チェック
        issues = _check_question_data_quality(rows, column_mapping)

        # サンプルデータ（最初の3行）
        sample_data = rows[:3]

        return QuestionCSVPreview(
            total_rows=len(rows),
            sample_data=sample_data,
            column_mapping=column_mapping,
            detected_issues=issues
        )

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="ファイルの文字コードが正しくありません。UTF-8形式で保存し直してください。"
        )
    except Exception as e:
        logger.error(f"Question CSV preview error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"CSVファイルの読み込みに失敗しました: {str(e)}"
        )


@router.post("/questions/csv/execute")
async def execute_questions_csv_upload(
    background_tasks: BackgroundTasks,
    exam_name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: bool = Depends(AdminAuth.require_admin_auth)
) -> Dict[str, str]:
    """
    問題CSV一括アップロード実行
    バックグラウンドで処理し、進捗確認用のIDを返す
    """
    try:
        # アップロードIDを生成
        upload_id = f"questions_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # CSVファイル読み取り
        content = await file.read()
        csv_content = content.decode('utf-8-sig')

        # バックグラウンドタスクで処理開始
        # セッションファクトリを渡してタスク内で新しいセッションを作成
        background_tasks.add_task(
            _process_questions_csv_upload,
            upload_id,
            csv_content,
            exam_name
        )

        return {
            "upload_id": upload_id,
            "message": "問題一括アップロードを開始しました。進捗は「処理状況確認」で確認できます。"
        }

    except Exception as e:
        logger.error(f"Questions CSV upload start error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"アップロード開始に失敗しました: {str(e)}"
        )


@router.get("/questions/csv/status/{upload_id}")
async def get_questions_upload_status(
    upload_id: str,
    _: bool = Depends(AdminAuth.require_admin_auth)
) -> QuestionCSVUploadStatus:
    """
    問題アップロード処理状況確認
    """
    # 実際の実装では Redis や データベースから状況を取得
    # ここでは簡易実装
    return QuestionCSVUploadStatus(
        upload_id=upload_id,
        status="processing",
        total_count=3,
        processed_count=2,
        success_count=2,
        error_count=0,
        progress_percentage=67,
        message="問題データを処理中です...",
        errors=[]
    )


def _detect_question_column_mapping(fieldnames: List[str]) -> Dict[str, str]:
    """
    問題CSVカラム名から必要な項目を自動検出
    """
    mapping = {}

    # 候補パターン
    patterns = {
        "question_number": ["問題番号", "問題No", "Question Number", "問番"],
        "title": ["タイトル", "問題タイトル", "Title", "題名"],
        "background_text": ["背景情報", "背景", "Background", "前提"],
        "question_text": ["設問文", "問題文", "Question", "設問"],
        "model_answer": ["模範解答", "解答例", "Model Answer", "正解"],
        "points": ["配点", "点数", "Points", "Score"],
        "max_chars": ["文字制限", "最大文字数", "Max Chars", "制限"],
        "grading_intention": ["出題趣旨", "採点観点", "Grading Intention"],
        "grading_commentary": ["採点講評", "講評", "Commentary"],
        "keywords": ["キーワード", "Keywords", "重要語句"]
    }

    for field in fieldnames:
        for key, candidates in patterns.items():
            if any(candidate in field for candidate in candidates):
                mapping[key] = field
                break

    return mapping


def _check_question_data_quality(rows: List[Dict], column_mapping: Dict[str, str]) -> List[str]:
    """
    問題データ品質チェック
    """
    issues = []

    # 必要カラムの存在確認
    required_fields = ["question_number", "title", "question_text", "model_answer"]
    for field in required_fields:
        if field not in column_mapping:
            issues.append(f"必要な項目「{field}」が見つかりません")

    # データ内容チェック
    if column_mapping:
        # 問題番号の重複チェック
        question_numbers = [row.get(column_mapping.get("question_number", ""), "").strip() for row in rows]
        if len(question_numbers) != len(set(question_numbers)):
            issues.append("問題番号に重複があります")

        # 空欄チェック
        for i, row in enumerate(rows, 1):
            if not row.get(column_mapping.get("question_number", ""), "").strip():
                issues.append(f"行{i}: 問題番号が空白です")
            if not row.get(column_mapping.get("title", ""), "").strip():
                issues.append(f"行{i}: タイトルが空白です")
            if not row.get(column_mapping.get("question_text", ""), "").strip():
                issues.append(f"行{i}: 設問文が空白です")
            if not row.get(column_mapping.get("model_answer", ""), "").strip():
                issues.append(f"行{i}: 模範解答が空白です")

    return issues


async def _process_questions_csv_upload(
    upload_id: str,
    csv_content: str,
    exam_name: str
):
    """
    バックグラウンドで問題CSV処理実行
    """
    # バックグラウンドタスク用の独立したDBセッションを作成
    db = SessionLocal()
    try:
        logger.info(f"Questions CSV upload {upload_id} processing started")

        # CSVを解析
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(csv_reader)

        # カラムマッピングを検出
        column_mapping = _detect_question_column_mapping(csv_reader.fieldnames or [])

        # 1. 試験を作成
        exam = Exam(
            title=exam_name,
            description=f"CSV一括アップロード試験: {exam_name}",
            year=2024,
            season=ExamSeason.SPRING,
            created_at=datetime.now()
        )
        db.add(exam)
        db.flush()  # IDを取得するため

        # 2. 問題データを一括挿入
        success_count = 0
        error_count = 0
        errors = []

        for i, row in enumerate(rows, 1):
            try:
                # 各項目を取得
                question_number = row.get(column_mapping.get("question_number", ""), "").strip()
                title = row.get(column_mapping.get("title", ""), "").strip()
                background_text = row.get(column_mapping.get("background_text", ""), "").strip()
                question_text = row.get(column_mapping.get("question_text", ""), "").strip()
                model_answer = row.get(column_mapping.get("model_answer", ""), "").strip()
                points_str = row.get(column_mapping.get("points", ""), "25").strip()
                max_chars_str = row.get(column_mapping.get("max_chars", ""), "400").strip()
                grading_intention = row.get(column_mapping.get("grading_intention", ""), "").strip()
                grading_commentary = row.get(column_mapping.get("grading_commentary", ""), "").strip()
                keywords_str = row.get(column_mapping.get("keywords", ""), "").strip()

                # バリデーション
                if not question_number:
                    errors.append(f"行{i}: 問題番号が空白です")
                    error_count += 1
                    continue

                if not title:
                    errors.append(f"行{i}: タイトルが空白です")
                    error_count += 1
                    continue

                if not question_text:
                    errors.append(f"行{i}: 設問文が空白です")
                    error_count += 1
                    continue

                if not model_answer:
                    errors.append(f"行{i}: 模範解答が空白です")
                    error_count += 1
                    continue

                # 数値変換
                try:
                    points = int(points_str) if points_str else 25
                    max_chars = int(max_chars_str) if max_chars_str else 400
                except ValueError:
                    errors.append(f"行{i}: 配点または文字制限が数値ではありません")
                    error_count += 1
                    continue

                # キーワード処理
                keywords = None
                if keywords_str:
                    keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]

                # 問題レコード作成
                question = Question(
                    exam_id=exam.id,
                    title=title,
                    question_number=question_number,
                    background_text=background_text or "",
                    question_text=question_text,
                    sub_questions=None,
                    model_answer=model_answer,
                    max_chars=max_chars,
                    points=points,
                    grading_intention=grading_intention or "",
                    grading_commentary=grading_commentary or "",
                    keywords=keywords
                )
                db.add(question)
                db.flush()

                success_count += 1

            except Exception as row_error:
                logger.error(f"Question row processing error {i}: {str(row_error)}")
                errors.append(f"行{i}: データ処理に失敗しました - {str(row_error)}")
                error_count += 1

        # 変更をコミット
        db.commit()

        logger.info(f"Questions CSV upload {upload_id} completed: {success_count} success, {error_count} errors")

        # TODO: 実際の実装では進捗状況をRedisに保存
        # _save_upload_status(upload_id, "completed", success_count, error_count, errors)

    except Exception as e:
        logger.error(f"Questions CSV upload {upload_id} failed: {str(e)}")
        db.rollback()
        # TODO: エラー状態をRedisに保存
        # _save_upload_status(upload_id, "error", 0, 0, [str(e)])
    finally:
        # バックグラウンドタスク用のセッションを確実にクローズ
        db.close()


@router.get("/")
async def admin_info():
    """管理者API情報"""
    return {
        "message": "PM試験AI採点システム 管理API",
        "version": "1.0.0",
        "features": [
            "試験作成・管理",
            "問題作成・編集・削除",
            "試験・問題一覧取得",
            "問題CSV一括アップロード"
        ],
        "status": "利用可能"
    }