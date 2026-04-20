# Bugs and Issues — status as of 2026-04-20

Most of the "critical" items below were already fixed in the code by the
time of review. Status legend: ✅ resolved, ⏳ open, 🟡 partial/by-design.

## Critical Bugs

### 1. Vector Store Division by Zero ✅
**File**: `src/retrieval/vector_store.py`
`_cosine_similarity()` guards `norm_a == 0 or norm_b == 0 → 0.0`.

### 2. Empty File Handling in Document Loader ✅
**File**: `src/ingestion/loader.py`
Empty content is short-circuited before chunking.

### 3. Session Memory Leak ✅
**File**: `src/gateway/session.py`
Sessions have explicit cleanup via the session manager.

### 4. Missing File Extension Check in Upload ✅
**File**: `src/gateway/server.py`
Extension is validated on upload.

### 5. WebSocket Connection Not Properly Closed 🟡
**File**: `src/gateway/server.py`
`process_file_with_progress()` is still defined inside the WS handler; it
closes over `websocket` + loop-local state so moving it out requires
explicit param threading. Not a functional bug — left as a style nit.

### 6. Provider Health Check Can Block Event Loop ✅
**File**: `src/providers/manager.py`
Health checks use `asyncio.gather` across providers.

### 7. Large File Memory Issue ✅
**File**: `src/ingestion/loader.py`
File size is capped; larger files are rejected early.

### 8. Embeddings Model Load Blocks Event Loop ✅
**File**: `src/retrieval/embeddings.py`
Model load is wrapped in `asyncio.to_thread()` / called once at startup.

### 9. Shell Command Injection Risk ✅
**File**: `src/tools/shell.py`
Blocked-command list + optional `strict_whitelist` mode (config:
`tools.shell.strict_whitelist`). When enabled and `"*"` is not in the
allowlist, only first-word matches in `allowed_commands` are permitted.

### 10. Tool Execution Missing Timeout ✅
**File**: `src/tools/registry.py`
5-minute default timeout via `asyncio.wait_for(..., timeout=TOOL_TIMEOUT)`.

## Medium Priority

### 11. Web Search Error Handling ✅
**File**: `src/tools/web_search.py`
3-attempt retry with exponential backoff.

### 12. Missing httpx Dependency Check ⏳
**File**: `src/tools/web_search.py`
Imports still raise if `ddgs`/`duckduckgo_search` are missing. Low-priority
— both extras are in `pyproject.toml`.

### 13. File Path Traversal ✅
**File**: `src/tools/filesystem.py`
All paths validated via `src/security/` workspace sandboxing.

### 14. Transcript Logger File Lock ✅
**File**: `src/memory/transcript.py`
Single-writer async queue serializes writes.

### 15. JSON Serialization Error ✅
**File**: `src/retrieval/vector_store.py`
`_save_collection` now uses atomic tmp-file writes + a `default=_safe_default`
fallback that logs the offending value and stringifies it.

### 16. Webchat Context Injection Timing ⏳
**File**: `src/channels/webchat.py`
Still a hard-coded 5-minute window. Open.

### 17. Missing Error Response for WebSocket ⏳
**File**: `src/gateway/server.py`
Some exception paths still don't send a structured error to the client.

## Low Priority (Improvements)

### 18. Hard-coded Paths ✅
**File**: various
Centralized in [src/config/paths.py](src/config/paths.py). New code should
import from there instead of rebuilding `Path.home() / ".wingman" / ...`.

### 19. Logging Inconsistency 🟡
**File**: various
Agent loop hot path now uses `logger`. Some `print()` calls remain in
non-hot paths (swarm scripts, legacy tools). Finish opportunistically.

### 20. Missing Type Hints ⏳
Ongoing. Picked up opportunistically during other edits.

### 21. Duplicate Code in Providers ✅
**File**: `src/providers/*.py`
Shared `OpenAICompatibleProvider` base class at
[src/providers/_openai_compat.py](src/providers/_openai_compat.py). New
Groq provider builds on it in ~12 lines. Existing `openai.py` / `kimi.py` /
`openrouter.py` still have their own implementations — fine to leave, but
migrating them is now a mechanical refactor.

### 22. No Connection Pooling ✅ (for new code)
**File**: `src/providers/_http.py`
Single shared `httpx.AsyncClient` singleton (50 max / 20 keepalive
connections, 120s timeout). Groq + `http_request` tool use it. Legacy
providers (openai.py, kimi.py, ollama.py) still own their clients — not a
bug, just an opportunity to consolidate later.
