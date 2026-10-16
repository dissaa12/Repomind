"""
code_helper/cli.py - Interactive Terminal CLI for Multi-Agent Code Helper
Allows developers to query the 5-agent team directly in the terminal without opening a browser.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows terminal
os.environ["PYTHONUTF8"] = "1"
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Load environment
root_dir = Path(__file__).resolve().parent.parent
load_dotenv(root_dir / ".env")

try:
    from code_helper.tools import rag_tools, ast_tools, onboarding_tools, code_tools
except ImportError:
    from tools import rag_tools, ast_tools, onboarding_tools, code_tools


def print_banner():
    print("=" * 72)
    print("  REPOMIND: MULTI-AGENT CODE HELPER (INTERACTIVE TERMINAL CLI)")
    print("  Powered by 1 Boss (Coordinator) + 4 Workers + Pinecone + AST")
    print("=" * 72)
    print("Available Commands:")
    print("  1. Type your question directly (e.g. 'Where is cosine similarity?')")
    print("  2. 'search <query>'       -> Force Code Searcher (RAG)")
    print("  3. 'imports <module>'     -> Force Architecture Mapper (AST Imports)")
    print("  4. 'symbols <file>'       -> Force Architecture Mapper (AST Classes/Functions)")
    print("  5. 'explain <file>'       -> Force Code Explainer (File summary)")
    print("  6. 'onboarding'           -> Force Onboarding Guide (Project map & setup)")
    print("  7. 'exit' or 'quit'       -> Quit CLI")
    print("-" * 72)


def dispatch_query(query: str):
    q = query.strip()
    if not q:
        return

    lower = q.lower()

    if lower in ("exit", "quit", "q"):
        print("\nExiting CLI. Happy coding!")
        sys.exit(0)

    # Manual shortcuts
    if lower == "onboarding" or "where do i start" in lower or "what does this project do" in lower:
        print("\n[ROUTED TO]: onboarding_guide (Worker 4)")
        print("-" * 60)
        print(onboarding_tools.get_project_overview())
        print("\n" + onboarding_tools.get_execution_guide())
        print("-" * 60)
        return

    if lower.startswith("imports "):
        mod = q.split(" ", 1)[1].strip().replace(".py", "")
        print(f"\n[ROUTED TO]: architecture_mapper (Worker 3) -> analyze_imports('{mod}')")
        print("-" * 60)
        print(ast_tools.analyze_imports(mod))
        print("-" * 60)
        return

    if lower.startswith("symbols "):
        fname = q.split(" ", 1)[1].strip()
        print(f"\n[ROUTED TO]: architecture_mapper (Worker 3) -> list_functions_and_classes('{fname}')")
        print("-" * 60)
        print(ast_tools.list_functions_and_classes(fname))
        print("-" * 60)
        return

    if lower.startswith("explain "):
        fname = q.split(" ", 1)[1].strip()
        print(f"\n[ROUTED TO]: code_explainer (Worker 2) -> get_file_summary('{fname}')")
        print("-" * 60)
        print(code_tools.get_file_summary(fname))
        print("-" * 60)
        return

    # Intelligent intent routing
    if any(k in lower for k in ["import", "which files import", "dependencies"]):
        target_mod = "config"
        for word in q.replace("?", "").replace(",", "").split():
            if word.endswith(".py") or word in ["config", "indexer", "vector_store", "query_pipeline", "main"]:
                target_mod = word.replace(".py", "")
                break
        print(f"\n[COORDINATOR DISPATCH]: Routing to architecture_mapper -> analyze_imports('{target_mod}')")
        print("-" * 60)
        print(ast_tools.analyze_imports(target_mod))
        print("-" * 60)
    elif any(k in lower for k in ["where", "find", "search", "locate", "how is", "similarity"]):
        search_term = q
        for prefix in ["where is", "where are", "find", "search for"]:
            if lower.startswith(prefix):
                search_term = q[len(prefix):].strip()
                break
        print(f"\n[COORDINATOR DISPATCH]: Routing to code_searcher -> rag_search('{search_term}')")
        print("-" * 60)
        results = rag_tools.rag_search(search_term)
        print(results)
        print("-" * 60)
    else:
        print(f"\n[COORDINATOR DISPATCH]: Searching codebase via code_searcher...")
        print("-" * 60)
        print(rag_tools.rag_search(q))
        print("-" * 60)


def main():
    print_banner()
    while True:
        try:
            query = input("\n[Repomind Developer] >> ")
            dispatch_query(query)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting CLI.")
            break


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run single query passed via command line arguments
        single_query = " ".join(sys.argv[1:])
        dispatch_query(single_query)
    else:
        main()
