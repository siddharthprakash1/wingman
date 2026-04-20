<p align="center">
  <img src="https://img.icons8.com/color/120/bot.png" alt="Wingman logo" width="120"/>
</p>

<h1 align="center">Wingman</h1>

<p align="center">
  <strong>An AI copilot that doesn't sleep when you do.</strong>
  <br/>
  <sub>Multi-channel, multi-agent, multi-model — one workspace.</sub>
</p>

<p align="center">
  <a href="#-quick-start">Quick start</a> ·
  <a href="#-what-is-wingman">What is it?</a> ·
  <a href="#-architecture">Architecture</a> ·
  <a href="#-the-swarm">The swarm</a> ·
  <a href="#-tools">Tools</a> ·
  <a href="#-configuration">Config</a> ·
  <a href="#-troubleshooting">Troubleshooting</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+"/>
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge" alt="MIT license"/>
  <img src="https://img.shields.io/badge/style-black-000000?style=for-the-badge" alt="Code style: black"/>
  <img src="https://img.shields.io/badge/lint-ruff-d7ff64?style=for-the-badge" alt="Ruff"/>
  <img src="https://img.shields.io/badge/types-mypy-1e415e?style=for-the-badge" alt="mypy"/>
  <img src="https://img.shields.io/badge/async-asyncio-4584b6?style=for-the-badge" alt="asyncio"/>
  <br/>
  <img src="https://img.shields.io/badge/channels-6-5865F2?style=for-the-badge" alt="6 channels"/>
  <img src="https://img.shields.io/badge/providers-6-0ea5e9?style=for-the-badge" alt="6 providers"/>
  <img src="https://img.shields.io/badge/tools-18+-22c55e?style=for-the-badge" alt="18+ tools"/>
  <img src="https://img.shields.io/badge/swarm%20bots-10-f97316?style=for-the-badge" alt="10 swarm bots"/>
</p>

---

> **TL;DR** — Point Wingman at one or more LLM providers. Talk to it from a browser, Telegram, Discord, Slack, WhatsApp, or your terminal. Leave it running overnight and it will either (a) simulate a 10-person engineering team in a Discord channel that builds small projects for you to review, or (b) crank out a polished Morning Brief while you sleep. Everything happens inside a sandboxed workspace at `~/.wingman/`.

---

## 🚀 Quick start

```bash
# 1. Clone and install
git clone https://github.com/siddharthprakash1/wingman.git && cd wingman
python -m venv .venv && source .venv/bin/activate
pip install -e ".[all]"

# 2. Configure — at minimum, one LLM provider key
cp config.example.json ~/.wingman/config.json
cp .env.example .env          # then edit .env and drop in an API key
python -m src.main onboard    # interactive wizard (optional)

# 3. Run
make agent      # interactive CLI chat
make gateway    # FastAPI server + WebChat UI on 127.0.0.1:18789
make doctor     # system health check
```

<details>
<summary><strong>First-run checklist</strong> — what to set up in order</summary>

| Step | What | Why |
| ---- | ---- | --- |
| 1 | `cp .env.example .env` and add `OPENAI_API_KEY` (or `GROQ_API_KEY`, `GEMINI_API_KEY`, etc.) | Nothing runs without at least one provider |
| 2 | `python -m src.main doctor` | Confirms providers, tools, and sandbox are healthy |
| 3 | `python -m src.main agent --interactive` | Smoke-test in the CLI before wiring channels |
| 4 | Edit `~/.wingman/config.json` to enable a channel (webchat is on by default) | Turn on Discord / Telegram / Slack / WhatsApp only when their tokens exist |
| 5 | (Optional) Drop documents into `~/.wingman/workspace/` and call the `ingest_document` tool | Populates the RAG vector store |
| 6 | (Optional) Set all 10 Discord bot tokens under `swarm.tokens` and launch `python run_overnight.py` | Starts the 24/7 multi-agent swarm |

</details>

---

## 🧭 What is Wingman

Wingman is a **single Python process** (plus some helpers) that turns one or more LLM API keys into:

- 🗣️ **A chat interface you can talk to from 6 different places** (web, Discord, Telegram, Slack, WhatsApp, CLI).
- 🤖 **A tool-using agent** — it can read/write files, run shell commands, search the web, drive a browser, query SQLite, hit HTTP APIs, execute short Python snippets, run git, schedule cron jobs, and about ten other things. Every dangerous surface is sandboxed.
- 🐝 **An autonomous multi-agent swarm** — ten specialized persona bots that discuss, design, and build small projects overnight in a Discord channel. Or an alternate "Night Lab" mode that runs a focused 6-stage reasoning pipeline and leaves you a polished Morning Brief.
- 📚 **A personal knowledge base** — ingest PDFs / Markdown / text into an on-disk vector store; Wingman auto-retrieves relevant context on every turn (if enabled).

Every subsystem is replaceable: swap providers via config, disable channels you don't use, toggle tools on or off, pick your swarm mode. Nothing requires a GPU; nothing requires a paid API if you run Ollama locally.

> **Name note** — the repo directory is `openclaw_mine` (the project was originally inspired by the OpenClaw / PicoClaw architecture), but the package and product name are **Wingman**. The README, `pyproject.toml`, and CLI all use the Wingman name.

---

## 📚 Table of contents

