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
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -e .
```

### 2. Setup

```bash
# Interactive setup wizard
python -m src.main onboard
```

This will:
- Configure your LLM provider (Gemini, OpenAI, Kimi, etc.)
- Initialize the workspace at `~/.wingman/workspace/`
- Create default configuration

### 3. Run

```bash
# Start the gateway server (includes WebChat UI)
python -m src.main gateway

# Open http://127.0.0.1:18789 in your browser
```

Or chat directly from the terminal:

```bash
# Single message
python -m src.main agent -m "What's the weather like?"

# Interactive mode
python -m src.main agent
```

## Configuration

Configuration is stored in `~/.wingman/config.json`:

```json
{
  "agents": {
    "defaults": {
      "model": "gemini/gemini-2.5-flash",
      "max_tokens": 8192,
      "temperature": 0.7
    }
  },
  "providers": {
    "gemini": {
      "api_key": "your-api-key"
    }
  },
  "channels": {
    "telegram": {
      "enabled": false,
      "token": ""
    }
  }
}
```

### Provider Options

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
