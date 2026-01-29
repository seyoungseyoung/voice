# 🛡️ Sentinel-Voice: AI 기반 실시간 보이스피싱 탐지 시스템

> DACON '피싱·스캠 예방 서비스 개발 경진대회' MVP

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 프로젝트 개요

**실시간 마이크 녹음** + **즉시 텍스트 변환** + **AI 위험도 분석**으로 보이스피싱을 탐지하는 웹 기반 보안 솔루션

### 핵심 기능
- 🎤 **실시간 음성 녹음 및 인식** - 말하면 즉시 텍스트로 표시
- 🤖 **AI 기반 위험도 분석** - 0-100 점수 자동 산출
- 🔒 **개인정보 자동 마스킹** - 서버 전송 전 PII 보호
- 📊 **직관적인 시각화** - 게이지 차트, 오디오 스펙트럼
- ⚡ **빠른 응답** - 1초 이내 텍스트 분석

### 차별화 포인트
- **하이브리드 AI**: 브라우저 STT + 서버 Whisper + Vector DB
- **RAG 기술**: FAISS로 실제 피싱 사례와 실시간 비교
- **Privacy-First**: 민감 정보 서버 전송 전 마스킹
- **웹 데모**: 설치 불필요, URL만 공유하면 즉시 체험

## 🚀 빠른 시작

```powershell
# 1. 가상환경 활성화
venv\Scripts\activate

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 샘플 데이터 생성
python scripts/create_sample_data.py

# 4. 서버 실행
python scripts/run_server.py
```

**웹 브라우저에서 접속**: http://localhost:8000

### 사용 방법

1. **"음성 파일 분석"** 탭 선택
2. **"녹음 시작"** 버튼 클릭
3. 피싱 대사 말하기 (예: "검찰청입니다. 계좌가 범죄에 연루되었으니 송금하세요")
4. **실시간으로 텍스트가 표시되는 것 확인** ✨
5. **"녹음 중지"** 클릭
6. **"이 녹음 분석하기"** 클릭
7. 결과 확인 (위험도, 탐지 기법, 권장 조치)

## 🎬 데모 스크린샷

(여기에 스크린샷 추가 예정)

## 📊 시스템 아키텍처

```
마이크/파일 입력
    ↓
실시간 STT (Web Speech API / Whisper)
    ↓
AI 분석 엔진
├─ 키워드 분석 (30%)
├─ 감정 분석 (30%)
└─ 유사도 검색 (40%) ← FAISS Vector DB
    ↓
위험도 점수 (0-100)
    ↓
사용자 알림 (게이지 + 권장 조치)
```

## 🛠 기술 스택

| 분야 | 기술 |
|------|------|
| 프론트엔드 | HTML5, CSS3, JavaScript, Web Speech API |
| 백엔드 | Python 3.11, FastAPI, Uvicorn |
| AI/ML | Whisper (STT), Sentence-BERT, FAISS |
| 오디오 | Librosa, SoundFile, NoiseReduce |

## 📁 프로젝트 구조

```
voice/
├── 📄 QUICKSTART.md          # 빠른 시작 가이드
├── 📄 COMPLETE_FEATURES.md   # 전체 기능 목록
├── 📄 DEMO_PLAN.md           # 데모 계획서
├── src/
│   ├── stt/                  # Speech-to-Text
│   ├── nlp/                  # 분석 파이프라인
│   ├── security/             # PII Masking
│   ├── scoring/              # Risk Scoring
│   └── server/               # FastAPI 서버
├── static/                   # 웹 데모 페이지
├── data/
│   ├── vector_db/            # FAISS 벡터 DB
│   └── training_dataset.json # 샘플 데이터
└── scripts/                  # 유틸리티 스크립트
```

## 📚 문서

- [빠른 시작 가이드](QUICKSTART.md) - 설치 및 실행 방법
- [완성 기능 목록](COMPLETE_FEATURES.md) - 전체 기능 및 사용법
- [데모 계획서](DEMO_PLAN.md) - 대회 전략 및 시연 계획
- [API 문서](http://localhost:8000/docs) - Swagger UI (서버 실행 후)

## 🔒 개인정보 보호 정책

### 현재 구현 (웹 데모)
본 시스템은 **데모 및 연구 목적**으로 웹 기반으로 구현되었습니다. 실제 통화 내용이 서버로 전송되므로 개인정보 보호에 주의가 필요합니다.

**⚠️ 주의사항:**
- 실제 통화 중 사용 시 상대방 동의 필요 (통신비밀보호법)
- 민감한 개인정보(금융정보, 주민번호 등) 입력 금지
- 테스트용 예시 문장만 사용 권장

### 실서비스 전환 시 권장사항

#### 1. 온디바이스(On-Device) 처리 방식
```
스마트폰 앱 → 기기 내부 AI 처리 → 위험 알림
(서버 전송 없음, 개인정보 유출 위험 없음)
```
- ✅ 통화 내용이 외부로 전송되지 않음
- ✅ 실시간 처리 가능 (TinyML, Edge AI)
- ✅ 통신비밀보호법 준수

#### 2. 사용자 동의 + 암호화 방식
```
사용자 동의 → End-to-End 암호화 → 서버 분석 → 즉시 삭제
```
- ⚠️ 명시적 사용자 동의 필수
- ⚠️ 전송 중 AES-256 암호화
- ⚠️ 서버 로그 저장 금지

#### 3. 하이브리드 방식 (권장)
```
로컬 키워드 감지 → 의심 시만 서버 분석
```
- ✅ 평소에는 기기 내부 처리
- ✅ 고위험 패턴 감지 시에만 전송
- ✅ 개인정보 노출 최소화

**📌 본 프로젝트는 기술적 실현 가능성(Proof of Concept)을 검증하는 것이 목적이며, 실서비스 시에는 온디바이스 AI로 전환을 권장합니다.**

## 🏆 개발 현황

- ✅ **Phase 1**: 데이터 엔지니어링 완료
- ✅ **Phase 2**: STT 모델 통합 완료
- ✅ **Phase 3**: Risk Scoring 완료
- ✅ **Phase 4**: 웹 MVP 완료
- ✅ **Phase 5**: Gemini + Rule Filter 최적화 완료
- 🚀 **대회 제출 준비 완료**

## 📞 지원

- GitHub Issues: [seyoungseyoung/voice/issues](https://github.com/seyoungseyoung/voice/issues)
- 문서: [docs/](docs/)

## 📄 라이선스

MIT License

---

<p align="center">
  Made with ❤️ for DACON 피싱·스캠 예방 서비스 개발 경진대회
</p>
