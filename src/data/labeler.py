"""
Data labeling module for phishing conversation analysis
Supports tagging: [접근], [협박], [개인정보요구], [송금유도]
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PhishingTag(Enum):
    """Phishing conversation tags"""
    APPROACH = "접근"  # Initial contact / gaining trust
    THREAT = "협박"  # Threatening / creating fear
    PII_REQUEST = "개인정보요구"  # Requesting personal information
    MONEY_REQUEST = "송금유도"  # Requesting money transfer
    NORMAL = "정상"  # Normal conversation


class ConversationSegment:
    """Represents a segment of conversation with labels"""

    def __init__(
        self,
        text: str,
        speaker: str,
        start_time: float,
        end_time: float,
        tags: Optional[List[PhishingTag]] = None
    ):
        self.text = text
        self.speaker = speaker
        self.start_time = start_time
        self.end_time = end_time
        self.tags = tags or []

    def add_tag(self, tag: PhishingTag):
        """Add a tag to this segment"""
        if tag not in self.tags:
            self.tags.append(tag)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "text": self.text,
            "speaker": self.speaker,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "tags": [tag.value for tag in self.tags]
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ConversationSegment":
        """Create from dictionary"""
        tags = [PhishingTag(tag) for tag in data.get("tags", [])]
        return cls(
            text=data["text"],
            speaker=data["speaker"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            tags=tags
        )


class PhishingDataLabeler:
    """
    Handles labeling of phishing conversation data
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("data/labeled")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_labeled_conversation(
        self,
        audio_file: str,
        segments: List[ConversationSegment],
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Create a labeled conversation dataset

        Args:
            audio_file: Path to audio file
            segments: List of conversation segments
            metadata: Additional metadata

        Returns:
            Labeled conversation dictionary
        """
        conversation = {
            "audio_file": audio_file,
            "segments": [seg.to_dict() for seg in segments],
            "metadata": metadata or {},
            "statistics": self._calculate_statistics(segments)
        }
        return conversation

    def _calculate_statistics(self, segments: List[ConversationSegment]) -> Dict:
        """Calculate statistics about the conversation"""
        tag_counts = {tag.value: 0 for tag in PhishingTag}

        for segment in segments:
            for tag in segment.tags:
                tag_counts[tag.value] += 1

        total_segments = len(segments)
        duration = max([seg.end_time for seg in segments]) if segments else 0

        return {
            "total_segments": total_segments,
            "total_duration": duration,
            "tag_counts": tag_counts,
            "is_phishing": any(
                tag in [PhishingTag.THREAT, PhishingTag.PII_REQUEST, PhishingTag.MONEY_REQUEST]
                for seg in segments for tag in seg.tags
            )
        }

    def save_labeled_data(self, conversation: Dict, output_file: Path):
        """Save labeled conversation to JSON file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(conversation, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved labeled data to: {output_file}")

    def load_labeled_data(self, input_file: Path) -> Dict:
        """Load labeled conversation from JSON file"""
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded labeled data from: {input_file}")
        return data

    def auto_label_with_keywords(self, text: str) -> List[PhishingTag]:
        """
        Automatically label text based on keyword patterns
        This is a simple rule-based approach for initial labeling

        Args:
            text: Conversation text

        Returns:
            List of detected tags
        """
        tags = []

        # Keyword patterns for each tag
        patterns = {
            PhishingTag.APPROACH: [
                "검찰", "경찰", "금융감독원", "금감원", "국세청",
                "보안팀", "상담원", "직원", "관계자"
            ],
            PhishingTag.THREAT: [
                "체포", "구속", "압류", "영장", "범죄",
                "위험", "피해", "손해", "법적", "처벌"
            ],
            PhishingTag.PII_REQUEST: [
                "주민번호", "계좌번호", "비밀번호", "카드번호",
                "인증번호", "확인번호", "보안카드", "OTP"
            ],
            PhishingTag.MONEY_REQUEST: [
                "송금", "이체", "입금", "출금", "보관",
                "안전계좌", "보호예수", "금액", "만원", "원"
            ]
        }

        # Check for each pattern
        for tag, keywords in patterns.items():
            if any(keyword in text for keyword in keywords):
                tags.append(tag)

        # If no phishing tags found, mark as normal
        if not tags:
            tags.append(PhishingTag.NORMAL)

        return tags

    def label_transcript(
        self,
        transcript: List[Dict],
        audio_file: str
    ) -> Dict:
        """
        Label a transcript automatically

        Args:
            transcript: List of transcript segments with 'text', 'speaker', 'start', 'end'
            audio_file: Path to audio file

        Returns:
            Labeled conversation
        """
        segments = []

        for item in transcript:
            text = item.get("text", "")
            speaker = item.get("speaker", "UNKNOWN")
            start_time = item.get("start", 0.0)
            end_time = item.get("end", 0.0)

            # Auto-label based on keywords
            tags = self.auto_label_with_keywords(text)

            segment = ConversationSegment(
                text=text,
                speaker=speaker,
                start_time=start_time,
                end_time=end_time,
                tags=tags
            )
            segments.append(segment)

        return self.create_labeled_conversation(audio_file, segments)

    def create_training_dataset(
        self,
        labeled_dir: Path,
        output_file: Path
    ):
        """
        Combine multiple labeled conversations into a training dataset

        Args:
            labeled_dir: Directory containing labeled JSON files
            output_file: Output file for combined dataset
        """
        dataset = {
            "conversations": [],
            "statistics": {
                "total_conversations": 0,
                "phishing_conversations": 0,
                "normal_conversations": 0,
                "total_segments": 0
            }
        }

        json_files = list(labeled_dir.glob("*.json"))

        for json_file in json_files:
            try:
                conversation = self.load_labeled_data(json_file)
                dataset["conversations"].append(conversation)

                stats = conversation.get("statistics", {})
                dataset["statistics"]["total_conversations"] += 1

                if stats.get("is_phishing", False):
                    dataset["statistics"]["phishing_conversations"] += 1
                else:
                    dataset["statistics"]["normal_conversations"] += 1

                dataset["statistics"]["total_segments"] += stats.get("total_segments", 0)

            except Exception as e:
                logger.error(f"Failed to load {json_file}: {e}")

        # Save combined dataset
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)

        logger.info(f"Created training dataset: {output_file}")
        logger.info(f"Total conversations: {dataset['statistics']['total_conversations']}")
        logger.info(f"Phishing: {dataset['statistics']['phishing_conversations']}")
        logger.info(f"Normal: {dataset['statistics']['normal_conversations']}")


def main():
    """Example usage"""
    labeler = PhishingDataLabeler()

    # Example: Create a labeled conversation
    segments = [
        ConversationSegment(
            text="안녕하세요, 검찰청입니다.",
            speaker="CALLER",
            start_time=0.0,
            end_time=2.5,
            tags=[PhishingTag.APPROACH]
        ),
        ConversationSegment(
            text="네? 무슨 일이시죠?",
            speaker="VICTIM",
            start_time=2.5,
            end_time=4.0,
            tags=[PhishingTag.NORMAL]
        ),
        ConversationSegment(
            text="당신 계좌가 범죄에 연루되었습니다. 즉시 주민번호를 확인해야 합니다.",
            speaker="CALLER",
            start_time=4.0,
            end_time=8.0,
            tags=[PhishingTag.THREAT, PhishingTag.PII_REQUEST]
        )
    ]

    conversation = labeler.create_labeled_conversation(
        audio_file="sample_phishing_call.wav",
        segments=segments,
        metadata={
            "source": "example",
            "date": "2024-01-01",
            "verified": True
        }
    )

    output_file = labeler.output_dir / "example_labeled.json"
    labeler.save_labeled_data(conversation, output_file)

    print(f"Example labeled data created at: {output_file}")


if __name__ == "__main__":
    main()
