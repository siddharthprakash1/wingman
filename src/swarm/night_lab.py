"""
Night Lab — overnight idea pipeline.

Instead of ten Discord bots small-talking into the void, Night Lab runs a
focused multi-stage reasoning pipeline on a rotating theme. Each cycle
produces one polished Morning Brief appended to ~/.wingman/briefs/<date>.md.

Pipeline (each stage is a single provider.chat() call):

    Seed       → pick theme + sharpen the question
    Scout      → web_search for recent signals (news / papers / releases)
    Analyst    → FIRE-score (Feasibility / Impact / Risk / Effort)
    Blueprint  → sketch architecture for the top idea
    Validator  → red-team critique
    Scribe     → synthesize into a ≤600 word Morning Brief

The whole thing runs on one provider (default: openai / gpt-4o-mini) — no
Discord dependency, no bot lifecycles, no shared-state gymnastics.

Provider is swappable via `settings.overnight.provider` ("openai", "groq",
"kimi", …) — whatever is registered in ProviderManager.
"""

from __future__ import annotations

import asyncio
import logging
import random
import signal
from datetime import date, datetime
from pathlib import Path

from src.config.paths import brief_path, ensure_dirs
from src.config.settings import Settings, get_settings
from src.providers.base import LLMProvider, Message
from src.providers.manager import ProviderManager

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Stage prompts — each is a focused persona, not a bot
# ---------------------------------------------------------------------------

SEED_PROMPT = """You are the Chief, setting direction for a late-night research sprint.

Theme: {theme}

Sharpen this theme into ONE specific question worth ~90 minutes of research.
The question should be:
- concrete (not "what's the future of X?")
- actionable (research should produce a buildable answer)
- grounded in a real current gap or opportunity

Return JUST the question — a single sentence, no preamble."""


SCOUT_PROMPT = """You are the Scout. Given these web-search results, extract
the 3-5 most promising signals.

Question: {question}

Search results:
{search_results}

For each signal, write one tight paragraph:
- what happened / what exists
- why it matters for the question
- where it points

No filler. No "here are the signals:" intros. Just the numbered signals."""


ANALYST_PROMPT = """You are the Analyst. Given the Scout's signals, pick the
single most promising angle and FIRE-score it.

Question: {question}

Scout's signals:
{signals}

Return exactly this shape:

**Angle:** one sentence describing the specific project/idea

**FIRE Score** (1-10 each):
- Feasibility: N — one-line reason
- Impact: N — one-line reason
- Risk: N — one-line reason
- Effort: N — one-line reason
**Composite:** (F + I - R - E) / 2

**Why this one:** 2-3 sentences on why this angle beats the alternatives."""


BLUEPRINT_PROMPT = """You are the Blueprint architect. Given the Analyst's
chosen angle, sketch a minimal buildable system.

Angle: {angle}

Return:

**What it is:** 1 sentence.
**Core components:** bullet list, ≤5 items, each one line.
**Data flow:** numbered steps, ≤6 steps.
**First milestone:** what does "v0.1 works" look like — 1-2 sentences.
**Stack choices:** one line each, concrete (no "some LLM" or "a database").

Keep the whole thing under 250 words. Favor boring, shippable choices."""


VALIDATOR_PROMPT = """You are the Validator. Red-team the Blueprint.

Angle: {angle}
Blueprint:
{blueprint}

Return:

**Top 3 failure modes** — what breaks this in practice. One tight paragraph each.
**Silent assumptions** — what the Blueprint assumes but doesn't state. Bullet list.
**Kill criteria** — what would make us abandon this? One sentence.

Be sharp. No hedging."""


SCRIBE_PROMPT = """You are the Scribe. Synthesize tonight's work into a
Morning Brief — the first thing a founder reads with coffee.

Inputs:
- Question: {question}
- Angle: {angle}
- Blueprint: {blueprint}
- Validator critique: {critique}

Write a Morning Brief (≤600 words) in this exact structure:

# {date} — {theme}

## The Question
One paragraph.

## The Angle
One paragraph — lead with the idea, then why now.

## Blueprint at a Glance
Compressed: components + data flow in ≤8 lines total.

## Risks Worth Naming
Bullet list, ≤4 items, one line each.

## Do This First
One concrete action the reader can take in the next 2 hours if they want to explore further.

---

Tone: confident but not hyped. No emojis. No "overall" / "in conclusion"
padding. The reader is smart and time-poor."""


# ---------------------------------------------------------------------------
# Provider helper
# ---------------------------------------------------------------------------

