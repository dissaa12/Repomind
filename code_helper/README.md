# Multi-Agent Code Helper

### Student Submission & Project Guide
**Student Guide Reference**: `Multi-Agent Code Helper (deboistech, 2026-10-12)`

---

## 1. What This Helper Does

The **Multi-Agent Code Helper** is an autonomous developer assistance system powered by Google ADK that answers questions about a code project (`Naive_RAG`). It features a team of 5 AI agents—1 coordinator boss and 4 specialized workers—that find where code is located, explain whole files, map module connections using AST parsing without AI guessing, and guide new developers on how to run the project.

---

## 2. Table of Agents

| Agent Name | Role / What it does | Instruction / Routing Trigger | Tools Assigned |
| :--- | :--- | :--- | :--- |
| **`coordinator`** | The Boss. Evaluates user questions and routes each to the right worker. Never answers itself. | *"Never answer yourself. Pick the best worker for the incoming question."* | Sub-agents: `searcher`, `explainer`, `mapper`, `guide` |
| **`code_searcher`** | Finds where something is in the code. Uses vector RAG search. | *"Use your search tool. Answer only from what it returns. If it finds nothing useful, say 'I could not find that'."* | `rag_search` |
| **`code_explainer`** | Reads whole files and explains classes, methods, and logic. | *"Use your file inspection tools to read and examine source code files. Explain what the file does clearly."* | Filesystem MCP Server (`list_directory`, `read_file`), `get_file_summary`, `read_specific_lines` |
| **`architecture_mapper`** | Maps file connections, imports, and symbol references using plain Python AST. | *"Use your plain Python AST tools to examine import statements, list classes and functions with zero guesswork."* | `analyze_imports`, `list_functions_and_classes`, `find_symbol_references` *(Plain Python, No AI)* |
| **`onboarding_guide`** | Explains what the project does, the 8-stage pipeline, and exact setup commands. | *"Use your onboarding tools to guide developers on what the project does and the exact commands to run."* | `get_project_overview`, `get_execution_guide` |

---

## 3. Table of Tools

| Tool Name | Worker | Uses AI? | Description |
| :--- | :--- | :--- | :--- |
| **`rag_search`** | `code_searcher` | Yes (Vectors) | Embeds user queries and searches Pinecone / local ChromaDB for closest code passages. |
| **`analyze_imports`** | `architecture_mapper` | **No (Plain Python AST)** | Parses AST of all project files to return which files import a given module (e.g. `config.py`). |
| **`list_functions_and_classes`**| `architecture_mapper` | **No (Plain Python AST)** | Extracts function and class definitions, line spans, arguments, and docstrings from a file. |
| **`find_symbol_references`** | `architecture_mapper` | **No (Plain Python AST)** | Scans all `.py` files to find lines where a specific function or variable is referenced. |
| **`get_file_summary`** | `code_explainer` | No (Plain Python) | Returns line counts, dependency counts, and defined classes/functions before full file reading. |
| **`read_specific_lines`** | `code_explainer` | No (Plain Python) | Reads a numbered line range from a file (e.g., lines 55 to 111). |
| **`get_project_overview`** | `onboarding_guide` | No (Static Knowledge) | Summarizes the purpose and responsibilities of the 5 core project files. |
| **`get_execution_guide`** | `onboarding_guide` | No (Static Knowledge) | Provides step-by-step terminal commands to create virtualenvs, run indexing, and run `--compare`. |
| **Filesystem MCP** (`read_file`, `list_directory`) | `code_explainer` | No (MCP Server) | Connects via `@modelcontextprotocol/server-filesystem` to safely read project files. |

---

## 4. Chunk Size and Why

- **Chunk Size**: `50 lines` (~150–250 tokens)
- **Overlap**: `10 lines` (~30–50 tokens)

**Why this was chosen**:
1. **Preserves Semantic Scope**: Typical Python functions in this project are 20 to 45 lines long. Sizing chunks at 50 lines allows each function to be indexed within a single, cohesive chunk.
2. **Boundary Protection**: If a function header or docstring begins on line 45, a hard 50-line cut would sever the header from its implementation. The 10-line overlap guarantees the full signature and docstring are preserved in the subsequent chunk.
3. **Retrieval Precision**: 50 lines produces high cosine similarity for specific questions (*"Where is chunk_document?"*), whereas larger windows (>150 lines) dilute relevance across unrelated functions.

