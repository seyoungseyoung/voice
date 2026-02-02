"""
48개 케이스와 LLM 프롬프트, Rule Filter 로직을 1:1 매칭 검증
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from generate_benchmark_report import test_cases

# LLM 프롬프트의 판단 기준
LLM_CRITERIA = {
    "유형A_공공기관사칭": {
        "signals": ["공공기관/기업 사칭", "금융정보 요구", "앱설치", "URL접속", "개인정보", "심리적압박", "장소이동"],
        "expected_score": "85-100"
    },
    "유형B_가족사칭": {
        "signals": ["가족/지인 사칭", "긴급 금전 요구", "친구계좌", "비정상 상황", "계좌번호 구두전달"],
        "expected_score": "70-100"
    },
    "유형C_투자사기": {
        "signals": ["과도한 수익률", "선납금 요구", "원금 보장", "환불 거부"],
        "expected_score": "70-100"
    },
    "유형D_사회공학": {
        "signals": ["모르는 사람", "지나치게 친근", "관계 형성", "개인 연락처 확보"],
        "expected_score": "65-100"
    },
    "정상_예약일정": {
        "signals": ["예약하신", "말씀하신", "사전 합의"],
        "expected_score": "0-30"
    },
    "정상_돈받는상황": {
        "signals": ["송금해드릴게요", "지급", "환급", "보상금"],
        "expected_score": "0-30"
    }
}

# Rule Filter 규칙
FILTER_RULES = {
    "Rule0_사용자항의": {
        "keywords": ["환불해", "신고하겠", "고소하겠", "책임져"],
        "count": 2,
        "action": "→ 20점"
    },
    "Rule1_채권추심": {
        "keywords": ["이자", "원금", "대출금", "채무", "연체", "상환"],
        "count": 2,
        "action": "→ 50점"
    },
    "Rule2_중고거래": {
        "keywords": ["중고", "안전결제", "직거래", "택배"],
        "count": 2,
        "action": "→ 50점"
    },
    "Rule3_Web3": {
        "keywords": ["지갑 연결", "트랜잭션", "에어드랍", "클레임"],
        "count": 1,
        "action": "→ 85점 이상 유지"
    },
    "Rule4_CEO_Fraud": {
        "keywords": ["개인 계좌", "법인 계좌에서"],
        "count": 1,
        "action": "→ LLM 점수 유지 (격하 금지)"
    },
    "Rule5_내부업무": {
        "keywords": ["대리/과장/부장", "거래처/미팅/회의"],
        "exclude": ["헤드헌팅", "헤드헌터"],
        "action": "→ 50점 (단, CEO Fraud 아니면)"
    },
    "Rule6_2차LLM": {
        "condition": "60-84점",
        "action": "→ 재검증 (예외상황 체크)"
    }
}

def analyze_case_logic(case):
    """케이스가 어떤 로직에 매칭되는지 분석"""
    text = case["text"].lower()
    case_type = case["type"]
    expected_min = case.get("min", 0)
    expected_max = case.get("max", 100)

    analysis = {
        "id": case["id"],
        "name": case["name"],
        "type": case_type,
        "expected": f"{expected_min}-{expected_max}",
        "llm_match": [],
        "filter_match": [],
        "predicted_llm_score": None,
        "predicted_final_score": None,
        "logic_path": []
    }

    # === LLM 프롬프트 매칭 ===

    # 유형A: 공공기관 사칭
    if any(kw in text for kw in ["검찰", "경찰", "금감원", "국세청", "금융감독원"]):
        has_signals = sum([
            any(kw in text for kw in ["앱", "설치", "apk"]),
            any(kw in text for kw in [".com", ".net", "접속", "링크"]),
            any(kw in text for kw in ["모텔", "숙박", "독립된"]),
            any(kw in text for kw in ["송금", "계좌", "입금"])
        ])
        if has_signals >= 1:
            analysis["llm_match"].append("유형A_공공기관사칭")
            analysis["predicted_llm_score"] = 95

    # 유형B: 가족 사칭
    if any(kw in text for kw in ["엄마", "아빠", "아들", "딸", "가족"]):
        if "친구 계좌" in text or "친구계좌" in text or ("친구" in text and "계좌" in text):
            analysis["llm_match"].append("유형B_가족사칭_친구계좌")
            analysis["predicted_llm_score"] = 90
        elif any(kw in text for kw in ["급해", "지금", "바로"]) and any(kw in text for kw in ["만원", "원"]):
            analysis["llm_match"].append("유형B_가족사칭_긴급")
            analysis["predicted_llm_score"] = 85

    # 유형D: 사회공학 (로맨스 스캠)
    if any(phrase in text for phrase in ["잘못 걸린", "번호가 바뀌", "인연"]):
        if "카톡" in text or "친구" in text:
            analysis["llm_match"].append("유형D_사회공학")
            analysis["predicted_llm_score"] = 75

    # 정상: 예약 일정
    if "예약" in text or "말씀하신" in text:
        analysis["llm_match"].append("정상_예약일정")
        analysis["predicted_llm_score"] = 15

    # 정상: 돈 받는 상황
    if any(phrase in text for phrase in ["송금해드릴", "입금해드릴", "지급", "환급"]):
        analysis["llm_match"].append("정상_돈받는상황")
        analysis["predicted_llm_score"] = 15

    # 기본값
    if not analysis["llm_match"]:
        if case_type == "phishing":
            analysis["predicted_llm_score"] = 80
        else:
            analysis["predicted_llm_score"] = 40

    # === Rule Filter 매칭 ===
    llm_score = analysis["predicted_llm_score"]

    # Rule 0: 사용자 항의
    complaint_count = sum(1 for kw in ["환불해", "신고하겠", "고소하겠", "책임져"] if kw in text)
    if complaint_count >= 2:
        analysis["filter_match"].append("Rule0_사용자항의")
        analysis["predicted_final_score"] = 20
        analysis["logic_path"].append("Rule0: 항의 → 20점")
        return analysis

    # Rule 1: 채권 추심
    debt_count = sum(1 for kw in ["이자", "원금", "대출금", "채무", "연체", "상환"] if kw in text)
    has_impersonation = any(kw in text for kw in ["검찰", "경찰", "금감원"])
    if debt_count >= 2 and not has_impersonation:
        analysis["filter_match"].append("Rule1_채권추심")
        analysis["predicted_final_score"] = 50
        analysis["logic_path"].append("Rule1: 채권추심 → 50점")
        return analysis

    # Rule 2: 중고거래
    commerce_count = sum(1 for kw in ["중고", "안전결제", "직거래", "택배"] if kw in text)
    if commerce_count >= 2:
        analysis["filter_match"].append("Rule2_중고거래")
        analysis["predicted_final_score"] = 50
        analysis["logic_path"].append("Rule2: 중고거래 → 50점")
        return analysis

    # Rule 3: Web3
    web3_count = sum(1 for kw in ["지갑", "트랜잭션", "에어드랍", "클레임"] if kw in text)
    if web3_count >= 1:
        analysis["filter_match"].append("Rule3_Web3")
        analysis["predicted_final_score"] = max(85, llm_score)
        analysis["logic_path"].append(f"Rule3: Web3 → {max(85, llm_score)}점")
        return analysis

    # Rule 4: CEO Fraud
    if ("개인 계좌" in text or "개인통장" in text) and ("법인" in text):
        analysis["filter_match"].append("Rule4_CEO_Fraud")
        analysis["predicted_final_score"] = llm_score
        analysis["logic_path"].append(f"Rule4: CEO Fraud → LLM {llm_score}점 유지")
        return analysis

    # Rule 5: 내부 업무
    has_title = any(kw in text for kw in ["대리", "과장", "부장", "팀장", "이사", "전무"])
    has_context = any(kw in text for kw in ["거래처", "미팅", "회의", "법인"])
    is_headhunter = any(kw in text for kw in ["헤드헌팅", "헤드헌터"])
    if has_title and has_context and not is_headhunter and 70 <= llm_score <= 95:
        if not ("개인 계좌" in text and "법인" in text):
            analysis["filter_match"].append("Rule5_내부업무")
            analysis["predicted_final_score"] = 50
            analysis["logic_path"].append("Rule5: 내부업무 → 50점")
            return analysis

    # Rule 6: 2차 LLM (60-84점)
    if 60 <= llm_score <= 84:
        # 예약일정/돈받는상황이면 정상 가능성
        if "예약" in text or "말씀하신" in text or "송금해드릴" in text:
            analysis["filter_match"].append("Rule6_2차LLM_정상")
            analysis["predicted_final_score"] = 20
            analysis["logic_path"].append("Rule6: 2차LLM → 예외1/3 → 20점")
            return analysis

    # Rule 통과
    analysis["predicted_final_score"] = llm_score
    analysis["logic_path"].append(f"Rule 통과 → LLM {llm_score}점 유지")

    return analysis

def main():
    print("\n" + "="*100)
    print("🔍 48개 케이스 로직 검증 (LLM 프롬프트 + Rule Filter)")
    print("="*100 + "\n")

    all_analyses = []
    potential_failures = []

    for case in test_cases:
        analysis = analyze_case_logic(case)
        all_analyses.append(analysis)

        # 예상 결과와 실제 기대값 비교
        expected_min = case.get("min", 0)
        expected_max = case.get("max", 100)
        predicted = analysis["predicted_final_score"]

        if predicted is None:
            potential_failures.append({
                "case": case,
                "analysis": analysis,
                "reason": "예측 점수 없음"
            })
        elif case["type"] == "phishing":
            if not (expected_min <= predicted <= 100):
                potential_failures.append({
                    "case": case,
                    "analysis": analysis,
                    "reason": f"피싱인데 {predicted}점 예상 (기대: {expected_min}+)"
                })
        elif case["type"] == "legitimate":
            if not (0 <= predicted <= expected_max):
                potential_failures.append({
                    "case": case,
                    "analysis": analysis,
                    "reason": f"정상인데 {predicted}점 예상 (기대: 0-{expected_max})"
                })
        elif case["type"] == "caution":
            if not (expected_min <= predicted <= expected_max):
                potential_failures.append({
                    "case": case,
                    "analysis": analysis,
                    "reason": f"주의인데 {predicted}점 예상 (기대: {expected_min}-{expected_max})"
                })

    # 결과 출력
    print(f"📊 총 {len(test_cases)}개 케이스 분석 완료\n")
    print(f"⚠️  예상 실패 케이스: {len(potential_failures)}개\n")

    if potential_failures:
        print("="*100)
        print("❌ 예상 실패 케이스 상세:")
        print("="*100 + "\n")

        for i, fail in enumerate(potential_failures, 1):
            case = fail["case"]
            analysis = fail["analysis"]
            reason = fail["reason"]

            print(f"[{i}] {analysis['id']}: {analysis['name']}")
            print(f"    타입: {analysis['type']}")
            print(f"    기대: {analysis['expected']}점")
            print(f"    예상 LLM: {analysis['predicted_llm_score']}점")
            print(f"    예상 최종: {analysis['predicted_final_score']}점")
            print(f"    LLM 매칭: {', '.join(analysis['llm_match']) if analysis['llm_match'] else '없음'}")
            print(f"    Filter 매칭: {', '.join(analysis['filter_match']) if analysis['filter_match'] else '없음'}")
            print(f"    로직 경로: {' → '.join(analysis['logic_path'])}")
            print(f"    ⚠️  문제: {reason}")
            print(f"    텍스트: {case['text'][:100]}...")
            print()
    else:
        print("✅ 모든 케이스가 로직상 통과할 것으로 예상됩니다!")

    print("="*100)
    print("\n📋 카테고리별 예상 결과:\n")

    by_type = {"phishing": [], "legitimate": [], "caution": []}
    for a in all_analyses:
        by_type[a["type"]].append(a)

    for case_type, cases in by_type.items():
        fail_count = sum(1 for c in cases if any(f["analysis"]["id"] == c["id"] for f in potential_failures))
        print(f"  {case_type.upper()}: {len(cases)}개 (예상 실패: {fail_count}개)")

    expected_accuracy = ((len(test_cases) - len(potential_failures)) / len(test_cases)) * 100
    print(f"\n🎯 예상 정확도: {expected_accuracy:.1f}%")

    print("\n" + "="*100)

if __name__ == "__main__":
    main()
