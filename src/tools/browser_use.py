"""
Browser-Use Integration - AI-powered web automation.

Browser-Use is an open-source library that enables AI agents to 
control web browsers using natural language instructions.

Features:
- Natural language browser automation
- AI-driven decision making for web interactions
- Form filling, clicking, navigation
- Data extraction from web pages
- Screenshot capture

Installation:
    pip install browser-use
    uvx browser-use install  # Install Chromium
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from src.config.settings import get_settings
from src.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


@dataclass
class BrowserTaskResult:
    """Result from a browser automation task."""
    success: bool
    output: str = ""
    extracted_data: dict[str, Any] = field(default_factory=dict)
    screenshots: list[str] = field(default_factory=list)
    error: str | None = None
    steps_taken: list[str] = field(default_factory=list)


class BrowserAgent:
    """
    AI-powered browser automation using Browser-Use.
    
    Enables natural language control of web browsers for:
    - Web scraping and data extraction
    - Form filling and submission
    - Navigation and clicking
    - Screenshot capture
    - Testing and monitoring
    """

    def __init__(
        self,
        llm_provider: str = "openai",
        headless: bool = True,
    ):
        self.settings = get_settings()
        self.llm_provider = llm_provider
        self.headless = headless
        self._agent = None
        self._browser = None

    async def _get_llm(self):
        """Get the LLM instance based on provider."""
        if self.llm_provider == "browser_use":
            # Use Browser-Use's optimized model
            try:
                from browser_use import ChatBrowserUse
                return ChatBrowserUse()
            except ImportError:
                logger.warning("ChatBrowserUse not available, falling back to OpenAI")
                self.llm_provider = "openai"
        
        if self.llm_provider == "openai":
            try:
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model="gpt-4o",
                    api_key=self.settings.providers.openai.api_key,
                )
            except ImportError:
                raise ImportError(
                    "langchain-openai not installed. Run: pip install langchain-openai"
                )
        
        elif self.llm_provider == "anthropic":
            try:
                from langchain_anthropic import ChatAnthropic
                return ChatAnthropic(
                    model="claude-3-5-sonnet-20241022",
                )
            except ImportError:
                raise ImportError(
                    "langchain-anthropic not installed. Run: pip install langchain-anthropic"
                )
        
        elif self.llm_provider == "gemini":
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                return ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    google_api_key=self.settings.providers.gemini.api_key,
                )
            except ImportError:
                raise ImportError(
                    "langchain-google-genai not installed. Run: pip install langchain-google-genai"
                )
        
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")

    async def run_task(
        self,
        task: str,
        url: str | None = None,
        max_steps: int = 50,
        save_screenshots: bool = False,
    ) -> BrowserTaskResult:
        """
        Run a browser automation task.
        
        Args:
            task: Natural language description of the task
            url: Optional starting URL
            max_steps: Maximum steps before timeout
            save_screenshots: Whether to capture screenshots
            
        Returns:
            BrowserTaskResult with output and any extracted data
        """
        try:
            from browser_use import Agent, Browser
        except ImportError:
            return BrowserTaskResult(
                success=False,
                error=(
                    "browser-use not installed. Run:\n"
                    "  pip install browser-use\n"
                    "  uvx browser-use install"
                ),
            )

        steps_taken = []
        
        try:
            # Get LLM
            llm = await self._get_llm()
            
            # Configure browser
            browser_config = {
                "headless": self.headless,
            }
            
            # Prepend URL to task if provided
            if url:
                task = f"Go to {url}. Then: {task}"
            
            # Create and run agent
            agent = Agent(
                task=task,
                llm=llm,
                max_steps=max_steps,
            )
            
            # Run the task
            result = await agent.run()
            
            # Extract result data
            output = ""
            extracted_data = {}
            
            if hasattr(result, 'final_result'):
                output = str(result.final_result)
            elif hasattr(result, 'output'):
                output = str(result.output)
            else:
                output = str(result)
            
            # Try to parse as JSON if it looks like JSON
            if output.strip().startswith('{') or output.strip().startswith('['):
                try:
                    extracted_data = json.loads(output)
                except json.JSONDecodeError:
                    pass
            
            return BrowserTaskResult(
                success=True,
                output=output,
                extracted_data=extracted_data,
                steps_taken=steps_taken,
            )
            
        except Exception as e:
            logger.error(f"Browser task failed: {e}")
            return BrowserTaskResult(
                success=False,
                error=str(e),
                steps_taken=steps_taken,
            )

    async def extract_data(
        self,
        url: str,
        extraction_prompt: str,
    ) -> dict[str, Any]:
        """
        Extract structured data from a webpage.
        
        Args:
            url: URL to extract from
            extraction_prompt: What data to extract
            
        Returns:
            Extracted data as dictionary
        """
        task = f"Go to {url}. Extract the following information: {extraction_prompt}. Return the data as JSON."
        result = await self.run_task(task)
        
        if result.success:
            return result.extracted_data or {"raw_output": result.output}
        else:
            return {"error": result.error}

    async def fill_form(
        self,
        url: str,
        form_data: dict[str, str],
        submit: bool = False,
    ) -> BrowserTaskResult:
        """
        Fill out a form on a webpage.
        
        Args:
            url: URL with the form
            form_data: Dictionary of field names/labels to values
            submit: Whether to submit the form
            
        Returns:
            BrowserTaskResult
        """
        form_instructions = "\n".join([
            f"- Fill '{field}' with '{value}'"
            for field, value in form_data.items()
        ])
        
        task = f"""Go to {url}. Fill out the form:
{form_instructions}
{"After filling all fields, submit the form." if submit else "Do not submit the form."}"""
        
        return await self.run_task(task)

    async def take_screenshot(
        self,
        url: str,
        output_path: str,
    ) -> BrowserTaskResult:
        """
        Take a screenshot of a webpage.
        
        Args:
            url: URL to screenshot
            output_path: Path to save screenshot
            
        Returns:
            BrowserTaskResult with screenshot path
        """
        task = f"Go to {url}. Take a screenshot and save it."
        result = await self.run_task(task, save_screenshots=True)
        result.screenshots = [output_path]
        return result

    async def search_and_extract(
        self,
        search_query: str,
        search_engine: str = "google",
        num_results: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Search the web and extract results.
        
        Args:
            search_query: What to search for
            search_engine: Search engine to use (google, bing, duckduckgo)
            num_results: Number of results to extract
            
        Returns:
            List of search results with title, url, snippet
        """
        search_urls = {
            "google": "https://www.google.com",
            "bing": "https://www.bing.com",
            "duckduckgo": "https://duckduckgo.com",
        }
        
        url = search_urls.get(search_engine, search_urls["google"])
        
        task = f"""Go to {url}. 
Search for: {search_query}
Extract the top {num_results} search results including:
- Title
- URL
- Snippet/description
Return as JSON array."""
        
        result = await self.run_task(task)
        
        if result.success and result.extracted_data:
            if isinstance(result.extracted_data, list):
                return result.extracted_data
            return [result.extracted_data]
        
        return []


