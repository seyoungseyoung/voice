"""
Script to run data collection
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.collector import DataCollector


if __name__ == "__main__":
    print("=" * 60)
    print("Sentinel-Voice: Data Collection")
    print("=" * 60)

    collector = DataCollector()
    collector.collect_all()

    print("\n" + "=" * 60)
    print("Data collection instructions completed.")
    print("Please follow the manual steps above to download datasets.")
    print("=" * 60)
