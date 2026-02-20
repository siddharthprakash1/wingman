#!/usr/bin/env python3
"""
Research Agent Example - Web Research and Information Synthesis

This example demonstrates how to use Wingman's research capabilities to:
1. Search the web for information
2. Gather data from multiple sources
3. Synthesize findings into a coherent report
4. Save results to markdown files

Usage:
    python examples/research_agent.py
"""

import asyncio
from pathlib import Path

from src.agent.loop import AgentLoop
from src.agents.router import AgentRouter
from src.config.settings import get_settings
from src.core.session import Session, SessionType
from src.memory.manager import MemoryManager
from src.providers.manager import ProviderManager
from src.tools.registry import create_default_registry


async def research_workflow():
    """Execute a research workflow on a specific topic."""
    
    # Setup
    settings = get_settings()
    workspace = Path(settings.workspace.path).expanduser()
    
    # Initialize components
    provider_manager = ProviderManager(settings)
    tool_registry = create_default_registry()
    memory_manager = MemoryManager(workspace)
    agent_router = AgentRouter()
    
    # Create a research session
    session = Session.create(
        session_type=SessionType.MAIN,
        channel="cli"
    )
    
    # Create agent loop
    agent_loop = AgentLoop(
        session=session,
        provider_manager=provider_manager,
        tool_registry=tool_registry,
        memory_manager=memory_manager,
        agent_router=agent_router,
        settings=settings,
    )
    
    # Define research topic
    research_topic = "Latest developments in quantum computing in 2026"
    
    print(f"🔬 Starting research on: {research_topic}")
    print("=" * 60)
    
    # Ask the agent to research
    query = f"""
    Please research the following topic and provide a comprehensive report:
    
    Topic: {research_topic}
    
    Your report should include:
    1. Key recent developments (2025-2026)
    2. Major players and organizations
    3. Technical breakthroughs
    4. Practical applications
    5. Future outlook
    
    Use web search to find current information. Synthesize your findings
    into a well-structured markdown report and save it to a file named
    'quantum_computing_report.md'.
    """
    
    # Execute the research workflow
    async for chunk in agent_loop.run_streaming(query):
        if chunk.get("type") == "content":
            print(chunk.get("content"), end="", flush=True)
        elif chunk.get("type") == "tool_call":
            tool_name = chunk.get("name")
            print(f"\n\n🛠️  Using tool: {tool_name}")
        elif chunk.get("type") == "tool_result":
            result = chunk.get("result", "")
            # Show truncated result
            preview = result[:200] + "..." if len(result) > 200 else result
            print(f"✅ Tool result: {preview}\n")
    
    print("\n" + "=" * 60)
    print("✅ Research complete!")
    
    # Show session summary
    print(f"\n📊 Session Summary:")
    print(f"   - Messages exchanged: {len(session.messages)}")
    print(f"   - Session ID: {session.session_id}")
    
    return session


async def quick_search_example():
    """Simple example of web search."""
    
    print("\n🔍 Quick Search Example")
    print("=" * 60)
    
    from src.tools.web_search import search_duckduckgo
    
    # Search for information
    results = await search_duckduckgo(
        query="Python 3.14 new features",
        num_results=5
    )
    
    print(results)


async def main():
    """Run examples."""
    
    print("""
╔══════════════════════════════════════════════════════════╗
║        Wingman Research Agent Example                    ║
╚══════════════════════════════════════════════════════════╝

This example demonstrates:
- Web search integration
- Information synthesis
- Report generation
- File output
    """)
    
    # Choose example
    print("\nSelect an example:")
    print("1. Full research workflow (comprehensive)")
    print("2. Quick web search (simple)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        await research_workflow()
    elif choice == "2":
        await quick_search_example()
    else:
        print("Invalid choice. Running full workflow...")
        await research_workflow()


if __name__ == "__main__":
    asyncio.run(main())
