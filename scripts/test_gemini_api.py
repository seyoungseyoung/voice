"""
Gemini + Filter API 엔드포인트 테스트
"""
import requests
import time

# API 엔드포인트
API_URL = "http://localhost:8000/api/analyze/gemini"

# 테스트 케이스
test_cases = [
    {
        "name": "정상 - 심리상담",
        "text": "안녕하세요, OO정신건강의학과입니다. 예약하신 비대면 진료 시간 되셔서 연락드렸습니다.",
        "expected": "정상"
    },
    {
        "name": "정상 - 원격지원",
        "text": "고객님, 말씀하신 와이파이 끊김 현상은 설정 충돌 문제로 보입니다. 제가 고객님 휴대폰 화면을 보면서 설정을 좀 잡아드려야 할 것 같은데요.",
        "expected": "정상 (Rule Filter 적용)"
    },
    {
        "name": "피싱 - 노골적 위협",
        "text": "야, 서울지검인데 너 대포통장 신고 들어왔어. 지금 당장 가까운 모텔로 튀어와. 안 오면 바로 수배 때린다.",
        "expected": "피싱"
    },
    {
        "name": "피싱 - 금감원 사칭",
        "text": "금융감독원 자산보호팀입니다. 현재 자금이 해외로 빠져나가고 있어 지급정지 요청을 해야 하는데, 본인 인증이 계속 실패하네요.",
        "expected": "피싱"
    }
]


def test_api():
    """API 테스트"""
    print("=" * 80)
    print("🧪 Gemini + Filter API 테스트")
    print("=" * 80)
    print()

    for i, case in enumerate(test_cases, 1):
        print(f"[{i}/{len(test_cases)}] {case['name']}")
        print(f"텍스트: {case['text'][:60]}...")
        print(f"기대 결과: {case['expected']}")

        try:
            response = requests.post(
                API_URL,
                json={"text": case["text"], "enable_filter": True},
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                print(f"\n✓ 응답 성공:")
                print(f"  - 점수: {result['score']}")
                print(f"  - 위험도: {result['risk_level']}")
                print(f"  - 판정: {'피싱' if result['is_phishing'] else '정상'}")
                print(f"  - Filter 적용: {result.get('filter_applied', False)}")
                if result.get('filter_applied'):
                    print(f"  - LLM 원점수: {result.get('llm_score')} → {result['score']}")
                print(f"  - 캐시: {result.get('cached', False)}")
            else:
                print(f"\n✗ 오류: HTTP {response.status_code}")
                print(f"  {response.text}")

        except Exception as e:
            print(f"\n✗ 예외 발생: {e}")

        print("-" * 80)
        time.sleep(0.5)

    print()
    print("=" * 80)
    print("🎯 Rate Limiting 테스트 (11번째 요청)")
    print("=" * 80)
    print()

    # Rate limit 테스트 (10/minute이므로 빠르게 11번 요청)
    print("10회 요청 후 11번째 요청 시도...")
    for i in range(11):
        try:
            response = requests.post(
                API_URL,
                json={"text": "테스트 텍스트", "enable_filter": True},
                timeout=5
            )
            if response.status_code == 429:
                print(f"✓ Rate limit 동작: {i+1}번째 요청에서 차단됨")
                break
            elif i == 10:
                print("⚠ Rate limit이 예상대로 동작하지 않음 (11번째 요청 성공)")
        except Exception as e:
            print(f"✗ 오류: {e}")
            break
        time.sleep(0.1)

    print()
    print("=" * 80)
    print("📈 캐시 통계 조회")
    print("=" * 80)
    try:
        response = requests.get("http://localhost:8000/api/cache/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"✓ 캐시 크기: {stats['cache_size']}")
            print(f"  TTL: {stats['ttl_seconds']}초")
        else:
            print(f"✗ 오류: HTTP {response.status_code}")
    except Exception as e:
        print(f"✗ 예외: {e}")

    print()
    print("✅ 테스트 완료!")


if __name__ == "__main__":
    print("서버가 http://localhost:8000에서 실행 중인지 확인하세요.")
    print()
    input("준비되면 Enter를 눌러주세요...")
    test_api()
