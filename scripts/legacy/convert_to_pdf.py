"""
HTML 보고서를 PDF로 변환
"""
import sys
import io
from playwright.sync_api import sync_playwright

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("📄 HTML을 PDF로 변환 중...")

# Playwright를 사용하여 HTML을 PDF로 변환
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('file:///c:/Users/tpdud/code/voice/benchmark_report.html')
    page.pdf(path='benchmark_report_simple.pdf', format='A4', print_background=True)
    browser.close()

print("[OK] PDF 보고서가 benchmark_report_simple.pdf에 저장되었습니다.")
