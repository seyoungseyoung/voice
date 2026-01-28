"""
Risk Scoring Algorithm for Voice Phishing Detection
Combines: Keyword Score + Sentiment Score + Similarity Score
"""
from typing import Dict, List, Tuple, Optional
import numpy as np
from collections import Counter
import logging

from src.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskScorer:
    """
    Multi-factor risk scoring for phishing detection

    Scoring Formula:
    Risk Score = (Keyword Score * 0.3) + (Sentiment Score * 0.3) + (Similarity Score * 0.4)
    """

    def __init__(
        self,
        keyword_weight: float = None,
        sentiment_weight: float = None,
        similarity_weight: float = None,
        threshold: int = None
    ):
        """
        Args:
            keyword_weight: Weight for keyword-based score (default from config)
            sentiment_weight: Weight for sentiment score (default from config)
            similarity_weight: Weight for similarity score (default from config)
            threshold: Risk threshold for alerts (default from config)
        """
        self.keyword_weight = keyword_weight or config.risk_scoring.keyword_weight
        self.sentiment_weight = sentiment_weight or config.risk_scoring.sentiment_weight
        self.similarity_weight = similarity_weight or config.risk_scoring.similarity_weight
        self.threshold = threshold or config.risk_scoring.risk_threshold

        # Normalize weights to sum to 1.0
        total = self.keyword_weight + self.sentiment_weight + self.similarity_weight
        self.keyword_weight /= total
        self.sentiment_weight /= total
        self.similarity_weight /= total

        logger.info(
            f"RiskScorer initialized: "
            f"keyword={self.keyword_weight:.2f}, "
            f"sentiment={self.sentiment_weight:.2f}, "
            f"similarity={self.similarity_weight:.2f}, "
            f"threshold={self.threshold}"
        )

        # Define phishing keyword categories with severity weights
        self.keyword_categories = {
            "기관사칭": {
                "keywords": ["검찰", "경찰", "금융감독원", "금감원", "국세청", "법원", "법무부"],
                "severity": 8
            },
            "협박": {
                "keywords": ["체포", "구속", "압류", "영장", "범죄", "처벌", "고소", "고발"],
                "severity": 9
            },
            "개인정보": {
                "keywords": ["주민번호", "계좌번호", "비밀번호", "카드번호", "인증번호", "OTP", "보안카드"],
                "severity": 10
            },
            "금전요구": {
                "keywords": ["송금", "이체", "입금", "안전계좌", "보호예수", "출금"],
                "severity": 10
            },
            "긴급성": {
                "keywords": ["즉시", "지금", "바로", "당장", "긴급", "시급"],
                "severity": 6
            }
        }

        # Sentiment keywords
        self.fear_keywords = ["위험", "피해", "손해", "문제", "심각", "걱정", "체포", "구속", "압류", "영장", "범죄", "처벌", "고소", "고발"]
        self.urgency_keywords = ["빨리", "서둘러", "늦으면", "마감", "기한", "즉시", "지금", "바로", "당장", "긴급", "시급"]

    def calculate_keyword_score(self, text: str) -> Tuple[float, Dict]:
        """
        Calculate keyword-based score

        Args:
            text: Input text

        Returns:
            Tuple of (score, metadata)
            score: 0-100
            metadata: Details about matched keywords
        """
        total_score = 0
        matches = {}
        matched_keywords = []

        for category, data in self.keyword_categories.items():
            keywords = data["keywords"]
            severity = data["severity"]
            category_matches = [kw for kw in keywords if kw in text]

            if category_matches:
                # Score increases with number of matches and severity
                category_score = len(category_matches) * severity
                total_score += category_score
                matches[category] = {
                    "keywords": category_matches,
                    "count": len(category_matches),
                    "score": category_score
                }
                matched_keywords.extend(category_matches)

        # Normalize to 0-100 scale
        # Max possible score estimate: ~50 (assuming multiple high-severity matches)
        normalized_score = min((total_score / 50) * 100, 100)

        metadata = {
            "raw_score": total_score,
            "normalized_score": normalized_score,
            "matches": matches,
            "total_keywords_matched": len(matched_keywords)
        }

        logger.debug(f"Keyword score: {normalized_score:.2f} ({len(matched_keywords)} keywords matched)")

        return normalized_score, metadata

    def calculate_sentiment_score(self, text: str) -> Tuple[float, Dict]:
        """
        Calculate sentiment-based score (fear, urgency)

        Args:
            text: Input text

        Returns:
            Tuple of (score, metadata)
        """
        fear_count = sum(1 for kw in self.fear_keywords if kw in text)
        urgency_count = sum(1 for kw in self.urgency_keywords if kw in text)

        # Combined sentiment score
        fear_score = min(fear_count * 15, 50)  # Max 50 from fear
        urgency_score = min(urgency_count * 12, 50)  # Max 50 from urgency

        total_score = min(fear_score + urgency_score, 100)

        metadata = {
            "fear_keywords_matched": fear_count,
            "urgency_keywords_matched": urgency_count,
            "fear_score": fear_score,
            "urgency_score": urgency_score,
            "total_score": total_score
        }

        logger.debug(f"Sentiment score: {total_score:.2f} (fear={fear_count}, urgency={urgency_count})")

        return total_score, metadata

    def calculate_similarity_score(
        self,
        similar_cases: List[Tuple[str, float, Dict]]
    ) -> Tuple[float, Dict]:
        """
        Calculate similarity-based score from vector search results

        Args:
            similar_cases: List of (script, similarity_score, metadata) from vector search

        Returns:
            Tuple of (score, metadata)
        """
        if not similar_cases:
            return 0.0, {"similar_cases_count": 0}

        # Use max similarity score and average of top 3
        similarity_scores = [score for _, score, _ in similar_cases]

        max_similarity = max(similarity_scores)
        avg_top3 = np.mean(similarity_scores[:3]) if len(similarity_scores) >= 3 else np.mean(similarity_scores)

        # Weighted combination: 70% max, 30% average
        combined_score = (max_similarity * 0.7 + avg_top3 * 0.3) * 100

        metadata = {
            "similar_cases_count": len(similar_cases),
            "max_similarity": float(max_similarity),
            "avg_similarity": float(avg_top3),
            "combined_score": combined_score
        }

        logger.debug(f"Similarity score: {combined_score:.2f} (max={max_similarity:.4f})")

        return combined_score, metadata

    def calculate_risk_score(
        self,
        text: str,
        similar_cases: Optional[List[Tuple[str, float, Dict]]] = None
    ) -> Dict:
        """
        Calculate overall risk score

        Args:
            text: Input text
            similar_cases: Optional similar cases from vector search

        Returns:
            Complete risk assessment dictionary
        """
        # Calculate individual scores
        keyword_score, keyword_meta = self.calculate_keyword_score(text)
        sentiment_score, sentiment_meta = self.calculate_sentiment_score(text)
        similarity_score, similarity_meta = self.calculate_similarity_score(similar_cases or [])

        # Weighted combination
        final_score = (
            keyword_score * self.keyword_weight +
            sentiment_score * self.sentiment_weight +
            similarity_score * self.similarity_weight
        )

        # Determine risk level
        if final_score >= 90:
            risk_level = "CRITICAL"
            alert_message = "⚠️ 매우 높은 위험! 즉시 통화를 종료하세요!"
        elif final_score >= 70:
            risk_level = "HIGH"
            alert_message = "⚠️ 보이스피싱 의심! 주의하세요!"
        elif final_score >= 50:
            risk_level = "MEDIUM"
            alert_message = "⚠️ 의심스러운 통화입니다."
        elif final_score >= 30:
            risk_level = "LOW"
            alert_message = "주의가 필요할 수 있습니다."
        else:
            risk_level = "SAFE"
            alert_message = "정상 통화로 판단됩니다."

        result = {
            "risk_score": round(final_score, 2),
            "risk_level": risk_level,
            "is_phishing": final_score >= self.threshold,
            "alert_message": alert_message,
            "component_scores": {
                "keyword": round(keyword_score, 2),
                "sentiment": round(sentiment_score, 2),
                "similarity": round(similarity_score, 2)
            },
            "weights": {
                "keyword": round(self.keyword_weight, 2),
                "sentiment": round(self.sentiment_weight, 2),
                "similarity": round(self.similarity_weight, 2)
            },
            "metadata": {
                "keyword": keyword_meta,
                "sentiment": sentiment_meta,
                "similarity": similarity_meta
            }
        }

        logger.info(
            f"Risk assessment complete: {final_score:.2f}/100 ({risk_level}) - "
            f"Keyword: {keyword_score:.1f}, Sentiment: {sentiment_score:.1f}, "
            f"Similarity: {similarity_score:.1f}"
        )

        return result


