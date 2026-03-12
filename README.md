<p align="center">
  <img src="https://img.icons8.com/color/96/bot.png" alt="Wingman Logo" width="120"/>
</p>

<h1 align="center">🤖 Wingman</h1>

<p align="center">
  <strong>Enterprise-Grade AI Assistant with Multi-Agent Swarm Intelligence</strong>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-features">Features</a> •
  <a href="#-discord-bot-swarm">Bot Swarm</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-configuration">Configuration</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License"/>
  <img src="https://img.shields.io/badge/code%20style-black-000000?style=for-the-badge" alt="Code Style"/>
  <img src="https://img.shields.io/badge/Discord-Bot%20Swarm-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"/>
</p>

---

## ⚡ Quick Start

```bash
# Clone & Install
git clone https://github.com/yourusername/wingman.git && cd wingman
python -m venv venv && source venv/bin/activate
pip install -e .[all]

# Configure (add your API keys)
cp config.example.json ~/.wingman/config.json
nano ~/.wingman/config.json

# Run
python -m src.cli.app chat
```

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🧠 Multi-Provider LLM
- **Kimi K2.5** (Free tier!)
- **Gemini** (Free tier!)
- **OpenAI** GPT-4o
- **Ollama** (Local)
- **OpenRouter** (100+ models)

</td>
<td width="50%">

### 💬 6 Messaging Channels
- 🌐 **WebChat** - Built-in UI
- 📱 **Telegram** - Bot integration
- 🎮 **Discord** - Full bot support
- 💻 **CLI** - Terminal interface
- 📞 **WhatsApp** - Via Twilio
- 💼 **Slack** - Workspace bot

</td>
</tr>
<tr>
<td>

### 🛠️ 14+ Integrated Tools
- 📁 Filesystem operations
- 🖥️ Shell command execution
- 🔍 Web search (DuckDuckGo)
- 🌐 Browser automation
- 📄 Document processing
- 🎵 Media handling
- ⏰ Cron scheduling
- 🧠 Memory management

</td>
<td>

### 🔒 Enterprise Security
- 🔐 Workspace sandboxing
- 📝 Security audit logging
- ⚡ Rate limiting (token bucket)
- 🔄 Load balancing + circuit breaker
- 💓 Health monitoring
- 🛡️ Command blocklist

</td>
</tr>
</table>

---

## 🐝 Discord Bot Swarm

<p align="center">
  <strong>10 AI Agents Working Together 24/7</strong>
</p>

Run an autonomous team of specialized AI bots on Discord. They research, discuss, score ideas, and build projects together - all while you sleep!

### 🎭 Meet The Team

<table>
<tr>
<th>Bot</th>
<th>Role</th>
<th>Personality</th>
<th>What They Do</th>
</tr>
<tr>
<td>📡 <strong>Pulse</strong></td>
<td>News Hunter</td>
<td>Ex-TechCrunch journalist</td>
<td>Finds breaking AI news with real sources</td>
</tr>
<tr>
<td>🔬 <strong>Scout</strong></td>
<td>Researcher</td>
<td>PhD ML (ex-Google Brain)</td>
<td>Deep dives into papers, repos, implementations</td>
</tr>
<tr>
<td>💻 <strong>Builder</strong></td>
<td>Tech Lead</td>
<td>15 YOE (ex-Stripe/Meta)</td>
<td>Writes production code, builds prototypes</td>
</tr>
<tr>
<td>📊 <strong>Analyst</strong></td>
<td>Strategist</td>
<td>Data Scientist + MBA</td>
<td>Scores ideas with FIRE framework</td>
</tr>
<tr>
<td>🏗️ <strong>Blueprint</strong></td>
<td>Architect</td>
<td>20 YOE (ex-AWS/Netflix)</td>
<td>Designs scalable system architecture</td>
</tr>
<tr>
<td>🧪 <strong>Validator</strong></td>
<td>QA Lead</td>
<td>SDET (ex-Microsoft)</td>
<td>Writes tests, finds bugs, security checks</td>
</tr>
<tr>
<td>🚀 <strong>Deploy</strong></td>
<td>SRE</td>
<td>12 YOE (ex-Google SRE)</td>
<td>CI/CD, Docker, infrastructure</td>
</tr>
<tr>
<td>💡 <strong>Spark</strong></td>
<td>Innovator</td>
<td>Ex-founder (3 exits)</td>
<td>Wild ideas, sees opportunities</td>
</tr>
<tr>
<td>📝 <strong>Scribe</strong></td>
<td>Writer</td>
<td>Dev Advocate</td>
<td>Documentation, summaries, reports</td>
</tr>
<tr>
<td>🧠 <strong>Chief</strong></td>
<td>Manager</td>
<td>EM (ex-Spotify/Airbnb)</td>
<td>Runs syncs, makes decisions, assigns tasks</td>
</tr>
</table>

