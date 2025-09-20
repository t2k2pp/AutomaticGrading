"""
LLMプロバイダーマネージャー
"""
import asyncio
from typing import Dict, Any, Optional, List
from .base import LLMProvider, BaseLLMProvider, LLMFactory, ScoringCriteria, LLMScoring
from .lmstudio import LMStudioProvider


class LLMManager:
    """LLMプロバイダーを管理するクラス"""

    def __init__(self):
        self._providers: Dict[LLMProvider, BaseLLMProvider] = {}
        self._default_provider: Optional[LLMProvider] = None
        self._register_providers()

    def _register_providers(self):
        """プロバイダーをファクトリーに登録"""
        # LMStudioプロバイダーを登録
        LLMFactory.register(LLMProvider.LMSTUDIO, LMStudioProvider)

        # 他のプロバイダーも事前に登録（実装時に追加）
        # LLMFactory.register(LLMProvider.OLLAMA, OllamaProvider)
        # LLMFactory.register(LLMProvider.GEMINI, GeminiProvider)
        # LLMFactory.register(LLMProvider.AZURE_OPENAI, AzureOpenAIProvider)

    async def initialize_provider(self, provider_type: LLMProvider, config: Dict[str, Any]) -> bool:
        """プロバイダーを初期化"""
        try:
            provider = LLMFactory.create(provider_type, config)

            # ヘルスチェック
            if not await provider.health_check():
                return False

            self._providers[provider_type] = provider

            # 最初に初期化されたプロバイダーをデフォルトに設定
            if self._default_provider is None:
                self._default_provider = provider_type

            return True

        except Exception as e:
            print(f"プロバイダー初期化エラー ({provider_type}): {str(e)}")
            return False

    def set_default_provider(self, provider_type: LLMProvider):
        """デフォルトプロバイダーを設定"""
        if provider_type in self._providers:
            self._default_provider = provider_type
        else:
            raise ValueError(f"プロバイダーが初期化されていません: {provider_type}")

    def get_provider(self, provider_type: Optional[LLMProvider] = None) -> BaseLLMProvider:
        """プロバイダーを取得"""
        target_provider = provider_type or self._default_provider

        if target_provider is None:
            raise ValueError("利用可能なプロバイダーがありません")

        if target_provider not in self._providers:
            raise ValueError(f"プロバイダーが初期化されていません: {target_provider}")

        return self._providers[target_provider]

    def get_available_providers(self) -> List[LLMProvider]:
        """利用可能なプロバイダー一覧を取得"""
        return list(self._providers.keys())

    async def score_answer(
        self,
        criteria: ScoringCriteria,
        provider_type: Optional[LLMProvider] = None
    ) -> LLMScoring:
        """解答を採点"""
        provider = self.get_provider(provider_type)
        return await provider.score_answer(criteria)

    async def health_check_all(self) -> Dict[LLMProvider, bool]:
        """すべてのプロバイダーのヘルスチェック"""
        results = {}

        for provider_type, provider in self._providers.items():
            try:
                results[provider_type] = await provider.health_check()
            except Exception:
                results[provider_type] = False

        return results

    def get_provider_info(self, provider_type: Optional[LLMProvider] = None) -> Dict[str, Any]:
        """プロバイダー情報を取得"""
        provider = self.get_provider(provider_type)

        info = {
            "provider": provider.provider_type.value,
            "default": provider.provider_type == self._default_provider,
            "available_providers": [p.value for p in self.get_available_providers()]
        }

        # プロバイダー固有の情報を追加
        if hasattr(provider, 'get_model_info'):
            info.update(provider.get_model_info())

        return info


# グローバルマネージャーインスタンス
llm_manager = LLMManager()