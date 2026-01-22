# Sentinel-Voice: AI-based Real-time Voice Phishing Detection System

하이브리드 AI 기반 실시간 보이스피싱 탐지 시스템

## 프로젝트 개요

통화 음성을 실시간 텍스트화(STT)하고, 하이브리드 NLP 모델(On-device + Cloud)을 통해 피싱 의도와 맥락을 분석하여 사용자에게 경고하는 보안 솔루션입니다.

## 주요 특징

- **맥락 기반 탐지**: 단순 키워드 매칭이 아닌 대화 맥락 분석
- **RAG 기술**: 최신 피싱 범죄 사례와 실시간 비교
- **Privacy-First**: 민감 정보 마스킹 및 온디바이스 처리

## 시스템 아키텍처

```
Audio Input → STT (Whisper) → NLP Analysis (2-Level) → Risk Scoring → Alert
                                ├─ Level 1: On-device (KoBERT/Llama)
                                └─ Level 2: Cloud (ClovaX + Vector DB)
```

## 설치 방법

### 1. 가상환경 생성
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 API 키 입력
```

## 프로젝트 구조

```
voice/
├── src/                    # 소스 코드
│   ├── config.py          # 설정 관리
│   ├── stt/               # Speech-to-Text
│   ├── nlp/               # NLP 분석
│   ├── security/          # PII Masking
│   ├── scoring/           # Risk Scoring
│   └── server/            # FastAPI 서버
├── data/                   # 데이터
│   ├── raw/               # 원본 데이터
│   ├── processed/         # 전처리 데이터
│   └── vector_db/         # 벡터 DB
├── models/                # 학습된 모델
├── tests/                 # 테스트 코드
├── logs/                  # 로그 파일
└── requirements.txt       # 의존성
```

## 사용 방법

### API 서버 실행

```bash
# 서버 시작
python scripts/run_server.py

# 또는 포트 지정
python scripts/run_server.py --host 0.0.0.0 --port 8000
```

API 문서: http://localhost:8000/docs

### 주요 스크립트

```bash
# 데이터 수집
python scripts/collect_data.py

# 데이터 전처리
python scripts/preprocess_data.py --input-dir data/raw --output-dir data/processed

# 데이터 라벨링
python scripts/label_data.py --transcript transcript.json --audio audio.wav

# Vector DB 구축
python scripts/build_vector_db.py --labeled-data data/training_dataset.json

# STT 벤치마크
python scripts/benchmark_stt.py --test-dir data/processed --whisper-models tiny,base

# 테스트 실행
pytest tests/
```

## 개발 로드맵

- [x] Phase 1: 데이터 엔지니어링
  - [x] 프로젝트 환경 설정
  - [x] 데이터 수집 도구
  - [x] 데이터 전처리 (노이즈 제거, 정규화)
  - [x] 데이터 라벨링 시스템
  - [x] Vector Database 구축 (FAISS)
- [x] Phase 2: 모델 탐색 및 최적화
  - [x] STT 모델 벤치마킹 (Whisper vs Clova Speech)
  - [x] LLM 파이프라인 설계 (LangChain)
- [x] Phase 3: 로직 설계
  - [x] PII Masking 모듈
  - [x] Risk Scoring Algorithm (Keyword + Sentiment + Similarity)
- [x] Phase 4: MVP 제작
  - [x] FastAPI 백엔드 서버
  - [ ] Flutter/Android 프론트엔드
  - [ ] 데모 시나리오 및 최적화

## 라이선스

MIT License
