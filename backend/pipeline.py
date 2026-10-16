"""
backend/pipeline.py - Core Orchestration Engine for Ingestion, Indexing, and Querying
"""

import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from config import get_settings
from db.database import (
    init_db,
    upsert_repository,
    get_repository,
    get_repositories,
    save_repo_files,
    get_repo_files,
)
from ingestion.file_crawler import crawl_repository
from ingestion.git_cloner import clone_or_update_repo
from parser.code_chunker import chunk_file
from retrieval.vector_store import get_vector_store
from retrieval.bm25_index import register_bm25_index
from retrieval.hybrid_retriever import retrieve_hybrid_chunks


# In-memory chunk map: {repo_id: {chunk_id: chunk_dict}}
_repo_chunk_cache: Dict[str, Dict[str, Dict[str, Any]]] = {}


def get_repo_chunks_map(repo_id: str) -> Dict[str, Dict[str, Any]]:
    return _repo_chunk_cache.get(repo_id, {})


def index_directory(
    root_path: Path,
    repo_id: str,
    name: str,
    source_type: str,
    source_path: str
) -> Dict[str, Any]:
    """
    Executes the full indexing pipeline:
    1. Crawl files
    2. Syntax & scope-aware chunking
    3. Dense ChromaDB vector indexing
    4. Sparse BM25 indexing
    5. SQLite metadata persistence
    """
    settings = get_settings()
    init_db()

    # Step 1: Crawl files
    files = crawl_repository(root_path)
    if not files:
        raise ValueError(f"No indexable source code files found in {root_path}")

    # Count languages and prepare file records
    languages: Dict[str, int] = {}
    db_file_records = []
    all_chunks: List[Dict[str, Any]] = []

    for f in files:
        lang = f["language"]
        languages[lang] = languages.get(lang, 0) + 1
        db_file_records.append({
            "id": str(uuid.uuid4()),
            "relative_path": f["relative_path"],
            "language": lang,
            "line_count": f["line_count"],
            "size_bytes": f["size_bytes"]
        })

        # Step 2: Syntax & scope-aware chunking
        file_chunks = chunk_file(f)
        all_chunks.extend(file_chunks)

    # Step 3: Dense ChromaDB vector indexing
    vector_store = get_vector_store()
    vector_store.index_chunks(repo_id, all_chunks)

    # Step 4: Sparse BM25 indexing
    register_bm25_index(repo_id, all_chunks)

    # Cache chunk details in memory for fast snippet retrieval
    _repo_chunk_cache[repo_id] = {c["id"]: c for c in all_chunks}

    # Step 5: Save SQLite metadata
    upsert_repository(
        repo_id=repo_id,
        name=name,
        source_type=source_type,
        source_path=source_path,
        file_count=len(files),
        chunk_count=len(all_chunks),
        languages=languages
    )
    save_repo_files(repo_id, db_file_records)

    return {
        "repo_id": repo_id,
        "name": name,
        "source_type": source_type,
        "file_count": len(files),
        "chunk_count": len(all_chunks),
        "languages": languages,
    }


def index_local_repo(dir_path_str: str, custom_name: Optional[str] = None) -> Dict[str, Any]:
    path = Path(dir_path_str).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Local path does not exist: {path}")

    name = custom_name or path.name
    repo_id = name.lower().replace(" ", "_").replace("-", "_")
    return index_directory(
        root_path=path,
        repo_id=repo_id,
        name=name,
        source_type="local",
        source_path=str(path)
    )


def index_github_repo(url_or_slug: str) -> Dict[str, Any]:
    clone_info = clone_or_update_repo(url_or_slug)
    repo_id = clone_info["repo_id"]
    local_dir = Path(clone_info["local_path"])
    return index_directory(
        root_path=local_dir,
        repo_id=repo_id,
        name=clone_info["name"],
        source_type="github",
        source_path=clone_info["url"]
    )


def auto_index_workspace_if_empty() -> None:
    """
    If no repositories exist in DB on startup, automatically index the current workspace.
    """
    init_db()
    repos = get_repositories()
    if not repos:
        workspace_dir = Path(__file__).resolve().parent.parent
        try:
            print(f"[*] Repomind: Auto-indexing current workspace: {workspace_dir}")
            index_local_repo(str(workspace_dir), custom_name="Repomind")
            print("[+] Workspace indexing complete!")
        except Exception as e:
            print(f"[!] Auto-index workspace notice: {e}")
