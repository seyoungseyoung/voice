"""
금감원 보이스피싱 음성 데이터 전사 스크립트
Transcribe FSS (Financial Supervisory Service) voice phishing audio files
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import sys
import os

# Add ffmpeg to PATH
ffmpeg_paths = [
    r"C:\Users\tpdud\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin",
    r"C:\ffmpeg\bin",
    r"C:\Program Files\ffmpeg\bin"
]
for path in ffmpeg_paths:
    if os.path.exists(path):
        os.environ["PATH"] = path + os.pathsep + os.environ.get("PATH", "")
        print(f"Added ffmpeg to PATH: {path}")
        break

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.stt.whisper_stt import WhisperSTT

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# 데이터셋 분류 매핑
CATEGORY_MAPPING = {
    "수사기관사칭형": {
        "type": "investigation_impersonation",
        "label": "검찰/경찰 사칭",
        "techniques": ["기관사칭", "협박", "개인정보"],
        "severity": "CRITICAL"
    },
    "대출사기형": {
        "type": "loan_fraud",
        "label": "대출 사기",
        "techniques": ["금전요구", "개인정보"],
        "severity": "HIGH"
    },
    "납치빙자형": {
        "type": "kidnapping_fraud",
        "label": "납치 빙자",
        "techniques": ["협박", "긴급성", "금전요구"],
        "severity": "CRITICAL"
    },
    "모집사기형": {
        "type": "recruitment_fraud",
        "label": "모집 사기",
        "techniques": ["금전요구"],
        "severity": "MEDIUM"
    }
}


def transcribe_fss_dataset(
    input_dir: Path,
    output_file: Path,
    model_size: str = "base"
) -> List[Dict]:
    """
    금감원 음성 데이터셋 전사

    Args:
        input_dir: 금감원 데이터 디렉토리
        output_file: JSON 출력 파일 경로
        model_size: Whisper 모델 크기

    Returns:
        전사 결과 리스트
    """
    logger.info("=" * 70)
    logger.info("금감원 보이스피싱 데이터 전사 시작")
    logger.info("=" * 70)

    # Whisper STT 초기화
    logger.info(f"Whisper 모델 로딩: {model_size}")
    stt = WhisperSTT(model_size=model_size, device="cpu")

    # 모든 MP3 파일 찾기
    mp3_files = list(input_dir.rglob("*.mp3"))
    logger.info(f"발견된 MP3 파일: {len(mp3_files)}개")

    if not mp3_files:
        logger.error(f"MP3 파일을 찾을 수 없습니다: {input_dir}")
        return []

    # 각 카테고리별로 정리
    transcriptions = []

    for i, audio_file in enumerate(mp3_files, 1):
        logger.info("")
        logger.info(f"[{i}/{len(mp3_files)}] 처리 중: {audio_file.name}")
        logger.info("-" * 70)

        # 카테고리 식별
        category_name = audio_file.parent.name
        category_info = CATEGORY_MAPPING.get(category_name, {
            "type": "unknown",
            "label": "미분류",
            "techniques": [],
            "severity": "UNKNOWN"
        })

        try:
            # STT 전사
            result = stt.transcribe(audio_file)
            transcript = result["text"].strip()

            # 세그먼트 정보
            segments = []
            for seg in result.get("segments", []):
                segments.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"].strip()
                })

            # 메타데이터 구성
            entry = {
                "id": f"FSS_{i:03d}",
                "source": "금융감독원",
                "category": category_name,
                "type": category_info["type"],
                "label": category_info["label"],
                "severity": category_info["severity"],
                "techniques": category_info["techniques"],
                "file_name": audio_file.name,
                "file_path": str(audio_file.relative_to(input_dir.parent)),
                "transcript": transcript,
                "segments": segments,
                "duration": segments[-1]["end"] if segments else 0,
                "language": result.get("language", "ko"),
                "transcribed_at": datetime.now().isoformat()
            }

            transcriptions.append(entry)

            # 전사 결과 출력
            logger.info(f"✓ 전사 완료")
            logger.info(f"  카테고리: {category_name} ({category_info['label']})")
            logger.info(f"  길이: {entry['duration']:.1f}초")
            logger.info(f"  텍스트: {transcript[:100]}...")

        except Exception as e:
            logger.error(f"✗ 전사 실패: {audio_file.name}")
            logger.error(f"  오류: {str(e)}")
            continue

    # JSON 저장
    logger.info("")
    logger.info("=" * 70)
    logger.info(f"전사 결과 저장 중: {output_file}")

    output_file.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        "metadata": {
            "source": "금융감독원 보이스피싱 데이터",
            "total_files": len(transcriptions),
            "transcribed_at": datetime.now().isoformat(),
            "whisper_model": model_size,
            "categories": {
                cat_name: {
                    "count": sum(1 for t in transcriptions if t["category"] == cat_name),
                    **cat_info
                }
                for cat_name, cat_info in CATEGORY_MAPPING.items()
            }
        },
        "transcriptions": transcriptions
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    logger.info(f"✓ 저장 완료: {len(transcriptions)}개 항목")
    logger.info("")

    # 통계 출력
    logger.info("=" * 70)
    logger.info("전사 통계")
    logger.info("=" * 70)

    for cat_name, cat_info in CATEGORY_MAPPING.items():
        count = sum(1 for t in transcriptions if t["category"] == cat_name)
        logger.info(f"{cat_name}: {count}개 ({cat_info['label']})")

    total_duration = sum(t["duration"] for t in transcriptions)
    logger.info(f"\n총 음성 길이: {total_duration:.1f}초 ({total_duration/60:.1f}분)")
    if len(transcriptions) > 0:
        logger.info(f"평균 길이: {total_duration/len(transcriptions):.1f}초")
    else:
        logger.error("전사된 파일이 없습니다. ffmpeg 설치를 확인하세요.")

    logger.info("")
    logger.info("=" * 70)
    logger.info("전사 작업 완료!")
    logger.info("=" * 70)

    return transcriptions


def main():
    """메인 실행"""
    # 경로 설정
    ROOT_DIR = Path(__file__).parent.parent
    INPUT_DIR = ROOT_DIR / "data" / "raw" / "금감원_보이스피싱"
    OUTPUT_FILE = ROOT_DIR / "data" / "processed" / "fss_transcriptions.json"

    # 입력 디렉토리 확인
    if not INPUT_DIR.exists():
        logger.error(f"입력 디렉토리가 존재하지 않습니다: {INPUT_DIR}")
        logger.error("먼저 금감원 데이터를 data/raw/금감원_보이스피싱/ 에 복사하세요.")
        return

    # 전사 실행
    transcriptions = transcribe_fss_dataset(
        input_dir=INPUT_DIR,
        output_file=OUTPUT_FILE,
        model_size="base"  # base 모델 사용 (속도와 정확도 균형)
    )

    if transcriptions:
        logger.info(f"\n다음 단계: Vector DB 업데이트")
        logger.info(f"실행 명령: python scripts/build_vector_db.py")


if __name__ == "__main__":
    main()
