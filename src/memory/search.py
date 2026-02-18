"""
Memory Search - Semantic search over past conversations.

Uses embeddings to find relevant context from:
- Past session messages
- Daily logs
- Memory files

Supports multiple embedding providers:
- OpenAI (text-embedding-3-small)
- Local (sentence-transformers)
"""

from __future__ import annotations

import json
import logging
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """A searchable memory entry."""
    id: str
    content: str
    source: str  # session_id, daily_log, memory_file
    timestamp: datetime
    embedding: list[float] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "embedding": self.embedding,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MemoryEntry:
        return cls(
            id=data["id"],
            content=data["content"],
            source=data["source"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            embedding=data.get("embedding", []),
            metadata=data.get("metadata", {}),
        )


class EmbeddingProvider:
    """Base class for embedding providers."""
    
    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    async def embed_single(self, text: str) -> list[float]:
        results = await self.embed([text])
        return results[0] if results else []


class OpenAIEmbeddings(EmbeddingProvider):
    """OpenAI embeddings provider."""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            import openai
            self._client = openai.AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        
        client = self._get_client()
        try:
            response = await client.embeddings.create(
                model=self.model,
                input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            return [[] for _ in texts]


class LocalEmbeddings(EmbeddingProvider):
    """Local embeddings using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                logger.error("sentence-transformers not installed")
                return None
        return self._model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        model = self._get_model()
        if model is None:
            return [[] for _ in texts]
        
        try:
            # Run in thread to avoid blocking
            embeddings = await asyncio.to_thread(
                model.encode, texts, convert_to_numpy=True
            )
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Local embedding error: {e}")
            return [[] for _ in texts]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0
    
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return dot_product / (norm_a * norm_b)


class MemorySearch:
    """
    Semantic search over memory.
    
    Indexes:
    - Session messages (conversation history)
    - Daily logs
    - Memory files (MEMORY.md)
    
    Uses a simple JSON-based storage for the index.
    For production, consider using a vector database.
    """

    def __init__(
        self,
        workspace: Path,
        embedding_provider: EmbeddingProvider | None = None,
    ):
        self.workspace = workspace
        self.index_path = workspace / ".memory_index.json"
        self.embedding_provider = embedding_provider
        self._entries: dict[str, MemoryEntry] = {}
        self._load_index()

    def _load_index(self) -> None:
        """Load the memory index from disk."""
        if self.index_path.exists():
            try:
                with open(self.index_path, "r") as f:
                    data = json.load(f)
                for entry_data in data.get("entries", []):
                    entry = MemoryEntry.from_dict(entry_data)
                    self._entries[entry.id] = entry
                logger.info(f"Loaded {len(self._entries)} memory entries")
            except Exception as e:
                logger.error(f"Failed to load memory index: {e}")

    def _save_index(self) -> None:
        """Save the memory index to disk."""
        try:
            data = {
                "entries": [e.to_dict() for e in self._entries.values()],
                "updated_at": datetime.now().isoformat(),
            }
            with open(self.index_path, "w") as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Failed to save memory index: {e}")

    def _generate_id(self, content: str, source: str) -> str:
        """Generate a unique ID for a memory entry."""
        hash_input = f"{source}:{content[:100]}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    async def add_entry(
        self,
        content: str,
        source: str,
        timestamp: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryEntry:
        """Add a new entry to the memory index."""
        entry_id = self._generate_id(content, source)
        
        # Skip if already exists
        if entry_id in self._entries:
            return self._entries[entry_id]
        
        # Generate embedding
        embedding = []
        if self.embedding_provider:
            embedding = await self.embedding_provider.embed_single(content)
        
        entry = MemoryEntry(
            id=entry_id,
            content=content,
            source=source,
            timestamp=timestamp or datetime.now(),
            embedding=embedding,
            metadata=metadata or {},
        )
        
        self._entries[entry_id] = entry
        self._save_index()
        
        return entry

    async def search(
        self,
        query: str,
        limit: int = 5,
        min_score: float = 0.5,
        source_filter: str | None = None,
    ) -> list[tuple[MemoryEntry, float]]:
        """
        Search for relevant memory entries.
        
        Returns list of (entry, score) tuples sorted by relevance.
        """
        if not self._entries:
            return []
        
        if not self.embedding_provider:
            # Fallback to keyword search
            return self._keyword_search(query, limit, source_filter)
        
        # Get query embedding
        query_embedding = await self.embedding_provider.embed_single(query)
        if not query_embedding:
            return self._keyword_search(query, limit, source_filter)
        
        # Calculate similarities
        results: list[tuple[MemoryEntry, float]] = []
        for entry in self._entries.values():
            if source_filter and not entry.source.startswith(source_filter):
                continue
            
            if not entry.embedding:
                continue
            
            score = cosine_similarity(query_embedding, entry.embedding)
            if score >= min_score:
                results.append((entry, score))
        
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:limit]

    def _keyword_search(
        self,
        query: str,
        limit: int,
        source_filter: str | None = None,
    ) -> list[tuple[MemoryEntry, float]]:
        """Simple keyword-based search fallback."""
        query_terms = query.lower().split()
        results: list[tuple[MemoryEntry, float]] = []
        
        for entry in self._entries.values():
            if source_filter and not entry.source.startswith(source_filter):
                continue
            
            content_lower = entry.content.lower()
            matches = sum(1 for term in query_terms if term in content_lower)
            if matches > 0:
                score = matches / len(query_terms)
                results.append((entry, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    async def index_session(self, session_path: Path) -> int:
        """Index messages from a session file."""
        if not session_path.exists():
            return 0
        
        try:
            with open(session_path, "r") as f:
                data = json.load(f)
            
            session_id = data.get("session_id", session_path.stem)
            count = 0
            
            for msg in data.get("messages", []):
                if msg.get("role") in ("user", "assistant"):
                    content = msg.get("content", "")
                    if len(content) > 50:  # Skip very short messages
                        await self.add_entry(
                            content=content[:1000],  # Truncate long messages
                            source=f"session:{session_id}",
                            timestamp=datetime.fromisoformat(
                                msg.get("timestamp", datetime.now().isoformat())
                            ),
                            metadata={"role": msg.get("role")},
                        )
                        count += 1
            
            return count
        except Exception as e:
            logger.error(f"Failed to index session {session_path}: {e}")
            return 0

    async def index_daily_logs(self) -> int:
        """Index all daily log files."""
        memory_dir = self.workspace / "memory"
        if not memory_dir.exists():
            return 0
        
        count = 0
        for log_path in memory_dir.glob("*.md"):
            try:
                content = log_path.read_text()
                # Split into chunks by timestamp
                chunks = content.split("\n[")
                for chunk in chunks:
                    if len(chunk) > 50:
                        await self.add_entry(
                            content=chunk[:500],
                            source=f"daily_log:{log_path.stem}",
                        )
                        count += 1
            except Exception as e:
                logger.error(f"Failed to index log {log_path}: {e}")
        
        return count

    async def rebuild_index(self) -> int:
        """Rebuild the entire memory index."""
        self._entries.clear()
        count = 0
        
        # Index sessions
        sessions_dir = self.workspace / "sessions"
        if sessions_dir.exists():
            for session_path in sessions_dir.glob("*.json"):
                count += await self.index_session(session_path)
        
        # Index daily logs
        count += await self.index_daily_logs()
        
        logger.info(f"Rebuilt memory index with {count} entries")
        return count

    def clear(self) -> None:
        """Clear the memory index."""
        self._entries.clear()
        if self.index_path.exists():
            self.index_path.unlink()
