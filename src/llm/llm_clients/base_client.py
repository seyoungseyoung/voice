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
        import re

        original_content = content[:200]  # Save for logging

        # Remove markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}")
            logger.debug(f"Content (first 200 chars): {original_content}")

            # Try to extract fields manually with better regex
            score_match = re.search(r'"score"\s*:\s*(\d+)', content)
            reasoning_match = re.search(r'"reasoning"\s*:\s*"([^"]*)', content)
            is_phishing_match = re.search(r'"is_phishing"\s*:\s*(true|false)', content, re.IGNORECASE)

            score = int(score_match.group(1)) if score_match else 50
            reasoning = reasoning_match.group(1) if reasoning_match else "JSON 파싱 실패"

            logger.info(f"Extracted manually: score={score}, reasoning={reasoning[:50]}")

            return {
                "score": score,
                "reasoning": reasoning,
                "is_phishing": score >= 70,
                "key_points": []
            }
