"""
Whisper-based Speech-to-Text implementation
Uses OpenAI Whisper for Korean speech recognition
"""
import time
import whisper
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Union
import logging
import librosa

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WhisperSTT:
    """
    Whisper-based STT for Korean voice phishing detection
    """

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        language: str = "ko"
    ):
        """
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to run on (cpu, cuda)
            language: Language code (ko for Korean)
        """
        self.model_size = model_size
        self.device = device
        self.language = language

        logger.info(f"Loading Whisper model: {model_size} on {device}")
        start_time = time.time()

        self.model = whisper.load_model(model_size, device=device)

        load_time = time.time() - start_time
        logger.info(f"Model loaded in {load_time:.2f}s")

    def transcribe(
        self,
        audio: Union[str, Path, np.ndarray],
        **kwargs
    ) -> Dict:
        """
        Transcribe audio to text

        Args:
            audio: Audio file path or numpy array
            **kwargs: Additional arguments for whisper.transcribe()

        Returns:
            Dictionary with transcription results
            {
                "text": full transcript,
                "segments": list of segment dicts with text, start, end times,
                "language": detected language
            }
        """
        logger.info(f"Transcribing audio...")
        start_time = time.time()

        # Default options for Korean
        options = {
            "language": self.language,
            "task": "transcribe",
            "verbose": False,
            **kwargs
        }

        # Load audio file to numpy array - try multiple loaders for robustness
        if isinstance(audio, (str, Path)):
            audio_path = Path(audio)
            logger.info(f"Loading audio file: {audio_path.name} ({audio_path.suffix})")

            # Strategy: Try soundfile -> librosa -> Whisper direct
            # This handles WAV, MP3, FLAC, OGG, M4A, WEBM, and more
            loaded = False

            # Try 1: soundfile (fastest for WAV/FLAC)
            try:
                import soundfile as sf
                logger.debug(f"Attempting soundfile...")
                audio_data, sample_rate = sf.read(str(audio), dtype='float32')

                # Convert stereo to mono
                if len(audio_data.shape) > 1:
                    audio_data = audio_data.mean(axis=1)

                # Resample to 16kHz if needed
                if sample_rate != 16000:
                    audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=16000)
                    sample_rate = 16000

                logger.info(f"✓ Soundfile: {len(audio_data)} samples at {sample_rate}Hz ({len(audio_data)/sample_rate:.2f}s)")
                result = self.model.transcribe(audio_data, **options)
                loaded = True

            except Exception as e1:
                logger.debug(f"Soundfile failed: {e1}")

            # Try 2: librosa (handles MP3, OGG, etc.)
            if not loaded:
                try:
                    logger.debug(f"Attempting librosa...")
                    audio_data, sr = librosa.load(str(audio), sr=16000, mono=True)
                    logger.info(f"✓ Librosa: {len(audio_data)} samples at {sr}Hz ({len(audio_data)/sr:.2f}s)")
                    result = self.model.transcribe(audio_data, **options)
                    loaded = True

                except Exception as e2:
                    logger.debug(f"Librosa failed: {e2}")

            # Try 3: Whisper direct (uses ffmpeg internally)
            if not loaded:
                logger.warning(f"All Python loaders failed, trying Whisper direct (requires ffmpeg)")
                result = self.model.transcribe(str(audio), **options)
                logger.info(f"✓ Whisper direct transcription successful")
        else:
            # Already a numpy array
            result = self.model.transcribe(audio, **options)

        transcribe_time = time.time() - start_time

        # Calculate metrics
        audio_duration = result.get("segments", [{}])[-1].get("end", 0) if result.get("segments") else 0
        rtf = transcribe_time / audio_duration if audio_duration > 0 else 0

        logger.info(
            f"Transcription complete: "
            f"{transcribe_time:.2f}s for {audio_duration:.2f}s audio "
            f"(RTF: {rtf:.2f})"
        )

        return result

    def transcribe_with_timestamps(
        self,
        audio: Union[str, Path, np.ndarray]
    ) -> List[Dict]:
        """
        Transcribe audio with word-level timestamps

        Args:
            audio: Audio file path or numpy array

        Returns:
            List of segments with timestamps
            [{"text": str, "start": float, "end": float, "speaker": str}, ...]
        """
        result = self.transcribe(audio, word_timestamps=True)

        segments = []
        for segment in result.get("segments", []):
            segments.append({
                "text": segment["text"].strip(),
                "start": segment["start"],
                "end": segment["end"],
                "speaker": "UNKNOWN"  # Placeholder, speaker diarization needed
            })

        return segments

    def benchmark(
        self,
        audio_files: List[Path],
        ground_truth: Optional[List[str]] = None
    ) -> Dict:
        """
        Benchmark Whisper performance on multiple audio files

        Args:
            audio_files: List of audio file paths
            ground_truth: Optional list of ground truth transcripts

        Returns:
            Benchmark statistics
        """
        logger.info(f"Benchmarking on {len(audio_files)} files...")

        total_time = 0
        total_audio_duration = 0
        transcriptions = []

        for i, audio_file in enumerate(audio_files, 1):
            logger.info(f"Processing {i}/{len(audio_files)}: {audio_file.name}")

            start = time.time()
            result = self.transcribe(audio_file)
            elapsed = time.time() - start

            audio_duration = result.get("segments", [{}])[-1].get("end", 0) if result.get("segments") else 0

            total_time += elapsed
            total_audio_duration += audio_duration
            transcriptions.append(result["text"])

        avg_rtf = total_time / total_audio_duration if total_audio_duration > 0 else 0

        benchmark_results = {
            "model_size": self.model_size,
            "device": self.device,
            "num_files": len(audio_files),
            "total_audio_duration": total_audio_duration,
            "total_processing_time": total_time,
            "average_rtf": avg_rtf,
            "transcriptions": transcriptions
        }

        # Calculate WER if ground truth provided
        if ground_truth and len(ground_truth) == len(transcriptions):
            from jiwer import wer
            overall_wer = wer(ground_truth, transcriptions)
            benchmark_results["wer"] = overall_wer
            logger.info(f"Word Error Rate (WER): {overall_wer:.4f}")

        logger.info(f"Benchmark complete:")
        logger.info(f"  Average RTF: {avg_rtf:.4f}")
        logger.info(f"  Total time: {total_time:.2f}s for {total_audio_duration:.2f}s audio")

        return benchmark_results


def main():
    """Example usage and benchmark"""

    # Test with different model sizes
    model_sizes = ["tiny", "base", "small"]

    for size in model_sizes:
        print("\n" + "=" * 60)
        print(f"Testing Whisper {size} model")
        print("=" * 60)

        stt = WhisperSTT(model_size=size, device="cpu")

        # Example: transcribe a file
        # audio_file = Path("data/processed/sample.wav")
        # if audio_file.exists():
        #     result = stt.transcribe(audio_file)
        #     print(f"\nTranscription: {result['text']}")
        #
        #     segments = stt.transcribe_with_timestamps(audio_file)
        #     print("\nSegments:")
        #     for seg in segments:
        #         print(f"[{seg['start']:.2f}-{seg['end']:.2f}] {seg['text']}")

        print(f"\n{size} model ready for benchmarking")


if __name__ == "__main__":
    main()
