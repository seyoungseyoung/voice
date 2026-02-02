"""
5개 오답 케이스 스몰 벤치마크
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

# 5개 오답 케이스
test_cases = [
    {
        "id": "E05",
        "name": "[피싱] 로맨스스캠 초기",
        "text": "어? 이거 김민준 전무님 번호 아닌가요? 골프 모임에서 뵀던... 아이고, 제가 번호를 잘못 저장했나 보네요. 죄송합니다. 목소리가 너무 점잖으셔서 실례인 줄 모르고... 저는 무역 사업 하는 '이수진'이라고 합니다. 이것도 인연인데 혹시 카톡 친구 해도 될까요? 제가 죄송해서 커피 기프티콘이라도 하나 보내드리고 싶어서요.",
        "expected_min": 65,
        "expected_max": 100,
        "type": "phishing"
    },
    {
        "id": "E07",
        "name": "[정상] 보험금 지급",
        "text": "여보세요, 정세영 고객님? 삼성화재 대물보상 담당자입니다. 아까 접수된 접촉 사고 건 때문에 전화드렸어요. 과실 비율 100:0 확정되셨고요. 미수선 수리비로 현금 처리 받으시는 게 유리하실 것 같아서요. 합의금 120만 원 책정되셨는데, 동의하시면 지금 불러주시는 계좌로 바로 송금해드릴게요. 세금 처리 때문에 주민번호 뒷자리도 알려주셔야 합니다.",
        "expected_min": 0,
        "expected_max": 30,
        "type": "legitimate"
    },
    {
        "id": "E11",
        "name": "[정상] 가족 급전 요청",
        "text": "엄마! 나 지금 큰일 났어. 나 지금 홍대인데 지갑을 잃어버렸어. 집에 갈 차비도 없고 카드도 다 정지시켜서 아무것도 못 해. 어, 폰은 있는데 배터리 3%야. 끊어지면 안 돼. 엄마, 나 지금 친구 계좌로 10만 원만 빨리 보내줘. 내가 집 가서 바로 줄게. 급해 진짜. 어, '박민수'고 카카오뱅크야. 내가 문자로 찍어보낼게. 지금 당장 좀 넣어줘. 나 택시 타야 돼.",
        "expected_min": 0,
        "expected_max": 30,
        "type": "legitimate"
    },
    {
        "id": "F02",
        "name": "[경고] CEO Fraud/BEC",
        "text": "김 대리, 나 지금 미팅 들어왔는데 거래처에서 입금 확인이 안 된다고 난리네? 지금 내가 OTP를 안 가져와서 그런데, 일단 법인 계좌에서 500만 원만 지금 바로 저쪽 대표님 개인 계좌로 쏴줘요. 내가 카톡으로 계좌 남길게. 나 지금 급하니까 결재 나중에 올리고 처리부터 해.",
        "expected_min": 70,
        "expected_max": 100,
        "type": "phishing"
    },
    {
        "id": "F03",
        "name": "[주의] 중고거래 사기",
        "text": "아, 안전결제는 정산이 너무 늦어서요. 제가 직거래는 지방이라 힘들고, 그냥 쿨거래 하시면 택포 5만 원에 드릴게요. 제 더치트 조회해보시면 깨끗해요. 지금 바로 입금 가능하세요? 다른 분도 연락 와서요.",
        "expected_min": 40,
        "expected_max": 60,
        "type": "caution"
    }
]

def main():
    print("\n" + "="*80)
    print("🔬 5개 오답 케이스 스몰 벤치마크 (Filter 개선 후)")
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
        if test_case['type'] == 'phishing':
            print(f"기대: {test_case['expected_min']}-{test_case['expected_max']}점 (피싱)")
        else:
            print(f"기대: {test_case['expected_min']}-{test_case['expected_max']}점 (정상)")

        try:
            result = detector.analyze(test_case["text"], enable_filter=True)

            llm_score = result.get("llm_score", 0)
            final_score = result.get("score", 0)
            filter_applied = result.get("filter_applied", False)
            reasoning = result.get("reasoning", "")

            # 결과 판정
            if test_case["type"] == "phishing":
                is_correct = test_case['expected_min'] <= final_score <= test_case['expected_max']
            else:
                is_correct = test_case['expected_min'] <= final_score <= test_case['expected_max']

            status = "✅ 성공" if is_correct else "❌ 실패"

            print(f"결과: LLM {llm_score}점 → 최종 {final_score}점 {status}")
            if filter_applied:
                print(f"필터: {reasoning[:80]}...")
            print()

            results.append({
                "id": test_case["id"],
                "name": test_case["name"],
                "expected": f"{test_case['expected_min']}-{test_case['expected_max']}",
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
                "expected": f"{test_case['expected_min']}-{test_case['expected_max']}",
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
        print(f"   기대: {r['expected']}점")
        print(f"   결과: LLM {r['llm_score']}점 → 최종 {r['final_score']}점")
        print()

    if correct_count == total_count:
        print("🎉 모든 케이스 통과!")
    else:
        print(f"⚠️ {total_count - correct_count}개 케이스 여전히 오답")
        print("\n남은 오답:")
        for r in results:
            if not r["is_correct"]:
                print(f"  - [{r['id']}] {r['name']}: {r['final_score']}점")

if __name__ == "__main__":
    main()
