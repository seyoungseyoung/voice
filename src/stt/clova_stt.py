"""
Naver Clova Speech-to-Text implementation
Uses Naver Cloud Platform Clova Speech API
"""
import time
import requests
import json
from pathlib import Path
from typing import Dict, List, Optional
import logging

from src.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClovaSTT:
    """
    Naver Clova Speech Recognition API wrapper
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        language: str = "ko-KR"
    ):
        """
        Args:
            client_id: Naver Cloud Platform Client ID
            client_secret: Naver Cloud Platform Client Secret
            language: Language code (ko-KR for Korean)
        """
        self.client_id = client_id or config.api.naver_client_id
        self.client_secret = client_secret or config.api.naver_client_secret
        self.language = language

        if not self.client_id or not self.client_secret:
            logger.warning(
                "Naver Cloud credentials not found. "
                "Please set NAVER_CLIENT_ID and NAVER_CLIENT_SECRET in .env file"
            )

        self.api_url = "https://naveropenapi.apigw.ntruss.com/recog/v1/stt"

    def transcribe(
        self,
        audio_file: Path,
        language: Optional[str] = None
    ) -> Dict:
        """
        Transcribe audio using Clova Speech API

        Args:
            audio_file: Path to audio file
            language: Optional language override

        Returns:
            Dictionary with transcription results
        """
        if not self.client_id or not self.client_secret:
            raise ValueError("Naver Cloud credentials not configured")

        logger.info(f"Transcribing with Clova Speech: {audio_file.name}")
        start_time = time.time()

        # Prepare request
        headers = {
            "X-NCP-APIGW-API-KEY-ID": self.client_id,
            "X-NCP-APIGW-API-KEY": self.client_secret,
            "Content-Type": "application/octet-stream"
        }

        params = {
            "lang": language or self.language
        }

        # Read audio file
        with open(audio_file, 'rb') as f:
            audio_data = f.read()

        # Make API request
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                params=params,
                data=audio_data
            )
            response.raise_for_status()

            result = response.json()
            elapsed = time.time() - start_time

            logger.info(f"Transcription complete in {elapsed:.2f}s")

            return {
                "text": result.get("text", ""),
                "raw_response": result,
                "processing_time": elapsed
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Clova Speech API error: {e}")
            raise

    def transcribe_with_timestamps(
        self,
        audio_file: Path
    ) -> List[Dict]:
        """
        Transcribe with timestamps (if supported by API)

        Note: Clova Speech basic API may not support word-level timestamps
        Advanced features may require different API endpoint

        Args:
            audio_file: Path to audio file

        Returns:
            List of segments (may be single segment if timestamps not available)
        """
        result = self.transcribe(audio_file)

        # Basic implementation - returns full text as single segment
        # Advanced implementation would parse detailed response
        return [{
            "text": result["text"],
            "start": 0.0,
            "end": 0.0,  # Duration unknown without additional info
            "speaker": "UNKNOWN"
        }]

    def benchmark(
        self,
        audio_files: List[Path],
        ground_truth: Optional[List[str]] = None
    ) -> Dict:
        """
        Benchmark Clova Speech performance

        Args:
            audio_files: List of audio file paths
            ground_truth: Optional list of ground truth transcripts

        Returns:
            Benchmark statistics
        """
        logger.info(f"Benchmarking Clova Speech on {len(audio_files)} files...")

        total_time = 0
        transcriptions = []
        api_calls = 0

        for i, audio_file in enumerate(audio_files, 1):
            logger.info(f"Processing {i}/{len(audio_files)}: {audio_file.name}")

            try:
                result = self.transcribe(audio_file)
                total_time += result["processing_time"]
                transcriptions.append(result["text"])
                api_calls += 1

                # Rate limiting - avoid too many requests
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"Failed to transcribe {audio_file.name}: {e}")
                transcriptions.append("")

        benchmark_results = {
            "service": "Naver Clova Speech",
            "num_files": len(audio_files),
            "successful_calls": api_calls,
            "total_processing_time": total_time,
            "average_time_per_file": total_time / api_calls if api_calls > 0 else 0,
            "transcriptions": transcriptions
        }

        # Calculate WER if ground truth provided
        if ground_truth and len(ground_truth) == len(transcriptions):
            from jiwer import wer
            # Filter out empty transcriptions
            valid_pairs = [(gt, trans) for gt, trans in zip(ground_truth, transcriptions) if trans]
            if valid_pairs:
                gt_valid, trans_valid = zip(*valid_pairs)
                overall_wer = wer(list(gt_valid), list(trans_valid))
                benchmark_results["wer"] = overall_wer
                logger.info(f"Word Error Rate (WER): {overall_wer:.4f}")

        logger.info(f"Benchmark complete:")
        logger.info(f"  Successful calls: {api_calls}/{len(audio_files)}")
        logger.info(f"  Average time: {benchmark_results['average_time_per_file']:.2f}s per file")

        return benchmark_results


def main():
    """Example usage"""
    stt = ClovaSTT()

    print("=" * 60)
    print("Naver Clova Speech STT")
    print("=" * 60)

    # Check credentials
    if not stt.client_id or not stt.client_secret:
        print("\n⚠ Warning: Naver Cloud credentials not configured")
        print("Please set the following in your .env file:")
        print("  NAVER_CLIENT_ID=your_client_id")
        print("  NAVER_CLIENT_SECRET=your_client_secret")
        return

    # Example: transcribe a file
    # audio_file = Path("data/processed/sample.wav")
    # if audio_file.exists():
    #     result = stt.transcribe(audio_file)
    #     print(f"\nTranscription: {result['text']}")
    # else:
    #     print(f"\nExample audio file not found: {audio_file}")

    print("\nClova STT ready for use")


if __name__ == "__main__":
    main()
