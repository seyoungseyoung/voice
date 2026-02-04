"""
Comprehensive LLM Benchmark - exam.md 전체 케이스
23개 케이스: 피싱 20개 + 정상 3개
"""
import sys
import os
import io

# Windows console encoding fix
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from src.llm.clovax_client import ClovaXClient
from src.llm.llm_clients.gemini_client import GeminiClient
from src.llm.llm_clients.openai_client import OpenAIClient
from src.llm.llm_clients.deepseek_client import DeepSeekClient
from src.llm.llm_clients.perplexity_client import PerplexityClient
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# === CATEGORY A: 전통적 보이스피싱 (Level 1-10) ===
traditional_phishing = [
    {
        "id": "A01",
        "level": 1,
        "category": "전통적 보이스피싱",
        "name": "노골적 위협",
        "text": "야, 서울지검인데 너 대포통장 신고 들어왔어. 지금 당장 가까운 모텔로 튀어와. 안 오면 바로 수배 때린다. 폰 끄지 말고 링크 보내는 거 깔아.",
        "expected_min": 90,
        "is_phishing": True
    },
    {
        "id": "A02",
        "level": 2,
        "category": "전통적 보이스피싱",
        "name": "어설픈 사칭",
        "text": "여기는 중앙지방검찰청입니다. 본인 계좌가 범죄에 연루되어 동결 예정입니다. 보안 검사를 위해 모텔 등 조용한 곳으로 이동해서 '팀뷰어' 어플을 설치하십시오.",
        "expected_min": 85,
        "is_phishing": True
    },
    {
        "id": "A03",
        "level": 3,
        "category": "전통적 보이스피싱",
        "name": "전형적인 시나리오",
        "text": "김철수 검사입니다. 수사 기밀 유지를 위해 제3자가 없는 독립된 공간이 필요합니다. 주변 소음이 섞이면 녹취가 증거로 채택이 안 됩니다. 근처 숙박업소로 이동하시고, 비대면 조사를 위한 보안 앱을 설치해주세요.",
        "expected_min": 85,
        "is_phishing": True
    },
    {
        "id": "A04",
        "level": 4,
        "category": "전통적 보이스피싱",
        "name": "피해자 구제 빙자",
        "text": "선생님, 지금 선생님이 피의자가 아니라 피해자 입장이신 걸 소명하려는 겁니다. 다만, 녹취 중에 주변 잡음이나 타인의 목소리가 섞이면 증거 효력이 사라져요. 그래서 댁보다는 방음이 확실한 스터디룸이나 비즈니스 호텔을 권장 드리는 겁니다.",
        "expected_min": 75,
        "is_phishing": True
    },
    {
        "id": "A05",
        "level": 5,
        "category": "전통적 보이스피싱",
        "name": "기술적 지원 위장",
        "text": "지금 폰이 해킹된 상태라 위치 추적이 되고 있어요. 댁으로 가시면 범인들이 알 수 있습니다. 일단 공공 와이파이가 없는 안전한 장소로 피신하셔야 하고요, 해킹 차단을 위해 한국인터넷진흥원(KISA) 인증 툴을 보내드릴 테니 실행해주세요.",
        "expected_min": 75,
        "is_phishing": True
    },
    {
        "id": "A06",
        "level": 6,
        "category": "전통적 보이스피싱",
        "name": "금융감독원 사칭",
        "text": "금융감독원 자산보호팀입니다. 현재 자금이 해외로 빠져나가고 있어 지급정지 요청을 해야 하는데, 본인 인증이 계속 실패하네요. 통신 보안이 확실한 곳에서 대기해주시면, 저희가 원격으로 '금융 보안 모듈'을 재설정해 드리겠습니다.",
        "expected_min": 70,
        "is_phishing": True
    },
    {
        "id": "A07",
        "level": 7,
        "category": "전통적 보이스피싱",
        "name": "가족 사칭 결합",
        "text": "아버님, 저 김 대리입니다. 아까 따님이 사고 합의 건으로 급하게 연락 주셨는데, 지금 상대방 보험사 직원이랑 대화 내용을 녹음해야 해요. 주변이 시끄러우면 안 되니까 조용한 방 잡고 계시면, 제가 보내드리는 '보험사 전용 녹취 앱' 켜두세요. 따님 바꿔드릴게요.",
        "expected_min": 70,
        "is_phishing": True
    },
    {
        "id": "A08",
        "level": 8,
        "category": "전통적 보이스피싱",
        "name": "재택근무/면접 위장",
        "text": "안녕하세요, OO기업 인사팀입니다. 1차 합격 축하드립니다. 2차는 AI 역량 검사로 진행되는데요, 부정행위 방지를 위해 독립된 공간(숙박 시설 등)에서 360도 카메라 세팅이 필요합니다. 보내드리는 '시험 감독 프로그램' 설치 후 응시 부탁드립니다.",
        "expected_min": 65,
        "is_phishing": True
    },
    {
        "id": "A09",
        "level": 9,
        "category": "전통적 보이스피싱",
        "name": "가짜 백신 프로그램",
        "text": "고객님, OO카드 FDS(이상거래탐지)팀입니다. 지금 고객님 폰에 악성코드가 심어져서 계속 결제 시도가 들어옵니다. 저희가 이걸 막으려면 '백신'을 업데이트해야 하는데, 데이터가 손실될 수 있으니 이동하지 마시고 한자리에서 와이파이 끄고 진행해 주세요.",
        "expected_min": 65,
        "is_phishing": True
    },
    {
        "id": "A10",
        "level": 10,
        "category": "전통적 보이스피싱",
        "name": "복합적인 사회공학 기법",
        "text": "네, 고객님. 불편 드려 죄송합니다. 최근 딥보이스 범죄가 늘어나서, 본인 확인 절차가 강화되었습니다. 현재 고객님 목소리의 생체 파형(Voice Print)을 등록해야 계좌 잠금이 풀리는데요, 이게 미세한 소음에도 오류가 납니다. 번거로우시겠지만, 지금 계신 카페는 소음 수치가 높아서 진행이 불가능합니다. 근처에 공유 오피스나 조용한 숙소 같은 곳을 잠시 이용해 주실 수 있을까요? 이동하시는 동안 통화가 끊기면 초기화되니 유지해 주시고요. 도착하시면 저희 은행 보안 팀에서 보내는 '생체 인증 플러그인'만 수락해 주시면 됩니다.",
        "expected_min": 60,
        "is_phishing": True
    }
]

