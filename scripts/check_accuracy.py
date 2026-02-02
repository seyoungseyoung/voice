"""
benchmark_results_detailed.json을 읽어서 정확도 재계산 (caution 타입 포함)
"""
import json

# JSON 파일 읽기
with open('benchmark_results_detailed.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

results = data['results']
total = len(results)

# 정답 판정 (caution 타입 포함)
correct = 0
incorrect_cases = []

for r in results:
    is_correct = False

    if r["type"] == "legitimate":
        is_correct = r["final_score"] <= r["expected_max"]
    elif r["type"] == "phishing":
        is_correct = r["final_score"] >= r["expected_min"]
    elif r["type"] == "caution":
        is_correct = r["expected_min"] <= r["final_score"] <= r["expected_max"]

    if is_correct:
        correct += 1
    else:
        incorrect_cases.append({
            "id": r["id"],
            "name": r["name"],
            "type": r["type"],
            "expected": f"{r['expected_min']}-{r['expected_max']}" if r['type'] in ['phishing', 'caution'] else f"0-{r['expected_max']}",
            "actual": r["final_score"]
        })

accuracy = (correct / total * 100) if total > 0 else 0

print(f"[최종 정확도: {accuracy:.1f}% ({correct}/{total})]")
print()

if incorrect_cases:
    print(f"[오답 케이스 {len(incorrect_cases)}개:]")
    for case in incorrect_cases:
        print(f"  [{case['id']}] {case['name']} - 예상: {case['expected']}, 실제: {case['actual']} (타입: {case['type'].upper()})")
else:
    print("[모든 케이스 정답!]")
