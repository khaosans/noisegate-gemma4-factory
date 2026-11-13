"""Model factory. Gemma is served through any OpenAI-compatible endpoint:

  Ollama on the Mac:   base_url=http://localhost:11434/v1   model=gemma4 (your local tag)
  vLLM (Kaggle/GPU):   base_url=http://localhost:8000/v1    model=google/gemma-4-31b-it

Requires `pip install langchain-openai` (see requirements-agent.txt). The supervisor only
needs a LangChain chat model, so any other provider class works the same way.
"""
from __future__ import annotations

import os


def make_chat_model(model: str | None = None, base_url: str | None = None,
                    temperature: float = 0.2, max_tokens: int = 4096):
    from langchain_openai import ChatOpenAI  # optional dependency

    return ChatOpenAI(
        model=model or os.environ.get("NOISEGATE_MODEL", "gemma4"),
        base_url=base_url or os.environ.get("NOISEGATE_BASE_URL", "http://localhost:11434/v1"),
        api_key=os.environ.get("NOISEGATE_API_KEY", "not-needed-for-local"),
        temperature=temperature,
        max_tokens=max_tokens,
    )