def main():
    """Example usage"""
    print("=" * 60)
    print("Sentinel-Voice: Risk Scoring System")
    print("=" * 60)

    scorer = RiskScorer()

    # Test cases
    test_cases = [
        {
            "name": "검찰 사칭 + 협박 + 송금 요구",
            "text": "검찰청입니다. 당신은 금융범죄에 연루되어 곧 체포됩니다. 즉시 안전계좌로 송금하세요.",
            "similar_cases": [("검찰청 사칭 피싱", 0.85, {}), ("금융범죄 사칭", 0.72, {})]
        },
        {
            "name": "개인정보 요구",
            "text": "은행입니다. 보안을 위해 계좌번호와 비밀번호를 확인해주세요.",
            "similar_cases": [("은행 사칭", 0.65, {})]
        },
        {
            "name": "정상 통화",
            "text": "안녕하세요. 배송이 지연되어 죄송합니다. 내일 도착 예정입니다.",
            "similar_cases": []
        }
    ]

    for test in test_cases:
        print(f"\n{'='*60}")
        print(f"테스트: {test['name']}")
        print(f"{'='*60}")
        print(f"텍스트: {test['text']}")

        result = scorer.calculate_risk_score(test['text'], test.get('similar_cases'))

        print(f"\n위험도: {result['risk_score']}/100 ({result['risk_level']})")
        print(f"피싱 여부: {'예' if result['is_phishing'] else '아니오'}")
        print(f"메시지: {result['alert_message']}")
        print(f"\n구성 점수:")
        print(f"  - Keyword: {result['component_scores']['keyword']:.2f}")
        print(f"  - Sentiment: {result['component_scores']['sentiment']:.2f}")
        print(f"  - Similarity: {result['component_scores']['similarity']:.2f}")


if __name__ == "__main__":
    main()
