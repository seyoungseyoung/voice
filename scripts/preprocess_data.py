"""
Script to preprocess audio data
"""
import sys
from pathlib import Path
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.preprocessor import AudioPreprocessor
from src.config import config


def main():
    parser = argparse.ArgumentParser(description="Preprocess audio data for phishing detection")
    parser.add_argument(
        "--input-dir",
        type=str,
        default=str(config.data_dir / "raw"),
        help="Input directory containing raw audio files"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(config.data_dir / "processed"),
        help="Output directory for processed audio files"
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*.wav",
        help="File pattern to match (default: *.wav)"
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        help="Target sample rate (default: 16000 Hz for Whisper)"
    )
    parser.add_argument(
        "--no-noise-reduce",
        action="store_true",
        help="Disable noise reduction"
    )
    parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Disable audio normalization"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Sentinel-Voice: Audio Preprocessing")
    print("=" * 60)
    print(f"Input directory:  {args.input_dir}")
    print(f"Output directory: {args.output_dir}")
    print(f"File pattern:     {args.pattern}")
    print(f"Target SR:        {args.sample_rate} Hz")
    print(f"Noise reduction:  {'Disabled' if args.no_noise_reduce else 'Enabled'}")
    print(f"Normalization:    {'Disabled' if args.no_normalize else 'Enabled'}")
    print("=" * 60)

    # Create preprocessor
    preprocessor = AudioPreprocessor(
        target_sr=args.sample_rate,
        normalize=not args.no_normalize,
        noise_reduce=not args.no_noise_reduce
    )

    # Run batch preprocessing
    input_path = Path(args.input_dir)
    output_path = Path(args.output_dir)

    if not input_path.exists():
        print(f"\n❌ Error: Input directory does not exist: {input_path}")
        print("Please run data collection first: python scripts/collect_data.py")
        sys.exit(1)

    output_files = preprocessor.preprocess_batch(input_path, output_path, args.pattern)

    print("\n" + "=" * 60)
    print(f"✓ Preprocessing complete: {len(output_files)} files processed")
    print(f"Output location: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
