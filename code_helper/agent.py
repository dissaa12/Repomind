"""
code_helper/agent.py - Google ADK Multi-Agent Team (1 Boss + 4 Workers + MCP)
Implements coordinator, code_searcher, code_explainer, architecture_mapper, and onboarding_guide.
"""

# pyright: reportMissingImports=false
import os
import shutil
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Robust imports for tools and Google ADK / MCP components
try:
    from .tools.rag_tools import rag_search
    from .tools.ast_tools import (
        analyze_imports,
        list_functions_and_classes,
        find_symbol_references,
        get_target_dir,
    )
    from .tools.onboarding_tools import get_project_overview, get_execution_guide
    from .tools.code_tools import get_file_summary, read_specific_lines
except (ImportError, ValueError):
    from tools.rag_tools import rag_search
    from tools.ast_tools import (
        analyze_imports,
        list_functions_and_classes,
        find_symbol_references,
        get_target_dir,
    )
    from tools.onboarding_tools import get_project_overview, get_execution_guide
    from tools.code_tools import get_file_summary, read_specific_lines

# Ensure virtualenv site-packages are accessible even when invoked via system python
_venv_site_packages = Path(__file__).resolve().parent.parent / "backend" / ".venv" / "Lib" / "site-packages"
if _venv_site_packages.exists() and str(_venv_site_packages) not in sys.path:
    sys.path.insert(0, str(_venv_site_packages))

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

try:
    from .prompts import (
        COORDINATOR_SYSTEM_PROMPT,
        COORDINATOR_DESCRIPTION,
        CODE_SEARCHER_SYSTEM_PROMPT,
        CODE_SEARCHER_DESCRIPTION,
        CODE_EXPLAINER_SYSTEM_PROMPT,
        CODE_EXPLAINER_DESCRIPTION,
        ARCHITECTURE_MAPPER_SYSTEM_PROMPT,
        ARCHITECTURE_MAPPER_DESCRIPTION,
        ONBOARDING_GUIDE_SYSTEM_PROMPT,
        ONBOARDING_GUIDE_DESCRIPTION,
    )
except (ImportError, ValueError):
    from prompts import (
        COORDINATOR_SYSTEM_PROMPT,
        COORDINATOR_DESCRIPTION,
        CODE_SEARCHER_SYSTEM_PROMPT,
        CODE_SEARCHER_DESCRIPTION,
        CODE_EXPLAINER_SYSTEM_PROMPT,
        CODE_EXPLAINER_DESCRIPTION,
        ARCHITECTURE_MAPPER_SYSTEM_PROMPT,
        ARCHITECTURE_MAPPER_DESCRIPTION,
        ONBOARDING_GUIDE_SYSTEM_PROMPT,
        ONBOARDING_GUIDE_DESCRIPTION,
    )


# -----------------------------------------------------------------------------
# 1. Model Configuration (LiteLLM with NVIDIA NIM -> Gemini -> Default Fallback)
# -----------------------------------------------------------------------------
def get_shared_model() -> LiteLlm:
    """
    Constructs the shared LiteLLM model object.
    Supports NVIDIA NIM as specified in the student guide, with seamless Gemini fallback.
    """
    nvidia_key = os.getenv("NVIDIA_API_KEY") or os.getenv("NVIDIA_NIM_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if nvidia_key:
        os.environ["NVIDIA_NIM_API_KEY"] = nvidia_key
        model_name = os.getenv("NVIDIA_CHAT_MODEL", "meta/llama-3.2-11b-vision-instruct")
        return LiteLlm(model=f"nvidia_nim/{model_name}")
    elif gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key
        return LiteLlm(model="gemini/gemini-3.8-flash")
    elif os.getenv("OPENAI_API_KEY"):
        return LiteLlm(model="gpt-4o-mini")
    else:
        return LiteLlm(model="gemini/gemini-3.8-flash")


model = get_shared_model()


# -----------------------------------------------------------------------------
# 2. Connect Filesystem MCP Server for Code Explainer
# -----------------------------------------------------------------------------
target_codebase_dir = str(get_target_dir())
explainer_tools = [get_file_summary, read_specific_lines]

npx_bin = shutil.which("npx.cmd") or shutil.which("npx") or "npx"

try:
    file_tools = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=npx_bin,
                args=["-y", "@modelcontextprotocol/server-filesystem", target_codebase_dir],
            ),
            timeout=30,
        ),
        tool_filter=["list_directory", "read_file"],
    )
    explainer_tools.insert(0, file_tools)
except Exception as e:
    print(f"[!] Notice: Filesystem MCP initialization: {e}. Using native fallback tools.")


# -----------------------------------------------------------------------------
# 3. Build the 4 Worker Agents
# -----------------------------------------------------------------------------

# Worker 1: Code Searcher (Finds where something is using RAG)
searcher = LlmAgent(
    name="code_searcher",
    model=model,
    description=CODE_SEARCHER_DESCRIPTION,
    instruction=CODE_SEARCHER_SYSTEM_PROMPT,
    tools=[rag_search],
)

# Worker 2: Code Explainer (Reads whole files and explains them via MCP)
explainer = LlmAgent(
    name="code_explainer",
    model=model,
    description=CODE_EXPLAINER_DESCRIPTION,
    instruction=CODE_EXPLAINER_SYSTEM_PROMPT,
    tools=explainer_tools,
)

# Worker 3: Architecture Mapper (Analyzes file dependencies & symbols with plain Python AST)
mapper = LlmAgent(
    name="architecture_mapper",
    model=model,
    description=ARCHITECTURE_MAPPER_DESCRIPTION,
    instruction=ARCHITECTURE_MAPPER_SYSTEM_PROMPT,
    tools=[analyze_imports, list_functions_and_classes, find_symbol_references],
)

# Worker 4: Onboarding Guide (Explains what project does and where to start)
guide = LlmAgent(
    name="onboarding_guide",
    model=model,
    description=ONBOARDING_GUIDE_DESCRIPTION,
    instruction=ONBOARDING_GUIDE_SYSTEM_PROMPT,
    tools=[get_project_overview, get_execution_guide],
)


# -----------------------------------------------------------------------------
# 4. Build the Boss / Coordinator Agent
# -----------------------------------------------------------------------------
root_agent = LlmAgent(
    name="coordinator",
    model=model,
    description=COORDINATOR_DESCRIPTION,
    instruction=COORDINATOR_SYSTEM_PROMPT,
    sub_agents=[searcher, explainer, mapper, guide],
)
