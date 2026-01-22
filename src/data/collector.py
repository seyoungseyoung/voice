"""
Data collection utilities for voice phishing datasets
"""
import os
import json
import requests
from pathlib import Path
from typing import List, Dict, Optional
from tqdm import tqdm
import logging

from src.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataCollector:
    """
    Collects voice phishing data from various sources:
    - AI Hub (보이스피싱 음성 데이터)
    - 금융감독원 (그놈 목소리 체험관)
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or config.data_dir / "raw"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def download_file(self, url: str, filename: str) -> Path:
        """
        Download a file from URL with progress bar

        Args:
            url: Download URL
            filename: Output filename

        Returns:
            Path to downloaded file
        """
        output_path = self.output_dir / filename

        if output_path.exists():
            logger.info(f"File already exists: {output_path}")
            return output_path

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))

            with open(output_path, 'wb') as f, tqdm(
                desc=filename,
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    size = f.write(chunk)
                    pbar.update(size)

            logger.info(f"Downloaded: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Download failed for {url}: {e}")
            if output_path.exists():
                output_path.unlink()
            raise

    def collect_aihub_data(self, dataset_url: Optional[str] = None):
        """
        Collect data from AI Hub

        Note: AI Hub requires manual download with login
        This function provides instructions and validates downloaded data
        """
        logger.info("=== AI Hub Data Collection ===")
        logger.info("AI Hub requires manual download with authentication.")
        logger.info("Please follow these steps:")
        logger.info("1. Visit: https://aihub.or.kr")
        logger.info("2. Search for: '보이스피싱 음성 데이터' or '민원 질의응답 데이터'")
        logger.info("3. Download the dataset")
        logger.info(f"4. Place downloaded files in: {self.output_dir}")

        # Check if data already exists
        existing_files = list(self.output_dir.glob("*.zip"))
        if existing_files:
            logger.info(f"\nFound {len(existing_files)} files in {self.output_dir}:")
            for f in existing_files:
                logger.info(f"  - {f.name}")
        else:
            logger.warning(f"\nNo data files found in {self.output_dir}")

    def collect_fss_data(self):
        """
        Collect data from 금융감독원 '그놈 목소리' platform

        Note: This may require web scraping or manual collection
        depending on the website's terms of service
        """
        logger.info("=== FSS (금융감독원) Data Collection ===")
        logger.info("FSS '그놈 목소리' data collection requires manual process.")
        logger.info("1. Visit: https://voice.fss.or.kr")
        logger.info("2. Collect sample voice recordings")
        logger.info(f"3. Save to: {self.output_dir / 'fss'}")

        fss_dir = self.output_dir / "fss"
        fss_dir.mkdir(exist_ok=True)

        existing_files = list(fss_dir.glob("*.wav")) + list(fss_dir.glob("*.mp3"))
        if existing_files:
            logger.info(f"\nFound {len(existing_files)} audio files in {fss_dir}")
        else:
            logger.warning(f"\nNo audio files found in {fss_dir}")

    def create_metadata(self, audio_files: List[Path]) -> Dict:
        """
        Create metadata file for collected audio data

        Args:
            audio_files: List of audio file paths

        Returns:
            Metadata dictionary
        """
        metadata = {
            "total_files": len(audio_files),
            "files": []
        }

        for audio_file in audio_files:
            file_info = {
                "filename": audio_file.name,
                "path": str(audio_file),
                "size_bytes": audio_file.stat().st_size,
                "extension": audio_file.suffix,
            }
            metadata["files"].append(file_info)

        # Save metadata
        metadata_path = self.output_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        logger.info(f"Metadata saved to: {metadata_path}")
        return metadata

    def collect_all(self):
        """
        Run all data collection processes
        """
        logger.info("Starting data collection process...")

        # AI Hub data
        self.collect_aihub_data()

        # FSS data
        self.collect_fss_data()

        # Create metadata for all collected files
        all_audio_files = (
            list(self.output_dir.glob("**/*.wav")) +
            list(self.output_dir.glob("**/*.mp3")) +
            list(self.output_dir.glob("**/*.flac"))
        )

        if all_audio_files:
            self.create_metadata(all_audio_files)
            logger.info(f"\n✓ Total audio files collected: {len(all_audio_files)}")
        else:
            logger.warning("\n⚠ No audio files found. Please download datasets manually.")


def main():
    """Main function for data collection"""
    collector = DataCollector()
    collector.collect_all()


if __name__ == "__main__":
    main()
