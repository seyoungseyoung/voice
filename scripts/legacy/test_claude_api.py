"""Claude API 직접 테스트"""
import sys
import os
import io
import json
import requests

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    print("❌ ANTHROPIC_API_KEY not found")
    sys.exit(1)

print("✅ API Key found")
print(f"Key prefix: {api_key[:20]}...")

headers = {
    "Content-Type": "application/json",
    "x-api-key": api_key,
    "anthropic-version": "2023-06-01"
}

payload = {
    "model": "claude-3-5-haiku-20241022",
    "max_tokens": 100,
    "messages": [
        {
            "role": "user",
            "content": "Hello, respond with just 'Hi'"
        }
    ]
}

print("\n📤 Sending request...")
print(json.dumps(payload, indent=2))

try:
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=payload,
        timeout=30
    )

    print(f"\n📥 Status: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

except Exception as e:
    print(f"\n❌ Error: {e}")
    if hasattr(e, 'response'):
        print(f"Response: {e.response.text}")
