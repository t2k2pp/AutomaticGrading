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
        "sqlite:///./pm_scoring.db"
    )

    # Redis設定
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # API設定
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
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

    # 管理API認証設定
    ADMIN_API_KEY: str = os.getenv("ADMIN_API_KEY", "")

    # 採点システム設定
    MAX_SCORING_WORKERS: int = int(os.getenv("MAX_SCORING_WORKERS", "4"))
    SCORING_TIMEOUT: int = int(os.getenv("SCORING_TIMEOUT", "300"))  # 5分

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }

    def model_post_init(self, __context):
        """設定値のバリデーション"""
        # 開発環境以外ではセキュリティキーの設定を必須とする
        if self.ENVIRONMENT != "development":
            if not self.SECRET_KEY or self.SECRET_KEY == "":
                raise ValueError("本番環境ではSECRET_KEYの設定が必要です。環境変数を設定してください。")
            if not self.ADMIN_API_KEY or self.ADMIN_API_KEY == "":
                raise ValueError("本番環境ではADMIN_API_KEYの設定が必要です。環境変数を設定してください。")

        # 開発環境でも空の場合は警告とデフォルト値設定
        if not self.SECRET_KEY:
            print("⚠️  WARNING: SECRET_KEYが設定されていません。開発用のデフォルト値を使用します。")
            object.__setattr__(self, 'SECRET_KEY', "dev-secret-key-for-development-only")

        if not self.ADMIN_API_KEY:
            print("⚠️  WARNING: ADMIN_API_KEYが設定されていません。開発用のデフォルト値を使用します。")
            object.__setattr__(self, 'ADMIN_API_KEY', "dev-admin-key-for-development-only")


# グローバル設定インスタンス
settings = Settings()