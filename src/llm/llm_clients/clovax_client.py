"""
ClovaX API Client (wrapper for multi-agent system)
"""
import os
import logging
from typing import Dict, Optional
import requests

from .base_client import BaseLLMClient

logger = logging.getLogger(__name__)


class ClovaXClient(BaseLLMClient):
    """ClovaX API client"""

    def __init__(self, api_key: Optional[str] = None, gateway_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("CLOVAX_API_KEY"))
        self.gateway_key = gateway_key or os.getenv("CLOVAX_GATEWAY_KEY")
        self.model_name = "ClovaX (HyperCLOVA X)"
        self.api_url = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"

    def is_available(self) -> bool:
        return bool(self.api_key and self.gateway_key)

    def analyze_phishing(self, text: str, prompt: str) -> Dict:
        """Analyze using ClovaX API"""
        if not self.is_available():
            return self._error_response("API key not configured")

        try:
            headers = {
                "X-NCP-CLOVASTUDIO-API-KEY": self.api_key,
                "X-NCP-APIGW-API-KEY": self.gateway_key,
                "X-NCP-CLOVASTUDIO-REQUEST-ID": "sentinel-voice-ensemble",
                "Content-Type": "application/json"
            }

            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": "당신은 보이스피싱 탐지 전문가입니다. 정확한 JSON 형식으로만 응답하세요."
                    },
                    {
                        "role": "user",
                        "content": f"{prompt}\n\n**통화 내용:**\n\"{text}\""
                    }
                ],
                "topP": 0.8,
                "topK": 0,
                "maxTokens": 800,
                "temperature": 0.2,
                "repeatPenalty": 5.0,
                "stopBefore": [],
                "includeAiFilters": True
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            # Extract content
            content = result["result"]["message"]["content"]
            parsed = self._parse_json_response(content)
            parsed["model"] = self.model_name

            logger.info(f"✓ {self.model_name} analysis: {parsed.get('score', 0)}/100")
            return parsed

        except Exception as e:
            logger.error(f"{self.model_name} error: {e}")
            return self._error_response(str(e))

    def _error_response(self, error: str) -> Dict:
        return {
            "score": 50,
            "reasoning": f"Error: {error}",
            "key_points": [],
            "model": self.model_name
        }
