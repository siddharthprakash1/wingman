"""
Bot Personalities & SwarmBot — Individual Discord bot definitions.

Each SwarmBot wraps:
- A discord.py Bot instance with its own token
- A specialized AgentSession with a tailored system prompt
- Shared memory access for cross-bot collaboration
- Tool access appropriate to the bot's role
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.config.settings import Settings

logger = logging.getLogger(__name__)


class BotRole(str, Enum):
    """The specialization of each bot in the swarm."""
    # Core team (original)
    RESEARCH = "research"
    ENGINEER = "engineer"
    WRITER = "writer"
    DATA = "data"
    COORDINATOR = "coordinator"
    # New specialized agents
    TREND_WATCHER = "trend_watcher"  # AI news & trends specialist
    ARCHITECT = "architect"          # System design & architecture
    TESTER = "tester"                # QA & testing specialist
    DEVOPS = "devops"                # Deployment & infrastructure
    INNOVATOR = "innovator"          # Creative ideation & brainstorming


@dataclass
class BotPersonality:
    """Defines a bot's identity, appearance, and behavior."""
    role: BotRole
    name: str
    emoji: str
    color: int  # Discord embed color
    description: str
    system_prompt: str
    allowed_tools: list[str] = field(default_factory=list)
    status_message: str = ""


# ---------------------------------------------------------------------------
# Import detailed personality prompts
# ---------------------------------------------------------------------------
from src.swarm.personalities import (
    PULSE_PROMPT, SCOUT_PROMPT, BUILDER_PROMPT, ANALYST_PROMPT,
    BLUEPRINT_PROMPT, VALIDATOR_PROMPT, DEPLOY_PROMPT, 
    SPARK_PROMPT, SCRIBE_PROMPT, CHIEF_PROMPT
)