# Tool registration functions

async def browser_task(
    task: str,
    url: str = "",
    max_steps: int = 30,
) -> str:
    """
    Execute a browser automation task using AI.
    
    Args:
        task: Natural language description of what to do
        url: Optional starting URL
        max_steps: Maximum steps (default: 30)
        
    Returns:
        Task result or extracted data
    """
    agent = BrowserAgent(headless=True)
    result = await agent.run_task(
        task=task,
        url=url if url else None,
        max_steps=max_steps,
    )
    
    if result.success:
        if result.extracted_data:
            return json.dumps(result.extracted_data, indent=2)
        return result.output
    else:
        return f"❌ Browser task failed: {result.error}"


async def browser_extract(
    url: str,
    what_to_extract: str,
) -> str:
    """
    Extract specific data from a webpage.
    
    Args:
        url: URL to extract from
        what_to_extract: Description of data to extract
        
    Returns:
        Extracted data as JSON
    """
    agent = BrowserAgent(headless=True)
    data = await agent.extract_data(url, what_to_extract)
    return json.dumps(data, indent=2)


async def browser_form(
    url: str,
    form_fields: dict[str, str],
    submit: bool = False,
) -> str:
    """
    Fill out a web form.
    
    Args:
        url: URL with the form
        form_fields: Dictionary mapping field names to values
        submit: Whether to submit after filling
        
    Returns:
        Result message
    """
    agent = BrowserAgent(headless=True)
    result = await agent.fill_form(url, form_fields, submit)
    
    if result.success:
        return f"✅ Form filled successfully" + (" and submitted" if submit else "")
    else:
        return f"❌ Form filling failed: {result.error}"


def register_browser_use_tools(registry: ToolRegistry) -> None:
    """Register Browser-Use tools with the registry."""
    
    registry.register(
        name="browser_task",
        description=(
            "Execute a browser automation task using AI. "
            "Can navigate websites, click buttons, fill forms, extract data, etc. "
            "Describe the task in natural language."
        ),
        parameters={
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Natural language description of the task (e.g., 'Find the price of iPhone 15 on Amazon')",
                },
                "url": {
                    "type": "string",
                    "description": "Optional starting URL",
                    "default": "",
                },
                "max_steps": {
                    "type": "integer",
                    "description": "Maximum steps before timeout (default: 30)",
                    "default": 30,
                },
            },
            "required": ["task"],
        },
        func=browser_task,
    )
    
    registry.register(
        name="browser_extract",
        description=(
            "Extract specific data from a webpage using AI. "
            "The AI will navigate to the URL and extract the requested information."
        ),
        parameters={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to extract data from",
                },
                "what_to_extract": {
                    "type": "string",
                    "description": "Description of what data to extract (e.g., 'product name, price, and rating')",
                },
            },
            "required": ["url", "what_to_extract"],
        },
        func=browser_extract,
    )
    
    registry.register(
        name="browser_form",
        description=(
            "Fill out a web form using AI. "
            "Provide the URL and a dictionary of field names/labels to values."
        ),
        parameters={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL containing the form",
                },
                "form_fields": {
                    "type": "object",
                    "description": "Dictionary mapping field names/labels to values",
                    "additionalProperties": {"type": "string"},
                },
                "submit": {
                    "type": "boolean",
                    "description": "Whether to submit the form after filling",
                    "default": False,
                },
            },
            "required": ["url", "form_fields"],
        },
        func=browser_form,
    )
