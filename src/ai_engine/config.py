"""
AI Engine設定
"""
import os
from typing import Optional


class Settings:
    # 環境設定
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # LLM設定
    LMSTUDIO_URL: str = os.getenv("LMSTUDIO_URL", "http://localhost:1234")
    LMSTUDIO_MODEL: str = os.getenv("LMSTUDIO_MODEL", "local-model")

    # 他のLLMプロバイダー設定
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    AZURE_OPENAI_ENDPOINT: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_KEY: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY")

    # AI設定
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.1"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2000"))
    MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "4"))

    # キャッシュ設定
    CACHE_DIR: str = os.getenv("CACHE_DIR", "/app/cache")
    MODEL_CACHE_SIZE: int = int(os.getenv("MODEL_CACHE_SIZE", "1000"))

    # パフォーマンス設定
    SCORING_TIMEOUT: int = int(os.getenv("SCORING_TIMEOUT", "30"))
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "10"))


# グローバル設定インスタンス
settings = Settings()