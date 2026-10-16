"""
code_helper/tools/ast_tools.py - Plain Python AST Code Analysis Tools (No AI Guessing)
Inspects function definitions, classes, import dependencies, and callers using Python's ast module.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Set


def get_target_dir() -> Path:
    """Returns the path to the target codebase (Naive_RAG by default)."""
    env_dir = os.getenv("TARGET_PROJECT_DIR")
    if env_dir and Path(env_dir).exists():
        return Path(env_dir).resolve()
    # Default to Naive_RAG directory in workspace
    workspace = Path(__file__).resolve().parent.parent.parent
    naive_rag = workspace / "Naive_RAG"
    if naive_rag.exists():
        return naive_rag
    return workspace


def analyze_imports(module_name: str = "") -> str:
    """
    Lists which files import what modules across the codebase using plain Python AST.
    If module_name is provided, shows all files that import that specific module (e.g. 'config' or 'pinecone').
    """
    target = get_target_dir()
    py_files = sorted(list(target.glob("*.py")))
    if not py_files:
        return f"No Python files found in {target}."

    import_map: Dict[str, List[str]] = {}
    reverse_map: Dict[str, List[str]] = {}

    for file_path in py_files:
        rel_name = file_path.name
        import_map[rel_name] = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                tree = ast.parse(f.read(), filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        import_map[rel_name].append(alias.name)
                        reverse_map.setdefault(alias.name, []).append(rel_name)
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    import_map[rel_name].append(mod)
                    reverse_map.setdefault(mod, []).append(rel_name)
        except Exception as e:
            import_map[rel_name].append(f"<Error parsing: {e}>")

    if module_name:
        clean_mod = module_name.replace(".py", "").strip().lower()
        matching_files = set()
        for mod, files in reverse_map.items():
            if clean_mod in mod.lower():
                matching_files.update(files)

        if matching_files:
            return f"The module '{module_name}' is imported by:\n- " + "\n- ".join(sorted(matching_files))
        return f"No files import module '{module_name}'. Available imports across the project:\n" + "\n".join(
            f"- {k} -> {', '.join(v[:6])}" for k, v in sorted(import_map.items())
        )

    # General overview
    output = [f"Import Dependency Map for {target.name}:"]
    for file_name, imports in import_map.items():
        unique_imports = sorted(list(set(imports)))
        output.append(f"\n[{file_name}] imports:")
        for imp in unique_imports:
            output.append(f"  • {imp}")
    return "\n".join(output)


def list_functions_and_classes(file_name: str) -> str:
    """
    Lists all class definitions, methods, and functions in a Python file along with line numbers and docstrings.
    Use file_name such as 'vector_store.py' or 'indexer.py'.
    """
    target = get_target_dir()
    clean_name = file_name.strip()
    if not clean_name.endswith(".py"):
        clean_name += ".py"

    target_file = target / clean_name
    if not target_file.exists():
        available = [f.name for f in target.glob("*.py")]
        return f"File '{clean_name}' not found in {target}. Available files: {', '.join(available)}"

    try:
        with open(target_file, "r", encoding="utf-8", errors="replace") as f:
            code = f.read()
        tree = ast.parse(code, filename=str(target_file))
    except Exception as e:
        return f"Could not parse '{clean_name}': {e}"

    lines = code.splitlines()
    output = [f"Functions and Classes in `{clean_name}` (Total Lines: {len(lines)}):"]

    found_symbols = False
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            found_symbols = True
            doc = ast.get_docstring(node) or "No docstring."
            doc_snippet = doc.strip().splitlines()[0] if doc.strip() else ""
            output.append(f"\n[Class] {node.name} (Lines {node.lineno}-{getattr(node, 'end_lineno', node.lineno)})")
            if doc_snippet:
                output.append(f"  Doc: \"{doc_snippet}\"")

            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    sub_doc = ast.get_docstring(sub) or ""
                    sub_doc_snippet = sub_doc.strip().splitlines()[0] if sub_doc.strip() else ""
                    args = [a.arg for a in sub.args.args if a.arg != "self"]
                    output.append(f"  • method {sub.name}({', '.join(args)}) [Line {sub.lineno}]")
                    if sub_doc_snippet:
                        output.append(f"    \"{sub_doc_snippet}\"")

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found_symbols = True
            doc = ast.get_docstring(node) or ""
            doc_snippet = doc.strip().splitlines()[0] if doc.strip() else ""
            args = [a.arg for a in node.args.args]
            output.append(f"\n[Function] {node.name}({', '.join(args)}) (Lines {node.lineno}-{getattr(node, 'end_lineno', node.lineno)})")
            if doc_snippet:
                output.append(f"  Doc: \"{doc_snippet}\"")

    if not found_symbols:
        output.append("No top-level functions or classes defined in this file (script or configuration structure).")

    return "\n".join(output)


def find_symbol_references(symbol_name: str) -> str:
    """
    Finds which files define or call a specific function, class, or variable name across the project.
    """
    target = get_target_dir()
    clean_sym = symbol_name.strip()
    py_files = sorted(list(target.glob("*.py")))
    matches: List[str] = []

    for file_path in py_files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            for idx, line in enumerate(lines, 1):
                if clean_sym in line:
                    matches.append(f"{file_path.name}:{idx} -> {line.strip()[:100]}")
        except Exception:
            continue

    if matches:
        return f"Found {len(matches)} reference(s) to '{clean_sym}':\n" + "\n".join(matches[:20])
    return f"No references found for symbol '{clean_sym}' in {target.name}."