PERSONALITIES: dict[BotRole, BotPersonality] = {
    BotRole.RESEARCH: BotPersonality(
        role=BotRole.RESEARCH,
        name="Scout",
        emoji="🔬",
        color=0x3498DB,  # Blue
        description="PhD Research Scientist - finds papers, repos, and deep technical insights.",
        status_message="Reading arxiv papers...",
        allowed_tools=[
            "web_search", "web_fetch", "read_file", "write_file",
            "list_dir", "memory_read", "memory_append",
        ],
        system_prompt=SCOUT_PROMPT,
    ),

    BotRole.ENGINEER: BotPersonality(
        role=BotRole.ENGINEER,
        name="Builder",
        emoji="💻",
        color=0x2ECC71,  # Green
        description="Senior Tech Lead (15 YOE) - writes production code, builds prototypes.",
        status_message="Shipping code...",
        allowed_tools=[
            "bash", "read_file", "write_file", "edit_file", "list_dir",
            "web_search", "memory_read", "memory_append",
        ],
        system_prompt=BUILDER_PROMPT,
    ),

    BotRole.WRITER: BotPersonality(
        role=BotRole.WRITER,
        name="Scribe",
        emoji="📝",
        color=0xE67E22,  # Orange
        description="Tech Writer & Dev Advocate - documentation expert, explains anything clearly.",
        status_message="Writing docs...",
        allowed_tools=[
            "read_file", "write_file", "edit_file", "list_dir",
            "web_search", "memory_read", "memory_append",
        ],
        system_prompt=SCRIBE_PROMPT,
    ),

    BotRole.DATA: BotPersonality(
        role=BotRole.DATA,
        name="Analyst",
        emoji="📊",
        color=0x9B59B6,  # Purple
        description="Data Scientist + MBA (Ex-McKinsey) - scores ideas with FIRE framework.",
        status_message="Running the numbers...",
        allowed_tools=[
            "bash", "read_file", "write_file", "list_dir",
            "web_search", "memory_read", "memory_append",
        ],
        system_prompt=ANALYST_PROMPT,
    ),

    BotRole.COORDINATOR: BotPersonality(
        role=BotRole.COORDINATOR,
        name="Chief",
        emoji="🧠",
        color=0xE74C3C,  # Red
        description="Engineering Manager (Ex-Spotify/Airbnb) - runs the team, makes decisions.",
        status_message="Leading the team...",
        allowed_tools=[
            "read_file", "write_file", "list_dir",
            "web_search", "memory_read", "memory_append",
        ],
        system_prompt=CHIEF_PROMPT,
    ),

    # =========================================================================
    # NEW SPECIALIZED AGENTS
    # =========================================================================

    BotRole.TREND_WATCHER: BotPersonality(
        role=BotRole.TREND_WATCHER,
        name="Pulse",
        emoji="📡",
        color=0x00CED1,  # Dark Turquoise
        description="AI Industry Analyst (Ex-TechCrunch) - hunts real news with sources.",
        status_message="Breaking: checking sources...",
        allowed_tools=[
            "web_search", "web_fetch", "read_file", "write_file",
            "list_dir", "memory_read", "memory_append",
        ],
        system_prompt=PULSE_PROMPT,
    ),

    BotRole.ARCHITECT: BotPersonality(
        role=BotRole.ARCHITECT,
        name="Blueprint",
        emoji="🏗️",
        color=0x4169E1,  # Royal Blue
        description="Principal Architect (20 YOE, Ex-AWS/Netflix) - designs scalable systems.",
        status_message="Drawing diagrams...",
        allowed_tools=[
            "bash", "read_file", "write_file", "edit_file", "list_dir",
            "web_search", "memory_read", "memory_append",
        ],
        system_prompt=BLUEPRINT_PROMPT,
    ),

    BotRole.TESTER: BotPersonality(
        role=BotRole.TESTER,
        name="Validator",
        emoji="🧪",
        color=0x32CD32,  # Lime Green
        description="Senior SDET (10 YOE, Ex-Microsoft) - finds bugs, writes tests, security-minded.",
        status_message="What happens if I...",
        allowed_tools=[
            "bash", "read_file", "write_file", "edit_file", "list_dir",
            "memory_read", "memory_append",
        ],
        system_prompt=VALIDATOR_PROMPT,
    ),

    BotRole.DEVOPS: BotPersonality(
        role=BotRole.DEVOPS,
        name="Deploy",
        emoji="🚀",
        color=0xFF6347,  # Tomato
        description="SRE Lead (12 YOE, Ex-Google SRE) - automation, containers, CI/CD.",
        status_message="Did you add it to the Makefile?",
        allowed_tools=[
            "bash", "read_file", "write_file", "edit_file", "list_dir",
            "web_search", "memory_read", "memory_append",
        ],
        system_prompt=DEPLOY_PROMPT,
    ),

    BotRole.INNOVATOR: BotPersonality(
        role=BotRole.INNOVATOR,
        name="Spark",
        emoji="💡",
        color=0xFFD700,  # Gold
        description="Innovation Lead / Ex-Founder (3 exits) - sees opportunities others miss.",
        status_message="Okay hear me out...",
        allowed_tools=[
            "web_search", "web_fetch", "read_file", "write_file",
            "memory_read", "memory_append",
        ],
        system_prompt=SPARK_PROMPT,
    ),
}


