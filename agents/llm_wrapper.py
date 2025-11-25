"""Lightweight wrapper for an LLM backend (OpenAI). If OpenAI is not available or no API key is set,
the wrapper will return a friendly fallback message.
"""
import os
from typing import Optional

_HAS_OPENAI = False
try:
    import openai
    _HAS_OPENAI = True
except Exception:
    _HAS_OPENAI = False


def ask_llm(prompt: str, model: str = "gpt-3.5-turbo", api_key: Optional[str] = None) -> str:
    """Ask the configured LLM. If api_key is provided it is used for the request; otherwise FALLBACK to env.

    Returns a friendly fallback if the openai package or API key is missing.
    The api_key parameter is intended to be passed from a UI session (in-memory) and not written to disk.
    """
    if not _HAS_OPENAI:
        return "LLM backend not available (openai package not installed). Install openai and set OPENAI_API_KEY to enable."

    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        return "OPENAI_API_KEY not set. Provide a key in the Streamlit sidebar or set the environment variable to enable LLM responses."

    try:
        openai.api_key = key
        # Use chat completions where available
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"LLM request failed: {e}"
