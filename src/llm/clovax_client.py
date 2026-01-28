"""
ClovaX API Client for LLM-based phishing detection
네이버 클라우드 ClovaX API를 사용한 맥락 기반 피싱 탐지
"""
import os
import json
import requests
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClovaXClient:
    """
    ClovaX API client for phishing detection

    Uses HyperCLOVA X for contextual analysis of conversation text
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_gateway_key: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        """
        Args:
            api_key: ClovaX API key (or set CLOVAX_API_KEY env var)
            api_gateway_key: API Gateway key (or set CLOVAX_GATEWAY_KEY env var)
            request_id: Request ID for tracking (optional)
        """
        self.api_key = api_key or os.getenv("CLOVAX_API_KEY")
        self.api_gateway_key = api_gateway_key or os.getenv("CLOVAX_GATEWAY_KEY")
        self.request_id = request_id or "sentinel-voice-001"

        # ClovaX API endpoint
        self.api_url = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"

        if not self.api_key:
            logger.warning("ClovaX API key not configured. LLM features will be disabled.")
        else:
            logger.info("ClovaX client initialized")

    def is_available(self) -> bool:
        """Check if ClovaX API is configured"""
        return bool(self.api_key and self.api_gateway_key)

    def analyze_phishing(
        self,
        conversation_text: str,
        similar_cases: Optional[List[Tuple[str, float, Dict]]] = None
    ) -> Dict:
        """
        Analyze conversation for phishing using ClovaX LLM

        Args:
            conversation_text: The conversation transcript
            similar_cases: Similar phishing cases from Vector DB

        Returns:
            Analysis result with risk score and explanation
        """
        if not self.is_available():
            logger.warning("ClovaX API not available, using fallback")
            return self._fallback_analysis(conversation_text, similar_cases)

        try:
            # Build prompt with context
            prompt = self._build_prompt(conversation_text, similar_cases)

            # Call ClovaX API
            response = self._call_api(prompt)

            # Parse response
            result = self._parse_response(response)

            return result

        except Exception as e:
            logger.error(f"ClovaX API error: {e}")
            return self._fallback_analysis(conversation_text, similar_cases)

    def _build_prompt(
        self,
        conversation_text: str,
        similar_cases: Optional[List[Tuple[str, float, Dict]]] = None
    ) -> str:
        """
        Build detailed prompt for ClovaX
        """
        # Format similar cases for context
        similar_context = ""
        if similar_cases and len(similar_cases) > 0:
            similar_context = "\n\n**유사한 실제 피싱 사례 (금융감독원):**\n"
            for i, (script, similarity, meta) in enumerate(similar_cases[:3], 1):
                label = meta.get('label', '알 수 없음')
                severity = meta.get('severity', 'UNKNOWN')
                similar_context += f"{i}. [{label}, {severity}] (유사도: {similarity*100:.1f}%)\n"
                similar_context += f"   \"{script[:150]}...\"\n\n"

        prompt = f"""당신은 보이스피싱 탐지 전문가입니다. 다음 통화 내용을 분석하여 보이스피싱 위험도를 정확하게 평가하세요.

**통화 내용:**
"{conversation_text}"
{similar_context}

**분석 기준:**
1. **맥락 분석**: 대화의 전체적인 흐름과 의도를 파악하세요
2. **교묘한 유도**: 직접적이지 않지만 개인정보나 금전을 요구하는 패턴
3. **심리적 조작**: 불안감, 긴급성, 권위 등을 이용한 조작 시도
4. **최신 수법**: 전통적 키워드가 없어도 피싱일 수 있습니다
5. **금감원 사례 비교**: 위 유사 사례와의 패턴 비교

**중요**:
- 단순 키워드 매칭이 아닌 대화의 맥락과 의도를 분석하세요
- "검찰", "경찰" 같은 단어가 없어도 피싱일 수 있습니다
- 정상적인 기관은 전화로 개인정보나 금전을 요구하지 않습니다

