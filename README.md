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

## 개발 로드맵

- [x] Phase 1: 프로젝트 환경 설정
- [ ] Phase 1: 데이터 수집 및 전처리
- [ ] Phase 2: 모델 탐색 및 최적화
- [ ] Phase 3: 로직 설계 (PII Masking, Risk Scoring)
- [ ] Phase 4: MVP 제작 및 데모

## 라이선스

MIT License
