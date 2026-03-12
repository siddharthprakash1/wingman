"""
Discord Bot Swarm — Multiple specialized Discord bots that collaborate.

## Core Team (Original 5)
- 🔬 Scout (ResearchBot): Scouts trends, news, papers
- 💻 Builder (EngineerBot): Builds code, prototypes, manages projects
- 📝 Scribe (WriterBot): Documentation, content, reports
- 📊 Analyst (DataBot): Analysis, scoring, trend evaluation
- 🧠 Chief (CoordinatorBot): Orchestrates daily sync-ups and decisions

## Extended Team (New 5)
- 📡 Pulse (TrendWatcher): AI news specialist, monitors breaking AI developments
- 🏗️ Blueprint (Architect): System design, API specs, technical architecture
- 🧪 Validator (Tester): QA specialist, writes tests, validates implementations
- 🚀 Deploy (DevOps): Infrastructure, CI/CD, Docker, deployment
- 💡 Spark (Innovator): Creative ideation, brainstorming, novel combinations

## Auto-Implementation Pipeline
When ideas score >= 7.0 in daily sync-ups:
1. Blueprint designs architecture
2. Builder implements MVP
3. Validator writes tests
4. Deploy sets up infrastructure

The bots share a common memory directory (~/.wingman/swarm/) and coordinate
via a dedicated Discord sync channel.
"""

from src.swarm.bots import BotPersonality, BotRole, SwarmBot, PERSONALITIES
from src.swarm.manager import SwarmManager, SwarmConfig
from src.swarm.sync import DailySyncOrchestrator, AUTO_IMPLEMENT_THRESHOLD

__all__ = [
    "BotPersonality",
    "BotRole",
    "SwarmBot",
    "PERSONALITIES",
    "SwarmManager",
    "SwarmConfig",
    "DailySyncOrchestrator",
    "AUTO_IMPLEMENT_THRESHOLD",
]
