"""
backend/config.py - Repomind System Configuration & Environment Settings
"""

import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load .env from backend directory or project root
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(PROJECT_ROOT / ".env")

class Settings(BaseModel):
    # Base Storage Paths
    data_dir: Path = Field(default_factory=lambda: PROJECT_ROOT / "data_store")
    chroma_dir: Path = Field(default_factory=lambda: PROJECT_ROOT / "data_store" / "chroma")
    repos_cache_dir: Path = Field(default_factory=lambda: PROJECT_ROOT / "data_store" / "repos")
    sqlite_db_path: Path = Field(default_factory=lambda: PROJECT_ROOT / "data_store" / "repomind.db")

    # API Keys
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    groq_api_key: str = Field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    github_token: str = Field(default_factory=lambda: os.getenv("GITHUB_TOKEN", ""))
    stitch_api_key: str = Field(default_factory=lambda: os.getenv("STITCH_API_KEY", ""))
    stitch_project_id: str = Field(default_factory=lambda: os.getenv("STITCH_PROJECT_ID", ""))
    ollama_base_url: str = Field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))

    # Default LLM Generation Settings
    active_provider: str = Field(default_factory=lambda: os.getenv("DEFAULT_PROVIDER", "gemini"))
    active_model: str = Field(default_factory=lambda: os.getenv("DEFAULT_MODEL", "gemini-3.8-flash"))
    temperature: float = 0.2
    max_tokens: int = 2048

    # RAG Retrieval Settings
    top_k: int = 6
    dense_weight: float = 0.6
    bm25_weight: float = 0.4
    symbol_match_boost: float = 1.3
    max_context_chars: int = 14000

    # Chunking Configuration
    max_chunk_lines: int = 80
    min_chunk_lines: int = 5
    line_overlap: int = 10

    def ensure_directories(self) -> None:
        """Create necessary storage directories if they do not exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.repos_cache_dir.mkdir(parents=True, exist_ok=True)


_settings_instance = None

def get_settings() -> Settings:
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
        _settings_instance.ensure_directories()
    return _settings_instance
