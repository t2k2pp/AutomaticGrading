"""
問題関連モデル
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import DateTime

from ..database import Base


class Question(Base):
    """問題テーブル - IPAのPM試験構造対応"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False, index=True)

    # 基本情報
    title = Column(String(200), nullable=False)  # 問題タイトル（例：リスク管理）
    question_number = Column(String(20), nullable=False)  # "問1", "設問1"など

    # IPAのPM試験構造対応
    background_text = Column(Text, nullable=False, comment="背景情報（プロジェクト概要・状況設定等）")
    question_text = Column(Text, nullable=False, comment="実際の設問内容")
    sub_questions = Column(JSON, nullable=True, comment="複数設問の場合の設問リスト")

    # 従来のフィールドも保持（下位互換性）
    problem_statement = Column(Text)  # 廃止予定（background_textに移行）

    # 採点関連
    max_chars = Column(Integer, default=400)  # 最大文字数
    points = Column(Integer, default=25)  # 配点

    # 採点基準
    model_answer = Column(Text, nullable=False, comment="模範解答")
    grading_intention = Column(Text, comment="出題趣旨")
    grading_commentary = Column(Text, comment="採点講評")
    keywords = Column(JSON, comment="重要キーワードリスト")
    grading_criteria = Column(JSON, comment="採点基準詳細")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # リレーション
    exam = relationship("Exam", back_populates="questions")
    answers = relationship("Answer", back_populates="question")

    def __repr__(self):
        return f"<Question({self.question_number})>"

    @property
    def keyword_list(self):
        """キーワードをリストで取得"""
        return self.keywords or []

    @property
    def criteria_dict(self):
        """採点基準を辞書で取得"""
        return self.grading_criteria or {}

    @property
    def full_question_text(self):
        """背景情報と設問を結合した完全な問題文（AI採点用）"""
        background = self.background_text or ""
        question = self.question_text or ""

        full_text = ""
        if background:
            full_text += f"【背景情報・プロジェクト概要】\n{background}\n\n"

        full_text += f"【設問】\n{question}"

        if self.has_sub_questions:
            full_text += "\n\n【詳細設問】\n"
            for i, sub_q in enumerate(self.sub_questions, 1):
                full_text += f"{i}. {sub_q}\n"

        return full_text

    @property
    def has_sub_questions(self):
        """複数設問があるかどうか"""
        return self.sub_questions is not None and len(self.sub_questions) > 0

    @property
    def display_name(self):
        """表示用の問題名"""
        return f"{self.question_number}: {self.title}"