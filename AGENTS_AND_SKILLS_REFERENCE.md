# Master Architecture Reference: Multi-Agent Code Helper & Skills Directory

> Complete reference manual for the **Multi-Agent Code Helper** (Google ADK & MCP), its tool registry, Model Context Protocol servers, and installed Antigravity engineering skills.

---

## 1. Multi-Agent Team Architecture

Built with **Google ADK** (`google-adk`) and orchestrated by a central coordinator routing questions across 4 specialized workers:

```
                          ┌───────────────────────────┐
                          │    Coordinator (Boss)     │
                          │   "Never answers itself"  │
                          └─────────────┬─────────────┘
                                        │
         ┌──────────────────┬───────────┴───────────┬──────────────────┐
         ▼                  ▼                       ▼                  ▼
┌─────────────────┐ ┌─────────────────┐   ┌─────────────────┐ ┌─────────────────┐
│  Code Searcher  │ │  Code Explainer │   │ Architecture    │ │   Onboarding    │
│                 │ │                 │   │     Mapper      │ │      Guide      │
│ "Where is it?"  │ │ "What does this │   │ "How are files  │ │"Where do I start│
│                 │ │    file do?"    │   │   connected?"   │ │  & how to run?" │
└────────┬────────┘ └────────┬────────┘   └────────┬────────┘ └────────┬────────┘
         │                   │                     │                   │
         ▼                   ▼                     ▼                   ▼
   [rag_search]      [Filesystem MCP]      [AST Import Graph]    [Project Overview]
                     [file_summary]        [Class & Func AST]    [Execution Guide]
                     [read_lines]          [Symbol Reference]
```

### Agents Specification Table

| Agent Name | Role / Description | Instruction / Rule | Tools Bound | Example Question |
| :--- | :--- | :--- | :--- | :--- |
| **`coordinator`** | **The Boss / Router**: Evaluates incoming queries and picks the best worker. Never answers itself. | *"Never answer yourself. Pick the best worker for the incoming question."* | Sub-agents: `searcher`, `explainer`, `mapper`, `guide` | *"Any incoming question"* |
| **`code_searcher`** | **Search Specialist**: Finds where code and algorithms reside across files. | *"Use your search tool. Answer only from what it returns. Say 'I could not find that' if nothing matches."* | `rag_search` | *"Where is the vector embedding done?"* |
| **`code_explainer`** | **Code Deep-Dive**: Reads entire source files or line blocks and explains logic. | *"Use your file inspection tools to read and examine source code files. Explain classes, functions, and algorithms."* | Filesystem MCP (`list_directory`, `read_file`), `get_file_summary`, `read_specific_lines` | *"Explain vector_store.py"* |
| **`architecture_mapper`**| **Structural Cartographer**: Maps import dependencies and symbol call hierarchies with plain Python. | *"Use your plain Python AST tools to examine import statements, list classes and functions with zero guesswork."* | `analyze_imports`, `list_functions_and_classes`, `find_symbol_references` *(Plain Python AST, No AI)* | *"Which files import config.py?"* |
| **`onboarding_guide`** | **New Developer Mentor**: Explains project purpose, 8-stage RAG map, and run commands. | *"Use your onboarding tools to guide developers on what the project does and the exact commands to run."* | `get_project_overview`, `get_execution_guide` | *"I am new. Where do I start?"* |

---

## 2. Tools Registry (7 Custom Tools + MCP Server)

| Tool Name | Module | Type | Description |
| :--- | :--- | :--- | :--- |
| **`rag_search`** | `rag_tools.py` | Vector RAG | Queries vector embeddings (Pinecone serverless or local ChromaDB) for top matching code snippets. |
| **`analyze_imports`** | `ast_tools.py` | **Plain Python (No AI)** | Parses abstract syntax trees (`ast.parse`) across all `.py` files to extract import hierarchies and reverse dependencies. |
| **`list_functions_and_classes`** | `ast_tools.py` | **Plain Python (No AI)** | Extracts function signatures, class definitions, line spans, and docstrings from a file. |
| **`find_symbol_references`** | `ast_tools.py` | **Plain Python (No AI)** | Scans all project files to locate where a specific function, class, or variable is called or referenced. |
| **`get_file_summary`** | `code_tools.py` | Structural | Returns total lines, dependency counts, and primary symbol summaries for a file. |
| **`read_specific_lines`** | `code_tools.py` | File Inspection | Extracts and numbers an exact line range (`start_line` to `end_line`) from a file. |
| **`get_project_overview`** | `onboarding_tools.py` | Static Knowledge | Summarizes the purpose of the 5 core files in `Naive_RAG`. |
| **`get_execution_guide`** | `onboarding_tools.py` | Static Knowledge | Provides exact terminal commands to configure `.venv`, run indexing, and execute `--compare`. |

---

## 3. Model Context Protocol (MCP) Server Integration

