# OpenClaw & PicoClaw Research Report

**Date**: February 20, 2026  
**Purpose**: Comprehensive analysis of OpenClaw and PicoClaw architectures to guide Wingman development  
**Status**: Complete autonomous research

---

## Executive Summary

**OpenClaw** (213k stars) is a production-grade, TypeScript-based personal AI assistant framework with enterprise-level multi-channel support, sophisticated agent orchestration, and a WebSocket-based Gateway architecture. It's designed to run on Mac/Linux/Windows with substantial resource requirements (>1GB RAM).

**PicoClaw** (16.6k stars) is an ultra-lightweight Go implementation inspired by OpenClaw, achieving 99% memory reduction (<10MB vs >1GB), 400x faster startup, and deployment on $10 hardware. It was bootstrapped using AI agents and focuses on core functionality with minimal dependencies.

**Wingman** (current implementation) is a Python-based multi-agent framework with MCP integration, memory systems, and multi-channel support. It sits between OpenClaw's enterprise complexity and PicoClaw's minimalist approach.

---

## 1. OpenClaw Architecture Analysis

### 1.1 Core Architecture

**Gateway-Centric Design**:
- **Single Gateway Daemon**: One long-lived process owns all messaging surfaces
- **WebSocket Control Plane**: All clients connect via WS on `127.0.0.1:18789`
- **Session Management**: Main session for direct chats, isolated group sessions
- **Multi-Agent Routing**: Route channels/accounts/peers to isolated agent workspaces

**Technology Stack**:
- **Language**: TypeScript (84.4%), Swift (11.6% for iOS/macOS)
- **Runtime**: Node.js ≥22
- **Package Manager**: pnpm (monorepo with workspaces)
- **Build System**: tsdown, TypeBox schemas → JSON Schema → Swift codegen
- **Testing**: Vitest (unit, e2e, gateway, extensions, live)

**Directory Structure**:
```
openclaw/
├── apps/                # Application packages
├── extensions/          # Channel extensions
├── packages/            # Core packages (monorepo)
├── src/                 # Main source
├── skills/              # Skill definitions
├── ui/                  # Web UI
├── vendor/a2ui/         # A2UI renderer
├── Swabble/             # iOS app
├── docs/                # Documentation site
└── test/                # Test suites
```

### 1.2 Agent System

**Pi Agent Runtime**:
- RPC mode with tool streaming and block streaming
- Workspace-based isolation (`~/.openclaw/workspace`)
- Multi-agent coordination via `sessions_*` tools
- Subagent spawning for parallel work

**Agent Files**:
```
~/.openclaw/workspace/
├── AGENTS.md           # Agent behavior guide
├── SOUL.md             # Agent personality/identity
├── TOOLS.md            # Tool descriptions
├── USER.md             # User preferences
├── HEARTBEAT.md        # Periodic task prompts (30min intervals)
├── sessions/           # Conversation history
├── memory/             # Long-term memory
└── skills/             # Custom skills
```

**Agent-to-Agent Communication**:
- `sessions_list` - Discover active agents
- `sessions_history` - Fetch transcripts
- `sessions_send` - Message other sessions with reply-back support

### 1.3 Memory Management

**Session Model**:
- **Main session**: Direct chats with user
- **Group sessions**: Isolated per-group contexts
- **Session pruning**: Automatic context management
- **Activation modes**: mention/always for groups
- **Queue modes**: Sequential message processing

**Memory Architecture**:
- **Transcript storage**: Full conversation logs in `sessions/`
- **Compact operation**: Summarize and reduce context
- **Memory templates**: Structured in `memory/` directory
- **Cross-session access**: Via `sessions_history` tool

### 1.4 Tool/Function Calling

**First-Class Tools**:
- **Browser Control**: Dedicated Chrome/Chromium with CDP
  - Snapshots, actions, uploads, profiles
  - Sandboxed execution
- **Canvas**: A2UI-based visual workspace
  - Push/reset, eval, snapshot
  - Agent-driven UI updates
- **Nodes**: Device-local execution
  - `system.run` - Execute commands (macOS)
  - `camera.*` - Camera snap/clip
  - `screen.record` - Screen recording
  - `location.get` - GPS location
  - `system.notify` - User notifications
- **Cron**: Scheduled jobs with database
- **Sessions**: Inter-agent communication
- **Discord/Slack Actions**: Native platform integrations

**Tool Streaming**:
- Real-time tool execution feedback
- Streaming results back to channels
- Block-level streaming for long operations

**Security Model**:
- **Sandbox modes**: per-session Docker containers for untrusted contexts
- **Tool allowlists**: Configurable per-agent
- **Tool denylists**: Block dangerous operations in groups
- **Elevated bash**: Per-session toggle with allowlist

### 1.5 LLM Provider Integration

**Model Configuration**:
```json
{
  "agent": {
    "model": "anthropic/claude-opus-4-6"
  },
  "models": {
    "claude-opus-4-6": {
      "provider": "anthropic",
      "maxTokens": 200000
    }
  }
}
```

**Supported Providers**:
- Anthropic (Claude Pro/Max with OAuth)
- OpenAI (ChatGPT/Codex with OAuth)
- Model failover system
- Provider rotation (OAuth vs API keys)
- Usage tracking and cost reporting

**OAuth Integration**:
- First-class OAuth support for Anthropic/OpenAI
- Token refresh and rotation
- Profile-based authentication

### 1.6 Multi-Channel Support

**Supported Channels** (All with bi-directional message flow):

**Primary Channels**:
- **WhatsApp**: via Baileys (QR pairing)
- **Telegram**: via grammY (bot token)
- **Discord**: via discord.js (bot token + intents)
- **Slack**: via Bolt SDK (bot + app tokens)
- **Signal**: via signal-cli
- **Google Chat**: via Chat API
- **Microsoft Teams**: via Bot Framework extension

**Extended Channels**:
- **BlueBubbles**: Recommended iMessage integration (webhook-based)
- **iMessage (legacy)**: macOS-only via `imsg`
- **Matrix**: Matrix protocol support
- **Zalo**: Vietnamese messaging platform
- **Zalo Personal**: Personal Zalo accounts
- **WebChat**: Built-in web interface

**Voice Channels**:
- **macOS/iOS/Android**: Voice Wake + Talk Mode
  - ElevenLabs integration
  - Push-to-talk (PTT)
  - Always-on speech

**Channel Features**:
- **DM Pairing**: Pairing codes for unknown senders (default)
- **Group Routing**: Mention gating, reply tags
- **Allowlists**: Per-channel sender filtering
- **Chunking**: Smart message splitting per channel limits
- **Media Pipeline**: Images/audio/video with transcription
- **Typing Indicators**: Real-time presence
- **Read Receipts**: Message status tracking

### 1.7 Session Management

**Gateway Protocol**:
```
WebSocket Text Frames (JSON)
├── connect         # Handshake (required first)
├── req/res        # Request-response pairs
└── event          # Server-push events
```

