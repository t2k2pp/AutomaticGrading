"""
LMStudio ローカルLLM統合
"""
import json
import aiohttp
import asyncio
from typing import Dict, Any, Optional
from .base import BaseLLMProvider, LLMProvider, LLMResponse, ScoringCriteria, LLMScoring, DetailedAnalysis, AspectDetail


class LMStudioProvider(BaseLLMProvider):
    """LMStudio ローカルLLMプロバイダー"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:1234")
        self.model = config.get("model", "local-model")
        self.timeout = config.get("timeout", 120)
        self.max_tokens = config.get("max_tokens", 2000)
        self.temperature = config.get("temperature", 0.1)

    def _get_provider_type(self) -> LLMProvider:
        return LLMProvider.LMSTUDIO

    async def generate_response(self, prompt: str, **kwargs) -> LLMResponse:
        """テキスト生成"""
        url = f"{self.base_url}/v1/chat/completions"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "stream": False
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"LMStudio API error: {response.status} - {error_text}")

                    result = await response.json()

                    if "choices" not in result or not result["choices"]:
                        raise Exception("Invalid response from LMStudio")

                    content = result["choices"][0]["message"]["content"]
                    usage = result.get("usage", {})

                    return LLMResponse(
                        content=content,
                        provider=self.provider_type,
                        model=self.model,
                        usage=usage,
                        metadata={"response_time": result.get("response_time")}
                    )

            except aiohttp.ClientError as e:
                raise Exception(f"LMStudio接続エラー: {str(e)}")
            except asyncio.TimeoutError:
                raise Exception(f"LMStudio応答タイムアウト ({self.timeout}秒)")

    async def score_answer(self, criteria: ScoringCriteria) -> LLMScoring:
        """解答採点"""
        prompt = self._build_scoring_prompt(criteria)

        try:
            response = await self.generate_response(
                prompt,
                temperature=0.1,  # 採点時は低温度で一貫性を確保
                max_tokens=1500
            )

            # JSONレスポンスを解析
            content = response.content.strip()

            # JSONブロックを抽出（```json```で囲まれている場合の対応）
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                if json_end != -1:
                    content = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                if json_end != -1:
                    content = content[json_start:json_end].strip()

            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # JSONパースに失敗した場合のフォールバック
                # レスポンスから数値を抽出して基本的な採点を行う
                import re

                score_match = re.search(r'"?total_score"?\s*:\s*(\d+(?:\.\d+)?)', content)
                total_score = float(score_match.group(1)) if score_match else 15.0

                confidence_match = re.search(r'"?confidence"?\s*:\s*(\d+(?:\.\d+)?)', content)
                confidence = float(confidence_match.group(1)) if confidence_match else 0.7

                result = {
                    "total_score": min(total_score, criteria.max_score),
                    "aspect_scores": {aspect: total_score / 5 for aspect in criteria.scoring_aspects},
                    "detailed_feedback": content,
                    "confidence": min(confidence, 1.0),
                    "reasoning": "LLMからの構造化されていない応答"
                }

            # 詳細分析情報を構造化
            detailed_analysis = None
            if "detailed_analysis" in result:
                analysis_data = result["detailed_analysis"]
                detailed_analysis = DetailedAnalysis(
                    strengths=analysis_data.get("strengths", []),
                    weaknesses=analysis_data.get("weaknesses", []),
                    missing_elements=analysis_data.get("missing_elements", []),
                    specific_issues=analysis_data.get("specific_issues", [])
                )

            # 観点別詳細評価を構造化
            aspect_reasoning = None
            if "aspect_reasoning" in result:
                aspect_reasoning = {}
                for aspect, details in result["aspect_reasoning"].items():
                    aspect_reasoning[aspect] = AspectDetail(
                        score=float(details.get("score", 0)),
                        reasoning=details.get("reasoning", ""),
                        evidence=details.get("evidence", ""),
                        deduction_points=details.get("deduction_points")
                    )

            return LLMScoring(
                total_score=min(float(result.get("total_score", 0)), criteria.max_score),
                aspect_scores=result.get("aspect_scores", {}),
                detailed_feedback=result.get("detailed_feedback", ""),
                confidence=min(float(result.get("confidence", 0.5)), 1.0),
                reasoning=result.get("reasoning", ""),

                # 新しい詳細項目
                detailed_analysis=detailed_analysis,
                aspect_reasoning=aspect_reasoning,
                improvement_suggestions=result.get("improvement_suggestions", []),
                confidence_reasoning=result.get("confidence_reasoning"),
                overall_reasoning=result.get("overall_reasoning"),
                attention_points=result.get("attention_points", [])
            )

        except Exception as e:
            raise Exception(f"採点処理エラー: {str(e)}")

    async def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            url = f"{self.base_url}/v1/models"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200

        except Exception:
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """モデル情報を取得"""
        return {
            "provider": self.provider_type.value,
            "model": self.model,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }