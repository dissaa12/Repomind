"""
backend/retrieval/hybrid_retriever.py - Hybrid Dense + BM25 Code Retriever
Combines ChromaDB vector embeddings with BM25 keyword matching and symbol boosting.
"""

import re
from typing import Any, Dict, List, Optional
from config import get_settings
from retrieval.vector_store import get_vector_store
from retrieval.bm25_index import get_bm25_index


def extract_potential_symbols(query: str) -> List[str]:
    """Extracts identifiers from query that might be function/class/file names."""
    words = re.findall(r"[a-zA-Z_][a-zA-Z0-9_\.]*", query)
    return [w.lower() for w in words if len(w) >= 3]


def retrieve_hybrid_chunks(
    repo_id: str,
    query: str,
    top_k: Optional[int] = None,
    chunk_map: Optional[Dict[str, Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Performs hybrid retrieval combining ChromaDB dense vector search with BM25 lexical search.
    """
    settings = get_settings()
    k = top_k or settings.top_k

    # 1. Dense Vector Retrieval
    vector_store = get_vector_store()
    dense_hits = vector_store.query(repo_id=repo_id, query_text=query, top_k=k * 2)

    # 2. Sparse BM25 Retrieval
    bm25_index = get_bm25_index(repo_id)
    bm25_hits = bm25_index.query(query_text=query, top_k=k * 2) if bm25_index else []

    # Map candidate chunks by ID
    candidate_scores: Dict[str, float] = {}
    chunk_info_map: Dict[str, Dict[str, Any]] = {}

    # Weight factors
    w_dense = settings.dense_weight
    w_bm25 = settings.bm25_weight

    for hit in dense_hits:
        cid = hit["id"]
        candidate_scores[cid] = candidate_scores.get(cid, 0.0) + (hit["score"] * w_dense)
        meta = hit.get("metadata") or {}
        chunk_info_map[cid] = {
            "id": cid,
            "file_path": meta.get("file_path", ""),
            "symbol_name": meta.get("symbol_name", ""),
            "symbol_type": meta.get("symbol_type", ""),
            "start_line": meta.get("start_line", 1),
            "end_line": meta.get("end_line", 1),
            "code": hit.get("text", ""),
        }

    for hit in bm25_hits:
        cid = hit["id"]
        candidate_scores[cid] = candidate_scores.get(cid, 0.0) + (hit["score"] * w_bm25)
        if cid not in chunk_info_map and "chunk" in hit:
            c = hit["chunk"]
            chunk_info_map[cid] = {
                "id": cid,
                "file_path": c.get("file_path", ""),
                "symbol_name": c.get("symbol_name", ""),
                "symbol_type": c.get("symbol_type", ""),
                "start_line": c.get("start_line", 1),
                "end_line": c.get("end_line", 1),
                "code": c.get("code") or c.get("search_text", ""),
            }

    # 3. Symbol Match Boost
    query_symbols = extract_potential_symbols(query)
    for cid, info in chunk_info_map.items():
        sym = (info.get("symbol_name") or "").lower()
        fpath = (info.get("file_path") or "").lower()
        for q_sym in query_symbols:
            if q_sym in sym or q_sym in fpath:
                candidate_scores[cid] = candidate_scores.get(cid, 0.0) * settings.symbol_match_boost
                break

    # If external chunk_map has actual original code snippet, enrich chunk info
    if chunk_map:
        for cid, info in chunk_info_map.items():
            if cid in chunk_map:
                orig = chunk_map[cid]
                info["code"] = orig.get("code", info["code"])
                info["context_header"] = orig.get("context_header", "")

    # Sort candidates by combined score
    ranked = sorted(
        candidate_scores.items(),
        key=lambda item: item[1],
        reverse=True
    )

    final_chunks: List[Dict[str, Any]] = []
    for cid, score in ranked[:k]:
        info = chunk_info_map.get(cid, {})
        final_chunks.append({
            "id": cid,
            "file_path": info.get("file_path", ""),
            "symbol_name": info.get("symbol_name", ""),
            "symbol_type": info.get("symbol_type", ""),
            "start_line": int(info.get("start_line", 1)),
            "end_line": int(info.get("end_line", 1)),
            "score": round(score, 4),
            "code": info.get("code", ""),
            "context_header": info.get("context_header", ""),
            "citation": f"{info.get('file_path')}:{info.get('start_line')}-{info.get('end_line')}",
        })

    return final_chunks
