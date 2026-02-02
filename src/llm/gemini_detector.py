"""
Gemini 2.5 Flash + Rule-based Filter 통합 시스템
빠르고 저렴하며 정확한 단일 LLM 솔루션
"""
import logging
from typing import Dict, Optional
from src.llm.llm_clients.gemini_client import GeminiClient
from src.filters.rule_filter_v2 import RuleBasedFilterV2 as RuleBasedFilter

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

**1단계: 화자 역할 및 금전 흐름 분석 (가장 중요!)**

**화자 주도권 파악:**
- **발신자(Caller)가 요구하는 쪽**: 송금 요청, 정보 요구, 협박/압박 → 피싱 가능성
- **수신자(Receiver)가 항의하는 쪽**: 환불 요구, 항의, 민원 → 정상 (피싱 피해 상황 아님)

**금전 흐름 방향 파악:**
- **사용자가 돈을 보내는 경우**: 송금, 이체, 입금 → 피싱 가능성 높음
- **사용자가 돈을 받는 경우**: "송금해드릴게요", "지급", "환급" → 정상 가능성 높음
  - 🚨 **치명적 함정**: 돈을 준다면서 **URL 접속, 앱 설치, 비밀번호, 선입금**을 요구하면 **무조건 피싱(점수 95점 이상)**입니다. 절대 정상으로 판단하지 마세요.

**장소 이동 요청 판단:**
- **온라인/독립 공간**: 모텔, 조용한 곳 → 피싱 가능성
- **공공장소/공식 기관**: 경찰서, 병원, 지구대 방문 → 정상 (금전 요구 없으면)

**중요**: 사용자가 항의/민원을 제기하거나 돈을 받는 상황 = 안전 (보이스피싱 당하는 상황 아님)

**2단계: 피싱 판단 기준:**
다음 중 하나에 해당하면 보이스피싱:

**유형 A: 공공기관/기업 사칭 피싱**
- 공공기관/기업/금융사를 사칭하며 + 아래 중 하나 이상:
  - 금융 정보 요구 (계좌, 비밀번호, OTP, 송금)
  - 앱 설치/원격 제어 요구
  - 가짜 URL 접속 유도 (.com, .net 등)
  - 개인정보 요구 (주민번호, 카드번호)
  - 심리적 압박 (긴급성, 위협, 처벌 언급)
  - 장소 이동 요구 (모텔, 독립된 공간 등)

**유형 B: 가족/지인 사칭 피싱 (긴급 송금형)**
- 가족/지인을 사칭하며 + 아래 중 하나 이상:
  - 긴급한 금전 요구 (사고, 납치, 급전 필요)
  - 🚨 **친구/타인 계좌로 송금 요구** (가족이 친구 계좌를 알 리 없음) → 100% 피싱
  - 비정상적 상황 설정 (전화번호 변경, 배터리 부족, 연락 두절 압박)
  - 계좌번호를 구두로 전달하거나 문자로 찍어 보냄 ("박민수, 카카오뱅크")
  - **중요**: 10만원 이하 소액이라도 **친구/지인/타인 계좌**로 보내달라고 하면 100% 피싱입니다.

**유형 C: 투자/대출 사기**
- 과도한 수익률 보장 (예: 500% 수익) + 아래 중 하나 이상:
  - 선납금/가입비 요구
  - 원금 보장 약속 (불법)
  - 환불 거부 및 책임 회피

**유형 D: 사회공학 초기 단계 (로맨스 스캠, 관계 형성)**
- 🚨 **모르는 사람이 지나치게 친근하게 접근** + 아래 중 하나 이상:
  - 잘못 걸린 전화 위장하며 관계 형성 시도
  - 과도한 친밀감 표현 ("인연", "운명", "커피 쏠게")
  - 개인 연락처 확보 시도 (카톡, SNS 친구 추가)
  - **향후 금전 요구를 위한 사전 작업 단계** → 피싱으로 판단

**점수 부여 가이드 (반드시 준수):**
- **90~100점 (매우 위험)**: 유형 A/B/C/D에 해당하며, 앱 설치/URL/송금/개인정보 요구가 명확함.
- **70~89점 (위험)**: 피싱 징후가 뚜렷하나 결정적 행동 요구가 모호함.
- **30~69점 (주의)**: 피싱과 정상이 혼재되거나 판단이 어려움.
- **0~20점 (안전)**: 명확한 정상 케이스 기준에 해당함 (예약된 진료, 부동산 거래, 단순 문의).

**중요: 공공기관 이름이 나왔다고 무조건 피싱이 아닙니다!**
- 단순히 "~에서 전화드렸습니다"만으로는 피싱 아님
- 일반적인 업무 통화 (예약, 안내, 문의)는 정상
- 금융/개인정보/앱 설치 요구가 **없으면** 정상

**정상 케이스 판단 기준 (이 경우 20점 이하 부여):**
- 🔑 **"예약하신", "말씀하신"** ← 사전 합의된 일정/문의
- ✅ 병원/상담센터의 예약된 진료 (비대면 진료 포함)
- ✅ 기술지원 센터의 단순 설정 안내 (금전/환불 언급 없음)
- ✅ 채용 안내 및 시험 일정 공지 (웹캠/마이페이지 접속은 정상 절차)
- ✅ 보험금/합의금 지급 (사용자가 돈 받는 상황, 단 URL/앱 설치 없어야 함)
- ✅ **경찰서/지구대 직접 방문 요청** (가족 인계 등) → 피싱범은 경찰서 방문을 꺼림
- ✅ **월세/관리비 독촉** (임대차 계약 기반)
- ✅ **중고거래 상호 인증** (물건 확인, 안전결제 논의)

**부동산 거래 특별 판단 (매우 중요!):**
부동산 거래는 거액의 송금이 발생하지만 **정상 거래**입니다. 다음 패턴이 있으면 안전으로 판단:

1. **화자 관계 파악**: "계약서에 있는 거 맞죠?", "아까 말씀드린" 등 → 이미 합의된 거래
2. **전문 용어 클러스터**: '키 불출', '법무사', '등기', '잔금', '등기 이전', '소유권 이전' → 부동산 거래 용어군
3. **논리적 절차**: "법무사 → 신분증 → 등기" 흐름은 한국 부동산 표준 절차
4. **사전 확인 언급**: "계약서", "집주인", "매도인" 등은 사전 관계 존재

**채용/면접 관련 구분:**
- **정상**: "집이나 독립된 공간", "마이페이지 접속", "웹캠 설정" (일반적 채용 절차)
- **피싱**: "모텔/숙박업소로 이동", "보안 앱 설치", "원격 제어" (디지털 감금 시도)

**부동산 거래 감지 시 출력:**
{"score": 15, "is_phishing": false, "reasoning": "거액 송금 요청이 있으나 부동산 거래의 정상적인 절차로 판단됨 (계약서 확인, 법무사 등기 절차)"}

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
