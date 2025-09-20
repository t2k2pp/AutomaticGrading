"""
初期データ投入ユーティリティ
"""
import logging
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..models.exam import Exam, ExamSeason
from ..models.question import Question
from ..models.answer import Answer

logger = logging.getLogger(__name__)


def create_initial_data(db: Session) -> Dict[str, Any]:
    """初期データを作成"""
    try:
        # 既存データチェック
        existing_exam = db.query(Exam).first()
        if existing_exam:
            logger.info("初期データは既に存在します")
            return {"status": "skipped", "message": "初期データは既に存在します"}

        # 試験データ作成
        exam_2024_autumn = Exam(
            year=2024,
            season=ExamSeason.AUTUMN,
            title="2024年秋期プロジェクトマネージャ試験",
            description="午後Ⅰ記述式問題",
            is_active=True
        )
        db.add(exam_2024_autumn)
        db.flush()  # IDを取得

        exam_2024_spring = Exam(
            year=2024,
            season=ExamSeason.SPRING,
            title="2024年春期プロジェクトマネージャ試験",
            description="午後Ⅰ記述式問題",
            is_active=False
        )
        db.add(exam_2024_spring)
        db.flush()

        # 問題データ作成
        question_1_1 = Question(
            exam_id=exam_2024_autumn.id,
            question_number="問1 設問1",
            question_text="プロジェクトでリスクが顕在化した理由を40字以内で述べよ。",
            problem_statement="あなたは、製造業A社のシステム部門に所属するプロジェクトマネージャである。新商品の受注管理システムの開発プロジェクトを担当している。",
            max_chars=40,
            points=25,
            model_answer="要員のスキル不足により、設計段階での品質問題が見過ごされ、後工程で大規模な手戻りが発生したため。",
            grading_intention="リスク管理の理解度と、具体的な原因分析能力を評価する。",
            keywords=["スキル不足", "品質問題", "手戻り", "要員", "設計段階"],
            grading_criteria={
                "keyword_matching": 0.3,
                "logical_consistency": 0.3,
                "practical_validity": 0.2,
                "completeness": 0.2
            }
        )
        db.add(question_1_1)
        db.flush()

        question_1_2 = Question(
            exam_id=exam_2024_autumn.id,
            question_number="問1 設問2",
            question_text="このリスクを回避するために事前に実施すべきだった対策を30字以内で述べよ。",
            problem_statement="",
            max_chars=30,
            points=20,
            model_answer="プロジェクト開始前に要員のスキルレベルを評価し、必要に応じて研修を実施する。",
            grading_intention="リスク予防策の立案能力を評価する。",
            keywords=["スキル評価", "研修", "要員", "事前対策"],
            grading_criteria={
                "preventive_thinking": 0.4,
                "feasibility": 0.3,
                "completeness": 0.3
            }
        )
        db.add(question_1_2)
        db.flush()

        # サンプル解答データ作成
        answer_1 = Answer(
            exam_id=exam_2024_autumn.id,
            question_id=question_1_1.id,
            candidate_id="TEST001",
            answer_text="メンバーの技術力が不足していたため、初期段階でのレビューが不十分となり、後に修正が必要となった。",
            char_count=38,
            is_blank=False
        )
        db.add(answer_1)

        answer_2 = Answer(
            exam_id=exam_2024_autumn.id,
            question_id=question_1_1.id,
            candidate_id="TEST002",
            answer_text="プロジェクト開始時のリスク評価が甘く、必要なスキルを持つ要員の確保が遅れたため。",
            char_count=35,
            is_blank=False
        )
        db.add(answer_2)

        answer_3 = Answer(
            exam_id=exam_2024_autumn.id,
            question_id=question_1_2.id,
            candidate_id="TEST001",
            answer_text="メンバーのスキル診断を実施し、不足分野の研修を計画する。",
            char_count=26,
            is_blank=False
        )
        db.add(answer_3)

        # コミット
        db.commit()

        logger.info("初期データの作成が完了しました")
        return {
            "status": "success",
            "message": "初期データの作成が完了しました",
            "created": {
                "exams": 2,
                "questions": 2,
                "answers": 3
            }
        }

    except Exception as e:
        db.rollback()
        logger.error(f"初期データ作成エラー: {e}")
        return {
            "status": "error",
            "message": f"初期データ作成エラー: {str(e)}"
        }