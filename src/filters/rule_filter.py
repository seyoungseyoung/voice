"""
Rule-based Filter for reducing False Positives
논리적 필터로 정상 서비스(원격지원, 채용검사 등)를 보호
"""
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


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
        "진료", "상담", "병원", "의사", "환자", "프라이버시"
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

    # 긴급/압박 키워드 (피싱에서 자주 사용)
    URGENCY_KEYWORDS = [
        "지금 당장", "즉시", "급히", "바로", "빨리",
        "안 하면", "하지 않으면", "불이익", "손해",
        "시간 내", "마감", "기한"
    ]

    def __init__(self):
        self.stats = {
            "total_filtered": 0,
            "downgraded": 0,
            "upgraded": 0,
            "passed": 0
        }

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
        if urgency_count >= 2 and crime_count >= 3:
            if llm_score < 80:
                self.stats["upgraded"] += 1
                logger.warning(
                    f"Rule Filter: 긴급성+금융 패턴 감지 "
                    f"(긴급:{urgency_count}, 범죄:{crime_count})"
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
            "passed": 0
        }
