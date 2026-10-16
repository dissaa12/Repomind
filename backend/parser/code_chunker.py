"""
backend/parser/code_chunker.py - Syntax & Scope-Aware Code Chunker
Extracts classes, functions, and semantic code blocks enriched with line numbers and symbol metadata.
"""

import ast
import re
from typing import Any, Dict, List, Optional
from config import get_settings


def parse_python_ast_chunks(content: str, rel_path: str) -> List[Dict[str, Any]]:
    """
    Parses Python code using the standard library `ast` module to extract classes,
    methods, and standalone functions with exact line numbers and docstrings.
    """
    lines = content.splitlines()
    total_lines = len(lines)
    if total_lines == 0:
        return []

    chunks: List[Dict[str, Any]] = []

    # Extract top-of-file imports and module docstring as context header
    imports: List[str] = []
    for line in lines[:40]:
        stripped = line.strip()
        if stripped.startswith(("import ", "from ", "#")) or stripped == "":
            imports.append(line)
        elif imports and stripped:
            break
    context_header = "\n".join(imports[:25]).strip()

    try:
        tree = ast.parse(content)
    except SyntaxError:
        # Fallback to regex-based chunker if file has syntax errors
        return fallback_block_chunker(content, rel_path, "python", context_header)

    covered_line_ranges: List[tuple[int, int]] = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", None)
            if not end_line:
                # Approximate end line if end_lineno is missing in older AST
                end_line = start_line + len(ast.unparse(node).splitlines())
            end_line = min(end_line, total_lines)

            symbol_name = node.name
            symbol_type = "class" if isinstance(node, ast.ClassDef) else "function"

            docstring = ast.get_docstring(node) or ""
            chunk_lines = lines[start_line - 1 : end_line]
            chunk_code = "\n".join(chunk_lines)

            covered_line_ranges.append((start_line, end_line))

            chunks.append({
                "id": f"{rel_path}:{start_line}-{end_line}:{symbol_name}",
                "file_path": rel_path,
                "language": "python",
                "symbol_name": symbol_name,
                "symbol_type": symbol_type,
                "docstring": docstring,
                "start_line": start_line,
                "end_line": end_line,
                "code": chunk_code,
                "context_header": context_header,
                "search_text": f"File: {rel_path} ({symbol_type} {symbol_name})\n{docstring}\n{chunk_code}"
            })

    # If file had no top-level functions/classes (e.g. script or config), chunk entire file or lines
    if not chunks:
        return fallback_block_chunker(content, rel_path, "python", context_header)

    return chunks


def parse_js_ts_chunks(content: str, rel_path: str, language: str) -> List[Dict[str, Any]]:
    """
    Parses JavaScript/TypeScript code using regex pattern matching for classes,
    exported functions, and arrow functions.
    """
    lines = content.splitlines()
    total_lines = len(lines)
    if total_lines == 0:
        return []

    # Extract imports as context header
    imports: List[str] = []
    for line in lines[:35]:
        stripped = line.strip()
        if stripped.startswith(("import ", "require(", "///", "//")) or stripped == "":
            imports.append(line)
        elif imports and stripped:
            break
    context_header = "\n".join(imports[:20]).strip()

    # Pattern for JS/TS function/class declarations
    pattern = re.compile(
        r"^(?:export\s+(?:default\s+)?)?(?:async\s+)?(?:function\*?\s+([a-zA-Z0-9_$]+)|class\s+([a-zA-Z0-9_$]+)|(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>|(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*function)",
        re.MULTILINE
    )

    matches = []
    for idx, line in enumerate(lines):
        match = pattern.match(line.strip())
        if match:
            name = next((g for g in match.groups() if g), "anonymous")
            matches.append((idx + 1, name))

    if not matches:
        return fallback_block_chunker(content, rel_path, language, context_header)

    chunks: List[Dict[str, Any]] = []
    settings = get_settings()

    for i, (start_line, symbol_name) in enumerate(matches):
        next_start = matches[i + 1][0] if i + 1 < len(matches) else total_lines + 1
        end_line = min(next_start - 1, start_line + settings.max_chunk_lines, total_lines)
        if end_line < start_line:
            end_line = start_line

        chunk_lines = lines[start_line - 1 : end_line]
        chunk_code = "\n".join(chunk_lines)

        chunks.append({
            "id": f"{rel_path}:{start_line}-{end_line}:{symbol_name}",
            "file_path": rel_path,
            "language": language,
            "symbol_name": symbol_name,
            "symbol_type": "function/component",
            "docstring": "",
            "start_line": start_line,
            "end_line": end_line,
            "code": chunk_code,
            "context_header": context_header,
            "search_text": f"File: {rel_path} ({symbol_name})\n{chunk_code}"
        })

    return chunks


