"""
Script to build vector database from labeled data
"""
import sys
from pathlib import Path
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.vector_db.vector_store import PhishingVectorStore


def main():
    parser = argparse.ArgumentParser(description="Build vector database for phishing detection")
    parser.add_argument(
        "--labeled-data",
        type=str,
        default="data/training_dataset.json",
        help="Path to labeled dataset JSON"
    )
    parser.add_argument(
        "--output-name",
        type=str,
        default="phishing_vector_db",
        help="Name for the vector database"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="jhgan/ko-sroberta-multitask",
        help="HuggingFace model for Korean embeddings"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Sentinel-Voice: Vector Database Builder")
    print("=" * 60)
    print(f"Labeled data:     {args.labeled_data}")
    print(f"Embedding model:  {args.model}")
    print(f"Output name:      {args.output_name}")
    print("=" * 60)

    # Create vector store
    vector_store = PhishingVectorStore(model_name=args.model)

    # Check if labeled data exists
    labeled_data_path = Path(args.labeled_data)
    if not labeled_data_path.exists():
        print(f"\n❌ Error: Labeled data not found at {labeled_data_path}")
        print("Please create labeled data first:")
        print("  1. Run data collection: python scripts/collect_data.py")
        print("  2. Preprocess audio: python scripts/preprocess_data.py")
        print("  3. Label data: python scripts/label_data.py --create-dataset")
        sys.exit(1)

    # Build vector database
    print("\nBuilding vector database...")
    vector_store.build_from_labeled_data(labeled_data_path)

    # Save vector database
    print(f"\nSaving vector database as '{args.output_name}'...")
    vector_store.save(args.output_name)

    # Print statistics
    stats = vector_store.get_statistics()
    print("\n" + "=" * 60)
    print("Vector Database Statistics:")
    print("=" * 60)
    print(f"Total scripts:        {stats['total_scripts']}")
    print(f"Embedding dimension:  {stats['embedding_dimension']}")
    print(f"Model:                {stats['model_name']}")
    print(f"Index type:           {stats['index_type']}")
    print("=" * 60)
    print("\n✓ Vector database built successfully")

    # Test search
    print("\nTesting search functionality...")
    test_queries = [
        "검찰청에서 전화가 왔어요",
        "계좌번호를 알려달라고 합니다",
        "안전계좌로 송금하라고 해요"
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        results = vector_store.search(query, top_k=2)
        for i, (script, score, meta) in enumerate(results, 1):
            print(f"  {i}. Score: {score:.4f} | {script[:50]}...")


if __name__ == "__main__":
    main()
