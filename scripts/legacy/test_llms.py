"""
LLM 연결 테스트 - 모든 LLM이 정상 작동하는지 확인
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

from src.llm.llm_clients.gemini_client import GeminiClient
from src.llm.llm_clients.openai_client import OpenAIClient
from src.llm.llm_clients.deepseek_client import DeepSeekClient
from src.llm.llm_clients.perplexity_client import PerplexityClient

# 간단한 테스트 프롬프트
TEST_PROMPT = """다음 문장의 위험도를 0-100 점수로 평가하세요.

**응답 형식 (JSON):**
{
  "score": <0-100 정수>,
  "reasoning": "<간략한 이유>"
}

JSON:"""

TEST_TEXT = "안녕하세요, 은행입니다. 계좌가 해킹되어서 보안 앱을 설치하세요."

def test_client(name, client):
    """개별 LLM 테스트"""
    print(f"\n[{name}]")
    print("-" * 60)

    if not client.is_available():
        print(f"❌ API 키가 설정되지 않았습니다.")
        return False

    print(f"✓ API 키 확인")
    print(f"✓ 모델: {client.model_name}")

    try:
        print(f"⏳ API 호출 테스트 중...")
        result = client.analyze_phishing(TEST_TEXT, TEST_PROMPT)

        score = result.get("score", 0)
        reasoning = result.get("reasoning", "N/A")

        print(f"✅ 성공!")
        print(f"   점수: {score}/100")
        print(f"   분석: {reasoning[:80]}")
        return True

    except Exception as e:
        print(f"❌ 실패: {str(e)[:100]}")
        return False


def main():
    print("="*60)
    print("🔬 LLM 연결 테스트")
    print("="*60)

    clients = {
        "Gemini 2.5 Pro": GeminiClient(),
        "GPT-4o": OpenAIClient(),
        "DeepSeek V3": DeepSeekClient(),
        "Perplexity Sonar": PerplexityClient()
    }

    results = {}
    for name, client in clients.items():
        results[name] = test_client(name, client)

    # 최종 결과
    print("\n" + "="*60)
    print("📊 최종 결과")
    print("="*60)

    for name, success in results.items():
        status = "✅ 작동" if success else "❌ 오류"
        print(f"{name:<25} {status}")

    working_count = sum(1 for s in results.values() if s)
    total_count = len(results)

    print("="*60)
    print(f"총 {working_count}/{total_count} LLM 정상 작동")
    print("="*60)


if __name__ == "__main__":
    main()