**Connection Lifecycle**:
1. Client sends `connect` with device identity
2. Gateway validates + issues device token
3. Client sends requests (`agent`, `send`, `health`)
4. Gateway pushes events (`presence`, `tick`, `agent`)

**Pairing System**:
- Device-based pairing for all WS clients
- Pairing codes for new devices
- Auto-approval for local/tailnet connections
- Challenge-response for remote devices

**Session State**:
```typescript
{
  thinkingLevel: "off|minimal|low|medium|high|xhigh",
  verboseLevel: boolean,
  model: string,
  sendPolicy: string,
  groupActivation: "mention|always",
  elevatedBash: boolean  // Per-session toggle
}
```

### 1.8 Unique Features

**Canvas + A2UI**:
- Agent-driven visual workspace
- Push HTML/CSS/JS updates
- Live rendering on macOS/iOS/Android
- Eval JavaScript in canvas context

**Voice Wake**:
- Always-on voice activation
- Push-to-talk mode
- Talk Mode overlay (continuous conversation)
- ElevenLabs TTS integration

**Nodes System**:
- Bonjour/mDNS discovery
- Device capability advertising
- Remote command execution
- Permission-aware (TCC on macOS)

**Skills Platform**:
- Bundled skills (shipped with OpenClaw)
- Managed skills (ClawHub registry)
- Workspace skills (user-defined)
- Install gating + UI
- Skill frontmatter (YAML metadata)

**ClawHub**:
- Centralized skill registry
- Skill search and discovery
- Agent can auto-install skills as needed

**Heartbeat System**:
- Periodic task prompts (30min default)
- Reads `HEARTBEAT.md` in workspace
- Async task execution
- Subagent spawning for long tasks

**Live Canvas**:
- Agent-controlled UI rendering
- Real-time updates
- Cross-platform (macOS, iOS, Android)

**Gmail Pub/Sub**:
- Webhook-based email triggers
- Integration with Google Cloud Pub/Sub
- Automated email processing

### 1.9 Code Quality & Best Practices

**Testing**:
- Comprehensive test suites (unit, e2e, gateway, extensions)
- Vitest for all testing
- Live testing config for integration tests

**Linting & Formatting**:
- Oxlint (fast linter)
- Oxfmt (formatter)
- Pre-commit hooks (detect-secrets, shellcheck)
- Swiftformat/Swiftlint for iOS

**Type Safety**:
- TypeBox schemas for protocol
- JSON Schema generation
- Swift model codegen from schemas
- Full TypeScript strict mode

**Development Workflow**:
- Hot reload in dev mode (`pnpm gateway:watch`)
- Auto-building UI on first run
- Monorepo with pnpm workspaces
- Daemon installation (`--install-daemon`)

**Release Process**:
- Semantic versioning (`vYYYY.M.D`)
- Channels: stable, beta, dev
- GitHub releases with changelog
- npm dist-tags
- Auto-update via Sparkle (macOS)

**Documentation**:
- Comprehensive docs site (docs.openclaw.ai)
- DeepWiki integration
- In-code documentation
- Contributing guidelines
- Vision document

### 1.10 Performance Optimizations

**Gateway Optimizations**:
- Single long-lived process (no restart needed)
- Config hot reload (hybrid mode)
- Event debouncing (300ms default)
- Connection pooling
- Idempotency keys for retries

**Resource Management**:
- Session pruning
- Media size caps
- Temp file lifecycle
- Memory-efficient streaming

**Networking**:
- WebSocket keep-alive
- Reconnection logic
- Rate limiting (3 req/60s for write RPCs)
- Retry policies

---

## 2. PicoClaw Architecture Analysis

### 2.1 Core Architecture

**Minimalist Design Philosophy**:
- **Single Binary**: Self-contained Go executable
- **No Dependencies**: Pure Go, no Node.js/Python required
- **Resource Efficient**: <10MB RAM, 1s boot time
- **Cross-Platform**: RISC-V, ARM, x86 support

**Technology Stack**:
- **Language**: Go 1.21+ (98.8%)
- **Build System**: Makefile with goreleaser
- **Binary Size**: Optimized with build flags
- **Deployment**: Single static binary

**Directory Structure**:
```
picoclaw/
├── cmd/picoclaw/       # Main entry point
├── pkg/                # Core packages
│   ├── agent/          # Agent implementation
│   ├── gateway/        # Gateway server
│   ├── channels/       # Channel integrations
│   ├── tools/          # Tool system
│   ├── memory/         # Memory management
│   └── providers/      # LLM providers
├── config/             # Config templates
├── workspace/          # Default workspace
└── docs/               # Documentation
```

### 2.2 Agent System

**Lightweight Agent Runtime**:
- Stateless agent execution
- Minimal context management
- Tool-based extensibility
- Subagent spawning via `spawn` tool

**Agent Workspace**:
```
~/.picoclaw/workspace/
├── AGENTS.md           # Agent behavior
├── SOUL.md             # Agent identity
├── TOOLS.md            # Tool descriptions
├── USER.md             # User preferences
├── HEARTBEAT.md        # Periodic tasks (30min)
├── IDENTITY.md         # Agent identity details
├── sessions/           # Session storage
├── memory/             # Long-term memory (MEMORY.md)
├── state/              # Persistent state
├── cron/               # Scheduled jobs
└── skills/             # Custom skills
```

**Agent Communication**:
- Subagent spawning for async tasks
- Independent context per subagent
- Direct user messaging via `message` tool
- No cross-session history (by design)

### 2.3 Memory Management

**Minimal Memory Footprint**:
- **RAM Usage**: <10MB (99% less than OpenClaw)
- **Session Storage**: Simple JSON files
- **Memory File**: Single `MEMORY.md` for long-term storage
- **State Management**: Minimal in `state/` directory

**Efficiency Techniques**:
- Lazy loading of sessions
- No in-memory caching
- Streaming responses
- Efficient Go garbage collection

### 2.4 Tool/Function Calling

**Core Tools**:
- **read_file**: Read files (workspace-restricted)
- **write_file**: Write files (workspace-restricted)
- **list_dir**: List directories (workspace-restricted)
- **edit_file**: Edit files (workspace-restricted)
- **append_file**: Append to files (workspace-restricted)
- **exec**: Execute commands (sandboxed)
- **web_search**: Web search (Brave or DuckDuckGo)
- **spawn**: Create subagent for async tasks
- **message**: Send message to user (from subagent)

**Security Sandbox** (Default: Enabled):
```json
{
  "agents": {
    "defaults": {
      "workspace": "~/.picoclaw/workspace",
      "restrict_to_workspace": true
    }
  }
}
```

**Sandbox Protection**:
- All file operations restricted to workspace
- Command execution path validation
- Dangerous command blocking:
  - `rm -rf`, `del /f`, `rmdir /s`
  - `format`, `mkfs`, `diskpart`
  - `dd if=`, direct disk writes
  - `shutdown`, `reboot`, `poweroff`
  - Fork bombs
