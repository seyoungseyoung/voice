"""
벤치마크 케이스 48개를 점검하고 분류가 애매한 케이스를 식별
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 벤치마크 케이스 import
from generate_benchmark_report import test_cases

def analyze_case(case):
    """케이스 분석 및 문제점 식별"""
    text = case["text"]
    case_type = case["type"]
    case_id = case["id"]
    name = case["name"]

    # 분석 지표
    issues = []

    # 1. 금전 흐름 분석
    money_in_keywords = ["송금해드릴", "입금해드릴", "지급", "환급", "보상금", "합의금"]
    money_out_keywords = ["송금", "입금", "이체", "보내", "넣으"]

    has_money_in = any(kw in text for kw in money_in_keywords)
    has_money_out = any(kw in text for kw in money_out_keywords)

    # 2. 화자 분석
    user_complaint = any(kw in text for kw in ["환불해", "신고하겠", "고소하겠", "책임져"])
    caller_demand = any(kw in text for kw in ["해주세요", "해야", "필요", "하셔야"])

    # 3. 피싱 신호
    phishing_signals = {
        "앱설치": any(kw in text for kw in ["팀뷰어", "APK", "앱", "설치", "다운로드"]),
        "URL": any(kw in text for kw in [".com", ".net", "접속", "링크"]),
        "원격제어": any(kw in text for kw in ["원격", "제어", "접속번호", "화면 공유"]),
        "공공기관사칭": any(kw in text for kw in ["검찰", "경찰", "금감원", "국세청"]),
        "장소이동": any(kw in text for kw in ["모텔", "숙박", "독립된 공간", "조용한 곳"]),
        "긴급압박": any(kw in text for kw in ["지금 당장", "즉시", "급히", "바로"]),
    }

    phishing_count = sum(phishing_signals.values())

    # 4. 정상 신호
    legitimate_signals = {
        "공식채널": any(kw in text for kw in ["공식 홈페이지", "마이페이지", "카카오톡", "줌"]),
        "예약일정": any(kw in text for kw in ["예약", "예정", "안내", "일정"]),
        "전문용어": any(kw in text for kw in ["법무사", "등기", "계약서", "잔금"]),
    }

    legitimate_count = sum(legitimate_signals.values())

    # === 문제 케이스 식별 ===

    # 문제 1: legitimate인데 피싱 신호가 많음
    if case_type == "legitimate" and phishing_count >= 2:
        issues.append(f"⚠️ 정상으로 분류되었지만 피싱 신호 {phishing_count}개")

    # 문제 2: phishing인데 피싱 신호가 적음
    if case_type == "phishing" and phishing_count == 0:
        issues.append(f"⚠️ 피싱으로 분류되었지만 명확한 피싱 신호 없음")

    # 문제 3: 사용자가 돈을 받는데 phishing으로 분류
    if case_type == "phishing" and has_money_in and not any(phishing_signals.values()):
        issues.append(f"⚠️ 사용자가 돈을 받는 상황인데 피싱? (함정 패턴 없음)")

    # 문제 4: 사용자가 항의하는데 phishing으로 분류
    if case_type == "phishing" and user_complaint:
        issues.append(f"⚠️ 사용자가 항의하는 상황인데 피싱?")

    # 문제 5: legitimate인데 개인정보 요구
    if case_type == "legitimate" and any(kw in text for kw in ["주민번호", "주민등록증", "카드번호"]):
        if not has_money_in:  # 돈을 받는 경우가 아니면
            issues.append(f"⚠️ 정상인데 개인정보 요구 (돈 받는 상황 아님)")

    return {
        "id": case_id,
        "name": name,
        "type": case_type,
        "text_preview": text[:80] + "...",
        "has_money_in": has_money_in,
        "has_money_out": has_money_out,
        "user_complaint": user_complaint,
        "phishing_signals": phishing_count,
        "legitimate_signals": legitimate_count,
        "issues": issues,
    }

def main():
    print("\n" + "="*100)
    print("🔍 벤치마크 케이스 48개 분류 점검")
    print("="*100 + "\n")

    all_analyses = []

    for case in test_cases:
        analysis = analyze_case(case)
        all_analyses.append(analysis)

    # 문제가 있는 케이스만 출력
    problematic_cases = [a for a in all_analyses if a["issues"]]

    print(f"📊 총 {len(test_cases)}개 케이스 중 {len(problematic_cases)}개 케이스에 문제 발견\n")
    print("="*100)

    if not problematic_cases:
        print("✅ 모든 케이스가 명확하게 분류되어 있습니다!")
    else:
        for i, case in enumerate(problematic_cases, 1):
            print(f"\n[{i}] {case['id']}: {case['name']}")
            print(f"    타입: {case['type'].upper()}")
            print(f"    텍스트: {case['text_preview']}")
            print(f"    금전 흐름: IN={case['has_money_in']}, OUT={case['has_money_out']}")
            print(f"    화자: 사용자 항의={case['user_complaint']}")
            print(f"    신호: 피싱={case['phishing_signals']}개, 정상={case['legitimate_signals']}개")
            print(f"    문제점:")
            for issue in case["issues"]:
                print(f"        {issue}")

    print("\n" + "="*100)
    print("\n📋 카테고리별 통계:\n")

    by_type = {}
    for a in all_analyses:
        t = a["type"]
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(a)

    for case_type, cases in by_type.items():
        problematic = [c for c in cases if c["issues"]]
        print(f"  {case_type.upper()}: {len(cases)}개 (문제: {len(problematic)}개)")

    print("\n" + "="*100)

    # 구체적인 재분류 제안
    print("\n🔧 재분류 제안:\n")

    for case in problematic_cases:
        print(f"\n[{case['id']}] {case['name']}")
        print(f"현재 타입: {case['type']}")

        # 자동 재분류 제안
        if case['user_complaint']:
            print(f"제안: LEGITIMATE (사용자가 항의자 역할)")
        elif case['has_money_in'] and case['phishing_signals'] == 0:
            print(f"제안: LEGITIMATE (돈 받는 상황, 피싱 신호 없음)")
        elif case['phishing_signals'] >= 3:
            print(f"제안: PHISHING (명확한 피싱 신호 {case['phishing_signals']}개)")
        elif case['phishing_signals'] == 0 and case['type'] == 'phishing':
            print(f"제안: 재검토 필요 (피싱 신호 부족)")
        else:
            print(f"제안: 수동 검토 필요")

if __name__ == "__main__":
    main()
