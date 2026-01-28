"""
금감원 전사 데이터를 Vector DB에 추가하는 스크립트
"""
import sys
import json
from pathlib import Path
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.vector_db.vector_store import PhishingVectorStore


def main():
    ROOT_DIR = Path(__file__).parent.parent
    FSS_DATA = ROOT_DIR / "data" / "processed" / "fss_transcriptions.json"
    VECTOR_DB_NAME = "phishing_vector_db"

    print("=" * 70)
    print("Sentinel-Voice: 금감원 데이터 Vector DB 통합")
    print("=" * 70)

    # Load FSS transcriptions
    if not FSS_DATA.exists():
        print(f"\n❌ 오류: 전사 파일을 찾을 수 없습니다: {FSS_DATA}")
        print("먼저 전사 스크립트를 실행하세요:")
        print("  python scripts/transcribe_fss_data.py")
        sys.exit(1)

    print(f"\n📂 전사 데이터 로딩: {FSS_DATA}")
    with open(FSS_DATA, 'r', encoding='utf-8') as f:
        fss_data = json.load(f)

    transcriptions = fss_data['transcriptions']
    metadata = fss_data['metadata']

    print(f"✓ 로드 완료: {len(transcriptions)}개 항목")
    print(f"  출처: {metadata['source']}")
    print(f"  모델: {metadata['whisper_model']}")
    print(f"  전사 일시: {metadata['transcribed_at']}")

    # Initialize or load existing vector store
    vector_store = PhishingVectorStore(model_name="jhgan/ko-sroberta-multitask")

    # Check if existing database exists
    db_path = ROOT_DIR / "data" / "vector_db" / f"{VECTOR_DB_NAME}.faiss"
    if db_path.exists():
        print(f"\n📦 기존 Vector DB 로드: {db_path}")
        vector_store.load(VECTOR_DB_NAME)
        stats_before = vector_store.get_statistics()
        print(f"  현재 스크립트 수: {stats_before['total_scripts']}")
    else:
        print("\n🆕 새로운 Vector DB 생성")

    # Prepare data for vector DB
    print("\n🔧 Vector DB에 추가할 데이터 준비 중...")
    scripts_to_add = []

    for entry in transcriptions:
        # 전사된 텍스트 가져오기
        script = entry['transcript']

        # 메타데이터 구성
        meta = {
            'id': entry['id'],
            'source': entry['source'],
            'category': entry['category'],
            'type': entry['type'],
            'label': entry['label'],
            'severity': entry['severity'],
            'techniques': entry['techniques'],
            'file_name': entry['file_name'],
            'duration': entry['duration']
        }

        scripts_to_add.append((script, meta))

    print(f"  준비 완료: {len(scripts_to_add)}개 스크립트")

    # Add to vector store
    print("\n➕ Vector DB에 추가 중...")
    scripts_list = [script for script, _ in scripts_to_add]
    metadata_list = [meta for _, meta in scripts_to_add]

    vector_store.add_phishing_scripts(scripts_list, metadata_list)
    print(f"✓ 추가 완료: {len(scripts_to_add)}개")

    # Save vector database
    print(f"\n💾 Vector DB 저장: {VECTOR_DB_NAME}")
    vector_store.save(VECTOR_DB_NAME)

    # Print statistics
    stats = vector_store.get_statistics()
    print("\n" + "=" * 70)
    print("Vector Database 통계")
    print("=" * 70)
    print(f"총 스크립트 수:       {stats['total_scripts']}")
    print(f"임베딩 차원:          {stats['embedding_dimension']}")
    print(f"모델:                 {stats['model_name']}")
    print(f"인덱스 타입:          {stats['index_type']}")

    # Category breakdown
    print(f"\n카테고리별 분포:")
    for cat_name, cat_info in metadata['categories'].items():
        count = cat_info['count']
        label = cat_info['label']
        severity = cat_info['severity']
        print(f"  - {cat_name}: {count}개 ({label}, {severity})")

    print("=" * 70)
    print("\n✓ Vector DB 구축 완료!")

    # Test search
    print("\n🔍 검색 기능 테스트...")
    test_queries = [
        "검찰청에서 전화가 왔어요",
        "계좌번호를 알려달라고 합니다",
        "안전계좌로 송금하라고 해요",
        "대출 받을 수 있다고 합니다",
        "아르바이트 제안을 받았어요"
    ]

    for query in test_queries:
        print(f"\n질의: \"{query}\"")
        results = vector_store.search(query, top_k=2)
        for i, (script, score, meta) in enumerate(results, 1):
            category = meta.get('category', 'Unknown')
            label = meta.get('label', 'Unknown')
            print(f"  {i}. 유사도: {score:.4f} | {category} ({label})")
            print(f"     {script[:60]}...")

    print("\n" + "=" * 70)
    print("다음 단계: 서버 실행 및 웹 데모 테스트")
    print("실행 명령: python scripts/run_server.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
