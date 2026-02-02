"""
Rule-based Filter v2 - 명확한 우선순위와 로직
"""
import logging
from typing import Dict, Optional
import re

logger = logging.getLogger(__name__)

# 2차 LLM 검증용
try:
    from src.llm.llm_clients.gemini_client import GeminiClient
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("GeminiClient not available - 2nd stage verification disabled")


class RuleBasedFilterV2:
    """
    명확한 우선순위와 로직을 가진 Rule Filter

    필터 적용 순서:
    0. 사용자 항의/민원 → 정상 (20점)
    1. 채권 추심 → 중위험 (50점)
    2. 중고거래 사기 → 중위험 (50점)
    3. Web3 스캠 → 고위험 유지 (85점+)
    4. CEO Fraud (개인 계좌) → 피싱 유지
    5. 헤드헌터 제외 → 피싱 유지
    6. 2차 LLM 검증 (60-98점) → 재평가
    7. 원격 제어 + 정상 서비스 → 정상 (25점)
    8. 낮은 점수 + 고위험 키워드 → 상향 (70점)
    9. 긴급성 + 금융 키워드 → 상향 (85점)
    """

    def __init__(self):
        self.stats = {
            "total_filtered": 0,
            "rule0_user_complaint": 0,
            "rule1_debt_collection": 0,
            "rule2_commerce_fraud": 0,
            "rule3_web3_scam": 0,
            "rule4_ceo_fraud": 0,
            "rule5_headhunter": 0,
            "rule6_second_stage": 0,
            "rule7_remote_legit": 0,
            "rule8_keyword_upgrade": 0,
            "rule9_urgency_upgrade": 0,
            "passed": 0
        }

        # 2차 LLM 초기화
        if GEMINI_AVAILABLE:
            try:
                self.second_stage_llm = GeminiClient()
                logger.info("✓ 2nd stage LLM verification enabled (Gemini Flash)")
            except Exception as e:
                self.second_stage_llm = None
                logger.warning(f"Failed to initialize 2nd stage LLM: {e}")
        else:
            self.second_stage_llm = None

    def filter(self, text: str, llm_score: float, llm_reasoning: str = "") -> Dict:
        """
        LLM 판정 결과를 Rule 기반으로 2차 검증

        Returns:
            {
                "final_score": 최종 점수,
                "risk_level": 위험도,
                "reason": 필터 적용 이유,
                "filter_applied": 필터 적용 여부,
                "keyword_analysis": {...}
            }
        """
        self.stats["total_filtered"] += 1
        text_lower = text.lower()

        # 키워드 분석 (모든 규칙에서 사용)
        keyword_analysis = self._analyze_keywords(text_lower, llm_reasoning.lower())

        # ===== Rule 0: 사용자 항의/민원 (최우선 정상 판정) =====
        if self._is_user_complaint(text_lower):
            self.stats["rule0_user_complaint"] += 1
            return self._make_response(
                score=20,
                reason="사용자가 항의/민원을 제기하는 상황 (피싱 피해자 아님)",
                filter_applied=True,
                original_score=llm_score,
                keyword_analysis=keyword_analysis
            )

        # ===== Rule 1: 채권 추심 → 중위험 =====
        if self._is_debt_collection(text_lower):
            self.stats["rule1_debt_collection"] += 1
            return self._make_response(
                score=50,
                reason="불법 채권 추심으로 판단 (피싱은 아니지만 경고 필요)",
                filter_applied=True,
                original_score=llm_score,
                keyword_analysis=keyword_analysis
            )

        # ===== Rule 2: 중고거래 사기 → 중위험 =====
        if self._is_commerce_fraud(text_lower):
            self.stats["rule2_commerce_fraud"] += 1
            return self._make_response(
                score=50,
                reason="중고거래 사기 패턴 감지 (안전결제 거부)",
                filter_applied=True,
                original_score=llm_score,
                keyword_analysis=keyword_analysis
            )

        # ===== Rule 3: Web3 스캠 → 고위험 유지 =====
        web3_risk = self._detect_web3_scam(text_lower)
        if web3_risk:
            self.stats["rule3_web3_scam"] += 1
            return self._make_response(
                score=max(85, llm_score),
                reason="Web3/암호화폐 스캠 패턴 감지 (지갑 연결/트랜잭션 서명 요구)",
                filter_applied=True,
                original_score=llm_score,
                keyword_analysis=keyword_analysis
            )

        # ===== Rule 4: CEO Fraud 체크 (개인 계좌 = 피싱 유지) =====
        # 내부 업무 패턴이지만 개인 계좌 송금은 제외
        if self._is_ceo_fraud(text_lower):
            self.stats["rule4_ceo_fraud"] += 1
            # CEO Fraud는 LLM 점수 유지 (필터로 격하하지 않음)
            logger.info(f"Rule 4: CEO Fraud detected - maintaining LLM score {llm_score}")
            # 다음 규칙으로 넘어가도록 아무것도 반환하지 않음

        # ===== Rule 5: 내부 업무 지시 (헤드헌터 제외) → 중위험 =====
        if self._is_internal_instruction(text_lower) and 70 <= llm_score <= 95:
            # CEO Fraud가 아닌 경우에만 적용
            if not self._is_ceo_fraud(text_lower):
                self.stats["rule5_headhunter"] += 1
                return self._make_response(
                    score=50,
                    reason="내부 업무 지시 패턴 (CEO Fraud 가능성 있으나 정상 업무일 수도 있음)",
                    filter_applied=True,
                    original_score=llm_score,
                    keyword_analysis=keyword_analysis
                )

        # ===== Rule 6: 2차 LLM 검증 (60-98점 애매한 케이스) =====
        if 60 <= llm_score <= 98 and self.second_stage_llm:
            second_check = self._second_stage_verification(text, llm_score, llm_reasoning)
            if second_check["is_safe"]:
                self.stats["rule6_second_stage"] += 1
                logger.info(
                    f"Rule 6: 2차 LLM 검증 완료 - 정상 판정 "
                    f"(원점수:{llm_score})"
                )
                return self._make_response(
                    score=20,
                    reason=f"2차 LLM 검증: {second_check['reasoning']}",
                    filter_applied=True,
                    original_score=llm_score,
                    keyword_analysis=keyword_analysis
                )

        # ===== Rule 7: 원격 제어 + 정상 서비스 패턴 =====
        if self._is_remote_legit_service(text_lower, llm_reasoning.lower(), llm_score, keyword_analysis):
            self.stats["rule7_remote_legit"] += 1
            return self._make_response(
                score=25,
                reason="원격 지원 요청이지만 정상 서비스로 판단됨 (예약된 일정, 공식 채널)",
                filter_applied=True,
                original_score=llm_score,
                keyword_analysis=keyword_analysis
            )

        # ===== Rule 8: 낮은 점수 + 고위험 키워드 많음 → 상향 =====
        if llm_score < 60 and keyword_analysis["crime"] >= 5:
            self.stats["rule8_keyword_upgrade"] += 1
            return self._make_response(
                score=70,
                reason="LLM 점수는 낮지만 다수의 피싱 키워드 감지됨",
                filter_applied=True,
                original_score=llm_score,
                keyword_analysis=keyword_analysis
            )

        # ===== Rule 9: 긴급성 + 금융 키워드 → 상향 =====
        if (keyword_analysis["urgency"] >= 2 and
            keyword_analysis["crime"] >= 3 and
            keyword_analysis["legit"] <= 2 and
            llm_score < 80):
            self.stats["rule9_urgency_upgrade"] += 1
            return self._make_response(
                score=85,
                reason="긴급성 압박 + 금융/수사 키워드 조합 (전형적 피싱 패턴)",
                filter_applied=True,
                original_score=llm_score,
                keyword_analysis=keyword_analysis
            )

        # ===== Rule 통과: LLM 판정 유지 =====
        self.stats["passed"] += 1
        return self._make_response(
            score=llm_score,
            reason="Rule filter passed - LLM 판정 유지",
            filter_applied=False,
            original_score=llm_score,
            keyword_analysis=keyword_analysis
        )

    # ========== 개별 패턴 감지 함수 ==========

    def _is_user_complaint(self, text: str) -> bool:
        """사용자가 항의/민원하는 상황"""
        complaint_keywords = [
            "환불해", "환불하세요", "환불 해주세요", "내놔",
            "신고", "고소", "소비자원", "공정위", "경찰서 갈",
            "항의합니다", "항의드립니다", "책임지세요", "책임져"
        ]
        return sum(1 for kw in complaint_keywords if kw in text) >= 2

    def _is_debt_collection(self, text: str) -> bool:
        """채권 추심 패턴 (불법이지만 피싱 아님)"""
        debt_keywords = [
            "이자", "원금", "대출금", "채무", "빌린",
            "받은 돈", "연체", "상환", "변제", "입금 안", "입금해"
        ]
        debt_count = sum(1 for kw in debt_keywords if kw in text)

        # 공공기관 사칭이 없어야 함
        # E03(대환대출 사기) 방지를 위해 금융기관/센터 사칭도 포함
        impersonation = ["검찰", "경찰", "금감원", "국세청", "진흥원", "지원센터", "은행", "캐피탈"]
        has_impersonation = any(kw in text for kw in impersonation)

        # 대출 사기(대환대출) 키워드가 있으면 채권 추심(정상)으로 분류하면 안 됨
        loan_fraud_keywords = ["대환", "햇살론", "정부", "지원금", "가상계좌", "신청서", "대상자"]
        has_loan_fraud = any(kw in text for kw in loan_fraud_keywords)

        # 채권 추심 키워드 존재 + 사칭 없음 + 대출 사기 패턴 아님
        return debt_count >= 2 and not has_impersonation and not has_loan_fraud

    def _is_commerce_fraud(self, text: str) -> bool:
        """중고거래 사기 패턴"""
        commerce_keywords = [
            "중고나라", "중고거래", "당근", "번개장터", "중고",
            "안전결제", "직거래", "택배", "선입금"
        ]
        return sum(1 for kw in commerce_keywords if kw in text) >= 2

    def _detect_web3_scam(self, text: str) -> bool:
        """Web3/암호화폐 스캠"""
        web3_critical = [
            "지갑 연결", "wallet connect", "트랜잭션 서명",
            "transaction sign", "시드 구문", "private key"
        ]
        web3_warning = [
            "에어드랍", "airdrop", "거버넌스", "스냅샷",
            "클레임", "claim", "가스비", "gas"
        ]

        critical_count = sum(1 for kw in web3_critical if kw in text)
        warning_count = sum(1 for kw in web3_warning if kw in text)

        return critical_count >= 1 or (warning_count >= 2)

    def _is_ceo_fraud(self, text: str) -> bool:
        """CEO Fraud 명백한 신호 (법인→개인 계좌)"""
        ceo_signals = [
            "개인 계좌", "개인통장", "대표님 개인", "사장님 개인",
            "법인 계좌에서", "법인통장에서"
        ]
        return any(signal in text for signal in ceo_signals) and "개인" in text

    def _is_internal_instruction(self, text: str) -> bool:
        """내부 업무 지시 패턴 (헤드헌터 제외)"""
        titles = ["대리", "과장", "부장", "팀장", "실장", "이사", "전무"]
        context = ["거래처", "법인 계좌", "법인통장", "결재", "보고", "미팅", "회의"]

        # 외부 헤드헌터 제외
        external_recruiter = ["헤드헌팅", "헤드헌터", "채용 공고", "면접 제안"]
        if any(kw in text for kw in external_recruiter):
            return False

        has_title = any(kw in text for kw in titles)
        has_context = any(kw in text for kw in context)

        return has_title and has_context

    def _is_remote_legit_service(self, text: str, reasoning: str, llm_score: float, kw_analysis: Dict) -> bool:
        """원격 제어 + 정상 서비스 패턴"""
        if not (60 <= llm_score <= 95):
            return False

        remote_keywords = ["원격", "remote", "제어", "control", "앱", "설치", "접속"]
        is_remote = any(kw in text or kw in reasoning for kw in remote_keywords)

        if not is_remote:
            return False

        # 정상 신호 체크
        # "공식"은 피싱범도 자주 쓰므로 제외, "말씀하신/예약" 등 상호작용 확인된 것만 인정
        legit_signals = ["예약", "예정", "말씀하신"]
        has_legit = any(sig in text for sig in legit_signals)

        # 환불/결제/금전 관련 내용이 있으면 원격 제어는 무조건 위험 (Rule 7 적용 금지)
        money_keywords = ["환불", "결제", "카드", "돈", "금전", "보상"]
        has_money_context = any(kw in text for kw in money_keywords)

        fake_url_patterns = ["-support.com", "-center.com", "-help.com", "bit.ly", "tinyurl"]
        has_fake_url = any(pattern in text for pattern in fake_url_patterns)

        return (has_legit and
                not has_fake_url and
                not has_money_context and
                kw_analysis["crime"] <= 1 and
                kw_analysis["urgency"] == 0)

    def _analyze_keywords(self, text: str, reasoning: str) -> Dict:
        """키워드 분석"""
        crime_keywords = [
            "송금", "계좌", "입금", "출금", "이체", "환불", "환급",
            "대포통장", "금전", "돈", "현금", "카드번호", "비밀번호",
            "OTP", "공인인증서", "검찰", "경찰", "검사", "형사", "수사"
        ]

        legit_keywords = [
            "서비스센터", "고객센터", "상담센터", "AS", "기사님",
            "예약", "예정", "안내", "일정", "공식", "마이페이지",
            "부동산", "법무사", "등기", "계약서", "잔금"
        ]

        urgency_keywords = [
            "지금 당장", "즉시", "급히", "바로", "빨리",
            "안 하면", "불이익", "손해", "마감", "기한"
        ]

        crime_count = sum(1 for kw in crime_keywords if kw in text)
        legit_count = sum(1 for kw in legit_keywords if kw in text)
        urgency_count = sum(1 for kw in urgency_keywords if kw in text)

        return {
            "crime": crime_count,
            "legit": legit_count,
            "urgency": urgency_count
        }

    def _second_stage_verification(self, text: str, first_score: float, first_reasoning: str) -> Dict:
        """2차 LLM 검증"""
        if not self.second_stage_llm:
            return {"is_safe": False, "reasoning": "2nd stage LLM not available"}

        verification_prompt = f"""당신은 보이스피싱 2차 검증 전문가입니다.

**배경**:
- 1차 AI 판정: {first_score}점 (피싱 의심)
- 1차 판정 이유: {first_reasoning}

**재검증 임무**: 3단계 체계적 분석을 수행하세요.

## 📋 Step 1: 예외 상황 매칭

다음 3가지 **예외 상황** 중 하나에 해당하는지 확인:

### ✅ 예외 1: 사용자가 돈을 받는 상황
- "송금해드릴게요", "입금해드릴", "지급", "환급", "보상금"
- 개인정보(주민번호, 계좌) 요구 → 세금/송금 처리용이므로 정상

### ✅ 예외 2: 사용자가 항의/협박하는 상황
- "환불해", "환불하세요", "신고하겠", "고소하겠", "책임져"

### ✅ 예외 3: 예약된 일정
- "예약하신", "말씀하신" → 사전 합의된 일정

## 🔍 Step 2: 함정 패턴 체크

예외 1에 해당하더라도 다음 **피싱 신호**가 있으면 피싱:
- ⚠️ 앱 설치 요구 (팀뷰어, 원격, APK)
- ⚠️ URL 접속 요구 (.com, .net, bit.ly)
- ⚠️ 원격 제어 요구 (접속번호, 화면 공유)
- ⚠️ **타인/친구 계좌 송금 요구** (가족 사칭 시 소액이라도 피싱)

## ✅ Step 3: 최종 판단

**답변 형식 (JSON)**:
{{
  "step1_exception_match": "예외 1/2/3 중 해당하는가? (예외번호 또는 '해당없음')",
  "step2_trap_detected": "함정 패턴 발견? (yes/no)",
  "step3_final_decision": "정상 또는 피싱",
  "score": 0-100,
  "is_phishing": true 또는 false,
  "reasoning": "Step 1~3 종합 판단 결과 (2-3문장)"
}}

**핵심 로직**:
- 예외 해당 ✅ + 함정 없음 ✅ → 정상 (score: 0-30, is_phishing: false)
- 예외 해당 ✅ + 함정 있음 ❌ → 피싱 (score: {first_score}, is_phishing: true)
- 예외 해당 없음 ❌ → 피싱 (score: {first_score}, is_phishing: true)"""

        try:
            result = self.second_stage_llm.analyze_phishing(text, verification_prompt)
            is_phishing = result.get("is_phishing", True)
            second_score = result.get("score", first_score)
            reasoning_text = result.get("reasoning", "2차 검증 완료")

            is_safe = not is_phishing or second_score <= 30

            return {
                "is_safe": is_safe,
                "reasoning": reasoning_text,
                "second_score": second_score
            }

        except Exception as e:
            logger.error(f"2nd stage verification failed: {e}")
            return {"is_safe": False, "reasoning": f"Error: {str(e)}"}

    def _make_response(self, score: float, reason: str, filter_applied: bool,
                      original_score: float, keyword_analysis: Dict) -> Dict:
        """응답 생성"""
        risk_level = self._get_risk_level(score)
        return {
            "final_score": score,
            "risk_level": risk_level,
            "reason": reason,
            "filter_applied": filter_applied,
            "original_score": original_score,
            "keyword_analysis": keyword_analysis,
            "detected_techniques": []
        }

    def _get_risk_level(self, score: float) -> str:
        """점수를 위험도로 변환"""
        if score >= 85:
            return "고위험 (차단 권장)"
        elif score >= 70:
            return "중위험 (경고)"
        elif score >= 50:
            return "낮은 위험 (주의)"
        elif score >= 30:
            return "매우 낮음 (정상 가능성)"
        else:
            return "안전"

    def get_statistics(self) -> Dict:
        """필터 통계 반환"""
        return self.stats

    def reset_statistics(self):
        """통계 초기화"""
        for key in self.stats:
            self.stats[key] = 0
