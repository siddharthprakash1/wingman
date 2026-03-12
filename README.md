# Wingman 🤖

**Enterprise-Grade AI Assistant with OpenClaw Architecture**

A production-ready, self-hosted AI assistant with advanced features: multi-channel messaging, voice capabilities, security sandboxing, load balancing, hot-reload plugins, and comprehensive monitoring.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## ✨ Features

### 🎯 Core Capabilities
- **Multi-Provider LLM Support**: Kimi K2.5, Gemini, OpenAI, Ollama (local), OpenRouter
- **6 Messaging Channels**: WebChat, Telegram, Discord, CLI, WhatsApp, Slack
- **8 Specialized Agents**: Research, Coding, Writing, Data Analysis, System Admin, Browser, Router, Base
- **Voice Capabilities**: Wake word detection (Porcupine), STT (Whisper/Google), TTS (OpenAI/ElevenLabs)
- **14+ Integrated Tools**: Filesystem, Shell, Web Search, Browser Automation, Documents, Media, and more

### 🔒 Security & Reliability
- **Workspace Sandboxing**: All file/shell operations restricted to safe boundaries
- **Security Audit Logging**: JSONL-based tracking of violations and blocked commands
- **Rate Limiting**: Token bucket and sliding window strategies for API calls
- **Load Balancing**: Round-robin provider selection with circuit breaker and exponential backoff
- **Health Monitoring**: Real-time metrics for CPU, memory, disk, and process health

### 🚀 Advanced Features
- **Multi-Agent Communication**: Parent-child agent hierarchy with message passing
- **Skills Hub**: ClawHub-style community skills with hot-reload (SHA256 checksums)
- **Plugin System**: Hot-reload, lifecycle management, dependency tracking
- **Autonomous Heartbeat**: Background tasks for cleanup, memory consolidation, health checks
- **Structured Logging**: JSON logs with search, Rich console output, log rotation
- **Testing Framework**: AgentTester with pytest fixtures for unit and integration tests

### 🐝 Discord Bot Swarm
- **5 Specialized Bots**: Scout (Research), Builder (Engineer), Scribe (Writer), Analyst (Data), Chief (Coordinator)
- **Daily Sync-Ups**: Automated meetings where bots discuss findings, score ideas, and decide on projects
- **Shared Memory**: Bots write to shared directories — research/, projects/, docs/, analysis/, decisions/
- **Idea Scoring**: FINE framework (Feasibility, Impact, Novelty, Effort) with 1-10 scoring and go/no-go decisions
- **Auto-Restart**: Exponential backoff on crashes, runs 24/7 on your old laptop
- **Gateway Integration**: REST API endpoints + CLI commands to monitor and control the swarm

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Gateway (FastAPI + WebSocket)                        │
│                         127.0.0.1:18789                                 │
├─────────┬──────────┬──────────┬─────────┬──────────┬──────────────────┤
│ WebChat │ Telegram │ Discord  │   CLI   │ WhatsApp │     Slack        │
│   UI    │   Bot    │   Bot    │         │  (Twilio)│  (Bolt+Socket)   │
└────┬────┴────┬─────┴────┬─────┴────┬────┴────┬─────┴────┬─────────────┘
     │         │          │          │         │          │
     └─────────┴──────────┴──────────┴─────────┴──────────┘
                            │
                    ┌───────┴────────┐
                    │  Agent Router  │  ← Smart task routing
                    └───────┬────────┘
                            │
       ┌────────────────────┼─────────────────────────┐
       │                    │                         │
   ┌───┴────┐          ┌────┴─────┐            ┌─────┴────┐
   │Research│          │  Coder   │            │  Writer  │ ...
   │ Agent  │          │  Agent   │            │  Agent   │
   └───┬────┘          └────┬─────┘            └─────┬────┘
       │                    │                         │
       └────────────────────┼─────────────────────────┘
                            │
                ┌───────────┴────────────┐
                │    Tool Registry       │
                │  + Sessions System     │ ← Multi-agent communication
                │  + Skills Hub          │ ← Hot-reload skills
                └───────────┬────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   ┌────┴─────┐       ┌─────┴──────┐     ┌─────┴──────┐
   │Rate      │       │Health      │     │Security    │
   │Limiter   │       │Monitor     │     │Audit       │
   └──────────┘       └────────────┘     └────────────┘