**응답 형식 (반드시 JSON):**
{{
  "risk_score": <0-100 정수>,
  "is_phishing": <true/false>,
  "confidence": <0-100 정수>,
  "techniques": [<탐지된 기법 리스트>],
  "reasoning": "<상세한 분석 근거>",
  "red_flags": [<의심스러운 요소들>],
  "recommendation": "<사용자에게 줄 조언>"
}}

JSON 응답:"""

        return prompt

    def _call_api(self, prompt: str) -> Dict:
        """
        Call ClovaX API
        """
        headers = {
            "X-NCP-CLOVASTUDIO-API-KEY": self.api_key,
            "X-NCP-APIGW-API-KEY": self.api_gateway_key,
            "X-NCP-CLOVASTUDIO-REQUEST-ID": self.request_id,
            "Content-Type": "application/json"
        }

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": "당신은 금융감독원 소속 보이스피싱 탐지 전문가입니다. 대화의 맥락을 정확히 분석하여 피싱 여부를 판단합니다."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "topP": 0.8,
            "topK": 0,
            "maxTokens": 1000,
            "temperature": 0.3,  # Lower temperature for more consistent analysis
            "repeatPenalty": 5.0,
            "stopBefore": [],
            "includeAiFilters": True
        }

        logger.info("Calling ClovaX API...")
        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            timeout=30
        )

        response.raise_for_status()
        return response.json()

    def _parse_response(self, api_response: Dict) -> Dict:
        """
        Parse ClovaX API response
        """
        try:
            # Extract content from response
            content = api_response['result']['message']['content']

            # Try to parse as JSON
            # Remove markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)

            # Validate required fields
            if "risk_score" not in result:
                raise ValueError("Missing risk_score in response")

            logger.info(f"ClovaX analysis: risk_score={result['risk_score']}, is_phishing={result.get('is_phishing', False)}")

            return result

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse ClovaX response: {e}")
            logger.debug(f"Raw response: {api_response}")
            raise

    def _fallback_analysis(
        self,
        conversation_text: str,
        similar_cases: Optional[List[Tuple[str, float, Dict]]] = None
    ) -> Dict:
        """
        Fallback analysis when ClovaX is not available
        Uses simple heuristics
        """
        logger.info("Using fallback analysis (ClovaX not available)")

        # Simple keyword-based fallback
        risk_score = 0
        techniques = []
        red_flags = []

        # Check for high-risk keywords
        high_risk_keywords = ["검찰", "경찰", "금감원", "국세청", "체포", "영장", "송금", "계좌번호", "비밀번호"]
        for keyword in high_risk_keywords:
            if keyword in conversation_text:
                risk_score += 15
                red_flags.append(f"'{keyword}' 키워드 탐지")

        # Check similar cases
        if similar_cases and len(similar_cases) > 0:
            max_similarity = max(s for _, s, _ in similar_cases)
            risk_score += int(max_similarity * 40)
            techniques.append("금감원 피싱 사례와 유사")

        risk_score = min(risk_score, 100)

        return {
            "risk_score": risk_score,
            "is_phishing": risk_score >= 70,
            "confidence": 60,  # Lower confidence for fallback
            "techniques": techniques,
            "reasoning": "ClovaX API를 사용할 수 없어 간단한 키워드 기반 분석을 사용했습니다.",
            "red_flags": red_flags,
            "recommendation": "의심스러운 경우 112에 신고하세요." if risk_score >= 50 else "정상 통화로 보입니다."
        }


def main():
    """Example usage"""
    client = ClovaXClient()

    if not client.is_available():
        print("⚠️ ClovaX API 키가 설정되지 않았습니다.")
        print("환경 변수를 설정하세요:")
        print("  - CLOVAX_API_KEY")
        print("  - CLOVAX_GATEWAY_KEY")
        return

    # Test case
    test_text = "안녕하세요, 서울중앙지검입니다. 당신 계좌가 범죄에 사용되었습니다."

    result = client.analyze_phishing(test_text)

    print("\n분석 결과:")
    print(f"위험도: {result['risk_score']}/100")
    print(f"피싱 여부: {result['is_phishing']}")
    print(f"신뢰도: {result['confidence']}%")
    print(f"근거: {result['reasoning']}")


if __name__ == "__main__":
    main()
