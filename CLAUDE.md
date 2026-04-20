# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

"Wingman" (package name `wingman`, repo dir `openclaw_mine`) — a personal AI assistant inspired by the OpenClaw/PicoClaw architecture. The two names refer to the same thing; the README and pyproject.toml use "Wingman".

Python 3.11+. Single package under `src/` with 20+ subpackages.

## Commands

Prefer the Makefile targets — they're the canonical invocations.

**Setup**
- `pip install -e .[dev]` — dev install (use `.[all]` for discord/slack/whatsapp/voice/extraction/browser extras)
- `cp config.example.json ~/.wingman/config.json && cp .env.example .env` — bootstrap config (then edit `.env` with API keys)
- `python -m src.main onboard` (or `make onboard`) — interactive setup wizard

**Run**
- `make agent` → `python -m src.main agent --interactive` — interactive CLI chat
- `make gateway` → `python -m src.main gateway` — FastAPI server on 127.0.0.1:18789 (WebChat UI + REST/WS)
- `make doctor` → `python -m src.main doctor` — system health check
- `python run_swarm.py` — start 10-bot Discord swarm
- `python run_overnight.py` — **Night Lab** overnight idea pipeline. Writes one polished Morning Brief per cycle to `~/.wingman/briefs/<date>.md`. Flags: `--once`, `--theme "X"`. Configured by `settings.overnight` (default: OpenAI / gpt-4o-mini / 60-minute cycles).

**Test / lint / typecheck**
- `pytest` — full suite (asyncio_mode=auto is preconfigured)
- `pytest tests/test_core.py::test_session_creation` — single test
- `pytest --cov=src --cov-report=html` — with coverage
- `black src/ tests/` • `ruff check src/ tests/ --fix` • `mypy src/` (line-length 100, py311 target)

## Architecture

The system has **three orthogonal axes** that new contributors conflate. Keep them separate when reasoning about changes.

**1. Channel → Gateway → Agent → Tools/LLM (the request path)**

- [src/channels/](src/channels/) — 6 channel handlers (webchat, telegram, discord, slack, whatsapp, cli) all extend `base.py`.
- [src/gateway/server.py](src/gateway/server.py) — FastAPI control plane. Serves the WebChat UI, REST endpoints (`/api/health`, `/api/config`, `/api/sessions`, `/api/tools`, `/api/swarm/*`), and WebSocket. All channels ultimately hit the gateway router.
- [src/agent/loop.py](src/agent/loop.py) — the agentic loop (LLM call → tool dispatch → iterate). `src/agent/prompt.py` builds system prompts. **RAG is auto-injected here** when `settings.agents.rag.auto_retrieve` is true: top-k hits from the vector store are inserted as a system message right after the main system prompt.
- [src/tools/registry.py](src/tools/registry.py) — tool discovery. Core tools: filesystem, shell, web_search, browser_use, documents, cron, sessions, desktop, media, macos, extraction. **Developer tools** added recently: [git_ops.py](src/tools/git_ops.py) (status/diff/log/branch/show/commit — network + history-rewriting blocked), [http_client.py](src/tools/http_client.py) (arbitrary REST + GraphQL on shared httpx client), [sqlite_ops.py](src/tools/sqlite_ops.py) (query/exec/schema on workspace-sandboxed DB files), [python_exec.py](src/tools/python_exec.py) (subprocess-isolated `python -c` with hard timeout). All file/shell tools go through [src/security/](src/security/) for workspace sandboxing and blocked-command checks.
- [src/providers/manager.py](src/providers/manager.py) — round-robin load balancer with circuit breaker (3 consecutive failures → skip) + exponential backoff. Providers: Kimi / Gemini / Ollama / OpenAI (two configs: `openai` flagship + `openai_chat` cost-effective) / **Groq** / OpenRouter. All implement `base.py`'s `LLMProvider` interface.
  - **OpenAI-compatible providers (OpenAI, Groq, OpenRouter, Kimi) share [src/providers/_openai_compat.py](src/providers/_openai_compat.py)** — a base class that handles the `/chat/completions` protocol once. Adding a new OpenAI-compatible provider is ~12 lines: subclass `OpenAICompatibleProvider` and set `_provider_name` + default `api_base`/`model`.
  - **One shared httpx AsyncClient** lives in [src/providers/_http.py](src/providers/_http.py) (50 max / 20 keepalive connections, 120s timeout) — providers that migrate to it stop duplicating connection pools.