### 🔄 How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│                     🌙 OVERNIGHT OPERATION                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   Every 20-40 minutes:                                              │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐        │
│   │  📡     │    │  🔬     │    │  💡     │    │  💻     │        │
│   │ Pulse   │───▶│ Scout   │───▶│ Spark   │───▶│ Builder │        │
│   │ (News)  │    │(Research)│   │ (Ideas) │    │ (Code)  │        │
│   └─────────┘    └─────────┘    └─────────┘    └─────────┘        │
│                                                                     │
│   ════════════════════════════════════════════════════════════     │
│                                                                     │
│   📊 Analyst scores with FIRE:                                      │
│   ┌────────────┬────────────┬────────────┬────────────┐            │
│   │ Feasibility│   Impact   │    Risk    │   Effort   │            │
│   │    /10     │    /10     │    /10     │    /10     │            │
│   └────────────┴────────────┴────────────┴────────────┘            │
│                         │                                           │
│                         ▼                                           │
│              Score ≥ 28/40 (7.0 avg)                                │
│                    │                                                │
│          ┌─────────┴─────────┐                                      │
│          │                   │                                      │
│          ▼                   ▼                                      │
│     🟢 AUTO-BUILD       🔴 SKIP                                     │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                     ⏰ 09:00 DAILY SYNC                             │
│   Chief runs meeting → All bots report → Decisions made            │
│   → Scribe writes summary → Saved to ~/.wingman/swarm/             │
└─────────────────────────────────────────────────────────────────────┘
```

### 🚀 Run The Swarm

```bash
# Start overnight operation (runs until you stop it)
python run_overnight.py

# Or run the basic swarm
python run_swarm.py

# Check logs
tail -f overnight.log
```

### 📂 Shared Memory

All bots collaborate through shared directories:

```
~/.wingman/swarm/
├── 📡 trends/        # Pulse's AI news digests
├── 🔬 research/      # Scout's papers & repos
├── 💡 ideas/         # Spark's project proposals
├── 📊 analysis/      # Analyst's FIRE scores
├── 🏗️ architecture/  # Blueprint's system designs
├── 💻 projects/      # Builder's code
├── 🧪 tests/         # Validator's test suites
├── 🐛 bugs/          # Bug reports
├── 🚀 devops/        # Deploy's configs
├── 📝 docs/          # Scribe's documentation
├── 🧠 decisions/     # Chief's decisions
└── 📋 syncs/         # Daily meeting summaries
```

---

## 🏗️ Architecture

```
                              ┌─────────────────────────────────┐
                              │     🌐 Gateway (FastAPI)        │
                              │       127.0.0.1:18789           │
                              └───────────────┬─────────────────┘
                                              │
        ┌───────────────────────────────────────────────────────────┐
        │                                                           │
   ┌────┴────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
   │ WebChat │  │Telegram │  │ Discord │  │  Slack  │  │WhatsApp │
   │   🌐    │  │   📱    │  │   🎮    │  │   💼    │  │   📞    │
   └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘
        │            │            │            │            │
        └────────────┴────────────┼────────────┴────────────┘
                                  │
                         ┌────────┴────────┐
                         │  🎯 Agent Router │
                         └────────┬────────┘
                                  │
     ┌────────────────────────────┼────────────────────────────┐
     │              │             │             │              │
┌────┴────┐   ┌─────┴────┐  ┌─────┴────┐  ┌─────┴────┐  ┌─────┴────┐
│Research │   │ Engineer │  │  Writer  │  │  Data    │  │ Browser  │
│   🔬    │   │    💻    │  │    📝    │  │   📊     │  │    🌐    │
└────┬────┘   └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘
     │              │             │             │              │
     └──────────────┴─────────────┼─────────────┴──────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │    🛠️ Tool Registry       │
                    │    📚 Skills Hub          │
                    │    💾 Memory System       │
                    └─────────────┬─────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
    ┌─────┴─────┐          ┌──────┴──────┐         ┌─────┴─────┐
    │ ⚡ Rate   │          │ 💓 Health   │         │ 🔐 Security│
    │  Limiter  │          │  Monitor    │         │   Audit    │
    └───────────┘          └─────────────┘         └───────────┘
