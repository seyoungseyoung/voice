"""
API tests for Sentinel-Voice
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from src.server.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Sentinel-Voice"
    assert "version" in data


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


def test_analyze_text_phishing():
    """Test text analysis with phishing content"""
    payload = {
        "text": "검찰청입니다. 당신은 금융범죄에 연루되었으니 즉시 안전계좌로 송금하세요.",
        "enable_pii_masking": True
    }

    response = client.post("/api/analyze/text", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "risk_score" in data
    assert "risk_level" in data
    assert "is_phishing" in data

    # Should detect as phishing
    assert data["is_phishing"] is True
    assert data["risk_score"] >= 70


def test_analyze_text_normal():
    """Test text analysis with normal content"""
    payload = {
        "text": "안녕하세요. 배송이 내일 도착 예정입니다.",
        "enable_pii_masking": False
    }

    response = client.post("/api/analyze/text", json=payload)
    assert response.status_code == 200

    data = response.json()
    # Should be safe
    assert data["risk_score"] < 50


def test_analyze_text_pii_masking():
    """Test PII masking in text analysis"""
    payload = {
        "text": "제 계좌번호는 1234-567890입니다.",
        "enable_pii_masking": True
    }

    response = client.post("/api/analyze/text", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["masked_text"] is not None
    assert "계좌번호" in data["pii_detected"]


def test_get_stats():
    """Test stats endpoint"""
    response = client.get("/api/stats")
    assert response.status_code == 200

    data = response.json()
    assert "vector_db" in data
    assert "risk_scorer" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
