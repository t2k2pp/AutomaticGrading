"""
採点関連モデル
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, Float, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from ..database import Base


class ScoringStatus(enum.Enum):
    PENDING = "pending"          # 採点待ち
    IN_PROGRESS = "in_progress"  # 採点中
    COMPLETED = "completed"      # 採点完了
    FAILED = "failed"           # 採点失敗
    REVIEWED = "reviewed"       # 人間レビュー済み


class ScoringMethod(enum.Enum):
    RULE_BASED = "rule_based"        # ルールベース採点
    SEMANTIC = "semantic"            # 意味理解採点
    COMPREHENSIVE = "comprehensive"   # 総合評価採点
    HUMAN = "human"                  # 人間採点


class ScoringResult(Base):
    """採点結果テーブル"""
    __tablename__ = "scoring_results"

    id = Column(Integer, primary_key=True, index=True)
    answer_id = Column(Integer, ForeignKey("answers.id"), nullable=False, index=True)

    # 採点情報
    status = Column(SQLEnum(ScoringStatus), default=ScoringStatus.PENDING, nullable=False, index=True)
    scoring_method = Column(SQLEnum(ScoringMethod), nullable=False)

    # スコア情報
    total_score = Column(Float)  # 総合スコア
    max_score = Column(Float)    # 最大スコア
    percentage = Column(Float)   # パーセンテージ
    confidence = Column(Float)   # 信頼度 (0.0-1.0)

    # 詳細スコア
    rule_based_score = Column(Float)     # ルールベーススコア
    semantic_score = Column(Float)       # 意味理解スコア
    comprehensive_score = Column(Float)  # 総合評価スコア

    # 採点詳細
    scoring_details = Column(JSON)  # 詳細な採点結果
    scoring_reasons = Column(JSON)  # 採点理由
    suggestions = Column(JSON)      # 改善提案

    # AI関連情報
    model_name = Column(String(100))
    temperature = Column(Float)
    tokens_used = Column(Integer)
    processing_time_ms = Column(Integer)

    # レビュー情報
    is_reviewed = Column(Boolean, default=False)
    reviewer_id = Column(String(100))
    review_comments = Column(Text)
    human_score = Column(Float)  # 人間による最終スコア
    score_adjustment = Column(Float)  # スコア調整値

    # タイムスタンプ
    scoring_started_at = Column(DateTime(timezone=True))
    scoring_completed_at = Column(DateTime(timezone=True))
    reviewed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # リレーション
    answer = relationship("Answer", back_populates="scoring_results")
    audit_logs = relationship("ScoringAuditLog", back_populates="scoring_result")

    def __repr__(self):
        return f"<ScoringResult(answer_id={self.answer_id}, score={self.total_score})>"

    @property
    def final_score(self):
        """最終スコア取得（人間レビュー後があればそれを、なければAIスコアを返す）"""
        return self.human_score if self.human_score is not None else self.total_score

    @property
    def grade(self):
        """成績グレード算出"""
        if not self.percentage:
            return "N/A"

        if self.percentage >= 90:
            return "A"
        elif self.percentage >= 80:
            return "B"
        elif self.percentage >= 70:
            return "C"
        elif self.percentage >= 60:
            return "D"
        else:
            return "F"


class ScoringAuditLog(Base):
    """採点監査ログテーブル"""
    __tablename__ = "scoring_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    scoring_result_id = Column(Integer, ForeignKey("scoring_results.id"), nullable=False, index=True)

    action = Column(String(50), nullable=False)  # "created", "updated", "reviewed"
    user_id = Column(String(100))
    user_type = Column(String(20))  # "ai", "human", "system"

    old_values = Column(JSON)  # 変更前の値
    new_values = Column(JSON)  # 変更後の値
    reason = Column(Text)      # 変更理由

    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45))
    user_agent = Column(Text)

    # リレーション
    scoring_result = relationship("ScoringResult", back_populates="audit_logs")

    def __repr__(self):
        return f"<ScoringAuditLog(action={self.action}, timestamp={self.timestamp})>"