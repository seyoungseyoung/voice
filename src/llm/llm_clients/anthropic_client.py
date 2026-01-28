"""
Anthropic Claude API Client
"""
import os
import logging
from typing import Dict, Optional
import requests

from .base_client import BaseLLMClient

logger = logging.getLogger(__name__)


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API client"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("ANTHROPIC_API_KEY"))
        self.model_name = "Claude 3.5 Haiku"
        self.api_url = "https://api.anthropic.com/v1/messages"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def analyze_phishing(self, text: str, prompt: str) -> Dict:
        """Analyze using Claude API"""
        if not self.is_available():
            return self._error_response("API key not configured")

        try:
            full_prompt = f"{prompt}\n\n**통화 내용:**\n\"{text}\""

            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }

            payload = {
                "model": "claude-3-5-haiku-20241022",
                "max_tokens": 800,
                "temperature": 0.2,
                "messages": [
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ]
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            # Extract content from Claude response
            content = result["content"][0]["text"]
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
