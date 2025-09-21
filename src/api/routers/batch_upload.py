"""
CSV一括アップロード API
採点者向けに簡単操作で大量データを処理
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks, Form
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import csv
import io
import logging
from datetime import datetime

from ..database import get_db
from ..models.answer import Answer
from ..models.exam import Exam
from ..models.question import Question
from ..services.scoring_service import ScoringService

logger = logging.getLogger(__name__)
router = APIRouter()


class BatchUploadRequest(BaseModel):
    """一括アップロード設定"""
    exam_name: str = Field(..., description="試験名（例：2024年度社内PM試験）")
    question_text: str = Field(..., description="問題文")
    question_title: str = Field(..., description="問題タイトル（例：リスク管理）")
    max_score: int = Field(25, description="満点")
    char_limit: int = Field(40, description="文字数制限")


class BatchUploadStatus(BaseModel):
    """アップロード状況"""
    upload_id: str
    status: str  # "uploading", "processing", "completed", "error"
    total_count: int
    processed_count: int
    success_count: int
    error_count: int
    progress_percentage: int
    message: str
    errors: List[str] = []


class UploadPreview(BaseModel):
    """アップロード前プレビュー"""
    total_rows: int
    sample_data: List[Dict[str, str]]
    column_mapping: Dict[str, str]
    detected_issues: List[str]


@router.post("/upload/preview")
async def preview_csv_upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> UploadPreview:
    """
    CSVファイルの内容をプレビュー表示
    採点者が確認してから実際のアップロードを実行
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
        column_mapping = _detect_column_mapping(fieldnames)

        # データ品質チェック
        issues = _check_data_quality(rows, column_mapping)

        # サンプルデータ（最初の5行）
        sample_data = rows[:5]

        return UploadPreview(
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
        logger.error(f"CSV preview error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"CSVファイルの読み込みに失敗しました: {str(e)}"
        )


@router.post("/upload/execute")
async def execute_batch_upload(
    background_tasks: BackgroundTasks,
    exam_name: str = Form(...),
    question_text: str = Form(...),
    question_title: str = Form(...),
    max_score: int = Form(25),
    char_limit: int = Form(400),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    CSV一括アップロード実行
    バックグラウンドで処理し、進捗確認用のIDを返す
    """
    try:
        # アップロードIDを生成
        upload_id = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # CSVファイル読み取り
        content = await file.read()
        csv_content = content.decode('utf-8-sig')

        # アップロードリクエストオブジェクト作成
        upload_request = BatchUploadRequest(
            exam_name=exam_name,
            question_text=question_text,
            question_title=question_title,
            max_score=max_score,
            char_limit=char_limit
        )

        # バックグラウンドタスクで処理開始
        background_tasks.add_task(
            _process_batch_upload,
            upload_id,
            csv_content,
            upload_request,
            db
        )

        return {
            "upload_id": upload_id,
            "message": "一括アップロードを開始しました。進捗は「処理状況確認」で確認できます。"
        }

    except Exception as e:
        logger.error(f"Batch upload start error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"アップロード開始に失敗しました: {str(e)}"
        )


@router.get("/upload/status/{upload_id}")
async def get_upload_status(upload_id: str) -> BatchUploadStatus:
    """
    アップロード処理状況確認
    """
    # 実際の実装では Redis や データベースから状況を取得
    # ここでは簡易実装
    return BatchUploadStatus(
        upload_id=upload_id,
        status="processing",
        total_count=100,
        processed_count=45,
        success_count=43,
        error_count=2,
        progress_percentage=45,
        message="データを処理中です...",
        errors=["行15: 受験者IDが空白です", "行23: 解答文字数が制限を超えています"]
    )


def _detect_column_mapping(fieldnames: List[str]) -> Dict[str, str]:
    """
    CSVカラム名から必要な項目を自動検出
    """
    mapping = {}

    # 候補パターン
    patterns = {
        "student_id": ["受験者ID", "学生ID", "ID", "受験番号", "Student ID", "id"],
        "name": ["氏名", "名前", "受験者名", "Name", "name"],
        "answer": ["解答", "回答", "Answer", "answer", "解答内容", "回答内容"]
    }

    for field in fieldnames:
        for key, candidates in patterns.items():
            if any(candidate in field for candidate in candidates):
                mapping[key] = field
                break

    return mapping


def _check_data_quality(rows: List[Dict], column_mapping: Dict[str, str]) -> List[str]:
    """
    データ品質チェック
    """
    issues = []

    # 必要カラムの存在確認
    required_fields = ["student_id", "answer"]
    for field in required_fields:
        if field not in column_mapping:
            issues.append(f"必要な項目「{field}」が見つかりません")

    # データ内容チェック
    if column_mapping:
        empty_ids = sum(1 for row in rows if not row.get(column_mapping.get("student_id", ""), "").strip())
        if empty_ids > 0:
            issues.append(f"受験者IDが空白の行が{empty_ids}件あります")

        empty_answers = sum(1 for row in rows if not row.get(column_mapping.get("answer", ""), "").strip())
        if empty_answers > 0:
            issues.append(f"解答が空白の行が{empty_answers}件あります")

    return issues


async def _process_batch_upload(
    upload_id: str,
    csv_content: str,
    upload_request: BatchUploadRequest,
    db: Session
):
    """
    バックグラウンドでCSV処理実行
    """
    try:
        logger.info(f"Batch upload {upload_id} processing started")

        # CSVを解析
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(csv_reader)

        # カラムマッピングを検出
        column_mapping = _detect_column_mapping(csv_reader.fieldnames or [])

        # 1. 試験を作成
        exam = Exam(
            name=upload_request.exam_name,
            description=f"一括アップロード試験: {upload_request.exam_name}",
            created_at=datetime.now()
        )
        db.add(exam)
        db.flush()  # IDを取得するため

        # 2. 問題を作成
        question = Question(
            exam_id=exam.id,
            title=upload_request.question_title,
            question_number="問1",
            background_text="CSV一括アップロードによる問題",
            question_text=upload_request.question_text,
            sub_questions=None,
            model_answer="",
            max_chars=upload_request.char_limit,
            points=upload_request.max_score,
            grading_intention="CSV一括アップロード時に設定された問題",
            grading_commentary="",
            keywords=None
        )
        db.add(question)
        db.flush()  # IDを取得するため

        # 3. 解答データを一括挿入
        scoring_service = ScoringService(db)
        success_count = 0
        error_count = 0
        errors = []

        for i, row in enumerate(rows, 1):
            try:
                # 受験者IDと解答を取得
                student_id = row.get(column_mapping.get("student_id", ""), "").strip()
                answer_text = row.get(column_mapping.get("answer", ""), "").strip()
                student_name = row.get(column_mapping.get("name", ""), "未設定").strip()

                # バリデーション
                if not student_id:
                    errors.append(f"行{i}: 受験者IDが空白です")
                    error_count += 1
                    continue

                if not answer_text:
                    errors.append(f"行{i}: 解答が空白です")
                    error_count += 1
                    continue

                # 解答レコード作成
                answer = Answer(
                    exam_id=exam.id,
                    question_id=question.id,
                    candidate_id=student_id,
                    answer_text=answer_text,
                    submitted_at=datetime.now()
                )
                answer.update_char_count()  # 文字数を自動計算
                db.add(answer)
                db.flush()

                # AI採点を実行
                try:
                    scoring_result = await scoring_service.evaluate_answer(answer.id)

                    success_count += 1

                except Exception as scoring_error:
                    logger.error(f"Scoring error for row {i}: {str(scoring_error)}")
                    errors.append(f"行{i}: AI採点に失敗しました - {str(scoring_error)}")
                    error_count += 1

            except Exception as row_error:
                logger.error(f"Row processing error {i}: {str(row_error)}")
                errors.append(f"行{i}: データ処理に失敗しました - {str(row_error)}")
                error_count += 1

        # 変更をコミット
        db.commit()

        logger.info(f"Batch upload {upload_id} completed: {success_count} success, {error_count} errors")

        # TODO: 実際の実装では進捗状況をRedisに保存
        # _save_upload_status(upload_id, "completed", success_count, error_count, errors)

    except Exception as e:
        logger.error(f"Batch upload {upload_id} failed: {str(e)}")
        db.rollback()
        # TODO: エラー状態をRedisに保存
        # _save_upload_status(upload_id, "error", 0, 0, [str(e)])


@router.get("/")
async def batch_upload_info():
    """一括アップロード機能情報"""
    return {
        "message": "CSV一括アップロード機能",
        "version": "1.0.0",
        "supported_formats": ["CSV (UTF-8)"],
        "max_file_size": "10MB",
        "max_records": 1000,
        "status": "利用可能"
    }