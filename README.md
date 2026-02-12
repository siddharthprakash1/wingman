# 🦞 Wingman

**Wingman** is your personal, local AI assistant powered by **Kimi K2.5** (via Ollama).

It combines a powerful CLI, a beautiful WebChat UI, and a multi-agent "Project Mode" capable of planning and building complex software projects autonomously.

## Features

-   **💬 Chat**: A ChatGPT-like interface running locally.
-   **🚀 Project Mode**: innovative "Manager-Engineer-Reviewer" agent loop for building apps.
-   **🔌 Integrations**: Connects with Discord and Telegram.
-   **🧠 Memory**: Remembers past conversations and project context.
-   **🔍 Tools**: Capable of web search and file operations.

## Installation

```bash
pip install -e .
```

## Usage

### Start the Gateway (WebChat + API)

```bash
wingman gateway
```

Visit [http://localhost:18789](http://localhost:18789).

### CLI Chat

```bash
wingman chat "Hello, world!"
```

## Configuration

Configuration is stored in `~/.wingman/config.json`.
