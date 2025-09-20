"""
採点結果エクスポート API
2次採点者が確認済みの結果をCSV/Excel形式で出力
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Literal
from datetime import datetime
import csv
import io
import json

from ..database import get_db
from ..models.answer import Answer
from ..models.exam import Exam
from ..models.question import Question

router = APIRouter()


@router.get("/scoring-results/{exam_id}")
async def export_scoring_results(
    exam_id: int,
    format: Literal["csv", "excel"] = Query(default="csv", description="出力形式"),
    reviewed_only: bool = Query(default=False, description="レビュー済みのみ"),
    db: Session = Depends(get_db)
):
    """
    採点結果を一括エクスポート
    """
    try:
        # 試験情報を取得
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            raise HTTPException(status_code=404, detail="試験が見つかりません")

        # 解答データと採点結果を取得
        query = db.query(Answer).join(Question).filter(Question.exam_id == exam_id)

        if reviewed_only:
            query = query.filter(Answer.is_reviewed == True)

        answers = query.all()

        if not answers:
            raise HTTPException(status_code=404, detail="エクスポート対象のデータがありません")

        if format == "csv":
            return await _export_csv(exam, answers)
        elif format == "excel":
            return await _export_excel(exam, answers)
        else:
            raise HTTPException(status_code=400, detail="サポートされていない形式です")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"エクスポートに失敗しました: {str(e)}")


async def _export_csv(exam: Exam, answers: List[Answer]) -> StreamingResponse:
    """CSV形式でエクスポート"""

    output = io.StringIO()
    writer = csv.writer(output)

    # ヘッダー行
    headers = [
        "試験名",
        "問題タイトル",
        "受験者ID",
        "受験者名",
        "解答内容",
        "AI採点スコア",
        "最終スコア",
        "成績",
        "信頼度",
        "レビュー状況",
        "2次採点者コメント",
        "提出日時",
        "採点日時",
        "AI詳細分析",
        "強み",
        "弱み",
        "不足要素",
        "改善提案"
    ]
    writer.writerow(headers)

    # データ行
    for answer in answers:
        # AI分析データを解析
        ai_feedback = answer.ai_feedback or {}
        detailed_analysis = ai_feedback.get("detailed_analysis", {})

        row = [
            exam.name,
            answer.question.title if answer.question else "",
            answer.student_id,
            answer.student_name,
            _truncate_text(answer.answer_text, 500),  # 長すぎる場合は切り詰め
            answer.score,
            answer.final_score or answer.score,
            _calculate_grade(answer.final_score or answer.score, answer.question.max_score if answer.question else 25),
            f"{(answer.confidence * 100):.1f}%" if answer.confidence else "",
            "レビュー済み" if answer.is_reviewed else "未レビュー",
            answer.reviewer_notes or "",
            answer.submitted_at.strftime("%Y-%m-%d %H:%M:%S") if answer.submitted_at else "",
            answer.scored_at.strftime("%Y-%m-%d %H:%M:%S") if answer.scored_at else "",
            detailed_analysis.get("confidence_reasoning", ""),
            "; ".join(detailed_analysis.get("strengths", [])),
            "; ".join(detailed_analysis.get("weaknesses", [])),
            "; ".join(detailed_analysis.get("missing_elements", [])),
            "; ".join(ai_feedback.get("improvement_suggestions", []))
        ]
        writer.writerow(row)

    output.seek(0)

    # ファイル名を生成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"採点結果_{exam.name}_{timestamp}.csv"

    # レスポンスヘッダー設定
    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"',
        'Content-Type': 'text/csv; charset=utf-8-sig'  # BOM付きUTF-8でExcel対応
    }

    # BOMを追加してExcelで文字化けを防ぐ
    content = "\ufeff" + output.getvalue()

    return StreamingResponse(
        io.StringIO(content),
        media_type="text/csv",
        headers=headers
    )


async def _export_excel(exam: Exam, answers: List[Answer]) -> StreamingResponse:
    """Excel形式でエクスポート（今後実装予定）"""
    raise HTTPException(status_code=501, detail="Excel形式は今後実装予定です")


def _truncate_text(text: str, max_length: int) -> str:
    """テキストを指定文字数で切り詰め"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def _calculate_grade(score: float, max_score: float) -> str:
    """スコアから成績を計算"""
    if not score or not max_score:
        return "N/A"

    percentage = (score / max_score) * 100

    if percentage >= 90:
        return "A"
    elif percentage >= 80:
        return "B"
    elif percentage >= 70:
        return "C"
    elif percentage >= 60:
        return "D"
    else:
        return "F"


@router.get("/summary/{exam_id}")
async def export_summary_report(
    exam_id: int,
    db: Session = Depends(get_db)
):
    """
    採点結果サマリーレポートを生成
    """
    try:
        # 試験情報を取得
        exam = db.query(Exam).filter(Exam.id == exam_id).first()
        if not exam:
            raise HTTPException(status_code=404, detail="試験が見つかりません")

        # 統計情報を計算
        answers = db.query(Answer).join(Question).filter(Question.exam_id == exam_id).all()

        total_count = len(answers)
        reviewed_count = sum(1 for answer in answers if answer.is_reviewed)

        scores = [answer.final_score or answer.score for answer in answers if answer.score is not None]

        if scores:
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
        else:
            avg_score = max_score = min_score = 0

        # 成績分布
        grade_distribution = {}
        for answer in answers:
            if answer.score is not None:
                grade = _calculate_grade(
                    answer.final_score or answer.score,
                    answer.question.max_score if answer.question else 25
                )
                grade_distribution[grade] = grade_distribution.get(grade, 0) + 1

        summary = {
            "exam_name": exam.name,
            "export_date": datetime.now().isoformat(),
            "statistics": {
                "total_submissions": total_count,
                "reviewed_submissions": reviewed_count,
                "review_rate": f"{(reviewed_count/total_count*100):.1f}%" if total_count > 0 else "0%",
                "average_score": f"{avg_score:.1f}",
                "highest_score": f"{max_score:.1f}",
                "lowest_score": f"{min_score:.1f}"
            },
            "grade_distribution": grade_distribution,
            "ai_scoring_reliability": {
                "high_confidence_rate": f"{sum(1 for a in answers if a.confidence and a.confidence >= 0.8)/len(answers)*100:.1f}%" if answers else "0%",
                "modification_rate": f"{sum(1 for a in answers if a.is_reviewed and a.final_score != a.score)/reviewed_count*100:.1f}%" if reviewed_count > 0 else "0%"
            }
        }

        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"サマリー生成に失敗しました: {str(e)}")


@router.get("/")
async def export_info():
    """エクスポート機能情報"""
    return {
        "message": "採点結果エクスポート機能",
        "version": "1.0.0",
        "supported_formats": ["CSV", "Excel (今後実装)"],
        "features": [
            "全採点結果の一括エクスポート",
            "レビュー済みのみフィルタリング",
            "詳細なAI分析データ出力",
            "統計サマリーレポート生成"
        ],
        "status": "利用可能"
    }