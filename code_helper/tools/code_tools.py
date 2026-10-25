"""
code_helper/tools/code_tools.py - Code Inspection & File Summarization Tools
Provides fast file structure inspection and line-range extraction.
"""

try:
    from .ast_tools import get_target_dir
except ImportError:
    from ast_tools import get_target_dir


def get_file_summary(file_name: str) -> str:
    """
    Returns a structural summary of a source file including total lines, primary functions,
    and responsibilities before reading the full file.
    """
    target = get_target_dir()
    clean = file_name.strip()
    if not clean.endswith(".py"):
        clean += ".py"

    target_file = target / clean
    if not target_file.exists():
        available = [f.name for f in target.glob("*.py")]
        return f"File '{clean}' not found in {target}. Available files: {', '.join(available)}"

    try:
        with open(target_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        total_lines = len(lines)
        imports = [l.strip() for l in lines if l.strip().startswith(("import ", "from "))]
        defs = [l.strip().split("(")[0].replace("def ", "").replace("class ", "")
                for l in lines if l.strip().startswith(("def ", "class "))]

        return f"""File Summary: `{clean}`
- Total Lines: {total_lines}
- Imports: {len(imports)} dependencies
- Top-level Definitions ({len(defs)}): {', '.join(defs[:8])}
- Path: {target_file}
"""
    except Exception as e:
        return f"Could not summarize '{clean}': {e}"


def read_specific_lines(file_name: str, start_line: int, end_line: int) -> str:
    """
    Reads a specific line range from a file in the project.
    Useful for inspecting exact functions without dumping the entire file.
    """
    target = get_target_dir()
    clean = file_name.strip()
    if not clean.endswith(".py"):
        clean += ".py"

    target_file = target / clean
    if not target_file.exists():
        return f"File '{clean}' not found in {target}."

    try:
        with open(target_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        start = max(1, start_line)
        end = min(len(lines), end_line)

        if start > end:
            return f"Invalid line range: {start}-{end} (file has {len(lines)} lines)."

        extracted = lines[start - 1 : end]
        output = [f"--- `{clean}` (Lines {start}-{end}) ---"]
        for idx, line in enumerate(extracted, start):
            output.append(f"{idx:4d} | {line.rstrip()}")

        return "\n".join(output)
    except Exception as e:
        return f"Could not read lines from '{clean}': {e}"
