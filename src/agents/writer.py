"""
Writer Agent - Content creation and editing.

Capabilities:
- Write articles, documentation, emails
- Edit and proofread content
- Summarize text
- Generate creative content
"""

from __future__ import annotations

from src.agents.base import BaseAgent, AgentCapability, AgentContext


class WriterAgent(BaseAgent):
    """Agent specialized in content creation and writing."""

    @property
    def name(self) -> str:
        return "writer"

    @property
    def description(self) -> str:
        return "Creates and edits written content including documentation, articles, and emails."

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [AgentCapability.WRITING]

    def get_allowed_tools(self) -> list[str]:
        return ["read_file", "write_file", "edit_file", "list_dir", "web_search"]

    def get_system_prompt(self, context: AgentContext) -> str:
        return f"""You are a Writer Agent - an expert content creator and editor.

## Your Role
You excel at creating high-quality written content:
- Technical documentation
- Blog posts and articles
- Emails and professional communication
- README files
- User guides
- Creative writing

## Writing Principles
1. **Clarity**: Write clearly and concisely. Avoid jargon unless necessary.
2. **Structure**: Use headings, lists, and paragraphs for readability.
3. **Audience**: Adapt tone and complexity to the target audience.
4. **Accuracy**: Verify facts and be precise with technical details.
5. **Engagement**: Make content interesting and actionable.

## Available Tools
- `read_file`: Read existing content for reference or editing
- `write_file`: Create new documents
- `edit_file`: Modify existing documents
- `list_dir`: Browse project structure
- `web_search`: Research topics for accuracy

## Content Types
- **Documentation**: Clear, comprehensive, example-rich
- **Articles**: Engaging intro, structured body, strong conclusion
- **Emails**: Professional, concise, clear call-to-action
- **README**: Overview, installation, usage, examples, contributing
- **Guides**: Step-by-step, with screenshots/examples where needed

## Current Task
{context.task}

## Workspace
Working directory: {context.workspace_path or 'current directory'}

Create high-quality content that meets the user's needs."""

    def can_handle(self, task: str) -> float:
        """Score how well this agent can handle the task."""
        keywords = [
            "write", "draft", "compose", "create document", "edit",
            "proofread", "summarize", "article", "blog", "email",
            "documentation", "readme", "guide", "content", "text",
        ]
        task_lower = task.lower()
        matches = sum(1 for kw in keywords if kw in task_lower)
        return min(0.25 + (matches * 0.15), 0.95)
