"""
Provider Manager — selects the right LLM provider and handles failover.

Model string format: "provider/model-name"
  - "kimi/kimi-k2.5"           → Kimi K2.5 provider (default)
  - "gemini/gemini-2.5-flash"  → Gemini provider
  - "ollama/deepseek-r1:14b"   → Ollama provider
  - "openrouter/anthropic/claude-opus-4-5" → OpenRouter provider
"""

from __future__ import annotations

import logging
from typing import Any

from src.config.settings import Settings, get_settings
from src.providers.base import LLMProvider, LLMResponse, Message, ToolDefinition
from src.providers.gemini import GeminiProvider
from src.providers.kimi import KimiProvider
from src.providers.ollama import OllamaProvider
from src.providers.openrouter import OpenRouterProvider

logger = logging.getLogger(__name__)


class ProviderManager:
    """
    Manages LLM providers with automatic failover.

    Priority: configured default → kimi → gemini → ollama → openrouter
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._providers: dict[str, LLMProvider] = {}
        self._init_providers()

    def _init_providers(self) -> None:
        """Initialize all configured providers."""
        cfg = self.settings.providers

        # Kimi K2.5 (default — Moonshot AI)
        if cfg.kimi.api_key and cfg.kimi.api_key != "YOUR_KIMI_API_KEY":
            self._providers["kimi"] = KimiProvider(
                api_key=cfg.kimi.api_key,
                api_base=cfg.kimi.api_base,
                model=self.settings.get_model_name()
                if self.settings.get_model_provider() == "kimi"
                else cfg.kimi.model,
            )

        # Gemini
        if cfg.gemini.api_key and cfg.gemini.api_key != "YOUR_GEMINI_API_KEY":
            self._providers["gemini"] = GeminiProvider(
                api_key=cfg.gemini.api_key,
                model=self.settings.get_model_name()
                if self.settings.get_model_provider() == "gemini"
                else "gemini-2.5-flash",
                api_base=cfg.gemini.api_base,
            )

        # Ollama (always available if running)
        self._providers["ollama"] = OllamaProvider(
            api_base=cfg.ollama.api_base,
            model=cfg.ollama.model,
        )

        # OpenRouter
        if cfg.openrouter.api_key:
            self._providers["openrouter"] = OpenRouterProvider(
                api_key=cfg.openrouter.api_key,
                api_base=cfg.openrouter.api_base,
                model=self.settings.get_model_name()
                if self.settings.get_model_provider() == "openrouter"
                else "",
            )

    def get_provider(self, provider_name: str | None = None) -> LLMProvider:
        """
        Get a specific provider by name, or the default.

        Falls back through the priority chain if the requested provider
        is not available.
        """
        if provider_name and provider_name in self._providers:
            return self._providers[provider_name]

        # Use configured default
        default_provider = self.settings.get_model_provider()
        if default_provider in self._providers:
            return self._providers[default_provider]

        # Fallback priority
        for name in ["kimi", "gemini", "ollama", "openrouter"]:
            if name in self._providers:
                logger.info(f"Falling back to {name} provider")
                return self._providers[name]

        raise RuntimeError(
            "No LLM providers available. Configure at least one provider in config.json.\n"
            "Options:\n"
            "  1. Set providers.kimi.api_key (get one at https://platform.moonshot.cn)\n"
            "  2. Set providers.gemini.api_key (free at https://aistudio.google.com)\n"
            "  3. Install Ollama (https://ollama.com) and run: ollama pull deepseek-r1:14b\n"
            "  4. Set providers.openrouter.api_key (https://openrouter.ai)"
        )

    async def get_healthy_provider(self) -> LLMProvider:
        """
        Get the first healthy provider, with failover.

        Tries the default provider first, then falls back through the chain.
        """
        default_provider = self.settings.get_model_provider()
        priority = [default_provider] + [
            p for p in ["gemini", "ollama", "openrouter"] if p != default_provider
        ]

        for name in priority:
            if name in self._providers:
                provider = self._providers[name]
                try:
                    if await provider.health_check():
                        logger.info(f"Using provider: {name}")
                        return provider
                    else:
                        logger.warning(f"Provider {name} health check failed, trying next...")
                except Exception as e:
                    logger.warning(f"Provider {name} error: {e}, trying next...")

        # If no health check passes, return the default anyway
        return self.get_provider()

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream: bool = False,
        provider_name: str | None = None,
    ) -> LLMResponse:
        """
        Send a chat request with automatic failover.

        Uses the default provider first, falls back if it fails.
        """
        temperature = temperature or self.settings.agents.defaults.temperature
        max_tokens = max_tokens or self.settings.agents.defaults.max_tokens

        provider = self.get_provider(provider_name)

        try:
            return await provider.chat(
                messages=messages,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
            )
        except Exception as e:
            logger.error(f"Primary provider failed: {e}")
            # Try failover
            for name, fallback in self._providers.items():
                if fallback is not provider:
                    try:
                        logger.info(f"Attempting failover to {name}...")
                        return await fallback.chat(
                            messages=messages,
                            tools=tools,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            stream=stream,
                        )
                    except Exception as fe:
                        logger.warning(f"Failover to {name} also failed: {fe}")
                        continue

            raise RuntimeError(f"All providers failed. Last error: {e}") from e

    async def health_report(self) -> dict[str, Any]:
        """Get health status of all providers."""
        report = {}
        for name, provider in self._providers.items():
            try:
                healthy = await provider.health_check()
                report[name] = {
                    "status": "healthy" if healthy else "unhealthy",
                    "info": provider.get_model_info(),
                }
            except Exception as e:
                report[name] = {
                    "status": "error",
                    "error": str(e),
                    "info": provider.get_model_info(),
                }
        return report
