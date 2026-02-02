"""
Rule-based Filter for reducing False Positives
논리적 필터로 정상 서비스(원격지원, 채용검사 등)를 보호
"""
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# 2차 LLM 검증을 위해 Gemini Client import
try:
    from src.llm.llm_clients.gemini_client import GeminiClient
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("GeminiClient not available - 2nd stage verification disabled")


class RuleBasedFilter:
    """
    LLM 판정 후 2차 검증 필터
    목적: False Positive 감소 (정상 원격지원 서비스 보호)
    """

    # 범죄 의도 키워드 (피싱 신호)
    CRIME_KEYWORDS = [
        # 금융 관련
        "송금", "계좌", "입금", "출금", "이체", "환불", "환급",
        "대포통장", "금전", "돈", "현금", "카드번호", "비밀번호",
        "보안코드", "OTP", "공인인증서", "금융거래",

        # 수사기관 사칭
        "검찰", "경찰", "검사", "형사", "수사", "범죄", "피의자",
        "영장", "체포", "구속", "수배", "조사", "출석",

        # 금융기관 사칭
        "금감원", "금융감독원", "금융위원회", "한국은행",
        "예금보험공사", "신용정보원",

        # 디지털 감금 패턴
        "모텔", "숙박", "호텔", "독립된 공간", "조용한 곳",
        "이동", "장소", "위치", "폰 끄지",

        # 악성 앱/URL
        "APK", "설치", "다운로드", "링크", "URL", "접속",
        ".com", ".net", ".info", "bit.ly"
    ]

    # 정상 서비스 키워드 (합법 신호)
    LEGIT_KEYWORDS = [
        # 공식 서비스
        "서비스센터", "고객센터", "상담센터", "콜센터",
        "AS", "A/S", "기사님", "상담사", "담당자",

        # 예약/일정
        "예약", "예정", "안내", "일정", "시간",

        # 공식 채널 (명확히 "공식"이라는 단어가 붙은 경우만)
        "공식 홈페이지", "공식 사이트", "공식 앱", "공식 어플",
        "마이페이지", "카카오톡", "줌", "Zoom", "화상",

        # 원격 지원
        "접속번호", "원격 상담", "기본 설정", "기본 기능",
        "설정 메뉴", "화면 공유",

        # 채용/면접
        "채용", "면접", "인사팀", "합격", "지원", "응시",
        "시험", "검사", "역량", "서류",

        # 의료
        "진료", "상담", "병원", "의사", "환자", "프라이버시",

        # 부동산/법률 (정상 거래)
        "부동산", "공인중개사", "중개사무소", "법무사", "등기",
        "계약서", "잔금", "집주인", "매도인", "매수인",
        "키 불출", "등기 이전", "소유권 이전", "전입신고"
    ]

    # 공식 도메인 패턴 (실제 정부/공공기관 도메인)
    OFFICIAL_DOMAINS = [
        ".go.kr",  # 대한민국 정부기관
        ".or.kr",  # 비영리 단체
        ".ac.kr",  # 대학교
    ]

    # 가짜 URL 패턴 (피싱에서 자주 사용하는 도메인 패턴)
    FAKE_URL_PATTERNS = [
        "-support.com", "-center.com", "-help.com", "-service.com",
        "-verify.com", "-security.com", "-update.com", "-login.com",
        "-bank.net", "-govt.net", "-official.net",
        "bit.ly", "tinyurl", "short"
    ]

    # Web3/암호화폐 스캠 키워드
    WEB3_SCAM_KEYWORDS = {
        "critical": [
            "지갑 연결", "wallet connect", "트랜잭션 서명", "transaction sign",
            "시드 구문", "seed phrase", "프라이빗 키", "private key",
            "브릿지 사이트", "스왑 사이트", "클레임 사이트", "bridge site"
        ],
        "warning": [
            "에어드랍", "airdrop", "거버넌스 토큰", "governance token",
            "스냅샷", "snapshot", "가스비 지원", "gas fee",
            "클레임", "claim", "민팅", "minting", "재단 운영팀"
        ]
    }

    # 채권 추심 키워드 (불법 추심이지만 피싱은 아님)
    DEBT_COLLECTION_KEYWORDS = [
        "이자 입금", "이자", "원금 상환", "원금", "대출금", "채무", "빌린",
        "받은 돈", "연체", "상환일", "변제", "입금 안", "입금해"
    ]

    # 내부 조직 업무 지시 키워드 (CEO Fraud 경계 케이스)
    INTERNAL_WORK_KEYWORDS = {
        "titles": ["대리", "과장", "부장", "팀장", "실장", "이사", "전무"],
        "context": ["거래처", "법인 계좌", "법인통장", "결재", "보고", "미팅", "회의", "프로젝트"]
    }

    # 중고거래 사기 키워드 (전화 사기지만 보이스피싱은 아님)
    COMMERCE_FRAUD_KEYWORDS = [
        "중고나라", "중고거래", "당근", "번개장터", "중고", "직거래",
        "안전결제", "택배", "반값택배", "일반택배", "선입금"
    ]

    # 긴급/압박 키워드 (피싱에서 자주 사용)
    URGENCY_KEYWORDS = [
        "지금 당장", "즉시", "급히", "바로", "빨리",
        "안 하면", "하지 않으면", "불이익", "손해",
        "시간 내", "마감", "기한"
    ]

    # 금전 수령 키워드 (사용자가 돈을 받는 상황 - 정상)
    MONEY_RECEIVING_KEYWORDS = [
        "송금해드릴게요", "송금해 드릴게요", "송금 해드릴게요",
        "입금해드릴게요", "입금해 드릴게요", "입금 해드릴게요",
        "지급", "환급", "보상금", "지원금", "배상금"
    ]

    # 사용자 항의 키워드 (사용자가 협박/항의하는 상황 - 정상)
    USER_COMPLAINT_KEYWORDS = [
        "환불하세요", "환불 해주세요", "환불해 주세요",
        "신고하겠", "고소하겠", "소비자원", "공정위",
        "항의합니다", "항의드립니다", "책임지세요"
    ]

    def __init__(self):
        self.stats = {
            "total_filtered": 0,
            "downgraded": 0,
            "upgraded": 0,
            "passed": 0,
            "second_stage_checks": 0,
            "second_stage_downgrades": 0
        }
        # 금액 추출용 정규식
        import re
        self.amount_pattern = re.compile(r'([\d,]+)\s*만\s*원')

        # 2차 LLM 검증용 Gemini Client 초기화
        if GEMINI_AVAILABLE:
            try:
                self.second_stage_llm = GeminiClient()
                logger.info("✓ 2nd stage LLM verification enabled (Gemini Flash)")
            except Exception as e:
                self.second_stage_llm = None
                logger.warning(f"Failed to initialize 2nd stage LLM: {e}")
        else:
            self.second_stage_llm = None

    def detect_web3_scam(self, text: str) -> Optional[str]:
        """Web3/암호화폐 스캠 패턴 감지"""
        text_lower = text.lower()

        critical_count = sum(1 for kw in self.WEB3_SCAM_KEYWORDS["critical"] if kw in text_lower)
        warning_count = sum(1 for kw in self.WEB3_SCAM_KEYWORDS["warning"] if kw in text_lower)

        if critical_count >= 2:
            return "CRITICAL_SCAM"  # 점수 하향 금지
        if critical_count >= 1 and warning_count >= 2:
            return "HIGH_RISK"  # 최소 70점 유지
        return None

    def detect_debt_collection(self, text: str) -> bool:
        """채권 추심 패턴 감지 (불법 추심이지만 피싱 아님)"""
        text_lower = text.lower()
        debt_count = sum(1 for kw in self.DEBT_COLLECTION_KEYWORDS if kw in text_lower)

        # 채권 추심 키워드 2개 이상 + 공공기관 사칭 없음
        if debt_count >= 2:
            impersonation_keywords = ["검찰", "경찰", "금감원", "국세청", "금융감독원"]
            has_impersonation = any(kw in text_lower for kw in impersonation_keywords)
            return not has_impersonation
        return False

    def detect_internal_instruction(self, text: str) -> bool:
        """내부 조직 업무 지시 패턴 감지 (CEO Fraud 경계, 중간 위험도)"""
        text_lower = text.lower()

        # 조직 호칭 존재
        has_title = any(kw in text_lower for kw in self.INTERNAL_WORK_KEYWORDS["titles"])
        # 업무 맥락 존재
        has_context = any(kw in text_lower for kw in self.INTERNAL_WORK_KEYWORDS["context"])

        # 공공기관/금융기관 사칭 없음
        impersonation_keywords = ["검찰", "경찰", "금감원", "국세청", "금융감독원", "은행", "카드사"]
        has_impersonation = any(kw in text_lower for kw in impersonation_keywords)

        # CEO Fraud 명백한 신호 체크
        ceo_fraud_signals = [
            "개인 계좌", "개인통장", "대표님 개인", "사장님 개인",
            "법인 계좌에서", "법인통장에서"
        ]
        has_ceo_fraud_signal = any(signal in text_lower for signal in ceo_fraud_signals)

        # 법인→개인 송금은 CEO Fraud이므로 내부 업무로 격하하지 않음
        if has_ceo_fraud_signal and ("개인" in text_lower):
            return False

        # 조직 호칭 + 업무 맥락 + 사칭 없음 = 내부 업무 지시
        return has_title and has_context and not has_impersonation

    def detect_commerce_fraud(self, text: str) -> bool:
        """중고거래 사기 패턴 감지 (전화 사기지만 피싱은 아님)"""
        text_lower = text.lower()
        commerce_count = sum(1 for kw in self.COMMERCE_FRAUD_KEYWORDS if kw in text_lower)

        # 중고거래 키워드 2개 이상 = 중고거래 사기
        return commerce_count >= 2

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

    def filter(
        self,
        text: str,
        llm_score: float,
        llm_reasoning: str = ""
    ) -> Dict:
        """
        LLM 판정 결과를 Rule 기반으로 2차 검증

        Args:
            text: 통화 내용
            llm_score: LLM이 판정한 점수 (0-100)
            llm_reasoning: LLM의 판정 이유

        Returns:
            {
                "final_score": 최종 점수,
                "risk_level": 위험도,
                "reason": 필터 적용 이유,
                "filter_applied": 필터 적용 여부
            }
        """
        self.stats["total_filtered"] += 1

        # Web3 스캠 체크 (최우선)
        web3_risk = self.detect_web3_scam(text)
        if web3_risk == "CRITICAL_SCAM":
            # 필터 무시, LLM 점수 유지 (최소 85점 보장)
            final_score = max(85, llm_score)
            return {
                "final_score": final_score,
                "risk_level": self._get_risk_level(final_score),
                "reason": "Web3 지갑/트랜잭션 서명 요구 → 명백한 암호화폐 스캠",
                "filter_applied": True
            }

        # 채권 추심 체크
        if self.detect_debt_collection(text):
            # 채권 추심은 정상으로 격하 (최대 30점)
            final_score = min(30, llm_score)
            return {
                "final_score": final_score,
                "risk_level": self._get_risk_level(final_score),
                "reason": "실제 채무 관계 추심으로 판단 (공공기관 사칭 없음, 불법 추심일 수 있으나 피싱 아님)",
                "filter_applied": True
            }

        # 내부 업무 지시 체크 (CEO Fraud 경계 케이스)
        if self.detect_internal_instruction(text) and 70 <= llm_score <= 95:
            # 내부 업무 지시는 중간 위험도로 조정 (50점)
            final_score = 50
            return {
                "final_score": final_score,
                "risk_level": self._get_risk_level(final_score),
                "reason": "내부 조직 업무 지시 패턴 감지 (CEO Fraud 가능성 있으나 정상 업무일 수도 있음, 중간 위험도)",
                "filter_applied": True
            }

        # 중고거래 사기 체크
        if self.detect_commerce_fraud(text):
            # 중고거래 사기는 중간 위험도로 조정 (50점)
            final_score = 50
            return {
                "final_score": final_score,
                "risk_level": self._get_risk_level(final_score),
                "reason": "중고거래 사기 패턴 감지 (전화 사기지만 보이스피싱은 아님, 중간 위험도)",
                "filter_applied": True
            }

        # 텍스트를 소문자로 변환 (대소문자 무시)
        text_lower = text.lower()
        reasoning_lower = llm_reasoning.lower()

        # 키워드 카운팅 및 탐지된 키워드 목록 수집
        detected_crime = [kw for kw in self.CRIME_KEYWORDS if kw in text_lower]
        detected_legit = [kw for kw in self.LEGIT_KEYWORDS if kw in text_lower]
        detected_urgency = [kw for kw in self.URGENCY_KEYWORDS if kw in text_lower]

        crime_count = len(detected_crime)
        legit_count = len(detected_legit)
        urgency_count = len(detected_urgency)

        # URL 패턴 체크
        has_fake_url = any(pattern in text_lower for pattern in self.FAKE_URL_PATTERNS)
        has_official_domain = any(domain in text_lower for domain in self.OFFICIAL_DOMAINS)

        # 원격 제어 관련 판정인지 확인 (텍스트 + reasoning 모두 체크)
        remote_keywords = ["원격", "remote", "제어", "control", "앱", "설치", "접속", "화면"]
        is_remote_concern = any(
            keyword in text_lower for keyword in remote_keywords
        ) or any(
            keyword in reasoning_lower for keyword in remote_keywords
        )

        # === Rule 1: 원격 제어 의심 + 정상 서비스 패턴 ===
        # LLM이 60-95점 사이로 판정 + 원격 제어 언급
        if 60 <= llm_score <= 95 and is_remote_concern:
            # 가짜 URL이 없고, 범죄 키워드 적고, 정상 키워드 있고, 긴급성 없으면 정상 서비스로 격하
            if not has_fake_url and crime_count <= 1 and legit_count >= 1 and urgency_count == 0:
                self.stats["downgraded"] += 1
                # 공식 도메인이 있으면 더 확실한 신호
                if has_official_domain:
                    reason = "공식 도메인(.go.kr 등)을 사용하는 정상 서비스로 판단됨"
                else:
                    reason = "원격 지원 요청이지만 정상 서비스로 판단됨 (예약된 일정, 공식 채널)"
                logger.info(
                    f"Rule Filter: 정상 서비스로 격하 "
                    f"(범죄:{crime_count}, 정상:{legit_count}, 긴급:{urgency_count})"
                )
                return {
                    "final_score": 25,  # 안전 구간으로 격하
                    "risk_level": "낮은 주의",
                    "reason": reason,
                    "filter_applied": True,
                    "original_score": llm_score,
                    "keyword_analysis": {
                        "crime": crime_count,
                        "legit": legit_count,
                        "urgency": urgency_count
                    },
                    "detected_techniques": detected_crime[:10]
                }

        # === Rule 2: 낮은 점수 + 고위험 키워드 많음 ===
        # LLM이 낮게 판정했지만 범죄 키워드가 5개 이상
        if llm_score < 60 and crime_count >= 5:
            self.stats["upgraded"] += 1
            logger.warning(
                f"Rule Filter: 위험도 상향 "
                f"(원점수:{llm_score}, 범죄키워드:{crime_count})"
            )
            return {
                "final_score": 70,  # 경고 구간으로 상향
                "risk_level": "중위험",
                "reason": "LLM 점수는 낮지만 다수의 피싱 키워드 감지됨",
                "filter_applied": True,
                "detected_techniques": detected_crime[:10],
                "original_score": llm_score,
                "keyword_analysis": {
                    "crime": crime_count,
                    "legit": legit_count,
                    "urgency": urgency_count
                }
            }

        # === Rule 3: 긴급성 + 금융 조합 (전형적 피싱) ===
        # 긴급성 키워드 + 범죄 키워드가 많으면 높은 위험
        # 단, 정상 키워드가 많으면 (부동산, 법률 거래 등) 상향하지 않음
        if urgency_count >= 2 and crime_count >= 3 and legit_count <= 2:
            if llm_score < 80:
                self.stats["upgraded"] += 1
                logger.warning(
                    f"Rule Filter: 긴급성+금융 패턴 감지 "
                    f"(긴급:{urgency_count}, 범죄:{crime_count}, 정상:{legit_count})"
                )
                return {
                    "final_score": 85,
                    "risk_level": "고위험",
                    "reason": "긴급성 압박 + 금융/수사 키워드 조합 (전형적 피싱 패턴)",
                    "filter_applied": True,
                    "original_score": llm_score,
                    "keyword_analysis": {
                        "crime": crime_count,
                        "legit": legit_count,
                        "urgency": urgency_count
                    },
                    "detected_techniques": detected_crime[:10]
                }

        # === Rule 4: 2차 LLM 검증 (애매한 케이스) ===
        # 60-95 점수대 + 2차 LLM 사용 가능하면 재검증
        if 60 <= llm_score <= 95 and self.second_stage_llm:
            second_check = self._second_stage_verification(text, llm_score, llm_reasoning)
            if second_check["is_safe"]:
                self.stats["downgraded"] += 1
                self.stats["second_stage_downgrades"] += 1
                logger.info(
                    f"Rule Filter: 2차 LLM 검증 완료 - 정상 판정 "
                    f"(원점수:{llm_score}, 2차판정:{second_check['reasoning']})"
                )
                return {
                    "final_score": 20,
                    "risk_level": "안전",
                    "reason": f"2차 LLM 검증: {second_check['reasoning']}",
                    "filter_applied": True,
                    "original_score": llm_score,
                    "second_stage_result": second_check,
                    "keyword_analysis": {
                        "crime": crime_count,
                        "legit": legit_count,
                        "urgency": urgency_count
                    },
                    "detected_techniques": []
                }

        # === Rule 통과: 원래 LLM 판정 유지 ===
        self.stats["passed"] += 1
        return {
            "final_score": llm_score,
            "risk_level": "original",
            "reason": "Rule filter passed - LLM 판정 유지",
            "filter_applied": False,
            "original_score": llm_score,
            "keyword_analysis": {
                "crime": crime_count,
                "legit": legit_count,
                "urgency": urgency_count
            },
            "detected_techniques": detected_crime[:10]  # 최대 10개만 반환
        }

    def _second_stage_verification(
        self,
        text: str,
        first_score: float,
        first_reasoning: str
    ) -> Dict:
        """
        2차 LLM 검증: 애매한 케이스를 재분석

        Args:
            text: 통화 내용
            first_score: 1차 LLM 점수
            first_reasoning: 1차 LLM 판단 이유

        Returns:
            {
                "is_safe": bool,  # True면 정상, False면 위험 유지
                "reasoning": str   # 2차 판정 이유
            }
        """
        self.stats["second_stage_checks"] += 1

        if not self.second_stage_llm:
            return {"is_safe": False, "reasoning": "2nd stage LLM not available"}

        # 2차 검증용 프롬프트 (Chain-of-Thought + 함정 패턴 탐지)
        # 주의: analyze_phishing()이 자동으로 "통화 내용: {text}" 추가하므로 여기선 제외
        verification_prompt = f"""당신은 보이스피싱 2차 검증 전문가입니다.

**배경**:
- 1차 AI 판정: {first_score}점 (피싱 의심)
- 1차 판정 이유: {first_reasoning}

**재검증 임무**: 3단계 체계적 분석을 수행하세요.

---

## 📋 Step 1: 예외 상황 매칭

다음 3가지 **예외 상황** 중 하나에 해당하는지 확인:

### ✅ 예외 1: 사용자가 돈을 받는 상황
**정상 신호**:
- "송금해드릴게요", "입금해드릴", "지급", "환급", "보상금"
- 개인정보(주민번호, 계좌) 요구 → 세금/송금 처리용이므로 정상
- **예시**: 보험금 지급 + 주민번호 요구 (세금 처리) ✅

**❌ 함정 패턴 (피싱)**:
- "환불/환급" **+ 앱 설치/원격제어/URL 접속 요구**
- **예시**: "쿠팡 환불해드릴게요 + 팀뷰어 설치" → 피싱 ❌
- **예시**: "사기 피해금 찾았습니다 + cyber-police.me 접속" → 피싱 ❌
- **이유**: 정상 환급은 **계좌번호만** 요구, 앱/URL/원격제어 **불필요**

### ✅ 예외 2: 사용자가 항의/협박하는 상황
**정상 신호**:
- "환불해", "환불하세요", "신고하겠", "고소하겠", "책임져", "소비자원"
- 사용자가 **피해자가 아닌 항의자** 역할
- **예시**: "500% 수익 난다며! 당장 환불해줘" ✅

### ✅ 예외 3: 소액(10만원 이하) 긴급 요청
**정상 신호**:
- "10만원", "5만원", "차비", "급해" + 가족/지인
- 소액 급전은 정상 가능성 높음 (친구 계좌여도 정상)
- **예시**: "엄마 지갑 잃어버렸어 10만원만" ✅

---

## 🔍 Step 2: 함정 패턴 체크

예외 1에 해당하더라도 다음 **피싱 신호**가 있으면 피싱:
- ⚠️ 앱 설치 요구 (팀뷰어, 원격, APK, 보안관 등)
- ⚠️ URL 접속 요구 (.com, .net, bit.ly, 단축 URL)
- ⚠️ 원격 제어 요구 (접속번호, 화면 공유, 제어 권한)
- ⚠️ 가짜 공공기관 사칭 (URL이 .go.kr 아님)

---

## ✅ Step 3: 최종 판단

**답변 형식 (JSON)**:
{{
  "step1_exception_match": "예외 1/2/3 중 해당하는가? (예외번호 또는 '해당없음')",
  "step2_trap_detected": "함정 패턴 발견? (앱/URL/원격제어 요구 여부: yes/no)",
  "step3_final_decision": "정상 또는 피싱",
  "score": 0-100,
  "is_phishing": true 또는 false,
  "reasoning": "Step 1~3 종합 판단 결과 (2-3문장)"
}}

**핵심 로직**:
- 예외 해당 ✅ + 함정 없음 ✅ → 정상 (score: 0-30, is_phishing: false)
- 예외 해당 ✅ + 함정 있음 ❌ → **피싱** (score: {first_score}, is_phishing: true)
- 예외 해당 없음 ❌ → 피싱 (score: {first_score}, is_phishing: true)"""

        try:
            # Gemini Flash로 빠르게 2차 검증
            result = self.second_stage_llm.analyze_phishing(text, verification_prompt)

            # Gemini 응답: {"score": int, "is_phishing": bool, "reasoning": str}
            is_phishing = result.get("is_phishing", True)  # 기본값: 위험
            second_score = result.get("score", first_score)
            reasoning_text = result.get("reasoning", "2차 검증 완료")

            # is_phishing: false면 안전 (is_safe: true)
            is_safe = not is_phishing

            # 추가 검증: score가 낮으면 (0-30) 안전으로 판단
            if second_score <= 30:
                is_safe = True

            return {
                "is_safe": is_safe,
                "reasoning": reasoning_text,
                "second_score": second_score
            }

        except Exception as e:
            logger.error(f"2nd stage verification failed: {e}")
            return {"is_safe": False, "reasoning": f"Error: {str(e)}"}

    def get_statistics(self) -> Dict:
        """필터 통계 반환"""
        return {
            **self.stats,
            "downgrade_rate": (
                self.stats["downgraded"] / self.stats["total_filtered"] * 100
                if self.stats["total_filtered"] > 0 else 0
            ),
            "upgrade_rate": (
                self.stats["upgraded"] / self.stats["total_filtered"] * 100
                if self.stats["total_filtered"] > 0 else 0
            )
        }

    def reset_statistics(self):
        """통계 초기화"""
        self.stats = {
            "total_filtered": 0,
            "downgraded": 0,
            "upgraded": 0,
            "passed": 0,
            "second_stage_checks": 0,
            "second_stage_downgrades": 0
        }
