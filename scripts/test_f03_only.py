"""
F03 중고거래 케이스 단독 테스트
"""
import sys
import os
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from src.llm.gemini_detector import GeminiPhishingDetector

def main():
    print("\n" + "="*80)
    print("🔬 F03 중고거래 사기 케이스 테스트")
    print("="*80 + "\n")

    text = "아, 안전결제는 정산이 너무 늦어서요. 제가 직거래는 지방이라 힘들고, 그냥 쿨거래 하시면 택포 5만 원에 드릴게요. 제 더치트 조회해보시면 깨끗해요. 지금 바로 입금 가능하세요? 다른 분도 연락 와서요."

    detector = GeminiPhishingDetector()

    if not detector.is_available():
        print("❌ Gemini API를 사용할 수 없습니다.")
        return

    print("✅ Gemini Phishing Detector 초기화 완료\n")
    print(f"테스트 텍스트: {text}\n")

    # 중고거래 키워드 체크
    from src.filters.rule_filter import RuleBasedFilter
    filter_obj = RuleBasedFilter()

    print("🔍 키워드 매칭 체크:")
    for keyword in filter_obj.COMMERCE_FRAUD_KEYWORDS:
        if keyword in text.lower():
            print(f"  ✅ '{keyword}' 발견")

    is_commerce = filter_obj.detect_commerce_fraud(text)
    print(f"\n중고거래 사기 패턴 감지: {is_commerce}\n")

    try:
        result = detector.analyze(text, enable_filter=True)

        llm_score = result.get("llm_score", 0)
        final_score = result.get("score", 0)
        filter_applied = result.get("filter_applied", False)
        reasoning = result.get("reasoning", "")

        print(f"결과:")
        print(f"  LLM 점수: {llm_score}점")
        print(f"  최종 점수: {final_score}점")
        print(f"  필터 적용: {filter_applied}")
        print(f"  필터 이유: {reasoning}")

        # 기대: 0-30점 또는 40-60점
        if final_score <= 30:
            print(f"\n✅ 정상으로 판정 (30점 이하)")
        elif 40 <= final_score <= 60:
            print(f"\n✅ 중간 위험도로 판정 (40-60점, 목표 달성!)")
        else:
            print(f"\n❌ 여전히 높은 점수 ({final_score}점)")

    except Exception as e:
        print(f"❌ 에러: {e}")

if __name__ == "__main__":
    main()
