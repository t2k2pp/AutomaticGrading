"""
データベース設定とセッション管理
"""
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

from .config import settings

logger = logging.getLogger(__name__)

# SQLAlchemyエンジン作成
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.ENVIRONMENT == "development"
)

# セッションメーカー
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ベースクラス
Base = declarative_base()

# メタデータ
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    """データベースセッションの依存性注入"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


async def init_db():
    """データベース初期化"""
    try:
        # テーブル作成
        Base.metadata.create_all(bind=engine)
        logger.info("データベーステーブルが正常に作成されました")
    except Exception as e:
        logger.error(f"データベース初期化エラー: {e}")
        raise


async def close_db():
    """データベース接続クローズ"""
    engine.dispose()
    logger.info("データベース接続を閉じました")