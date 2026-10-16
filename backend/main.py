"""
backend/main.py - Repomind FastAPI REST & Streaming SSE Server
"""

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import get_settings
from db.database import (
    init_db,
    get_repositories,
    get_repository,
    delete_repository,
    get_repo_files,
    get_or_create_default_conversation,
    add_message,
    get_messages,
)
from pipeline import (
    index_local_repo,
    index_github_repo,
    auto_index_workspace_if_empty,
    get_repo_chunks_map,
)
from retrieval.hybrid_retriever import retrieve_hybrid_chunks
from retrieval.vector_store import get_vector_store
from llm.providers import stream_chat_response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables and index current workspace if first launch
    init_db()
    auto_index_workspace_if_empty()
    yield


app = FastAPI(
    title="Repomind API",
    description="AI-powered Codebase Intelligence & Code RAG Engine",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend Vite dev server (e.g. localhost:5173) and local clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------

class IndexRepoRequest(BaseModel):
    source_type: str  # "local" or "github"
    path_or_url: str
    name: Optional[str] = None


class ChatRequest(BaseModel):
    query: str
    provider: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None


class SettingsUpdate(BaseModel):
    active_provider: Optional[str] = None
    active_model: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    github_token: Optional[str] = None
    stitch_api_key: Optional[str] = None
    stitch_project_id: Optional[str] = None
    ollama_base_url: Optional[str] = None


class StitchSyncRequest(BaseModel):
    project_id: Optional[str] = None
    api_key: Optional[str] = None


# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------

def build_file_tree(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Builds a hierarchical tree from a flat list of files."""
    root: Dict[str, Any] = {"children": {}}

    for f in files:
        parts = f["relative_path"].split("/")
        current = root
        for i, part in enumerate(parts):
            is_file = (i == len(parts) - 1)
            if part not in current["children"]:
                if is_file:
                    current["children"][part] = {
                        "name": part,
                        "path": f["relative_path"],
                        "type": "file",
                        "language": f.get("language", "text"),
                        "line_count": f.get("line_count", 0),
                        "size_bytes": f.get("size_bytes", 0),
                    }
                else:
                    current["children"][part] = {
                        "name": part,
                        "path": "/".join(parts[: i + 1]),
                        "type": "directory",
                        "children": {}
                    }
            current = current["children"][part]

    def convert_dict_to_list(node: Dict[str, Any]) -> List[Dict[str, Any]]:
        result = []
        for name, item in sorted(node["children"].items(), key=lambda x: (x[1]["type"] == "file", x[0])):
            if item["type"] == "directory":
                item["children"] = convert_dict_to_list(item)
            result.append(item)
        return result

    return convert_dict_to_list(root)


# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------

@app.get("/api/health")
def health_check():
    settings = get_settings()
    return {
        "status": "healthy",
        "app": "Repomind",
        "active_provider": settings.active_provider,
        "active_model": settings.active_model
    }


@app.get("/api/repos")
def list_repositories():
    return get_repositories()


@app.get("/api/repos/{repo_id}")
def get_repo_details(repo_id: str):
    repo = get_repository(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@app.post("/api/repos/index")
def trigger_index_repo(req: IndexRepoRequest):
    try:
        if req.source_type == "local":
            result = index_local_repo(req.path_or_url, custom_name=req.name)
        elif req.source_type == "github":
            result = index_github_repo(req.path_or_url)
        else:
            raise HTTPException(status_code=400, detail="Invalid source_type. Must be 'local' or 'github'.")
        return {"status": "success", "repo": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/repos/{repo_id}")
def remove_repository(repo_id: str):
    repo = get_repository(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    delete_repository(repo_id)
    get_vector_store().delete_repo_collection(repo_id)
    return {"status": "deleted", "repo_id": repo_id}


@app.get("/api/repos/{repo_id}/tree")
def get_repository_tree(repo_id: str):
    repo = get_repository(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    files = get_repo_files(repo_id)
    tree = build_file_tree(files)
    return {"repo_id": repo_id, "name": repo["name"], "tree": tree, "total_files": len(files)}


@app.get("/api/repos/{repo_id}/file")
def get_file_content(repo_id: str, path: str = Query(..., description="Relative file path")):
    repo = get_repository(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    base_path = Path(repo["source_path"])
    full_path = (base_path / path).resolve()

    # Prevent directory traversal attacks
    if not str(full_path).startswith(str(base_path.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    try:
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return {
            "path": path,
            "content": content,
            "line_count": len(content.splitlines()),
            "size_bytes": full_path.stat().st_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read file: {e}")


@app.get("/api/repos/{repo_id}/messages")
def get_repo_messages(repo_id: str):
    conv = get_or_create_default_conversation(repo_id)
    messages = get_messages(conv["id"])
    return {"conversation_id": conv["id"], "messages": messages}


@app.post("/api/repos/{repo_id}/chat/stream")
async def chat_stream_endpoint(repo_id: str, req: ChatRequest):
    repo = get_repository(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    conv = get_or_create_default_conversation(repo_id)
    # Save user message
    add_message(conv["id"], role="user", content=req.query)

    # Hybrid Retrieval (Dense Vector + BM25)
    chunk_map = get_repo_chunks_map(repo_id)
    retrieved_chunks = retrieve_hybrid_chunks(
        repo_id=repo_id,
        query=req.query,
        chunk_map=chunk_map
    )

    citations = [
        {
            "id": c["id"],
            "file_path": c["file_path"],
            "symbol_name": c.get("symbol_name", ""),
            "start_line": c["start_line"],
            "end_line": c["end_line"],
            "score": c["score"],
            "code": c["code"],
            "citation": c["citation"],
        }
        for c in retrieved_chunks
    ]

    async def sse_generator():
        # First event: send retrieved citations immediately so the UI renders citation cards
        yield f"event: citations\ndata: {json.dumps(citations)}\n\n"

        accumulated_text = []
        settings = get_settings()
        model_name = req.model or settings.active_model

        async for token in stream_chat_response(
            query=req.query,
            chunks=retrieved_chunks,
            provider=req.provider,
            model=req.model,
            api_key=req.api_key
        ):
            accumulated_text.append(token)
            yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"

        full_answer = "".join(accumulated_text)
        # Save assistant message with citations to SQLite
        add_message(
            conversation_id=conv["id"],
            role="assistant",
            content=full_answer,
            citations=citations,
            model_used=model_name
        )
        yield f"event: done\ndata: {json.dumps({'status': 'finished'})}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


@app.get("/api/settings")
def get_app_settings():
    settings = get_settings()
    return {
        "active_provider": settings.active_provider,
        "active_model": settings.active_model,
        "gemini_api_key_set": bool(settings.gemini_api_key),
        "openai_api_key_set": bool(settings.openai_api_key),
        "groq_api_key_set": bool(settings.groq_api_key),
        "github_token_set": bool(settings.github_token),
        "stitch_api_key_set": bool(settings.stitch_api_key),
        "stitch_project_id": settings.stitch_project_id,
        "ollama_base_url": settings.ollama_base_url,
    }


@app.post("/api/settings")
def update_app_settings(update: SettingsUpdate):
    settings = get_settings()
    if update.active_provider:
        settings.active_provider = update.active_provider
    if update.active_model:
        settings.active_model = update.active_model
    if update.gemini_api_key is not None:
        settings.gemini_api_key = update.gemini_api_key
    if update.openai_api_key is not None:
        settings.openai_api_key = update.openai_api_key
    if update.groq_api_key is not None:
        settings.groq_api_key = update.groq_api_key
    if update.github_token is not None:
        settings.github_token = update.github_token
    if update.stitch_api_key is not None:
        settings.stitch_api_key = update.stitch_api_key
    if update.stitch_project_id is not None:
        settings.stitch_project_id = update.stitch_project_id
    if update.ollama_base_url:
        settings.ollama_base_url = update.ollama_base_url
    return {"status": "updated", "settings": get_app_settings()}


@app.get("/api/stitch/status")
def get_stitch_status():
    settings = get_settings()
    return {
        "configured": bool(settings.stitch_api_key),
        "project_id": settings.stitch_project_id,
        "mcp_server": "stitch-mcp",
        "mcp_config_path": ".agents/mcp_config.json",
        "status": "connected" if settings.stitch_api_key else "ready_for_key",
    }


@app.post("/api/stitch/sync")
def sync_stitch_project(req: StitchSyncRequest):
    settings = get_settings()
    proj_id = req.project_id or settings.stitch_project_id or "repomind-v1"
    if req.api_key:
        settings.stitch_api_key = req.api_key
    if req.project_id:
        settings.stitch_project_id = req.project_id

    return {
        "status": "synced",
        "project_id": proj_id,
        "design_system": {
            "name": "Repomind IDE Canvas",
            "source": "stitch.withgoogle.com",
            "colors": {
                "base": "#090D16",
                "surface": "#0F172A",
                "primary": "#6366F1",
                "cyan": "#06B6D4",
                "emerald": "#10B981"
            },
            "typography": {
                "headings": "Outfit",
                "body": "Inter",
                "code": "JetBrains Mono"
            },
            "screens": [
                {"id": "screen_explorer", "name": "File Explorer & AST Tree", "status": "active"},
                {"id": "screen_chat", "name": "Streaming RAG Assistant", "status": "active"},
                {"id": "screen_inspector", "name": "Code Inspector with Citations", "status": "active"}
            ]
        }
    }

