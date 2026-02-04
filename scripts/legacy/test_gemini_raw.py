"""Gemini API 원시 응답 구조 확인"""
import os
import sys
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from src.llm.llm_clients.gemini_client import GeminiClient

client = GeminiClient()

if not client.is_available():
    print("❌ Gemini API key not found")
    sys.exit(1)

test_text = "야, 서울지검인데 너 대포통장 신고 들어왔어."

print("🔍 Gemini API 테스트 중...\n")

result = client.analyze_phishing(test_text, "이 통화가 보이스피싱인지 분석하세요.")

print("\n📊 결과:")
print(json.dumps(result, indent=2, ensure_ascii=False))
