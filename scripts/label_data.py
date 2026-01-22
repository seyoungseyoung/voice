"""
Script to label conversation data
"""
import sys
from pathlib import Path
import argparse
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.labeler import PhishingDataLabeler


def main():
    parser = argparse.ArgumentParser(description="Label conversation data for phishing detection")
    parser.add_argument(
        "--transcript",
        type=str,
        help="Path to transcript JSON file"
    )
    parser.add_argument(
        "--audio",
        type=str,
        help="Path to audio file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/labeled",
        help="Output directory for labeled data"
    )
    parser.add_argument(
        "--create-dataset",
        action="store_true",
        help="Create training dataset from labeled files"
    )
    parser.add_argument(
        "--dataset-output",
        type=str,
        default="data/training_dataset.json",
        help="Output file for training dataset"
    )

    args = parser.parse_args()

    labeler = PhishingDataLabeler(output_dir=Path(args.output))

    if args.create_dataset:
        # Create training dataset from labeled files
        print("=" * 60)
        print("Creating training dataset from labeled files...")
        print("=" * 60)

        labeled_dir = Path(args.output)
        dataset_output = Path(args.dataset_output)

        labeler.create_training_dataset(labeled_dir, dataset_output)

        print("\n✓ Training dataset created")

    elif args.transcript and args.audio:
        # Label a transcript file
        print("=" * 60)
        print("Labeling transcript with automatic tags...")
        print("=" * 60)
        print(f"Transcript: {args.transcript}")
        print(f"Audio:      {args.audio}")
        print("=" * 60)

        # Load transcript
        with open(args.transcript, 'r', encoding='utf-8') as f:
            transcript = json.load(f)

        # Label the transcript
        conversation = labeler.label_transcript(transcript, args.audio)

        # Save labeled data
        output_file = Path(args.output) / f"{Path(args.audio).stem}_labeled.json"
        labeler.save_labeled_data(conversation, output_file)

        # Print statistics
        stats = conversation["statistics"]
        print(f"\n✓ Labeling complete")
        print(f"Total segments: {stats['total_segments']}")
        print(f"Duration: {stats['total_duration']:.2f}s")
        print(f"Is phishing: {stats['is_phishing']}")
        print(f"\nTag counts:")
        for tag, count in stats['tag_counts'].items():
            if count > 0:
                print(f"  - {tag}: {count}")

    else:
        parser.print_help()
        print("\nExamples:")
        print("  # Label a transcript:")
        print("  python scripts/label_data.py --transcript transcript.json --audio audio.wav")
        print("\n  # Create training dataset:")
        print("  python scripts/label_data.py --create-dataset")


if __name__ == "__main__":
    main()
