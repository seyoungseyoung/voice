"""
기존 benchmark_results_detailed.json을 읽어서 HTML 리포트만 재생성
"""
import json
import sys
import os

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.generate_benchmark_report import generate_html_report

# JSON 파일 읽기
with open('benchmark_results_detailed.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

results = data['results']
test_date = data['test_date']

# HTML 리포트 생성
generate_html_report(results, test_date)

print(f"\n✅ HTML 리포트 재생성 완료 (JSON 재사용)")
