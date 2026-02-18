"""
System Prompt Builder — constructs the full system prompt
by assembling memory files, tool descriptions, and context.
"""

from __future__ import annotations

import logging
from datetime import datetime

from src.memory.manager import MemoryManager

logger = logging.getLogger(__name__)


class PromptBuilder:
    """
    Builds the system prompt by combining memory files.

    The system prompt structure (mirroring OpenClaw/PicoClaw):
    1. IDENTITY.md  — Who you are
    2. SOUL.md      — Personality and tone
    3. AGENTS.md    — Behavioral guidelines
    4. USER.md      — User preferences
    5. TOOLS.md     — Available tools
    6. MEMORY.md    — Long-term curated facts
    7. Today's log  — Today's conversation summary
    8. Skills       — Active skill instructions (if any)
    """

    def __init__(self, memory: MemoryManager):
        self.memory = memory

    def build_system_prompt(self, extra_context: str = "") -> str:
        """
        Build the complete system prompt from all memory files.

        Args:
            extra_context: Additional context to append (e.g., skill instructions).

        Returns:
            The full system prompt string.
        """
        sections: list[str] = []

        # 1. Identity
        identity = self.memory.read_file("IDENTITY.md")
        if identity.strip():
            sections.append(f"## Your Identity\n\n{identity.strip()}")

        # 2. Soul / Personality
        soul = self.memory.read_file("SOUL.md")
        if soul.strip():
            sections.append(f"## Your Personality\n\n{soul.strip()}")

        # 3. Agent guidelines
        agents = self.memory.read_file("AGENTS.md")
        if agents.strip():
            sections.append(f"## Guidelines\n\n{agents.strip()}")

        # 4. User preferences
        user = self.memory.read_file("USER.md")
        if user.strip():
            sections.append(f"## About the User\n\n{user.strip()}")

        # 5. Tools description
        tools = self.memory.read_file("TOOLS.md")
        if tools.strip():
            sections.append(f"## Your Tools\n\n{tools.strip()}")

        # 6. Long-term memory
        memory_content = self.memory.read_file("MEMORY.md")
        if memory_content.strip():
            sections.append(f"## Long-Term Memory\n\n{memory_content.strip()}")

        # 7. Today's conversation log
        today_log = self.memory.read_daily_log()
        if today_log.strip():
            sections.append(f"## Today's Activity Log\n\n{today_log.strip()}")

        # 8. Current context
        now = datetime.now()
        context = (
            f"## Current Context\n\n"
            f"- **Date**: {now.strftime('%A, %B %d, %Y')}\n"
            f"- **Time**: {now.strftime('%I:%M %p')}\n"
            f"- **Platform**: macOS (local machine)\n"
        )
        sections.append(context)

        # 9. Extra context (skills, etc.)
        if extra_context.strip():
            sections.append(f"## Additional Context\n\n{extra_context.strip()}")

        return "\n\n---\n\n".join(sections)

    def build_tool_prompt(self) -> str:
        """
        Build a minimal tool-use instruction prompt.
        This is appended when tools are available.
        """
        return (
            "You have access to tools. Use them when needed to answer questions, "
            "execute tasks, or gather information. Always explain what you're doing "
            "and why before using a tool. After using a tool, interpret the result "
            "for the user.\n\n"
            "**CRITICAL - Knowledge Base Rules**:\n"
            "1. Documents uploaded by the user are automatically indexed in the knowledge base.\n"
            "2. When the user asks about 'the PDF', 'the document', 'the file', or any uploaded content, "
            "you MUST use the `search_knowledge` tool FIRST to retrieve the content.\n"
            "3. NEVER say you don't have access to uploaded files - ALWAYS search the knowledge base.\n"
            "4. If a message contains '[Context: The user recently uploaded...]', immediately use `search_knowledge`.\n"
            "5. Use `list_knowledge` to see what documents are available if unsure.\n\n"
            "**Important**: Use the `memory_update` or `memory_append` tools to save "
            "important information about the user for future sessions."
        )
