"""
backend/llm/providers.py - Multi-Provider LLM Adapter with Streaming Support
Supports Google Gemini, OpenAI, Groq, Ollama, and an offline grounded Mock provider.
"""

import asyncio
import os
from typing import Any, AsyncGenerator, Dict, List, Optional
from config import get_settings


SYSTEM_PROMPT = """You are Repomind, an expert AI software architect and codebase intelligence assistant.
Your task is to answer user questions about the repository accurately and concisely, strictly grounded in the provided code snippets and file context.

Guidelines:
1. Always cite exact file paths and line ranges using the format `[filename:start_line-end_line]` (e.g., `[backend/config.py:15-32]`) when referencing code.
2. If explaining a function or class, state which file it resides in and explain how it interacts with other modules.
3. If the retrieved context does not contain enough information to answer definitively, acknowledge what is visible and state clearly what is missing.
4. Keep answers structured with clear headings, bullet points, and syntax-highlighted code blocks where helpful.
"""


def format_context_prompt(query: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
    """Formats retrieved code chunks into a context block for the LLM prompt."""
    if not retrieved_chunks:
        return f"User Question: {query}\n\n(No specific code context was retrieved for this repository.)"

    context_parts: List[str] = ["Retrieved Code Context from Repository:\n"]
    for idx, c in enumerate(retrieved_chunks, 1):
        fpath = c.get("file_path", "unknown")
        start = c.get("start_line", 1)
        end = c.get("end_line", 1)
        sym = c.get("symbol_name") or "block"
        header = c.get("context_header") or ""
        code = c.get("code") or ""

        context_parts.append(
            f"--- [Snippet {idx}] {fpath} (Lines {start}-{end}) Symbol: {sym} ---\n"
            f"{header}\n{code}\n"
        )

    context_parts.append(f"\nUser Question: {query}\n\nPlease provide a clear, grounded explanation citing the snippets above:")
    return "\n".join(context_parts)


async def generate_mock_stream(
    query: str,
    chunks: List[Dict[str, Any]]
) -> AsyncGenerator[str, None]:
    """
    Offline realistic mock generator when no API key is provided.
    Generates grounded analysis using the actual retrieved chunks.
    """
    yield "### Codebase Analysis (Repomind Mock AI Mode)\n\n"
    await asyncio.sleep(0.04)

    if not chunks:
        yield f"I searched the indexed codebase for: **\"{query}\"**, but did not find matching symbols or chunks. Try indexing a repository or querying a specific file name."
        return

    top_chunk = chunks[0]
    yield f"Based on the retrieved code for **\"{query}\"**, here is the breakdown:\n\n"
    await asyncio.sleep(0.04)

    yield f"#### Primary Location: `[{top_chunk['file_path']}:{top_chunk['start_line']}-{top_chunk['end_line']}]`\n"
    if top_chunk.get("symbol_name"):
        yield f"- **Symbol**: `{top_chunk['symbol_name']}` ({top_chunk.get('symbol_type', 'code')})\n"
    yield f"- **Relevance Score**: `{top_chunk.get('score', 0.95):.3f}`\n\n"
    await asyncio.sleep(0.04)

    yield "```" + top_chunk.get("language", "python") + "\n"
    lines = top_chunk.get("code", "").splitlines()
    for line in lines[:15]:
        yield line + "\n"
        await asyncio.sleep(0.02)
    if len(lines) > 15:
        yield f"... ({len(lines) - 15} more lines)\n"
    yield "```\n\n"

    yield "#### Key Architectural Findings:\n"
    yield f"1. The logic is defined in `[{top_chunk['file_path']}:{top_chunk['start_line']}-{top_chunk['end_line']}]`.\n"
    if len(chunks) > 1:
        c2 = chunks[1]
        yield f"2. Related references appear in `[{c2['file_path']}:{c2['start_line']}-{c2['end_line']}]` with symbol `{c2.get('symbol_name', 'code')}`.\n"
    yield "3. You can click on the citation badges below to jump directly to this file and line range in the Code Inspector panel on the right.\n\n"
    yield "> [!TIP]\n> Configure your `GEMINI_API_KEY`, `OPENAI_API_KEY`, or `GROQ_API_KEY` in the top Settings panel to enable live LLM generation!"


async def stream_gemini(prompt: str, api_key: str, model_name: str) -> AsyncGenerator[str, None]:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    target_model = model_name or "gemini-3.8-flash"
    if "2.5" in target_model:
        target_model = "gemini-3.8-flash"
    model = genai.GenerativeModel(
        model_name=target_model,
        system_instruction=SYSTEM_PROMPT
    )
    response = await asyncio.to_thread(model.generate_content, prompt, stream=True)
    for chunk in response:
        if chunk.text:
            yield chunk.text


async def stream_openai_compatible(
    prompt: str,
    api_key: str,
    base_url: Optional[str],
    model_name: str
) -> AsyncGenerator[str, None]:
    from openai import AsyncOpenAI
    from collections.abc import AsyncIterable
    client = AsyncOpenAI(api_key=api_key or "not-needed", base_url=base_url)
    stream = await client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        stream=True
    )
    if isinstance(stream, AsyncIterable):
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta


async def stream_chat_response(
    query: str,
    chunks: List[Dict[str, Any]],
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Unified entry point for streaming LLM responses across providers.
    """
    settings = get_settings()
    active_prov = provider or settings.active_provider
    active_model = model or settings.active_model
    prompt = format_context_prompt(query, chunks)

    # 1. Google Gemini
    if active_prov == "gemini":
        key = api_key or settings.gemini_api_key
        if key:
            try:
                async for token in stream_gemini(prompt, key, active_model):
                    yield token
                return
            except Exception as e:
                yield f"\n\n*(Gemini API encountered an error: {e}. Falling back to grounded mock mode)*\n\n"

    # 2. OpenAI
    elif active_prov == "openai":
        key = api_key or settings.openai_api_key
        if key:
            try:
                async for token in stream_openai_compatible(
                    prompt=prompt,
                    api_key=key,
                    base_url=None,
                    model_name=active_model or "gpt-4o-mini"
                ):
                    yield token
                return
            except Exception as e:
                yield f"\n\n*(OpenAI API error: {e}. Falling back to grounded mock mode)*\n\n"

    # 3. Groq
    elif active_prov == "groq":
        key = api_key or settings.groq_api_key
        if key:
            try:
                async for token in stream_openai_compatible(
                    prompt=prompt,
                    api_key=key,
                    base_url="https://api.groq.com/openai/v1",
                    model_name=active_model or "llama-3.3-70b-versatile"
                ):
                    yield token
                return
            except Exception as e:
                yield f"\n\n*(Groq API error: {e}. Falling back to grounded mock mode)*\n\n"

    # 4. Local Ollama
    elif active_prov == "ollama":
        try:
            base = settings.ollama_base_url.rstrip("/") + "/v1"
            async for token in stream_openai_compatible(
                prompt=prompt,
                api_key="ollama",
                base_url=base,
                model_name=active_model or "llama3.2"
            ):
                yield token
            return
        except Exception as e:
            yield f"\n\n*(Ollama connection error: {e}. Falling back to grounded mock mode)*\n\n"

    # Fallback to grounded Mock generator
    async for token in generate_mock_stream(query, chunks):
        yield token
