"""
Audio preprocessing module for voice phishing detection
Includes: noise reduction, speaker diarization, audio normalization
"""
import librosa
import soundfile as sf
import numpy as np
import noisereduce as nr
from pathlib import Path
from typing import Tuple, Optional, List, Dict
import logging

from src.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioPreprocessor:
    """
    Preprocesses audio files for phishing detection:
    - Noise reduction
    - Audio normalization
    - Sample rate conversion
    - Silence removal
    """

    def __init__(
        self,
        target_sr: int = 16000,
        normalize: bool = True,
        noise_reduce: bool = True
    ):
        """
        Args:
            target_sr: Target sampling rate (default: 16000 for Whisper)
            normalize: Whether to normalize audio amplitude
            noise_reduce: Whether to apply noise reduction
        """
        self.target_sr = target_sr
        self.normalize = normalize
        self.noise_reduce = noise_reduce

    def load_audio(self, file_path: Path) -> Tuple[np.ndarray, int]:
        """
        Load audio file

        Args:
            file_path: Path to audio file

        Returns:
            Tuple of (audio_data, sample_rate)
        """
        try:
            audio, sr = librosa.load(file_path, sr=None)
            logger.info(f"Loaded audio: {file_path.name} (sr={sr}, duration={len(audio)/sr:.2f}s)")
            return audio, sr
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            raise

    def reduce_noise(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """
        Apply noise reduction using spectral gating

        Args:
            audio: Audio data
            sr: Sample rate

        Returns:
            Denoised audio
        """
        try:
            # Use first 1 second as noise profile
            noise_sample = audio[:sr]
            reduced = nr.reduce_noise(
                y=audio,
                sr=sr,
                y_noise=noise_sample,
                stationary=False,
                prop_decrease=1.0
            )
            logger.debug("Noise reduction applied")
            return reduced
        except Exception as e:
            logger.warning(f"Noise reduction failed: {e}, returning original audio")
            return audio

    def normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """
        Normalize audio amplitude to [-1, 1]

        Args:
            audio: Audio data

        Returns:
            Normalized audio
        """
        max_val = np.abs(audio).max()
        if max_val > 0:
            normalized = audio / max_val
            logger.debug(f"Audio normalized (max was {max_val:.4f})")
            return normalized
        return audio

    def resample_audio(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """
        Resample audio to target sample rate

        Args:
            audio: Audio data
            orig_sr: Original sample rate
            target_sr: Target sample rate

        Returns:
            Resampled audio
        """
        if orig_sr == target_sr:
            return audio

        resampled = librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)
        logger.debug(f"Resampled from {orig_sr}Hz to {target_sr}Hz")
        return resampled

    def remove_silence(
        self,
        audio: np.ndarray,
        sr: int,
        threshold_db: float = -40.0,
        min_silence_duration: float = 0.5
    ) -> np.ndarray:
        """
        Remove silence from audio

        Args:
            audio: Audio data
            sr: Sample rate
            threshold_db: Volume threshold in dB
            min_silence_duration: Minimum silence duration to remove (seconds)

        Returns:
            Audio with silence removed
        """
        # Split audio at silence
        intervals = librosa.effects.split(
            audio,
            top_db=-threshold_db,
            frame_length=int(sr * min_silence_duration),
            hop_length=int(sr * min_silence_duration / 4)
        )

        # Concatenate non-silent intervals
        if len(intervals) > 0:
            audio_trimmed = np.concatenate([audio[start:end] for start, end in intervals])
            logger.debug(f"Removed silence: {len(audio)} -> {len(audio_trimmed)} samples")
            return audio_trimmed

        return audio

    def preprocess(
        self,
        input_path: Path,
        output_path: Optional[Path] = None,
        remove_silence: bool = True
    ) -> Tuple[np.ndarray, int]:
        """
        Full preprocessing pipeline

        Args:
            input_path: Input audio file path
            output_path: Output path (optional, will save if provided)
            remove_silence: Whether to remove silence

        Returns:
            Tuple of (processed_audio, sample_rate)
        """
        logger.info(f"Preprocessing: {input_path.name}")

        # Load audio
        audio, sr = self.load_audio(input_path)

        # Resample if needed
        if sr != self.target_sr:
            audio = self.resample_audio(audio, sr, self.target_sr)
            sr = self.target_sr

        # Noise reduction
        if self.noise_reduce:
            audio = self.reduce_noise(audio, sr)

        # Remove silence
        if remove_silence:
            audio = self.remove_silence(audio, sr)

        # Normalize
        if self.normalize:
            audio = self.normalize_audio(audio)

        # Save if output path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            sf.write(output_path, audio, sr)
            logger.info(f"Saved preprocessed audio to: {output_path}")

        return audio, sr

    def preprocess_batch(
        self,
        input_dir: Path,
        output_dir: Path,
        file_pattern: str = "*.wav"
    ) -> List[Path]:
        """
        Preprocess all audio files in a directory

        Args:
            input_dir: Input directory
            output_dir: Output directory
            file_pattern: File pattern to match (e.g., "*.wav")

        Returns:
            List of output file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        input_files = list(input_dir.glob(file_pattern))

        if not input_files:
            logger.warning(f"No files found matching {file_pattern} in {input_dir}")
            return []

        logger.info(f"Processing {len(input_files)} files from {input_dir}")

        output_paths = []
        for input_file in input_files:
            try:
                output_file = output_dir / input_file.name
                self.preprocess(input_file, output_file)
                output_paths.append(output_file)
            except Exception as e:
                logger.error(f"Failed to process {input_file.name}: {e}")

        logger.info(f"Batch preprocessing complete: {len(output_paths)}/{len(input_files)} succeeded")
        return output_paths


class SpeakerDiarization:
    """
    Speaker diarization for separating caller and victim in phishing calls

    Note: This is a placeholder for future implementation
    Recommended libraries: pyannote.audio, resemblyzer
    """

    def __init__(self):
        logger.warning("SpeakerDiarization is not yet implemented")
        # TODO: Implement using pyannote.audio or resemblyzer

    def diarize(self, audio: np.ndarray, sr: int) -> Dict[str, List[Tuple[float, float]]]:
        """
        Perform speaker diarization

        Args:
            audio: Audio data
            sr: Sample rate

        Returns:
            Dictionary mapping speaker IDs to time segments
            e.g., {"SPEAKER_00": [(0.0, 5.2), (10.1, 15.3)], ...}
        """
        # Placeholder implementation
        logger.warning("Speaker diarization not implemented, returning dummy data")
        return {
            "SPEAKER_00": [(0.0, len(audio) / sr / 2)],
            "SPEAKER_01": [(len(audio) / sr / 2, len(audio) / sr)]
        }


def main():
    """Example usage"""
    preprocessor = AudioPreprocessor(target_sr=16000)

    # Example: preprocess a single file
    # input_file = Path("data/raw/sample.wav")
    # output_file = Path("data/processed/sample.wav")
    # preprocessor.preprocess(input_file, output_file)

    # Example: batch preprocess
    input_dir = config.data_dir / "raw"
    output_dir = config.data_dir / "processed"

    if input_dir.exists():
        preprocessor.preprocess_batch(input_dir, output_dir, "*.wav")
    else:
        logger.warning(f"Input directory not found: {input_dir}")
        logger.info("Please run data collection first: python scripts/collect_data.py")


if __name__ == "__main__":
    main()
