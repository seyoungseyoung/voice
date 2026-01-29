"""
Multi-Agent ClovaX System for Phishing Detection
3개의 전문 에이전트가 각각 다른 관점에서 분석
"""
import asyncio
import logging
from typing import Dict, List, Tuple, Optional
import json
import requests
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiAgentPhishingDetector:
    """
    3-Agent system for comprehensive phishing detection

    Agent 1: Context Analyst (맥락 분석가) - 대화의 흐름과 의도
    Agent 2: Psychological Manipul

ation Detector (심리 조작 탐지) - 불안/긴급성/권위
    Agent 3: Financial/Information Request Detector (금전/정보 요구 탐지)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_gateway_key: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("CLOVAX_API_KEY")
        self.api_gateway_key = api_gateway_key or os.getenv("CLOVAX_GATEWAY_KEY")
        self.request_id = request_id or "sentinel-voice-multi-agent"

        self.api_url = "https://clovastudio.stream.ntruss.com/testapp/v1/chat-completions/HCX-003"

        # Agent weights (can be tuned)
        self.agent_weights = {
            "context": 0.35,      # 35% - 맥락이 가장 중요
            "psychological": 0.35, # 35% - 심리 조작도 중요
            "financial": 0.30      # 30% - 금전/정보 요구
        }

        if not self.api_key:
            logger.warning("ClovaX API key not configured")
        else:
            logger.info("Multi-Agent Detector initialized (3 agents)")

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_gateway_key)

    def analyze(
        self,
        conversation_text: str,
        similar_cases: Optional[List[Tuple[str, float, Dict]]] = None
    ) -> Dict:
        """
        Run all 3 agents in parallel and combine results
        """
        if not self.is_available():
            logger.warning("Gemini not available")
            return self._fallback_result()

        try:
            # Format similar cases context
            similar_context = self._format_similar_cases(similar_cases)

            logger.info("🤖 Running 3-Agent analysis...")

            # Run all 3 agents
            agent1_result = self._agent1_context_analysis(conversation_text, similar_context)
            agent2_result = self._agent2_psychological_analysis(conversation_text)
            agent3_result = self._agent3_financial_analysis(conversation_text)

            # Combine results
            combined = self._combine_results(agent1_result, agent2_result, agent3_result)

            logger.info(f"✓ Multi-agent analysis complete: {combined['risk_score']}/100")
            return combined

        except Exception as e:
            logger.error(f"Multi-agent analysis failed: {e}")
            return self._fallback_result()

    def _format_similar_cases(self, similar_cases: Optional[List[Tuple[str, float, Dict]]]) -> str:
        """Format similar cases for prompt context"""
        if not similar_cases or len(similar_cases) == 0:
            return "유사 사례 없음"

        context = "\n**금감원 실제 피싱 사례:**\n"
        for i, (script, similarity, meta) in enumerate(similar_cases[:3], 1):
            label = meta.get('label', '알 수 없음')
            severity = meta.get('severity', 'UNKNOWN')
            context += f"{i}. [{label}] (유사도: {similarity*100:.1f}%)\n"
            context += f"   \"{script[:120]}...\"\n"
        return context

    def _agent1_context_analysis(self, text: str, similar_context: str) -> Dict:
        """
        Agent 1: 맥락 분석가 (Context Analyst)
        대화의 전체적인 흐름, 의도, 논리적 일관성, 그리고 최신 피싱 패턴을 분석합니다.
        """
        prompt = f"""당신은 최신 피싱 트렌드를 포함한 모든 대화의 맥락을 꿰뚫어 보는 전문가입니다. 다음 통화 내용의 **전체적인 맥락과 숨겨진 의도**를 깊이 있게 분석하세요.

**통화 내용:**
"{text}"

{similar_context}

