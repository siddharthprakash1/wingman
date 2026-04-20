"""
Groq LLM provider.

Groq exposes an OpenAI-compatible API at https://api.groq.com/openai/v1.
Any model listed at https://console.groq.com/docs/models works. Defaults to
llama-3.3-70b-versatile which is cheap, fast, and tool-calling capable.
"""

from __future__ import annotations

from src.providers._openai_compat import OpenAICompatibleProvider


class GroqProvider(OpenAICompatibleProvider):
    _provider_name = "groq"
    _context_window = 128_000

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.groq.com/openai/v1",
        model: str = "llama-3.3-70b-versatile",
    ):
        super().__init__(api_key=api_key, api_base=api_base, model=model)