- [🚀 Quick start](#-quick-start)
- [🧭 What is Wingman](#-what-is-wingman)
- [✨ Feature highlights](#-feature-highlights)
- [🏗️ Architecture](#-architecture)
- [🔌 LLM providers](#-llm-providers)
- [🛠️ Tools](#-tools)
- [📡 Channels](#-channels)
- [🐝 The swarm](#-the-swarm)
  - [LiveRoom — overnight build sessions](#liveroom--overnight-build-sessions)
  - [Night Lab — overnight reasoning pipeline](#night-lab--overnight-reasoning-pipeline)
  - [Meet the team](#meet-the-team)
- [🧠 Memory & RAG](#-memory--rag)
- [🔒 Security model](#-security-model)
- [⚙️ Configuration](#-configuration)
- [📦 Installation options](#-installation-options)
- [💻 CLI cheatsheet](#-cli-cheatsheet)
- [💬 Discord slash commands](#-discord-slash-commands)
- [📁 Workspace layout](#-workspace-layout)
- [🧪 Development](#-development)
- [🚑 Troubleshooting](#-troubleshooting)
- [🗺️ Repo layout](#-repo-layout)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## ✨ Feature highlights

<table>
<tr>
<td width="50%" valign="top">

### 🧠 Multi-provider LLM
Plug in any combination of:

- **OpenAI** — GPT-4o / gpt-4o-mini
- **Groq** — llama-3.3-70b (fastest tokens/sec)
- **Kimi** — Moonshot K2.5 (free tier)
- **Gemini** — 2.5 Flash / Pro (free tier)
- **Ollama** — everything local, no API key
- **OpenRouter** — 100+ models via one key

Round-robin load balancing, circuit breaker, exponential-backoff retries, health-check fanout.

</td>
<td width="50%" valign="top">

### 📡 Six channels
All channels hit the same gateway router:

- 🌐 **WebChat** — built-in HTML UI
- 💻 **CLI** — local terminal chat
- 💬 **Telegram** — bot integration
- 🎮 **Discord** — single bot or 10-bot swarm
- 💼 **Slack** — workspace bot (Socket Mode)
- 📞 **WhatsApp** — via Twilio

Per-channel `allow_from` lists restrict who can talk to the bot.

</td>
</tr>
<tr>
<td valign="top">

### 🛠️ 18+ integrated tools
- 📁 Filesystem (read / write / list / grep, sandboxed)
- 🖥️ Shell (with optional strict-whitelist mode)
- 🔍 Web search (DuckDuckGo)
- 🌐 Browser automation (browser-use)
- 📄 Documents + PDF extraction (LangExtract)
- 🎵 Media handling
- 🖱️ Desktop + macOS integration
- 📦 Package management (pip / npm / brew)
- ⏰ Cron scheduling
- 💬 Multi-agent session tools
- **🗄️ SQLite** (query / exec / schema)
- **🌍 HTTP client** (REST / GraphQL)
- **🐍 python_exec** (subprocess-isolated)
- **🔀 git_ops** (status / diff / log / commit)

</td>
<td valign="top">

### 🐝 The swarm
Two overnight modes:

- **LiveRoom** — 10 persona bots hold a real-time Discord conversation, select an idea each round, and **actually build** a project folder (`BLUEPRINT.md`, `src/main.py`, tests, Dockerfiles, etc.)
- **Night Lab** — a focused 6-stage reasoning pipeline (Seed → Scout → Analyst → Blueprint → Validator → Scribe) that writes one polished **Morning Brief** per cycle

Optional daily 09:00 sync pass using the FIRE scoring framework.

</td>
</tr>
<tr>
<td valign="top">

### 🔒 Security & sandbox
- 🛡️ Workspace sandbox (`~/.wingman/workspace/`)
- 🚫 Dangerous-command blocklist (`rm -rf /`, `:(){:|:&};:`, …)
- ✅ Optional strict shell whitelist
- 🔐 Per-tool boundary checks (git, sqlite, python_exec, shell, filesystem)
- 📝 JSONL audit log of every tool call
- ⚡ Token-bucket + sliding-window rate limiting per provider

</td>
<td valign="top">

### 🧠 Memory + RAG
- 🧾 Every turn stored in an append-only JSONL transcript
- 🧬 On-disk vector store with cosine similarity (no external DB)
- 📥 Ingest PDFs, Markdown, plain text via the `ingest_document` tool
- 🪄 **Auto-RAG** — top-k snippets auto-injected into every prompt when `agents.rag.auto_retrieve` is on
- 🔁 Atomic tmp-file writes so a crash mid-write can't corrupt the store

</td>
</tr>
</table>

---

## 🏗️ Architecture

Wingman has **three orthogonal axes**. New contributors tend to conflate them — keep them separate when reasoning about changes.

### The request path

```
                 ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
 inbound ────▶   │  WebChat  │ │    CLI    │ │ Telegram  │ │  Discord  │ │   Slack   │ │ WhatsApp  │
                 │    🌐     │ │    💻     │ │    💬     │ │    🎮     │ │    💼     │ │    📞     │
                 └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
                       │             │             │             │             │             │
                       └─────────────┴─────────────┼─────────────┴─────────────┴─────────────┘
                                                   │
                                         ┌─────────┴─────────┐
                                         │  🌐  Gateway      │  FastAPI · 127.0.0.1:18789
                                         │  /api  /ws  /ui   │  REST + WebSocket + WebChat UI
                                         └─────────┬─────────┘
                                                   │
                                         ┌─────────┴─────────┐
                                         │  🎯  Agent loop   │  src/agent/loop.py
                                         │  LLM ⇄ tools      │  (system prompt + optional RAG)
                                         └─────────┬─────────┘
                                                   │
                            ┌──────────────────────┼──────────────────────┐
                            │                      │                      │
                   ┌────────┴────────┐   ┌─────────┴─────────┐   ┌────────┴────────┐
                   │ 🛠️  Tool registry│   │  🔌 Providers    │   │ 🧠 Memory/RAG   │
                   │  (18+ tools)    │   │  Round-robin +   │   │ Vector store +  │
                   │  all sandboxed  │   │  circuit breaker │   │ transcripts     │
                   └────────┬────────┘   └─────────┬─────────┘   └─────────────────┘
                            │                      │
         ┌──────────────────┼──────────────────┐   │
         │ filesystem · shell · web_search     │   │     ┌──────────┬──────────┬──────────┐
         │ browser · documents · sqlite_ops    │   └────▶│  OpenAI  │   Groq   │   Kimi   │
         │ http_client · python_exec · git_ops │         │ Gemini   │  Ollama  │OpenRouter│
         │ cron · sessions · macos · media     │         └──────────┴──────────┴──────────┘
         └─────────────────────────────────────┘            All share one httpx client
```

### The three axes

<table>
<tr><th>Axis</th><th>What it is</th><th>Where it lives</th></tr>
<tr>
<td><strong>1. Request path</strong></td>
<td>Channel → Gateway → Agent loop → Tools / LLM. Every user message flows through this path regardless of where it came from.</td>
<td>
<code>src/channels/</code><br/>
<code>src/gateway/</code><br/>
<code>src/agent/</code><br/>
<code>src/tools/</code><br/>
<code>src/providers/</code>
</td>
</tr>
<tr>
<td><strong>2. Swarm</strong></td>
<td>Multi-agent orchestration <em>on top of</em> the agent primitives. LiveRoom runs 10 Discord bots in a real-time conversation; Night Lab runs a focused reasoning pipeline. Both write artifacts into the workspace.</td>
<td>
<code>src/swarm/live_room.py</code><br/>
<code>src/swarm/night_lab.py</code><br/>
<code>src/swarm/bots.py</code><br/>
<code>src/swarm/manager.py</code><br/>
<code>src/swarm/sync.py</code>
</td>
</tr>
<tr>
<td><strong>3. Cross-cutting</strong></td>
<td>Infrastructure both axes depend on: config + paths, core runtime, memory / retrieval / extraction, plugins, skills.</td>
<td>
<code>src/config/</code> (incl. <code>paths.py</code>)<br/>
<code>src/core/</code><br/>
<code>src/memory/</code> + <code>retrieval/</code> + <code>extraction/</code><br/>
<code>src/plugins/</code> + <code>skills/</code>
</td>
</tr>
</table>

### A single turn, in sequence

```
 user typed           │                                                  │
─────▶ "search for X" │                                                  │
                      ▼                                                  │
              ┌──────────────┐         build system prompt               │
              │ AgentSession │────────────────────────────────┐          │
              └──────┬───────┘                                ▼          │
                     │                            ┌──────────────────┐   │
                     │          (optional)        │ PromptBuilder    │   │
                     ▼                            └──────────────────┘   │
              ┌──────────────┐   search(top-k)   ┌──────────────────┐   │
              │ maybe inject │──────────────────▶│  Vector store    │   │
              │  RAG context │◀──────────────────│  ~/.wingman/vs   │   │
              └──────┬───────┘     snippets      └──────────────────┘   │
                     │                                                   │
                     ▼                                                   │
              ┌──────────────┐      tool defs    ┌──────────────────┐   │
              │ provider.chat│◀──────────────────│  ToolRegistry    │   │
              └──────┬───────┘                   └──────────────────┘   │
                     │                                                   │
           ┌─────────┴─────────┐                                         │
           │ has_tool_calls?   │                                         │
           └─────────┬─────────┘                                         │
            yes    ◀─┤ ┌──────────────────┐                              │
                     ▼ │ registry.execute │── read/write/shell/http/... │
              ┌──────────────┐◀─┘                                        │
              │ append result│   loop until no more tool calls           │
              └──────┬───────┘   or max_tool_iterations hit              │
            no       │                                                   │
                     ▼                                                   │
              ┌──────────────┐    back up through channel,               ▼
              │ final reply  │────────── rendered to the user ──────▶ user sees it
              └──────────────┘
```

---

## 🔌 LLM providers

Six providers ship. Any combination works — Wingman round-robins across whatever is configured and falls back on failure.

| Provider | Free tier | Default model | Notes | Env var |
| -------- | :-------: | ------------- | ----- | ------- |
| **OpenAI** | ❌ | `gpt-4o` | Flagship reasoning | `OPENAI_API_KEY` |
| **OpenAI (cheap)** | ❌ | `gpt-4o-mini` | Same key, cost-effective tier | `OPENAI_API_KEY` |
| **Groq** | ✅ | `llama-3.3-70b-versatile` | Fastest tokens/sec | `GROQ_API_KEY` |
| **Kimi** | ✅ | `kimi-k2.5` | 2M-token context | `KIMI_API_KEY` |
| **Gemini** | ✅ | `gemini-2.5-flash` | Google AI Studio | `GEMINI_API_KEY` |
| **Ollama** | ✅ | `kimi-k2.5:cloud` | Fully local, no key | `OLLAMA_API_BASE` |
| **OpenRouter** | 💰 | any | Claude / Llama / Mistral / 100+ | `OPENROUTER_API_KEY` |

### How providers work internally

```
                            ┌─────────────────────────┐
                            │    ProviderManager      │
                            │  round-robin + retry    │
                            └───────────┬─────────────┘
                                        │
       ┌────────────────────────────────┼──────────────────────────────┐
       │                                │                              │
 ┌─────▼────────┐                 ┌─────▼────────┐              ┌──────▼───────┐
 │   OpenAI     │                 │    Groq      │              │   Ollama     │
 │   ┌───────┐  │                 │   ┌───────┐  │              │   ┌───────┐  │
 │   │OpenAI │  │                 │   │OpenAI │  │              │   │  own  │  │
 │   │ compat│  │                 │   │ compat│  │              │   │ impl  │  │
 │   │ base  │  │                 │   │ base  │  │              │   └───────┘  │
 │   └───┬───┘  │                 │   └───┬───┘  │              └──────┬───────┘
 └───────┼──────┘                 └───────┼──────┘                     │
         │                                │                            │
         └────────────────┬───────────────┘                            │
                          │                                            │
                  ┌───────▼────────────────────────────────────────────▼┐
                  │              shared httpx AsyncClient                │
                  │   50 conns · 20 keepalive · 120s timeout · 10s cxn   │
                  └──────────────────────────────────────────────────────┘
```

Any provider speaking the OpenAI `/chat/completions` protocol (OpenAI, Groq, OpenRouter, Kimi, …) subclasses `OpenAICompatibleProvider` and sets three fields: `api_base`, `default_model`, `_provider_name`. Adding a new OpenAI-compatible provider is **~12 lines of code**.

### Failure behavior

- **Per-call retry** — configurable; exponential backoff
- **Circuit breaker** — 3 consecutive failures → provider skipped for a cooldown window
- **Fallback priority** — default provider first, then `kimi → gemini → ollama → openai → openai_chat → groq → openrouter`
- **Health check** — `make doctor` / `python -m src.main doctor` fans out to every configured provider in parallel

---

## 🛠️ Tools

The agent is a tool-using loop, not a plain chatbot. Every tool is registered in [src/tools/registry.py](src/tools/registry.py) and enforces its own security boundary.

### Tool inventory

| Category | Tool | What it does | Sandbox |
| -------- | ---- | ------------ | ------- |
| **Filesystem** | `read_file` · `write_file` · `list_dir` · `grep` · `find` | Read/write/list files, content & name search | Workspace |
| **Shell** | `shell_exec` | Run arbitrary shell commands | Blocklist + optional strict whitelist |
| **Web** | `web_search` · `web_fetch` | DuckDuckGo search + GET pages | — |
| **Browser** | `browser_open` · `browser_click` · `browser_type` · `browser_read` | Full browser automation via browser-use | — |
| **Documents** | `ingest_document` · `search_knowledge_base` | PDF / MD / text → vector store | Workspace |
| **Dev** | `git_ops` | status / diff / log / branch / show / commit (network + history-rewrite blocked) | Workspace repo |
| **Dev** | `http_client` | REST + GraphQL; any HTTP method | — |
| **Dev** | `sqlite_query` · `sqlite_exec` · `sqlite_schema` | SELECT + writes + schema introspection | Workspace DB files |
| **Dev** | `python_exec` | `python -c` in a subprocess with hard timeout | Subprocess · 300s max |
| **Platform** | `macos_*` · `desktop_*` · `media_*` · `package_*` | Native integrations | Platform-level perms |
| **Cron** | `cron_create` · `cron_list` · `cron_delete` | Schedule jobs | Workspace |
| **Sessions** | `session_*` | Multi-agent session handoff | Workspace |
| **Extraction** | `extract_structured` | LangExtract for structured data | Workspace |

### Workspace sandbox

All filesystem / shell / git / sqlite / python_exec tools resolve paths against `~/.wingman/workspace/` (configurable via `WINGMAN_WORKSPACE`). A path traversal attempt returns an error rather than escaping.

```
~/.wingman/workspace/              ← sandbox root
├── project-a/                     ← tool writes land here
├── notes/
│   └── today.md                   ← write_file OK
└── (anywhere else)                ← read_file "../etc/passwd" ❌
```

---

## 📡 Channels

One gateway router, many channels. Each channel extends [src/channels/base.py](src/channels/base.py).

| Channel | Transport | Enable in config | Auth |
| ------- | --------- | ---------------- | ---- |
| 🌐 **WebChat** | Browser (WS + REST) | `channels.webchat.enabled` | same-origin |
| 💻 **CLI** | Terminal | n/a (default) | local |
| 💬 **Telegram** | Long-polling | `channels.telegram.enabled` | bot token |
| 🎮 **Discord** | Gateway (WS) | `channels.discord.enabled` | bot token |
| 💼 **Slack** | Socket Mode | `channels.slack.enabled` | bot + app token |
| 📞 **WhatsApp** | Twilio webhook | `channels.whatsapp.enabled` | Twilio creds |

Each channel supports a per-channel `allow_from` list to restrict who can message the bot.

---

## 🐝 The swarm

Wingman ships two independent overnight modes. Pick whichever matches the kind of output you want to wake up to.

```
                      ┌─────────────────────────────────────┐
                      │   python run_overnight.py <FLAGS>   │
                      └─────────────────┬───────────────────┘
                                        │
              ┌─────────────────────────┴─────────────────────────┐
              │                                                   │
              ▼ (default)                                         ▼ (--brief)
      ┌───────────────┐                                  ┌───────────────┐
      │   LiveRoom    │                                  │   Night Lab   │
      │ 10 persona    │                                  │  single LLM   │
      │ Discord bots  │                                  │  6-stage pipe │
      │ talking + building │                             │ one brief/cycle│
      └───────┬───────┘                                  └───────┬───────┘
              │                                                   │
              ▼                                                   ▼
   ~/.wingman/workspace/liveroom/              ~/.wingman/briefs/<date>.md
     <date>-<slug>/
       BLUEPRINT.md
       src/main.py
       TEST_PLAN.md
       ...
```

### LiveRoom — overnight build sessions

Ten persona bots hold a real-time conversation in a Discord channel. Every round picks a topic, crystallizes it into a concrete buildable idea, and **actually writes files** for you to review in the morning.

```
 ┌────────┐  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────┐
 │ open   │─▶│ discuss  │─▶│  crystallize │─▶│    build     │─▶│ close  │
 │ Chief  │  │ 3 turns  │  │  moderator   │  │ alternating  │  │ Chief  │
 │ seeds  │  │ in-persona│ │  picks idea  │  │ build + react│  │ lists  │
 │ topic  │  │ chatter  │  │  scaffolds   │  │ write_file   │  │ files  │
 │        │  │          │  │  project dir │  │ forced       │  │ created│
 └────────┘  └──────────┘  └──────────────┘  └──────────────┘  └────────┘
                                  │
                                  ▼
                     ~/.wingman/workspace/liveroom/
                       2026-04-20-federated-rag/
                       ├── README.md              (seed)
                       ├── BLUEPRINT.md           (Blueprint bot wrote this)
                       ├── src/main.py            (Builder wrote this)
                       ├── TEST_PLAN.md           (Validator)
                       ├── tests/test_smoke.py
                       ├── Dockerfile             (Deploy)
                       ├── USAGE.md               (Scribe)
                       ├── NOTES.md               (Scout)
                       └── PITCH.md               (Spark)
```

**Run it**:

```bash
python run_overnight.py                  # rounds forever, 12 turns each, 15-min rest
python run_overnight.py --once           # one round and exit
python run_overnight.py --turns 8 --rest 10
```

**What you get in the morning**: a folder per round. Even when the idea is weak, the folder always contains at least a blueprint — something you can skim, judge, and either discard or take over. The whole point is **producing evaluable artifacts**, not just transcripts.

### Night Lab — overnight reasoning pipeline

A single provider runs a focused six-stage reasoning pipeline. No Discord, no persona bickering, no lifecycle management — just one polished Morning Brief per cycle.

```
  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌───────────┐   ┌───────────┐   ┌─────────┐
  │  Seed   │──▶│  Scout  │──▶│ Analyst │──▶│ Blueprint │──▶│ Validator │──▶│ Scribe  │
  │ sharpen │   │  web    │   │  FIRE   │   │  sketch   │   │ red-team  │   │ compose │
  │ theme + │   │ search  │   │ score   │   │   arch    │   │ critique  │   │ ≤600-wd │
  │ question│   │ signals │   │ 1–10 ×4 │   │           │   │           │   │  brief  │
  └─────────┘   └─────────┘   └─────────┘   └───────────┘   └───────────┘   └────┬────┘
                                                                                 │
                                                                                 ▼
                                                      ~/.wingman/briefs/2026-04-21.md
```

**FIRE scoring**: each candidate idea scored 1–10 on **F**easibility, **I**mpact, **R**isk, **E**ffort — composite = `(F + I − R − E) / 2`.

**Run it**:

```bash
python run_overnight.py --brief                          # every 60 min forever
python run_overnight.py --brief --once                   # one cycle
python run_overnight.py --brief --theme "Edge inference" # force a theme
```

**What you get in the morning**: a single Markdown file at `~/.wingman/briefs/<date>.md` with **The Question**, **The Angle**, **Blueprint at a Glance**, **Risks Worth Naming**, **Do This First**, plus collapsible sections for raw Scout / Analyst / Blueprint / Validator output. Readable in under 3 minutes.

### Meet the team

The 10 personas (same roster in LiveRoom; Night Lab uses them as prompt personas for each stage):

| Bot | Role | Persona | Specialty |
| --- | ---- | ------- | --------- |
| 🧠 **Chief** | Engineering Manager | Ex-Spotify / Airbnb | Runs syncs, makes calls, assigns tasks |
| 📡 **Pulse** | News Hunter | Ex-TechCrunch | Breaking AI news with sources |
| 🔬 **Scout** | Researcher | PhD ML (ex-Google Brain) | Papers, repos, implementations |
| 💡 **Spark** | Innovator | Ex-founder, 3 exits | Wild ideas, opportunities |
| 🏗️ **Blueprint** | Architect | 20 YOE (ex-AWS / Netflix) | System design + diagrams |
| 💻 **Builder** | Tech Lead | 15 YOE (ex-Stripe / Meta) | Production code, prototypes |
| 🧪 **Validator** | QA Lead | SDET (ex-Microsoft) | Tests, bugs, security |
| 🚀 **Deploy** | SRE | 12 YOE (ex-Google SRE) | CI/CD, Docker, infra |
| 📊 **Analyst** | Strategist | Data Scientist + MBA | FIRE scoring, metrics |
| 📝 **Scribe** | Writer | Dev Advocate | Docs, summaries, pitches |

Each bot in LiveRoom has its own Discord identity (token), speaks in-character, and has a full `AgentSession` with tool access — so a bot that says "I'll write the test plan" can actually call `write_file` to produce `TEST_PLAN.md`.

### Shared memory layout

LiveRoom writes to **per-round project folders**; Night Lab writes to dated brief files. Older workflow state (pre-LiveRoom) still lives under `~/.wingman/swarm/`:

```
~/.wingman/
├── 📄 config.json                    # your config (gitignored)
├── 📁 workspace/
│   ├── liveroom/
│   │   ├── 2026-04-20-federated-rag/
│   │   └── 2026-04-21-edge-inference/
│   └── (your own files / tool output)
├── 📝 briefs/
│   └── 2026-04-21.md                 # Night Lab output
├── 🐝 swarm/
│   ├── trends/                       # older per-role shared state
│   ├── research/
│   ├── projects/
│   ├── tests/
│   ├── devops/
│   ├── docs/
│   ├── decisions/
│   └── syncs/                        # daily 09:00 sync summaries
├── 🧬 vector_store/                  # on-disk embeddings
├── 💬 sessions/                      # JSONL transcripts per session
├── ⚡ skills/                        # user-installed skills
└── 📜 logs/                          # 10MB-rotated JSONL
```

---

## 🧠 Memory & RAG

Wingman remembers everything and optionally feeds prior context back into every prompt.

### The three layers

```
 ┌─────────────────────────────────────────────────────────────────┐
 │  Short-term — the current session's messages                    │
 │  (in memory, appended to every LLM call)                        │
 └─────────────────────────────────────────────────────────────────┘
              ▲
              │
 ┌─────────────────────────────────────────────────────────────────┐
 │  Transcript — append-only JSONL at ~/.wingman/sessions/<id>.jsonl│
 │  Logged: user messages, assistant replies, tool calls + results │
 └─────────────────────────────────────────────────────────────────┘
              ▲
              │
 ┌─────────────────────────────────────────────────────────────────┐
 │  Vector store — embeddings + cosine similarity search           │
 │  JSON-file backed, atomic tmp-file writes, scored retrieval     │
 └─────────────────────────────────────────────────────────────────┘
```

### Auto-RAG

When `agents.rag.auto_retrieve` is true, every user message is embedded and top-k hits (score ≥ `min_score`) are injected as a system message right after the main system prompt:

```python
# src/agent/loop.py
rag_msg = self._maybe_build_rag_message(user_input)
if rag_msg is not None:
    full_messages.insert(1, rag_msg)   # top of stack after system prompt
```

Empty store, no passing hits, or retrieval error → silent fall-through to the non-RAG path. Zero config by default (`top_k=3`, `min_score=0.3`).

### Ingesting documents

```bash
# Via CLI
wingman agent --interactive
> Please ingest ~/Downloads/paper.pdf

# Or directly
python -c "
import asyncio
from src.tools.documents import ingest_document
asyncio.run(ingest_document('~/Downloads/paper.pdf'))"
```

Supported formats: PDF, Markdown, plain text, HTML (via LangExtract for structured extraction).

---

## 🔒 Security model

Wingman is designed for a single trusted operator (you) running on your machine. Still, every tool enforces boundaries so prompt-injected or confused-LLM behavior can't escape.

| Layer | Mechanism | File |
| ----- | --------- | ---- |
| **Workspace sandbox** | All filesystem / shell / git / sqlite / python_exec paths resolve against `~/.wingman/workspace/`. Traversal returns an error. | [src/security/](src/security/), each tool's `_resolve_*` helper |
| **Command blocklist** | Patterns like `rm -rf /`, `chmod 777`, `curl \| sh`, `:(){:\|:&};:` always blocked. | [src/tools/shell.py](src/tools/shell.py) |
| **Strict whitelist (opt-in)** | When `tools.shell.strict_whitelist=true`, only commands whose first word is in `allowed_commands` run. | `settings.tools.shell` |
| **Git boundary** | `git_ops` blocks network subcommands (`push/fetch/pull/clone/remote`) and history rewrites (`reset/rebase/filter-branch/--force/--hard/-D`). | [src/tools/git_ops.py](src/tools/git_ops.py) |
| **Python subprocess isolation** | `python_exec` spawns fresh subprocesses in the workspace with a hard timeout (default 30s, cap 300s). Not a REPL. | [src/tools/python_exec.py](src/tools/python_exec.py) |
| **Rate limiting** | Token-bucket + sliding-window per provider. Prevents one runaway session from burning a quota. | [src/core/rate_limiter.py](src/core/rate_limiter.py) |
| **Audit log** | Every tool call + result logged to JSONL with timestamps; 10MB rotated. | [src/core/logging.py](src/core/logging.py) |
| **Secrets hygiene** | `.env` is gitignored. Keys come from env vars and `config.json`; never baked into source. | [src/config/settings.py](src/config/settings.py) |

If a secret lands in a transcript or log, **treat it as burned and rotate**. Don't try to scrub it.

---

## ⚙️ Configuration

Configuration layers, from lowest to highest priority:

```
 ┌───────────────────────────────────────────────────────────┐
 │ 1.  Pydantic defaults (hardcoded in src/config/settings.py)│
 │ 2.  ~/.wingman/config.json                                │
 │ 3.  .env (via python-dotenv, falls back to a tiny parser) │
 │ 4.  Real process env vars                                 │
 └───────────────────────────────────────────────────────────┘
                            │
                            ▼
                    merged Settings object
                    ↑ what every module reads
```

### Minimal config

```json
{
  "agents": {
    "defaults": { "model": "openai/gpt-4o-mini", "max_tokens": 8192 }
  },
  "providers": {
    "openai": { "api_key": "", "api_base": "https://api.openai.com/v1", "model": "gpt-4o" }
  }
}
```

Plus `.env`:

```dotenv
OPENAI_API_KEY=sk-proj-...
```

### Full config

<details>
<summary>📄 Click to expand — every section explained</summary>

```json
{
  "agents": {
    "defaults": {
      "workspace": "~/.wingman/workspace",
      "model": "openai/gpt-4o-mini",
      "max_tokens": 8192,
      "temperature": 0.7,
      "max_tool_iterations": 25,
      "workspace_sandboxed": true
    },
    "rag": {
      "auto_retrieve": true,
      "top_k": 3,
      "min_score": 0.3,
      "collection": "documents"
    }
  },
  "providers": {
    "openai":      { "api_key": "", "api_base": "https://api.openai.com/v1",  "model": "gpt-4o" },
    "openai_chat": { "api_key": "", "api_base": "https://api.openai.com/v1",  "model": "gpt-4o-mini" },
    "groq":        { "api_key": "", "api_base": "https://api.groq.com/openai/v1", "model": "llama-3.3-70b-versatile" },
    "kimi":        { "api_key": "", "api_base": "https://api.moonshot.cn/v1", "model": "kimi-k2.5" },
    "gemini":      { "api_key": "", "api_base": "https://generativelanguage.googleapis.com/v1beta" },
    "ollama":      { "api_base": "http://localhost:11434", "model": "kimi-k2.5:cloud" },
    "openrouter":  { "api_key": "", "api_base": "https://openrouter.ai/api/v1" }
  },
  "channels": {
    "webchat":  { "enabled": true,  "port": 8080 },
    "telegram": { "enabled": false, "token": "", "allow_from": [] },
    "discord":  { "enabled": false, "token": "", "allow_from": [] },
    "slack":    { "enabled": false, "bot_token": "", "app_token": "" },
    "whatsapp": { "enabled": false, "twilio_account_sid": "", "twilio_auth_token": "" }
  },
  "tools": {
    "web":     { "search": { "provider": "duckduckgo", "max_results": 5 } },
    "shell":   { "enabled": true, "allowed_commands": ["*"], "workspace_restricted": true, "strict_whitelist": false },
    "browser": { "enabled": true },
    "cron":    { "enabled": true }
  },
  "gateway": { "port": 18789, "host": "127.0.0.1", "cors_origins": ["http://localhost:*"] },
  "swarm": {
    "enabled": true,
    "sync_channel_id": 0,
    "sync_time": "09:00",
    "tokens": {
      "research": "", "engineer": "", "writer": "", "data": "", "coordinator": "",
      "trend_watcher": "", "architect": "", "tester": "", "devops": "", "innovator": ""
    }
  },
  "overnight": {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "cycle_minutes": 60,
    "themes": ["Open source LLM releases", "Edge inference", "Agent frameworks"]
  }
}
```

</details>

### Environment variables

Anything in `.env` or the process env wins over `config.json`.

| Env var | Overrides | Example |
| ------- | --------- | ------- |
| `OPENAI_API_KEY` | `providers.openai.api_key` (and `openai_chat`) | `sk-proj-...` |
| `GROQ_API_KEY` | `providers.groq.api_key` | `gsk_...` |
| `KIMI_API_KEY` | `providers.kimi.api_key` | `sk-...` |
| `GEMINI_API_KEY` | `providers.gemini.api_key` | `AIza...` |
| `OPENROUTER_API_KEY` | `providers.openrouter.api_key` | `sk-or-...` |
| `OLLAMA_API_BASE` | `providers.ollama.api_base` | `http://localhost:11434` |
| `WINGMAN_WORKSPACE` | `agents.defaults.workspace` | `~/.wingman/workspace` |
| `WINGMAN_WORKSPACE_SANDBOXED` | `agents.defaults.workspace_sandboxed` | `true` |
| `OVERNIGHT_PROVIDER` | `overnight.provider` | `groq` |
| `OVERNIGHT_MODEL` | `overnight.model` | `llama-3.3-70b-versatile` |
| `OVERNIGHT_CYCLE_MINUTES` | `overnight.cycle_minutes` | `60` |

---

## 📦 Installation options

```bash
# Full — every optional feature
pip install -e ".[all]"

# Individual extras
pip install -e ".[discord]"      # discord.py
pip install -e ".[slack]"        # slack_bolt
pip install -e ".[whatsapp]"     # twilio
pip install -e ".[voice]"        # Picovoice + STT + TTS
pip install -e ".[extraction]"   # LangExtract + PDF
pip install -e ".[browser]"      # browser-use + playwright
pip install -e ".[dev]"          # pytest, black, ruff, mypy
```

The base install gets you OpenAI / Groq / Gemini / Ollama / OpenRouter / Kimi + filesystem / shell / web_search / the new dev tools. Channels beyond WebChat + CLI are opt-in.

---

## 💻 CLI cheatsheet

```bash
# Main entry — delegates to src/cli/commands.py (typer)
python -m src.main <command>          # or: wingman <command>

# ── Core
wingman onboard                        # interactive setup wizard
wingman doctor                         # health check: providers, tools, config
wingman agent                          # one-shot run
wingman agent --interactive            # interactive chat

# ── Gateway
wingman gateway                        # FastAPI on 127.0.0.1:18789
wingman gateway -p 8080                # custom port

# ── Swarm (discord multi-bot)
wingman swarm start                    # start the 10-bot swarm
wingman swarm status                   # bot connection status
wingman swarm sync                     # trigger a sync pass

# ── Memory
wingman memory list
wingman memory search "federated RAG"

# ── Makefile shortcuts
make agent                             # = wingman agent --interactive
make gateway                           # = wingman gateway
make doctor                            # = wingman doctor
make onboard                           # = wingman onboard
make test                              # pytest
```

---

## 💬 Discord slash commands

When a bot connects, it registers its own slash commands:

| Bot | Commands |
| --- | -------- |
| 📡 **Pulse** | `/trends`, `/digest` |
| 🔬 **Scout** | `/research [topic]` |
| 💻 **Builder** | `/build [project]` |
| 📊 **Analyst** | `/score [idea]` |
| 🏗️ **Blueprint** | `/design [system]` |
| 🧪 **Validator** | `/test [component]`, `/validate` |
| 🚀 **Deploy** | `/setup [project]`, `/deploy` |
| 💡 **Spark** | `/brainstorm`, `/innovate [problem]` |
| 🧠 **Chief** | `/sync` |
| All | `/ask [question]`, `/status` |

---

## 📁 Workspace layout

Everything Wingman persists lives under `~/.wingman/` — single source of truth, easy to back up.

```
~/.wingman/
├── config.json                       # your configuration
├── workspace/                        # sandbox root for file/shell/git tools
│   └── liveroom/<date>-<slug>/       # per-round LiveRoom projects
├── briefs/<date>.md                  # Night Lab Morning Briefs
├── sessions/<session-id>.jsonl       # per-session transcripts
├── swarm/                            # older swarm shared state
├── vector_store/                     # document embeddings
├── skills/<skill>/manifest.json      # user-installed skills
├── logs/wingman.jsonl                # rotated audit log
└── extensions/                       # plugin modules
```

All paths are produced by [src/config/paths.py](src/config/paths.py) — single source of truth. Don't reconstruct `Path.home() / ".wingman" / ...` ad hoc; import from there.

---

## 🧪 Development

```bash
# Setup
pip install -e ".[dev]"

# Run the suite (pytest-asyncio auto-mode — no decorator needed)
pytest
pytest -k test_session_creation           # single test
pytest --cov=src --cov-report=html        # with coverage

# Lint + format + typecheck (line-length 100, py311 target)
ruff check src/ tests/ --fix
black src/ tests/
mypy src/

# Integration scripts (manual, need services running)
python tests/integration/test_documents.py
python tests/integration/test_langextract.py
python tests/integration/reproduce_issue.py
```

### Conventions

- **Conventional Commits** — `feat(scope):`, `fix(scope):`, `docs:`, `chore:`, `refactor:` (see [CONTRIBUTING.md](CONTRIBUTING.md))
- **Async everywhere** — I/O is `async def`; pytest-asyncio is in auto-mode
- **Line length 100** — enforced by black and ruff
- **Small focused commits** — easier to review and revert

---

## 🚑 Troubleshooting

<details>
<summary><strong>Bots start but nothing appears in Discord</strong></summary>

Cache miss on `self._bot.get_channel(channel_id)` — fixed in the latest version via a `fetch_channel` REST fallback with explicit success/failure logging. Grep the log for `send_to_channel:` lines. If you see `could not access channel <id>`, the bot doesn't have permission on that channel — re-invite it with the right scopes.

</details>

<details>
<summary><strong>OpenAI returns 400: "Invalid schema for function 'sqlite_query': array must contain items"</strong></summary>

Fixed in [src/tools/sqlite_ops.py](src/tools/sqlite_ops.py) — the `params` array schema now declares `items`. Pull the latest and restart.

</details>

<details>
<summary><strong>Overnight run produces chat but no files</strong></summary>

Make sure you're on a recent LiveRoom build. The crystallize phase announces a project folder early each round; if you don't see lines like `=== Round N — <topic> ===` and `Chief posted <chars> chars to <id>` followed by folder creation, the build phase won't fire. `run_overnight.py` without `--brief` is LiveRoom; with `--brief` you'll get Morning Briefs, not folders.

</details>

<details>
<summary><strong>"No providers configured" error</strong></summary>

Wingman needs at least one of: `OPENAI_API_KEY`, `GROQ_API_KEY`, `GEMINI_API_KEY`, `KIMI_API_KEY`, `OPENROUTER_API_KEY`, or a running Ollama at `OLLAMA_API_BASE`. Put one in `.env` and run `make doctor` to verify.

</details>

<details>
<summary><strong>Rate limited / circuit breaker tripped</strong></summary>

`src/core/rate_limiter.py` uses token-bucket + sliding-window per provider; the circuit breaker trips after 3 consecutive failures. Check the log (`~/.wingman/logs/`) for which provider's upset, wait the cooldown, or swap the default provider in config to a healthier one.

</details>

<details>
<summary><strong>Workspace-sandbox errors for paths you think should be allowed</strong></summary>

Paths are resolved (`os.path.expanduser` + `Path.resolve()`) and then checked against `~/.wingman/workspace/`. Symlinks that cross the boundary count as "outside." Either move the target inside the workspace or set `WINGMAN_WORKSPACE_SANDBOXED=false` for a local trial (not recommended in production).

</details>

<details>
<summary><strong>Vector store corruption</strong></summary>

The store writes via `<path>.tmp` then atomic rename, so a crash mid-write leaves the prior JSON intact. If you do end up with a truncated file, just delete the affected collection under `~/.wingman/vector_store/` — it rebuilds on next ingest.

</details>

---

## 🗺️ Repo layout

```
wingman/
├── src/
│   ├── agent/           # agent loop, prompt builder
│   ├── channels/        # webchat, cli, discord, telegram, slack, whatsapp
│   ├── config/          # settings.py + paths.py
│   ├── core/            # session, runtime, rate_limiter, health, logging
│   ├── gateway/         # FastAPI server, REST + WS + WebChat UI
│   ├── memory/          # transcripts, memory manager
│   ├── retrieval/       # vector store, embedding, search
│   ├── extraction/      # LangExtract-based structured extraction
│   ├── providers/       # openai, groq, kimi, gemini, ollama, openrouter + _http, _openai_compat
│   ├── security/        # workspace sandbox, blocklists, audit helpers
│   ├── swarm/           # bots, personalities, manager, live_room, night_lab, sync
│   ├── tools/           # all registered tools
│   ├── plugins/         # hot-reload plugin loader
│   ├── skills/          # user skills framework
│   └── main.py          # CLI entry point (typer)
├── tests/
│   ├── test_core.py
│   └── integration/     # manual scripts that need a running gateway
├── docs/                # architecture PDF + implementation notes
├── examples/            # small end-to-end scripts
├── run_overnight.py     # LiveRoom / Night Lab launcher
├── run_swarm.py         # basic 10-bot swarm (no LiveRoom)
├── Makefile
├── Dockerfile + docker-compose.yml
├── config.example.json
├── .env.example
├── CLAUDE.md            # session guide for Claude Code
└── CONTRIBUTING.md
```

---

## 🤝 Contributing

Contributions welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full contributor guide; the short version:

1. Fork → branch (`feat/thing` or `fix/thing`)
2. Write the change + tests
3. `black src/ tests/ && ruff check src/ tests/ && mypy src/ && pytest`
4. Commit with a Conventional Commits message
5. Open a PR — include a short description of *why* along with *what*

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

<p align="center">
  <sub>Built by <a href="https://github.com/siddharthprakash1">@siddharthprakash1</a> · <a href="https://github.com/siddharthprakash1/wingman/issues">Report a bug</a> · <a href="https://github.com/siddharthprakash1/wingman/issues">Request a feature</a></sub>
</p>
