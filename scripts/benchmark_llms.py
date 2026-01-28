"""
LLM Benchmark Test - exam.md 10개 레벨 테스트
모든 LLM이 각 문제를 해결하고 결과를 비교표로 출력
"""
import sys
import os
import io

# Windows console encoding fix
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from src.llm.llm_clients.clovax_client import ClovaXClient
from src.llm.llm_clients.gemini_client import GeminiClient
from src.llm.llm_clients.openai_client import OpenAIClient
from src.llm.llm_clients.deepseek_client import DeepSeekClient
from src.llm.llm_clients.perplexity_client import PerplexityClient
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# 테스트 케이스 (exam.md의 10개 레벨)
test_cases = [
    {
        "level": 1,
        "name": "노골적 위협",
        "text": "야, 서울지검인데 너 대포통장 신고 들어왔어. 지금 당장 가까운 모텔로 튀어와. 안 오면 바로 수배 때린다. 폰 끄지 말고 링크 보내는 거 깔아.",
        "expected_score_min": 90  # 최소 기대 점수
    },
    {
        "level": 2,
        "name": "어설픈 사칭",
        "text": "여기는 중앙지방검찰청입니다. 본인 계좌가 범죄에 연루되어 동결 예정입니다. 보안 검사를 위해 모텔 등 조용한 곳으로 이동해서 '팀뷰어' 어플을 설치하십시오.",
        "expected_score_min": 85
    },
    {
        "level": 3,
        "name": "전형적인 시나리오",
        "text": "김철수 검사입니다. 수사 기밀 유지를 위해 제3자가 없는 독립된 공간이 필요합니다. 주변 소음이 섞이면 녹취가 증거로 채택이 안 됩니다. 근처 숙박업소로 이동하시고, 비대면 조사를 위한 보안 앱을 설치해주세요.",
        "expected_score_min": 85
    },
    {
        "level": 4,
        "name": "피해자 구제 빙자",
        "text": "선생님, 지금 선생님이 피의자가 아니라 피해자 입장이신 걸 소명하려는 겁니다. 다만, 녹취 중에 주변 잡음이나 타인의 목소리가 섞이면 증거 효력이 사라져요. 그래서 댁보다는 방음이 확실한 스터디룸이나 비즈니스 호텔을 권장 드리는 겁니다.",
        "expected_score_min": 75
    },
    {
        "level": 5,
        "name": "기술적 지원 위장",
        "text": "지금 폰이 해킹된 상태라 위치 추적이 되고 있어요. 댁으로 가시면 범인들이 알 수 있습니다. 일단 공공 와이파이가 없는 안전한 장소로 피신하셔야 하고요, 해킹 차단을 위해 한국인터넷진흥원(KISA) 인증 툴을 보내드릴 테니 실행해주세요.",
        "expected_score_min": 75
    },
    {
        "level": 6,
        "name": "금융감독원 사칭",
        "text": "금융감독원 자산보호팀입니다. 현재 자금이 해외로 빠져나가고 있어 지급정지 요청을 해야 하는데, 본인 인증이 계속 실패하네요. 통신 보안이 확실한 곳에서 대기해주시면, 저희가 원격으로 '금융 보안 모듈'을 재설정해 드리겠습니다.",
        "expected_score_min": 70
    },
    {
        "level": 7,
        "name": "가족 사칭 결합",
        "text": "아버님, 저 김 대리입니다. 아까 따님이 사고 합의 건으로 급하게 연락 주셨는데, 지금 상대방 보험사 직원이랑 대화 내용을 녹음해야 해요. 주변이 시끄러우면 안 되니까 조용한 방 잡고 계시면, 제가 보내드리는 '보험사 전용 녹취 앱' 켜두세요. 따님 바꿔드릴게요.",
        "expected_score_min": 70
    },
    {
        "level": 8,
        "name": "재택근무/면접 위장",
        "text": "안녕하세요, OO기업 인사팀입니다. 1차 합격 축하드립니다. 2차는 AI 역량 검사로 진행되는데요, 부정행위 방지를 위해 독립된 공간(숙박 시설 등)에서 360도 카메라 세팅이 필요합니다. 보내드리는 '시험 감독 프로그램' 설치 후 응시 부탁드립니다.",
        "expected_score_min": 65
    },
    {
        "level": 9,
        "name": "가짜 백신 프로그램",
        "text": "고객님, OO카드 FDS(이상거래탐지)팀입니다. 지금 고객님 폰에 악성코드가 심어져서 계속 결제 시도가 들어옵니다. 저희가 이걸 막으려면 '백신'을 업데이트해야 하는데, 데이터가 손실될 수 있으니 이동하지 마시고 한자리에서 와이파이 끄고 진행해 주세요.",
        "expected_score_min": 65
    },
    {
        "level": 10,
        "name": "복합적인 사회공학 기법",
        "text": "네, 고객님. 불편 드려 죄송합니다. 최근 딥보이스 범죄가 늘어나서, 본인 확인 절차가 강화되었습니다. 현재 고객님 목소리의 생체 파형(Voice Print)을 등록해야 계좌 잠금이 풀리는데요, 이게 미세한 소음에도 오류가 납니다. 번거로우시겠지만, 지금 계신 카페는 소음 수치가 높아서 진행이 불가능합니다. 근처에 공유 오피스나 조용한 숙소 같은 곳을 잠시 이용해 주실 수 있을까요? 이동하시는 동안 통화가 끊기면 초기화되니 유지해 주시고요. 도착하시면 저희 은행 보안 팀에서 보내는 '생체 인증 플러그인'만 수락해 주시면 됩니다.",
        "expected_score_min": 60
    },
    # === FALSE POSITIVE 테스트 (정상 케이스) ===
    {
        "level": 11,
        "name": "[정상] 비대면 심리 상담",
        "text": "안녕하세요, OO정신건강의학과입니다. 예약하신 비대면 진료 시간 되셔서 연락드렸습니다. 진료 내용에 민감한 개인 정보가 포함될 수 있으니, 지금 주변에 사람이 없는 조용한 방이나 독립된 공간으로 이동해 주실 수 있나요? 카페나 공공장소시면 진료가 어렵습니다. 준비되시면 카카오톡으로 보내드린 '닥터나우(또는 줌)' 링크 눌러서 화상 진료실로 입장해 주세요.",
        "expected_score_min": 0,  # 낮을수록 좋음 (정상 케이스)
        "expected_score_max": 30  # 30점 이하여야 정답
    },
    {
        "level": 12,
        "name": "[정상] 가전제품 원격 지원",
        "text": "고객님, 말씀하신 와이파이 끊김 현상은 설정 충돌 문제로 보입니다. 제가 고객님 휴대폰 화면을 보면서 설정을 좀 잡아드려야 할 것 같은데요. 휴대폰 기본 설정 메뉴에 보시면 '원격 상담' 기능이 있습니다. 그거 누르시고 화면에 뜨는 6자리 접속 번호를 저한테 불러주시겠어요? 연결되면 제가 화면을 제어하면서 해결해 드리겠습니다.",
        "expected_score_min": 0,
        "expected_score_max": 30
    },
    {
        "level": 13,
        "name": "[정상] 기업 채용 AI 역량 검사",
        "text": "안녕하세요, OO그룹 인사팀 채용 담당자입니다. 서류 합격 축하드립니다. 내일부터 진행되는 온라인 AI 역량 검사 관련해서 안내 전화 드렸습니다. 부정행위 방지를 위해서 반드시 혼자 계신 공간에서 응시하셔야 하고요, 웹캠으로 주변 360도를 비춰주셔야 합니다. 시험 프로그램은 저희 채용 홈페이지 '마이페이지'에서 다운로드 가능하시니까 미리 설치하고 테스트 부탁드립니다.",
        "expected_score_min": 0,
        "expected_score_max": 30
    }
]

