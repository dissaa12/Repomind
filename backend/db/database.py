"""
backend/db/database.py - SQLite Persistence for Repositories, Files, and Chat Sessions
"""

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from config import get_settings


def get_connection() -> sqlite3.Connection:
    settings = get_settings()
    settings.sqlite_db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(settings.sqlite_db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize database tables with schema."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repositories (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                source_type TEXT NOT NULL, -- 'local' or 'github'
                source_path TEXT NOT NULL,
                indexed_at TEXT NOT NULL,
                file_count INTEGER DEFAULT 0,
                chunk_count INTEGER DEFAULT 0,
                languages TEXT DEFAULT '{}'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repo_files (
                id TEXT PRIMARY KEY,
                repo_id TEXT NOT NULL,
                relative_path TEXT NOT NULL,
                language TEXT NOT NULL,
                line_count INTEGER DEFAULT 0,
                size_bytes INTEGER DEFAULT 0,
                FOREIGN KEY (repo_id) REFERENCES repositories (id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                repo_id TEXT NOT NULL,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (repo_id) REFERENCES repositories (id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL, -- 'user' or 'assistant'
                content TEXT NOT NULL,
                citations TEXT DEFAULT '[]',
                model_used TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
            )
        """)
        conn.commit()


def upsert_repository(
    repo_id: str,
    name: str,
    source_type: str,
    source_path: str,
    file_count: int,
    chunk_count: int,
    languages: Dict[str, int]
) -> Dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        cursor.execute("""
            INSERT INTO repositories (id, name, source_type, source_path, indexed_at, file_count, chunk_count, languages)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                source_type=excluded.source_type,
                source_path=excluded.source_path,
                indexed_at=excluded.indexed_at,
                file_count=excluded.file_count,
                chunk_count=excluded.chunk_count,
                languages=excluded.languages
        """, (repo_id, name, source_type, source_path, now, file_count, chunk_count, json.dumps(languages)))
        conn.commit()
    return get_repository(repo_id) or {}


def get_repositories() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM repositories ORDER BY indexed_at DESC")
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["languages"] = json.loads(d.get("languages") or "{}")
            result.append(d)
        return result


def get_repository(repo_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM repositories WHERE id = ?", (repo_id,))
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        d["languages"] = json.loads(d.get("languages") or "{}")
        return d


def delete_repository(repo_id: str) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM repositories WHERE id = ?", (repo_id,))
        cursor.execute("DELETE FROM repo_files WHERE repo_id = ?", (repo_id,))
        cursor.execute("DELETE FROM conversations WHERE repo_id = ?", (repo_id,))
        conn.commit()


def save_repo_files(repo_id: str, files_data: List[Dict[str, Any]]) -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM repo_files WHERE repo_id = ?", (repo_id,))
        for f in files_data:
            cursor.execute("""
                INSERT INTO repo_files (id, repo_id, relative_path, language, line_count, size_bytes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                f.get("id") or str(uuid.uuid4()),
                repo_id,
                f["relative_path"],
                f.get("language", "text"),
                f.get("line_count", 0),
                f.get("size_bytes", 0)
            ))
        conn.commit()


def get_repo_files(repo_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM repo_files WHERE repo_id = ? ORDER BY relative_path ASC", (repo_id,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def get_or_create_default_conversation(repo_id: str) -> Dict[str, Any]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM conversations WHERE repo_id = ? ORDER BY created_at ASC LIMIT 1", (repo_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        conv_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        cursor.execute("""
            INSERT INTO conversations (id, repo_id, title, created_at)
            VALUES (?, ?, ?, ?)
        """, (conv_id, repo_id, "Codebase Q&A", now))
        conn.commit()
        return {"id": conv_id, "repo_id": repo_id, "title": "Codebase Q&A", "created_at": now}


def add_message(
    conversation_id: str,
    role: str,
    content: str,
    citations: Optional[List[Dict[str, Any]]] = None,
    model_used: str = ""
) -> Dict[str, Any]:
    msg_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    cit_json = json.dumps(citations or [])
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO messages (id, conversation_id, role, content, citations, model_used, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (msg_id, conversation_id, role, content, cit_json, model_used, now))
        conn.commit()
    return {
        "id": msg_id,
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
        "citations": citations or [],
        "model_used": model_used,
        "created_at": now,
    }


def get_messages(conversation_id: str) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC", (conversation_id,))
        rows = cursor.fetchall()
        messages = []
        for r in rows:
            d = dict(r)
            d["citations"] = json.loads(d.get("citations") or "[]")
            messages.append(d)
        return messages
