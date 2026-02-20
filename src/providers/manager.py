"""
Provider Manager — selects the right LLM provider and handles failover.

Model string format: "provider/model-name"
  - "kimi/kimi-k2.5"           → Kimi K2.5 provider (default)
  - "gemini/gemini-2.5-flash"  → Gemini provider
  - "ollama/deepseek-r1:14b"   → Ollama provider
  - "openrouter/anthropic/claude-opus-4-5" → OpenRouter provider

Features round-robin load balancing and automatic failover with exponential backoff.
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Any

from src.config.settings import Settings, get_settings
from src.providers.base import LLMProvider, LLMResponse, Message, ToolDefinition
from src.providers.gemini import GeminiProvider
from src.providers.kimi import KimiProvider
from src.providers.ollama import OllamaProvider
from src.providers.openai import OpenAIProvider
from src.providers.openrouter import OpenRouterProvider

class ProviderManager:
    """
    Manages LLM providers with automatic failover and round-robin load balancing.

    Features:
    - Round-robin selection across healthy providers
    - Automatic failover with exponential backoff
    - Health-based provider selection
    - Request distribution for better reliability
    
    Priority: configured default → kimi → gemini → ollama → openrouter
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._providers: dict[str, LLMProvider] = {}
        self._provider_order: list[str] = []  # For round-robin
        self._current_index = 0  # Round-robin index
        self._provider_stats: dict[str, dict[str, Any]] = {}  # Track usage stats
        self._init_providers()

    def _init_providers(self) -> None:Provider] = {}
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

        # OpenAI
        # OpenAI Chat (Weak/Cheap model)
        if cfg.openai_chat.api_key:
            self._providers["openai_chat"] = OpenAIProvider(
                api_key=cfg.openai_chat.api_key,
                api_base=cfg.openai_chat.api_base,
                model=self.settings.get_model_name()
                if self.settings.get_model_provider() == "openai_chat"
                else cfg.openai_chat.model,
            )
        
        # Initialize provider order for round-robin
        self._provider_order = list(self._providers.keys())
        
        # Initialize stats tracking
        for name in self._provider_order:
            self._provider_stats[name] = {
                "requests": 0,
                "successes": 0,
                "failures": 0,
                "last_failure": None,
                "consecutive_failures": 0,
            }

    def get_provider(self, provider_name: str | None = None) -> LLMProvider:
            self._providers["openai_chat"] = OpenAIProvider(
                api_key=cfg.openai_chat.api_key,
                api_base=cfg.openai_chat.api_base,
                model=self.settings.get_model_name()
                if self.settings.get_model_provider() == "openai_chat"
                else cfg.openai_chat.model,
            )

    def get_provider(self, provider_name: str | None = None) -> LLMProvider:
        """
        Get a specific provider by name, or the default.

        Falls back through the priority chain if the requested provider
        is not available.
            "  5. Set providers.openrouter.api_key (https://openrouter.ai)"
        )
    
    def get_next_round_robin_provider(self) -> LLMProvider | None:
        """
        Get the next provider using round-robin selection.
        
        Skips providers with recent consecutive failures.
        """
        if not self._provider_order:
            return None
        
        # Try all providers in round-robin order
        attempts = 0
        while attempts < len(self._provider_order):
            name = self._provider_order[self._current_index]
            self._current_index = (self._current_index + 1) % len(self._provider_order)
            attempts += 1
            
            # Skip providers with too many consecutive failures (circuit breaker)
            stats = self._provider_stats.get(name, {})
            if stats.get("consecutive_failures", 0) >= 3:
                logger.debug(f"Skipping {name} due to consecutive failures")
                continue
            
            if name in self._providers:
                return self._providers[name]
        
        # If all providers are circuit-broken, return default anyway
        return self.get_provider()
    
    def record_success(self, provider_name: str) -> None:
        """Record a successful request for a provider."""
        if provider_name in self._provider_stats:
            stats = self._provider_stats[provider_name]
            stats["requests"] += 1
            stats["successes"] += 1
            stats["consecutive_failures"] = 0  # Reset on success
    
    def record_failure(self, provider_name: str) -> None:
        """Record a failed request for a provider."""
        if provider_name in self._provider_stats:
            stats = self._provider_stats[provider_name]
            stats["requests"] += 1
            stats["failures"] += 1
            stats["consecutive_failures"] += 1
            stats["last_failure"] = asyncio.get_event_loop().time()

    async def get_healthy_provider(self) -> LLMProvider:
        # Use configured default
        default_provider = self.settings.get_model_provider()
        if default_provider in self._providers:
            return self._providers[default_provider]

        # Fallback priority
        for name in ["kimi", "gemini", "ollama", "openai", "openai_chat", "openrouter"]:
            if name in self._providers:
                logger.info(f"Falling back to {name} provider")
                return self._providers[name]

        raise RuntimeError(
            "No LLM providers available. Configure at least one provider in config.json.\n"
            "Options:\n"
            "  1. Set providers.kimi.api_key (get one at https://platform.moonshot.cn)\n"
            "  2. Set providers.gemini.api_key (free at https://aistudio.google.com)\n"
            "  3. Install Ollama (https://ollama.com) and run: ollama pull deepseek-r1:14b\n"
            "  4. Set providers.openai.api_key\n"
            "  5. Set providers.openrouter.api_key (https://openrouter.ai)"
        )

    async def get_healthy_provider(self) -> LLMProvider:
        """
        Get the first healthy provider, with failover.

        Tries the default provider first, then falls back through the chain.
        Uses non-blocking async health checks with timeout.
        """
        default_provider = self.settings.get_model_provider()
        priority = [default_provider] + [
            p for p in ["gemini", "ollama", "openai", "openrouter"] if p != default_provider
        ]

        async def check_provider(name: str) -> tuple[str, bool]:
            """Non-blocking health check for a single provider."""
            if name not in self._providers:
                return name, False
            
            provider = self._providers[name]
            try:
                # Run health check with timeout to prevent blocking
                is_healthy = await asyncio.wait_for(
                    provider.health_check(),
                    timeout=5.0  # 5 second timeout
                )
                return name, is_healthy
            except asyncio.TimeoutError:
                logger.warning(f"Provider {name} health check timed out")
                return name, False
            except Exception as e:
                logger.warning(f"Provider {name} health check error: {e}")
                return name, False

        # Check all providers concurrently
        tasks = [check_provider(name) for name in priority if name in self._providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Find first healthy provider
        for result in results:
            if isinstance(result, tuple):
                name, is_healthy = result
                if is_healthy:
                    logger.info(f"Using healthy provider: {name}")
                    return self._providers[name]
        
        # If no health check passes, return the default anyway
        logger.warning("No healthy providers found, using default")
        return self.get_provider()

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream: bool = False,
        provider_name: str | None = None,
        max_retries: int = 3,
    ) -> LLMResponse:
        """
        Send a chat request with automatic failover and exponential backoff.

        Uses round-robin load balancing when no specific provider is requested.
        Retries failed requests with exponential backoff.
        
        Args:
            messages: Conversation history
            tools: Available tools for function calling
            temperature: Sampling temperature
            max_tokens: Maximum response length
            stream: Enable streaming responses
            provider_name: Force specific provider (disables round-robin)
            max_retries: Maximum retry attempts per provider (default: 3)
        """
        temperature = temperature or self.settings.agents.defaults.temperature
        max_tokens = max_tokens or self.settings.agents.defaults.max_tokens

        # Get initial provider
        if provider_name:
            provider = self.get_provider(provider_name)
            providers_to_try = [(provider_name, provider)]
        else:
            # Use round-robin for load balancing
            provider = self.get_next_round_robin_provider()
            if provider:
                provider_name = next(
                    (name for name, p in self._providers.items() if p is provider),
                    None
                )
                providers_to_try = [(provider_name, provider)]
            else:
                providers_to_try = []
            
            # Add fallback providers
            for name, p in self._providers.items():
                if (name, p) not in providers_to_try:
                    providers_to_try.append((name, p))
        
        last_error = None
        
        # Try each provider with exponential backoff
        for idx, (prov_name, prov) in enumerate(providers_to_try):
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        # Exponential backoff: 1s, 2s, 4s
                        backoff = 2 ** attempt
                        logger.info(f"Retrying {prov_name} after {backoff}s backoff (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(backoff)
                    
                    response = await prov.chat(
                        messages=messages,
                        tools=tools,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        stream=stream,
                    )
                    
                    # Success!
                    self.record_success(prov_name)
                    if idx > 0 or attempt > 0:
                        logger.info(f"Successful failover to {prov_name}")
                    return response
                
                except Exception as e:
                    last_error = e
                    self.record_failure(prov_name)
                    
                    if attempt < max_retries - 1:
                        logger.warning(f"{prov_name} failed (attempt {attempt + 1}/{max_retries}): {e}")
                    else:
                        logger.error(f"{prov_name} failed after {max_retries} attempts: {e}")
                        # Move to next provider
                        break

        # All providers exhausted
        error_msg = f"All providers failed after retries. Last error: {last_error}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from last_error

    async def health_report(self) -> dict[str, Any]:
        """Get health status and usage statistics of all providers."""
        report = {}
        for name, provider in self._providers.items():
            try:
                healthy = await provider.health_check()
                stats = self._provider_stats.get(name, {})
                report[name] = {
                    "status": "healthy" if healthy else "unhealthy",
                    "info": provider.get_model_info(),
                    "stats": {
                        "total_requests": stats.get("requests", 0),
                        "successes": stats.get("successes", 0),
                        "failures": stats.get("failures", 0),
                        "consecutive_failures": stats.get("consecutive_failures", 0),
                        "success_rate": (
                            stats["successes"] / stats["requests"] * 100
                            if stats.get("requests", 0) > 0
                            else 0.0
                        ),
                    },
                }
            except Exception as e:
                report[name] = {
                    "status": "error",
                    "error": str(e),
                    "info": provider.get_model_info(),
                }
        return report
    
    def get_load_balancing_stats(self) -> dict[str, Any]:
        """Get load balancing and failover statistics."""
        return {
            "providers": list(self._provider_order),
            "current_round_robin_index": self._current_index,
            "stats": self._provider_stats,
        }
