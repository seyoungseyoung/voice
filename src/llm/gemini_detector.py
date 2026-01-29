"""
Gemini 2.5 Flash + Rule-based Filter 통합 시스템
빠르고 저렴하며 정확한 단일 LLM 솔루션
"""
import logging
from typing import Dict, Optional
from src.llm.llm_clients.gemini_client import GeminiClient
from src.filters.rule_filter import RuleBasedFilter

logger = logging.getLogger(__name__)


class GeminiPhishingDetector:
    """
    Gemini 2.5 Flash + Rule-based Filter 조합
    - 빠른 응답 속도
    - 저렴한 비용 (무료 티어)
    - 96.3% 기본 정확도 + Rule Filter로 98%+ 목표
    """

    def __init__(self):
        self.gemini = GeminiClient()
        self.rule_filter = RuleBasedFilter()
        self.model_name = "Gemini 2.5 Flash + Rule Filter"

        if not self.gemini.is_available():
            logger.warning("Gemini API key not configured")
        else:
            logger.info("✓ Gemini Phishing Detector initialized")

    def is_available(self) -> bool:
        """Gemini API 사용 가능 여부"""
        return self.gemini.is_available()

    def analyze(self, text: str, enable_filter: bool = True) -> Dict:
        """
        보이스피싱 분석 (Gemini + Rule Filter)

        Args:
            text: 통화 내용
            enable_filter: Rule Filter 적용 여부 (기본: True)

        Returns:
            {
                "score": 최종 점수 (0-100),
                "risk_level": 위험도,
                "is_phishing": 피싱 여부,
                "reasoning": 판정 이유,
                "model": 모델명,
                "filter_applied": 필터 적용 여부,
                "llm_score": 원본 LLM 점수,
                "keyword_analysis": 키워드 분석
            }
        """
        if not self.is_available():
            return self._error_response("Gemini API not configured")

        try:
            # Step 1: Gemini 분석
            logger.info(f"🔍 Gemini analyzing: {text[:50]}...")

            prompt = self._build_prompt()
            gemini_result = self.gemini.analyze_phishing(text, prompt)

            llm_score = gemini_result.get("score", 50)
            llm_reasoning = gemini_result.get("reasoning", "")

            # Step 2: Rule Filter 적용 (항상 실행해서 키워드 분석 얻기)
            filter_result = None
            if enable_filter:
                logger.info("⚙️ Applying Rule-based Filter...")
                filter_result = self.rule_filter.filter(
                    text=text,
                    llm_score=llm_score,
                    llm_reasoning=llm_reasoning
                )

                final_score = filter_result["final_score"]
                filter_applied = filter_result["filter_applied"]
                # 항상 keyword_analysis 가져옴 (필터 적용 여부와 무관)
                keyword_analysis = filter_result.get("keyword_analysis", {})

                # 필터가 적용되었으면 로그
                if filter_applied:
                    logger.info(
                        f"✓ Rule Filter {'downgraded' if final_score < llm_score else 'upgraded'}: "
                        f"{llm_score} → {final_score} ({filter_result['reason']})"
                    )
            else:
                final_score = llm_score
                filter_applied = False
                keyword_analysis = {}

            # Step 3: 최종 위험도 판정
            risk_level, is_phishing = self._calculate_risk(final_score)

            # 탐지된 피싱 기법 추출 (항상 표시)
            detected_techniques = filter_result.get("detected_techniques", []) if filter_result else []

            # Component scores 계산 (원래 시스템 점수 복원)
            component_scores = {}
            if keyword_analysis:
                # 범죄 키워드 점수: 0-10개 기준 → 0-100
                crime_score = min(keyword_analysis.get("crime", 0) * 10, 100)
                # 정상 키워드 점수: 많을수록 안전 → 역산 (10개 기준)
                legit_score = max(100 - keyword_analysis.get("legit", 0) * 10, 0)
                # 긴급성 키워드 점수: 0-10개 기준 → 0-100
                urgency_score = min(keyword_analysis.get("urgency", 0) * 10, 100)

                component_scores = {
                    "keyword": crime_score,
                    "sentiment": urgency_score,
                    "similarity": legit_score
                }

            # Reasoning 결정: Rule Filter가 점수를 변경했으면 Filter의 reason만 사용
            final_reasoning = gemini_result.get("reasoning", "")
            if filter_applied and filter_result and final_score != llm_score:
                # 점수가 변경되었으면 Filter reason만 표시 (Gemini 원본은 숨김)
                final_reasoning = filter_result.get("reason", "")

            return {
                "score": final_score,
                "risk_level": risk_level,
                "is_phishing": is_phishing,
                "reasoning": final_reasoning,
                "model": self.model_name,
                "filter_applied": filter_applied,
                "llm_score": llm_score,
                "keyword_analysis": keyword_analysis,
                "component_scores": component_scores,
                "key_points": gemini_result.get("key_points", []),
                "detected_techniques": detected_techniques
            }

        except Exception as e:
            logger.error(f"Gemini Detector error: {e}")
            return self._error_response(str(e))

    def _build_prompt(self) -> str:
        """Gemini용 프롬프트 생성"""
        return """당신은 보이스피싱 탐지 전문가입니다. 다음 통화 내용을 분석하세요.

**피싱 판단 기준 (모두 해당해야 피싱):**
1. 공공기관/기업을 **사칭**하며 + 아래 중 하나 이상:
   - 금융 정보 요구 (계좌, 비밀번호, OTP, 송금)
   - 앱 설치/원격 제어 요구
   - 가짜 URL 접속 유도 (.com, .net 등)
   - 개인정보 요구 (주민번호, 카드번호)
2. 심리적 압박 (긴급성, 위협, 처벌 언급)
3. 장소 이동 요구 (모텔, 독립된 공간 등)

**중요: 공공기관 이름이 나왔다고 무조건 피싱이 아닙니다!**
- 단순히 "~에서 전화드렸습니다"만으로는 피싱 아님
- 일반적인 업무 통화 (예약, 안내, 문의)는 정상
- 금융/개인정보/앱 설치 요구가 **없으면** 정상

**정상 케이스 예시:**
- 병원/상담센터의 예약 안내
- 회사/식당 예약 전화
- 기술지원 센터의 설정 안내 (공식 기능 사용)
- 채용 안내 및 시험 일정 공지

**중요:** 응답은 반드시 유효한 JSON 형식이어야 합니다. reasoning 필드에는 줄바꿈이나 특수문자를 사용하지 마세요.

**응답 형식 (유효한 JSON만 출력):**
{"score": 95, "is_phishing": true, "reasoning": "금융감독원을 사칭하며 앱 설치를 유도하고 개인정보를 요구함"}

위 형식을 정확히 따라 JSON만 출력하세요:"""

    def _calculate_risk(self, score: float) -> tuple:
        """
        점수를 위험도로 변환

        Returns:
            (risk_level: str, is_phishing: bool)
        """
        if score >= 85:
            return ("고위험 (차단 권장)", True)
        elif score >= 70:
            return ("중위험 (경고)", True)
        elif score >= 50:
            return ("낮은 위험 (주의)", False)
        elif score >= 30:
            return ("매우 낮음 (정상 가능성)", False)
        else:
            return ("안전", False)

    def _error_response(self, error: str) -> Dict:
        """에러 응답"""
        return {
            "score": 50,
            "risk_level": "알 수 없음",
            "is_phishing": False,
            "reasoning": f"Error: {error}",
            "model": self.model_name,
            "filter_applied": False,
            "llm_score": 50,
            "keyword_analysis": {},
            "key_points": []
        }

    def get_filter_statistics(self) -> Dict:
        """Rule Filter 통계 반환"""
        return self.rule_filter.get_statistics()

    def reset_filter_statistics(self):
        """Rule Filter 통계 초기화"""
        self.rule_filter.reset_statistics()