- Consistent across main agent, subagents, heartbeat

### 2.5 LLM Provider Integration

**Model-Centric Configuration** (New Approach):
```json
{
  "model_list": [
    {
      "model_name": "gpt-5.2",
      "model": "openai/gpt-5.2",
      "api_key": "sk-..."
    },
    {
      "model_name": "claude-sonnet-4.6",
      "model": "anthropic/claude-sonnet-4.6",
      "api_key": "sk-ant-..."
    }
  ],
  "agents": {
    "defaults": {
      "model": "gpt-5.2"
    }
  }
}
```

**Provider Routing by Protocol**:
- **OpenAI-compatible**: OpenRouter, Groq, Zhipu, vLLM, Ollama, etc.
- **Anthropic protocol**: Claude-native API
- **Gemini protocol**: Google Gemini direct
- **OAuth path**: OpenAI OAuth/token auth

**Supported Providers** (15+ vendors):
- OpenAI, Anthropic, Google Gemini
- Zhipu (GLM), DeepSeek, Moonshot
- Qwen (通义千问), Groq, Cerebras
- NVIDIA, Ollama (local), OpenRouter
- vLLM, GitHub Copilot (gRPC)
- Volcengine, Shengsuanyun, Antigravity

**Load Balancing**:
- Multiple endpoints per model name
- Automatic round-robin distribution
- Failover support

**OAuth Support**:
- Anthropic OAuth via `picoclaw auth login --provider anthropic`
- Token management

### 2.6 Multi-Channel Support

**Supported Channels**:

| Channel | Complexity | Notes |
|---------|-----------|-------|
| Telegram | Easy | Bot token |
| Discord | Easy | Bot token + intents |
| QQ | Easy | AppID + AppSecret |
| DingTalk | Medium | App credentials |
| LINE | Medium | Credentials + webhook |

**Channel Features**:
- Bi-directional messaging
- Voice transcription (Groq Whisper for Telegram)
- Media support (basic)
- Group chat support (limited)

**Notable Omissions** (vs OpenClaw):
- No WhatsApp support
- No Slack integration
- No Signal support
- No iMessage/BlueBubbles
- No Google Chat, Teams, Matrix, Zalo

### 2.7 Session Management

**Simplified Sessions**:
- No WebSocket gateway (direct channel connections)
- File-based session storage
- Minimal state tracking
- No session pruning (manual cleanup)

**Configuration**:
```json
{
  "agents": {
    "defaults": {
      "max_tokens": 8192,
      "temperature": 0.7,
      "max_tool_iterations": 20
    }
  }
}
```

### 2.8 Unique Features

**Ultra-Lightweight Deployment**:
- Runs on $10 hardware (LicheeRV-Nano @ $9.9)
- Android phones via Termux
- NanoKVM for server maintenance
- MaixCAM for smart monitoring
- Embedded Linux devices (RISC-V)

**AI-Bootstrapped Development**:
- 95% agent-generated core code
- Human-in-the-loop refinement
- Self-improving codebase

**Heartbeat with Async Spawn**:
```markdown
# Periodic Tasks

## Quick Tasks (respond directly)
- Report current time

## Long Tasks (use spawn for async)
- Search the web for AI news and summarize
- Check email and report important messages
```

**ClawdChat Integration**:
- Agent Social Network
- Inter-agent communication
- Read skill.md from clawdchat.ai

**Termux Support**:
- Full Android deployment guide
- Proot-based Linux environment
- Mobile AI assistant

### 2.9 Code Quality & Best Practices

**Go Best Practices**:
- golangci-lint configuration
- Goreleaser for releases
- Docker Compose support
- Comprehensive error handling

**Security**:
- Command injection prevention
- System abuse protection
- Workspace sandboxing
- Input validation

**Development Workflow**:
- `make build` - Build binary
- `make build-all` - Multi-platform builds
- `make install` - Build and install
- Hot reload not mentioned (Go limitation)

**Testing**:
- Skill validation with test cases
- Basic unit tests
- No comprehensive test suite mentioned

**Documentation**:
- Multi-language READMEs (EN, ZH, JA, PT, VI, FR)
- Configuration examples
- Deployment guides
- Community roadmap

### 2.10 Performance Characteristics

**Startup Performance**:
- **Boot Time**: <1s (vs >500s for TypeScript)
- **Memory**: <10MB (vs >1GB for OpenClaw)
- **Binary Size**: Optimized with build flags
- **Cold Start**: Fast Go runtime initialization

**Resource Efficiency**:
- No JIT compilation overhead
- Efficient Go concurrency
- Minimal dependency tree
- Static binary (no runtime dependencies)

**Deployment Targets**:
- $10 hardware (LicheeRV-Nano)
- 0.6GHz single-core processors
- 256MB RAM boards
- Old Android phones (10+ years)

**Trade-offs**:
- Recent PRs increased memory to 10-20MB
- Feature additions impact footprint
- Optimization planned for v1.0

---

## 3. Comparison Matrix

### 3.1 Architecture Comparison

| Aspect | OpenClaw | PicoClaw | Wingman |
|--------|----------|----------|---------|
| **Language** | TypeScript | Go | Python |
| **Runtime** | Node.js ≥22 | Native Go | Python 3.11+ |
| **Memory** | >1GB | <10MB | ~50-100MB |
| **Startup** | >500s | <1s | ~5-10s |
| **Cost** | Mac Mini ($599) | Any Linux ($10) | Any Linux ($20-50) |
| **Architecture** | Gateway WS Control Plane | Direct Channel + CLI | Multi-agent with MCP |
| **Concurrency** | Node.js async | Go goroutines | Python asyncio |
| **Deployment** | npm package + daemon | Single binary | pip package |

### 3.2 Feature Comparison

| Feature | OpenClaw | PicoClaw | Wingman |
|---------|----------|----------|---------|
| **Multi-Channel** | 12+ channels | 5 channels | 4 channels |
| **WhatsApp** | ✅ Baileys | ❌ | ❌ |
| **Telegram** | ✅ grammY | ✅ | ✅ |
| **Discord** | ✅ discord.js | ✅ | ✅ |
| **Slack** | ✅ Bolt SDK | ❌ | ❌ |
| **WebChat** | ✅ Built-in | ❌ | ✅ |
| **Voice** | ✅ Wake+Talk | ❌ | ❌ |
| **Canvas/UI** | ✅ A2UI | ❌ | ❌ |
| **Browser Control** | ✅ CDP | ❌ | ✅ BrowserUse |
| **Memory** | Sessions + Memory | MEMORY.md | MemGPT-style |
| **Multi-Agent** | sessions_* tools | spawn subagent | Native routing |
| **Skills** | ClawHub registry | Basic workspace | MCP servers |
| **Cron** | ✅ Database | ✅ File-based | ✅ APScheduler |
| **Sandbox** | Docker per-session | Workspace-restricted | ❌ (planned) |
| **OAuth** | ✅ Anthropic/OpenAI | ✅ Anthropic | ❌ |
| **Hot Reload** | ✅ Hybrid mode | ❌ | ❌ |

