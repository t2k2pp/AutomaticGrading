"""
アプリケーション設定
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # データベース設定
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://scoring_user:scoring_pass@localhost:5432/pm_scoring"
    )

    # Redis設定
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # API設定
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # AI Engine設定
    AI_ENGINE_URL: str = os.getenv("AI_ENGINE_URL", "http://localhost:8001")
    AI_MODEL: str = os.getenv("AI_MODEL", "gpt-4")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.1"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "1000"))

    # Celery設定
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    # アプリケーション設定
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")

    # セキュリティ設定
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    ALGORITHM: str = "HS256"

    # 採点システム設定
    MAX_SCORING_WORKERS: int = int(os.getenv("MAX_SCORING_WORKERS", "4"))
    SCORING_TIMEOUT: int = int(os.getenv("SCORING_TIMEOUT", "300"))  # 5分

    class Config:
        env_file = ".env"
        case_sensitive = True


# グローバル設定インスタンス
settings = Settings()