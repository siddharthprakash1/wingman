# Bugs and Issues Found During Code Review

## Critical Bugs

### 1. Vector Store Division by Zero
**File**: `src/retrieval/vector_store.py`
**Issue**: `_cosine_similarity()` can divide by zero if either vector has zero norm
**Fix**: Add zero-check

### 2. Empty File Handling in Document Loader  
**File**: `src/ingestion/loader.py`
**Issue**: No check for empty files which will create empty chunks
**Fix**: Add empty content check

### 3. Session Memory Leak
**File**: `src/gateway/session.py`
**Issue**: Sessions accumulate in memory with no cleanup mechanism
**Fix**: Add session timeout/cleanup

### 4. Missing File Extension Check in Upload
**File**: `src/gateway/server.py`
**Issue**: File upload doesn't validate file extension before processing
**Fix**: Add extension validation

### 5. WebSocket Connection Not Properly Closed
**File**: `src/gateway/server.py`
**Issue**: `process_file_with_progress()` defined inside loop but connection not checked
**Fix**: Move function definition outside, add connection check

### 6. Provider Health Check Can Block Event Loop
**File**: `src/providers/manager.py`
**Issue**: Iterating through providers for health check is synchronous in async context
**Fix**: Use asyncio.gather for parallel health checks

### 7. Large File Memory Issue
**File**: `src/ingestion/loader.py`
**Issue**: Entire file content loaded into memory; large PDFs can cause OOM
**Fix**: Add file size limit check

### 8. Embeddings Model Load Blocks Event Loop
**File**: `src/retrieval/embeddings.py`
**Issue**: `_load_model()` is synchronous but called from async context
**Fix**: Use `asyncio.to_thread()` for model loading

### 9. Shell Command Injection Risk
**File**: `src/tools/shell.py`
**Issue**: No validation on shell commands - potential security risk
**Fix**: Add command whitelist/blacklist option

### 10. Tool Execution Missing Timeout
**File**: `src/tools/registry.py`
**Issue**: Tool execution has no timeout, can hang indefinitely
**Fix**: Add timeout wrapper

## Medium Priority

### 11. Web Search Error Handling
**File**: `src/tools/web_search.py`
**Issue**: DuckDuckGo rate limits not handled
**Fix**: Add retry logic with backoff

### 12. Missing httpx Dependency Check
**File**: `src/tools/web_search.py`
**Issue**: httpx import can fail but not handled gracefully
**Fix**: Add try-except for import

### 13. File Path Traversal
**File**: `src/tools/filesystem.py`
**Issue**: No check for path traversal attacks (../../etc/passwd)
**Fix**: Add path validation

### 14. Transcript Logger File Lock
**File**: `src/memory/transcript.py`
**Issue**: No file locking, concurrent writes can corrupt log
**Fix**: Add file locking or queue writes

### 15. JSON Serialization Error
**File**: `src/retrieval/vector_store.py`
**Issue**: `_save_collection()` can fail with non-serializable metadata
**Fix**: Add JSON serialization wrapper

### 16. Webchat Context Injection Timing
**File**: `src/channels/webchat.py`
**Issue**: 5-minute window for context injection is arbitrary and not configurable
**Fix**: Make configurable

### 17. Missing Error Response for WebSocket
**File**: `src/gateway/server.py`
**Issue**: Some exceptions don't send error to client
**Fix**: Add comprehensive error handling

## Low Priority (Improvements)

### 18. Hard-coded Paths
**File**: Various
**Issue**: `~/.wingman` path hard-coded in multiple places
**Fix**: Centralize path configuration

### 19. Logging Inconsistency
**File**: Various
**Issue**: Some modules use print(), some use logger
**Fix**: Standardize on logger

### 20. Missing Type Hints
**File**: Various
**Issue**: Some functions missing return type hints
**Fix**: Add type hints

### 21. Duplicate Code in Providers
**File**: `src/providers/*.py`
**Issue**: Message conversion logic duplicated across providers
**Fix**: Extract to base class

### 22. No Connection Pooling
**File**: `src/providers/openai.py`
**Issue**: HTTP client created per provider, no pooling
**Fix**: Consider shared connection pool
