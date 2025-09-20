"""
問題関連モデル
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import DateTime

from ..database import Base


class Question(Base):
    """問題テーブル"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False, index=True)
    question_number = Column(String(20), nullable=False)  # "問1", "設問1"など
    question_text = Column(Text, nullable=False)
    problem_statement = Column(Text)  # プロジェクト概要など
    max_chars = Column(Integer, default=40)  # 最大文字数
    points = Column(Integer, default=25)  # 配点

    # 採点基準
    model_answer = Column(Text, nullable=False)
    grading_intention = Column(Text)  # 出題趣旨
    grading_commentary = Column(Text)  # 採点講評
    keywords = Column(JSON)  # キーワードリスト
    grading_criteria = Column(JSON)  # 採点基準詳細

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