### 3.3 Agent System Comparison

| Aspect | OpenClaw | PicoClaw | Wingman |
|--------|----------|----------|---------|
| **Agent Runtime** | Pi (RPC mode) | Lightweight Go | Custom Python |
| **Workspace** | ~/.openclaw/workspace | ~/.picoclaw/workspace | Configurable |
| **Agent Files** | AGENTS/SOUL/TOOLS/USER | AGENTS/SOUL/TOOLS/USER/IDENTITY | AGENTS.md only |
| **Heartbeat** | ✅ 30min default | ✅ 30min default | ❌ |
| **Subagents** | sessions_spawn | spawn tool | Native routing |
| **Agent-to-Agent** | sessions_* tools | spawn + message | Shared memory |
| **Context** | Full session history | Minimal | MemGPT segments |

### 3.4 Tool System Comparison

| Tool Category | OpenClaw | PicoClaw | Wingman |
|---------------|----------|----------|---------|
| **File Ops** | Full (sandbox-aware) | Workspace-only | Full (no sandbox) |
| **Shell Exec** | Elevated bash toggle | Sandboxed exec | Shell tool |
| **Web Search** | ❌ | Brave/DuckDuckGo | Brave Search |
| **Browser** | CDP control | ❌ | BrowserUse MCP |
| **Canvas** | A2UI + Canvas API | ❌ | ❌ |
| **Media** | Camera/Screen/Audio | ❌ | Desktop capture |
| **Location** | ✅ Nodes | ❌ | ❌ |
| **Notifications** | ✅ macOS/iOS/Android | ❌ | macOS (basic) |
| **Cron** | Database-backed | File-based | APScheduler |
| **Sessions** | Inter-agent comm | Subagent spawn | Shared state |

### 3.5 Provider Integration Comparison

| Aspect | OpenClaw | PicoClaw | Wingman |
|--------|----------|----------|---------|
| **Config Style** | Model-centric | model_list array | Provider-centric |
| **Providers** | Anthropic/OpenAI (OAuth) | 15+ vendors | OpenAI-compatible |
| **Failover** | ✅ Model failback | ✅ Load balancing | ❌ |
| **OAuth** | ✅ First-class | ✅ Anthropic | ❌ |
| **Cost Tracking** | ✅ Usage reports | ❌ | ❌ |
| **Rotation** | ✅ API key rotation | ✅ Round-robin | ❌ |

### 3.6 Session Management Comparison

| Aspect | OpenClaw | PicoClaw | Wingman |
|--------|----------|----------|---------|
| **Protocol** | WebSocket JSON | Direct/CLI | Direct/CLI |
| **Pairing** | Device-based | N/A | N/A |
| **State** | Rich (7+ fields) | Minimal | Basic |
| **Persistence** | File-based | File-based | File/DB-based |
| **Pruning** | ✅ Automatic | ❌ Manual | ❌ Manual |
| **Hot Reload** | ✅ Config changes | ❌ | ❌ |

---

## 4. Gaps in Wingman vs OpenClaw/PicoClaw

### 4.1 Critical Gaps (High Priority)

1. **Gateway Architecture**
   - **Missing**: WebSocket control plane
   - **Impact**: No central coordination, limited scalability
   - **OpenClaw Has**: Single WS gateway for all clients/channels
   - **PicoClaw Has**: Direct channel connections (simpler)
   - **Recommendation**: Implement lightweight gateway inspired by PicoClaw's simplicity

2. **Multi-Channel Support**
   - **Missing**: WhatsApp, Slack, Signal, iMessage, Teams, Matrix
   - **Impact**: Limited messaging platform coverage
   - **OpenClaw Has**: 12+ channels with full feature parity
   - **PicoClaw Has**: 5 channels (Telegram, Discord, QQ, DingTalk, LINE)
   - **Recommendation**: Add WhatsApp (Baileys) and Slack (Bolt SDK)

3. **Security Sandbox**
   - **Missing**: Workspace restriction, command blocking
   - **Impact**: Full system access is security risk
   - **OpenClaw Has**: Docker per-session sandboxes
   - **PicoClaw Has**: Workspace-restricted tools with command blocking
   - **Recommendation**: Implement PicoClaw's workspace restriction model

4. **Skills/Plugin System**
   - **Missing**: Skill registry, dynamic skill loading
   - **Impact**: Manual skill management
   - **OpenClaw Has**: ClawHub registry with auto-install
   - **PicoClaw Has**: Workspace skills directory
   - **Recommendation**: Build MCP-based skill system with registry

5. **Agent-to-Agent Communication**
   - **Missing**: Structured inter-agent messaging
   - **Impact**: Limited multi-agent coordination
   - **OpenClaw Has**: sessions_* tools (list/history/send/spawn)
   - **PicoClaw Has**: spawn + message tools
   - **Recommendation**: Implement spawn + message pattern

### 4.2 Important Gaps (Medium Priority)

6. **Heartbeat System**
   - **Missing**: Periodic task execution
   - **Impact**: No autonomous background work
   - **OpenClaw/PicoClaw Have**: 30min heartbeat with HEARTBEAT.md
   - **Recommendation**: Add APScheduler-based heartbeat

7. **OAuth Provider Support**
   - **Missing**: OAuth for Anthropic/OpenAI
   - **Impact**: API key management burden
   - **OpenClaw Has**: Full OAuth + rotation
   - **PicoClaw Has**: Anthropic OAuth
   - **Recommendation**: Add OAuth support for major providers

8. **Voice Integration**
   - **Missing**: Voice wake, TTS, STT
   - **Impact**: No voice interaction
   - **OpenClaw Has**: Voice Wake + Talk Mode (ElevenLabs)
   - **PicoClaw Has**: Groq Whisper transcription
   - **Recommendation**: Add Groq Whisper + ElevenLabs TTS

9. **Hot Reload**
   - **Missing**: Config changes require restart
   - **Impact**: Downtime for config updates
   - **OpenClaw Has**: Hybrid hot reload (most fields)
   - **PicoClaw Has**: N/A (Go limitation)
   - **Recommendation**: Implement Python-based config watcher

10. **Usage Tracking**
    - **Missing**: Token/cost reporting
    - **Impact**: No visibility into LLM costs
    - **OpenClaw Has**: Per-session usage tracking
    - **Recommendation**: Add token counting and cost estimation

### 4.3 Nice-to-Have Gaps (Low Priority)

11. **Canvas/UI System**
    - **Missing**: Agent-driven UI
    - **OpenClaw Has**: A2UI with Canvas API
    - **Recommendation**: Low priority (complex to implement)

12. **Nodes System**
    - **Missing**: Device pairing and remote execution
    - **OpenClaw Has**: Bonjour discovery + remote nodes
    - **Recommendation**: Low priority (use SSH/tunnels instead)

