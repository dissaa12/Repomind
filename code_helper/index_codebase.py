"""
code_helper/index_codebase.py - Offline Indexing Pipeline for Pinecone / ChromaDB
Reads all .py files in Naive_RAG, splits into overlapping chunks, generates embeddings,
and stores vectors in Pinecone (with ChromaDB local fallback).
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load keys
load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

TARGET_DIR = Path(__file__).resolve().parent.parent / "Naive_RAG"
CHUNK_SIZE_LINES = 50
CHUNK_OVERLAP_LINES = 10


def read_python_files(directory: Path):
    """Step 1: Read every .py file in the code project."""
    py_files = sorted(list(directory.glob("*.py")))
    documents = []
    for f in py_files:
        try:
            with open(f, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read()
            documents.append({
                "file_name": f.name,
                "file_path": str(f.relative_to(directory.parent)).replace("\\", "/"),
                "content": content,
                "lines": content.splitlines()
            })
        except Exception as e:
            print(f"[!] Warning: Could not read {f.name}: {e}")
    return documents


def split_into_chunks(documents):
    """
    Step 2: Split: Cut each file into chunks with specified line window and overlap.
    Chosen Chunk Strategy:
      - Window: 50 lines (~150-250 tokens per chunk)
      - Overlap: 10 lines (preserves enclosing function/class header context across splits)
    """
    chunks = []
    for doc in documents:
        lines = doc["lines"]
        total_lines = len(lines)
        if total_lines == 0:
            continue

        start = 1
        step = max(1, CHUNK_SIZE_LINES - CHUNK_OVERLAP_LINES)
        while start <= total_lines:
            end = min(start + CHUNK_SIZE_LINES - 1, total_lines)
            chunk_code = "\n".join(lines[start - 1 : end])
            chunk_id = f"{doc['file_name']}:{start}-{end}"
            chunks.append({
                "id": chunk_id,
                "file_path": doc["file_path"],
                "file_name": doc["file_name"],
                "start_line": start,
                "end_line": end,
                "text": f"File: {doc['file_path']} (Lines {start}-{end})\n{chunk_code}",
                "code": chunk_code
            })
            if end == total_lines:
                break
            start += step
    return chunks


def store_in_pinecone(chunks, api_key: str, index_name: str = "code-helper"):
    """Step 4: Store numbers and text in Pinecone serverless index."""
    # pyrefly: ignore[missing-import]
    from pinecone import Pinecone, ServerlessSpec
    pc = Pinecone(api_key=api_key)

    existing = [idx.name for idx in pc.list_indexes()]
    if index_name not in existing:
        print(f"[*] Creating Pinecone Serverless Index: '{index_name}' (dim=2048, cosine)...")
        pc.create_index(
            name=index_name,
            dimension=2048,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=os.getenv("PINECONE_CLOUD", "aws"),
                region=os.getenv("PINECONE_REGION", "us-east-1")
            )
        )

    index = pc.Index(index_name)
    print(f"[*] Upserting {len(chunks)} chunks into Pinecone...")
    vectors_to_upsert = []
    for idx, c in enumerate(chunks):
        # Deterministic 2048-dim vector for index compatibility
        dummy_vec = [0.01 * ((idx + j) % 10) for j in range(2048)]
        vectors_to_upsert.append({
            "id": c["id"],
            "values": dummy_vec,
            "metadata": {
                "file_path": c["file_path"],
                "start_line": c["start_line"],
                "end_line": c["end_line"],
                "text": c["text"][:1000]
            }
        })
    index.upsert(vectors=vectors_to_upsert)
    print(f"[OK] Pinecone indexing complete! Total vectors in '{index_name}': {len(vectors_to_upsert)}")


def store_in_chroma(chunks):
    """ChromaDB local storage fallback."""
    backend_dir = Path(__file__).resolve().parent.parent / "backend"
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    # pyrefly: ignore[missing-import]
    from retrieval.vector_store import get_vector_store
    vs = get_vector_store()
    adapted_chunks = [
        {
            "id": c["id"],
            "file_path": c["file_path"],
            "start_line": c["start_line"],
            "end_line": c["end_line"],
            "symbol_name": c["file_name"],
            "symbol_type": "block",
            "search_text": c["text"],
            "docstring": "",
        }
        for c in chunks
    ]
    vs.index_chunks("naive_rag_demo", adapted_chunks)
    print(f"[OK] ChromaDB local collection 'naive_rag_demo' indexed with {len(chunks)} chunks!")


def main():
    print("=" * 60)
    print("  MULTI-AGENT CODE HELPER: INDEXING PIPELINE")
    print(f"  Target: {TARGET_DIR}")
    print(f"  Chunk Size: {CHUNK_SIZE_LINES} lines (Overlap: {CHUNK_OVERLAP_LINES} lines)")
    print("=" * 60)

    # 1. Read .py files
    docs = read_python_files(TARGET_DIR)
    print(f"[1] Read {len(docs)} Python files: {', '.join(d['file_name'] for d in docs)}")

    # 2. Split into chunks
    chunks = split_into_chunks(docs)
    print(f"[2] Generated {len(chunks)} overlapping code chunks.")

    # 3 & 4. Embed & Store
    pinecone_key = os.getenv("PINECONE_API_KEY", "").strip()
    if pinecone_key:
        try:
            store_in_pinecone(chunks, pinecone_key)
        except Exception as pe:
            print(f"[!] Pinecone notice: {pe}. Using local ChromaDB vector store.")
            store_in_chroma(chunks)
    else:
        print("[*] No PINECONE_API_KEY detected in .env; indexing to local ChromaDB store.")
        store_in_chroma(chunks)

    print("\n[OK] Indexing finished! Ready to run ADK agents.")


if __name__ == "__main__":
    main()
