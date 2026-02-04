"""
Script to benchmark STT models (Whisper vs Clova Speech)
"""
import sys
from pathlib import Path
import argparse
import json
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.stt.whisper_stt import WhisperSTT
from src.stt.clova_stt import ClovaSTT
from src.config import config


def collect_test_files(test_dir: Path, pattern: str = "*.wav", max_files: int = 10):
    """Collect test audio files"""
    files = list(test_dir.glob(pattern))[:max_files]
    return files


def benchmark_whisper(audio_files: List[Path], model_sizes: List[str]):
    """Benchmark Whisper models"""
    results = {}

    for size in model_sizes:
        print(f"\n{'='*60}")
        print(f"Benchmarking Whisper {size} model")
        print(f"{'='*60}")

        try:
            stt = WhisperSTT(model_size=size, device="cpu")
            result = stt.benchmark(audio_files)
            results[f"whisper_{size}"] = result

            print(f"\nResults:")
            print(f"  Files processed: {result['num_files']}")
            print(f"  Total audio: {result['total_audio_duration']:.2f}s")
            print(f"  Processing time: {result['total_processing_time']:.2f}s")
            print(f"  Average RTF: {result['average_rtf']:.4f}")

        except Exception as e:
            print(f"❌ Error benchmarking Whisper {size}: {e}")
            results[f"whisper_{size}"] = {"error": str(e)}

    return results


def benchmark_clova(audio_files: List[Path]):
    """Benchmark Clova Speech"""
    print(f"\n{'='*60}")
    print(f"Benchmarking Naver Clova Speech")
    print(f"{'='*60}")

    try:
        stt = ClovaSTT()

        if not stt.client_id or not stt.client_secret:
            print("⚠ Skipping Clova Speech - credentials not configured")
            return {"clova": {"error": "Credentials not configured"}}

        result = stt.benchmark(audio_files)

        print(f"\nResults:")
        print(f"  Files processed: {result['num_files']}")
        print(f"  Successful calls: {result['successful_calls']}")
        print(f"  Processing time: {result['total_processing_time']:.2f}s")
        print(f"  Average per file: {result['average_time_per_file']:.2f}s")

        return {"clova": result}

    except Exception as e:
        print(f"❌ Error benchmarking Clova Speech: {e}")
        return {"clova": {"error": str(e)}}


def main():
    parser = argparse.ArgumentParser(description="Benchmark STT models for phishing detection")
    parser.add_argument(
        "--test-dir",
        type=str,
        default="data/processed",
        help="Directory containing test audio files"
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*.wav",
        help="File pattern to match"
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=10,
        help="Maximum number of files to test"
    )
    parser.add_argument(
        "--whisper-models",
        type=str,
        default="tiny,base",
        help="Comma-separated list of Whisper model sizes (tiny,base,small,medium,large)"
    )
    parser.add_argument(
        "--skip-clova",
        action="store_true",
        help="Skip Clova Speech benchmark"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="benchmark_results.json",
        help="Output file for benchmark results"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Sentinel-Voice: STT Benchmark")
    print("=" * 60)

    # Collect test files
    test_dir = Path(args.test_dir)
    if not test_dir.exists():
        print(f"❌ Error: Test directory not found: {test_dir}")
        print("Please run data preprocessing first:")
        print("  python scripts/preprocess_data.py")
        sys.exit(1)

    audio_files = collect_test_files(test_dir, args.pattern, args.max_files)

    if not audio_files:
        print(f"❌ Error: No audio files found in {test_dir} matching {args.pattern}")
        sys.exit(1)

    print(f"\nTest files: {len(audio_files)}")
    for f in audio_files[:5]:
        print(f"  - {f.name}")
    if len(audio_files) > 5:
        print(f"  ... and {len(audio_files) - 5} more")

    # Benchmark Whisper
    whisper_models = args.whisper_models.split(",")
    whisper_results = benchmark_whisper(audio_files, whisper_models)

    # Benchmark Clova
    clova_results = {}
    if not args.skip_clova:
        clova_results = benchmark_clova(audio_files)

    # Combine results
    all_results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "test_files_count": len(audio_files),
        "whisper": whisper_results,
        "clova": clova_results
    }

    # Save results
    output_path = Path(args.output)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("Benchmark Summary")
    print("=" * 60)

    # Print comparison
    print("\nModel Comparison:")
    print(f"{'Model':<20} {'RTF/Time':<15} {'Status':<10}")
    print("-" * 50)

    for model_name, result in whisper_results.items():
        if "error" in result:
            print(f"{model_name:<20} {'N/A':<15} {'Failed':<10}")
        else:
            rtf = result.get('average_rtf', 0)
            print(f"{model_name:<20} {rtf:<15.4f} {'Success':<10}")

    if "clova" in clova_results and "error" not in clova_results["clova"]:
        avg_time = clova_results["clova"].get("average_time_per_file", 0)
        print(f"{'clova':<20} {f'{avg_time:.2f}s/file':<15} {'Success':<10}")

    print("\n" + "=" * 60)
    print(f"✓ Benchmark results saved to: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    from typing import List
    main()
