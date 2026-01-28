"""
OpenAI GPT API Client
"""
import os
import logging
from typing import Dict, Optional
import requests

from .base_client import BaseLLMClient

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """OpenAI GPT API client"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("OPENAI_API_KEY"))
        self.model_name = "GPT-4o"
        self.api_url = "https://api.openai.com/v1/chat/completions"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def analyze_phishing(self, text: str, prompt: str) -> Dict:
        """Analyze using OpenAI GPT API"""
        if not self.is_available():
            return self._error_response("API key not configured")

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "gpt-4o",
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
                "temperature": 0.2,
                "max_tokens": 800
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
            content = result["choices"][0]["message"]["content"]
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