```

---

## ⚙️ Configuration

### Minimal Setup

```json
// ~/.wingman/config.json
{
  "agents": {
    "defaults": {
      "model": "ollama/qwen3:32b",
      "max_tokens": 8192
    }
  },
  "providers": {
    "ollama": {
      "api_base": "http://localhost:11434"
    }
  }
}
```

### Full Configuration

<details>
<summary>📄 Click to expand full config</summary>

```json
{
  "agents": {
    "defaults": {
      "workspace": "~/.wingman/workspace",
      "model": "ollama/qwen3:32b",
      "max_tokens": 8192,
      "temperature": 0.7,
      "max_tool_iterations": 25
    }
  },
  "providers": {
    "kimi": {
      "api_key": "your-key",
      "api_base": "https://api.moonshot.ai/v1"
    },
    "gemini": {
      "api_key": "your-key"
    },
    "ollama": {
      "api_base": "http://localhost:11434",
      "model": "qwen3:32b"
    },
    "openrouter": {
      "api_key": "your-key"
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "your-bot-token"
    },
    "discord": {
      "enabled": true,
      "token": "your-bot-token"
    }
  },
  "swarm": {
    "enabled": true,
    "sync_channel_id": 123456789,
    "sync_time": "09:00",
    "tokens": {
      "research": "discord-bot-token",
      "engineer": "discord-bot-token",
      "writer": "discord-bot-token",
      "data": "discord-bot-token",
      "coordinator": "discord-bot-token",
      "trend_watcher": "discord-bot-token",
      "architect": "discord-bot-token",
      "tester": "discord-bot-token",
      "devops": "discord-bot-token",
      "innovator": "discord-bot-token"
    }
  }
}
```

</details>

### Provider Options

| Provider | Free Tier | Model | Get API Key |
|----------|:---------:|-------|-------------|
| **Ollama** | ✅ Local | `ollama/qwen3:32b` | [ollama.ai](https://ollama.ai) |
| **Kimi** | ✅ Yes | `kimi/kimi-k2.5` | [moonshot.ai](https://platform.moonshot.ai) |
| **Gemini** | ✅ Yes | `gemini/gemini-2.5-flash` | [aistudio.google.com](https://aistudio.google.com) |
| OpenAI | ❌ Paid | `openai/gpt-4o` | [platform.openai.com](https://platform.openai.com) |
| OpenRouter | 💰 Pay/use | `openrouter/*` | [openrouter.ai](https://openrouter.ai) |

---

## 📦 Installation Options

```bash
# Full installation (recommended)
pip install -e .[all]

# Specific features
pip install -e .[discord]      # Discord bot
pip install -e .[voice]        # Wake word + STT + TTS
pip install -e .[browser]      # Browser automation
pip install -e .[dev]          # Development tools
```

---

## 🎯 Usage

### CLI Commands

```bash
# Chat
wingman chat                    # Interactive mode
wingman chat -m "Hello"         # Single message

# Gateway
wingman gateway                 # Start web server
wingman gateway -p 8080         # Custom port

# Swarm
wingman swarm start             # Launch Discord bots
wingman swarm status            # Check bot status
wingman swarm sync              # Trigger sync meeting

# Tools
wingman doctor                  # System health check
wingman memory search "topic"   # Search memory
```

### Discord Slash Commands

Each bot has its own commands:

| Bot | Commands |
|-----|----------|
| 📡 Pulse | `/trends`, `/digest` |
| 🔬 Scout | `/research [topic]` |
| 💻 Builder | `/build [project]` |
| 📊 Analyst | `/score [idea]` |
| 🏗️ Blueprint | `/design [system]` |
| 🧪 Validator | `/test [component]`, `/validate` |
| 🚀 Deploy | `/setup [project]`, `/deploy` |
| 💡 Spark | `/brainstorm`, `/innovate [problem]` |
| 🧠 Chief | `/sync` |
| All | `/ask [question]`, `/status` |

---

## 📊 Workspace Structure

```
~/.wingman/
├── 📄 config.json           # Main configuration
├── 📁 workspace/
│   ├── 💬 sessions/         # Chat history
│   ├── 🧠 memory/           # Long-term memory
│   ├── ⚡ skills/           # Custom skills
│   └── ⏰ cron/             # Scheduled tasks
├── 🐝 swarm/                # Bot swarm data
│   ├── trends/
│   ├── research/
│   ├── projects/
│   └── ...
└── 🔌 extensions/           # Plugins
```

---

## 🔒 Security

| Feature | Description |
|---------|-------------|
| 🔐 **Sandbox** | All file ops restricted to workspace |
| 🚫 **Blocklist** | Dangerous commands blocked (`rm -rf /`, etc.) |
| 📝 **Audit Log** | All security events logged |
| ⚡ **Rate Limit** | Token bucket + sliding window |
| 🔄 **Circuit Breaker** | Auto-recovery from failures |

---

## 🛠️ Development

```bash
# Setup
pip install -e .[dev]

# Test
pytest

# Lint
ruff check src/
black src/

# Type check
mypy src/
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>Built with ❤️ for the AI community</strong>
</p>

<p align="center">
  <a href="https://github.com/yourusername/wingman/issues">Report Bug</a> •
  <a href="https://github.com/yourusername/wingman/issues">Request Feature</a>
</p>
