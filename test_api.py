"""
Quick API test script
"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("Sentinel-Voice API Test")
print("=" * 60)

# Test 1: Health Check
print("\n1. Health Check")
response = requests.get(f"{BASE_URL}/health")
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))

# Test 2: Normal Text
print("\n2. Normal Text Analysis")
response = requests.post(
    f"{BASE_URL}/api/analyze/text",
    json={
        "text": "안녕하세요. 배송이 내일 도착 예정입니다.",
        "enable_pii_masking": False
    }
)
print(f"Status: {response.status_code}")
result = response.json()
print(f"Risk Score: {result['risk_score']}/100")
print(f"Risk Level: {result['risk_level']}")
print(f"Is Phishing: {result['is_phishing']}")
print(f"Alert: {result['alert_message']}")

# Test 3: Phishing Text - 기관 사칭
print("\n3. Phishing Text - 기관 사칭")
response = requests.post(
    f"{BASE_URL}/api/analyze/text",
    json={
        "text": "검찰청입니다. 당신은 금융범죄에 연루되었습니다.",
        "enable_pii_masking": True
    }
)
print(f"Status: {response.status_code}")
result = response.json()
print(f"Risk Score: {result['risk_score']}/100")
print(f"Risk Level: {result['risk_level']}")
print(f"Is Phishing: {result['is_phishing']}")
print(f"Alert: {result['alert_message']}")
print(f"Techniques: {result['techniques_detected']}")

# Test 4: High Risk - 협박 + 송금 유도
print("\n4. High Risk - 협박 + 송금 유도")
response = requests.post(
    f"{BASE_URL}/api/analyze/text",
    json={
        "text": "검찰청입니다. 당신 계좌가 범죄에 연루되어 곧 체포됩니다. 즉시 안전계좌 1234-567890으로 송금하세요.",
        "enable_pii_masking": True
    }
)
print(f"Status: {response.status_code}")
result = response.json()
print(f"Risk Score: {result['risk_score']}/100")
print(f"Risk Level: {result['risk_level']}")
print(f"Is Phishing: {result['is_phishing']}")
print(f"Alert: {result['alert_message']}")
print(f"Techniques: {result['techniques_detected']}")
print(f"Component Scores: {result['component_scores']}")
print(f"Masked Text: {result['masked_text'][:100]}...")
print(f"PII Detected: {result['pii_detected']}")

# Test 5: Statistics
print("\n5. System Statistics")
response = requests.get(f"{BASE_URL}/api/stats")
print(f"Status: {response.status_code}")
stats = response.json()
print(f"Vector DB Scripts: {stats['vector_db']['total_scripts']}")
print(f"Risk Threshold: {stats['risk_scorer']['threshold']}")
print(f"Weights: Keyword={stats['risk_scorer']['keyword_weight']}, "
      f"Sentiment={stats['risk_scorer']['sentiment_weight']}, "
      f"Similarity={stats['risk_scorer']['similarity_weight']}")

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