def _resolve_provider(settings: Settings, manager: ProviderManager) -> LLMProvider:
    """
    Build a dedicated provider instance scoped to settings.overnight — so the
    Night Lab uses its own (usually cheaper) model without disturbing the
    shared provider pool the agent CLI/gateway use.
    """
    name = settings.overnight.provider
    model = settings.overnight.model
    cfg = settings.providers

    try:
        if name == "openai" and cfg.openai.api_key:
            from src.providers.openai import OpenAIProvider
            return OpenAIProvider(api_key=cfg.openai.api_key, api_base=cfg.openai.api_base, model=model)
        if name == "openai_chat" and cfg.openai_chat.api_key:
            from src.providers.openai import OpenAIProvider
            return OpenAIProvider(api_key=cfg.openai_chat.api_key, api_base=cfg.openai_chat.api_base, model=model)
        if name == "groq" and cfg.groq.api_key:
            from src.providers.groq import GroqProvider
            return GroqProvider(api_key=cfg.groq.api_key, api_base=cfg.groq.api_base, model=model)
        if name == "kimi" and cfg.kimi.api_key:
            from src.providers.kimi import KimiProvider
            return KimiProvider(api_key=cfg.kimi.api_key, api_base=cfg.kimi.api_base, model=model)
        if name == "openrouter" and cfg.openrouter.api_key:
            from src.providers.openrouter import OpenRouterProvider
            return OpenRouterProvider(api_key=cfg.openrouter.api_key, api_base=cfg.openrouter.api_base, model=model)
        if name == "ollama":
            from src.providers.ollama import OllamaProvider
            return OllamaProvider(api_base=cfg.ollama.api_base, model=model or cfg.ollama.model)
    except Exception as e:
        logger.warning(f"Night Lab provider init for '{name}' failed: {e}")

    # Fallback: reuse whatever the manager decides
    logger.warning(
        f"Night Lab provider '{name}' unavailable — falling back to manager default"
    )
    return manager.get_provider()


async def _chat(
    provider: LLMProvider,
    system: str,
    user: str,
    max_tokens: int,
) -> str:
    """One-shot text completion — no tools, no streaming."""
    messages = [
        Message(role="system", content=system),
        Message(role="user", content=user),
    ]
    resp = await provider.chat(
        messages=messages,
        tools=None,
        temperature=0.7,
        max_tokens=max_tokens,
    )
    return (resp.content or "").strip()


# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------

async def _stage_seed(provider: LLMProvider, theme: str, max_tokens: int) -> str:
    system = "You are a senior research lead. Be precise and brief."
    return await _chat(provider, system, SEED_PROMPT.format(theme=theme), max_tokens)


async def _stage_scout(
    provider: LLMProvider,
    question: str,
    max_tokens: int,
) -> tuple[str, str]:
    """Run web_search, then ask Scout to distill. Returns (raw_search, signals)."""
    from src.tools.web_search import web_search

    # Give the scout broad coverage without hammering DDG
    query = question if len(question) < 200 else question[:200]
    try:
        raw = await web_search(query=query, max_results=8)
    except Exception as e:
        logger.warning(f"web_search failed in Night Lab: {e}")
        raw = "(web_search unavailable — reason from first-principles)"

    signals = await _chat(
        provider,
        "You are a sharp research analyst. No filler, no hedging.",
        SCOUT_PROMPT.format(question=question, search_results=raw[:8000]),
        max_tokens,
    )
    return raw, signals


async def _stage_analyst(
    provider: LLMProvider,
    question: str,
    signals: str,
    max_tokens: int,
) -> str:
    return await _chat(
        provider,
        "You are a disciplined analyst. Show your scoring logic in one-liners.",
        ANALYST_PROMPT.format(question=question, signals=signals),
        max_tokens,
    )


async def _stage_blueprint(provider: LLMProvider, angle: str, max_tokens: int) -> str:
    return await _chat(
        provider,
        "You are a pragmatic systems architect. Favor boring, shippable choices.",
        BLUEPRINT_PROMPT.format(angle=angle),
        max_tokens,
    )


async def _stage_validator(
    provider: LLMProvider,
    angle: str,
    blueprint: str,
    max_tokens: int,
) -> str:
    return await _chat(
        provider,
        "You are a skeptical red-teamer. No hedging.",
        VALIDATOR_PROMPT.format(angle=angle, blueprint=blueprint),
        max_tokens,
    )


async def _stage_scribe(
    provider: LLMProvider,
    theme: str,
    question: str,
    angle: str,
    blueprint: str,
    critique: str,
    max_tokens: int,
) -> str:
    today = date.today().isoformat()
    return await _chat(
        provider,
        "You are a clean, confident writer. No emojis. No padding.",
        SCRIBE_PROMPT.format(
            date=today,
            theme=theme,
            question=question,
            angle=angle,
            blueprint=blueprint,
            critique=critique,
        ),
        max_tokens,
    )


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

def _extract_angle(analyst_output: str) -> str:
    """Pull the `**Angle:**` line out of the Analyst's FIRE scoring."""
    for line in analyst_output.splitlines():
        s = line.strip()
        if s.lower().startswith("**angle:**"):
            return s.split(":", 1)[1].strip(" *")
    # fallback: first non-empty line
    for line in analyst_output.splitlines():
        s = line.strip()
        if s:
            return s[:200]
    return "(no angle extracted)"


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

