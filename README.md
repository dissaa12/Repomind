# Repomind — AI Repository Intelligence & Codebase RAG

> An AI-powered codebase intelligence system that indexes, maps, and answers architectural & implementation questions across any repository with syntax-aware chunking, hybrid retrieval, and interactive code citations.

---

## 🌟 Key Features

1. **3-Panel IDE Web Dashboard**:
   - **Left Panel (File Explorer)**: Interactive hierarchical file tree with language tags, line counts, and real-time search filtering.
   - **Center Panel (Conversational RAG Chat)**: Real-time token streaming via Server-Sent Events (SSE), suggested architectural prompt chips, and interactive citation badges.
   - **Right Panel (Code Inspector)**: In-depth code viewer with line numbers, copy actions, and **auto-scrolling citation highlights** when clicking reference badges in chat.

2. **Syntax & Scope-Aware AST Chunking**:
   - Parses code by functions, classes, methods, and semantic sections (AST for Python, regex parsers for JS/TS, headers for Markdown).
   - Preserves exact line numbers, symbol names, and file paths.

3. **Hybrid Retrieval (ChromaDB + BM25)**:
   - **Dense Vectors**: 384-dimensional dense semantic vectors persisted in local ChromaDB collections.
   - **Sparse Lexical Search**: BM25 index with camelCase and snake_case tokenization for exact variable, function, and identifier matching.
   - **Symbol Match Boosting**: Dynamically elevates chunks when user queries mention specific code symbols.

4. **Multi-Provider LLM Engine**:
   - Supports **Google Gemini** (`gemini-2.5-flash`), **OpenAI** (`gpt-4o-mini`), **Groq** (`llama-3.3-70b`), and **Local Ollama** (`llama3.2`).
   - Includes an **offline grounded Mock AI mode** that works immediately without requiring any API keys.

5. **Multi-Source Ingestion**:
   - **Local Directories**: Point Repomind to any directory on disk for instant local indexing.
   - **GitHub Repositories**: Shallow clones and indexes any public or private GitHub repository via URL.

---

## 🚀 Quick Start

### 1. Launch with Single Click
- **Windows Batch**: Double-click [`run_repomind.bat`](file:///c:/Users/patil/OneDrive/Desktop/Repomind/run_repomind.bat)
- **PowerShell**: Run [`run_repomind.ps1`](file:///c:/Users/patil/OneDrive/Desktop/Repomind/run_repomind.ps1)

### 2. Manual Startup

**Terminal 1 — Backend (FastAPI)**:
```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — Frontend (Vite + React)**:
```powershell
cd frontend
npm run dev
```

Open your browser to: **`http://localhost:5173/`**

---

## 🛠️ Architecture Map

```
Repomind/
├── backend/
│   ├── config.py                 # Paths, API keys, & retrieval parameters
│   ├── pipeline.py               # Central ingestion & indexing orchestrator
│   ├── main.py                   # FastAPI REST & SSE streaming endpoints
│   ├── db/database.py            # SQLite persistence for repos, files, & chat history
│   ├── ingestion/
│   │   ├── file_crawler.py       # Smart traversal with .gitignore & noise filtering
│   │   └── git_cloner.py         # Shallow Git cloner for remote repositories
│   ├── parser/
│   │   └── code_chunker.py       # AST & scope-aware multi-language chunker
│   ├── retrieval/
│   │   ├── vector_store.py       # ChromaDB persistent dense vector store
│   │   ├── bm25_index.py         # BM25 sparse keyword & symbol search index
│   │   └── hybrid_retriever.py   # Hybrid fusion with symbol matching boost
│   └── llm/
│       └── providers.py          # Unified Gemini/OpenAI/Groq/Ollama/Mock adapter
├── frontend/
│   ├── src/
│   │   ├── index.css             # Vanilla CSS design system (IDE dark theme)
│   │   ├── App.jsx               # Main state orchestrator
│   │   └── components/
│   │       ├── Header.jsx        # Repo switcher, active model pill, & modals
│   │       ├── FileExplorer.jsx  # Hierarchical tree with search filter
│   │       ├── ChatPanel.jsx     # Streaming chat with citation badges
│   │       ├── CodeInspector.jsx # Line-by-line syntax viewer with auto-scroll
│   │       ├── IngestModal.jsx   # Ingestion dialog (Local / GitHub)
│   │       └── SettingsModal.jsx # API key & LLM provider settings
└── data_store/                   # SQLite database & ChromaDB vector storage
```
