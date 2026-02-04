"""
Playwright를 사용하여 HTML을 PDF로 변환
"""
import sys
import io
import os
import asyncio
from playwright.async_api import async_playwright

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

async def convert_html_to_pdf():
    print("📄 HTML을 PDF로 변환 중...")

    # 현재 디렉토리의 절대 경로
    html_path = os.path.abspath("benchmark_report.html")
    pdf_path = os.path.abspath("benchmark_report.pdf")

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # HTML 파일 로드
        await page.goto(f'file:///{html_path}')

        # PDF로 저장
        await page.pdf(
            path=pdf_path,
            format='A4',
            print_background=True,
            margin={
                'top': '20px',
                'right': '20px',
                'bottom': '20px',
                'left': '20px'
            }
        )

        await browser.close()

    print(f"✅ PDF 보고서가 {pdf_path}에 저장되었습니다.")

if __name__ == "__main__":
    asyncio.run(convert_html_to_pdf())
