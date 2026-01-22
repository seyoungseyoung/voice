"""
Create sample phishing data for demo and testing
"""
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.labeler import PhishingDataLabeler, ConversationSegment, PhishingTag
from src.vector_db.vector_store import PhishingVectorStore


def create_sample_conversations():
    """Create sample phishing conversations"""
    labeler = PhishingDataLabeler()

    conversations = []

    # Sample 1: 검찰 사칭
    segments1 = [
        ConversationSegment(
            text="안녕하세요, 서울중앙지검 김철수 검사입니다.",
            speaker="CALLER",
            start_time=0.0,
            end_time=3.0,
            tags=[PhishingTag.APPROACH]
        ),
        ConversationSegment(
            text="네? 검찰청이요?",
            speaker="VICTIM",
            start_time=3.0,
            end_time=4.5,
            tags=[PhishingTag.NORMAL]
        ),
        ConversationSegment(
            text="당신 명의의 계좌가 보이스피싱 범죄에 사용되었습니다. 지금 바로 확인하지 않으면 내일 체포영장이 발부됩니다.",
            speaker="CALLER",
            start_time=4.5,
            end_time=10.0,
            tags=[PhishingTag.THREAT]
        ),
        ConversationSegment(
            text="주민등록번호와 계좌번호를 말씀해주세요.",
            speaker="CALLER",
            start_time=10.0,
            end_time=12.0,
            tags=[PhishingTag.PII_REQUEST]
        )
    ]

    conv1 = labeler.create_labeled_conversation(
        "sample_prosecutor.wav",
        segments1,
        {"type": "검찰_사칭", "severity": "high"}
    )
    conversations.append(conv1)

    # Sample 2: 금융감독원 사칭
    segments2 = [
        ConversationSegment(
            text="금융감독원입니다. 고객님 계좌에서 이상거래가 감지되었습니다.",
            speaker="CALLER",
            start_time=0.0,
            end_time=4.0,
            tags=[PhishingTag.APPROACH]
        ),
        ConversationSegment(
            text="즉시 안전계좌로 자금을 이체하셔야 피해를 막을 수 있습니다.",
            speaker="CALLER",
            start_time=4.0,
            end_time=7.0,
            tags=[PhishingTag.MONEY_REQUEST]
        ),
        ConversationSegment(
            text="카드번호와 OTP 번호를 알려주세요.",
            speaker="CALLER",
            start_time=7.0,
            end_time=9.0,
            tags=[PhishingTag.PII_REQUEST]
        )
    ]

    conv2 = labeler.create_labeled_conversation(
        "sample_fss.wav",
        segments2,
        {"type": "금감원_사칭", "severity": "high"}
    )
    conversations.append(conv2)

    # Sample 3: 경찰 사칭
    segments3 = [
        ConversationSegment(
            text="서울경찰청 금융범죄수사대입니다.",
            speaker="CALLER",
            start_time=0.0,
            end_time=2.5,
            tags=[PhishingTag.APPROACH]
        ),
        ConversationSegment(
            text="고객님 계좌가 범죄에 연루되어 압류 조치가 예정되어 있습니다.",
            speaker="CALLER",
            start_time=2.5,
            end_time=6.0,
            tags=[PhishingTag.THREAT]
        ),
        ConversationSegment(
            text="지금 당장 전 재산을 보호예수 계좌로 송금하셔야 합니다.",
            speaker="CALLER",
            start_time=6.0,
            end_time=9.0,
            tags=[PhishingTag.MONEY_REQUEST]
        )
    ]

    conv3 = labeler.create_labeled_conversation(
        "sample_police.wav",
        segments3,
        {"type": "경찰_사칭", "severity": "critical"}
    )
    conversations.append(conv3)

    # Sample 4: 은행 사칭
    segments4 = [
        ConversationSegment(
            text="국민은행 보안팀입니다. 고객님 계좌에서 해킹 시도가 감지되었습니다.",
            speaker="CALLER",
            start_time=0.0,
            end_time=4.0,
            tags=[PhishingTag.APPROACH]
        ),
        ConversationSegment(
            text="보안카드 번호 전체를 말씀해주시면 계좌를 보호하겠습니다.",
            speaker="CALLER",
            start_time=4.0,
            end_time=7.0,
            tags=[PhishingTag.PII_REQUEST]
        )
    ]

    conv4 = labeler.create_labeled_conversation(
        "sample_bank.wav",
        segments4,
        {"type": "은행_사칭", "severity": "medium"}
    )
    conversations.append(conv4)

    # Sample 5: 국세청 사칭
    segments5 = [
        ConversationSegment(
            text="국세청입니다. 체납된 세금이 있어 연락드렸습니다.",
            speaker="CALLER",
            start_time=0.0,
            end_time=3.0,
            tags=[PhishingTag.APPROACH]
        ),
        ConversationSegment(
            text="오늘 중으로 납부하지 않으면 재산 압류와 법적 처벌을 받게 됩니다.",
            speaker="CALLER",
            start_time=3.0,
            end_time=7.0,
            tags=[PhishingTag.THREAT]
        ),
        ConversationSegment(
            text="지금 즉시 계좌로 입금하세요.",
            speaker="CALLER",
            start_time=7.0,
            end_time=9.0,
            tags=[PhishingTag.MONEY_REQUEST]
        )
    ]

    conv5 = labeler.create_labeled_conversation(
        "sample_nts.wav",
        segments5,
        {"type": "국세청_사칭", "severity": "high"}
    )
    conversations.append(conv5)

    return conversations


def main():
    print("=" * 60)
    print("Creating Sample Phishing Data")
    print("=" * 60)

    # Create sample conversations
    conversations = create_sample_conversations()

    # Save training dataset
    dataset = {
        "conversations": conversations,
        "statistics": {
            "total_conversations": len(conversations),
            "phishing_conversations": len(conversations),
            "normal_conversations": 0,
            "total_segments": sum(len(c["segments"]) for c in conversations)
        }
    }

    output_file = Path("data/training_dataset.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Created training dataset: {output_file}")
    print(f"  Total conversations: {len(conversations)}")
    print(f"  Total segments: {dataset['statistics']['total_segments']}")

    # Build vector database
    print("\n" + "=" * 60)
    print("Building Vector Database")
    print("=" * 60)

    vector_store = PhishingVectorStore()
    vector_store.build_from_labeled_data(output_file)
    vector_store.save("phishing_vector_db")

    stats = vector_store.get_statistics()
    print(f"\n✓ Vector database built successfully")
    print(f"  Total scripts: {stats['total_scripts']}")
    print(f"  Embedding dimension: {stats['embedding_dimension']}")

    # Test search
    print("\n" + "=" * 60)
    print("Testing Vector Search")
    print("=" * 60)

    test_queries = [
        "검찰청에서 전화가 왔는데 계좌 확인을 요구합니다",
        "경찰이라고 하면서 송금하라고 해요",
        "은행에서 보안카드 번호를 물어봅니다"
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        results = vector_store.search(query, top_k=2)
        for i, (script, score, meta) in enumerate(results, 1):
            print(f"  {i}. Score: {score:.4f}")
            print(f"     Script: {script[:60]}...")

    print("\n" + "=" * 60)
    print("Sample data creation complete!")
    print("Restart the server to use the new vector database.")
    print("=" * 60)


if __name__ == "__main__":
    main()
