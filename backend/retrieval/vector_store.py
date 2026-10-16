"""
backend/retrieval/vector_store.py - ChromaDB Vector Store Manager
Provides high-speed local dense embedding storage and cosine similarity search.
"""

import hashlib
from typing import Any, Dict, List, Optional
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from chromadb.config import Settings as ChromaSettings
import numpy as np
from config import get_settings


class FastLocalDenseEmbedding(EmbeddingFunction[Documents]):
    """
    Ultra-fast, deterministic local embedding function producing 384-dimensional dense vectors
    without requiring external model downloads.
    """
    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def name(self) -> str:
        return "fast_local_embedding"

    def __call__(self, input: Documents) -> Embeddings:
        results: Embeddings = []
        for text in input:
            vec = np.zeros(self.dimension, dtype=np.float32)
            words = text.lower().replace("\n", " ").split()
            for w in words:
                if not w:
                    continue
                h = int(hashlib.md5(w.encode("utf-8")).hexdigest()[:8], 16)
                idx = h % self.dimension
                sign = 1.0 if (h >> 5) & 1 else -1.0
                vec[idx] += sign

                if len(w) >= 4:
                    for i in range(len(w) - 2):
                        tri = w[i : i + 3]
                        h_tri = int(hashlib.md5(tri.encode("utf-8")).hexdigest()[:8], 16)
                        idx_tri = h_tri % self.dimension
                        sign_tri = 1.0 if (h_tri >> 3) & 1 else -1.0
                        vec[idx_tri] += sign_tri * 0.5

            norm = np.linalg.norm(vec)
            if norm > 0.0:
                vec = vec / norm
            results.append(vec.tolist())
        return results


class ChromaVectorStore:
    def __init__(self):
        settings = get_settings()
        settings.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(settings.chroma_dir),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.embedding_fn = FastLocalDenseEmbedding(dimension=384)

    def _get_collection_name(self, repo_id: str) -> str:
        clean = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in repo_id)
        if len(clean) < 3:
            clean = f"repo_{clean}"
        return f"repo_{clean[:55]}".lower()

    def get_or_create_collection(self, repo_id: str):
        name = self._get_collection_name(repo_id)
        return self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

    def delete_repo_collection(self, repo_id: str) -> None:
        name = self._get_collection_name(repo_id)
        try:
            self.client.delete_collection(name=name)
        except Exception:
            pass

    def index_chunks(self, repo_id: str, chunks: List[Dict[str, Any]]) -> None:
        if not chunks:
            return

        collection = self.get_or_create_collection(repo_id)
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            ids = [c["id"] for c in batch]
            documents = [c["search_text"] for c in batch]
            metadatas = [
                {
                    "file_path": c["file_path"],
                    "language": c.get("language", ""),
                    "symbol_name": c.get("symbol_name", ""),
                    "symbol_type": c.get("symbol_type", ""),
                    "start_line": int(c.get("start_line", 1)),
                    "end_line": int(c.get("end_line", 1)),
                    "docstring": (c.get("docstring") or "")[:300],
                }
                for c in batch
            ]

            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )

    def query(self, repo_id: str, query_text: str, top_k: int = 10) -> List[Dict[str, Any]]:
        collection = self.get_or_create_collection(repo_id)
        count = collection.count()
        if count == 0:
            return []

        actual_k = min(top_k, count)
        results = collection.query(
            query_texts=[query_text],
            n_results=actual_k,
            include=["documents", "metadatas", "distances"]
        )

        hits: List[Dict[str, Any]] = []
        if not results or not results["ids"] or not results["ids"][0]:
            return []

        ids = results["ids"][0]
        docs = results["documents"][0] if results["documents"] else []
        metas = results["metadatas"][0] if results["metadatas"] else []
        distances = results["distances"][0] if results["distances"] else []

        for chunk_id, doc, meta, dist in zip(ids, docs, metas, distances):
            cosine_sim = max(0.0, 1.0 - (dist / 2.0)) if dist is not None else 0.5
            hits.append({
                "id": chunk_id,
                "score": cosine_sim,
                "text": doc,
                "metadata": meta,
            })

        return hits


_vector_store_instance = None

def get_vector_store() -> ChromaVectorStore:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = ChromaVectorStore()
    return _vector_store_instance