13. **Gmail Pub/Sub**
    - **Missing**: Email triggers
    - **OpenClaw Has**: GCP Pub/Sub integration
    - **Recommendation**: Add IMAP polling as simpler alternative

14. **Model Failover**
    - **Missing**: Automatic fallback
    - **OpenClaw/PicoClaw Have**: Provider failover
    - **Recommendation**: Add retry logic with fallback models

15. **ClawHub-style Registry**
    - **Missing**: Central skill registry
    - **OpenClaw Has**: ClawHub.com
    - **Recommendation**: Build MCP registry or integrate with existing

---

## 5. Key Architectural Decisions

### 5.1 OpenClaw's Design Philosophy

**Strengths**:
- **Comprehensive**: Production-grade multi-channel support
- **Extensible**: Skills, nodes, canvas, webhooks
- **Secure**: Sandbox modes, pairing, OAuth
- **Developer-friendly**: Hot reload, monorepo, TypeScript safety

**Trade-offs**:
- **Resource-intensive**: >1GB RAM, Node.js dependency
- **Complex**: Large codebase, many moving parts
- **Slow startup**: >500s on low-end hardware
- **Platform-specific**: macOS/iOS apps, macOS permissions

**Best For**:
- Power users with modern hardware
- Enterprise deployments
- Feature-rich personal assistants
- macOS/iOS ecosystem

### 5.2 PicoClaw's Design Philosophy

**Strengths**:
- **Minimal**: <10MB RAM, single binary
- **Fast**: 1s boot, instant commands
- **Portable**: RISC-V/ARM/x86, $10 hardware
- **Simple**: Easy to understand and modify

**Trade-offs**:
- **Limited channels**: 5 vs 12+ in OpenClaw
- **No hot reload**: Go limitation
- **Basic features**: No voice, canvas, nodes
- **Young project**: Still maturing

**Best For**:
- Embedded/edge devices
- Resource-constrained environments
- Simple automation tasks
- Cost-sensitive deployments

### 5.3 Recommended Approach for Wingman

**Hybrid Philosophy**:
1. **Core from PicoClaw**: Lightweight, workspace-restricted, sandboxed
2. **Features from OpenClaw**: Multi-channel, OAuth, heartbeat, skills
3. **Python Advantages**: Rich ecosystem, MCP integration, familiar syntax

**Architecture Recommendations**:

1. **Gateway Design**: Implement lightweight event bus (not full WebSocket)
   - Use Python `asyncio` for concurrent channel handling
   - Simple pub/sub for agent-to-agent communication
   - File-based state (like PicoClaw), not in-memory

2. **Security Model**: Adopt PicoClaw's workspace restriction
   - Sandbox all tools to workspace directory
   - Block dangerous commands (rm -rf, etc.)
   - Add opt-in for system-wide access

3. **Provider System**: Model-centric config (PicoClaw style)
   - Support OpenClaw's OAuth flows
   - Add load balancing and failover
   - Track usage and costs

4. **Channel System**: Prioritize high-value channels
   - WhatsApp (Baileys port or API)
   - Telegram (python-telegram-bot)
   - Discord (discord.py)
   - Slack (slack-sdk)
   - WebChat (existing)

5. **Skills System**: MCP-first with workspace fallback
   - MCP servers for complex skills
   - Workspace SKILL.md files for simple skills
   - Skill registry (JSON file, not ClawHub initially)

6. **Heartbeat**: APScheduler-based
   - Read HEARTBEAT.md every 30min
   - Support spawn-style async tasks
   - Graceful failure handling

7. **Memory**: Keep MemGPT-style segments
   - Add MEMORY.md file for persistence
   - Session transcripts in `sessions/`
   - Cross-session access via tools

---

## 6. Prioritized Implementation Roadmap

### Phase 1: Security & Foundation (Week 1-2)

**Goal**: Make Wingman secure and reliable

1. **Workspace Sandboxing** (HIGH PRIORITY)
   - Add `restrict_to_workspace` config option
   - Implement path validation for all file tools
   - Block dangerous exec commands
   - Test with malicious prompts

2. **Provider OAuth** (HIGH PRIORITY)
   - Add Anthropic OAuth support
   - Implement token refresh logic
   - Support API key fallback

3. **Agent Files Standardization** (MEDIUM PRIORITY)
   - Add SOUL.md, IDENTITY.md, HEARTBEAT.md
   - Document file format and usage
   - Auto-create on workspace init

**Deliverables**:
- Secure-by-default workspace restriction
- OAuth support for Anthropic
- Complete agent workspace template

### Phase 2: Multi-Agent & Communication (Week 3-4)

**Goal**: Enable sophisticated agent coordination

1. **Spawn Tool** (HIGH PRIORITY)
   - Implement subagent spawning
   - Add message tool for subagent→user communication
   - Async task execution

2. **Sessions Tools** (HIGH PRIORITY)
   - `sessions_list` - List active agents
   - `sessions_history` - Fetch transcripts
   - `sessions_send` - Inter-agent messaging

3. **Heartbeat System** (MEDIUM PRIORITY)
   - APScheduler integration
   - HEARTBEAT.md parser
   - 30min default interval
   - Spawn integration for async tasks

**Deliverables**:
- Multi-agent coordination tools
- Autonomous heartbeat execution
- Subagent spawn/message system

### Phase 3: Channel Expansion (Week 5-6)

**Goal**: Match OpenClaw's channel coverage

1. **WhatsApp Integration** (HIGH PRIORITY)
   - Research Baileys Python alternatives
   - Implement QR pairing
   - Add allowlist support

2. **Slack Integration** (MEDIUM PRIORITY)
   - slack-sdk integration
   - Bot + app token auth
   - Thread support

3. **Voice Support** (MEDIUM PRIORITY)
   - Groq Whisper for STT
   - ElevenLabs for TTS
   - Telegram voice message transcription

**Deliverables**:
- WhatsApp channel (if feasible)
- Slack channel
- Voice transcription for Telegram

### Phase 4: Skills & Ecosystem (Week 7-8)

**Goal**: Build extensible skill system

1. **Skill Registry** (MEDIUM PRIORITY)
   - JSON-based skill catalog
   - Skill metadata (SKILL.md frontmatter)
   - Install/uninstall commands

2. **MCP Skill Bridge** (HIGH PRIORITY)
   - Auto-discover MCP servers
   - Convert MCP tools to Wingman tools
   - Skill-level sandboxing

3. **ClawdChat Integration** (LOW PRIORITY)
   - Read skill.md from clawdchat.ai
   - Agent social network support

**Deliverables**:
- Skill registry with 10+ bundled skills
- MCP server auto-discovery
- ClawdChat compatibility

### Phase 5: Operations & Polish (Week 9-10)

**Goal**: Production-ready deployment

1. **Hot Reload** (MEDIUM PRIORITY)
   - Watchdog for config file
   - Reload channels/agents without restart
   - Graceful degradation