**분석 포인트 (과거 & 최신 피싱 패턴 모두 고려):**
1.  **기관 사칭의 교묘함**: "서울중앙지검 첨단범죄수사부", "특수부" 등 구체적인 부서명을 언급하거나, "비대면 약식 조사"라는 명분을 내세우는지 확인하세요.
2.  **복합적 패턴 탐지 (Combination Logic)**: 단순히 "검사"라는 단어뿐만 아니라, **[검사/수사관 사칭] + [장소 이동/모텔] + [앱 설치/원격 제어]**가 하나의 통화 내에서 동시에 발생하는지 분석하세요. 이 조합은 피싱일 확률이 매우 높습니다.
3.  **논리적 비약과 회피**: 정상적인 질문에 동문서답하거나, "보안 유지", "기밀 수사"를 핑계로 제3자와의 접촉을 차단하고 대화를 통제하려는지 확인하세요.
4.  **최신 기술 결합 시도**: "저희가 보낸 URL을 클릭하세요", "악성코드 검사를 위해 원격 제어를 하겠습니다" 등 기술적인 조치를 요구하는 흐름을 탐지하세요.
5.  **사례와의 패턴 일치성**: 제공된 '금감원 실제 피싱 사례'와 대화의 전개 방식(접근->위협->고립->정보요구)이 얼마나 유사한지 비교 분석하세요.

**평가 기준:**
- 90-100: [사칭 + 고립 유도 + 앱 설치] 패턴이 뚜렷하거나, 최신 피싱 시나리오와 정확히 일치함.
- 70-89: 피싱이 강하게 의심됨. 대화의 흐름이 비정상적이고 강압적이거나 논리적 비약이 잦음.
- 50-69: 의심스러운 요소가 존재함. 일반적인 통화와는 다른 점이 느껴짐.
- 30-49: 약간의 주의가 필요하지만, 명백한 위협은 아님.
- 0-29: 지극히 정상적인 대화 패턴.

**응답 (JSON):**
{{
  "score": <0-100 정수>,
  "is_suspicious": <true/false>,
  "reasoning": "<상세한 분석 근거 2-3문장>",
  "key_indicators": [<핵심 의심 요소 리스트>]
}}

JSON:"""

        return self._call_llm(prompt, "context_analyst")

    def _agent2_psychological_analysis(self, text: str) -> Dict:
        """
        Agent 2: 심리 조작 탐지 (Psychological Manipulation Detector)
        불안감, 긴급성, 권위, 유대감 형성 등 교묘한 심리적 조작 기법을 분석합니다.
        """
        prompt = f"""당신은 인간의 심리를 조종하는 모든 기법을 간파하는 프로파일러입니다. 다음 통화에서 사용된 **모든 종류의 심리적 조작 기법**을 찾아내세요.

**통화 내용:**
"{text}"

**탐지할 심리 조작 기법 (고전적 & 최신):**
1.  **고립 유도 (Isolation - 셀프 감금)**: "주변에 듣는 사람이 있으면 안 됩니다", "가까운 모텔이나 조용한 방으로 이동하세요", "문을 잠그세요", "CCTV 없는 곳으로 가세요" 등 피해자를 사회적으로 고립시키는 발언.
2.  **공포/불안 조성 (Fear Mongering)**: "구속 영장 발부", "체포조 출동", "공범으로 처벌", "당신 명의가 도용되어 범죄에 이용됨" 등 극도의 공포심 유발.
3.  **권위 사칭 (Authority Appeal)**: "서울중앙지검 김철수 검사", "첨단범죄수사부", "금융감독원 과장" 등 구체적이고 위압적인 직함을 사용하여 복종 유도.
4.  **장시간 통화 및 통제 (Duration Control)**: "전화 끊으면 도주로 간주합니다", "배터리 충전기 꽂으세요", "와이파이 끄고 데이터만 켜세요" 등 통화를 끊지 못하게 하고 상황을 통제하려는 시도.
5.  **기밀 유지 강요**: "특급 기밀 수사라 발설하면 공무집행방해입니다", "가족에게도 말하면 안 됩니다"라며 입막음 시도.
6.  **대화 주도권 불균형**: 한쪽은 계속해서 지시("~하세요", "이동하세요")하고, 다른 쪽은 짧게 대답("네", "알겠습니다")하거나 공포 반응을 보이는지 분석.

**중요:**
- 단어가 직접 나오지 않더라도 **전체적인 맥락상 압박감이나 혼란을 유발**하면 탐지해야 합니다.
- 정상적인 수사기관은 전화로 이동을 명령하거나, 모텔로 가라고 하거나, 충전기를 꽂으라고 지시하지 않습니다.

