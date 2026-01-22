# Sentinel-Voice 빠른 시작 가이드

## 1. 환경 설정

### 가상환경 활성화 및 패키지 설치
```powershell
# 가상환경 활성화
venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

**참고:** 패키지 설치에는 약 5-10분이 소요됩니다.

## 2. 샘플 데이터 생성

```powershell
# 샘플 피싱 데이터 및 Vector DB 생성
python scripts/create_sample_data.py
```

이 작업은 다음을 수행합니다:
- 5가지 피싱 시나리오 생성
- Vector Database 구축 (FAISS)
- 유사도 검색 테스트

## 3. 서버 실행

```powershell
# API 서버 시작
python scripts/run_server.py
```

서버가 시작되면 다음 URL에 접속 가능:
- **데모 페이지**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **건강 체크**: http://localhost:8000/health

## 4. 데모 사용법

### 웹 데모 페이지
1. 브라우저에서 http://localhost:8000 접속
2. 3가지 탭 중 선택:
   - **텍스트 분석**: 직접 입력하여 분석
   - **음성 파일 분석**: 파일 업로드
   - **데모 시나리오**: 미리 준비된 시나리오 테스트

3. 분석 결과 확인:
   - 위험도 점수 (0-100)
   - 위험 레벨 (SAFE/LOW/MEDIUM/HIGH/CRITICAL)
   - 탐지된 피싱 기법
   - 개인정보 마스킹 결과

### API 직접 호출

#### Python으로 테스트
```python
import requests

# 텍스트 분석
response = requests.post(
    "http://localhost:8000/api/analyze/text",
    json={
        "text": "검찰청입니다. 당신 계좌가 범죄에 연루되었으니 즉시 송금하세요.",
        "enable_pii_masking": True
    }
)
print(response.json())
```

#### PowerShell로 테스트
```powershell
# Health Check
Invoke-WebRequest -Uri "http://localhost:8000/health" | Select-Object -Expand Content

# Text Analysis
$body = @{
    text = "검찰청입니다. 계좌가 범죄에 연루되었습니다."
    enable_pii_masking = $true
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/analyze/text" -Method POST -Body $body -ContentType "application/json"
```

## 5. 트러블슈팅

### 패키지 설치 오류
```powershell
# 특정 패키지가 설치되지 않는 경우
pip install faiss-cpu sentence-transformers openai-whisper --no-cache-dir
```

### 모델 다운로드 느림
- Whisper 모델 (약 150MB) 첫 실행 시 자동 다운로드
- Sentence Transformer 모델 (약 450MB) 첫 실행 시 자동 다운로드
- 이후 실행에서는 캐시 사용으로 빠름

### Vector DB 없음 경고
```
WARNING:src.vector_db.vector_store:Vector database not found
```
→ 정상입니다. `python scripts/create_sample_data.py` 실행 후 서버 재시작

### 서버 포트 충돌
```powershell
# 다른 포트로 실행
python scripts/run_server.py --port 8080
```

## 6. 다음 단계

### 실제 데이터 수집
```powershell
# AI Hub 민원 데이터 다운로드
python scripts/collect_data.py
```

데이터 수집 후:
1. `data/raw/` 폴더에 파일 배치
2. 전처리: `python scripts/preprocess_data.py`
3. 라벨링: `python scripts/label_data.py --create-dataset`
4. Vector DB 재구축: `python scripts/build_vector_db.py`

### 성능 테스트
```powershell
# API 테스트
pytest tests/test_api.py -v

# STT 벤치마크
python scripts/benchmark_stt.py
```

### 배포 (선택사항)
```powershell
# 프로덕션 모드로 실행
uvicorn src.server.main:app --host 0.0.0.0 --port 80 --workers 4
```

## 7. 주요 파일 구조

```
voice/
├── scripts/
│   ├── run_server.py           # 서버 실행
│   ├── create_sample_data.py   # 샘플 데이터 생성
│   └── test_api.py             # API 테스트
├── src/
│   ├── server/main.py          # FastAPI 서버
│   ├── nlp/phishing_pipeline.py # 분석 파이프라인
│   ├── scoring/risk_scorer.py  # 위험도 채점
│   └── security/pii_masking.py # 개인정보 마스킹
├── static/
│   ├── index.html              # 데모 페이지
│   ├── style.css               # 스타일
│   └── script.js               # 프론트엔드 로직
└── data/
    ├── raw/                    # 원본 데이터
    ├── processed/              # 전처리 데이터
    └── vector_db/              # 벡터 데이터베이스
```

## 8. 주요 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/` | GET | 데모 페이지 |
| `/health` | GET | 건강 체크 |
| `/api/analyze/text` | POST | 텍스트 분석 |
| `/api/analyze/audio` | POST | 음성 파일 분석 |
| `/api/stats` | GET | 시스템 통계 |
| `/docs` | GET | Swagger API 문서 |

## 9. 개발 모드

```powershell
# 자동 리로드 활성화 (코드 수정 시 자동 재시작)
python scripts/run_server.py --reload
```

## 10. 지원

문제 발생 시:
1. [GitHub Issues](https://github.com/seyoungseyoung/voice/issues)
2. API 문서 확인: http://localhost:8000/docs
3. 로그 확인: 콘솔 출력 참조