# 간단한 프롬프트 (맥락 분석 기준)
ANALYSIS_PROMPT = """당신은 보이스피싱 탐지 전문가입니다. 다음 통화 내용을 분석하세요.

**분석 기준:**
1. 공공기관/기업 사칭 여부
2. 장소 이동 요구 (모텔, 독립 공간, 조용한 곳 등)
3. 앱 설치 유도 (원격 제어, 보안 앱, 플러그인 등)
4. 심리적 압박 (긴급성, 위협, 불안 조성)
5. 고립 유도 (주변인 차단, 통화 유지 요구)

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
            "level": test_case["level"],
            "model": llm_client.model_name,
            "score": result.get("score", 0),
            "is_phishing": result.get("is_phishing", False),
            "reasoning": result.get("reasoning", "N/A")[:100]  # 100자로 제한
        }
    except Exception as e:
        return {
            "level": test_case["level"],
            "model": llm_client.model_name,
            "score": 0,
            "is_phishing": False,
            "reasoning": f"Error: {str(e)[:50]}"
        }


def main():
    print("\n" + "="*100)
    print("🔬 LLM 벤치마크 테스트 - exam.md 10개 레벨")
    print("="*100 + "\n")

    # LLM 클라이언트 초기화
    clients = {
        "Gemini": GeminiClient(),
        "GPT": OpenAIClient(),
        "DeepSeek": DeepSeekClient(),
        "Perplexity": PerplexityClient()
    }

    # ClovaX는 GATEWAY_KEY 필요
    clovax = ClovaXClient()
    if clovax.is_available():
        clients["ClovaX"] = clovax

    # 사용 가능한 LLM만 필터
    available_clients = {name: client for name, client in clients.items() if client.is_available()}

    if not available_clients:
        print("❌ 사용 가능한 LLM이 없습니다. .env 파일에 API 키를 설정하세요.")
        return

    print(f"✅ 사용 가능한 LLM: {', '.join(available_clients.keys())}\n")

    # 결과 저장
    all_results = []

    # 모든 테스트 케이스 실행
    for test_case in test_cases:
        print(f"[Level {test_case['level']}] {test_case['name']} 테스트 중...")

        # 모든 LLM 병렬 실행
        with ThreadPoolExecutor(max_workers=5) as executor:
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
                if "expected_score_max" in test_case:
                    status = "✅" if score <= test_case["expected_score_max"] else "❌"
                else:
                    status = "✅" if score >= test_case["expected_score_min"] else "❌"
                print(f"  {status} {llm_name}: {score}점")

        time.sleep(1)  # API 레이트 리밋 방지

    # 결과 집계
    print("\n" + "="*100)
    print("📊 최종 결과 비교표")
    print("="*100 + "\n")

    # 헤더
    llm_names = list(available_clients.keys())
    header = f"{'Level':<8} {'문제 유형':<25}"
    for name in llm_names:
        header += f" {name:<12}"
    print(header)
    print("-"*100)

    # 각 레벨별 점수 출력
    for test_case in test_cases:
        level = test_case["level"]
        name = test_case["name"]
        row = f"{level:<8} {name:<25}"

        for llm_name in llm_names:
            # 해당 LLM의 해당 레벨 점수 찾기
            result = next((r for r in all_results if r["level"] == level and r["model"] == available_clients[llm_name].model_name), None)
            if result:
                score = result["score"]
                row += f" {score:<12}"
            else:
                row += f" {'N/A':<12}"

        print(row)

    # 합산 점수
    print("-"*100)
    total_row = f"{'합계':<8} {'(1000점 만점)':<25}"
    for llm_name in llm_names:
        model_name = available_clients[llm_name].model_name
        total = sum(r["score"] for r in all_results if r["model"] == model_name)
        total_row += f" {total:<12}"
    print(total_row)

    # 평균 점수
    avg_row = f"{'평균':<8} {'(100점 만점)':<25}"
    for llm_name in llm_names:
        model_name = available_clients[llm_name].model_name
        scores = [r["score"] for r in all_results if r["model"] == model_name]
        avg = round(sum(scores) / len(scores), 2) if scores else 0
        avg_row += f" {avg:<12}"
    print(avg_row)

    print("="*100)

    # 가장 높은 점수의 LLM
    total_scores = {}
    for llm_name in llm_names:
        model_name = available_clients[llm_name].model_name
        total_scores[llm_name] = sum(r["score"] for r in all_results if r["model"] == model_name)

    best_llm = max(total_scores, key=total_scores.get)
    print(f"\n🏆 최고 성능: {best_llm} ({total_scores[best_llm]}점)")

    # 레벨별 최고 점수
    print("\n📈 레벨별 최고 점수:")
    for test_case in test_cases:
        level = test_case["level"]
        level_results = [r for r in all_results if r["level"] == level]
        best_result = max(level_results, key=lambda x: x["score"])
        print(f"  Level {level} ({test_case['name']}): {best_result['model']} - {best_result['score']}점")

    print("\n✅ 벤치마크 테스트 완료!")


if __name__ == "__main__":
    main()
