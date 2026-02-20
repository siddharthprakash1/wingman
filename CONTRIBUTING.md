# Contributing to Wingman AI

Thank you for considering contributing to Wingman! This document provides guidelines and instructions for contributing.

## 🎯 Ways to Contribute

- **Bug Reports**: Found a bug? Open an [issue](https://github.com/yourusername/wingman/issues)
- **Feature Requests**: Have an idea? Start a [discussion](https://github.com/yourusername/wingman/discussions)
- **Code Contributions**: Submit a pull request
- **Documentation**: Improve docs, tutorials, examples
- **Plugins**: Create and share community plugins

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/wingman.git
cd wingman

# Add upstream remote
git remote add upstream https://github.com/yourusername/wingman.git
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e .[dev,all]

# Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

### 3. Create a Branch

```bash
# Update your fork
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

## 📝 Development Guidelines

### Code Style

We use **Black** for code formatting and **Ruff** for linting:

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/ --fix

# Type checking
mypy src/
```

### Code Standards

- **Type Hints**: Use type hints for all function signatures
- **Docstrings**: Document all public functions, classes, and modules (Google style)
- **Async/Await**: Use async patterns for I/O operations
- **Error Handling**: Handle exceptions gracefully with logging
- **Testing**: Write tests for new features and bug fixes

Example:

```python
async def process_message(
    message: str,
    session_id: str,
    max_iterations: int = 10,
) -> str:
    """
    Process a user message through the agent loop.
    
    Args:
        message: User's input message
        session_id: Unique session identifier
        max_iterations: Maximum tool execution iterations
    
    Returns:
        Agent's response text
    
    Raises:
        ValueError: If message is empty
        RuntimeError: If max iterations exceeded
    """
    if not message.strip():
        raise ValueError("Message cannot be empty")
    
    # Implementation...
```

### Testing

Write tests for all new features:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_core.py

# Run specific test
pytest tests/test_core.py::test_session_creation
```

Test structure:

```python
import pytest
from src.testing import AgentTester, AgentTestCase

@pytest.mark.asyncio
async def test_agent_response(agent_session):
    """Test agent can respond to simple query."""
    response = await agent_session.process_message("Hello")
    assert len(response) > 0
    assert any(word in response.lower() for word in ["hi", "hello", "greet"])
```

### Commit Messages

Use clear, descriptive commit messages following [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(channels): Add WhatsApp integration via Twilio
fix(security): Prevent path traversal in filesystem tool
docs(readme): Update installation instructions
test(agents): Add tests for multi-agent communication
refactor(providers): Simplify load balancing logic
perf(memory): Optimize vector search queries
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Test additions/changes
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks

## 🔍 Pull Request Process

### 1. Before Submitting

- [ ] Code follows project style guidelines
- [ ] All tests pass (`pytest`)
- [ ] New tests added for new features
- [ ] Documentation updated (README, docstrings)
- [ ] No merge conflicts with `main`
- [ ] Commit messages are clear and descriptive

### 2. Submit PR

1. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Open a Pull Request on GitHub

3. Fill out the PR template:
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update
   
   ## Testing
   - [ ] Tests pass locally
   - [ ] Added new tests
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] No breaking changes (or documented)
   ```

### 3. Code Review

- Maintainers will review your PR
- Address any requested changes
- Push updates to the same branch
- PR will be merged once approved

## 🐛 Bug Reports

### Before Reporting

1. Check [existing issues](https://github.com/yourusername/wingman/issues)
2. Try to reproduce on latest version
3. Collect relevant information

### Report Template

```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Step one
2. Step two
3. ...

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: macOS 14.0 / Ubuntu 22.04 / Windows 11
- Python: 3.11.5
- Wingman version: 0.1.0
- LLM Provider: Kimi K2.5

## Logs
```
Relevant error messages or logs
```

## Additional Context
Screenshots, configurations, etc.
```

## 💡 Feature Requests

### Before Requesting

1. Check [discussions](https://github.com/yourusername/wingman/discussions)
2. Consider if it fits the project scope
3. Think about implementation approach

### Request Template

```markdown
## Feature Description
Clear description of the feature

## Motivation
Why is this feature needed?

## Proposed Solution
How should it work?

## Alternatives Considered
Other approaches you've considered

## Additional Context
Examples, mockups, references
```

## 🔌 Plugin Development

### Plugin Structure

```
extensions/my-plugin/
├── plugin.json          # Plugin manifest
├── __init__.py          # Main plugin code
├── README.md            # Plugin documentation
└── requirements.txt     # Optional dependencies
```

### Plugin Manifest

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "type": "tool",
  "description": "Description of what this plugin does",
  "author": "Your Name <email@example.com>",
  "license": "MIT",
  "dependencies": [],
  "config": {
    "option1": "default_value"
  }
}
```

### Plugin Code

```python
"""
My Plugin - Description

Detailed plugin documentation.
"""

def setup(loader):
    """Called when plugin is loaded."""
    # Register your tool/channel/provider
    loader.register_tool(
        name="my_tool",
        definition={
            "description": "Tool description",
            "parameters": {
                "param1": {"type": "string", "description": "Parameter 1"}
            }
        },
        func=my_tool_implementation
    )

def my_tool_implementation(param1: str) -> dict:
    """Tool implementation."""
    return {"result": f"Processed: {param1}"}

def activate(loader):
    """Called when plugin becomes active."""
    pass

def deactivate(loader):
    """Called when plugin is deactivated."""
    pass

def teardown(loader):
    """Called when plugin is unloaded."""
    pass
```

### Sharing Plugins

1. Create a repository for your plugin
2. Add to [Awesome Wingman Plugins](https://github.com/yourusername/awesome-wingman-plugins)
3. Share in [Discussions](https://github.com/yourusername/wingman/discussions)

## 📚 Documentation

### Where to Update

- **README.md**: Main project documentation
- **Docstrings**: In-code documentation (Google style)
- **CONTRIBUTING.md**: This file
- **examples/**: Usage examples

### Documentation Style

- Use clear, concise language
- Include code examples
- Add screenshots/diagrams where helpful
- Keep README table of contents updated

## 🤝 Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all.

### Our Standards

**Positive Behavior:**
- Being respectful and inclusive
- Welcoming newcomers
- Accepting constructive criticism
- Focusing on what's best for the community

**Unacceptable Behavior:**
- Harassment or discrimination
- Trolling or insulting comments
- Publishing others' private information
- Other unprofessional conduct

### Enforcement

Violations may result in temporary or permanent ban from the project.

Report issues to: [conduct@wingman.ai](mailto:conduct@wingman.ai)

## 📞 Getting Help

- **Documentation**: [README.md](README.md)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/wingman/discussions)
- **Discord**: [Community Server](https://discord.gg/wingman)
- **Email**: [support@wingman.ai](mailto:support@wingman.ai)

## 🎉 Recognition

Contributors will be:
- Listed in [CONTRIBUTORS.md](CONTRIBUTORS.md)
- Mentioned in release notes
- Featured in community highlights

Thank you for contributing to Wingman! 🚀