class NightLab:
    """One-shot overnight pipeline: theme → Morning Brief."""

    def __init__(self, settings: Settings | None = None):
        ensure_dirs()
        self.settings = settings or get_settings()
        self.manager = ProviderManager(self.settings)
        self.provider = _resolve_provider(self.settings, self.manager)
        self._stop = asyncio.Event()
        self._cycle_count = 0

    async def run_cycle(self, theme: str | None = None) -> Path:
        """Run one full pipeline and return the path of the brief written."""
        cfg = self.settings.overnight
        mtok = cfg.max_tokens_per_stage
        theme = theme or random.choice(cfg.themes)

        self._cycle_count += 1
        logger.info(f"Night Lab cycle {self._cycle_count} — theme: {theme}")

        # 1. Seed
        question = await _stage_seed(self.provider, theme, mtok)
        logger.info(f"[seed] {question[:200]}")

        # 2. Scout
        _raw, signals = await _stage_scout(self.provider, question, mtok)

        # 3. Analyst
        analyst = await _stage_analyst(self.provider, question, signals, mtok)
        angle = _extract_angle(analyst)

        # 4. Blueprint
        blueprint = await _stage_blueprint(self.provider, angle, mtok)

        # 5. Validator
        critique = await _stage_validator(self.provider, angle, blueprint, mtok)

        # 6. Scribe
        brief = await _stage_scribe(
            self.provider, theme, question, angle, blueprint, critique, mtok
        )

        path = _append_brief(
            theme=theme,
            question=question,
            signals=signals,
            analyst=analyst,
            blueprint=blueprint,
            critique=critique,
            brief=brief,
        )
        logger.info(f"Night Lab brief appended → {path}")

        # Optional Discord broadcast
        if cfg.post_to_discord and cfg.discord_channel_id:
            await _maybe_post_to_discord(brief, cfg.discord_channel_id)

        return path

    async def run_forever(self) -> None:
        """Run cycles on a fixed interval until stop() is called."""
        cfg = self.settings.overnight
        interval = max(10, cfg.cycle_minutes) * 60

        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, self.stop)
            except NotImplementedError:
                pass  # Windows

        while not self._stop.is_set():
            try:
                await self.run_cycle()
            except Exception as e:
                logger.exception(f"Night Lab cycle failed: {e}")
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=interval)
            except asyncio.TimeoutError:
                continue

    def stop(self) -> None:
        logger.info("Night Lab stop requested")
        self._stop.set()


# ---------------------------------------------------------------------------
# Output — one markdown file per day, appended to
# ---------------------------------------------------------------------------

def _append_brief(
    *,
    theme: str,
    question: str,
    signals: str,
    analyst: str,
    blueprint: str,
    critique: str,
    brief: str,
) -> Path:
    """Append this cycle's brief to ~/.wingman/briefs/<date>.md (atomic-ish)."""
    path = brief_path()
    ts = datetime.now().strftime("%H:%M")

    section = (
        f"\n\n<!-- cycle @ {ts} · theme: {theme} -->\n\n"
        f"{brief}\n\n"
        "---\n\n"
        f"<details><summary>Scout signals ({ts})</summary>\n\n"
        f"**Question:** {question}\n\n{signals}\n\n</details>\n\n"
        f"<details><summary>Analyst scoring ({ts})</summary>\n\n{analyst}\n\n</details>\n\n"
        f"<details><summary>Blueprint ({ts})</summary>\n\n{blueprint}\n\n</details>\n\n"
        f"<details><summary>Validator critique ({ts})</summary>\n\n{critique}\n\n</details>\n\n"
    )

    if not path.exists():
        header = f"# Morning Briefs — {date.today().isoformat()}\n"
        path.write_text(header + section, encoding="utf-8")
    else:
        with path.open("a", encoding="utf-8") as f:
            f.write(section)
    return path


async def _maybe_post_to_discord(brief: str, channel_id: int) -> None:
    """Best-effort: post the brief to a Discord channel if swarm is configured."""
    try:
        from src.config.settings import get_settings
        from src.swarm.manager import SwarmConfig, SwarmManager

        settings = get_settings()
        cfg = SwarmConfig(settings)
        cfg.load_from_dict(settings.swarm.model_dump())
        mgr = SwarmManager(cfg)
        await mgr.start()
        await asyncio.sleep(5)
        chief = mgr.bots.get("coordinator")
        if chief:
            await chief.send_to_channel(channel_id, f"🌙 **Night Lab brief**\n\n{brief[:1900]}")
        await mgr.stop()
    except Exception as e:
        logger.warning(f"Discord broadcast failed: {e}")
