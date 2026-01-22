# Sentinel-Voice API Documentation

## Base URL
```
http://localhost:8000
```

## Endpoints

### 1. Root
```
GET /
```

Returns basic service information.

**Response:**
```json
{
  "service": "Sentinel-Voice",
  "version": "0.1.0",
  "status": "running",
  "endpoints": {
    "analyze_audio": "/api/analyze/audio",
    "analyze_text": "/api/analyze/text",
    "health": "/health"
  }
}
```

### 2. Health Check
```
GET /health
```

Check service health status.

**Response:**
```json
{
  "status": "healthy",
  "pipeline_ready": true,
  "scorer_ready": true,
  "masker_ready": true
}
```

### 3. Analyze Audio
```
POST /api/analyze/audio
```

Analyze audio file for voice phishing detection.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (audio file: .wav, .mp3, .flac, .m4a)

**Response:**
```json
{
  "risk_score": 85.5,
  "risk_level": "HIGH",
  "is_phishing": true,
  "alert_message": "⚠️ 보이스피싱 의심! 주의하세요!",
  "component_scores": {
    "keyword": 90.0,
    "sentiment": 75.0,
    "similarity": 88.0
  },
  "techniques_detected": [
    "기관 사칭",
    "협박",
    "금전 요구"
  ],
  "masked_text": "검찰청입니다. 계좌번호 [계좌번호:****1234]로...",
  "pii_detected": {
    "계좌번호": 1,
    "주민번호": 1
  }
}
```

### 4. Analyze Text
```
POST /api/analyze/text
```

Analyze text for phishing detection.

**Request:**
```json
{
  "text": "검찰청입니다. 당신은 금융범죄에 연루되었습니다.",
  "enable_pii_masking": true
}
```

**Response:**
Same as Analyze Audio response.

### 5. Statistics
```
GET /api/stats
```

Get system statistics.

**Response:**
```json
{
  "vector_db": {
    "total_scripts": 1000,
    "embedding_dimension": 768,
    "model_name": "jhgan/ko-sroberta-multitask"
  },
  "risk_scorer": {
    "keyword_weight": 0.3,
    "sentiment_weight": 0.3,
    "similarity_weight": 0.4,
    "threshold": 70
  }
}
```

## Risk Levels

| Score Range | Risk Level | Description |
|-------------|------------|-------------|
| 90-100 | CRITICAL | 매우 높은 위험 - 즉시 통화 종료 |
| 70-89 | HIGH | 보이스피싱 의심 - 주의 필요 |
| 50-69 | MEDIUM | 의심스러운 통화 |
| 30-49 | LOW | 주의 필요 |
| 0-29 | SAFE | 정상 통화 |

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input |
| 403 | Forbidden - Service not ready |
| 500 | Internal Server Error |
| 503 | Service Unavailable - Pipeline not initialized |

## Usage Examples

### cURL

```bash
# Health check
curl http://localhost:8000/health

# Analyze text
curl -X POST http://localhost:8000/api/analyze/text \
  -H "Content-Type: application/json" \
  -d '{"text": "검찰청입니다. 송금하세요.", "enable_pii_masking": true}'

# Analyze audio
curl -X POST http://localhost:8000/api/analyze/audio \
  -F "file=@sample.wav"
```

### Python

```python
import requests

# Analyze text
response = requests.post(
    "http://localhost:8000/api/analyze/text",
    json={
        "text": "검찰청입니다. 계좌번호를 알려주세요.",
        "enable_pii_masking": True
    }
)
result = response.json()
print(f"Risk Score: {result['risk_score']}")

# Analyze audio
with open("audio.wav", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/analyze/audio",
        files={"file": f}
    )
result = response.json()
print(f"Is Phishing: {result['is_phishing']}")
```

### JavaScript

```javascript
// Analyze text
fetch('http://localhost:8000/api/analyze/text', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    text: '검찰청입니다. 송금하세요.',
    enable_pii_masking: true
  })
})
.then(response => response.json())
.then(data => console.log('Risk Score:', data.risk_score));

// Analyze audio
const formData = new FormData();
formData.append('file', audioFile);

fetch('http://localhost:8000/api/analyze/audio', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log('Is Phishing:', data.is_phishing));
```

## Interactive Documentation

Visit http://localhost:8000/docs for interactive Swagger UI documentation.