2. **Usage Tracking** (MEDIUM PRIORITY)
   - Token counting per-session
   - Cost estimation
   - `/status` command output

3. **Doctor/Health Commands** (MEDIUM PRIORITY)
   - `wingman doctor` - Config validation
   - `wingman health` - System status
   - Auto-fix common issues

4. **Deployment Guides** (LOW PRIORITY)
   - Docker Compose
   - Systemd service
   - Raspberry Pi guide

**Deliverables**:
- Hot reload for config changes
- Usage/cost tracking
- Production deployment guides

### Phase 6: Advanced Features (Week 11-12)

**Goal**: Differentiate Wingman from OpenClaw/PicoClaw

1. **Hybrid Memory System** (HIGH PRIORITY)
   - Combine MemGPT + MEMORY.md
   - Smart context pruning
   - Cross-session memory search

2. **Browser MCP Integration** (MEDIUM PRIORITY)
   - Enhance BrowserUse integration
   - Add screenshot/snapshot tools
   - Workflow recording

3. **Email Triggers** (LOW PRIORITY)
   - IMAP polling
   - Email→task automation
   - Pub/Sub for Gmail (optional)

4. **Model Failover** (MEDIUM PRIORITY)
   - Retry logic with exponential backoff
   - Automatic fallback to secondary model
   - Provider rotation

**Deliverables**:
- Production-grade memory system
- Enhanced browser automation
- Reliable model failover

---

## 7. Specific Recommendations

### 7.1 Architecture Changes

**Recommendation 1: Adopt PicoClaw's Workspace Restriction**
```python
# config/settings.py
class AgentConfig:
    workspace: str = "~/.wingman/workspace"
    restrict_to_workspace: bool = True  # Default secure
    
# src/tools/filesystem.py
def validate_path(path: str, workspace: str, restrict: bool) -> bool:
    if not restrict:
        return True
    resolved = Path(path).resolve()
    workspace_resolved = Path(workspace).resolve()
    return str(resolved).startswith(str(workspace_resolved))
```

**Recommendation 2: Implement Spawn Tool**
```python
# src/tools/subagent.py
async def spawn(task: str, context: dict) -> str:
    """Spawn async subagent for long-running task"""
    subagent_id = generate_id()
    asyncio.create_task(run_subagent(subagent_id, task, context))
    return f"Spawned subagent {subagent_id} for: {task}"

async def run_subagent(id: str, task: str, context: dict):
    agent = create_agent(id, context)
    result = await agent.run(task)
    await message_user(result)  # Direct communication
```

**Recommendation 3: Add Heartbeat System**
```python
# src/core/heartbeat.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class HeartbeatManager:
    def __init__(self, workspace: str, interval_minutes: int = 30):
        self.workspace = workspace
        self.scheduler = AsyncIOScheduler()
        
    async def check_heartbeat(self):
        heartbeat_file = f"{self.workspace}/HEARTBEAT.md"
        if not os.path.exists(heartbeat_file):
            return
        
        tasks = parse_heartbeat(heartbeat_file)
        for task in tasks:
            if task.is_async:
                await spawn(task.description, {})
            else:
                await run_quick_task(task.description)
```

**Recommendation 4: Model-Centric Provider Config**
```python
# config/models.yaml
model_list:
  - model_name: "claude-sonnet-4.6"
    model: "anthropic/claude-sonnet-4.6"
    api_key: "${ANTHROPIC_API_KEY}"
    auth_method: "oauth"  # or "api_key"
    
  - model_name: "gpt-5.2"
    model: "openai/gpt-5.2"
    api_key: "${OPENAI_API_KEY}"
    
  - model_name: "gpt-5.2-fallback"
    model: "openai/gpt-5.2"
    api_base: "https://backup.openai.com/v1"
    api_key: "${OPENAI_BACKUP_KEY}"
    
agents:
  defaults:
    model: "claude-sonnet-4.6"
    fallback_models: ["gpt-5.2", "gpt-5.2-fallback"]
```

**Recommendation 5: Sessions Tools**
```python
# src/tools/sessions.py
def sessions_list() -> list[dict]:
    """List all active agent sessions"""
    return [
        {"id": s.id, "name": s.name, "active": s.active}
        for s in get_all_sessions()
    ]

def sessions_history(session_id: str, limit: int = 50) -> list[dict]:
    """Fetch transcript for a session"""
    session = get_session(session_id)
    return session.get_history(limit)

async def sessions_send(
    session_id: str, 
    message: str,
    reply_back: bool = False,
    announce: bool = True
) -> str:
    """Send message to another session"""
    session = get_session(session_id)
    await session.send_message(message, reply_back, announce)
```

### 7.2 Code Structure Changes

**Recommendation 6: Reorganize to Match OpenClaw/PicoClaw**
```
wingman/
├── src/
│   ├── core/
│   │   ├── gateway.py       # Event bus (lightweight)
│   │   ├── session.py       # Session management
│   │   ├── heartbeat.py     # Heartbeat system
│   │   └── runtime.py       # Agent runtime
│   ├── agents/
│   │   ├── base.py          # Base agent
│   │   ├── coding/          # Coding agents
│   │   ├── research.py      # Research agent
│   │   └── router.py        # Multi-agent router
│   ├── channels/
│   │   ├── base.py          # Base channel
│   │   ├── telegram.py      # Telegram
│   │   ├── discord.py       # Discord
│   │   ├── whatsapp.py      # WhatsApp (new)
│   │   ├── slack.py         # Slack (new)
│   │   └── webchat.py       # WebChat
│   ├── tools/
│   │   ├── registry.py      # Tool registration
│   │   ├── filesystem.py    # File operations
│   │   ├── shell.py         # Shell execution
│   │   ├── web_search.py    # Web search
│   │   ├── browser_use.py   # Browser MCP
│   │   ├── sessions.py      # Inter-agent tools (new)
│   │   ├── spawn.py         # Subagent spawn (new)
│   │   └── cron.py          # Scheduled tasks
│   ├── providers/
│   │   ├── base.py          # Base provider
│   │   ├── openai.py        # OpenAI
│   │   ├── anthropic.py     # Anthropic with OAuth
│   │   ├── gemini.py        # Gemini
│   │   └── manager.py       # Provider manager + failover
│   ├── memory/
│   │   ├── manager.py       # Memory manager
│   │   ├── segments.py      # MemGPT segments
│   │   ├── memory_md.py     # MEMORY.md handler (new)
│   │   └── search.py        # Memory search
│   ├── skills/
│   │   ├── registry.py      # Skill catalog (new)
│   │   ├── loader.py        # Skill loader
│   │   └── manager.py       # Skill manager
│   └── config/
│       ├── settings.py      # Settings model
│       └── validator.py     # Config validation
└── workspace/               # Default workspace template
    ├── AGENTS.md
    ├── SOUL.md
    ├── IDENTITY.md
    ├── TOOLS.md
    ├── USER.md
    ├── HEARTBEAT.md         # New
    ├── MEMORY.md            # New
    ├── sessions/
    ├── memory/
    ├── cron/
    └── skills/
```

