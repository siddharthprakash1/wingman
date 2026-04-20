"""
Live Room — real-time collaborative Discord conversation with personas.

Each round has four phases:
  1. Open       — Chief frames the seed topic.
  2. Discuss    — ~3 free turns where the moderator picks speakers based on
                  whose expertise maps to the thread.
  3. Crystallize — the moderator extracts a concrete idea (title, slug,
                  one-liner), scaffolds a project folder under
                  ~/.wingman/workspace/liveroom/<date>-<slug>/, and Chief
                  announces it in the channel.
  4. Build      — the remaining turns alternate between implementer turns
                  (Blueprint/Builder/Validator/Deploy/Scribe/... are *required*
                  to call write_file against the project folder) and short
                  reactions. After each turn we diff the project folder to
                  log which files were actually produced.
  5. Close      — Chief wraps with a synthesis + explicit list of artifacts.

Each bot uses its full AgentSession, so tool calls (write_file, web_search,
shell, etc.) are available. Pacing is adaptive.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from src.config.paths import WORKSPACE_DIR
from src.config.settings import Settings, get_settings
from src.providers.base import Message as ProviderMessage
from src.providers.manager import ProviderManager

if TYPE_CHECKING:
    from src.swarm.manager import SwarmManager

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Participant catalogue
# ---------------------------------------------------------------------------

PARTICIPANTS: dict[str, dict[str, str]] = {
    "coordinator":   {"name": "Chief",     "emoji": "🧠", "role": "engineering manager — frames questions, synthesizes, redirects"},
    "trend_watcher": {"name": "Pulse",     "emoji": "📡", "role": "ex-TechCrunch journalist — breaks AI news, cites sources, allergic to hype"},
    "research":      {"name": "Scout",     "emoji": "🔬", "role": "ML PhD research scientist — reads papers, compares approaches"},
    "innovator":     {"name": "Spark",     "emoji": "💡", "role": "3-exit founder — generates bold ideas, challenges assumptions"},
    "data":          {"name": "Analyst",   "emoji": "📊", "role": "data scientist w/ MBA — numbers, FIRE scoring, market sizing"},
    "architect":     {"name": "Blueprint", "emoji": "🏛️", "role": "principal systems architect — component diagrams, data flow"},
    "engineer":      {"name": "Builder",   "emoji": "🔨", "role": "senior tech lead — implementation concerns, real-world tradeoffs"},
    "tester":        {"name": "Validator", "emoji": "🧪", "role": "senior SDET — red-teams, finds failure modes, security-minded"},
    "devops":        {"name": "Deploy",    "emoji": "🚀", "role": "SRE lead — CI/CD, infra, operational reality"},
    "writer":        {"name": "Scribe",    "emoji": "📝", "role": "technical writer — clarifies, summarizes, documents decisions"},
}

# Roles that are expected to ship files during the build phase.
# Chief and Pulse can still be picked in discuss/react turns but won't be
# assigned build turns — they're not primarily implementers.
IMPLEMENTER_ORDER: list[str] = [
    "architect", "engineer", "tester", "devops", "writer",
    "research", "innovator", "data",
]


SEED_TOPICS: list[str] = [
    "What's one specific thing in open-source LLM tooling that's broken right now — and what would a good fix look like?",
    "If we had to ship one developer-productivity tool this month, what would it be and why?",
    "Pick a recent AI release and argue whether it's genuinely useful or overhyped.",
    "What's a boring, unglamorous problem in applied ML that an agent could actually solve well?",
    "Name a category of AI startup you'd bet against right now — and a better adjacent idea.",
    "What's a gap in the current agent-framework landscape nobody's filling?",
]


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

@dataclass
class Utterance:
    role_key: str
    display: str          # "🧠 Chief"
    text: str
    at: datetime

    def as_transcript_line(self) -> str:
        return f"{self.display}: {self.text.strip()}"


@dataclass
class Project:
    slug: str
    title: str
    one_liner: str
    path: Path                                   # ~/.wingman/workspace/liveroom/<date>-<slug>/
    round_index: int
    seed_topic: str
    created_at: datetime = field(default_factory=datetime.now)
    files_created: list[str] = field(default_factory=list)   # relative paths


# ---------------------------------------------------------------------------
# LiveRoom
# ---------------------------------------------------------------------------

class LiveRoom:
    """
    Drives a real-time team conversation in a Discord channel that
    crystallizes one buildable idea per round and produces real files.
    """

    def __init__(
        self,
        manager: "SwarmManager",
        channel_id: int,
        settings: Settings | None = None,
    ):
        self.manager = manager
        self.channel_id = channel_id
        self.settings = settings or get_settings()
        self.history: list[Utterance] = []
        self._stop = asyncio.Event()
        self._round_count = 0
        self._turn_count = 0

        self.projects: list[Project] = []
        self.current_project: Project | None = None

        self._provider_mgr = ProviderManager(self.settings)
        self._moderator = self._resolve_moderator()

    # -- provider -------------------------------------------------------------

    def _resolve_moderator(self):
        """Pick the cheapest configured provider for moderator decisions."""
        cfg = self.settings.providers
        try:
            if cfg.openai_chat.api_key:
                from src.providers.openai import OpenAIProvider
                return OpenAIProvider(
                    api_key=cfg.openai_chat.api_key,
                    api_base=cfg.openai_chat.api_base,
                    model=cfg.openai_chat.model,
                )
            if cfg.openai.api_key:
                from src.providers.openai import OpenAIProvider
                return OpenAIProvider(
                    api_key=cfg.openai.api_key,
                    api_base=cfg.openai.api_base,
                    model=self.settings.overnight.model,
                )
            if cfg.groq.api_key:
                from src.providers.groq import GroqProvider
                return GroqProvider(
                    api_key=cfg.groq.api_key,
                    api_base=cfg.groq.api_base,
                    model=cfg.groq.model,
                )
        except Exception as e:
            logger.warning(f"Moderator provider init failed: {e}")
        return self._provider_mgr.get_provider()

    # -- helpers --------------------------------------------------------------

    def _connected_roles(self) -> list[str]:
        return [r for r, b in self.manager.bots.items() if b._bot is not None]

    def _snapshot_files(self) -> set[str]:
        """Return relative paths of files inside the current project folder."""
        pj = self.current_project
        if not pj or not pj.path.exists():
            return set()
        return {
            str(p.relative_to(pj.path))
            for p in pj.path.rglob("*")
            if p.is_file()
        }

    async def _call_moderator_json(
        self,
        system: str,
        user: str,
        max_tokens: int = 300,
        temperature: float = 0.6,
    ) -> dict | None:
        """Run a moderator prompt and parse its JSON reply (with fence stripping)."""
        messages = [
            ProviderMessage(role="system", content=system),
            ProviderMessage(role="user", content=user),
        ]
        try:
            resp = await self._moderator.chat(
                messages=messages, tools=None,
                temperature=temperature, max_tokens=max_tokens,
            )
            raw = (resp.content or "").strip()
            if raw.startswith("```"):
                raw = raw.strip("`")
                if raw.lower().startswith("json"):
                    raw = raw[4:].strip()
            return json.loads(raw)
        except Exception as e:
            logger.warning(f"Moderator JSON parse failed: {e}")
            return None

    # -- speaker selection ----------------------------------------------------

    async def _pick_next_speaker(self, seed_topic: str) -> tuple[str, str]:
        """Discuss-phase pick: moderator LLM chooses who speaks next."""
        connected = self._connected_roles()
        if not connected:
            raise RuntimeError("No connected bots in the swarm")

        roster = "\n".join(
            f"  {r} → {PARTICIPANTS[r]['name']} ({PARTICIPANTS[r]['role']})"
            for r in connected if r in PARTICIPANTS
        )
        transcript = "\n".join(u.as_transcript_line() for u in self.history[-8:]) \
            or "(conversation just started)"

        system = (
            "You are the director of a fast-paced team conversation. "
            "Pick exactly one participant to speak next. Keep the discussion "
            "alive, avoid repetition, surface disagreement, and let the right "
            "specialist weigh in at the right moment."
        )
        user = (
            f"Seed topic: {seed_topic}\n\n"
            f"Roster (role_key → persona):\n{roster}\n\n"
            f"Recent transcript:\n{transcript}\n\n"
            "Rules:\n"
            "- Don't let the same person speak twice in a row unless directly challenged.\n"
            "- Pick someone whose expertise maps to the latest thread.\n"
            "- If the thread is drifting, pick 'coordinator' (Chief) to redirect.\n"
            "- If we're 6+ turns in with no concrete idea, pick 'innovator' or 'data'.\n\n"
            'Return STRICT JSON only: {"speaker": "<role_key>", "prompt": "<one-sentence instruction>"}'
        )
        data = await self._call_moderator_json(system, user)
        speaker = (data or {}).get("speaker", "")
        prompt = (data or {}).get("prompt", "") or "Continue the discussion in your own voice."
        if speaker not in connected:
            logger.debug(f"Moderator picked unknown speaker '{speaker}'; falling back")
            speaker = random.choice(connected)
        return speaker, prompt

    def _pick_implementer(self) -> tuple[str, str]:
        """Build-phase pick: rotate through implementer roles, prefer fresh voices."""
        connected = self._connected_roles()
        eligible = [r for r in IMPLEMENTER_ORDER if r in connected]
        if not eligible:
            return random.choice(connected), "Ship something real this turn."

        recent = [u.role_key for u in self.history[-3:]]
        fresh = [r for r in eligible if r not in recent]
        pick = fresh[0] if fresh else eligible[0]
        return pick, "It's your build turn — create a concrete file in the project folder."

    # -- crystallize ----------------------------------------------------------

    async def _crystallize_idea(self, topic: str) -> Project | None:
        """
        Extract a concrete idea from the discussion, scaffold a project folder,
        and announce it. Returns the new Project or None on failure.
        """
        transcript = "\n".join(u.as_transcript_line() for u in self.history[-8:])
        system = (
            "You are the project manager. Extract the single most concrete, "
            "buildable idea the team has discussed so far this round. The idea "
            "must be specific enough that a developer could start coding it "
            "in the next 5 minutes."
        )
        user = (
            f"Seed topic: {topic}\n\n"
            f"Recent transcript:\n{transcript}\n\n"
            'Return STRICT JSON only: '
            '{"title": "<5-8 word name>", '
            '"slug": "<lowercase-kebab-case, 2-5 words, filesystem-safe>", '
            '"one_liner": "<one concrete sentence describing the thing>"}'
        )
        data = await self._call_moderator_json(system, user, max_tokens=200, temperature=0.4)
        if data is None:
            title = f"Round {self._round_count} idea"
            slug = f"round-{self._round_count}"
            one_liner = topic
        else:
            title = str(data.get("title", "")).strip() or f"Round {self._round_count} idea"
            slug = _sanitize_slug(str(data.get("slug", "")).strip()) \
                or f"round-{self._round_count}"
            one_liner = str(data.get("one_liner", "")).strip() or topic

        date_str = datetime.now().strftime("%Y-%m-%d")
        project_path = WORKSPACE_DIR / "liveroom" / f"{date_str}-{slug}"
        try:
            project_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Could not create project folder {project_path}: {e}")
            return None

        seed_readme = (
            f"# {title}\n\n"
            f"{one_liner}\n\n"
            f"**Round:** {self._round_count}\n"
            f"**Started:** {datetime.now().isoformat(timespec='seconds')}\n"
            f"**Seed topic:** {topic}\n\n"
            "## Status\n\n"
            "Scaffolded by the LiveRoom. Persona bots are adding artifacts below.\n"
            "If any file here looks promising, the human can take it and build it properly.\n"
        )
        (project_path / "README.md").write_text(seed_readme)

        project = Project(
            slug=slug, title=title, one_liner=one_liner,
            path=project_path, round_index=self._round_count, seed_topic=topic,
        )
        project.files_created.append("README.md")

        chief = self.manager.bots.get("coordinator")
        if chief:
            msg = (
                f"**🧠 Chief — crystallizing the idea**\n"
                f"Project: **{title}**\n"
                f"> {one_liner}\n"
                f"Folder: `{project_path}`\n\n"
                "Team — next turns are **BUILD TIME**. Blueprint, Builder, "
                "Validator, Deploy, Scribe — use `write_file` to ship real "
                "files into that folder. No more just-talking."
            )
            try:
                await chief.send_to_channel(self.channel_id, msg)
            except Exception as e:
                logger.warning(f"Chief crystallize send failed: {e}")

        self.history.append(Utterance(
            role_key="coordinator",
            display="🧠 Chief",
            text=f"Project crystallized: {title} — {one_liner} (folder: {project_path})",
            at=datetime.now(),
        ))
        logger.info(f"Project crystallized: {title!r} ({slug}) → {project_path}")
        return project

    # -- one turn -------------------------------------------------------------

    async def _take_turn(self, seed_topic: str, mode: str = "discuss") -> Utterance | None:
        if mode == "build":
            role_key, direction = self._pick_implementer()
        else:
            role_key, direction = await self._pick_next_speaker(seed_topic)

        bot = self.manager.bots.get(role_key)
        if not bot:
            return None

        p = PARTICIPANTS.get(role_key, {"name": role_key, "emoji": "🤖"})
        display = f"{p['emoji']} {p['name']}"

        briefing = self._build_briefing(role_key, seed_topic, direction, mode)

        before = self._snapshot_files()
        try:
            reply = await bot.ask(briefing, context=f"live-room-{mode}")
        except Exception as e:
            logger.error(f"Bot {role_key} failed to produce a reply: {e}")
            return None
        after = self._snapshot_files()

        new_files = sorted(after - before)
        pj = self.current_project
        if pj and new_files:
            for rel in new_files:
                if rel not in pj.files_created:
                    pj.files_created.append(rel)
            logger.info(f"[turn {self._turn_count + 1}] ARTIFACTS from {display}: {new_files}")

        reply = _clean_reply(reply, p.get("name", ""))
        if not reply:
            return None

        try:
            await bot.send_to_channel(self.channel_id, reply)
        except Exception as e:
            logger.error(f"Failed to send message from {role_key}: {e}")
            return None

        u = Utterance(role_key=role_key, display=display, text=reply, at=datetime.now())
        self.history.append(u)
        self._turn_count += 1
        logger.info(f"[turn {self._turn_count}] ({mode}) {display}: {reply[:120]}")
        return u

    def _build_briefing(
        self, role_key: str, topic: str, direction: str, mode: str
    ) -> str:
        p = PARTICIPANTS[role_key]
        transcript = "\n".join(u.as_transcript_line() for u in self.history[-10:]) \
            or "(no prior messages)"

        if mode == "build" and self.current_project is not None:
            pj = self.current_project
            suggested = _default_artifact_for(role_key, pj.path)
            existing = ", ".join(pj.files_created) or "(only the seed README.md so far)"
            return (
                "You are in a live team chat — but it's BUILD TIME, not discuss time.\n"
                f"Project: **{pj.title}** — {pj.one_liner}\n"
                f"Project folder (absolute, sandboxed): {pj.path}\n"
                f"Files already in the folder: {existing}\n\n"
                f"Your job this turn: call the `write_file` tool to create a real "
                f"artifact in the project folder that moves this forward. "
                f"Suggested artifact for you ({p['name']}):\n  {suggested}\n\n"
                f"Recent transcript:\n{transcript}\n\n"
                f"Director's note: {direction}\n\n"
                "Rules:\n"
                "- YOU MUST CALL write_file with an absolute path under the project folder above. "
                "Do not just describe what you would write — write it.\n"
                "- If the suggested file already exists, pick a different filename that adds new value "
                "(e.g. add a module stub, a config, a second doc). Don't overwrite a teammate's work.\n"
                "- The content should be real: imports, function stubs, ASCII diagrams, concrete test "
                "cases, realistic Dockerfiles, not marketing copy.\n"
                "- Even if the idea looks weak, still ship a blueprint/stub — the human will decide later.\n"
                "- After writing, post a 1–3 sentence Discord message: what you created, why, and what's "
                "still missing. Do NOT prefix with your name.\n"
            )

        if mode == "react" and self.current_project is not None:
            pj = self.current_project
            existing = ", ".join(pj.files_created) or "(only the seed README.md)"
            return (
                "You are in a live team chat, reacting to the build work in progress.\n"
                f"Project: **{pj.title}** — {pj.one_liner}\n"
                f"Project folder: {pj.path}\n"
                f"Files so far: {existing}\n\n"
                f"Recent transcript:\n{transcript}\n\n"
                f"Director's note: {direction}\n\n"
                "Rules:\n"
                "- Reply in 2–4 sentences: critique, extend, or propose the next artifact.\n"
                "- You MAY use `read_file` to inspect anything just written — but don't dump its contents.\n"
                "- Reference specific files or people by name (use **bold**).\n"
                "- DO NOT prefix with your name.\n"
            )

        # Discuss mode (default, phase 1)
        return (
            "You are in a live team chat in a Discord channel. Stay in-persona.\n"
            f"Seed topic of the round: {topic}\n\n"
            f"Recent transcript:\n{transcript}\n\n"
            f"Director's note to you: {direction}\n\n"
            "Rules:\n"
            "- Reply in 2–5 sentences, conversational tone, like a real Slack message.\n"
            "- DO NOT prefix with your name (Discord already shows it).\n"
            "- Reference specific earlier statements and people by name.\n"
            "- You MAY use web_search if you need a source — but don't over-research.\n"
            "- No preamble, no 'Here is my response:', just speak."
        )

    # -- round orchestration --------------------------------------------------

    async def _open_round(self, topic: str) -> None:
        chief = self.manager.bots.get("coordinator")
        if not chief:
            return
        opener = (
            f"**🧠 Round {self._round_count} — seed topic**\n\n"
            f"> {topic}\n\n"
            "Team — let's hash this out. Three turns of discussion, then we "
            "crystallize the best idea and everyone ships a real file for it. "
            "Pulse, Scout, Spark, Analyst, Blueprint, Builder, Validator, Deploy, Scribe."
        )
        try:
            await chief.send_to_channel(self.channel_id, opener)
        except Exception as e:
            logger.warning(f"Chief open failed: {e}")
        self.history.append(Utterance(
            role_key="coordinator",
            display="🧠 Chief",
            text=f"Seed: {topic}",
            at=datetime.now(),
        ))

    async def _close_round(self) -> None:
        chief = self.manager.bots.get("coordinator")
        if not chief:
            return

        pj = self.current_project
        files_block: str
        if pj and pj.files_created:
            files_block = "Files produced this round:\n" + "\n".join(
                f"  - {f}" for f in pj.files_created
            )
        elif pj:
            files_block = "(only the seed README.md — team didn't ship additional artifacts)"
        else:
            files_block = "(no project crystallized)"

        transcript = "\n".join(u.as_transcript_line() for u in self.history[-16:])
        briefing = (
            "Round is wrapping up. Post a tight 4–6 line synthesis.\n"
            "Cover: (1) the idea that crystallized, (2) what artifacts were actually "
            "produced (be specific — file names matter), (3) what's still missing for "
            "the human to pick this up tomorrow. In-persona, no bullet padding.\n\n"
            f"Project: {pj.title if pj else '(none)'}\n"
            f"Project folder: {pj.path if pj else '(n/a)'}\n"
            f"{files_block}\n\n"
            f"Recent transcript:\n{transcript}"
        )
        try:
            synth = await chief.ask(briefing, context="live-room-close")
        except Exception as e:
            logger.warning(f"Chief close failed: {e}")
            return
        synth = _clean_reply(synth, "Chief")

        body = synth or ""
        if pj:
            body += f"\n\n**Project folder:** `{pj.path}`"
            if pj.files_created:
                file_list = "\n".join(f"• `{f}`" for f in pj.files_created)
                body += f"\n**Files:**\n{file_list}"
            else:
                body += "\n_No files produced beyond the seed README._"

        if body.strip():
            try:
                await chief.send_to_channel(
                    self.channel_id, f"**🧠 Chief — round wrap**\n{body}"
                )
            except Exception as e:
                logger.warning(f"Chief wrap send failed: {e}")

    async def run_round(self, topic: str | None = None, turns: int = 12) -> None:
        """Run one full round: open → discuss → crystallize → build → close."""
        self._round_count += 1
        topic = topic or random.choice(SEED_TOPICS)
        logger.info(f"=== Round {self._round_count} — {topic} ===")

        await self._open_round(topic)
        await asyncio.sleep(random.uniform(3, 6))

        # Phase 1 — discuss
        discuss_turns = min(3, max(1, turns // 3))
        for _ in range(discuss_turns):
            if self._stop.is_set():
                return
            await self._take_turn(topic, mode="discuss")
            await asyncio.sleep(random.uniform(8, 18))

        # Phase 2 — crystallize
        if not self._stop.is_set():
            project = await self._crystallize_idea(topic)
            if project is not None:
                self.current_project = project
                self.projects.append(project)
                await asyncio.sleep(random.uniform(3, 6))

        # Phase 3 — build (alternating build/react turns)
        build_turns = max(0, turns - discuss_turns)
        for i in range(build_turns):
            if self._stop.is_set():
                break
            mode = "build" if (i % 2 == 0) else "react"
            await self._take_turn(topic, mode=mode)
            await asyncio.sleep(random.uniform(8, 18))

        # Phase 4 — close
        await self._close_round()
        self.current_project = None

    async def run_forever(self, turns_per_round: int = 12, rest_minutes: int = 15) -> None:
        loop = asyncio.get_event_loop()
        try:
            import signal as _sig
            for s in (_sig.SIGINT, _sig.SIGTERM):
                try:
                    loop.add_signal_handler(s, self.stop)
                except NotImplementedError:
                    pass  # Windows
        except Exception:
            pass

        while not self._stop.is_set():
            try:
                await self.run_round(turns=turns_per_round)
            except Exception as e:
                logger.exception(f"Round failed: {e}")
            if self._stop.is_set():
                break
            rest = max(60, rest_minutes * 60)
            logger.info(f"Round {self._round_count} done. Resting {rest}s.")
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=rest)
            except asyncio.TimeoutError:
                continue

    def stop(self) -> None:
        logger.info("LiveRoom stop requested")
        self._stop.set()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sanitize_slug(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:40]


def _default_artifact_for(role_key: str, project_path: Path) -> str:
    """Per-role suggested artifact. Absolute paths so bots can pass them straight to write_file."""
    mapping: dict[str, str] = {
        "architect":     f"{project_path}/BLUEPRINT.md — component diagram (ASCII), data flow, module boundaries, first-pass API surface",
        "engineer":      f"{project_path}/src/main.py — real Python skeleton with imports, a primary class/function, and a runnable __main__ block",
        "tester":        f"{project_path}/TEST_PLAN.md — failure modes, happy path, edge cases, plus {project_path}/tests/test_smoke.py with 2-3 concrete assertions",
        "devops":        f"{project_path}/Dockerfile and/or {project_path}/docker-compose.yml — realistic infra for this component",
        "writer":        f"{project_path}/USAGE.md — what it is, how to run it, open questions (not a duplicate of README.md)",
        "research":      f"{project_path}/NOTES.md — relevant prior art, key papers/libraries, algorithms the prototype should use",
        "innovator":     f"{project_path}/PITCH.md — 90-second elevator pitch, 3 killer use cases, one killer demo",
        "data":          f"{project_path}/METRICS.md — FIRE score (Feasibility/Impact/Risk/Effort), 3 quantitative success metrics, market sizing",
        "trend_watcher": f"{project_path}/CONTEXT.md — recent releases/competitors that make this timely, with sources",
        "coordinator":   f"{project_path}/DECISIONS.md — open decisions with owners and rationale",
    }
    return mapping.get(role_key, f"{project_path}/NOTES-{role_key}.md — your angle on this project")


def _clean_reply(text: str, name: str) -> str:
    if not text:
        return ""
    t = text.strip()
    prefixes = [f"{name}:", f"**{name}:**", f"**{name}**:"]
    low = t.lower()
    for pref in prefixes:
        if low.startswith(pref.lower()):
            t = t[len(pref):].lstrip()
            break
    if len(t) > 1800:
        t = t[:1800].rsplit(" ", 1)[0] + "…"
    return t
