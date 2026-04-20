"""
Configuration management for Wingman.

Loads and validates config from ~/.wingman/config.json, then layers env-var
overrides on top (from .env and real env vars).
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# .env loading (best-effort)
# ---------------------------------------------------------------------------

def _find_dotenv() -> Path | None:
    """Walk up from CWD looking for a .env, stopping at the git root."""
    candidates = [Path.cwd() / ".env"]
    for parent in Path.cwd().parents:
        candidates.append(parent / ".env")
        if (parent / ".git").exists():
            break
    for p in candidates:
        if p.exists():
            return p
    return None


def _load_dotenv_minimal(path: Path) -> None:
    """
    Tiny KEY=VALUE parser — fallback when python-dotenv isn't installed.
    Supports comments, blank lines, optional `export` prefix, and
    surrounding single or double quotes. Does NOT expand variables.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip()
        if (len(val) >= 2) and ((val[0] == val[-1]) and val[0] in ("'", '"')):
            val = val[1:-1]
        if key and key not in os.environ:
            os.environ[key] = val


def _load_dotenv_if_available() -> None:
    """
    Load .env from CWD or repo root into os.environ. Prefers python-dotenv
    if installed; otherwise uses a tiny built-in parser so the feature
    still works on systems without the dep.
    """
    path = _find_dotenv()
    if path is None:
        return
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv(path, override=False)
    except ImportError:
        _load_dotenv_minimal(path)


_load_dotenv_if_available()


# ---------------------------------------------------------------------------
# Default paths
# ---------------------------------------------------------------------------

DEFAULT_CONFIG_DIR = Path.home() / ".wingman"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.json"
DEFAULT_WORKSPACE = DEFAULT_CONFIG_DIR / "workspace"


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class RagConfig(BaseModel):
    auto_retrieve: bool = True
    top_k: int = 3
    min_score: float = 0.3
    collection: str = "documents"


class AgentDefaults(BaseModel):
    workspace: str = str(DEFAULT_WORKSPACE)
    model: str = "ollama/kimi-k2.5:cloud"
    max_tokens: int = 8192
    temperature: float = 0.7
    max_tool_iterations: int = 25
    workspace_sandboxed: bool = True


class AgentConfig(BaseModel):
    defaults: AgentDefaults = Field(default_factory=AgentDefaults)
    rag: RagConfig = Field(default_factory=RagConfig)


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


class GroqProviderConfig(BaseModel):
    api_key: str = ""
    api_base: str = "https://api.groq.com/openai/v1"
    model: str = "llama-3.3-70b-versatile"


class ProvidersConfig(BaseModel):
    kimi: KimiProviderConfig = Field(default_factory=KimiProviderConfig)
    gemini: GeminiProvider = Field(default_factory=GeminiProvider)
    ollama: OllamaProvider = Field(default_factory=OllamaProvider)
    openrouter: OpenRouterProvider = Field(default_factory=OpenRouterProvider)
    openai: OpenAIProviderConfig = Field(default_factory=OpenAIProviderConfig)
    openai_chat: OpenAIChatProviderConfig = Field(default_factory=OpenAIChatProviderConfig)
    groq: GroqProviderConfig = Field(default_factory=GroqProviderConfig)


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
    workspace_restricted: bool = True
    strict_whitelist: bool = False  # If True, only `allowed_commands` first-words may run


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
    twilio_whatsapp_number: str = ""
    allow_from: list[str] = Field(default_factory=list)


class SlackChannel(BaseModel):
    enabled: bool = False
    bot_token: str = ""
    app_token: str = ""
    allow_from: list[str] = Field(default_factory=list)


class VoiceConfig(BaseModel):
    enabled: bool = False
    wake_word: str = "wingman"
    stt_provider: str = "google"
    tts_provider: str = "pyttsx3"
    picovoice_access_key: str = ""
    elevenlabs_api_key: str = ""


class ChannelsConfig(BaseModel):
    telegram: TelegramChannel = Field(default_factory=TelegramChannel)
    discord: DiscordChannel = Field(default_factory=DiscordChannel)
    webchat: WebChatChannel = Field(default_factory=WebChatChannel)
    whatsapp: WhatsAppChannel = Field(default_factory=WhatsAppChannel)
    slack: SlackChannel = Field(default_factory=SlackChannel)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)


class GatewayConfig(BaseModel):
    port: int = 18789
    host: str = "127.0.0.1"