---

## 5. MCP Server Used and Why

- **MCP Server**: `@modelcontextprotocol/server-filesystem`
- **Connection**: `npx -y @modelcontextprotocol/server-filesystem <path_to_code>`

**Why this MCP server was chosen**:
1. **Standardized Protocol**: Implements the Model Context Protocol (MCP) standard, enabling any MCP-compliant agent to safely inspect project files.
2. **Directory Sandboxing**: Restricts the agent's filesystem access strictly to the target project directory, preventing accidental reading of parent directories or system files.
3. **Built-in Tool Exposure**: Automatically exposes clean, schema-validated tools (`read_file`, `list_directory`) directly to the `code_explainer` agent without custom I/O code.

---

## 6. Exact Commands to Run

```powershell
# 1. Run codebase indexing (indexes Naive_RAG into Pinecone with local ChromaDB fallback)
python code_helper/index_codebase.py

# 2. Interactive Terminal Chat via Google ADK
adk run code_helper

# 3. Interactive Web Interface via Google ADK Web
adk web

# 4. Or run the Verification Trace Test directly
python code_helper/test_agent_trace.py
```

---

## 7. 3 Sample Questions with Verified Answers

### Sample 1: "Where is the search done?"
- **Answered By**: **`code_searcher`** (Worker 1)
- **Tool Used**: `rag_search("search")`
- **Output / Answer**:
  > *Found relevant matches in `query_pipeline.py:48-96 (retrieve_top_k)` and `vector_store.py:120-165 (query_vector)`. Stage 6 retrieval embeds the user query and performs cosine similarity search against the vector database.*

### Sample 2: "Which files import config.py?"
- **Answered By**: **`architecture_mapper`** (Worker 3)
- **Tool Used**: `analyze_imports("config")`
- **Output / Answer**:
  > *The module 'config' is imported by:*
  > - `indexer.py`
  > - `main.py`
  > - `query_pipeline.py`
  > - `vector_store.py`

### Sample 3: "I am new. Where do I start?"
- **Answered By**: **`onboarding_guide`** (Worker 4)
- **Tool Used**: `get_project_overview()` and `get_execution_guide()`
- **Output / Answer**:
  > *Welcome! This project is an educational 8-stage Naive RAG pipeline studying `astratech_employee_handbook.txt` across 5 core files: `config.py` (settings), `indexer.py` (chunking & embeddings), `vector_store.py` (Pinecone storage), `query_pipeline.py` (retrieval & generation), and `main.py` (demo runner).*
  > *To start, run `python main.py` in your terminal to see the live demonstration comparing Raw LLM vs. Naive RAG.*

---

## 8. One Problem Hit and How It Was Fixed

- **Problem Hit**: On Windows PowerShell, running the offline indexing script initially threw a `UnicodeEncodeError: 'charmap' codec can't encode character '\u2713'` when printing status checkmarks (`✓`) because the default Windows console code page (cp1252) does not support unicode glyphs.
- **How It Was Fixed**:
  1. Replaced raw unicode glyphs with ASCII status tags (`[OK]`, `[!]`, `[*]`), guaranteeing cross-platform compatibility across Windows, Linux, and macOS without relying on terminal codepage overrides.
  2. Set `PYTHONUTF8=1` in the runner environment to ensure UTF-8 encoding across all file operations.

---

## Final Checklist Verification
- [x] 1 boss that only routes (`coordinator`)
- [x] 4 workers with clear descriptions (`code_searcher`, `code_explainer`, `architecture_mapper`, `onboarding_guide`)
- [x] Your own RAG, all 5 steps (`index_codebase.py` & `rag_tools.py`)
- [x] Chunking explained in the README (50 lines, 10 overlap)
- [x] Runs with `adk run code_helper` or `adk web`
- [x] Pinecone as vector database (with automatic local fallback)
- [x] 5 or more tools, at least 1 with no AI (7 tools total, 3 with no AI)
- [x] Filesystem MCP on the Code Explainer (`@modelcontextprotocol/server-filesystem`)
- [x] Keys in `.env`, not in code
- [x] 3 sample questions and 1 problem + fix documented
