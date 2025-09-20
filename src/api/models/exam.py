"""
試験関連モデル
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from ..database import Base


class ExamSeason(enum.Enum):
    SPRING = "spring"
    AUTUMN = "autumn"


class Exam(Base):
    """試験テーブル"""
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, index=True)
    season = Column(SQLEnum(ExamSeason), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # リレーション
    questions = relationship("Question", back_populates="exam", cascade="all, delete-orphan")
    answers = relationship("Answer", back_populates="exam")

    def __repr__(self):
        return f"<Exam({self.year}-{self.season.value})>"

    @property
    def display_name(self):
        season_jp = "春期" if self.season == ExamSeason.SPRING else "秋期"
        return f"{self.year}年{season_jp}PM試験"