class SwarmBotTokens(BaseModel):
    research: str = ""
    engineer: str = ""
    writer: str = ""
    data: str = ""
    coordinator: str = ""
    trend_watcher: str = ""
    architect: str = ""
    tester: str = ""
    devops: str = ""
    innovator: str = ""


class SwarmConfig(BaseModel):
    enabled: bool = False
    sync_channel_id: int = 0
    sync_time: str = "09:00"
    swarm_dir: str = str(Path.home() / ".wingman" / "swarm")
    tokens: SwarmBotTokens = Field(default_factory=SwarmBotTokens)


class OvernightConfig(BaseModel):
    """Settings for the Night Lab pipeline (run_overnight.py)."""
    provider: str = "openai"  # Key from ProvidersConfig: openai / groq / kimi / ...
    model: str = "gpt-4o-mini"
    cycle_minutes: int = 60
    max_tokens_per_stage: int = 2048
    themes: list[str] = Field(default_factory=lambda: [
        "AI agents and tooling",
        "Developer productivity",
        "Open source LLM releases",
        "Applied ML engineering",
    ])
    post_to_discord: bool = False  # If True, also posts the brief to the sync channel
    discord_channel_id: int = 0


class Settings(BaseModel):
    """Root configuration model for Wingman."""
    agents: AgentConfig = Field(default_factory=AgentConfig)
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    channels: ChannelsConfig = Field(default_factory=ChannelsConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    gateway: GatewayConfig = Field(default_factory=GatewayConfig)
    swarm: SwarmConfig = Field(default_factory=SwarmConfig)
    overnight: OvernightConfig = Field(default_factory=OvernightConfig)

    @property
    def workspace_path(self) -> Path:
        return Path(os.path.expanduser(self.agents.defaults.workspace))

    @property
    def config_dir(self) -> Path:
        return DEFAULT_CONFIG_DIR

    def get_model_provider(self) -> str:
        model = self.agents.defaults.model
        if "/" in model:
            return model.split("/", 1)[0]
        return "gemini"

    def get_model_name(self) -> str:
        model = self.agents.defaults.model
        if "/" in model:
            return model.split("/", 1)[1]
        return model


# ---------------------------------------------------------------------------
# Env overrides
# ---------------------------------------------------------------------------

def _apply_env_overrides(settings: Settings) -> Settings:
    """
    Overlay environment variables on top of config.json.
    env wins over config.json.
    """
    env = os.environ

    # Providers
    if v := env.get("KIMI_API_KEY"):
        settings.providers.kimi.api_key = v
    if v := env.get("GEMINI_API_KEY"):
        settings.providers.gemini.api_key = v
    if v := env.get("OPENAI_API_KEY"):
        settings.providers.openai.api_key = v
        if not settings.providers.openai_chat.api_key:
            settings.providers.openai_chat.api_key = v
    if v := env.get("OPENROUTER_API_KEY"):
        settings.providers.openrouter.api_key = v
    if v := env.get("GROQ_API_KEY"):
        settings.providers.groq.api_key = v
    if v := env.get("OLLAMA_API_BASE"):
        settings.providers.ollama.api_base = v

    # Overnight
    if v := env.get("OVERNIGHT_PROVIDER"):
        settings.overnight.provider = v
    if v := env.get("OVERNIGHT_MODEL"):
        settings.overnight.model = v
    if v := env.get("OVERNIGHT_CYCLE_MINUTES"):
        try:
            settings.overnight.cycle_minutes = int(v)
        except ValueError:
            pass

    # Workspace
    if v := env.get("WINGMAN_WORKSPACE"):
        settings.agents.defaults.workspace = v

    return settings


# ---------------------------------------------------------------------------
# Singleton loader
# ---------------------------------------------------------------------------

_settings: Settings | None = None


def load_settings(config_path: Path | None = None) -> Settings:
    """Load settings from config JSON + .env. Creates defaults if file not found."""
    global _settings

    path = config_path or DEFAULT_CONFIG_PATH

    if path.exists():
        with open(path, "r") as f:
            raw: dict[str, Any] = json.load(f)
        _settings = Settings.model_validate(raw)
    else:
        _settings = Settings()

    _settings = _apply_env_overrides(_settings)
    return _settings


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


def save_settings(settings: Settings, config_path: Path | None = None) -> None:
    path = config_path or DEFAULT_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(settings.model_dump(), f, indent=2)
