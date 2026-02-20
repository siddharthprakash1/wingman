"""
Testing framework for Wingman AI agents.

Provides utilities for testing agents, tools, and multi-agent workflows.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

import pytest

logger = logging.getLogger(__name__)


@dataclass
class AgentTestCase:
    """Test case for agent."""
    name: str
    input: str
    expected_output: str | None = None
    expected_tools: List[str] | None = None
    expected_keywords: List[str] | None = None
    max_iterations: int = 10
    timeout_seconds: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentTestResult:
    """Result of agent test."""
    test_name: str
    passed: bool
    output: str
    tools_used: List[str]
    iterations: int
    duration_seconds: float
    error: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentTester:
    """
    Test framework for AI agents.
    
    Supports unit tests, integration tests, and end-to-end workflows.
    """
    
    def __init__(self, settings=None):
        """
        Initialize agent tester.
        
        Args:
            settings: Wingman settings for agent configuration
        """
        self.settings = settings
        self.results: List[AgentTestResult] = []
    
    async def run_test(
        self,
        test_case: AgentTestCase,
        session=None,
    ) -> AgentTestResult:
        """
        Run single agent test case.
        
        Args:
            test_case: Test case to run
            session: Agent session to use
        
        Returns:
            Test result
        """
        import time
        
        start_time = time.time()
        
        try:
            # Process message through agent
            response = await session.process_message(
                test_case.input,
                max_iterations=test_case.max_iterations,
            )
            
            duration = time.time() - start_time
            
            # Extract tools used (from session state)
            tools_used = getattr(session, "_tools_used", [])
            iterations = getattr(session, "_iterations", 0)
            
            # Validate results
            passed = True
            error = None
            
            if test_case.expected_output:
                if test_case.expected_output.lower() not in response.lower():
                    passed = False
                    error = f"Expected '{test_case.expected_output}' in output"
            
            if test_case.expected_tools:
                for tool in test_case.expected_tools:
                    if tool not in tools_used:
                        passed = False
                        error = f"Expected tool '{tool}' not used"
            
            if test_case.expected_keywords:
                for keyword in test_case.expected_keywords:
                    if keyword.lower() not in response.lower():
                        passed = False
                        error = f"Expected keyword '{keyword}' not in output"
            
            result = AgentTestResult(
                test_name=test_case.name,
                passed=passed,
                output=response,
                tools_used=tools_used,
                iterations=iterations,
                duration_seconds=duration,
                error=error,
                metadata=test_case.metadata,
            )
            
            self.results.append(result)
            return result
        
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            result = AgentTestResult(
                test_name=test_case.name,
                passed=False,
                output="",
                tools_used=[],
                iterations=0,
                duration_seconds=duration,
                error=f"Test timeout after {test_case.timeout_seconds}s",
            )
            self.results.append(result)
            return result
        
        except Exception as e:
            duration = time.time() - start_time
            result = AgentTestResult(
                test_name=test_case.name,
                passed=False,
                output="",
                tools_used=[],
                iterations=0,
                duration_seconds=duration,
                error=str(e),
            )
            self.results.append(result)
            return result
    
    async def run_test_suite(
        self,
        test_cases: List[AgentTestCase],
        session=None,
    ) -> List[AgentTestResult]:
        """Run multiple test cases."""
        results = []
        
        for test_case in test_cases:
            logger.info(f"Running test: {test_case.name}")
            result = await self.run_test(test_case, session)
            results.append(result)
            
            status = "✓" if result.passed else "✗"
            logger.info(
                f"{status} {test_case.name}: "
                f"{result.duration_seconds:.2f}s, "
                f"{result.iterations} iterations"
            )
        
        return results
    
    def get_summary(self) -> dict:
        """Get test summary statistics."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        if total > 0:
            avg_duration = sum(r.duration_seconds for r in self.results) / total
            avg_iterations = sum(r.iterations for r in self.results) / total
        else:
            avg_duration = 0
            avg_iterations = 0
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0,
            "avg_duration_seconds": avg_duration,
            "avg_iterations": avg_iterations,
        }
    
    def save_results(self, output_path: Path):
        """Save test results to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "summary": self.get_summary(),
            "results": [
                {
                    "test_name": r.test_name,
                    "passed": r.passed,
                    "output": r.output,
                    "tools_used": r.tools_used,
                    "iterations": r.iterations,
                    "duration_seconds": r.duration_seconds,
                    "error": r.error,
                    "metadata": r.metadata,
                }
                for r in self.results
            ],
        }
        
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved test results to {output_path}")


# Pytest fixtures
@pytest.fixture
def agent_tester(settings=None):
    """Pytest fixture for agent tester."""
    return AgentTester(settings=settings)


@pytest.fixture
async def agent_session(settings=None):
    """Pytest fixture for agent session."""
    from src.core.session import AgentSession
    
    session = AgentSession(
        session_id="test_session",
        settings=settings,
    )
    
    yield session
    
    # Cleanup
    await session.close()


# Example test cases
EXAMPLE_TEST_CASES = [
    AgentTestCase(
        name="simple_greeting",
        input="Hello!",
        expected_keywords=["hi", "hello", "greet"],
        max_iterations=1,
    ),
    AgentTestCase(
        name="file_search",
        input="Find all Python files in the current directory",
        expected_tools=["filesystem_list", "filesystem_search"],
        max_iterations=5,
    ),
    AgentTestCase(
        name="web_search",
        input="What's the latest news about AI?",
        expected_tools=["web_search"],
        expected_keywords=["ai", "news"],
        max_iterations=5,
    ),
]


# Example usage
if __name__ == "__main__":
    async def main():
        from src.config.settings import get_settings
        from src.core.session import AgentSession
        
        settings = get_settings()
        session = AgentSession(session_id="test", settings=settings)
        
        tester = AgentTester(settings=settings)
        
        # Run test suite
        results = await tester.run_test_suite(EXAMPLE_TEST_CASES, session=session)
        
        # Print summary
        summary = tester.get_summary()
        print(f"\nTest Summary:")
        print(f"  Total: {summary['total']}")
        print(f"  Passed: {summary['passed']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Pass Rate: {summary['pass_rate']:.1%}")
        print(f"  Avg Duration: {summary['avg_duration_seconds']:.2f}s")
        
        # Save results
        tester.save_results(Path("test_results.json"))
        
        await session.close()
    
    asyncio.run(main())
