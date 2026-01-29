"""
Multi-LLM Ensemble System
5개 LLM (ClovaX, Gemini, GPT, DeepSeek, Perplexity)을 비교하여 최종 판정
"""
import logging
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

try:
    from .clovax_client import ClovaXClient
except ImportError:
    ClovaXClient = None

from .llm_clients.gemini_client import GeminiClient
from .llm_clients.openai_client import OpenAIClient
from .llm_clients.deepseek_client import DeepSeekClient
from .llm_clients.perplexity_client import PerplexityClient

logger = logging.getLogger(__name__)


class MultiLLMEnsemble:
    """
    5개 LLM을 동시에 실행하여 비교 분석
    """

    def __init__(self):
        self.clients = {
            "Gemini": GeminiClient(),
            "GPT": OpenAIClient(),
            "DeepSeek": DeepSeekClient(),
            "Perplexity": PerplexityClient()
        }
        
        if ClovaXClient:
            self.clients["ClovaX"] = ClovaXClient()

        # 사용 가능한 LLM 확인
        self.available_llms = {
            name: client for name, client in self.clients.items()
            if client.is_available()
        }

        if not self.available_llms:
            logger.warning("⚠️ No LLM API keys configured!")
        else:
            logger.info(f"✓ {len(self.available_llms)} LLMs available: {', '.join(self.available_llms.keys())}")

    def is_available(self) -> bool:
        return len(self.available_llms) > 0

    def analyze(
        self,
        conversation_text: str,
        similar_cases: Optional[List[Tuple[str, float, Dict]]] = None
    ) -> Dict:
        """
        모든 LLM을 동시 실행하여 비교 분석
        """
        if not self.is_available():
            return self._fallback_result()

        try:
            # FSS 사례 컨텍스트 생성
            similar_context = self._format_similar_cases(similar_cases)

            # 3가지 Agent 프롬프트 (multi_agent_detector.py와 동일)
            prompts = {
                "context": self._get_context_prompt(conversation_text, similar_context),
                "psychological": self._get_psychological_prompt(conversation_text),
                "financial": self._get_financial_prompt(conversation_text)
            }

            logger.info(f"🤖 Running {len(self.available_llms)} LLMs × 3 agents = {len(self.available_llms) * 3} analyses...")

            # 모든 LLM × 모든 Agent를 병렬 실행
            all_results = {}
            with ThreadPoolExecutor(max_workers=15) as executor:
                futures = {}

                for llm_name, client in self.available_llms.items():
                    for agent_name, prompt in prompts.items():
                        future = executor.submit(
                            client.analyze_phishing,
                            conversation_text,
                            prompt
                        )
                        futures[future] = (llm_name, agent_name)

                # 결과 수집
                for future in as_completed(futures):
                    llm_name, agent_name = futures[future]
                    try:
                        result = future.result(timeout=35)
                        key = f"{llm_name}_{agent_name}"
                        all_results[key] = result
                        logger.debug(f"✓ {llm_name} {agent_name}: {result.get('score', 0)}")
                    except Exception as e:
                        logger.error(f"✗ {llm_name} {agent_name} failed: {e}")

            # 결과 분석 및 비교
            comparison = self._compare_results(all_results)

            logger.info(f"✓ Ensemble complete: {comparison['ensemble_score']}/100")
            return comparison

        except Exception as e:
            logger.error(f"Ensemble analysis failed: {e}")
            return self._fallback_result()

    def _format_similar_cases(self, similar_cases: Optional[List[Tuple[str, float, Dict]]]) -> str:
        """FSS 사례 포맷"""
        if not similar_cases or len(similar_cases) == 0:
            return "유사 사례 없음"

        context = "\n**금감원 실제 피싱 사례:**\n"
        for i, (script, similarity, meta) in enumerate(similar_cases[:3], 1):
            label = meta.get('label', '알 수 없음')
            context += f"{i}. [{label}] (유사도: {similarity*100:.1f}%)\n"
            context += f"   \"{script[:120]}...\"\n"
        return context

    def _get_context_prompt(self, text: str, similar_context: str) -> str:
        """Agent 1: 맥락 분석 프롬프트 (multi_agent_detector.py와 동일)"""
        return f"""당신은 대화 맥락 분석 전문가입니다. 다음 통화 내용의 **전체적인 맥락과 의도**를 분석하세요.

{similar_context}

**분석 포인트:**
1. 대화의 논리적 흐름과 일관성
2. 발신자의 실제 의도 (표면적 vs 숨겨진 의도)
3. 정상적인 기관/회사의 통화 패턴과의 차이
4. 금감원 실제 사례와의 패턴 유사성
5. 대화의 전개 방식 (급작스러운 전환, 회피 등)

**디지털 감금 패턴 체크리스트:**
- [ ] 공공기관 언급 후 즉각적인 "위치 이동" 요구
- [ ] "전화 끊지 말 것" 또는 "누구와도 말하지 말 것" 지시
- [ ] 이동 장소가 "모텔", "PC방", "독립된 공간" 등 고립 가능한 곳
- [ ] 이동 후 "앱 설치" 또는 "원격 점검" 요청

✅ 3개 이상 해당 시 95점, 2개 시 75점, 1개 시 50점

**평가 기준:**
- 90-100: 전형적인 피싱 대화 패턴, 금감원 사례와 매우 유사
- 70-89: 피싱 의심, 비정상적 대화 흐름
- 50-69: 의심스러운 요소 있음
- 30-49: 일부 주의 필요
- 0-29: 정상적인 대화 패턴

**응답 (JSON):**
{{
  "score": <0-100 정수>,
  "is_suspicious": <true/false>,
  "reasoning": "<상세한 분석 근거 2-3문장>",
  "key_indicators": [<핵심 의심 요소 리스트>]
}}

JSON:"""

    def _get_psychological_prompt(self, text: str) -> str:
        """Agent 2: 심리 조작 탐지 프롬프트"""
        return f"""당신은 심리 조작 패턴 탐지 전문가입니다. 다음 통화에서 **심리적 조작 기법**을 찾아내세요.

**탐지할 심리 조작 기법:**
1. **공포/불안 조성**: "체포", "범죄 연루", "피해", "손실" 등
2. **긴급성 압박**: "즉시", "지금 당장", "늦으면 안됨" 등
3. **권위 이용**: 공공기관 언급, 전문 용어 남발
4. **고립 유도**: "다른 사람에게 말하지 마세요"
5. **혼란 조성**: 복잡한 설명, 빠른 전개
6. **물리적 고립 유도**: "집은 도청 위험", "모텔로 이동", "CCTV 없는 곳"
7. **지속적 통제 의도**: "전화 끊지 마세요", "충전기 꽂으세요", "내일까지 대기"
8. **명령형 발화 패턴**: 연속 5회 이상 "~하세요", "~갑니다" 사용

**중요:**
- 단어가 직접 나오지 않아도 **맥락상 압박**이 있으면 탐지
- 정상 기관은 전화로 긴급하게 개인정보/금전을 요구하지 않음
- ⚠️ 정상 기관은 절대 시민을 특정 장소로 이동시키지 않습니다!

**평가 기준:**
- 90-100: 다층적 심리 조작, 매우 위험
- 70-89: 명백한 심리 압박 존재
- 50-69: 심리적 불편함 유도
- 30-49: 약한 압박 요소
- 0-29: 정상적 대화

**응답 (JSON):**
{{
  "score": <0-100 정수>,
  "manipulation_detected": <true/false>,
  "techniques_found": [<탐지된 기법들>],
  "reasoning": "<분석 근거 2-3문장>"
}}

JSON:"""

    def _get_financial_prompt(self, text: str) -> str:
        """Agent 3: 금전/정보 요구 탐지 프롬프트"""
        return f"""당신은 금전/개인정보 요구 탐지 전문가입니다. 다음 통화에서 **숨겨진 요구**를 찾아내세요.

**탐지 대상:**
1. **직접적 요구**: "계좌번호 알려주세요", "송금하세요"
2. **간접적 유도**: "확인이 필요합니다", "안전을 위해" (→ 실제로는 정보 요구)
3. **교묘한 포장**: "보호", "안전", "확인" 등의 긍정적 단어로 포장
4. **단계적 접근**: 작은 정보부터 시작해 점점 확대
5. **정당화**: 그럴듯한 이유로 요구를 정당화
6. **원격 제어 앱 특정**: TeamViewer, QuickSupport, AnyDesk, "법무부 앱", "보안 점검 앱", "APK 파일"
7. **설치 후 행동 통제**: "화면 뒤집어 놓으세요", "시키는 대로만 하세요", "은행 앱 켜세요"

**원격 제어 앱 설치 위험 시그널:**
- "제가 보낸 링크 클릭하세요" + SMS/카톡 링크
- "팀뷰어", "퀵서포트", "전용 앱" 언급
- "플레이스토어 아님", "APK 직접 설치"
- "화면 뒤집기", "권한 모두 허용" 지시
- 설치 후 "은행 앱 실행", "비밀번호 입력" 요구

**핵심:**
- **정상 기관은 전화로 개인정보를 요구하지 않습니다**
- 🚨 정상 수사기관은 개인 폰에 앱 설치를 절대 요구하지 않습니다!
- 단어가 없어도 **유도하는 맥락**이 있으면 위험

**평가 기준:**
- 90-100: 명백한 금전/정보 요구 (직접 or 교묘)
- 70-89: 강한 유도, 요구 의도 명확
- 50-69: 의심스러운 정보 확인 시도
- 30-49: 일반적 확인 수준
- 0-29: 정보 요구 없음

**응답 (JSON):**
{{
  "score": <0-100 정수>,
  "request_detected": <true/false>,
  "request_types": [<탐지된 요구 유형들>],
  "reasoning": "<분석 근거 2-3문장>"
}}

JSON:"""

    def _compare_results(self, all_results: Dict) -> Dict:
        """모든 LLM 결과를 비교 테이블 형식으로 정리 (앙상블X, 비교O)"""

        # LLM별로 3개 Agent 점수 가중 평균 계산
        llm_scores = {}
        weights = {"context": 0.35, "psychological": 0.35, "financial": 0.30}

        comparison_table = []
        comparison_table.append("\n" + "="*80)
        comparison_table.append("🔬 LLM 성능 비교표 (Multi-Agent 분석)")
        comparison_table.append("="*80)
        comparison_table.append(f"{'LLM':<15} {'맥락(35%)':<12} {'심리(35%)':<12} {'금전(30%)':<12} {'최종점수':<10}")
        comparison_table.append("-"*80)

        for llm_name in self.available_llms.keys():
            context_score = all_results.get(f"{llm_name}_context", {}).get("score", 50)
            psych_score = all_results.get(f"{llm_name}_psychological", {}).get("score", 50)
            fin_score = all_results.get(f"{llm_name}_financial", {}).get("score", 50)

            final = round(
                context_score * weights["context"] +
                psych_score * weights["psychological"] +
                fin_score * weights["financial"],
                2
            )

            llm_scores[llm_name] = final

            comparison_table.append(
                f"{llm_name:<15} {context_score:<12} {psych_score:<12} {fin_score:<12} {final:<10}"
            )

        comparison_table.append("="*80)

        # 통계
        if llm_scores:
            scores_list = list(llm_scores.values())
            avg = round(statistics.mean(scores_list), 2)
            median = round(statistics.median(scores_list), 2)
            max_score = max(scores_list)
            min_score = min(scores_list)

            comparison_table.append(f"평균: {avg}  |  중앙값: {median}  |  최고: {max_score}  |  최저: {min_score}")
            comparison_table.append("="*80)
        else:
            avg = median = max_score = min_score = 50

        # 상세 분석 (각 LLM의 reasoning)
        detailed_analysis = []
        for llm_name in self.available_llms.keys():
            detailed_analysis.append(f"\n--- {llm_name} ({llm_scores.get(llm_name, 0)}점) ---")
            for agent in ["context", "psychological", "financial"]:
                key = f"{llm_name}_{agent}"
                if key in all_results:
                    score = all_results[key].get("score", 0)
                    reasoning = all_results[key].get("reasoning", "N/A")
                    detailed_analysis.append(f"  [{agent}] {score}점")
                    detailed_analysis.append(f"    {reasoning}")

        return {
            "risk_score": avg,  # 참고용 평균값
            "is_phishing": avg >= 70,
            "confidence": 0,  # 사용자가 직접 판단하므로 0
            "comparison_table": "\n".join(comparison_table),
            "llm_scores": llm_scores,  # 각 LLM별 최종 점수
            "statistics": {
                "average": avg,
                "median": median,
                "max": max_score,
                "min": min_score
            },
            "all_results": all_results,  # 모든 상세 결과
            "detailed_analysis": "\n".join(detailed_analysis),
            "reasoning": "🔬 5개 LLM 성능 비교 모드 - 사용자가 직접 최적 모델을 선택하세요.",
            "recommendation": "위 비교표를 참고하여 가장 정확한 LLM을 선택하세요.",
            "techniques": [],
            "red_flags": []
        }

    def _fallback_result(self) -> Dict:
        """LLM을 사용할 수 없을 때"""
        return {
            "risk_score": 50,
            "is_phishing": False,
            "confidence": 0,
            "ensemble_score": 50,
            "llm_scores": {},
            "all_results": {},
            "reasoning": "LLM API 키가 설정되지 않았습니다.",
            "recommendation": "API 키를 설정하세요.",
            "techniques": [],
            "red_flags": []
        }
