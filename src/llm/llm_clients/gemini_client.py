"""
Google Gemini API Client
"""
import os
import logging
from typing import Dict, Optional
import requests

from .base_client import BaseLLMClient

logger = logging.getLogger(__name__)


class GeminiClient(BaseLLMClient):
    """Google Gemini API client"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("GEMINI_API_KEY"))
        self.model_name = "Gemini 2.5 Flash"
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def analyze_phishing(self, text: str, prompt: str) -> Dict:
        """Analyze using Gemini API"""
        if not self.is_available():
            return self._error_response("API key not configured")

        try:
            full_prompt = f"{prompt}\n\n**통화 내용:**\n\"{text}\""

            headers = {
                "Content-Type": "application/json"
            }

            payload = {
                "contents": [{
                    "parts": [{
                        "text": full_prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 800
                }
            }

            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                headers=headers,
                json=payload,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            # Extract content
            content = result["candidates"][0]["content"]["parts"][0]["text"]
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