**Recommendation 7: Config Migration to model_list**
```yaml
# OLD (current Wingman)
providers:
  openai:
    api_key: "sk-..."
    model: "gpt-4"
    
agents:
  defaults:
    provider: "openai"

# NEW (PicoClaw-style)
model_list:
  - model_name: "gpt-4"
    model: "openai/gpt-4"
    api_key: "sk-..."
    
agents:
  defaults:
    model: "gpt-4"
```

### 7.3 Feature Implementation Priority

**High Priority (Implement First)**:
1. Workspace sandboxing (security)
2. Spawn + message tools (multi-agent)
3. Sessions tools (inter-agent communication)
4. Heartbeat system (autonomous tasks)
5. OAuth for Anthropic (better auth)

**Medium Priority (Implement Second)**:
6. WhatsApp channel (major platform)
7. Slack channel (enterprise)
8. Voice transcription (Groq Whisper)
9. Hot reload (ops convenience)
10. Usage tracking (cost visibility)

**Low Priority (Implement Later)**:
11. ClawdChat integration (ecosystem)
12. Email triggers (automation)
13. Model failover (reliability)
14. Canvas/UI (complex, low ROI)
15. Nodes system (use SSH instead)

---

## 8. Code Examples from OpenClaw/PicoClaw

### 8.1 OpenClaw: Session Management

```typescript
// Gateway session state
interface SessionState {
  thinkingLevel: "off" | "minimal" | "low" | "medium" | "high" | "xhigh";
  verboseLevel: boolean;
  model: string;
  sendPolicy: string;
  groupActivation: "mention" | "always";
  elevatedBash: boolean;
}

// WebSocket protocol
interface WSRequest {
  type: "req";
  id: string;
  method: "agent" | "send" | "health" | "status";
  params: any;
}

interface WSResponse {
  type: "res";
  id: string;
  ok: boolean;
  payload?: any;
  error?: string;
}

interface WSEvent {
  type: "event";
  event: "presence" | "tick" | "agent" | "shutdown";
  payload: any;
  seq?: number;
  stateVersion?: number;
}
```

### 8.2 PicoClaw: Workspace Restriction

```go
// pkg/tools/filesystem.go
func validatePath(path, workspace string, restrict bool) error {
    if !restrict {
        return nil
    }
    
    absPath, err := filepath.Abs(path)
    if err != nil {
        return fmt.Errorf("invalid path: %w", err)
    }
    
    absWorkspace, err := filepath.Abs(workspace)
    if err != nil {
        return fmt.Errorf("invalid workspace: %w", err)
    }
    
    if !strings.HasPrefix(absPath, absWorkspace) {
        return fmt.Errorf("path outside workspace: %s", absPath)
    }
    
    return nil
}

// Dangerous command blocking
var dangerousPatterns = []string{
    "rm -rf", "del /f", "rmdir /s",
    "format", "mkfs", "diskpart",
    "dd if=", "/dev/sd",
    "shutdown", "reboot", "poweroff",
    ":(){ :|:& };:",  // fork bomb
}

func checkDangerousCommand(cmd string) error {
    for _, pattern := range dangerousPatterns {
        if strings.Contains(cmd, pattern) {
            return fmt.Errorf("dangerous command blocked: %s", pattern)
        }
    }
    return nil
}
```

### 8.3 PicoClaw: Heartbeat System

```go
// pkg/core/heartbeat.go
type HeartbeatManager struct {
    workspace string
    interval  time.Duration
    agent     *Agent
}

func (h *HeartbeatManager) Start() {
    ticker := time.NewTicker(h.interval)
    go func() {
        for range ticker.C {
            h.check()
        }
    }()
}

func (h *HeartbeatManager) check() {
    heartbeatPath := filepath.Join(h.workspace, "HEARTBEAT.md")
    content, err := os.ReadFile(heartbeatPath)
    if err != nil {
        return // No heartbeat file
    }
    
    tasks := parseHeartbeat(string(content))
    for _, task := range tasks {
        if task.IsAsync {
            h.spawnSubagent(task.Description)
        } else {
            h.runQuickTask(task.Description)
        }
    }
}
```

### 8.4 OpenClaw: Agent-to-Agent Tools

```typescript
// sessions_list tool
{
  name: "sessions_list",
  description: "List all active agent sessions",
  inputSchema: {
    type: "object",
    properties: {},
  },
  handler: async () => {
    const sessions = await sessionManager.list();
    return sessions.map(s => ({
      id: s.id,
      name: s.name,
      active: s.active,
      lastActivity: s.lastActivity,
    }));
  },
}

// sessions_send tool
{
  name: "sessions_send",
  description: "Send message to another agent session",
  inputSchema: {
    type: "object",
    properties: {
      sessionId: { type: "string" },
      message: { type: "string" },
      replyBack: { type: "boolean", default: false },
      announce: { type: "boolean", default: true },
    },
    required: ["sessionId", "message"],
  },
  handler: async ({ sessionId, message, replyBack, announce }) => {
    const session = await sessionManager.get(sessionId);
    await session.sendMessage(message, { replyBack, announce });
    return { status: "sent", sessionId };
  },
}
```

### 8.5 PicoClaw: Model-Centric Config

```go
// pkg/providers/manager.go
type ModelConfig struct {
    ModelName  string `json:"model_name"`
    Model      string `json:"model"`      // vendor/model format
    APIKey     string `json:"api_key"`
    APIBase    string `json:"api_base"`
    AuthMethod string `json:"auth_method"` // "api_key" or "oauth"
}

type ProviderManager struct {
    models map[string][]ModelConfig  // Round-robin per model name
    index  map[string]int            // Current index for load balancing
}

func (pm *ProviderManager) GetProvider(modelName string) (Provider, error) {
    configs := pm.models[modelName]
    if len(configs) == 0 {
        return nil, fmt.Errorf("no config for model: %s", modelName)
    }
    
    // Round-robin load balancing
    idx := pm.index[modelName]
    config := configs[idx]
    pm.index[modelName] = (idx + 1) % len(configs)
    
    // Route by vendor prefix
    vendor := strings.Split(config.Model, "/")[0]
    return pm.createProvider(vendor, config)
}
```

---

## 9. Conclusion

### 9.1 Key Takeaways

**OpenClaw** is a production-grade, feature-rich framework that sets the standard for multi-channel AI assistants. Its Gateway architecture, comprehensive channel support, and sophisticated agent system make it ideal for power users and enterprise deployments. However, its resource requirements (>1GB RAM) and complexity limit its applicability to embedded/edge scenarios.

**PicoClaw** demonstrates that the core AI assistant functionality can be delivered in <10MB RAM with a 1s boot time, making it viable for $10 hardware. Its Go implementation, workspace restriction, and model-centric configuration provide a compelling alternative for resource-constrained environments. The AI-bootstrapped development approach is innovative and shows the future of agent-assisted programming.

