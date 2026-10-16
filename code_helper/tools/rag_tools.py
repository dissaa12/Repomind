"""
code_helper/tools/rag_tools.py - Vector Database RAG Search Tool
Supports Pinecone serverless search with transparent ChromaDB local fallback.
"""

# pyright: reportMissingImports=false
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

# Ensure backend directory and virtualenv site-packages are in sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

VENV_SITE_PACKAGES = BACKEND_DIR / ".venv" / "Lib" / "site-packages"
if VENV_SITE_PACKAGES.exists() and str(VENV_SITE_PACKAGES) not in sys.path:
    sys.path.insert(0, str(VENV_SITE_PACKAGES))

# Dynamic imports with graceful fallbacks
try:
    from pinecone import Pinecone
except ImportError:
    Pinecone = None

try:
    from backend.retrieval.hybrid_retriever import retrieve_hybrid_chunks
except ImportError:
    try:
        from retrieval.hybrid_retriever import retrieve_hybrid_chunks
    except ImportError:
        retrieve_hybrid_chunks = None


def rag_search(query: str) -> str:
    """
    Searches the codebase vector index for relevant code snippets matching the query.
    Use this tool whenever asking where something is in the code or seeking functions
    related to a specific topic.
    """
    clean_query = query.strip()
    if not clean_query:
        return "I could not find that. Please provide a search query."

    pinecone_key = os.getenv("PINECONE_API_KEY", "").strip()
    index_name = os.getenv("PINECONE_INDEX_NAME", "code-helper")

    # 1. Try Pinecone if key is present and Pinecone client is installed
    if pinecone_key and Pinecone is not None:
        try:
            pc = Pinecone(api_key=pinecone_key)
            if index_name in [idx.name for idx in pc.list_indexes()]:
                index = pc.Index(index_name)
                results = index.query(
                    vector=[0.0] * 2048,
                    top_k=4,
                    include_metadata=True
                )
                if results and results.get("matches"):
                    output = [f"Found {len(results['matches'])} relevant code matches in Pinecone:"]
                    for m in results["matches"]:
                        meta = m.get("metadata", {})
                        fpath = meta.get("file_path", "unknown")
                        lines = f"{meta.get('start_line', 1)}-{meta.get('end_line', 1)}"
                        text = meta.get("text", "")[:350]
                        output.append(f"\n--- [{fpath} Lines {lines}] (Score: {m.get('score', 0):.3f}) ---")
                        output.append(text)
                    return "\n".join(output)
        except Exception:
            # Fall through to local ChromaDB search
            pass

    # 2. Local ChromaDB / Workspace Fallback
    if retrieve_hybrid_chunks is not None:
        try:
            chunks = retrieve_hybrid_chunks("repomind", clean_query, top_k=4)
            if not chunks:
                chunks = retrieve_hybrid_chunks("naive_rag_demo", clean_query, top_k=4)

            if not chunks:
                return f"I could not find that in the indexed code for query: '{clean_query}'."

            output = [f"Found {len(chunks)} relevant code matches (Hybrid Vector + Lexical Search):"]
            for c in chunks:
                fpath = c.get("file_path", "code")
                start = c.get("start_line", 1)
                end = c.get("end_line", 1)
                sym = c.get("symbol_name") or "snippet"
                score = c.get("score", 0.0)
                code_preview = c.get("code", "")[:400]
                output.append(f"\n--- [{fpath}:{start}-{end} ({sym})] (Relevance: {score:.3f}) ---")
                output.append(code_preview)

            return "\n".join(output)
        except Exception as e:
            return f"I could not find that. Vector search encountered an error: {e}"

    return "I could not find that. Vector retrieval service is currently initializing."