```

## 🚀 Quick Start

### 1. Install

```bash
# Clone the repository
git clone https://github.com/yourusername/wingman.git
cd wingman

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install base + all optional features
pip install -e .[all]

# Or install specific feature sets:
# pip install -e .[dev,discord,voice]  # Development + Discord + Voice
```

### 2. Configure

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys (at minimum, add one LLM provider)
# Required: KIMI_API_KEY or GEMINI_API_KEY or OPENAI_API_KEY
nano .env
```

### 3. Run

```bash
# Interactive setup wizard
python -m src.cli.app onboard

# Start WebChat UI + Gateway
python -m src.cli.app gateway
# Open http://127.0.0.1:18789

# Or chat in terminal
python -m src.cli.app chat
```

## 📦 Installation Options

| Package Extra | Description | Install Command |
|---------------|-------------|-----------------|
| `[all]` | Everything (recommended) | `pip install -e .[all]` |
| `[dev]` | Development tools | `pip install -e .[dev]` |
| `[discord]` | Discord bot | `pip install -e .[discord]` |
| `[whatsapp]` | WhatsApp (Twilio) | `pip install -e .[whatsapp]` |
| `[slack]` | Slack bot | `pip install -e .[slack]` |
| `[voice]` | Voice (wake word, STT, TTS) | `pip install -e .[voice]` |
| `[local]` | Local embeddings | `pip install -e .[local]` |
| `[extraction]` | LangExtract | `pip install -e .[extraction]` |
| `[browser]` | Browser automation | `pip install -e .[browser]` |

## ⚙️ Configuration

Configuration is managed through `~/.wingman/config.json` and environment variables (`.env`).

### Minimal Configuration

```bash
# .env
KIMI_API_KEY=your_kimi_api_key_here  # Free tier available at platform.moonshot.cn
DEFAULT_MODEL=kimi/kimi-k2.5
WINGMAN_WORKSPACE=~/.wingman/workspace
```

### Advanced Configuration

```json
// ~/.wingman/config.json
{
  "agents": {
    "defaults": {
      "model": "kimi/kimi-k2.5",
      "max_tokens": 8192,
      "temperature": 0.7,
      "max_tool_iterations": 25,
      "workspace_sandboxed": true  // Security: restrict operations to workspace
    }
  },
  "providers": {
    "kimi": {
      "api_key": "sk-...",
      "api_base": "https://api.moonshot.cn/v1",
      "model": "kimi-k2.5"
    },
    "gemini": {
      "api_key": "...",
      "api_base": "https://generativelanguage.googleapis.com/v1beta"
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "123456:ABC-DEF...",
      "allow_from": ["@username"]
    },
    "discord": {
      "enabled": true,
      "token": "..."
    },
    "whatsapp": {
      "enabled": false,
      "twilio_account_sid": "...",
      "twilio_auth_token": "...",
      "twilio_whatsapp_number": "whatsapp:+14155238886"
    },
    "slack": {
      "enabled": false,
      "bot_token": "xoxb-...",
      "app_token": "xapp-..."  // For Socket Mode
    }
  },
  "tools": {
    "shell": {
      "enabled": true,
      "workspace_restricted": true,
      "blocked_commands": ["rm -rf /", "mkfs", "format"]
    }
  }
}
```

### Provider Options

