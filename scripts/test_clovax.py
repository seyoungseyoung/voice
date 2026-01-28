"""ClovaX API 테스트"""
import sys
import os
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from src.llm.llm_clients.clovax_client import ClovaXClient

client = ClovaXClient()

print(f"✅ API Key: {client.api_key[:20]}...")
print(f"✅ Gateway Key: {client.gateway_key[:20]}...")
print(f"✅ Available: {client.is_available()}")

if client.is_available():
    print("\n🔍 테스트 중...")
    result = client.analyze_phishing(
        "야, 서울지검인데 너 대포통장 신고 들어왔어. 지금 당장 가까운 모텔로 튀어와.",
        "이 통화가 보이스피싱인지 분석하세요. JSON 형식으로 score(0-100), is_phishing(true/false), reasoning을 반환하세요."
    )
    print(f"\n📊 결과: {result}")
else:
    print("❌ ClovaX not available")