class SwarmBot:
    """
    A single Discord bot in the swarm.

    Wraps a discord.py bot with a specialized AgentSession,
    shared memory access, and a distinct personality.
    """

    def __init__(
        self,
        personality: BotPersonality,
        token: str,
        settings: "Settings",
        swarm_dir: Path,
        sync_channel_id: int | None = None,
    ):
        self.personality = personality
        self.token = token
        self.settings = settings
        self.swarm_dir = swarm_dir
        self.sync_channel_id = sync_channel_id

        # Ensure bot-specific directories exist
        self._ensure_directories()

        # Will be initialized when the bot starts
        self._bot = None
        self._agent_session = None
        self._running = False

    def _ensure_directories(self) -> None:
        """Create the bot's shared memory directories."""
        dirs_by_role = {
            # Original bots
            BotRole.RESEARCH: "research",
            BotRole.ENGINEER: "projects",
            BotRole.WRITER: "docs",
            BotRole.DATA: "analysis",
            BotRole.COORDINATOR: "decisions",
            # New specialized bots
            BotRole.TREND_WATCHER: "trends",
            BotRole.ARCHITECT: "architecture",
            BotRole.TESTER: "tests",
            BotRole.DEVOPS: "devops",
            BotRole.INNOVATOR: "ideas",
        }
        subdir = dirs_by_role.get(self.personality.role, self.personality.role.value)
        (self.swarm_dir / subdir).mkdir(parents=True, exist_ok=True)
        
        # Also create bugs directory for Tester
        if self.personality.role == BotRole.TESTER:
            (self.swarm_dir / "bugs").mkdir(parents=True, exist_ok=True)

    def _get_agent_session(self):
        """Create a specialized AgentSession for this bot."""
        from src.agent.loop import AgentSession

        session = AgentSession(
            session_id=f"swarm-{self.personality.role.value}",
            settings=self.settings,
        )
        return session

    async def _process_message(self, user_input: str, context: str = "") -> str:
        """Process a message through the bot's agent session."""
        p = self.personality
        
        # Verbose logging - show what's happening
        print(f"\n{'='*60}")
        print(f"🤖 {p.emoji} {p.name} ({p.role.value}) - Processing request")
        print(f"{'='*60}")
        print(f"📥 Input: {user_input[:200]}{'...' if len(user_input) > 200 else ''}")
        if context:
            print(f"📋 Context: {context}")
        print(f"{'─'*60}")
        
        if self._agent_session is None:
            print(f"🔧 Creating new AgentSession for {p.name}...")
            self._agent_session = self._get_agent_session()

        # Prepend the bot's system prompt for better context
        full_input = f"[Bot: {p.name} ({p.role.value})]\n"
        full_input += f"[System Prompt Summary: {p.description}]\n"
        if context:
            full_input += f"[Context: {context}]\n"
        full_input += f"\nUser Request: {user_input}"
        
        # Add instruction to use tools and not hallucinate
        full_input += "\n\n[IMPORTANT: Use tools like web_search to get real information. Do NOT make up or hallucinate any information. If a tool fails, say so honestly.]"

        try:
            print(f"🧠 Sending to LLM ({self.settings.agents.defaults.model})...")
            response = await self._agent_session.process_message(
                full_input, channel="discord-swarm"
            )
            print(f"✅ Response received ({len(response)} chars)")
            print(f"📤 Response preview: {response[:300]}{'...' if len(response) > 300 else ''}")
            print(f"{'='*60}\n")
            return response
        except Exception as e:
            print(f"❌ Error: {type(e).__name__}: {e}")
            print(f"{'='*60}\n")
            logger.error(f"Bot {p.name} error: {e}")
            return f"❌ Error: {e}"

    async def start(self) -> None:
        """Start the Discord bot."""
        try:
            import discord
            from discord.ext import commands
        except ImportError:
            logger.error("discord.py not installed. pip install discord.py")
            return

        if not self.token:
            logger.warning(f"No token for {self.personality.name} bot")
            return

        intents = discord.Intents.default()
        intents.message_content = True

        bot = commands.Bot(
            command_prefix=f"!{self.personality.role.value} ",
            intents=intents,
            help_command=None,
        )
        self._bot = bot
        p = self.personality

        # --- Slash command: /ask ---
        @bot.tree.command(
            name="ask",
            description=f"Ask {p.name} ({p.emoji} {p.role.value}) a question",
        )
        async def ask_command(interaction: discord.Interaction, question: str):
            await interaction.response.defer()
            response = await self._process_message(
                question,
                context=f"User {interaction.user.name} asked via slash command",
            )
            embed = discord.Embed(
                description=response[:4096],
                color=p.color,
            )
            embed.set_author(name=f"{p.emoji} {p.name}")
            embed.set_footer(text=f"Requested by {interaction.user.name}")
            await interaction.followup.send(embed=embed)

        # --- Slash command: /status ---
        @bot.tree.command(
            name="status",
            description=f"Get {p.name}'s current status",
        )
        async def status_command(interaction: discord.Interaction):
            # Read recent work from the bot's directory
            recent = self._get_recent_work_summary()
            embed = discord.Embed(
                title=f"{p.emoji} {p.name} — Status",
                description=recent or "No recent activity.",
                color=p.color,
            )
            await interaction.response.send_message(embed=embed)

        # --- Slash command: /research (Research bot only) ---
        if p.role == BotRole.RESEARCH:
            @bot.tree.command(
                name="research",
                description="Research a topic and save findings",
            )
            async def research_command(interaction: discord.Interaction, topic: str):
                await interaction.response.defer()
                response = await self._process_message(
                    f"Research this topic thoroughly and save your findings: {topic}",
                    context="Explicit research request",
                )
                embed = discord.Embed(
                    description=response[:4096],
                    color=p.color,
                )
                embed.set_author(name=f"{p.emoji} {p.name} — Research")
                await interaction.followup.send(embed=embed)

        # --- Slash command: /build (Engineer bot only) ---
        if p.role == BotRole.ENGINEER:
            @bot.tree.command(
                name="build",
                description="Start building a project or prototype",
            )
            async def build_command(interaction: discord.Interaction, project: str):
                await interaction.response.defer()
                response = await self._process_message(
                    f"Create a project plan and start building: {project}",
                    context="Explicit build request",
                )
                embed = discord.Embed(
                    description=response[:4096],
                    color=p.color,
                )
                embed.set_author(name=f"{p.emoji} {p.name} — Building")
                await interaction.followup.send(embed=embed)

        # --- Slash command: /score (Data bot only) ---
        if p.role == BotRole.DATA:
            @bot.tree.command(
                name="score",
                description="Score a project idea on feasibility, impact, effort, novelty",
            )
            async def score_command(interaction: discord.Interaction, idea: str):
                await interaction.response.defer()
                response = await self._process_message(
                    f"Score this idea using your scoring framework:\n\n{idea}",
                    context="Explicit scoring request",
                )
                embed = discord.Embed(
                    description=response[:4096],
                    color=p.color,
                )
                embed.set_author(name=f"{p.emoji} {p.name} — Scoring")
                await interaction.followup.send(embed=embed)

        # --- Slash command: /sync (Coordinator bot only) ---
        if p.role == BotRole.COORDINATOR:
            @bot.tree.command(
                name="sync",
                description="Trigger a manual sync-up meeting",
            )
            async def sync_command(interaction: discord.Interaction):
                await interaction.response.defer()
                embed = discord.Embed(
                    title="🧠 Manual Sync-Up Triggered",
                    description="Starting sync-up meeting… This will take a moment.",
                    color=p.color,
                )
                await interaction.followup.send(embed=embed)
                # The actual sync is handled by DailySyncOrchestrator
                # which will be called from the SwarmManager

        # --- Slash command: /trends (Trend Watcher bot only) ---
        if p.role == BotRole.TREND_WATCHER:
            @bot.tree.command(
                name="trends",
                description="Get the latest AI news and trends",
            )
            async def trends_command(interaction: discord.Interaction):
                await interaction.response.defer()
                response = await self._process_message(
                    "Search for the latest AI news from today. Check Hacker News, "
                    "ArXiv, major AI company blogs, and tech news sites. "
                    "Summarize the top 5 most important developments and save your findings.",
                    context="Explicit trends request",
                )
                embed = discord.Embed(
                    description=response[:4096],
                    color=p.color,
                )
                embed.set_author(name=f"{p.emoji} {p.name} — AI Trends")
                await interaction.followup.send(embed=embed)

            @bot.tree.command(
                name="digest",
                description="Generate a daily AI news digest",
            )
            async def digest_command(interaction: discord.Interaction):
                await interaction.response.defer()
                response = await self._process_message(
                    "Create a comprehensive daily AI digest covering: "
                    "1) Breaking news 2) New model releases 3) Research papers "
                    "4) Startup/funding news 5) Community discussions. "
                    "Save to trends directory as today's digest.",
                    context="Daily digest request",
                )
                embed = discord.Embed(
                    description=response[:4096],
                    color=p.color,
                )
                embed.set_author(name=f"{p.emoji} {p.name} — Daily Digest")
                await interaction.followup.send(embed=embed)

        # --- Slash command: /design (Architect bot only) ---
        if p.role == BotRole.ARCHITECT:
            @bot.tree.command(
                name="design",
                description="Design architecture for a project",
            )
            async def design_command(interaction: discord.Interaction, project: str):
                await interaction.response.defer()
                response = await self._process_message(
                    f"Design the system architecture for this project: {project}\n\n"
                    "Include: system overview, component diagram, data model, "
                    "API design, tech stack recommendation, and implementation plan. "
                    "Save the architecture document.",
                    context="Architecture design request",
                )
                embed = discord.Embed(
                    description=response[:4096],
                    color=p.color,
                )
                embed.set_author(name=f"{p.emoji} {p.name} — Architecture")
                await interaction.followup.send(embed=embed)

        # --- Slash command: /test (Tester bot only) ---
        if p.role == BotRole.TESTER:
            @bot.tree.command(
                name="test",
                description="Write tests for a component or project",
            )
            async def test_command(interaction: discord.Interaction, component: str):
                await interaction.response.defer()
                response = await self._process_message(
                    f"Write comprehensive tests for: {component}\n\n"
                    "Include unit tests, edge cases, and error handling tests. "
                    "Use pytest format and save to the tests directory.",
                    context="Test writing request",
                )
                embed = discord.Embed(
                    description=response[:4096],
                    color=p.color,
                )
                embed.set_author(name=f"{p.emoji} {p.name} — Tests")
                await interaction.followup.send(embed=embed)

            @bot.tree.command(
                name="validate",
                description="Validate a project implementation",
            )
            async def validate_command(interaction: discord.Interaction, project: str):
                await interaction.response.defer()
                response = await self._process_message(
                    f"Validate the implementation of project: {project}\n\n"
                    "Run existing tests, check for bugs, verify error handling, "
                    "and report any issues found. Create bug reports if needed.",
                    context="Validation request",
                )
                embed = discord.Embed(
                    description=response[:4096],
                    color=p.color,
                )
                embed.set_author(name=f"{p.emoji} {p.name} — Validation")
                await interaction.followup.send(embed=embed)

        # --- Slash command: /deploy (DevOps bot only) ---
        if p.role == BotRole.DEVOPS:
            @bot.tree.command(
                name="setup",
                description="Set up project infrastructure",
            )
            async def setup_command(interaction: discord.Interaction, project: str):
                await interaction.response.defer()
                response = await self._process_message(
                    f"Set up infrastructure for project: {project}\n\n"
                    "Create: pyproject.toml, Dockerfile, docker-compose.yml, "
                    "Makefile, GitHub Actions CI workflow, and .env.example. "
                    "Save all files to the project directory.",
                    context="Project setup request",
                )
                embed = discord.Embed(
                    description=response[:4096],
                    color=p.color,
                )
                embed.set_author(name=f"{p.emoji} {p.name} — Setup")
                await interaction.followup.send(embed=embed)

            @bot.tree.command(
                name="deploy",
                description="Deploy a project",
            )
            async def deploy_command(interaction: discord.Interaction, project: str):
                await interaction.response.defer()
                response = await self._process_message(
                    f"Prepare deployment for project: {project}\n\n"
                    "Verify all configuration, run pre-deployment checks, "
                    "and provide deployment instructions or execute deployment.",
                    context="Deployment request",
                )
                embed = discord.Embed(
                    description=response[:4096],
                    color=p.color,
                )
                embed.set_author(name=f"{p.emoji} {p.name} — Deploy")
                await interaction.followup.send(embed=embed)

        # --- Slash command: /brainstorm (Innovator bot only) ---
        if p.role == BotRole.INNOVATOR:
            @bot.tree.command(
                name="brainstorm",
                description="Generate creative project ideas",
            )
            async def brainstorm_command(interaction: discord.Interaction, topic: str = ""):
                await interaction.response.defer()
                prompt = "Generate 5 creative project ideas"
                if topic:
                    prompt += f" related to: {topic}"
                prompt += (
                    "\n\nFor each idea, provide: name, one-liner, problem, "
                    "solution, why now, unique angle, and MVP scope. "
                    "Save the best ideas to the ideas directory."
                )
                response = await self._process_message(prompt, context="Brainstorming request")
                embed = discord.Embed(
                    description=response[:4096],
                    color=p.color,
                )
                embed.set_author(name=f"{p.emoji} {p.name} — Brainstorm")
                await interaction.followup.send(embed=embed)

            @bot.tree.command(
                name="innovate",
                description="Propose innovative solutions to a problem",
            )
            async def innovate_command(interaction: discord.Interaction, problem: str):
                await interaction.response.defer()
                response = await self._process_message(
                    f"Propose 3-5 innovative solutions to this problem: {problem}\n\n"
                    "Think outside the box, combine concepts from different domains, "
                    "and challenge assumptions. Include unconventional approaches.",
                    context="Innovation request",
                )
                embed = discord.Embed(
                    description=response[:4096],
                    color=p.color,
                )
                embed.set_author(name=f"{p.emoji} {p.name} — Innovation")
                await interaction.followup.send(embed=embed)

        # --- Event: on_ready ---
        @bot.event
        async def on_ready():
            logger.info(f"Swarm bot '{p.name}' ({p.emoji}) connected as {bot.user}")
            try:
                synced = await bot.tree.sync()
                logger.info(f"  → Synced {len(synced)} slash commands")
            except Exception as e:
                logger.error(f"  → Failed to sync commands: {e}")

            # Set custom status
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name=p.status_message,
            )
            await bot.change_presence(activity=activity)

        # --- Event: on_message ---
        @bot.event
        async def on_message(message: discord.Message):
            if message.author == bot.user:
                return
            # Respond to mentions or DMs
            if not (
                bot.user.mentioned_in(message)
                or isinstance(message.channel, discord.DMChannel)
            ):
                return

            text = message.content
            if bot.user:
                text = text.replace(f"<@{bot.user.id}>", "").strip()
                text = text.replace(f"<@!{bot.user.id}>", "").strip()
            if not text:
                return

            try:
                async with message.channel.typing():
                    response = await self._process_message(
                        text,
                        context=f"Discord message from {message.author.name}",
                    )
                # Send response, splitting if necessary
                if len(response) <= 2000:
                    await message.reply(response)
                else:
                    chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                    for i, chunk in enumerate(chunks):
                        if i == 0:
                            await message.reply(chunk)
                        else:
                            await message.channel.send(chunk)
            except Exception as e:
                logger.error(f"Bot {p.name} message handler error: {e}")
                await message.reply(f"❌ Error: {e}")

        self._running = True
        logger.info(f"Starting swarm bot: {p.emoji} {p.name} ({p.role.value})")
        await bot.start(self.token)

    async def stop(self) -> None:
        """Stop the Discord bot."""
        self._running = False
        if self._bot:
            await self._bot.close()
            logger.info(f"Stopped swarm bot: {self.personality.name}")

    async def send_to_channel(self, channel_id: int, content: str) -> None:
        """Send a message to a specific Discord channel."""
        if not self._bot:
            return
        channel = self._bot.get_channel(channel_id)
        if channel:
            # Split long messages
            if len(content) <= 2000:
                await channel.send(content)
            else:
                chunks = [content[i:i+2000] for i in range(0, len(content), 2000)]
                for chunk in chunks:
                    await channel.send(chunk)

    async def send_embed_to_channel(
        self, channel_id: int, title: str, description: str, fields: dict[str, str] | None = None
    ) -> None:
        """Send a rich embed to a specific Discord channel."""
        if not self._bot:
            return
        channel = self._bot.get_channel(channel_id)
        if channel:
            embed = discord.Embed(
                title=f"{self.personality.emoji} {title}",
                description=description[:4096],
                color=self.personality.color,
            )
            if fields:
                for name, value in fields.items():
                    embed.add_field(name=name, value=value[:1024], inline=False)
            await channel.send(embed=embed)

    async def ask(self, question: str, context: str = "") -> str:
        """Programmatically ask this bot a question (for bot-to-bot comms)."""
        return await self._process_message(question, context=context)

    def _get_recent_work_summary(self) -> str:
        """Get a summary of this bot's recent work from shared memory."""
        dirs_by_role = {
            # Original bots
            BotRole.RESEARCH: "research",
            BotRole.ENGINEER: "projects",
            BotRole.WRITER: "docs",
            BotRole.DATA: "analysis",
            BotRole.COORDINATOR: "decisions",
            # New specialized bots
            BotRole.TREND_WATCHER: "trends",
            BotRole.ARCHITECT: "architecture",
            BotRole.TESTER: "tests",
            BotRole.DEVOPS: "devops",
            BotRole.INNOVATOR: "ideas",
        }
        subdir = dirs_by_role.get(self.personality.role, self.personality.role.value)
        bot_dir = self.swarm_dir / subdir

        if not bot_dir.exists():
            return "No work directory found."

        files = sorted(bot_dir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
        if not files:
            return "No recent work files."

        # Return the last few file names and first lines
        lines = []
        for f in files[:5]:
            first_line = f.read_text().strip().split("\n")[0] if f.stat().st_size > 0 else "(empty)"
            age = datetime.now().timestamp() - f.stat().st_mtime
            if age < 3600:
                age_str = f"{int(age/60)}m ago"
            elif age < 86400:
                age_str = f"{int(age/3600)}h ago"
            else:
                age_str = f"{int(age/86400)}d ago"
            lines.append(f"• `{f.name}` ({age_str}): {first_line[:80]}")

        return "\n".join(lines)

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def bot_user(self):
        """Get the Discord user object for this bot."""
        return self._bot.user if self._bot else None