# === CATEGORY B: 정상 케이스 (False Positive 테스트) ===
legitimate_cases = [
    {
        "id": "B01",
        "level": 11,
        "category": "정상 케이스",
        "name": "[정상] 비대면 심리 상담",
        "text": "안녕하세요, OO정신건강의학과입니다. 예약하신 비대면 진료 시간 되셔서 연락드렸습니다. 진료 내용에 민감한 개인 정보가 포함될 수 있으니, 지금 주변에 사람이 없는 조용한 방이나 독립된 공간으로 이동해 주실 수 있나요? 카페나 공공장소시면 진료가 어렵습니다. 준비되시면 카카오톡으로 보내드린 '닥터나우(또는 줌)' 링크 눌러서 화상 진료실로 입장해 주세요.",
        "expected_max": 30,
        "is_phishing": False
    },
    {
        "id": "B02",
        "level": 12,
        "category": "정상 케이스",
        "name": "[정상] 가전제품 원격 지원",
        "text": "고객님, 말씀하신 와이파이 끊김 현상은 설정 충돌 문제로 보입니다. 제가 고객님 휴대폰 화면을 보면서 설정을 좀 잡아드려야 할 것 같은데요. 휴대폰 기본 설정 메뉴에 보시면 '원격 상담' 기능이 있습니다. 그거 누르시고 화면에 뜨는 6자리 접속 번호를 저한테 불러주시겠어요? 연결되면 제가 화면을 제어하면서 해결해 드리겠습니다.",
        "expected_max": 30,
        "is_phishing": False
    },
    {
        "id": "B03",
        "level": 13,
        "category": "정상 케이스",
        "name": "[정상] 기업 채용 AI 역량 검사",
        "text": "안녕하세요, OO그룹 인사팀 채용 담당자입니다. 서류 합격 축하드립니다. 내일부터 진행되는 온라인 AI 역량 검사 관련해서 안내 전화 드렸습니다. 부정행위 방지를 위해서 반드시 혼자 계신 공간에서 응시하셔야 하고요, 웹캠으로 주변 360도를 비춰주셔야 합니다. 시험 프로그램은 저희 채용 홈페이지 '마이페이지'에서 다운로드 가능하시니까 미리 설치하고 테스트 부탁드립니다.",
        "expected_max": 30,
        "is_phishing": False
    }
]

