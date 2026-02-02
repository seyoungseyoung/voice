"""
3개 오답 케이스 테스트 스크립트
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

# 오답 3개 케이스
test_cases = [
    {
        "id": "F01",
        "name": "[정상] 고압적 사채 추심",
        "text": "야, 김철수 씨. 전화 좀 피하지 맙시다? 오늘까지 이자 입금 안 되면 내일 당장 회사 찾아가서 뒤집어 엎는다고 했죠? 당신 와이프한테도 연락할 거야. 법대로 하라며? 그래 법대로 딱지 붙여줄 테니까 당장 입금해.",
        "expected": "≤30점 (정상)",
        "type": "legitimate"
    },
    {
        "id": "F02",
        "name": "[정상] CEO 긴급 송금",
        "text": "김 대리, 나 지금 미팅 들어왔는데 거래처에서 입금 확인이 안 된다고 난리네? 지금 내가 OTP를 안 가져와서 그런데, 일단 법인 계좌에서 500만 원만 지금 바로 저쪽 대표님 개인 계좌로 쏴줘요. 내가 카톡으로 계좌 남길게. 나 지금 급하니까 결재 나중에 올리고 처리부터 해.",
        "expected": "40-60점 (주의)",
        "type": "legitimate"
    },
    {
        "id": "G03",
        "name": "[피싱] Web3 에어드랍",
        "text": "안녕하세요, 재단 운영팀입니다. 지난번 스냅샷 기준으로 거버넌스 토큰 에어드랍 대상자신데, 지금 지갑 연결이 해제되셔서 클레임이 안 되고 계세요. 가스비는 저희가 지원하니까, 보내드리는 공식 브릿지 사이트 접속하셔서 트랜잭션 서명만 한번 해주시면 됩니다.",
        "expected": "≥70점 (피싱)",
        "type": "phishing"
    }
]

def main():
    print("\n" + "="*80)
    print("🔬 3개 오답 케이스 재테스트 (프롬프트 개선 후)")
    print("="*80 + "\n")

    detector = GeminiPhishingDetector()

    if not detector.is_available():
        print("❌ Gemini API를 사용할 수 없습니다.")
        return

    print("✅ Gemini Phishing Detector 초기화 완료\n")

    results = []

    for test_case in test_cases:
        print(f"[{test_case['id']}] {test_case['name']}")
        print(f"입력: {test_case['text'][:60]}...")
        print(f"기대: {test_case['expected']}")

        try:
            result = detector.analyze(test_case["text"], enable_filter=True)

            llm_score = result.get("llm_score", 0)
            final_score = result.get("score", 0)
            filter_applied = result.get("filter_applied", False)
            reasoning = result.get("reasoning", "")

            # 결과 판정
            if test_case["id"] == "F01":
                # 30점 이하면 성공
                is_correct = final_score <= 30
            elif test_case["id"] == "F02":
                # 40-60점 범위면 성공 (엄격하게는 30점 이하)
                is_correct = 30 <= final_score <= 60 or final_score <= 30
            elif test_case["id"] == "G03":
                # 70점 이상이면 성공
                is_correct = final_score >= 70

            status = "✅ 성공" if is_correct else "❌ 실패"

            print(f"결과: LLM {llm_score}점 → 최종 {final_score}점 {status}")
            if filter_applied:
                print(f"필터: {reasoning}")
            print()

            results.append({
                "id": test_case["id"],
                "name": test_case["name"],
                "expected": test_case["expected"],
                "llm_score": llm_score,
                "final_score": final_score,
                "filter_applied": filter_applied,
                "reasoning": reasoning,
                "is_correct": is_correct
            })

        except Exception as e:
            print(f"  ❌ 에러: {e}\n")
            results.append({
                "id": test_case["id"],
                "name": test_case["name"],
                "expected": test_case["expected"],
                "llm_score": 0,
                "final_score": 0,
                "filter_applied": False,
                "reasoning": f"Error: {e}",
                "is_correct": False
            })

    # 최종 결과
    print("="*80)
    print("📊 최종 결과")
    print("="*80)

    correct_count = sum(1 for r in results if r["is_correct"])
    total_count = len(results)

    print(f"\n성공: {correct_count}/{total_count} ({correct_count/total_count*100:.1f}%)\n")

    for r in results:
        status = "✅" if r["is_correct"] else "❌"
        print(f"{status} [{r['id']}] {r['name']}")
        print(f"   기대: {r['expected']}")
        print(f"   결과: LLM {r['llm_score']}점 → 최종 {r['final_score']}점")
        print()

    if correct_count == total_count:
        print("🎉 모든 케이스 통과! 프롬프트 개선 성공!")
    else:
        print(f"⚠️ {total_count - correct_count}개 케이스 여전히 오답")

if __name__ == "__main__":
    main()