The **Code Explainer** agent connects to the standard **Filesystem MCP Server** (`@modelcontextprotocol/server-filesystem`) using Google ADK's `McpToolset`:

```python
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

file_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", target_codebase_dir],
        ),
        timeout=30,
    ),
    tool_filter=["list_directory", "read_file"],
)
```

### Why Filesystem MCP?
1. **Security & Sandboxing**: Restricts file reading strictly to the target project directory. Attempts to traverse outside the target folder are blocked at the protocol level.
2. **Tool Standard**: Exposes `list_directory` and `read_file` directly to the agent without writing custom file-access boilerplate.
3. **Multi-Client Interoperability**: Compatible with any MCP client (Claude Desktop, Antigravity IDE, Cursor, Google ADK).

---

### 3.2 Google Stitch MCP Server (`stitch-mcp`)

The **Stitch MCP Server** integrates **Google Stitch** (Google's AI-native UI design & canvas tool at [stitch.withgoogle.com](https://stitch.withgoogle.com)) directly into the Repomind development environment:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "C:\\Users\\patil\\OneDrive\\Desktop\\Repomind"]
    },
    "stitch": {
      "command": "npx",
      "args": ["-y", "stitch-mcp"],
      "env": {
        "STITCH_API_KEY": "${STITCH_API_KEY}"
      }
    }
  }
}
```

#### How the Frontend Connects with Stitch:
- **Design Tokens**: Maps Stitch visual design tokens (colors, typography, spacing) into our custom `index.css` system.
- **Screen Sync**: The React dashboard includes a dedicated **Stitch Studio** button in the header that opens the Stitch Design Sync modal, connecting project canvases to the active 3-panel IDE layout.
- **API Endpoints**: `/api/stitch/status` and `/api/stitch/sync` allow dynamic screen synchronization from Stitch project IDs.

---

## 4. Installed Antigravity Skills Directory

This workspace has access to the following specialized engineering and workflow skills:

| Skill | Path / Location | Purpose & Capabilities |
| :--- | :--- | :--- |
| **`credentials`** | [SKILL.md](file:///C:/Users/patil/.gemini/config/plugins/science/skills/credentials/SKILL.md) | Safely handles API keys and secrets (`GEMINI_API_KEY`, `NVIDIA_API_KEY`, `PINECONE_API_KEY`, `GITHUB_TOKEN`) in `.env` without exposing them in logs, terminals, or chat transcripts. |
| **`uv`** | [SKILL.md](file:///C:/Users/patil/.gemini/config/plugins/science/skills/uv/SKILL.md) | High-speed Python virtual environment and dependency manager. Used to install packages (FastAPI, ChromaDB, LiteLLM, ADK) up to 10-100x faster than traditional pip. |
| **`workflow-skill-creator`** | [SKILL.md](file:///C:/Users/patil/.gemini/config/plugins/science/skills/workflow_skill_creator/SKILL.md) | Packages completed agent workflows, AST tools, and indexing routines into permanent reusable Antigravity skills. |
| **`agy-customizations`** | [SKILL.md](file:///C:/Users/patil/.gemini/antigravity-ide/builtin/skills/agy-customizations/SKILL.md) | Guides the configuration of workspace rules, subagents, and custom MCP tool definitions for Antigravity IDE. |

---

## 5. Chunking Strategy & Technical Rationale

In `code_helper/index_codebase.py`, code is sliced using a **sliding window strategy**:
- **Chunk Size**: `50 lines` (~150 to 250 tokens)
- **Overlap**: `10 lines` (~30 to 50 tokens)

### Why 50 Lines with 10-Line Overlap?
1. **Preserving Function & Class Signatures**: In typical Python files, standard helper functions range between 15 to 45 lines. A 50-line window ensures most functions fit entirely within a single chunk.
2. **Preventing Boundary Splitting**: The 10-line overlap ensures that if a function header or docstring starts near the end of chunk $N$, it also appears at the beginning of chunk $N+1$, preventing cutoffs where the function name is separated from its body.
3. **Embedding Vector Density**: At 50 lines, vectors generated by embedding models (`nvidia/nemotron-3-embed-1b` or dense local models) retain high semantic specificity. In contrast, 200+ line chunks dilute cosine similarity across too many unrelated methods.

---

## 6. How to Run

### Command-Line Interface (ADK CLI)
```powershell
# 1. Run codebase indexing (indexes Naive_RAG into ChromaDB & Pinecone)
.\backend\.venv\Scripts\python.exe code_helper/index_codebase.py

# 2. Interactive Terminal Chat via Google ADK
.\backend\.venv\Scripts\python.exe -m google.adk.cli run code_helper

# 3. Interactive Web Interface via Google ADK Web
.\backend\.venv\Scripts\python.exe -m google.adk.cli web
```

### Repomind Full-Stack IDE Dashboard
```powershell
# Launch the complete 3-panel React + FastAPI dashboard
.\run_repomind.ps1
```
Open your browser to: **`http://localhost:5173/`**