# === CATEGORY C: URL 기반 피싱 (가짜 사이트) ===
url_based_phishing = [
    {
        "id": "C01",
        "level": 14,
        "category": "URL 기반 피싱",
        "name": "대법원 사건 검색 위장",
        "text": "본인 사건이 맞는지 직접 확인해보세요. 인터넷 주소창에 scourt-law.com 입력하시면 대법원 형사 사법 포털 나옵니다. 거기서 '사건 조회' 누르시고 성함 입력해 보세요. 판결문 자세히 보시려면 보안 뷰어(Viewer) 설치하라고 뜨죠? 그거 설치하세요.",
        "expected_min": 70,
        "is_phishing": True
    },
    {
        "id": "C02",
        "level": 15,
        "category": "URL 기반 피싱",
        "name": "검찰청 비대면 조사 위장",
        "text": "바쁘시니까 서울중앙지검 홈페이지(spo-invest.net) 접속하셔서 '비대면 조사실' 배너 클릭하세요. 공인인증서 대신 '수사기관용 본인확인 앱'으로 로그인하셔야 합니다.",
        "expected_min": 75,
        "is_phishing": True
    },
    {
        "id": "C03",
        "level": 16,
        "category": "URL 기반 피싱",
        "name": "금융감독원 계좌 동결 위장",
        "text": "지금 계좌가 1시간 뒤에 동결됩니다. 금융감독원 민원 포털(fss-secure.co.kr) 들어가셔서 '불법 계좌 해제 신청' 누르세요. 거기서 하라는 대로 보안 프로그램 업데이트하셔야 동결 막습니다.",
        "expected_min": 75,
        "is_phishing": True
    },
    {
        "id": "C04",
        "level": 17,
        "category": "URL 기반 피싱",
        "name": "국세청 환급금 위장",
        "text": "고객님, 국세청입니다. 2024년도 미환급 세액 320만 원이 조회되시는데 신청이 안 되어 있어서요. 모바일 홈택스 주소 보내드릴게요(hometax-refund.info). 여기 접속해서 '환급 신청서' 다운받아 작성해서 다시 올리세요.",
        "expected_min": 70,
        "is_phishing": True
    },
    {
        "id": "C05",
        "level": 18,
        "category": "URL 기반 피싱",
        "name": "질병관리청 건강검진 위장",
        "text": "건강검진센터입니다. 이번 검사 결과에서 중대한 이상 소견이 발견되어 정밀 검사가 필요합니다. 자세한 수치는 의료 포털(health-check.kr)에서 결과지 조회해 보세요. 결과지 확인 버튼 누르면 의료 정보 암호화 모듈 설치 필요 팝업 뜰 겁니다.",
        "expected_min": 65,
        "is_phishing": True
    },
    {
        "id": "C06",
        "level": 19,
        "category": "URL 기반 피싱",
        "name": "한국장학재단 장학금 소명",
        "text": "한국장학재단입니다. 부모님 소득 정보 오류로 장학금 환수 대상이 되셨어요. 이의 신청하시려면 재단 사이트(kosaf-support.com) 가셔서 증빙 서류 제출 앱을 까셔야 합니다.",
        "expected_min": 70,
        "is_phishing": True
    },
    {
        "id": "C07",
        "level": 20,
        "category": "URL 기반 피싱",
        "name": "은행 대환 대출 위장",
        "text": "정부 지원 '햇살론' 대상자로 선정되셨습니다. 기존 고금리 대출을 3%대로 대환해 드립니다. KB국민은행 특판 사이트(kb-loancenter.net)에서 한도 조회하고 신청 앱 설치하세요.",
        "expected_min": 65,
        "is_phishing": True
    },
    {
        "id": "C08",
        "level": 21,
        "category": "URL 기반 피싱",
        "name": "택배 오배송 위장",
        "text": "[CJ대한통운] 운송장 번호 450-*** 주소지 불명으로 반송 대기 중. 실시간 주소지 수정: cj-logistics-help.com 본인 확인을 위해 휴대폰 번호를 입력하고 인증 앱을 설치하세요.",
        "expected_min": 60,
        "is_phishing": True
    },
    {
        "id": "C09",
        "level": 22,
        "category": "URL 기반 피싱",
        "name": "가상화폐 거래소 위장",
        "text": "업비트 보안팀입니다. 미국에서 로그인이 시도되어 출금이 제한됐습니다. 해제하시려면 전용 보안 페이지(upbit-security.org)에서 OTP 재설정 앱을 다운로드하셔야 합니다.",
        "expected_min": 70,
        "is_phishing": True
    },
    {
        "id": "C10",
        "level": 23,
        "category": "URL 기반 피싱",
        "name": "사이버수사국 2차 피해",
        "text": "사이버수사대입니다. 지난번 신고하신 사기 피해금 찾았습니다. 환급 절차 밟으시려면 경찰청 사이버 안전국(cyber-police.me) 접속하셔서 '피해 구제 신청서' 작성하세요.",
        "expected_min": 70,
        "is_phishing": True
    }
]

