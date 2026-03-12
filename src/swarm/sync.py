"""
Daily Sync Orchestrator — runs the daily bot sync-up meeting.

The sync-up follows a structured protocol:
1. Coordinator opens the meeting
2. Pulse reports AI news/trends
3. Scout reports research findings
4. Spark presents innovative ideas
5. Analyst scores promising ideas
6. Blueprint designs architecture for approved ideas
7. Builder reports engineering status
8. Validator reports test results
9. Deploy reports infrastructure status
10. Coordinator makes go/no-go decisions
11. Scribe writes the summary

Projects with score >= 7.0 are AUTO-IMPLEMENTED.

This runs as a heartbeat task (configurable schedule) or can be
triggered manually via the /sync slash command.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.swarm.bots import SwarmBot, BotRole

logger = logging.getLogger(__name__)

# Auto-implementation threshold
AUTO_IMPLEMENT_THRESHOLD = 7.0


class DailySyncOrchestrator:
    """
    Orchestrates the daily sync-up meeting between swarm bots.

    The meeting happens in a dedicated Discord channel and follows
    a structured agenda. Results are saved to shared memory.
    """

    def __init__(
        self,
        bots: dict[str, "SwarmBot"],
        sync_channel_id: int,
        swarm_dir: Path,
    ):
        self.bots = bots  # role_name -> SwarmBot
        self.sync_channel_id = sync_channel_id
        self.swarm_dir = swarm_dir
        self.sync_history_dir = swarm_dir / "syncs"
        self.sync_history_dir.mkdir(parents=True, exist_ok=True)
        self._is_syncing = False

    @property
    def is_syncing(self) -> bool:
        return self._is_syncing

    async def run_sync(self) -> dict[str, Any]:
        """
        Run a full daily sync-up meeting with all bots.

        Enhanced flow:
        1. Coordinator opens meeting
        2. Pulse reports AI news/trends
        3. Scout reports research findings  
        4. Spark presents innovative ideas
        5. Analyst scores all ideas
        6. If any idea scores >= 7.0: AUTO-IMPLEMENT
           a. Blueprint designs architecture
           b. Builder implements MVP
           c. Validator writes tests
           d. Deploy sets up infrastructure
        7. Coordinator makes final decisions
        8. Scribe writes summary

        Returns a dict with the meeting results.
        """
        if self._is_syncing:
            logger.warning("Sync already in progress, skipping")
            return {"status": "skipped", "reason": "already_in_progress"}

        self._is_syncing = True
        timestamp = datetime.now()
        date_str = timestamp.strftime("%Y-%m-%d")
        time_str = timestamp.strftime("%H:%M")

        logger.info(f"Starting daily sync-up at {date_str} {time_str}")

        results: dict[str, Any] = {
            "date": date_str,
            "time": time_str,
            "status": "in_progress",
            "reports": {},
            "ideas": [],
            "scores": [],
            "approved_projects": [],
            "implementations": [],
            "decisions": [],
            "tasks": {},
        }

        try:
            # Get all bots (some may be None if not configured)
            coordinator = self.bots.get("coordinator")
            trend_watcher = self.bots.get("trend_watcher")
            researcher = self.bots.get("research")
            innovator = self.bots.get("innovator")
            analyst = self.bots.get("data")
            architect = self.bots.get("architect")
            engineer = self.bots.get("engineer")
            tester = self.bots.get("tester")
            devops = self.bots.get("devops")
            writer = self.bots.get("writer")

            # ----------------------------------------------------------
            # Step 1: Coordinator opens the meeting
            # ----------------------------------------------------------
            if coordinator:
                opening = (
                    f"# 🧠 Daily Sync-Up — {date_str} {time_str}\n\n"
                    f"Good {'morning' if timestamp.hour < 12 else 'afternoon'} team! "
                    f"Time for our daily sync. Today's agenda:\n\n"
                    f"**📋 Agenda:**\n"
                    f"1. 📡 AI News & Trends (Pulse)\n"
                    f"2. 🔬 Research Findings (Scout)\n"
                    f"3. 💡 Creative Ideas (Spark)\n"
                    f"4. 📊 Idea Scoring (Analyst)\n"
                    f"5. 🚀 Auto-Implementation (if score ≥ 7.0)\n"
                    f"6. 💻 Engineering Status (Builder)\n"
                    f"7. 🧪 Test Results (Validator)\n"
                    f"8. 🚀 Infrastructure (Deploy)\n"
                    f"9. 🎯 Decisions & Tasks\n"
                    f"10. 📝 Summary (Scribe)\n\n"
                    f"Let's go! 🔥"
                )
                await self._post_to_sync_channel(coordinator, opening)
                await asyncio.sleep(1)

            # ----------------------------------------------------------
            # Step 2: AI News & Trends (Pulse - Trend Watcher)
            # ----------------------------------------------------------
            if trend_watcher:
                await self._post_to_sync_channel(
                    coordinator or trend_watcher,
                    "---\n## 📡 Pulse — What's happening in AI today?"
                )
                trends_report = await trend_watcher.ask(
                    "Give your daily AI news briefing. Search for:\n"
                    "1. Breaking AI news from today\n"
                    "2. New model releases or announcements\n"
                    "3. Interesting research papers\n"
                    "4. Startup/funding news\n"
                    "5. Community discussions (HN, Reddit, Twitter)\n\n"
                    "List top 5 most important developments with 🔥/💡/📌 tags. "
                    "Highlight any that could become projects. Save to trends directory.",
                    context="Daily sync-up - AI news briefing",
                )
                results["reports"]["trends"] = trends_report
                await self._post_to_sync_channel(trend_watcher, trends_report)
                await asyncio.sleep(1)

            # ----------------------------------------------------------
            # Step 3: Research Findings (Scout)
            # ----------------------------------------------------------
            if researcher:
                await self._post_to_sync_channel(
                    coordinator or researcher,
                    "---\n## 🔬 Scout — Research findings?"
                )
                research_report = await researcher.ask(
                    "Give your daily sync-up report. What interesting things have you "
                    "found? List your top 3-5 findings with brief descriptions. "
                    "Focus on ACTIONABLE ideas we could implement. Be concise.",
                    context="Daily sync-up meeting",
                )
                results["reports"]["research"] = research_report
                await self._post_to_sync_channel(researcher, research_report)
                await asyncio.sleep(1)

            # ----------------------------------------------------------
            # Step 4: Creative Ideas (Spark - Innovator)
            # ----------------------------------------------------------
            if innovator:
                await self._post_to_sync_channel(
                    coordinator or innovator,
                    "---\n## 💡 Spark — What creative ideas do you have?"
                )
                
                # Give Spark context from trends and research
                trends_context = results["reports"].get("trends", "")[:800]
                research_context = results["reports"].get("research", "")[:800]
                
                ideas_report = await innovator.ask(
                    f"Based on today's AI trends and research:\n\n"
                    f"**Trends:** {trends_context}\n\n"
                    f"**Research:** {research_context}\n\n"
                    f"Generate 3 innovative project ideas. For each:\n"
                    f"- Name and one-liner\n"
                    f"- Problem it solves\n"
                    f"- Why NOW is the right time\n"
                    f"- MVP scope (what can we build in 1-2 days)\n\n"
                    f"Be creative but practical. Save to ideas directory.",
                    context="Daily sync-up - idea generation",
                )
                results["reports"]["ideas"] = ideas_report
                results["ideas"] = ideas_report
                await self._post_to_sync_channel(innovator, ideas_report)
                await asyncio.sleep(1)

            # ----------------------------------------------------------
            # Step 5: Idea Scoring (Analyst)
            # ----------------------------------------------------------
            all_ideas = ""
            if results["reports"].get("trends"):
                all_ideas += f"**From Trends:**\n{results['reports']['trends'][:600]}\n\n"
            if results["reports"].get("research"):
                all_ideas += f"**From Research:**\n{results['reports']['research'][:600]}\n\n"
            if results["reports"].get("ideas"):
                all_ideas += f"**From Innovator:**\n{results['reports']['ideas'][:600]}\n\n"

            if analyst and all_ideas:
                await self._post_to_sync_channel(
                    coordinator or analyst,
                    "---\n## 📊 Analyst — Score all ideas"
                )
                score_request = (
                    f"Score each distinct project idea from today's reports:\n\n"
                    f"{all_ideas}\n\n"
                    f"Use your FINE framework:\n"
                    f"- **F**easibility (1-10): Can we build it?\n"
                    f"- **I**mpact (1-10): Will people use it?\n"
                    f"- **N**ovelty (1-10): Is it new/different?\n"
                    f"- **E**ffort (1-10): How easy? (10=trivial)\n"
                    f"- **Overall**: Average score\n\n"
                    f"Present as a table. Mark ideas with Overall ≥ 7.0 as ✅ APPROVED for auto-implementation.\n"
                    f"Save analysis to your directory."
                )
                analysis = await analyst.ask(score_request, context="Daily sync-up scoring")
                results["scores"] = analysis
                await self._post_to_sync_channel(analyst, analysis)
                await asyncio.sleep(1)

                # ----------------------------------------------------------
                # Step 6: AUTO-IMPLEMENTATION for approved ideas (score >= 7.0)
                # ----------------------------------------------------------
                # Parse for approved projects (look for ✅ or score >= 7)
                if "✅" in analysis or "APPROVED" in analysis.upper() or ">= 7" in analysis:
                    await self._post_to_sync_channel(
                        coordinator or analyst,
                        "---\n## 🚀 AUTO-IMPLEMENTATION TRIGGERED!\n\n"
                        "One or more ideas scored ≥ 7.0. Starting implementation pipeline..."
                    )

                    # Extract the top approved idea for implementation
                    top_idea = await analyst.ask(
                        f"From your analysis:\n{analysis[:1000]}\n\n"
                        f"What is the SINGLE best idea to implement right now? "
                        f"Provide just the name and a 2-sentence description.",
                        context="Selecting top idea",
                    )
                    results["approved_projects"].append(top_idea)

                    # 6a. Architecture Design (Blueprint)
                    if architect:
                        await self._post_to_sync_channel(
                            architect,
                            f"---\n## 🏗️ Blueprint — Design the architecture\n\n"
                            f"**Project:** {top_idea[:500]}"
                        )
                        arch_design = await architect.ask(
                            f"Design the system architecture for this project:\n\n"
                            f"{top_idea}\n\n"
                            f"Provide:\n"
                            f"1. System overview (components)\n"
                            f"2. Data model/schema\n"
                            f"3. API endpoints (if applicable)\n"
                            f"4. Tech stack (Python preferred)\n"
                            f"5. File structure\n"
                            f"6. Implementation tasks for Builder\n\n"
                            f"Keep it minimal but complete. Save to architecture directory.",
                            context="Auto-implementation - architecture design",
                        )
                        results["implementations"].append({"phase": "architecture", "output": arch_design})
                        await self._post_to_sync_channel(architect, arch_design[:2000])
                        await asyncio.sleep(1)

                    # 6b. Implementation (Builder)
                    if engineer:
                        await self._post_to_sync_channel(
                            engineer,
                            f"---\n## 💻 Builder — Implement the MVP"
                        )
                        
                        arch_context = results["implementations"][-1]["output"][:1500] if results["implementations"] else top_idea
                        
                        implementation = await engineer.ask(
                            f"Implement the MVP for this project:\n\n"
                            f"**Project:** {top_idea[:500]}\n\n"
                            f"**Architecture:** {arch_context}\n\n"
                            f"Create:\n"
                            f"1. Main source files\n"
                            f"2. README.md with usage\n"
                            f"3. Requirements/dependencies\n\n"
                            f"Keep it simple and runnable. Save to projects directory.",
                            context="Auto-implementation - building MVP",
                        )
                        results["implementations"].append({"phase": "implementation", "output": implementation})
                        await self._post_to_sync_channel(engineer, implementation[:2000])
                        await asyncio.sleep(1)

                    # 6c. Testing (Validator)
                    if tester:
                        await self._post_to_sync_channel(
                            tester,
                            f"---\n## 🧪 Validator — Write tests"
                        )
                        tests = await tester.ask(
                            f"Write tests for this project:\n\n"
                            f"**Project:** {top_idea[:300]}\n\n"
                            f"Create pytest-compatible tests covering:\n"
                            f"1. Basic functionality\n"
                            f"2. Edge cases\n"
                            f"3. Error handling\n\n"
                            f"Save to tests directory.",
                            context="Auto-implementation - testing",
                        )
                        results["implementations"].append({"phase": "testing", "output": tests})
                        await self._post_to_sync_channel(tester, tests[:2000])
                        await asyncio.sleep(1)

                    # 6d. Infrastructure (Deploy)
                    if devops:
                        await self._post_to_sync_channel(
                            devops,
                            f"---\n## 🚀 Deploy — Set up infrastructure"
                        )
                        infra = await devops.ask(
                            f"Set up infrastructure for this project:\n\n"
                            f"**Project:** {top_idea[:300]}\n\n"
                            f"Create:\n"
                            f"1. Dockerfile\n"
                            f"2. docker-compose.yml\n"
                            f"3. Makefile with common commands\n"
                            f"4. .env.example\n"
                            f"5. GitHub Actions CI workflow\n\n"
                            f"Save to the project directory.",
                            context="Auto-implementation - infrastructure",
                        )
                        results["implementations"].append({"phase": "infrastructure", "output": infra})
                        await self._post_to_sync_channel(devops, infra[:2000])
                        await asyncio.sleep(1)

                    await self._post_to_sync_channel(
                        coordinator or engineer,
                        "---\n## ✅ Auto-Implementation Complete!\n\n"
                        f"Project **{top_idea[:100]}** has been designed, built, tested, and configured. "
                        f"Check the projects directory for the implementation."
                    )

            # ----------------------------------------------------------
            # Step 7: Engineering Status (existing projects)
            # ----------------------------------------------------------
            if engineer:
                await self._post_to_sync_channel(
                    coordinator or engineer,
                    "---\n## 💻 Builder — Status of existing projects?"
                )
                eng_report = await engineer.ask(
                    "Give a brief status on any OTHER ongoing projects "
                    "(not the one just implemented). Any blockers? Progress? "
                    "Check your projects directory. Be concise.",
                    context="Daily sync-up meeting",
                )
                results["reports"]["engineer"] = eng_report
                await self._post_to_sync_channel(engineer, eng_report)
                await asyncio.sleep(1)

            # ----------------------------------------------------------
            # Step 8: Test Results
            # ----------------------------------------------------------
            if tester:
                await self._post_to_sync_channel(
                    coordinator or tester,
                    "---\n## 🧪 Validator — Any bugs or test failures?"
                )
                test_report = await tester.ask(
                    "Report on test status across all projects. "
                    "Any failing tests? Bugs found? Check tests and bugs directories.",
                    context="Daily sync-up meeting",
                )
                results["reports"]["tester"] = test_report
                await self._post_to_sync_channel(tester, test_report)
                await asyncio.sleep(1)

            # ----------------------------------------------------------
            # Step 9: Infrastructure Status
            # ----------------------------------------------------------
            if devops:
                await self._post_to_sync_channel(
                    coordinator or devops,
                    "---\n## 🚀 Deploy — Infrastructure status?"
                )
                devops_report = await devops.ask(
                    "Report on infrastructure and deployment status. "
                    "Any issues? CI/CD status? Check devops directory.",
                    context="Daily sync-up meeting",
                )
                results["reports"]["devops"] = devops_report
                await self._post_to_sync_channel(devops, devops_report)
                await asyncio.sleep(1)

            # ----------------------------------------------------------
            # Step 10: Coordinator makes final decisions
            # ----------------------------------------------------------
            if coordinator:
                await self._post_to_sync_channel(
                    coordinator,
                    "---\n## 🎯 Chief — Decisions & Task Assignments"
                )
                
                all_reports = "\n\n".join([
                    f"**{k.title()}:** {v[:300]}" 
                    for k, v in results["reports"].items() if v
                ])
                
                decision_context = (
                    f"Here's what the team reported:\n\n{all_reports[:2000]}\n\n"
                    f"**Scores:** {str(results.get('scores', 'No scores'))[:500]}\n\n"
                    f"**Implementations:** {len(results.get('implementations', []))} phases completed\n\n"
                    f"Make decisions:\n"
                    f"1. Approve/reject the auto-implemented project?\n"
                    f"2. Any other projects to start?\n"
                    f"3. Assign tomorrow's tasks to each bot.\n"
                    f"Be decisive and specific."
                )
                decisions = await coordinator.ask(decision_context, context="Decision time")
                results["decisions"] = decisions
                await self._post_to_sync_channel(coordinator, decisions)
                await asyncio.sleep(1)

            # ----------------------------------------------------------
            # Step 11: Writer creates the summary
            # ----------------------------------------------------------
            if writer:
                await self._post_to_sync_channel(
                    coordinator or writer,
                    "---\n## 📝 Scribe — Meeting Summary"
                )
                
                summary_request = (
                    f"Create a comprehensive sync-up summary for {date_str}.\n\n"
                    f"Include:\n"
                    f"- 📡 AI News highlights\n"
                    f"- 🔬 Research findings\n"
                    f"- 💡 Ideas generated\n"
                    f"- 📊 Scoring results\n"
                    f"- 🚀 Projects auto-implemented\n"
                    f"- 🎯 Decisions made\n"
                    f"- 📋 Task assignments\n"
                    f"- ⚠️ Blockers (if any)\n\n"
                    f"Reports:\n{str(results['reports'])[:2000]}\n\n"
                    f"Decisions:\n{str(results['decisions'])[:500]}\n\n"
                    f"Format as a clean markdown document."
                )
                summary = await writer.ask(summary_request, context="Sync-up summary")
                results["summary"] = summary

                # Save the summary to shared memory
                summary_path = self.sync_history_dir / f"sync-{date_str}.md"
                summary_path.write_text(summary)
                logger.info(f"Sync summary saved to {summary_path}")

                # Post closing
                await self._post_to_sync_channel(
                    coordinator or writer,
                    f"---\n## 📋 Meeting Summary\n\n{summary[:2000]}"
                )

            # ----------------------------------------------------------
            # Closing
            # ----------------------------------------------------------
            if coordinator:
                implemented = len(results.get("implementations", []))
                closing = (
                    f"---\n# ✅ Sync Complete!\n\n"
                    f"**Date:** {date_str}\n"
                    f"**Ideas Scored:** {len(str(results.get('scores', '')).split('|')) // 5 or '?'}\n"
                    f"**Auto-Implementations:** {implemented} phases\n"
                    f"**Projects Approved:** {len(results.get('approved_projects', []))}\n\n"
                    f"See you tomorrow! 👋"
                )
                await self._post_to_sync_channel(coordinator, closing)

            # ----------------------------------------------------------
            # Done
            # ----------------------------------------------------------
            results["status"] = "completed"
            logger.info(f"Daily sync-up completed: {date_str}")

        except Exception as e:
            logger.error(f"Sync-up failed: {e}")
            results["status"] = "failed"
            results["error"] = str(e)

            # Try to notify the channel
            try:
                if coordinator:
                    await self._post_to_sync_channel(
                        coordinator,
                        f"❌ Sync-up encountered an error: {e}"
                    )
            except Exception:
                pass

        finally:
            self._is_syncing = False

        return results

    async def _post_to_sync_channel(self, bot: "SwarmBot", content: str) -> None:
        """Post a message to the sync channel from a specific bot."""
        try:
            await bot.send_to_channel(self.sync_channel_id, content)
        except Exception as e:
            logger.error(f"Failed to post to sync channel: {e}")

    def get_last_sync(self) -> dict[str, Any] | None:
        """Get the most recent sync summary."""
        files = sorted(self.sync_history_dir.glob("sync-*.md"), reverse=True)
        if not files:
            return None
        latest = files[0]
        return {
            "date": latest.stem.replace("sync-", ""),
            "content": latest.read_text(),
            "path": str(latest),
        }

    def list_syncs(self, limit: int = 10) -> list[dict[str, str]]:
        """List recent sync summaries."""
        files = sorted(self.sync_history_dir.glob("sync-*.md"), reverse=True)
        return [
            {
                "date": f.stem.replace("sync-", ""),
                "path": str(f),
            }
            for f in files[:limit]
        ]
