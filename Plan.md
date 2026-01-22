[Project Proposal] Sentinel-Voice: 하이브리드 AI 기반 실시간 보이스피싱 탐지 시스템
1. 프로젝트 개요 (Overview)
목표: DACON '피싱·스캠 예방 서비스 개발 경진대회' MVP 출품 및 수상

핵심 컨셉: 통화 음성을 실시간 텍스트화(STT)하고, **하이브리드 NLP 모델(On-device + Cloud)**을 통해 피싱 의도와 맥락을 분석하여 사용자에게 경고하는 보안 솔루션.

차별화 포인트:

단순 키워드 매칭이 아닌 맥락(Context) 기반의 고도화된 탐지.

RAG(검색 증강 생성) 기술을 적용하여 최신 피싱 범죄 사례와 실시간 비교 분석.

Privacy-First: 민감 정보 마스킹 및 온디바이스 처리를 통한 개인정보 보호 강화.

2. 시스템 아키텍처 (System Architecture)
전체 시스템은 **Client(App)**와 **Server(AI Engine)**로 구성되며, Latency(지연 시간) 최소화를 최우선으로 설계함.

Input Layer: 음성 데이터 수집 (Audio Stream) 및 전처리 (Noise Reduction).

STT Layer: OpenAI Whisper (Fine-tuned) 모델을 통해 음성을 텍스트로 변환.

Analysis Layer (The Core):

Level 1 (On-device): 경량화 모델(KoBERT/Llama-3-8B)로 1차 필터링 (속도 중심).

Level 2 (Cloud): 위험 감지 시 ClovaX API 호출 + Vector DB 조회 (정확도 중심).

Output Layer: 위험 스코어(0~100) 산출 및 UI 경고 표시 (진동/팝업).

3. 단계별 세부 실행 계획 (Roadmap)
Phase 1: 데이터 엔지니어링 (Data Engineering)
목표: 피싱 탐지 모델 학습을 위한 고품질 데이터셋 구축.

Data Resources:

[필수] AI Hub: '보이스피싱 음성 데이터', '민원 질의응답 데이터' (약 1만 건 이상 확보 목표).

금융감독원: '그놈 목소리' 체험관의 실제 녹음 파일 크롤링/다운로드.

Action Items:

데이터 정제: 노이즈 제거 및 Speaker Diarization (화자 분리) 적용 (범죄자와 피해자 구분).

라벨링(Labeling): 대화 텍스트에 [접근], [협박], [개인정보요구], [송금유도] 등 단계별 태그 부착.

Vector Database 구축: 최신 피싱 스크립트를 임베딩하여 FAISS 또는 ChromaDB에 저장 (RAG 구현용).

Phase 2: 모델 탐색 및 최적화 (Model Research)
목표: 한국어 특화 STT 및 NLP 모델 선정 및 파이프라인 구축.

Key Tech Stack:

STT: OpenAI Whisper (Large-v3) vs Naver Clova Speech 성능/비용 비교. (한국어 파인튜닝 필수)

LLM:

Main: HyperCLOVA X (복잡한 맥락 추론용).

Local: KoBERT or Solar (실시간 문장 분류용).

Action Items:

Whisper 모델의 한국어 처리 속도(Inference Time) 벤치마킹.

LangChain을 활용하여 STT -> Vector Search -> LLM Prompting으로 이어지는 체인 설계.

Phase 3: 로직 설계 (Logic Design)
목표: 오탐(False Positive)을 줄이고 정탐률을 높이는 알고리즘 구현.

Core Logic:

PII Masking: 서버 전송 전 주민번호, 계좌번호 등 숫자는 [MASK] 처리하는 모듈 개발 (보안 심사 대비).

Risk Scoring Algorithm:

Keyword Score (30%) + Sentiment Score (30%, 다급함/공포 감지) + Similarity Score (40%, 기존 범죄 패턴과의 유사도).

Trigger Condition: 모르는 번호 && 통화 시간 30초 이상 경과 시 분석 시작.

Phase 4: MVP 제작 (Prototyping)
목표: 심사위원 시연용 데모 앱 개발.

Environment:

Frontend: Flutter (빠른 UI 구현) 또는 Native Android (백그라운드 서비스 제어 유리).

Backend: Python FastAPI (AI 모델 서빙).

Demo Scenario:

앱 실행 및 '보호 모드' ON.

가상의 피싱 전화 파일 재생 (스피커).

앱이 실시간으로 대화를 자막으로 띄움.

"검찰" 사칭 및 "송금" 요구 시점애 화면이 붉게 변하며 "경고: 검찰 사칭 피싱 위험 92%" 알림 발생.

4. 필요 리소스 및 환경 (Resources)
Compute:

Google Colab Pro+ 또는 학과 GPU 서버 (모델 학습 및 추론 테스트용).

Local Server (데모 시연 시 노트북 GPU 활용).

API Keys:

Naver Cloud Platform (ClovaX, Clova Speech) - 크레딧 확인 필요.

OpenAI API (Whisper, GPT-4 - 비교군용).

Tools:

Python 3.10+, PyTorch, Hugging Face Transformers.

LangChain, FAISS (Vector DB).