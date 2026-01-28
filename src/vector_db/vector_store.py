"""
Vector database implementation for phishing script similarity search
Uses FAISS for fast similarity search with sentence embeddings
"""
import json
import pickle
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import logging

from src.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PhishingVectorStore:
    """
    Vector store for phishing scripts using FAISS
    Enables RAG-based similarity search for real-time detection
    """

    def __init__(
        self,
        model_name: str = "jhgan/ko-sroberta-multitask",
        vector_db_path: Optional[Path] = None
    ):
        """
        Args:
            model_name: HuggingFace model for Korean sentence embeddings
            vector_db_path: Path to save/load vector database
        """
        self.model_name = model_name
        self.vector_db_path = vector_db_path or config.data_dir / "vector_db"
        self.vector_db_path.mkdir(parents=True, exist_ok=True)

        # Load sentence transformer model
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()

        # FAISS index
        self.index = None
        self.scripts = []  # Store original scripts
        self.metadata = []  # Store metadata for each script

    def add_phishing_scripts(
        self,
        scripts: List[str],
        metadata: Optional[List[Dict]] = None
    ):
        """
        Add phishing scripts to the vector database

        Args:
            scripts: List of phishing conversation scripts
            metadata: Optional metadata for each script (e.g., type, severity)
        """
        if not scripts:
            logger.warning("No scripts provided")
            return

        logger.info(f"Adding {len(scripts)} scripts to vector database...")

        # Generate embeddings
        embeddings = self.model.encode(
            scripts,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True  # Normalize for cosine similarity
        )

        # Initialize FAISS index if not exists
        if self.index is None:
            # Use IndexFlatIP for cosine similarity (with normalized vectors)
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            logger.info(f"Created FAISS index with dimension {self.embedding_dim} (Cosine Similarity)")

        # Add to FAISS index
        self.index.add(embeddings.astype('float32'))

        # Store scripts and metadata
        self.scripts.extend(scripts)

        if metadata:
            self.metadata.extend(metadata)
        else:
            self.metadata.extend([{} for _ in scripts])

        logger.info(f"Total scripts in database: {len(self.scripts)}")

    def search(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[Tuple[str, float, Dict]]:
        """
        Search for similar phishing scripts

        Args:
            query: Query text
            top_k: Number of results to return
            score_threshold: Minimum similarity score (0-1, optional)

        Returns:
            List of (script, similarity_score, metadata) tuples
        """
        if self.index is None or len(self.scripts) == 0:
            logger.warning("Vector database is empty")
            return []

        # Encode query (normalize for cosine similarity)
        query_embedding = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)

        # Search in FAISS
        scores, indices = self.index.search(
            query_embedding.astype('float32'),
            min(top_k, len(self.scripts))
        )

        # IndexFlatIP returns cosine similarity (higher is better, range -1 to 1)
        # Convert to 0-1 range: (score + 1) / 2
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.scripts):
                # Convert cosine similarity (-1 to 1) to 0-1 range
                similarity = (float(score) + 1.0) / 2.0

                if score_threshold is None or similarity >= score_threshold:
                    results.append((
                        self.scripts[idx],
                        similarity,
                        self.metadata[idx]
                    ))

        return results

    def save(self, name: str = "phishing_vector_db"):
        """
        Save vector database to disk

        Args:
            name: Database name
        """
        if self.index is None:
            logger.warning("No index to save")
            return

        # Save FAISS index
        index_path = self.vector_db_path / f"{name}.index"
        faiss.write_index(self.index, str(index_path))

        # Save scripts and metadata
        data = {
            "scripts": self.scripts,
            "metadata": self.metadata,
            "model_name": self.model_name,
            "embedding_dim": self.embedding_dim
        }

        data_path = self.vector_db_path / f"{name}.pkl"
        with open(data_path, 'wb') as f:
            pickle.dump(data, f)

        logger.info(f"Vector database saved to {self.vector_db_path}")

    def load(self, name: str = "phishing_vector_db"):
        """
        Load vector database from disk

        Args:
            name: Database name
        """
        index_path = self.vector_db_path / f"{name}.index"
        data_path = self.vector_db_path / f"{name}.pkl"

        if not index_path.exists() or not data_path.exists():
            logger.warning(f"Vector database not found at {self.vector_db_path}")
            return False

        # Load FAISS index
        self.index = faiss.read_index(str(index_path))

        # Load scripts and metadata
        with open(data_path, 'rb') as f:
            data = pickle.load(f)

        self.scripts = data["scripts"]
        self.metadata = data["metadata"]

        logger.info(f"Loaded vector database with {len(self.scripts)} scripts")
        return True

    def build_from_labeled_data(self, labeled_data_path: Path):
        """
        Build vector database from labeled conversation data

        Args:
            labeled_data_path: Path to labeled dataset JSON
        """
        logger.info(f"Building vector database from {labeled_data_path}")

        with open(labeled_data_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)

        scripts = []
        metadata = []

        for conversation in dataset.get("conversations", []):
            # Extract phishing segments
            for segment in conversation.get("segments", []):
                tags = segment.get("tags", [])

                # Only add segments with phishing tags
                if any(tag in ["협박", "개인정보요구", "송금유도"] for tag in tags):
                    scripts.append(segment["text"])
                    metadata.append({
                        "tags": tags,
                        "speaker": segment.get("speaker", "UNKNOWN"),
                        "audio_file": conversation.get("audio_file", ""),
                        "is_phishing": True
                    })

        if scripts:
            self.add_phishing_scripts(scripts, metadata)
            logger.info(f"Built vector database with {len(scripts)} phishing segments")
        else:
            logger.warning("No phishing segments found in labeled data")

    def get_statistics(self) -> Dict:
        """Get statistics about the vector database"""
        return {
            "total_scripts": len(self.scripts),
            "embedding_dimension": self.embedding_dim,
            "model_name": self.model_name,
            "index_type": type(self.index).__name__ if self.index else None
        }


def main():
    """Example usage"""
    vector_store = PhishingVectorStore()

    # Example: Add some phishing scripts
    example_scripts = [
        "검찰청입니다. 당신의 계좌가 범죄에 사용되었습니다.",
        "금융감독원인데요. 즉시 계좌번호를 확인해야 합니다.",
        "경찰청입니다. 지금 바로 안전계좌로 송금하세요.",
        "국세청입니다. 체납된 세금을 즉시 납부하세요.",
    ]

    example_metadata = [
        {"type": "prosecutor_impersonation", "severity": "high"},
        {"type": "fss_impersonation", "severity": "high"},
        {"type": "police_impersonation", "severity": "high"},
        {"type": "nts_impersonation", "severity": "medium"},
    ]

    vector_store.add_phishing_scripts(example_scripts, example_metadata)

    # Save
    vector_store.save()

    # Search
    query = "검찰에서 전화가 왔는데 계좌 확인을 요구합니다"
    results = vector_store.search(query, top_k=3)

    print("\n" + "=" * 60)
    print(f"Query: {query}")
    print("=" * 60)

    for i, (script, score, meta) in enumerate(results, 1):
        print(f"\n{i}. Similarity: {score:.4f}")
        print(f"   Script: {script}")
        print(f"   Metadata: {meta}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