**2. Swarm (multi-agent orchestration on top of the agent primitives)**

- [src/swarm/](src/swarm/) has two modes:
  - **Live swarm** (`run_swarm.py`): 10 specialized Discord bots — `bots.py` + `personalities.py` + `manager.py`, with `sync.py` running a daily 09:00 FIRE-framework synchronization pass.
  - **Night Lab** ([src/swarm/night_lab.py](src/swarm/night_lab.py), run by `run_overnight.py`): a single-provider reasoning pipeline — **Seed → Scout (web_search) → Analyst (FIRE) → Blueprint → Validator → Scribe** — producing one Morning Brief per cycle. No Discord dependency. Provider-swappable via `settings.overnight.provider`. This replaced the older "bots talking at each other all night" script.
- Swarm bots share state via files under `~/.wingman/swarm/` (trends/, research/, projects/, analysis/, …). Swarm code does **not** reach into agent internals; it talks to the same gateway + agent loop as any channel.

**3. Cross-cutting infrastructure (used by both axes above)**

- [src/config/](src/config/) — [settings.py](src/config/settings.py) loads `config.json` then layers `.env` via python-dotenv + `_apply_env_overrides()` (OPENAI_API_KEY, GROQ_API_KEY, KIMI_API_KEY, GEMINI_API_KEY, OPENROUTER_API_KEY, OLLAMA_API_BASE, OVERNIGHT_PROVIDER/MODEL/CYCLE_MINUTES, WINGMAN_WORKSPACE). [paths.py](src/config/paths.py) is the single source of truth for every `~/.wingman/*` subdirectory — import from there rather than rebuilding `Path.home() / ".wingman" / ...` ad hoc.
- [src/core/](src/core/) — `session.py`, `runtime.py`, `rate_limiter.py` (token-bucket + sliding-window per provider), `health.py`, `heartbeat.py`, `logging.py` (JSONL + Rich console with 10MB rotation).
- [src/memory/](src/memory/) + [src/retrieval/](src/retrieval/) + [src/extraction/](src/extraction/) — memory stores transcripts; retrieval runs embedding + cosine-similarity search over a JSON-file-backed vector store (atomic tmp-file writes, safe-serialization fallback); extraction pulls structured data from documents (LangExtract) and feeds both.
- [src/plugins/](src/plugins/) — hot-reload loader with SHA256 change detection and setup/activate/deactivate/teardown lifecycle.
- [src/skills/](src/skills/) — reusable skills with `manifest.json`, stored under `~/.wingman/skills/`.

## Working in this repo — things to know

- **Workspace sandbox**: filesystem, shell, sqlite, git, and python_exec tools are sandboxed to `~/.wingman/workspace/`. Path-traversal and blocked-command checks live in `src/security/` and in each tool's `_resolve_*` helper; don't weaken them without reason. Shell has an optional `strict_whitelist` mode (config: `tools.shell.strict_whitelist`) that restricts commands to an explicit allowlist.
- **Async everywhere**: I/O uses async/await. pytest-asyncio is auto-mode, so no `@pytest.mark.asyncio` decorator is needed.
- **Config layering**: `~/.wingman/config.json` first, `.env` overrides second. Don't hardcode paths; read from `src/config/settings.py` or `src/config/paths.py`.
- **Secrets live in `.env`, not in chat or git.** The repo's `.env` is gitignored. If a secret ends up in a transcript or log, treat it as burned and rotate.
- **Reference material, not source of truth**: `OpenClaw Architecture and Code-Level Overview.pdf`, `IMPLEMENTATION_SUMMARY.md`, `BUGS_FOUND.md` — useful context but the code has moved past several items (most of the "critical" bugs in `BUGS_FOUND.md` are fixed).
- **Commits** follow Conventional Commits per [CONTRIBUTING.md](CONTRIBUTING.md) (`feat(scope):`, `fix(scope):`, `docs:`, etc.).
