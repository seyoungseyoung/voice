"""
Base LLM Client interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    """Base class for all LLM clients"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.model_name = "unknown"

    @abstractmethod
    def is_available(self) -> bool:
        """Check if API key is configured"""
        pass

    @abstractmethod
    def analyze_phishing(self, text: str, prompt: str) -> Dict:
        """
        Analyze phishing with given prompt

        Args:
            text: Conversation text to analyze
            prompt: Analysis prompt

        Returns:
            {
                "score": int (0-100),
                "reasoning": str,
                "key_points": list,
                "model": str
            }
        """
        pass

    def _parse_json_response(self, content: str) -> Dict:
        """Common JSON parsing logic"""
        import json

        # Remove markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            # Try to extract score manually
            import re
            score_match = re.search(r'"score"\s*:\s*(\d+)', content)
            if score_match:
                return {
                    "score": int(score_match.group(1)),
                    "reasoning": "JSON parsing failed, extracted score only",
                    "key_points": []
                }
            return {
                "score": 50,
                "reasoning": f"Parsing failed: {str(e)}",
                "key_points": []
            }
