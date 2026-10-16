"""
backend/retrieval/bm25_index.py - BM25 Sparse Lexical Search Index for Code
Enables exact matching for identifiers, function names, and variable symbols.
"""

import re
from typing import Any, Dict, List, Optional
from rank_bm25 import BM25Okapi


def tokenize_code(text: str) -> List[str]:
    """
    Tokenizes code into individual keywords, identifier tokens, and subwords.
    Handles snake_case, camelCase, and punctuation.
    """
    # Split on non-alphanumeric characters
    raw_tokens = re.findall(r"[a-zA-Z0-9_]+", text)
    tokens: List[str] = []

    for t in raw_tokens:
        lower_t = t.lower()
        tokens.append(lower_t)
        # Split camelCase: e.g. "parsePythonAST" -> "parse", "python", "ast"
        subwords = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)", t)
        for s in subwords:
            ls = s.lower()
            if ls != lower_t:
                tokens.append(ls)
        # Split snake_case: e.g. "file_crawler" -> "file", "crawler"
        if "_" in lower_t:
            for part in lower_t.split("_"):
                if part and part != lower_t:
                    tokens.append(part)

    return tokens


class BM25RepoIndex:
    def __init__(self, repo_id: str, chunks: List[Dict[str, Any]]):
        self.repo_id = repo_id
        self.chunks = chunks
        self.chunk_ids = [c["id"] for c in chunks]

        # Pre-tokenize all chunk search texts
        corpus = [tokenize_code(c.get("search_text", "") + " " + c.get("file_path", "")) for c in chunks]
        self.bm25 = BM25Okapi(corpus) if corpus else None

    def query(self, query_text: str, top_k: int = 10) -> List[Dict[str, Any]]:
        if not self.bm25 or not self.chunks:
            return []

        tokens = tokenize_code(query_text)
        if not tokens:
            return []

        scores = self.bm25.get_scores(tokens)
        max_score = max(scores) if len(scores) > 0 and max(scores) > 0 else 1.0

        scored_pairs = []
        for idx, score in enumerate(scores):
            if score > 0:
                normalized_score = float(score) / float(max_score)
                chunk = self.chunks[idx]
                scored_pairs.append({
                    "id": chunk["id"],
                    "score": normalized_score,
                    "chunk": chunk
                })

        scored_pairs.sort(key=lambda x: x["score"], reverse=True)
        return scored_pairs[:top_k]


# Registry of in-memory BM25 indices per repo
_bm25_registry: Dict[str, BM25RepoIndex] = {}


def register_bm25_index(repo_id: str, chunks: List[Dict[str, Any]]) -> None:
    _bm25_registry[repo_id] = BM25RepoIndex(repo_id, chunks)


def get_bm25_index(repo_id: str) -> Optional[BM25RepoIndex]:
    return _bm25_registry.get(repo_id)
