# Wingman Examples

This directory contains practical examples demonstrating Wingman's capabilities.

## Quick Start Examples

1. **[research_agent.py](research_agent.py)** - Web research and information synthesis
2. **[coding_assistant.py](coding_assistant.py)** - Code generation and debugging
3. **[data_analysis.py](data_analysis.py)** - Data processing and visualization
4. **[memory_search.py](memory_search.py)** - Semantic search over conversation history
5. **[multi_agent.py](multi_agent.py)** - Multi-agent collaboration workflow

## Prerequisites

Before running examples:

```bash
# 1. Install Wingman
pip install -e .

# 2. Configure environment
cp .env.example .env
# Edit .env and add your API keys (at minimum, KIMI_API_KEY or GEMINI_API_KEY)

# 3. Initialize workspace
python -m src.cli.app onboard
```

## Running Examples

Each example can be run directly:

```bash
python examples/research_agent.py
python examples/coding_assistant.py
python examples/data_analysis.py
```

## Example Descriptions

### 1. Research Agent (`research_agent.py`)
Demonstrates web search, information gathering, and synthesis:
- Search the web for current information
- Gather data from multiple sources
- Synthesize findings into a coherent report
- Save results to markdown files

**Use cases:**
- Market research
- Technical documentation lookup
- News aggregation
- Fact-checking

### 2. Coding Assistant (`coding_assistant.py`)
Shows code generation, analysis, and debugging capabilities:
- Generate code from natural language descriptions
- Debug and fix code issues
- Refactor existing code
- Write tests and documentation

**Use cases:**
- Rapid prototyping
- Bug fixing
- Code review assistance
- Test generation

### 3. Data Analysis (`data_analysis.py`)
Demonstrates data processing and analysis:
- Load and process CSV/JSON data
- Perform statistical analysis
- Generate visualizations
- Export results

**Use cases:**
- Business intelligence
- Scientific data analysis
- Log file analysis
- Report generation

### 4. Memory Search (`memory_search.py`)
Shows semantic search over conversation history:
- Index past conversations
- Search by semantic meaning (not just keywords)
- Retrieve relevant context
- Build knowledge base

**Use cases:**
- Knowledge management
- Finding past discussions
- Context-aware assistance
- Personal knowledge base

### 5. Multi-Agent Collaboration (`multi_agent.py`)
Demonstrates complex workflows with multiple agents:
- Planner breaks down complex tasks
- Research agent gathers information
- Coding agent implements solutions
- Reviewer validates results

**Use cases:**
- Complex project execution
- End-to-end automation
- Quality-assured workflows
- Collaborative problem solving

## Advanced Usage

### Custom Tool Development

```python
from src.tools.registry import ToolRegistry

registry = ToolRegistry()

@registry.register(
    name="my_custom_tool",
    description="Does something useful",
    parameters={
        "type": "object",
        "properties": {
            "input": {"type": "string", "description": "Input parameter"}
        },
        "required": ["input"]
    }
)
async def my_custom_tool(input: str) -> str:
    # Your implementation here
    return f"Processed: {input}"
```

### Custom Agents

```python
from src.agents.base import BaseAgent

class MyCustomAgent(BaseAgent):
    def get_capabilities(self) -> list[str]:
        return ["custom_capability_1", "custom_capability_2"]
    
    def score_capability(self, task_description: str) -> float:
        # Return 0.0-0.95 based on how well this agent matches the task
        if "my specialty" in task_description.lower():
            return 0.9
        return 0.1
```

## Configuration Tips

### For Local/Offline Use

Use Ollama for completely local execution:

```bash
# Install Ollama
brew install ollama  # macOS
# or download from https://ollama.com

# Pull a model
ollama pull deepseek-r1:14b

# Update .env
DEFAULT_MODEL=ollama/deepseek-r1:14b
```

### For Cost-Effective Use

Use Gemini Flash or Kimi K2.5 (both have generous free tiers):

```env
DEFAULT_MODEL=gemini/gemini-2.5-flash
# or
DEFAULT_MODEL=kimi/kimi-k2.5
```

### For Best Performance

Use Gemini Pro or GPT-4o:

```env
DEFAULT_MODEL=gemini/gemini-2.5-pro
# or
DEFAULT_MODEL=openai/gpt-4o
```

## Troubleshooting

### "No providers available"
- Check that you've set at least one API key in `.env`
- Run `python -m src.cli.app doctor` to check configuration

### "Tool execution failed"
- Check tool permissions in session configuration
- Some tools (bash, file access) may be restricted in certain session types

### Import errors
- Make sure you've installed dependencies: `pip install -e .`
- Check that you're in the correct virtual environment

## Contributing

Have a great example to share? Please submit a PR with:
1. Your example script in this directory
2. Update to this README describing the example
3. Any required dependencies added to `requirements.txt`

## Support

- 📖 Full documentation: See main [README.md](../README.md)
- 🐛 Issues: Report at [GitHub Issues](https://github.com/siddharthprakash1/wingman/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/siddharthprakash1/wingman/discussions)