def parse_markdown_chunks(content: str, rel_path: str) -> List[Dict[str, Any]]:
    """
    Parses Markdown files section-by-section based on headers (#, ##, ###).
    """
    lines = content.splitlines()
    total_lines = len(lines)
    if total_lines == 0:
        return []

    sections = []
    current_title = "Overview"
    current_start = 1

    for idx, line in enumerate(lines):
        if line.startswith(("# ", "## ", "### ")):
            if idx + 1 > current_start:
                sections.append((current_start, idx, current_title))
            current_title = line.strip("# \t")
            current_start = idx + 1

    sections.append((current_start, total_lines, current_title))

    chunks: List[Dict[str, Any]] = []
    for start_line, end_line, title in sections:
        if end_line < start_line:
            continue
        chunk_lines = lines[start_line - 1 : end_line]
        chunk_text = "\n".join(chunk_lines).strip()
        if not chunk_text:
            continue

        chunks.append({
            "id": f"{rel_path}:{start_line}-{end_line}:{title[:30]}",
            "file_path": rel_path,
            "language": "markdown",
            "symbol_name": title[:40],
            "symbol_type": "section",
            "docstring": "",
            "start_line": start_line,
            "end_line": end_line,
            "code": chunk_text,
            "context_header": f"# {title}",
            "search_text": f"File: {rel_path} Section: {title}\n{chunk_text}"
        })

    return chunks


def fallback_block_chunker(
    content: str,
    rel_path: str,
    language: str,
    context_header: str = ""
) -> List[Dict[str, Any]]:
    """
    Fallback sliding window block chunker preserving line boundaries.
    """
    settings = get_settings()
    lines = content.splitlines()
    total_lines = len(lines)
    if total_lines == 0:
        return []

    chunks: List[Dict[str, Any]] = []
    window = settings.max_chunk_lines
    step = max(1, window - settings.line_overlap)

    start = 1
    while start <= total_lines:
        end = min(start + window - 1, total_lines)
        chunk_lines = lines[start - 1 : end]
        chunk_code = "\n".join(chunk_lines)

        symbol_name = f"Lines {start}-{end}"
        chunks.append({
            "id": f"{rel_path}:{start}-{end}",
            "file_path": rel_path,
            "language": language,
            "symbol_name": symbol_name,
            "symbol_type": "block",
            "docstring": "",
            "start_line": start,
            "end_line": end,
            "code": chunk_code,
            "context_header": context_header,
            "search_text": f"File: {rel_path} ({symbol_name})\n{chunk_code}"
        })

        if end == total_lines:
            break
        start += step

    return chunks


def chunk_file(file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Selects the optimal parsing strategy based on file language.
    """
    content = file_info.get("content", "")
    rel_path = file_info.get("relative_path", "")
    language = file_info.get("language", "text")

    if language == "python":
        return parse_python_ast_chunks(content, rel_path)
    elif language in ("javascript", "typescript"):
        return parse_js_ts_chunks(content, rel_path, language)
    elif language == "markdown":
        return parse_markdown_chunks(content, rel_path)
    else:
        return fallback_block_chunker(content, rel_path, language)
