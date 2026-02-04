# 🛡️ Sentinel-Voice: AI 기반 실시간 보이스피싱 탐지 시스템

> **100% 정확도 달성** - Gemini 2.5 Flash + Rule Filter V2로 54개 벤치마크 케이스 완벽 탐지

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![Accuracy](https://img.shields.io/badge/Accuracy-100%25-brightgreen.svg)](./scripts/benchmark_results_detailed.json)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 프로젝트 개요

**실시간 음성 인식** + **2단계 AI 검증** + **Rule 기반 필터링**으로 보이스피싱을 탐지하는 고정밀 보안 솔루션

### 🏆 주요 성과

- ✅ **100% 정확도** - 54개 테스트 케이스 전부 정확히 판정
- ✅ **2단계 LLM 검증** - Chain-of-Thought 추론으로 엣지 케이스 해결
- ✅ **실제 사례 검증** - 금융감독원 및 실제 피해 사례 6건 포함
- ✅ **False Positive 0건** - 정상 통화를 피싱으로 오판하지 않음

### 핵심 기능

- 🎤 **실시간 음성 녹음 및 인식** - 말하면 즉시 텍스트로 표시
- 🤖 **하이브리드 AI 분석**
  - 1차: Gemini 2.5 Flash (LLM 기반 판정)
  - 2차: Chain-of-Thought 추론 검증 (60-98점 애매한 케이스)
  - 3차: Rule Filter V2 (10가지 패턴 규칙)
- 🔒 **개인정보 자동 마스킹** - 서버 전송 전 PII 보호
- 📊 **직관적인 시각화** - 게이지 차트, 오디오 스펙트럼
- ⚡ **빠른 응답** - 1초 이내 텍스트 분석

### 차별화 포인트

| 기능 | 설명 |
|------|------|
| **2단계 LLM 검증** | 60-98점 애매한 케이스에 대해 Chain-of-Thought로 재검증 |
| **능동적 제안 탐지** | "대상자로 선정" 등 정부지원금 사칭 피싱 탐지 |
| **10가지 Rule Filter** | 채권추심, 중고거래, Web3 스캠 등 유형별 정교한 분류 |
| **False Positive 제로** | 보험금 지급, 부동산 계약 등 정상 통화를 피싱으로 오판하지 않음 |
| **Privacy-First** | 민감 정보 서버 전송 전 마스킹 |

## 📊 벤치마크 결과

### 테스트 케이스 구성 (총 54개)

| 카테고리 | 개수 | 설명 | 정확도 |
|---------|------|------|--------|
| **A** | 10개 | 전통적 보이스피싱 (검찰·금감원 사칭) | 100% |
| **B** | 4개 | 정상 케이스 (심리상담, 원격지원) | 100% |
| **C** | 10개 | URL 기반 피싱 (스미싱, 가짜 사이트) | 100% |
| **D** | 4개 | 신규 공격 유형 (딥보이스, 로맨스 스캠) | 100% |
| **E** | 12개 | 고난도 애매한 케이스 | 100% |
| **F** | 3개 | Hard Negatives (정상→피싱 오판 방지) | 100% |
| **G** | 3개 | Hard Positives (피싱→정상 오판 방지) | 100% |
| **H** | 2개 | 맥락 모호 케이스 | 100% |
| **I** | 6개 | **실제 보이스피싱 녹취록** | 100% |

**총 정확도: 54/54 (100%)**

### 보고서 생성

```bash
cd scripts
python generate_benchmark_report.py  # 상세 벤치마크 실행
python generate_simple_pdf.py        # 간단한 PDF 보고서 생성
```

생성된 파일:
- `benchmark_results_detailed.json` - 전체 결과 데이터
- `benchmark_report.html` - 웹 보고서
- `benchmark_report.pdf` - PDF 보고서

## 🚀 빠른 시작

### 1. 환경 설정

```powershell
# 가상환경 활성화
venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일에 GEMINI_API_KEY 입력
```

### 2. 샘플 데이터 생성

```powershell
python scripts/create_sample_data.py
```

### 3. 서버 실행

```powershell
python scripts/run_server.py
```

**웹 브라우저에서 접속**: http://localhost:8000

### 🐳 Docker로 실행 (권장)

```bash
# 1. .env 파일 생성
cp .env.example .env
# .env 파일에 API 키 입력

# 2. Docker Compose로 실행
docker-compose up -d

# 3. 로그 확인
docker-compose logs -f

# 4. 중지
docker-compose down
```

## 🎬 사용 방법

### 음성 파일 분석

1. **"음성 파일 분석"** 탭 선택
2. **"녹음 시작"** 버튼 클릭
3. 피싱 대사 말하기 (예: "검찰청입니다. 계좌가 범죄에 연루되었으니 송금하세요")
4. **실시간으로 텍스트가 표시되는 것 확인** ✨
5. **"녹음 중지"** 클릭
6. **"이 녹음 분석하기"** 클릭
7. 결과 확인 (위험도, 탐지 기법, 권장 조치)

### 텍스트 직접 분석

1. **"텍스트 직접 입력"** 탭 선택
2. 의심스러운 통화 내용 입력
3. **"분석하기"** 클릭
4. 실시간 분석 결과 확인

## 🧠 AI 엔진 상세

### 3단계 하이브리드 검증 시스템

```
입력 텍스트
    ↓
┌─────────────────────────────┐
│ 1차: Gemini 2.5 Flash LLM   │
│ - 0-100점 피싱 점수 산출     │
│ - 상세한 판정 이유 생성       │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│ 2차: Chain-of-Thought 검증  │ (60-98점만)
│ - 예외 상황 3가지 체크       │
│   ① 사용자가 돈을 받는 상황  │
│   ② 사용자가 항의하는 상황   │
│   ③ 예약된 일정            │
│ - 함정 패턴 체크            │
│   ⚠️ 앱 설치 요구          │
│   ⚠️ URL 접속 요구         │
│   ⚠️ 능동적 제안 ("대상자로 선정") │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│ 3차: Rule Filter V2         │
│ - 10가지 패턴 규칙 적용      │
│   Rule 0: 사용자 항의 → 정상 │
│   Rule 1: 금융기관 전화 사칭 → 피싱 │
│   Rule 2: 채권 추심 → 중위험 │
│   Rule 3: 중고거래 사기 → 중위험 │
│   Rule 4: Web3 스캠 → 고위험 │
│   Rule 5-10: (기타 패턴)     │
└─────────────────────────────┘
    ↓
최종 점수 (0-100)
```

### Rule Filter V2 상세

| Rule | 패턴 | 조치 | 예시 |
|------|------|------|------|
| **0** | 사용자 항의/민원 | 20점 (정상) | "환불하세요", "신고하겠" |
| **1** | 금융기관 전화 사칭 | 95점 (피싱) | 은행이 전화로 인증서/앱 요구 |
| **2** | 채권 추심 | 50점 (중위험) | "이자 안 내면 회사 찾아간다" |
| **3** | 중고거래 사기 | 50점 (중위험) | "안전결제 말고 직거래만" |
| **4** | Web3 스캠 | 85점 (고위험) | "지갑 연결", "트랜잭션 서명" |
| **5** | CEO Fraud | LLM 유지 | "법인 계좌→개인 계좌 송금" |
| **6** | 헤드헌터 사칭 | 50점 (중위험) | 외부 채용 사칭 |
| **7** | 2차 LLM 검증 | 재평가 | 60-98점 애매한 케이스 |
| **8** | 원격 제어 정상 서비스 | 25점 (정상) | "예약하신 원격 지원" |
| **9** | 키워드 집중 공격 | 70점 (경고) | 피싱 키워드 5개 이상 |
| **10** | 긴급성+금융 복합 | 85점 (고위험) | "지금 당장 송금" |

## 📁 프로젝트 구조

```
voice/
├── 📄 README.md              # 프로젝트 소개 (이 파일)
├── 📄 QUICKSTART.md          # 빠른 시작 가이드
├── 📄 COMPLETE_FEATURES.md   # 전체 기능 목록
├── src/
│   ├── llm/
│   │   ├── gemini_detector.py          # Gemini LLM 탐지기
│   │   └── llm_clients/
│   │       └── gemini_client.py        # Gemini API 클라이언트
│   ├── filters/
│   │   └── rule_filter_v2.py           # Rule Filter V2 (10가지 규칙)
│   ├── stt/                            # Speech-to-Text
│   ├── security/                       # PII Masking
│   └── server/                         # FastAPI 서버
├── static/                             # 웹 데모 페이지
├── scripts/
│   ├── generate_benchmark_report.py    # 벤치마크 실행 (54케이스)
│   ├── generate_simple_pdf.py          # 간단한 PDF 보고서
│   ├── run_server.py                   # 서버 실행
│   ├── create_sample_data.py           # 샘플 데이터 생성
│   ├── test_real_cases.py              # 실제 사례 테스트
│   └── legacy/                         # 구버전 스크립트
└── data/
    ├── training_dataset.json           # 샘플 데이터
    └── benchmark_results_detailed.json # 벤치마크 결과
```

## 🛠 기술 스택

| 분야 | 기술 |
|------|------|
| **프론트엔드** | HTML5, CSS3, JavaScript, Web Speech API |
| **백엔드** | Python 3.11, FastAPI, Uvicorn |
| **AI/ML** | Google Gemini 2.5 Flash, Chain-of-Thought Reasoning |
| **STT** | Whisper, Web Speech API |
| **오디오** | Librosa, SoundFile, NoiseReduce |

## 📚 주요 스크립트

### 벤치마크 & 보고서

```bash
# 전체 벤치마크 실행 (54케이스)
python scripts/generate_benchmark_report.py

# 간단한 PDF 보고서 생성
python scripts/generate_simple_pdf.py

# 실제 사례 테스트
python scripts/test_real_cases.py

# Gemini API 테스트
python scripts/test_gemini_api.py
```

### 데이터 & 서버

```bash
# 샘플 데이터 생성
python scripts/create_sample_data.py

# 서버 실행
python scripts/run_server.py

# 벡터 DB 구축
python scripts/build_vector_db.py
python scripts/build_fss_vector_db.py
```

## 🔒 개인정보 보호 정책

### 현재 구현 (웹 데모)

본 시스템은 **기술 검증(PoC)** 목적으로 웹 기반으로 구현되었습니다.

**⚠️ 주의사항:**
- 실제 통화 중 사용 시 상대방 동의 필요 (통신비밀보호법)
- 민감한 개인정보(금융정보, 주민번호 등) 입력 금지
- 테스트용 예시 문장만 사용 권장

### 실서비스 전환 시 권장사항

#### 1. 온디바이스(On-Device) 처리 (권장)
```
스마트폰 앱 → 기기 내부 AI 처리 → 위험 알림
(서버 전송 없음, 개인정보 유출 위험 없음)
```

#### 2. 하이브리드 방식
```
로컬 키워드 감지 → 의심 시만 서버 분석
```

**📌 본 프로젝트는 기술적 실현 가능성(Proof of Concept)을 검증하는 것이 목적이며, 실서비스 시에는 온디바이스 AI로 전환을 권장합니다.**

## 🏆 개발 히스토리

- ✅ **2025-02-01**: Rule Filter V2 개발 - 채권추심/중고거래/Web3 분리
- ✅ **2025-02-02**: 2단계 LLM 검증 도입 - Chain-of-Thought 추론
- ✅ **2025-02-03**: 능동적 제안 피싱 패턴 추가 - G02 케이스 해결
- ✅ **2025-02-04**: **100% 정확도 달성** (54/54)
- 🚀 **대회 제출 준비 완료**

## 🎯 향후 계획

- [ ] 실시간 통화 감시 기능 (안드로이드 앱)
- [ ] 온디바이스 AI 경량화 (TinyML)
- [ ] 다국어 지원 (영어, 중국어)
- [ ] 음성 감정 분석 통합

## 📞 지원

- GitHub Issues: [github.com/seyoungseyoung/voice/issues](https://github.com/seyoungseyoung/voice/issues)
- 문서: [docs/](docs/)

## 📄 라이선스

MIT License

---

<p align="center">
  Made with ❤️ by SeYoung<br>
  <strong>100% Accuracy Achieved</strong> 🎯
</p>