**평가 기준:**
- 90-100: [고립 유도]나 [장시간 통제] 등 악질적인 심리 조작이 명백함.
- 70-89: 명백한 심리적 압박과 조작 기법(공포 조성, 권위 사칭)이 2가지 이상 발견됨.
- 50-69: 심리적 불편함을 유도하거나 혼란을 조성하는 요소가 있음.
- 30-49: 약한 압박이나 유도성 발언이 포함됨.
- 0-29: 정상적이고 안정적인 대화.

**응답 (JSON):**
{{
  "score": <0-100 정수>,
  "manipulation_detected": <true/false>,
  "techniques_found": [<탐지된 기법들>],
  "reasoning": "<분석 근거 2-3문장>"
}}

JSON:"""

        return self._call_llm(prompt, "psychological_detector")

    def _agent3_financial_analysis(self, text: str) -> Dict:
        """
        Agent 3: 금전/정보 요구 탐지 (Financial/Information Request Detector)
        직접적/간접적, 명시적/암시적 금전 및 개인/금융정보 요구를 분석합니다.
        """
        prompt = f"""당신은 사기꾼들의 모든 '요구'를 꿰뚫어 보는 금융 보안 전문가입니다. 다음 통화 내용에서 **명시적이거나 암시적인 모든 형태의 금전 또는 정보 요구**를 탐지하세요.

**통화 내용:**
"{text}"

**탐지 대상 (과거 & 최신 수법 포함):**
1.  **악성 앱 및 원격 제어 (Technical Control)**:
    *   "팀뷰어(TeamViewer)", "퀵서포트" 설치 요구.
    *   "보내드린 링크(URL) 클릭해서 전용 보안 앱(APK) 설치하세요."
    *   "원격으로 폰 검사하겠습니다", "화면 뒤집어 놓으세요."
    *   "IP 추적", "악성코드 확인" 핑계로 폰 조작 유도.
2.  **직접적 금전/정보 요구**: "안전 계좌로 이체하세요", "주민번호와 계좌 비밀번호 불러주세요", "상품권 핀번호 보내세요."
3.  **교묘한 정보 유도**: "본인 확인 절차입니다", "금융감독원 전산 등록을 위해..."라며 민감 정보 요구.
4.  **행위 유도**: "은행에 가서 현금을 인출하세요", "창구 직원에게는 인테리어 자금이라고 하세요" 등 구체적인 행동 지시.

**핵심:**
- **"요구"는 단지 돈을 달라는 것뿐만이 아닙니다. 앱 설치, 링크 클릭, 원격 제어 허용 등 폰을 장악하려는 모든 시도가 치명적인 요구입니다.**
- 어떤 기관도 전화로 '팀뷰어' 설치를 요구하거나, 링크를 통해 앱(APK)을 깔라고 하지 않습니다.

**평가 기준:**
- 90-100: [원격 제어 앱] 설치 요구, [링크 클릭] 유도, 또는 명백한 금전 요구가 있음.
- 70-89: 교묘하게 포장되었으나, 그 의도가 명확한 금전/정보 요구(비밀번호 등).
- 50-69: 의심스러운 정보 확인 시도나, 불필요한 행동을 제안함.
- 30-49: 일반적인 본인 확인 절차일 수 있으나, 과도한 정보를 요구.
- 0-29: 금전 또는 민감 정보 요구가 전혀 없음.

**응답 (JSON):**
{{
  "score": <0-100 정수>,
  "request_detected": <true/false>,
  "request_types": [<탐지된 요구 유형들>],
  "reasoning": "<분석 근거 2-3문장>"
}}

