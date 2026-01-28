#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
금감원 데이터로 피싱 탐지 API 테스트
"""
import requests
import json

API_URL = "http://localhost:8000/api/analyze/text"

test_cases = [
    {
        "name": "시나리오 1: 검찰 사칭 + 협박 + 송금 요구",
        "text": "안녕하세요, 서울중앙지검 김철수 검사입니다. 당신 명의의 계좌가 보이스피싱 범죄에 사용되었습니다. 지금 바로 확인하지 않으면 내일 체포영장이 발부됩니다. 주민등록번호와 계좌번호를 말씀해주세요."
    },
    {
        "name": "시나리오 2: 금융감독원 사칭 + 개인정보 요구",
        "text": "금융감독원입니다. 고객님 계좌에서 이상거래가 감지되었습니다. 즉시 안전계좌로 자금을 이체하셔야 피해를 막을 수 있습니다. 카드번호 1234-5678-9012-3456과 OTP 번호를 알려주세요."
    },
    {
        "name": "시나리오 3: 정상 통화",
        "text": "안녕하세요. 택배 배송 관련하여 연락드렸습니다. 오늘 오후 2시경 방문 예정인데 댁에 계실까요?"
    },
    {
        "name": "실제 금감원 데이터 유사 - 명의도용",
        "text": "다른 게 아니라 본인이 연루된 명의도용 사건이 지금 검찰청 확인되어 있습니다. 명의도용된 휴대폰으로 불법적인 일을 했기 때문에 수사를 진행합니다."
    },
    {
        "name": "실제 금감원 데이터 유사 - 대출 사기",
        "text": "KB 국민은행 고객관리부입니다. 고객님 최근에 대출 신청하셨나요? 고객님의 신용등급으로 3000만원까지 대출 가능합니다. 승인을 위해 계좌번호 확인이 필요합니다."
    }
]

print("=" * 70)
print("Sentinel-Voice: 피싱 탐지 API 테스트 (금감원 데이터 통합)")
print("=" * 70)

for i, test_case in enumerate(test_cases, 1):
    print(f"\n[테스트 {i}/{len(test_cases)}] {test_case['name']}")
    print("-" * 70)
    print(f"입력 텍스트: {test_case['text'][:80]}...")

    try:
        response = requests.post(
            API_URL,
            json={"text": test_case["text"], "enable_pii_masking": True},
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()

            print(f"\n📊 분석 결과:")
            print(f"  위험도: {result['risk_score']}/100 ({result['risk_level']})")
            print(f"  피싱 여부: {'⚠️ 예' if result['is_phishing'] else '✅ 아니오'}")
            print(f"  경고 메시지: {result['alert_message']}")

            print(f"\n  세부 점수:")
            print(f"    - 키워드: {result['component_scores']['keyword']:.1f}")
            print(f"    - 감정: {result['component_scores']['sentiment']:.1f}")
            print(f"    - 유사도: {result['component_scores']['similarity']:.1f}")

            if result['techniques_detected']:
                print(f"\n  탐지된 기법: {', '.join(result['techniques_detected'])}")

            if result.get('masked_text'):
                print(f"\n  마스킹된 텍스트: {result['masked_text'][:100]}...")
        else:
            print(f"❌ 오류: HTTP {response.status_code}")
            print(f"   {response.text}")

    except Exception as e:
        print(f"❌ 예외 발생: {e}")

print("\n" + "=" * 70)
print("테스트 완료!")
print("=" * 70)
