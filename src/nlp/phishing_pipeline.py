"""
End-to-end phishing detection pipeline using LangChain
Integrates STT → Vector Search → LLM Analysis
"""
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# LangChain imports - optional, using rule-based approach for now
# from langchain_core.prompts import PromptTemplate
# from langchain.chains import LLMChain
# from langchain_community.llms import HuggingFacePipeline
# from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

from src.stt.whisper_stt import WhisperSTT
from src.vector_db.vector_store import PhishingVectorStore
from src.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PhishingDetectionPipeline:
    """
    Complete pipeline for voice phishing detection

    Flow:
    1. Audio → STT (Whisper)
    2. Transcript → Vector DB Search (FAISS)
    3. Transcript + Similar cases → LLM Analysis
    4. → Risk Score + Alert
    """

    def __init__(
        self,
        stt_model: Optional[WhisperSTT] = None,
        vector_store: Optional[PhishingVectorStore] = None,
        llm_model_name: str = "beomi/llama-2-ko-7b",
        use_local_llm: bool = True
    ):
        """
        Args:
            stt_model: STT model instance (default: Whisper base)
            vector_store: Vector store instance
            llm_model_name: HuggingFace model name for LLM
            use_local_llm: Use local LLM (True) or API (False)
        """
        # Initialize STT
        self.stt = stt_model or WhisperSTT(model_size="base")
        logger.info("STT initialized")

        # Initialize Vector Store
        self.vector_store = vector_store or PhishingVectorStore()
        try:
            self.vector_store.load()
            logger.info(f"Vector store loaded with {len(self.vector_store.scripts)} scripts")
        except:
            logger.warning("Vector store not loaded - similarity search will be limited")

        # Initialize LLM
        self.use_local_llm = use_local_llm
        if use_local_llm:
            logger.info(f"Loading local LLM: {llm_model_name}")
            # Note: This is a placeholder - actual model loading may require GPU
            # For CPU-only demo, use a smaller model
            self.llm = None  # Placeholder
            logger.warning("Local LLM not initialized - using rule-based analysis")
        else:
            # For API-based LLM (e.g., OpenAI GPT, ClovaX)
            self.llm = None
            logger.warning("API-based LLM not configured")

        # Create prompt template
        self.prompt_template = self._create_prompt_template()

    def _create_prompt_template(self) -> str:
        """Create prompt template for phishing analysis"""
        template = """당신은 보이스피싱 탐지 전문가입니다. 다음 통화 내용을 분석하여 보이스피싱 위험도를 평가하세요.

통화 내용:
{transcript}

유사한 보이스피싱 사례:
{similar_cases}

다음 기준으로 분석하세요:
1. 접근 방식 (검찰, 경찰, 금융기관 사칭 여부)
2. 협박 또는 긴급성 조성
3. 개인정보 요구
4. 송금 유도

분석 결과를 다음 형식으로 제공하세요:
- 위험도: [0-100 점수]
- 탐지된 피싱 기법: [목록]
- 근거: [설명]
- 권장 조치: [사용자에게 제공할 조언]
"""
        return template

    def transcribe_audio(self, audio_path: Path) -> str:
        """
        Step 1: Transcribe audio to text

        Args:
            audio_path: Path to audio file

        Returns:
            Transcript text
        """
        logger.info(f"Transcribing audio: {audio_path.name}")
        result = self.stt.transcribe(audio_path)
        transcript = result["text"]
        logger.info(f"Transcription: {transcript[:100]}...")
        return transcript

    def search_similar_cases(
        self,
        transcript: str,
        top_k: int = 3
    ) -> List[Tuple[str, float, Dict]]:
        """
        Step 2: Search for similar phishing cases

        Args:
            transcript: Conversation transcript
            top_k: Number of similar cases to retrieve

        Returns:
            List of (script, similarity_score, metadata)
        """
        logger.info("Searching for similar phishing cases...")

        if len(self.vector_store.scripts) == 0:
            logger.warning("Vector store is empty, no similar cases found")
            return []

        results = self.vector_store.search(transcript, top_k=top_k)

        for i, (script, score, meta) in enumerate(results, 1):
            logger.info(f"  {i}. Similarity: {score:.4f} - {script[:50]}...")

        return results

    def analyze_with_llm(
        self,
        transcript: str,
        similar_cases: List[Tuple[str, float, Dict]]
    ) -> Dict:
        """
        Step 3: Analyze with LLM

        Args:
            transcript: Conversation transcript
            similar_cases: Similar phishing cases from vector search

        Returns:
            Analysis result dictionary
        """
        # Format similar cases
        similar_cases_text = "\n".join([
            f"- (유사도: {score:.2f}) {script}"
            for script, score, _ in similar_cases
        ]) if similar_cases else "유사 사례 없음"

        # For now, use rule-based analysis since LLM is not loaded
        # In production, this would use the LLM
        logger.info("Analyzing with rule-based approach (LLM placeholder)")

        risk_score = self._rule_based_analysis(transcript, similar_cases)

        return {
            "risk_score": risk_score,
            "is_phishing": risk_score >= 70,
            "techniques_detected": self._detect_techniques(transcript),
            "similar_cases_count": len(similar_cases),
            "recommendation": self._get_recommendation(risk_score)
        }

    def _rule_based_analysis(
        self,
        transcript: str,
        similar_cases: List[Tuple[str, float, Dict]]
    ) -> int:
        """
        Rule-based risk scoring (placeholder for LLM analysis)

        Args:
            transcript: Conversation transcript
            similar_cases: Similar cases

        Returns:
            Risk score (0-100)
        """
        score = 0

        # Check for authority impersonation
        authority_keywords = ["검찰", "경찰", "금융감독원", "금감원", "국세청", "법원"]
        if any(kw in transcript for kw in authority_keywords):
            score += 30

        # Check for threats
        threat_keywords = ["체포", "구속", "압류", "영장", "범죄", "처벌", "고소"]
        if any(kw in transcript for kw in threat_keywords):
            score += 25

        # Check for PII requests
        pii_keywords = ["주민번호", "계좌번호", "비밀번호", "카드번호", "인증번호"]
        if any(kw in transcript for kw in pii_keywords):
            score += 25

        # Check for money requests
        money_keywords = ["송금", "이체", "입금", "안전계좌", "보호예수"]
        if any(kw in transcript for kw in money_keywords):
            score += 20

        # Bonus from similar cases
        if similar_cases:
            max_similarity = max([score for _, score, _ in similar_cases])
            score += int(max_similarity * 10)

        return min(score, 100)

    def _detect_techniques(self, transcript: str) -> List[str]:
        """Detect phishing techniques used"""
        techniques = []

        if any(kw in transcript for kw in ["검찰", "경찰", "금감원"]):
            techniques.append("기관 사칭")

        if any(kw in transcript for kw in ["체포", "구속", "영장"]):
            techniques.append("협박")

        if any(kw in transcript for kw in ["주민번호", "계좌번호", "비밀번호"]):
            techniques.append("개인정보 탈취")

        if any(kw in transcript for kw in ["송금", "안전계좌"]):
            techniques.append("금전 요구")

        return techniques

    def _get_recommendation(self, risk_score: int) -> str:
        """Get user recommendation based on risk score"""
        if risk_score >= 90:
            return "즉시 통화를 종료하고 112에 신고하세요!"
        elif risk_score >= 70:
            return "의심스러운 통화입니다. 개인정보나 금전 제공을 절대 하지 마세요."
        elif risk_score >= 50:
            return "주의가 필요합니다. 상대방의 신원을 확인하세요."
        else:
            return "정상 통화로 판단됩니다."

    def analyze_audio(self, audio_path: Path) -> Dict:
        """
        Complete analysis pipeline

        Args:
            audio_path: Path to audio file

        Returns:
            Complete analysis result
        """
        logger.info(f"Starting phishing detection analysis for: {audio_path.name}")

        # Step 1: Transcribe
        transcript = self.transcribe_audio(audio_path)

        # Step 2: Vector search
        similar_cases = self.search_similar_cases(transcript)

        # Step 3: LLM analysis
        analysis = self.analyze_with_llm(transcript, similar_cases)

        # Combine results
        result = {
            "audio_file": str(audio_path),
            "transcript": transcript,
            "similar_cases": [
                {"script": script, "similarity": float(score)}
                for script, score, _ in similar_cases
            ],
            **analysis
        }

        logger.info(f"Analysis complete - Risk Score: {analysis['risk_score']}/100")

        return result


def main():
    """Example usage"""
    print("=" * 60)
    print("Sentinel-Voice: Phishing Detection Pipeline")
    print("=" * 60)

    # Create pipeline
    pipeline = PhishingDetectionPipeline()

    # Example: analyze an audio file
    # audio_file = Path("data/processed/sample.wav")
    # if audio_file.exists():
    #     result = pipeline.analyze_audio(audio_file)
    #
    #     print(f"\n분석 결과:")
    #     print(f"위험도: {result['risk_score']}/100")
    #     print(f"피싱 여부: {'예' if result['is_phishing'] else '아니오'}")
    #     print(f"탐지된 기법: {', '.join(result['techniques_detected'])}")
    #     print(f"권장 조치: {result['recommendation']}")
    # else:
    #     print(f"\nExample audio not found: {audio_file}")

    print("\nPipeline ready for use")


if __name__ == "__main__":
    main()
