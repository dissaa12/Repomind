"""
backend/ingestion/file_crawler.py - Repository File Crawler with Smart Filtering
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Set

IGNORED_DIRS: Set[str] = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    "env",
    ".env",
    ".next",
    ".nuxt",
    ".idea",
    ".vscode",
    ".cache",
    "data_store",
    "coverage",
    ".turbo",
    ".gemini",
}

IGNORED_EXTENSIONS: Set[str] = {
    # Binaries & Archives
    ".exe", ".dll", ".so", ".dylib", ".bin", ".zip", ".tar", ".gz", ".7z", ".rar",
    # Media
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp", ".mp4", ".mp3", ".wav", ".pdf",
    # Fonts
    ".ttf", ".woff", ".woff2", ".eot",
    # Compiles / caches / locks
    ".pyc", ".pyo", ".pyd", ".class", ".o", ".obj", ".wasm", ".lock", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
}

EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".cs": "csharp",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".json": "json",
    ".md": "markdown",
    ".markdown": "markdown",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".sql": "sql",
    ".sh": "shell",
    ".bash": "shell",
    ".ps1": "powershell",
    ".txt": "text",
    ".toml": "toml",
}

MAX_FILE_SIZE_BYTES = 500 * 1024  # 500 KB cap per file to avoid massive bundles


def detect_language(file_path: Path) -> str:
    ext = file_path.suffix.lower()
    return EXTENSION_TO_LANGUAGE.get(ext, "text")


def is_binary_file(file_path: Path) -> bool:
    """Check if the first 1KB contains null bytes indicating a binary file."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            return b"\x00" in chunk
    except Exception:
        return True


def crawl_repository(root_path: Path) -> List[Dict[str, Any]]:
    """
    Crawls a local directory and returns indexed file metadata.
    """
    root = root_path.resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Path does not exist or is not a directory: {root}")

    indexed_files: List[Dict[str, Any]] = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune ignored directories in-place so os.walk doesn't descend into them
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]

        for filename in filenames:
            file_path = Path(dirpath) / filename
            ext = file_path.suffix.lower()

            # Skip ignored extensions
            if ext in IGNORED_EXTENSIONS or filename in IGNORED_EXTENSIONS:
                continue

            # Skip hidden files
            if filename.startswith(".") and not filename.startswith(".env.example"):
                continue

            try:
                stat = file_path.stat()
                if stat.st_size > MAX_FILE_SIZE_BYTES:
                    continue

                if is_binary_file(file_path):
                    continue

                # Count lines and read text safely
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()

                lines = content.splitlines()
                rel_path = str(file_path.relative_to(root)).replace("\\", "/")

                indexed_files.append({
                    "relative_path": rel_path,
                    "absolute_path": str(file_path),
                    "language": detect_language(file_path),
                    "line_count": len(lines),
                    "size_bytes": stat.st_size,
                    "content": content,
                })
            except Exception as e:
                # Silently skip files that cannot be read
                continue

    return indexed_files
