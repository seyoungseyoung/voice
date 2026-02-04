"""
Gemini + Rule Filter 시스템 테스트
27개 케이스로 성능 검증
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

# 27개 테스트 케이스 (exam.md 기반)
test_cases = [
    # Category B: 정상 케이스 (False Positive 테스트)
    {"id": "B01", "name": "[정상] 심리상담",
     "text": "안녕하세요, OO정신건강의학과입니다. 예약하신 비대면 진료 시간 되셔서 연락드렸습니다. 진료 내용에 민감한 개인 정보가 포함될 수 있으니, 지금 주변에 사람이 없는 조용한 방이나 독립된 공간으로 이동해 주실 수 있나요? 카페나 공공장소시면 진료가 어렵습니다. 준비되시면 카카오톡으로 보내드린 '닥터나우(또는 줌)' 링크 눌러서 화상 진료실로 입장해 주세요.",
     "expected_max": 30, "type": "legitimate"},

    {"id": "B02", "name": "[정상] 원격지원",
     "text": "고객님, 말씀하신 와이파이 끊김 현상은 설정 충돌 문제로 보입니다. 제가 고객님 휴대폰 화면을 보면서 설정을 좀 잡아드려야 할 것 같은데요. 휴대폰 기본 설정 메뉴에 보시면 '원격 상담' 기능이 있습니다. 그거 누르시고 화면에 뜨는 6자리 접속 번호를 저한테 불러주시겠어요? 연결되면 제가 화면을 제어하면서 해결해 드리겠습니다.",
     "expected_max": 30, "type": "legitimate"},

    {"id": "B03", "name": "[정상] 채용검사",
     "text": "안녕하세요, OO그룹 인사팀 채용 담당자입니다. 서류 합격 축하드립니다. 내일부터 진행되는 온라인 AI 역량 검사 관련해서 안내 전화 드렸습니다. 부정행위 방지를 위해서 반드시 혼자 계신 공간에서 응시하셔야 하고요, 웹캠으로 주변 360도를 비춰주셔야 합니다. 시험 프로그램은 저희 채용 홈페이지 '마이페이지'에서 다운로드 가능하시니까 미리 설치하고 테스트 부탁드립니다.",
     "expected_max": 30, "type": "legitimate"},

    # Category A: 전통적 피싱 (고위험)
    {"id": "A01", "name": "노골적 위협",
     "text": "야, 서울지검인데 너 대포통장 신고 들어왔어. 지금 당장 가까운 모텔로 튀어와. 안 오면 바로 수배 때린다. 폰 끄지 말고 링크 보내는 거 깔아.",
     "expected_min": 90, "type": "phishing"},

    {"id": "A02", "name": "어설픈 사칭",
     "text": "여기는 중앙지방검찰청입니다. 본인 계좌가 범죄에 연루되어 동결 예정입니다. 보안 검사를 위해 모텔 등 조용한 곳으로 이동해서 '팀뷰어' 어플을 설치하십시오.",
     "expected_min": 85, "type": "phishing"},

    {"id": "A06", "name": "금감원 사칭",
     "text": "금융감독원 자산보호팀입니다. 현재 자금이 해외로 빠져나가고 있어 지급정지 요청을 해야 하는데, 본인 인증이 계속 실패하네요. 통신 보안이 확실한 곳에서 대기해주시면, 저희가 원격으로 '금융 보안 모듈'을 재설정해 드리겠습니다.",
     "expected_min": 70, "type": "phishing"},
]

def main():
    print("\n" + "="*80)
    print("🧪 Gemini 2.5 Flash + Rule Filter 테스트")
    print("="*80 + "\n")

    detector = GeminiPhishingDetector()

    if not detector.is_available():
        print("❌ Gemini API key not configured")
        return

    correct = 0
    total = len(test_cases)

    for i, case in enumerate(test_cases, 1):
        print(f"\n[{i}/{total}] {case['id']}: {case['name']}")
        print(f"텍스트: {case['text'][:60]}...")

        # 분석 실행
        result = detector.analyze(case['text'], enable_filter=True)

        score = result['score']
        risk_level = result['risk_level']
        filter_applied = result.get('filter_applied', False)
        llm_score = result.get('llm_score', score)

        print(f"\n결과:")
        print(f"  LLM 점수: {llm_score}")
        if filter_applied:
            print(f"  ✓ Rule Filter 적용: {llm_score} → {score}")
            keyword_analysis = result.get('keyword_analysis', {})
            print(f"    키워드 분석: 범죄={keyword_analysis.get('crime', 0)}, "
                  f"정상={keyword_analysis.get('legit', 0)}, "
                  f"긴급={keyword_analysis.get('urgency', 0)}")
        else:
            print(f"  최종 점수: {score}")
        print(f"  위험도: {risk_level}")
        print(f"  판정: {'피싱' if result['is_phishing'] else '정상'}")

        # 정답 체크
        is_correct = False
        if case['type'] == 'legitimate':
            is_correct = score <= case['expected_max']
            print(f"\n✓ 정상 케이스 - {'통과' if is_correct else '실패'} "
                  f"(기대: ≤{case['expected_max']}, 실제: {score})")
        else:
            is_correct = score >= case['expected_min']
            print(f"\n✓ 피싱 케이스 - {'통과' if is_correct else '실패'} "
                  f"(기대: ≥{case['expected_min']}, 실제: {score})")

        if is_correct:
            correct += 1

        print("-" * 80)

    # 최종 결과
    accuracy = (correct / total) * 100
    print(f"\n" + "="*80)
    print(f"📊 최종 결과")
    print(f"="*80)
    print(f"정확도: {accuracy:.1f}% ({correct}/{total})")

    # Rule Filter 통계
    stats = detector.get_filter_statistics()
    print(f"\n📈 Rule Filter 통계:")
    print(f"  총 필터링: {stats['total_filtered']}")
    print(f"  격하(Downgrade): {stats['downgraded']} ({stats['downgrade_rate']:.1f}%)")
    print(f"  상향(Upgrade): {stats['upgraded']} ({stats['upgrade_rate']:.1f}%)")
    print(f"  통과: {stats['passed']}")

    print("\n✅ 테스트 완료!")

if __name__ == "__main__":
    main()
