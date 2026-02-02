"""
기존 benchmark_results_detailed.json을 읽어서 HTML과 PDF 재생성
"""
import json
import sys
import os
from datetime import datetime

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.generate_benchmark_report import generate_html_report

# JSON 파일 읽기
print("📖 benchmark_results_detailed.json 읽는 중...")
with open('benchmark_results_detailed.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

results = data['results']

# HTML 리포트 생성 (수정된 로직 적용)
print("🔨 HTML 리포트 생성 중 (caution 타입 포함)...")
generate_html_report(results)

print("\n✅ HTML 리포트 재생성 완료!")
print("   - benchmark_report.html")

# PDF 생성
print("\n📄 PDF 변환 중...")
try:
    import subprocess
    result = subprocess.run(
        ['python', 'scripts/convert_to_pdf.py'],
        capture_output=True,
        text=True,
        timeout=30
    )
    if result.returncode == 0:
        print("✅ PDF 생성 완료: benchmark_report.pdf")
    else:
        print(f"⚠️ PDF 생성 실패: {result.stderr}")
except Exception as e:
    print(f"⚠️ PDF 생성 중 오류: {e}")
    print("   HTML 파일은 정상적으로 생성되었습니다.")
