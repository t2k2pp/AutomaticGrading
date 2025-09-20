"""
解答関連モデル
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..database import Base


class Answer(Base):
    """解答テーブル"""
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    candidate_id = Column(String(50), nullable=False, index=True)  # 受験者ID（匿名化済み）
    answer_text = Column(Text, nullable=False)
    char_count = Column(Integer)
    is_blank = Column(Boolean, default=False)

    # 提出情報
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45))  # IPv6対応
    user_agent = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # リレーション
    exam = relationship("Exam", back_populates="answers")
    question = relationship("Question", back_populates="answers")
    scoring_results = relationship("ScoringResult", back_populates="answer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Answer(candidate={self.candidate_id}, question={self.question_id})>"

    @property
    def is_valid_length(self):
        """文字数制限内かチェック"""
        if not self.question:
            return True
        return self.char_count <= self.question.max_chars

    def update_char_count(self):
        """文字数を更新"""
        self.char_count = len(self.answer_text) if self.answer_text else 0
        self.is_blank = not bool(self.answer_text.strip()) if self.answer_text else True