"""
Configuration management for OpenClaw Mine.

Loads and validates config from ~/.openclaw_mine/config.json.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Default paths
# ---------------------------------------------------------------------------

DEFAULT_CONFIG_DIR = Path.home() / ".wingman"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.json"
DEFAULT_WORKSPACE = DEFAULT_CONFIG_DIR / "workspace"


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class AgentDefaults(BaseModel):
    workspace: str = str(DEFAULT_WORKSPACE)
    model: str = "ollama/kimi-k2.5:cloud"
    max_tokens: int = 8192
    temperature: float = 0.7
    max_tool_iterations: int = 25
    workspace_sandboxed: bool = True  # Enforce workspace boundaries for all operations


class AgentConfig(BaseModel):
    defaults: AgentDefaults = Field(default_factory=AgentDefaults)


class GeminiProvider(BaseModel):
    api_key: str = ""
    api_base: str = "https://generativelanguage.googleapis.com/v1beta"


class OllamaProvider(BaseModel):
    api_base: str = "http://localhost:11434"
    model: str = "kimi-k2.5:cloud"


class OpenRouterProvider(BaseModel):
    api_key: str = ""
    api_base: str = "https://openrouter.ai/api/v1"


class OpenAIProviderConfig(BaseModel):
    api_key: str = ""
    api_base: str = "https://api.openai.com/v1"
    model: str = "gpt-4o"


class OpenAIChatProviderConfig(BaseModel):
    api_key: str = ""
    api_base: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"


class KimiProviderConfig(BaseModel):
    api_key: str = ""
    api_base: str = "https://api.moonshot.ai/v1"
    model: str = "kimi-k2.5"


class ProvidersConfig(BaseModel):
    kimi: KimiProviderConfig = Field(default_factory=KimiProviderConfig)
    gemini: GeminiProvider = Field(default_factory=GeminiProvider)
    ollama: OllamaProvider = Field(default_factory=OllamaProvider)
    openrouter: OpenRouterProvider = Field(default_factory=OpenRouterProvider)
    openai: OpenAIProviderConfig = Field(default_factory=OpenAIProviderConfig)
    openai_chat: OpenAIChatProviderConfig = Field(default_factory=OpenAIChatProviderConfig)


class WebSearchConfig(BaseModel):
    provider: str = "duckduckgo"
    api_key: str = ""
    max_results: int = 5


class WebToolConfig(BaseModel):
    search: WebSearchConfig = Field(default_factory=WebSearchConfig)


class ShellToolConfig(BaseModel):
    enabled: bool = True
    allowed_commands: list[str] = Field(default_factory=lambda: ["*"])
    blocked_commands: list[str] = Field(default_factory=lambda: [
        "rm -rf /", "rm -rf /*", "mkfs", "dd if=", "format",
        "curl | sh", "wget | sh", "curl | bash", "wget | bash",
        ":(){:|:&};:", "chmod 777", "chmod -R 777",
    ])
    workspace_restricted: bool = True  # Only allow commands in workspace


class BrowserToolConfig(BaseModel):
    enabled: bool = True


class CronToolConfig(BaseModel):
    enabled: bool = True


class ToolsConfig(BaseModel):
    web: WebToolConfig = Field(default_factory=WebToolConfig)
    shell: ShellToolConfig = Field(default_factory=ShellToolConfig)
    browser: BrowserToolConfig = Field(default_factory=BrowserToolConfig)
    cron: CronToolConfig = Field(default_factory=CronToolConfig)


class TelegramChannel(BaseModel):
    enabled: bool = False
    token: str = ""
    allow_from: list[str] = Field(default_factory=list)


class DiscordChannel(BaseModel):
    enabled: bool = False
    token: str = ""
    allow_from: list[str] = Field(default_factory=list)


class WebChatChannel(BaseModel):
    enabled: bool = True
    port: int = 8080


class WhatsAppChannel(BaseModel):
    enabled: bool = False
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_number: str = ""  # Format: whatsapp:+14155238886
    allow_from: list[str] = Field(default_factory=list)


class SlackChannel(BaseModel):
    enabled: bool = False
    bot_token: str = ""
    app_token: str = ""  # For Socket Mode
    allow_from: list[str] = Field(default_factory=list)


class ChannelsConfig(BaseModel):
    telegram: TelegramChannel = Field(default_factory=TelegramChannel)
    discord: DiscordChannel = Field(default_factory=DiscordChannel)
    webchat: WebChatChannel = Field(default_factory=WebChatChannel)
    whatsapp: WhatsAppChannel = Field(default_factory=WhatsAppChannel)
    slack: SlackChannel = Field(default_factory=SlackChannel)


class GatewayConfig(BaseModel):
    port: int = 18789
    host: str = "127.0.0.1"


class Settings(BaseModel):
    """Root configuration model for OpenClaw Mine."""

    agents: AgentConfig = Field(default_factory=AgentConfig)
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    channels: ChannelsConfig = Field(default_factory=ChannelsConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    gateway: GatewayConfig = Field(default_factory=GatewayConfig)

    @property
    def workspace_path(self) -> Path:
        """Resolved workspace path (expands ~)."""
        return Path(os.path.expanduser(self.agents.defaults.workspace))

    @property
    def config_dir(self) -> Path:
        """The ~/.openclaw_mine directory."""
        return DEFAULT_CONFIG_DIR

    def get_model_provider(self) -> str:
        """Extract provider name from model string (e.g. 'gemini/gemini-2.5-flash' -> 'gemini')."""
        model = self.agents.defaults.model
        if "/" in model:
            return model.split("/", 1)[0]
        return "gemini"

    def get_model_name(self) -> str:
        """Extract model name from model string (e.g. 'gemini/gemini-2.5-flash' -> 'gemini-2.5-flash')."""
        model = self.agents.defaults.model
        if "/" in model:
            return model.split("/", 1)[1]
        return model


# ---------------------------------------------------------------------------
# Singleton loader
# ---------------------------------------------------------------------------

_settings: Settings | None = None


def load_settings(config_path: Path | None = None) -> Settings:
    """Load settings from config JSON file. Creates defaults if file not found."""
    global _settings

    path = config_path or DEFAULT_CONFIG_PATH

    if path.exists():
        with open(path, "r") as f:
            raw: dict[str, Any] = json.load(f)
        _settings = Settings.model_validate(raw)
    else:
        _settings = Settings()

    return _settings


def get_settings() -> Settings:
    """Get the current settings instance (loads if needed)."""
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


def save_settings(settings: Settings, config_path: Path | None = None) -> None:
    """Write settings to the config JSON file."""
    path = config_path or DEFAULT_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(settings.model_dump(), f, indent=2)