| Provider | Free Tier | Model Example | API Key Source |
|----------|-----------|---------------|----------------|
| **Kimi K2.5** ⭐ | ✅ Yes | `kimi/kimi-k2.5` | [platform.moonshot.cn](https://platform.moonshot.cn) |
| **Gemini** | ✅ Yes | `gemini/gemini-2.5-flash` | [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| **Ollama** | ✅ Local | `ollama/llama3:latest` | No key needed (local) |
| OpenAI | ❌ Paid | `openai/gpt-4o` | [platform.openai.com](https://platform.openai.com/api-keys) |
| OpenRouter | ❌ Paid | `openrouter/anthropic/claude-opus-4-5` | [openrouter.ai](https://openrouter.ai) |

## 🎯 Usage Examples

### Basic Chat
```bash
$ python -m src.cli.app chat
You: What's the weather like?
Wingman: I'll check the weather for you...
```

### Channel Integration
```bash
# Start Telegram bot
export TELEGRAM_BOT_TOKEN="123456:ABC..."
python -m src.channels.telegram

# Start Discord bot
export DISCORD_BOT_TOKEN="..."
python -m src.channels.discord
```

### Voice Interaction
```python
from src.voice import WakeWordDetector, SpeechToText, TextToSpeech

# Wake word detection
detector = WakeWordDetector(access_key="...", keywords=["porcupine"])
detector.start(lambda keyword: print(f"Wake word: {keyword}"))

# Speech-to-text
stt = SpeechToText(provider="openai_whisper")
text = await stt.transcribe_file("audio.wav")

# Text-to-speech
tts = TextToSpeech(provider="openai_tts", voice="alloy")
audio_bytes = await tts.synthesize("Hello world", output_path="output.mp3")
```

### Multi-Agent Workflow
```python
from src.tools.sessions import sessions_create, sessions_message

# Create child agent
child_id = sessions_create(
    task="Research the latest AI news",
    agent_type="research"
)

# Send message to child
response = sessions_message(
    session_id=child_id,
    message="Find news from the past week"
)
```

### Testing
```python
from src.testing import AgentTester, AgentTestCase

tester = AgentTester(settings=settings)

test_cases = [
    AgentTestCase(
        name="file_search",
        input="Find all Python files",
        expected_tools=["filesystem_list"],
        max_iterations=5
    )
]

results = await tester.run_test_suite(test_cases, session=session)
summary = tester.get_summary()
print(f"Pass rate: {summary['pass_rate']:.1%}")
```

## 🐝 Discord Bot Swarm

Run a team of 5 specialized AI bots on Discord that collaborate, hold daily meetings, and build projects together.

### Quick Start

```bash
# 1. Set up the swarm (interactive wizard)
wingman swarm setup

# 2. Start the swarm (runs 24/7)
wingman swarm start

# 3. Or start everything together (gateway + swarm)
wingman gateway
```

### The Bots

| Bot | Role | What It Does |
|-----|------|-------------|
| 🔬 Scout | Research | Finds trends, papers, tech news, and project ideas |
| 💻 Builder | Engineer | Writes code, creates prototypes, reviews architecture |
| 📝 Scribe | Writer | Documentation, blog posts, reports, and summaries |
| 📊 Analyst | Data | Evaluates ideas using FINE scoring (1-10 per category) |
| 🧠 Chief | Coordinator | Runs daily sync-ups, makes go/no-go decisions |

### Daily Sync-Up Protocol

Every day at the configured time (default 9:00 AM), the bots hold a structured meeting:

1. **Chief** opens the meeting
2. **Scout** reports latest research and trend findings
3. **Builder** shares technical assessments and prototypes
4. **Scribe** summarizes key themes
5. **Analyst** scores each idea: Feasibility + Impact + Novelty + Effort (0-40 scale)
6. **Chief** makes go/no-go decisions (≥ 7.0 average = GO)
7. **Scribe** writes the meeting summary to `~/.wingman/swarm/syncs/`

### CLI Commands

```bash
wingman swarm setup     # Interactive token setup wizard
wingman swarm start     # Launch all bots (24/7 mode)
wingman swarm status    # Check bot configuration and status
wingman swarm sync      # Manually trigger a sync-up meeting
wingman swarm ask research -m "What's trending in AI agents?"
```

### REST API (when gateway is running)

```bash
# Check swarm status
curl http://localhost:18789/api/swarm/status

# Trigger a sync
curl -X POST http://localhost:18789/api/swarm/sync

# Ask a bot
curl -X POST http://localhost:18789/api/swarm/ask \
  -H "Content-Type: application/json" \
  -d '{"bot": "research", "message": "What are the latest AI trends?"}'
```

### Discord Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create **5 applications** (one per bot)
3. For each: Bot → Reset Token → copy it
4. Enable **Message Content Intent** and **Server Members Intent**
5. Invite all 5 bots to your server with `applications.commands` + `bot` scopes
6. Create a `#daily-sync` channel and copy its ID
7. Run `wingman swarm setup` and paste the tokens

### Shared Memory

All bots write to `~/.wingman/swarm/`:

```
~/.wingman/swarm/
├── research/      # Scout's findings (trends, papers, ideas)
├── projects/      # Builder's code and prototypes
├── docs/          # Scribe's documentation and reports
├── analysis/      # Analyst's scoring and evaluations
├── decisions/     # Chief's go/no-go decisions
└── syncs/         # Daily meeting summaries (sync-YYYY-MM-DD.md)
```

## 🔒 Security Features

### Workspace Sandboxing
All file and shell operations are restricted to the configured workspace:

```python
# .env
WINGMAN_WORKSPACE=~/.wingman/workspace
WINGMAN_WORKSPACE_SANDBOXED=true
```

- **Path traversal protection**: Blocks `../` escape attempts
- **Blocked paths**: `/etc`, `/bin`, `/usr/bin`, `/sys`, etc.
- **Command blocklist**: `rm -rf /`, `mkfs`, `curl | sh`, fork bombs
- **Audit logging**: All violations logged to `~/.wingman/security_audit.jsonl`

### Security Audit

```bash
# View security audit log
tail -f ~/.wingman/security_audit.jsonl

# Example entry:
{
  "timestamp": "2026-02-20T10:30:00",
  "event_type": "path_traversal",
  "path": "/etc/passwd",
  "session_id": "abc123",
  "blocked": true
}
```

## 📊 Monitoring & Observability

### Health Checks
```python
from src.core.health import get_health_monitor, check_memory, check_disk

monitor = get_health_monitor()
monitor.register_check("memory", check_memory)
monitor.register_check("disk", check_disk)

# Run checks
results = await monitor.run_checks()
for name, result in results.items():
    print(f"{name}: {result.status} - {result.message}")
```

### Metrics Collection
```python
from src.core.health import get_health_monitor

monitor = get_health_monitor()

# Record metrics
monitor.metrics.increment("api_calls", tags={"provider": "openai"})
monitor.metrics.timing("request_duration", 123.45, tags={"endpoint": "/chat"})

# Get stats
stats = monitor.metrics.get_stats("request_duration")
print(f"Average: {stats['timing']['avg_ms']}ms")
print(f"P95: {stats['timing']['p95_ms']}ms")
```

### Structured Logging
```python
from src.core.logging import StructuredLogger

logger = StructuredLogger("app")

logger.info("Request received", session_id="abc123", user_id="user456")
logger.error("API failed", provider="openai", error_code=429)

# Search logs
results = logger.search_logs(query="failed", level="ERROR", limit=10)
```

## 🔄 Rate Limiting

```python
from src.core.rate_limiter import get_rate_limiter, RateLimitConfig, RateLimitStrategy

limiter = get_rate_limiter()

# Configure provider rate limit
limiter.configure(
    "openai",
    RateLimitConfig(
        max_requests=60,
        window_seconds=60,
        burst_size=10,
        strategy=RateLimitStrategy.TOKEN_BUCKET
    )
)

# Use in code
await limiter.acquire("openai")  # Waits if limit reached
```

## 🔌 Plugin Development

### Create a Plugin

```bash
mkdir -p extensions/my-tool-plugin
cd extensions/my-tool-plugin
```

```json
// plugin.json
{
  "name": "my-tool",
  "version": "1.0.0",
  "type": "tool",
  "description": "My custom tool",
  "author": "Your Name",
  "dependencies": []
}
```

```python
# __init__.py
def setup(loader):
    """Called when plugin is loaded."""
    print("My tool plugin loaded!")
    
    # Register tool
    loader.register_tool(
        name="my_tool",
        definition={"description": "Does something cool"},
        func=my_tool_function
    )

def my_tool_function(arg1: str) -> str:
    """Tool implementation."""
    return f"Processed: {arg1}"

def activate(loader):
    """Called when plugin becomes active."""
    print("Plugin activated!")

def deactivate(loader):
    """Called when plugin is deactivated."""
    print("Plugin deactivated!")

def teardown(loader):
    """Called when plugin is unloaded."""
    print("Plugin unloaded!")
```

### Hot-Reload Plugins

```python
from src.plugins.loader import PluginLoader

loader = PluginLoader(extensions_dir=Path("extensions"))

# Load all plugins
loaded = loader.load_all()

# Enable hot-reload (checks for file changes every 5s)
loader.enable_hot_reload(interval_seconds=5)

# Manually reload a plugin
loader.reload("my-tool")
```

## 📚 API Reference

### Core Modules

| Module | Description |
|--------|-------------|
| `src.agents` | Specialized agents (Research, Coding, Writer, Data, System, Browser, Router) |
| `src.channels` | Messaging channels (WebChat, Telegram, Discord, WhatsApp, Slack, CLI) |
| `src.providers` | LLM providers (Kimi, Gemini, OpenAI, Ollama, OpenRouter) |
| `src.tools` | Built-in tools (filesystem, shell, web_search, browser, documents, media) |
| `src.voice` | Voice capabilities (wake word, STT, TTS) |
| `src.core` | Core systems (runtime, session, rate_limiter, health, logging, heartbeat) |
| `src.skills` | Skills management (hub with hot-reload) |
| `src.plugins` | Plugin system (loader with lifecycle management) |
| `src.memory` | Memory management (transcript, search) |
| `src.testing` | Testing framework (AgentTester, fixtures) |
| `src.security` | Security (audit logging) |

## 🛠️ Development

### Setup Development Environment

```bash
# Install with dev dependencies
pip install -e .[dev]

# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Format code
black src/
ruff check src/ --fix

# Type checking
mypy src/
```

### Project Structure

```
wingman/
├── src/
│   ├── agents/          # Specialized AI agents
│   ├── channels/        # Messaging channel adapters
│   ├── cli/             # Command-line interface
│   ├── config/          # Configuration management
│   ├── core/            # Core runtime & systems
│   ├── gateway/         # WebSocket gateway server
│   ├── memory/          # Memory & transcript management
│   ├── plugins/         # Plugin system
│   ├── providers/       # LLM provider integrations
│   ├── retrieval/       # Vector store & embeddings
│   ├── security/        # Security audit
│   ├── skills/          # Skills hub
│   ├── testing/         # Testing framework
│   ├── tools/           # Tool registry & implementations
│   └── voice/           # Voice capabilities
├── tests/               # Test suites
├── extensions/          # Plugin directory
├── .env.example         # Environment variables template
├── pyproject.toml       # Package configuration
└── README.md
```

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

Inspired by:
- [OpenClaw](https://github.com/openclaw/openclaw) - Enterprise multi-channel architecture (213k⭐)
- [PicoClaw](https://github.com/picoclaw/picoclaw) - Lightweight Go implementation (16.6k⭐)

## 🔗 Links

- **Documentation**: [Coming Soon]
- **Discord Community**: [Coming Soon]
- **Bug Reports**: [GitHub Issues](https://github.com/yourusername/wingman/issues)
- **Roadmap**: [GitHub Projects](https://github.com/yourusername/wingman/projects)

---

**Built with ❤️ by the Wingman community**

| Provider | Model Example | Free Tier |
|----------|--------------|-----------|
| Gemini | `gemini/gemini-2.5-flash` | Yes |
| OpenAI | `openai/gpt-4o` | No |
| Kimi | `kimi/kimi-k2.5` | Yes |
| Ollama | `ollama/llama3` | Yes (local) |
| OpenRouter | `openrouter/anthropic/claude-3-5-sonnet` | Pay-per-use |

## Workspace Layout

```
~/.wingman/
├── config.json          # Main configuration
├── workspace/
│   ├── sessions/        # Chat session history
│   ├── memory/          # Daily logs
│   ├── skills/          # Custom skills
│   ├── cron/            # Scheduled tasks
│   ├── IDENTITY.md      # Who the assistant is
│   ├── SOUL.md          # Personality/tone
│   ├── AGENTS.md        # Behavioral rules
│   ├── USER.md          # User preferences (learned)
│   ├── MEMORY.md        # Long-term facts
│   └── TOOLS.md         # Tool usage conventions
└── extensions/          # Plugins
```

## Commands

```bash
# Setup
wingman onboard          # Interactive setup wizard

# Server
wingman gateway          # Start the gateway server
wingman gateway -p 8080  # Custom port

# Chat
wingman agent            # Interactive mode
wingman agent -m "Hi"    # Single message
wingman agent --stream   # Stream output

# Channels
wingman channels list    # List configured channels
wingman channels login telegram  # Configure Telegram

# Skills
wingman skills list      # List available skills
wingman skills create my-skill  # Create new skill

# Memory
wingman memory search "topic"  # Search memory
wingman memory rebuild   # Rebuild search index

# Health
wingman doctor           # Check system health
```

## Agents

### Built-in Agents

| Agent | Capabilities | Description |
|-------|-------------|-------------|
| **Research** | Web search, URL fetching | Information gathering and synthesis |
| **Engineer** | Code, files, shell | Software development |
| **Reviewer** | Code review | Quality assurance |
| **Writer** | Content creation | Documentation, articles, emails |
| **Data** | Analysis, visualization | Data processing and insights |
| **System** | Shell, packages | System administration |
| **Browser** | Web automation | Form filling, scraping |
| **Planner** | Task decomposition | Breaking down complex tasks |

### Agent Routing

Tasks are automatically routed to the most appropriate agent:

```
"Research Python best practices" → Research Agent
"Write a function to sort arrays" → Engineer Agent
"Review this code for bugs" → Reviewer Agent
"Draft an email to the team" → Writer Agent
```

## Skills

Skills are modular capabilities that can be activated on demand:

```
~/.wingman/workspace/skills/
├── research/
│   └── SKILL.md
├── coding/
│   └── SKILL.md
└── writing/
    └── SKILL.md
```

Create a skill:

```bash
wingman skills create my-skill
```

Skill format (`SKILL.md`):
```markdown
---
description: My custom skill
triggers: keyword1, keyword2
tools: bash, read_file
---

# Skill Instructions

Detailed instructions for the agent when this skill is active.
```

## Security

### Session Isolation

- **main**: Full access (CLI/local)
- **dm:\<channel\>:\<user\>**: Isolated per user
- **group:\<channel\>:\<group\>**: Isolated per group with restricted tools

### Tool Sandboxing

- Tool allowlists/denylists per session type
- Docker isolation for untrusted sessions (coming soon)
- Require approval for destructive operations

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/

# Linting
ruff check src/

# Format
black src/
```

## Contributing

Contributions welcome! Please read the contributing guidelines first.

## License

MIT License - see LICENSE file for details.

## Acknowledgments

Inspired by [OpenClaw](https://github.com/openclaw/openclaw) and [PicoClaw](https://github.com/sipeed/picoclaw).