# 모든 케이스 통합
all_test_cases = traditional_phishing + legitimate_cases + url_based_phishing

# 분석 프롬프트
ANALYSIS_PROMPT = """당신은 보이스피싱 탐지 전문가입니다. 다음 통화 내용을 분석하세요.

**분석 기준:**
1. 공공기관/기업 사칭 여부
2. 장소 이동 요구 (모텔, 독립 공간, 조용한 곳 등)
3. 앱 설치 유도 (원격 제어, 보안 앱, 플러그인 등)
4. 심리적 압박 (긴급성, 위협, 불안 조성)
5. 고립 유도 (주변인 차단, 통화 유지 요구)
6. **가짜 URL** (.com, .net 등 비공식 도메인)
7. **정상 케이스 식별**: 예약된 일정, 공식 홈페이지 안내, 합리적 목적

**중요: 정상 케이스 vs 피싱 구분**
- 정상: 사전 예약, 공식 채널, 기기 기본 기능, 사용자 요청에 응답
- 피싱: 갑작스런 연락, 비공식 URL, 외부 앱 설치, 긴급성 강요

**응답 형식 (JSON):**
{
  "score": <0-100 정수, 피싱 위험도>,
  "is_phishing": <true/false>,
  "reasoning": "<간략한 판단 근거 1-2문장>"
}

JSON:"""


def test_llm(llm_client, test_case):
    """단일 LLM 테스트"""
    try:
        result = llm_client.analyze_phishing(test_case["text"], ANALYSIS_PROMPT)
        return {
            "id": test_case["id"],
            "model": llm_client.model_name,
            "score": result.get("score", 0),
            "is_phishing": result.get("is_phishing", False),
            "reasoning": result.get("reasoning", "N/A")[:80]
        }
    except Exception as e:
        return {
            "id": test_case["id"],
            "model": llm_client.model_name,
            "score": 0,
            "is_phishing": False,
            "reasoning": f"Error: {str(e)[:50]}"
        }


