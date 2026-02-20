#!/usr/bin/env python3
"""
Coding Assistant Example - Code Generation and Debugging

This example demonstrates how to use Wingman's coding capabilities to:
1. Generate code from natural language descriptions
2. Debug and fix code issues
3. Refactor existing code
4. Write tests and documentation

Usage:
    python examples/coding_assistant.py
"""

import asyncio
from pathlib import Path

from src.agents.coding.engineer import CodingEngineerAgent
from src.agents.coding.reviewer import CodeReviewerAgent
from src.config.settings import get_settings
from src.core.session import Session, SessionType
from src.providers.manager import ProviderManager
from src.tools.registry import create_default_registry


async def generate_snake_game():
    """Generate a simple Snake game using the coding agent."""
    
    print("🐍 Generating Snake Game...")
    print("=" * 60)
    
    # Setup
    settings = get_settings()
    provider_manager = ProviderManager(settings)
    tool_registry = create_default_registry()
    
    # Create coding session
    session = Session.create(
        session_type=SessionType.MAIN,
        channel="cli"
    )
    
    # Initialize coding agent
    coding_agent = CodingEngineerAgent()
    
    # Task description
    task = """
    Create a simple Snake game in Python using pygame.
    
    Requirements:
    1. Classic snake game mechanics (movement, food, growth)
    2. Score tracking
    3. Game over detection (wall collision, self collision)
    4. Simple graphics (colored rectangles)
    5. Keyboard controls (arrow keys)
    
    Save the code to 'snake_game.py' with proper documentation.
    """
    
    # Get the provider
    provider = await provider_manager.get_healthy_provider()
    
    # Execute task (simplified - in real usage, would use full agent loop)
    print(f"Task: {task}\n")
    print("Agent: Starting code generation...\n")
    
    # This is a simplified example showing the structure
    # In production, you'd use the full AgentLoop
    
    confidence = coding_agent.score_capability(task)
    print(f"✅ Coding agent confidence: {confidence:.0%}\n")
    
    if confidence > 0.7:
        print("Agent: I can help with this task!")
        print("Agent: I'll create the snake game with the following structure:")
        print("  - Game class for main logic")
        print("  - Snake class for snake state")
        print("  - Food class for food management")
        print("  - Main game loop with event handling")
        print("\nAgent: Writing code to snake_game.py...")
    
    return session


async def debug_code_example():
    """Debug a code snippet."""
    
    print("\n🐛 Code Debugging Example")
    print("=" * 60)
    
    buggy_code = '''
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)  # Bug: Division by zero if empty list

result = calculate_average([])  # This will crash!
print(result)
'''
    
    print("Buggy code:")
    print(buggy_code)
    
    print("\n🤖 Agent analysis:")
    print("Issue found: Division by zero when empty list is passed")
    print("\nSuggested fix:")
    
    fixed_code = '''
def calculate_average(numbers):
    if not numbers:  # Handle empty list
        return 0
    
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)

# Alternative: More pythonic version
def calculate_average_v2(numbers):
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)

result = calculate_average([])
print(f"Average of empty list: {result}")

result = calculate_average([1, 2, 3, 4, 5])
print(f"Average of [1,2,3,4,5]: {result}")
'''
    
    print(fixed_code)


async def code_review_example():
    """Demonstrate code review capabilities."""
    
    print("\n📝 Code Review Example")
    print("=" * 60)
    
    # Setup
    settings = get_settings()
    reviewer_agent = CodeReviewerAgent()
    
    code_to_review = '''
def process_data(data):
    results = []
    for item in data:
        if item > 0:
            results.append(item * 2)
    return results
'''
    
    print("Code under review:")
    print(code_to_review)
    
    confidence = reviewer_agent.score_capability(
        f"Review this code:\n{code_to_review}"
    )
    
    print(f"\n📊 Reviewer agent confidence: {confidence:.0%}\n")
    
    print("Review feedback:")
    print("""
✅ Strengths:
   - Clear function name
   - Simple logic
   - Returns expected type

⚠️  Suggestions:
   1. Add type hints for better code clarity
   2. Add docstring explaining parameters and return value
   3. Consider list comprehension for more Pythonic code
   4. Add input validation (handle None, non-iterable)
   5. Consider edge cases (empty list)

🔧 Improved version:
    """)
    
    improved_code = '''
def process_data(data: list[int | float]) -> list[int | float]:
    """
    Process numerical data by doubling positive values.
    
    Args:
        data: List of numbers to process
        
    Returns:
        List containing doubled positive values from input
        
    Examples:
        >>> process_data([1, -2, 3])
        [2, 6]
        >>> process_data([])
        []
    """
    if not isinstance(data, list):
        raise TypeError("Input must be a list")
    
    return [item * 2 for item in data if item > 0]
'''
    
    print(improved_code)


async def main():
    """Run coding examples."""
    
    print("""
╔══════════════════════════════════════════════════════════╗
║        Wingman Coding Assistant Example                  ║
╚══════════════════════════════════════════════════════════╝

This example demonstrates:
- Code generation from descriptions
- Debugging assistance
- Code review and improvement suggestions
- Best practices enforcement
    """)
    
    # Choose example
    print("\nSelect an example:")
    print("1. Generate Snake game (code generation)")
    print("2. Debug buggy code (debugging)")
    print("3. Code review (review & improvement)")
    print("4. Run all examples")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        await generate_snake_game()
    elif choice == "2":
        await debug_code_example()
    elif choice == "3":
        await code_review_example()
    elif choice == "4":
        await generate_snake_game()
        await debug_code_example()
        await code_review_example()
    else:
        print("Invalid choice. Running all examples...")
        await generate_snake_game()
        await debug_code_example()
        await code_review_example()
    
    print("\n" + "=" * 60)
    print("✅ Examples complete!")


if __name__ == "__main__":
    asyncio.run(main())