**Wingman** can leverage insights from both projects:
- **From OpenClaw**: Multi-channel support, OAuth, heartbeat, skills registry, agent-to-agent tools
- **From PicoClaw**: Workspace sandboxing, model-centric config, spawn pattern, minimal dependencies
- **Python Strengths**: Rich ecosystem, MCP integration, familiar syntax, rapid iteration

### 9.2 Recommended Next Steps

1. **Immediate (Week 1-2)**:
   - Implement workspace sandboxing (security first!)
   - Add spawn + message tools
   - Create HEARTBEAT.md support

2. **Short-term (Week 3-6)**:
   - Build sessions_* tools for inter-agent communication
   - Add OAuth for Anthropic/OpenAI
   - Integrate WhatsApp and Slack channels

3. **Medium-term (Week 7-10)**:
   - Develop skill registry with MCP integration
   - Implement hot reload for config changes
   - Add usage tracking and cost reporting

4. **Long-term (Week 11-12)**:
   - Enhance memory system (MemGPT + MEMORY.md)
   - Build model failover and load balancing
   - Create production deployment guides

### 9.3 Differentiation Strategy

**Wingman should differentiate by**:
1. **Best-in-class MCP integration**: Leverage MCP ecosystem that OpenClaw/PicoClaw lack
2. **Hybrid memory**: Combine MemGPT's sophisticated memory with simple MEMORY.md persistence
3. **Python ecosystem**: Easy integration with ML/AI libraries, FastAPI, asyncio
4. **Balanced approach**: More features than PicoClaw, lighter than OpenClaw
5. **Developer-friendly**: Clear code, good docs, easy to extend

**Avoid competing on**:
- Resource efficiency (PicoClaw wins)
- Feature completeness (OpenClaw wins)
- Platform-specific apps (OpenClaw has Swift iOS/macOS apps)

**Focus on**:
- Cross-platform Python simplicity
- MCP-first architecture
- Research/coding agent specialization
- Easy self-hosting
- Strong defaults with optional complexity

---

## Appendix A: Resource Links

**OpenClaw**:
- GitHub: https://github.com/openclaw/openclaw
- Docs: https://docs.openclaw.ai/
- Website: https://openclaw.ai/
- Discord: https://discord.gg/clawd
- ClawHub: https://clawhub.com/
- Stars: 213k
- Contributors: 705
- Language: TypeScript (84.4%)

**PicoClaw**:
- GitHub: https://github.com/sipeed/picoclaw
- Website: https://picoclaw.io/
- Company: https://sipeed.com/
- Discord: https://discord.gg/V4sAZ9XWpN
- Stars: 16.6k
- Contributors: 66
- Language: Go (98.8%)

**Related Projects**:
- nanobot: https://github.com/HKUDS/nanobot (Python, inspired PicoClaw)
- ClawdChat: https://clawdchat.ai/ (Agent social network)
- awesome-openclaw-skills: https://github.com/VoltAgent/awesome-openclaw-skills
- Pi agent runtime: https://github.com/badlogic/pi-mono

---

## Appendix B: Comparison Tables

### B.1 Channel Support Comparison

| Channel | OpenClaw | PicoClaw | Wingman | Priority for Wingman |
|---------|----------|----------|---------|---------------------|
| WhatsApp | ✅ Baileys | ❌ | ❌ | HIGH |
| Telegram | ✅ grammY | ✅ | ✅ | ✅ |
| Discord | ✅ discord.js | ✅ | ✅ | ✅ |
| Slack | ✅ Bolt SDK | ❌ | ❌ | HIGH |
| Signal | ✅ signal-cli | ❌ | ❌ | MEDIUM |
| Google Chat | ✅ Chat API | ❌ | ❌ | LOW |
| Teams | ✅ Bot Framework | ❌ | ❌ | LOW |
| iMessage | ✅ BlueBubbles | ❌ | ❌ | LOW |
| Matrix | ✅ | ❌ | ❌ | LOW |
| WebChat | ✅ Built-in | ❌ | ✅ | ✅ |
| QQ | ❌ | ✅ | ❌ | LOW |
| DingTalk | ❌ | ✅ | ❌ | LOW |
| LINE | ❌ | ✅ | ❌ | LOW |

### B.2 Tool Comparison

| Tool | OpenClaw | PicoClaw | Wingman | Implementation Priority |
|------|----------|----------|---------|------------------------|
| File Read/Write | ✅ | ✅ Sandboxed | ✅ | Add sandboxing (HIGH) |
| Shell Exec | ✅ Elevated | ✅ Sandboxed | ✅ | Add sandboxing (HIGH) |
| Web Search | ❌ | ✅ Brave/DDG | ✅ Brave | ✅ |
| Browser Control | ✅ CDP | ❌ | ✅ BrowserUse | ✅ |
| Canvas/UI | ✅ A2UI | ❌ | ❌ | LOW |
| Camera | ✅ Nodes | ❌ | ✅ Desktop | ✅ |
| Screen Capture | ✅ Nodes | ❌ | ✅ Desktop | ✅ |
| Location | ✅ Nodes | ❌ | ❌ | LOW |
| Notifications | ✅ Multi-platform | ❌ | ✅ macOS | MEDIUM |
| Cron/Scheduling | ✅ Database | ✅ File-based | ✅ APScheduler | ✅ |
| Sessions Tools | ✅ list/history/send | ❌ | ❌ | HIGH |
| Spawn Subagent | ✅ sessions_spawn | ✅ spawn | ❌ | HIGH |
| Message Tool | ❌ | ✅ | ❌ | HIGH |
| Heartbeat | ✅ 30min | ✅ 30min | ❌ | HIGH |

### B.3 Provider Comparison

| Provider | OpenClaw | PicoClaw | Wingman | Priority |
|----------|----------|----------|---------|----------|
| OpenAI | ✅ OAuth | ✅ API | ✅ API | Add OAuth (HIGH) |
| Anthropic | ✅ OAuth | ✅ OAuth | ✅ API | Add OAuth (HIGH) |
| Gemini | ❌ | ✅ | ✅ | ✅ |
| Zhipu (GLM) | ❌ | ✅ | ❌ | LOW |
| DeepSeek | ❌ | ✅ | ❌ | LOW |
| Groq | ❌ | ✅ | ❌ | MEDIUM (for Whisper) |
| Ollama | ❌ | ✅ | ✅ | ✅ |
| OpenRouter | ✅ | ✅ | ❌ | MEDIUM |
| Kimi | ❌ | ❌ | ✅ | ✅ |
| Failover | ✅ | ✅ | ❌ | HIGH |
| Load Balancing | ❌ | ✅ Round-robin | ❌ | MEDIUM |
| Cost Tracking | ✅ | ❌ | ❌ | MEDIUM |

---

**End of Research Report**