def main():
    print("\n" + "="*120)
    print("🔬 포괄적 LLM 벤치마크 - exam.md 전체 23개 케이스")
    print("="*120)
    print(f"Category A: 전통적 보이스피싱 (10개)")
    print(f"Category B: 정상 케이스 (3개) - False Positive 테스트")
    print(f"Category C: URL 기반 피싱 (10개) - 가짜 사이트 위장")
    print("="*120 + "\n")

    # LLM 클라이언트 초기화
    clients = {
        "Gemini": GeminiClient(),
        "GPT": OpenAIClient(),
        "DeepSeek": DeepSeekClient(),
        "Perplexity": PerplexityClient()
    }

    # 사용 가능한 LLM만 필터
    available_clients = {name: client for name, client in clients.items() if client.is_available()}

    if not available_clients:
        print("❌ 사용 가능한 LLM이 없습니다. .env 파일에 API 키를 설정하세요.")
        return

    print(f"✅ 사용 가능한 LLM: {', '.join(available_clients.keys())}\n")

    # 결과 저장
    all_results = []

    # 카테고리별로 테스트
    for category_name, cases in [
        ("A. 전통적 보이스피싱", traditional_phishing),
        ("B. 정상 케이스", legitimate_cases),
        ("C. URL 기반 피싱", url_based_phishing)
    ]:
        print(f"\n{'='*120}")
        print(f"📂 {category_name}")
        print(f"{'='*120}\n")

        for test_case in cases:
            print(f"[{test_case['id']}] {test_case['name']} 테스트 중...")

            # 모든 LLM 병렬 실행
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(test_llm, client, test_case): llm_name
                    for llm_name, client in available_clients.items()
                }

                for future in as_completed(futures):
                    result = future.result()
                    all_results.append(result)
                    llm_name = futures[future]
                    score = result["score"]

                    # 정상 케이스는 낮은 점수가 좋음
                    if "expected_max" in test_case:
                        status = "✅" if score <= test_case["expected_max"] else "❌"
                    else:
                        status = "✅" if score >= test_case["expected_min"] else "❌"

                    print(f"  {status} {llm_name}: {score}점")

            time.sleep(1)  # API 레이트 리밋 방지

    # ===== 결과 집계 =====
    print("\n" + "="*120)
    print("📊 최종 결과 분석")
    print("="*120 + "\n")

    # 1. LLM별 종합 점수
    llm_scores = {name: {"total": 0, "correct": 0, "total_cases": 0} for name in available_clients.keys()}

    for result in all_results:
        model_name = result["model"]
        for llm_name, client in available_clients.items():
            if client.model_name == model_name:
                llm_scores[llm_name]["total_cases"] += 1

                # 해당 케이스 찾기
                test_case = next((tc for tc in all_test_cases if tc["id"] == result["id"]), None)
                if test_case:
                    # 정답 판정
                    if "expected_max" in test_case:
                        is_correct = result["score"] <= test_case["expected_max"]
                    else:
                        is_correct = result["score"] >= test_case["expected_min"]

                    if is_correct:
                        llm_scores[llm_name]["correct"] += 1
                        llm_scores[llm_name]["total"] += 100
                break

    # 2. 결과 출력
    print(f"{'LLM':<15} {'정답률':<15} {'평균 점수':<15}")
    print("-"*120)

    for llm_name in sorted(llm_scores.keys(), key=lambda x: llm_scores[x]["correct"], reverse=True):
        stats = llm_scores[llm_name]
        accuracy = (stats["correct"] / stats["total_cases"]) * 100 if stats["total_cases"] > 0 else 0
        avg_score = stats["total"] / stats["total_cases"] if stats["total_cases"] > 0 else 0

        print(f"{llm_name:<15} {accuracy:>5.1f}% ({stats['correct']}/{stats['total_cases']}){'':<5} {avg_score:>5.1f}/100")

    print("="*120)

    # 3. 카테고리별 성능
    print("\n📈 카테고리별 성능 분석\n")

    categories = {
        "A": "전통적 보이스피싱",
        "B": "정상 케이스 (FP 테스트)",
        "C": "URL 기반 피싱"
    }

    for cat_id, cat_name in categories.items():
        print(f"\n[{cat_id}] {cat_name}")
        print("-"*60)

        for llm_name in available_clients.keys():
            cat_results = [r for r in all_results if r["id"].startswith(cat_id) and
                          any(c.model_name == r["model"] for name, c in available_clients.items() if name == llm_name)]

            if cat_results:
                cat_correct = 0
                for result in cat_results:
                    test_case = next((tc for tc in all_test_cases if tc["id"] == result["id"]), None)
                    if test_case:
                        if "expected_max" in test_case:
                            if result["score"] <= test_case["expected_max"]:
                                cat_correct += 1
                        else:
                            if result["score"] >= test_case["expected_min"]:
                                cat_correct += 1

                cat_accuracy = (cat_correct / len(cat_results)) * 100 if cat_results else 0
                print(f"  {llm_name:<15} {cat_accuracy:>5.1f}% ({cat_correct}/{len(cat_results)})")

    print("\n" + "="*120)
    print("✅ 포괄적 벤치마크 테스트 완료!")
    print("="*120)


if __name__ == "__main__":
    main()
