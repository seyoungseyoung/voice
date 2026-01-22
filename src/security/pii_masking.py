"""
PII (Personally Identifiable Information) Masking Module
Masks sensitive information before sending to cloud services
"""
import re
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PIIMasker:
    """
    Masks personally identifiable information in text
    Supports: 주민번호, 계좌번호, 카드번호, 전화번호, 이메일
    """

    def __init__(self, mask_char: str = "*"):
        """
        Args:
            mask_char: Character to use for masking
        """
        self.mask_char = mask_char

        # Regex patterns for different PII types
        self.patterns = {
            "주민번호": re.compile(r'\d{6}[-\s]?[1-4]\d{6}'),  # 6digits-7digits
            "계좌번호": re.compile(r'\d{3,4}[-\s]?\d{2,6}[-\s]?\d{2,6}'),  # Account numbers
            "카드번호": re.compile(r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}'),  # Card numbers
            "전화번호": re.compile(r'0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}'),  # Phone numbers
            "이메일": re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),  # Email
            "숫자시퀀스": re.compile(r'\d{8,}'),  # Long number sequences (potential sensitive data)
        }

    def mask_text(self, text: str, mask_types: List[str] = None) -> Tuple[str, Dict]:
        """
        Mask PII in text

        Args:
            text: Input text
            mask_types: List of PII types to mask (None = mask all)

        Returns:
            Tuple of (masked_text, metadata)
            metadata contains: {
                "masked_count": int,
                "masked_types": {type: count}
            }
        """
        if mask_types is None:
            mask_types = list(self.patterns.keys())

        masked_text = text
        metadata = {
            "masked_count": 0,
            "masked_types": {}
        }

        for pii_type in mask_types:
            if pii_type not in self.patterns:
                logger.warning(f"Unknown PII type: {pii_type}")
                continue

            pattern = self.patterns[pii_type]
            matches = pattern.findall(masked_text)

            if matches:
                for match in matches:
                    # Mask all but last 4 characters
                    if len(match) > 4:
                        masked_value = self.mask_char * (len(match) - 4) + match[-4:]
                    else:
                        masked_value = self.mask_char * len(match)

                    masked_text = masked_text.replace(match, f"[{pii_type}:{masked_value}]", 1)

                metadata["masked_types"][pii_type] = len(matches)
                metadata["masked_count"] += len(matches)

        if metadata["masked_count"] > 0:
            logger.info(f"Masked {metadata['masked_count']} PII instances: {metadata['masked_types']}")

        return masked_text, metadata

    def mask_numbers(self, text: str, preserve_last_n: int = 4) -> str:
        """
        Mask all numbers in text (aggressive masking for maximum privacy)

        Args:
            text: Input text
            preserve_last_n: Number of digits to preserve

        Returns:
            Masked text
        """
        def replace_numbers(match):
            num = match.group()
            if len(num) > preserve_last_n:
                return self.mask_char * (len(num) - preserve_last_n) + num[-preserve_last_n:]
            return self.mask_char * len(num)

        # Mask sequences of 4 or more digits
        masked = re.sub(r'\d{4,}', replace_numbers, text)
        return masked

    def detect_pii(self, text: str) -> Dict[str, List[str]]:
        """
        Detect PII in text without masking

        Args:
            text: Input text

        Returns:
            Dictionary of {pii_type: [detected_values]}
        """
        detected = {}

        for pii_type, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                detected[pii_type] = matches

        return detected

    def safe_log(self, text: str) -> str:
        """
        Create a safe version of text for logging (all numbers masked)

        Args:
            text: Input text

        Returns:
            Masked text safe for logging
        """
        return self.mask_numbers(text, preserve_last_n=0)


class PIIAwareTranscriptProcessor:
    """
    Processes transcripts with PII awareness
    Integrates with STT pipeline to ensure privacy
    """

    def __init__(self, masker: PIIMasker = None):
        """
        Args:
            masker: PIIMasker instance
        """
        self.masker = masker or PIIMasker()

    def process_transcript(
        self,
        transcript: str,
        enable_masking: bool = True
    ) -> Dict:
        """
        Process transcript with PII detection and optional masking

        Args:
            transcript: Raw transcript
            enable_masking: Whether to mask detected PII

        Returns:
            Dictionary with processed transcript and metadata
        """
        # Detect PII
        detected_pii = self.masker.detect_pii(transcript)

        # Mask if enabled
        if enable_masking:
            masked_transcript, mask_metadata = self.masker.mask_text(transcript)
        else:
            masked_transcript = transcript
            mask_metadata = {"masked_count": 0, "masked_types": {}}

        return {
            "original_transcript": transcript,
            "processed_transcript": masked_transcript,
            "pii_detected": detected_pii,
            "mask_metadata": mask_metadata,
            "has_sensitive_data": len(detected_pii) > 0
        }

    def create_privacy_report(self, processed_result: Dict) -> str:
        """
        Create a privacy protection report

        Args:
            processed_result: Result from process_transcript

        Returns:
            Human-readable privacy report
        """
        report = []
        report.append("=== 개인정보 보호 보고서 ===")

        if processed_result["has_sensitive_data"]:
            report.append(f"\n⚠ 민감한 정보 감지됨:")
            for pii_type, values in processed_result["pii_detected"].items():
                report.append(f"  - {pii_type}: {len(values)}건")

            if processed_result["mask_metadata"]["masked_count"] > 0:
                report.append(f"\n✓ 총 {processed_result['mask_metadata']['masked_count']}건 마스킹 완료")
            else:
                report.append(f"\n⚠ 마스킹이 활성화되지 않았습니다")
        else:
            report.append("\n✓ 민감한 정보가 감지되지 않았습니다")

        return "\n".join(report)


def main():
    """Example usage"""
    print("=" * 60)
    print("Sentinel-Voice: PII Masking Module")
    print("=" * 60)

    masker = PIIMasker()

    # Test examples
    test_cases = [
        "제 주민번호는 123456-1234567입니다.",
        "계좌번호 1234-567890으로 송금해주세요.",
        "카드번호는 1234-5678-9012-3456이에요.",
        "연락처는 010-1234-5678입니다.",
        "이메일 test@example.com으로 보내주세요.",
    ]

    for i, text in enumerate(test_cases, 1):
        print(f"\n예제 {i}:")
        print(f"원본: {text}")

        masked_text, metadata = masker.mask_text(text)
        print(f"마스킹: {masked_text}")
        print(f"메타데이터: {metadata}")

    # Test transcript processor
    print("\n" + "=" * 60)
    print("Transcript Processor Test")
    print("=" * 60)

    processor = PIIAwareTranscriptProcessor()

    sample_transcript = """
    검찰청입니다. 당신의 계좌번호 1234-567890이 범죄에 사용되었습니다.
    주민번호 123456-1234567을 확인해야 합니다.
    """

    result = processor.process_transcript(sample_transcript)

    print("\n원본:")
    print(result["original_transcript"])

    print("\n처리됨:")
    print(result["processed_transcript"])

    print("\n" + processor.create_privacy_report(result))


if __name__ == "__main__":
    main()
