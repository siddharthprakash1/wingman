# Wingman 🦞

**Personal AI Assistant - OpenClaw-style Architecture**

A self-hosted, privacy-first AI assistant that runs on your own hardware. Connect through messaging apps you already use, with full control over your data.

## Features

- **Multi-Provider LLM Support**: Gemini, OpenAI, Kimi K2.5, Ollama (local), OpenRouter
- **Multi-Channel Messaging**: Telegram, Discord, WebChat UI
- **Specialized Agents**: Research, Coding, Writing, Data Analysis, System Admin
- **Persistent Memory**: Session history, daily logs, long-term memory with semantic search
- **Skills System**: Modular task-specific capabilities
- **Plugin Architecture**: Extensible channels, tools, providers, and agents

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Gateway (WebSocket)                     │
│                     127.0.0.1:18789                         │
├─────────────┬─────────────┬─────────────┬──────────────────┤
│   WebChat   │   Telegram  │   Discord   │      CLI         │
│     UI      │    Bot      │    Bot      │                  │
└──────┬──────┴──────┬──────┴──────┬──────┴────────┬─────────┘
       │             │             │               │
       └─────────────┴─────────────┴───────────────┘
                            │
                    ┌───────┴───────┐
                    │  Agent Router  │
                    └───────┬───────┘
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
   ┌───┴───┐           ┌────┴────┐          ┌───┴───┐
   │Research│           │  Coder  │          │Writer │ ...
   │ Agent  │           │  Agent  │          │ Agent │
   └───┬───┘           └────┬────┘          └───┬───┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                    ┌───────┴───────┐
                    │  Tool Registry │
                    │  (bash, files, │
                    │   web, etc.)   │
                    └───────────────┘
```

## Quick Start

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
