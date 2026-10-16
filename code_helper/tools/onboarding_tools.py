"""
code_helper/tools/onboarding_tools.py - Project Onboarding & Execution Guidance Tools
Provides architecture overviews and step-by-step developer setup commands.
"""

def get_project_overview() -> str:
    """
    Returns a comprehensive architecture overview of the codebase and the responsibilities of the 5 core files.
    """
    return """=== PROJECT OVERVIEW: NAIVE RAG ARCHITECTURE ===
This project is an end-to-end, educational Naive RAG (Retrieval-Augmented Generation) pipeline.
It demonstrates how private documents are ingested, embedded, stored in a vector database, and retrieved to answer queries without hallucinations.

Core 5 Files and their Responsibilities:
1. `config.py`:
   - System settings, environment variables, Pinecone connection credentials, and model names.
   - Provides mock fallback toggles (`force_mock_ai=True`).

2. `indexer.py`:
   - Offline indexing pipeline (Stages 1 to 4).
   - Ingests raw text (`astratech_employee_handbook.txt`), slices text into overlapping chunks (sliding window), computes vector embeddings, and stores them in the vector database.

3. `vector_store.py`:
   - Pinecone serverless database connector + local in-memory cosine similarity fallback.
   - Handles vector upsertion and top-k approximate nearest neighbor search.

4. `query_pipeline.py`:
   - Online query pipeline (Stages 5 to 8).
   - Embeds user questions, queries vector DB for top-k chunks, injects context into prompts, and generates grounded answers.

5. `main.py`:
   - Interactive live CLI demo orchestrator with side-by-side scorecard comparing baseline LLM vs. Naive RAG.
"""


def get_execution_guide() -> str:
    """
    Returns exact terminal commands to set up the environment, run indexing, and execute queries.
    """
    return """=== DEVELOPER QUICKSTART GUIDE ===
Follow these exact steps to run and test the project:

1. Setup Python Virtual Environment:
   cd Naive_RAG
   python -m venv .venv
   .\\.venv\\Scripts\\python.exe -m pip install --upgrade pip
   .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt

2. Run the Full Live Demo Walkthrough (Indexing + Baseline Comparison + RAG Query):
   .\\.venv\\Scripts\\python.exe main.py

3. Re-run Only the Offline Indexing Pipeline:
   .\\.venv\\Scripts\\python.exe main.py --index

4. Ask a Custom Question via RAG:
   .\\.venv\\Scripts\\python.exe main.py --query "What is the Wi-Fi password for office visitors?"

5. Run Side-by-Side Comparison (Raw LLM vs. RAG):
   .\\.venv\\Scripts\\python.exe main.py --compare

6. Offline Simulation Mode (No external API calls):
   .\\.venv\\Scripts\\python.exe main.py --mock
"""
