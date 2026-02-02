"""
간단한 테이블 형식의 벤치마크 리포트 생성
"""
import json
import datetime

# JSON 파일 읽기
with open('benchmark_results_detailed.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

results = data['results']
total = len(results)

# 정답 판정
correct = sum(1 for r in results if (
    (r["type"] == "legitimate" and r["final_score"] <= r["expected_max"]) or
    (r["type"] == "phishing" and r["final_score"] >= r["expected_min"]) or
    (r["type"] == "caution" and r["expected_min"] <= r["final_score"] <= r["expected_max"])
))
accuracy = (correct / total * 100) if total > 0 else 0

# HTML 생성
html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>보이스피싱 탐지 벤치마크 결과</title>
    <style>
        body {{
            font-family: 'Malgun Gothic', sans-serif;
            margin: 20px;
            background: #f5f5f5;
            font-size: 12px;
        }}

        .container {{
            max-width: 100%;
            margin: 0 auto;
            background: white;
            padding: 20px;
        }}

        h1 {{
            font-size: 1.5em;
            margin-bottom: 5px;
        }}

        .summary {{
            background: #f8f9fa;
            padding: 10px;
            margin: 10px 0;
            border-left: 3px solid #333;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}

        th {{
            background: #333;
            color: white;
            padding: 6px;
            text-align: left;
            font-weight: normal;
            font-size: 11px;
        }}

        td {{
            padding: 6px;
            border-bottom: 1px solid #ddd;
            vertical-align: top;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        .pass {{
            color: #28a745;
            font-weight: bold;
        }}

        .fail {{
            color: #dc3545;
            font-weight: bold;
        }}

        .phishing {{
            color: #dc3545;
        }}

        .legitimate {{
            color: #28a745;
        }}

        .caution {{
            color: #ffc107;
        }}

        .text-content {{
            font-size: 11px;
            line-height: 1.4;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>보이스피싱 탐지 벤치마크 결과</h1>
        <p>Gemini 2.5 Flash + Rule Filter | {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}</p>

        <div class="summary">
            <strong>결과:</strong> 정확도 {accuracy:.1f}% ({correct}/{total}) |
            필터 적용: {sum(1 for r in results if r['filter_applied'])}건
        </div>

        <table>
            <thead>
                <tr>
                    <th style="width: 50px;">ID</th>
                    <th style="width: 150px;">케이스명</th>
                    <th style="width: 300px;">통화 내용</th>
                    <th style="width: 60px;">LLM점수</th>
                    <th style="width: 60px;">최종점수</th>
                    <th style="width: 70px;">예상범위</th>
                    <th style="width: 50px;">결과</th>
                    <th>판정 이유</th>
                </tr>
            </thead>
            <tbody>
"""

# 모든 결과를 테이블로 출력
for r in results:
    is_correct = (
        (r["type"] == "legitimate" and r["final_score"] <= r["expected_max"]) or
        (r["type"] == "phishing" and r["final_score"] >= r["expected_min"]) or
        (r["type"] == "caution" and r["expected_min"] <= r["final_score"] <= r["expected_max"])
    )

    if r['type'] == 'caution':
        expected_range = f"{r['expected_min']}-{r['expected_max']}"
    elif r['type'] == 'phishing':
        expected_range = f"{r['expected_min']}-100"
    else:
        expected_range = f"0-{r['expected_max']}"

    result_text = "✓" if is_correct else "✗"
    result_class = "pass" if is_correct else "fail"
    type_class = r["type"]

    html += f"""
                <tr>
                    <td><strong>{r['id']}</strong></td>
                    <td class="{type_class}">{r['name']}</td>
                    <td class="text-content">{r['input_text']}</td>
                    <td style="text-align: center;">{r['llm_score']}</td>
                    <td style="text-align: center;"><strong>{r['final_score']}</strong></td>
                    <td style="text-align: center;">{expected_range}</td>
                    <td class="{result_class}" style="text-align: center; font-size: 16px;">{result_text}</td>
                    <td class="text-content">{r['reasoning']}</td>
                </tr>
"""

html += """
            </tbody>
        </table>

        <p style="margin-top: 20px; color: #666; font-size: 11px;">
            Sentinel-Voice 프로젝트 | 자동 생성 보고서
        </p>
    </div>
</body>
</html>
"""

# HTML 저장
with open('benchmark_report.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"[OK] 간단한 HTML 보고서 생성 완료: benchmark_report.html")
print(f"     정확도: {accuracy:.1f}% ({correct}/{total})")
