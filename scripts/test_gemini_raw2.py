"""Gemini API 응답 구조 확인"""
import sys
import os
import io
import json
import requests

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ GEMINI_API_KEY not found")
    sys.exit(1)

print("✅ API Key found")

headers = {
    "Content-Type": "application/json"
}

payload = {
    "contents": [{
        "parts": [{
            "text": "Hello, respond with just 'Hi'"
        }]
    }],
    "generationConfig": {
        "temperature": 0.2,
        "maxOutputTokens": 100
    }
}

print("\n📤 Sending request...")

try:
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={api_key}",
        headers=headers,
        json=payload,
        timeout=30
    )

    print(f"\n📥 Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print("\n✅ Full Response:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # Try to extract content
        try:
            content = result["candidates"][0]["content"]["parts"][0]["text"]
            print(f"\n✅ Extracted content: {content}")
        except KeyError as e:
            print(f"\n❌ KeyError: {e}")
            print("Available keys in result:", list(result.keys()))
            if "candidates" in result:
                print("Available keys in candidates[0]:", list(result["candidates"][0].keys()))
                if "content" in result["candidates"][0]:
                    print("Available keys in content:", list(result["candidates"][0]["content"].keys()))
    else:
        print("Error response:")
        print(response.text)

except Exception as e:
    print(f"\n❌ Error: {e}")