JSON:"""

        return self._call_llm(prompt, "financial_detector")

    def _call_llm(self, prompt: str, agent_name: str) -> Dict:
        """Call Gemini API for a single agent"""
        logger.debug(f"Calling Gemini for {agent_name}...")
        
        # GeminiClient의 analyze_phishing 메서드 활용
        # (이미 JSON 파싱 로직이 포함되어 있다고 가정)
        result = self.client.analyze_phishing(prompt, prompt) # text 인자에 prompt를 넣어서 처리
        
        # 결과에 agent 이름 추가
        result['agent'] = agent_name
        logger.debug(f"{agent_name} score: {result.get('score', 0)}")
        return result

    def _parse_agent_response(self, api_response: Dict, agent_name: str) -> Dict:
        """Parse agent response (Deprecated - handled by GeminiClient)"""
        # GeminiClient가 이미 파싱된 dict를 반환하므로 이 메서드는 사용되지 않을 수 있음
        try:
            content = api_response['result']['message']['content']

            # Remove markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)
            result['agent'] = agent_name
            return result

        except Exception as e:
            logger.error(f"{agent_name} parse error: {e}")
            # Return neutral score on parse error
            return {
                "score": 50,
                "agent": agent_name,
                "reasoning": f"파싱 오류: {str(e)}"
            }

    def _combine_results(
        self,
        agent1: Dict,
        agent2: Dict,
        agent3: Dict
    ) -> Dict:
        """Combine results from all 3 agents"""

        # Calculate weighted final score
        final_score = (
            agent1.get("score", 50) * self.agent_weights["context"] +
            agent2.get("score", 50) * self.agent_weights["psychological"] +
            agent3.get("score", 50) * self.agent_weights["financial"]
        )

        final_score = round(final_score, 2)

        # Determine if phishing
        is_phishing = final_score >= 70

        # Collect all techniques/indicators
        all_techniques = []
        if "key_indicators" in agent1:
            all_techniques.extend(agent1["key_indicators"])
        if "techniques_found" in agent2:
            all_techniques.extend(agent2["techniques_found"])
        if "request_types" in agent3:
            all_techniques.extend(agent3["request_types"])

        # Collect all red flags
        red_flags = []
        if agent1.get("is_suspicious", False):
            red_flags.append(f"맥락 의심 ({agent1.get('score', 0)}점)")
        if agent2.get("manipulation_detected", False):
            red_flags.append(f"심리 조작 ({agent2.get('score', 0)}점)")
        if agent3.get("request_detected", False):
            red_flags.append(f"금전/정보 요구 ({agent3.get('score', 0)}점)")

        # Combined reasoning
        reasoning = f"""
**맥락 분석 ({agent1.get('score', 0)}점)**: {agent1.get('reasoning', 'N/A')}

**심리 조작 ({agent2.get('score', 0)}점)**: {agent2.get('reasoning', 'N/A')}

**금전/정보 요구 ({agent3.get('score', 0)}점)**: {agent3.get('reasoning', 'N/A')}
""".strip()

        # Recommendation
        if final_score >= 90:
            recommendation = "⚠️ 매우 높은 위험! 즉시 통화를 종료하고 112에 신고하세요!"
        elif final_score >= 70:
            recommendation = "⚠️ 보이스피싱 의심! 개인정보나 금전 제공을 절대 하지 마세요."
        elif final_score >= 50:
            recommendation = "⚠️ 의심스러운 통화입니다. 상대방의 신원을 직접 확인하세요."
        else:
            recommendation = "정상 통화로 판단되지만, 항상 주의하세요."

        return {
            "risk_score": final_score,
            "is_phishing": is_phishing,
            "confidence": 85,  # High confidence for multi-agent system
            "techniques": all_techniques,
            "reasoning": reasoning,
            "red_flags": red_flags,
            "recommendation": recommendation,
            "agent_scores": {
                "context": agent1.get("score", 0),
                "psychological": agent2.get("score", 0),
                "financial": agent3.get("score", 0)
            }
        }

    def _fallback_result(self) -> Dict:
        """Fallback when ClovaX is not available"""
        return {
            "risk_score": 50,
            "is_phishing": False,
            "confidence": 0,
            "techniques": [],
            "reasoning": "Gemini API를 사용할 수 없습니다.",
            "red_flags": [],
            "recommendation": "Gemini API 키를 설정하세요.",
            "agent_scores": {"context": 0, "psychological": 0, "financial": 0}
        }


def main():
    """Test multi-agent system"""
    detector = MultiAgentPhishingDetector()

    if not detector.is_available():
        print("⚠️ Gemini API 키가 필요합니다")
        return

    test_text = "안녕하세요, 금융감독원입니다. 고객님 계좌에서 이상 거래가 감지되어 확인이 필요합니다."

    result = detector.analyze(test_text)

    print(f"\n위험도: {result['risk_score']}/100")
    print(f"피싱 여부: {result['is_phishing']}")
    print(f"\n분석:\n{result['reasoning']}")
    print(f"\nAgent 점수: {result['agent_scores']}")


if __name__ == "__main__":
    main()
