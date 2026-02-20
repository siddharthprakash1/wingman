"""
Local Embeddings - Generate embeddings using local models.

Uses sentence-transformers for fast, local embedding generation
without API calls.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Singleton instance
_embeddings_instance: "LocalEmbeddings | None" = None


class LocalEmbeddings:
    """
    Generate embeddings using local sentence-transformers models.
    
    Default model: all-MiniLM-L6-v2 (fast, 384 dimensions)
    Alternative: all-mpnet-base-v2 (better quality, 768 dimensions)
    """
    
    # Popular models with their dimensions
    MODELS = {
        "all-MiniLM-L6-v2": 384,        # Fast, good quality
        "all-mpnet-base-v2": 768,        # Better quality
        "paraphrase-MiniLM-L6-v2": 384,  # Good for paraphrase
        "multi-qa-MiniLM-L6-cos-v1": 384, # Good for QA
    }
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str | None = None,
    ):
        self.model_name = model_name
        self.device = device
        self._model = None
        self._dimension = self.MODELS.get(model_name, 384)
    
    async def _load_model_async(self):
        """Async wrapper for lazy model loading to prevent blocking."""
        if self._model is None:
            # Load model in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_model_sync)
        return self._model
    
    def _load_model_sync(self):
        """Synchronous model loading (called from executor)."""
        if self._model is not None:
            return self._model
            
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. Run: pip install sentence-transformers"
            )
        
        logger.info(f"Loading embedding model: {self.model_name}")
        self._model = SentenceTransformer(self.model_name, device=self.device)
        logger.info(f"Model loaded. Dimension: {self._dimension}")
        return self._model
    
    def _load_model(self):
        """Lazy load the model (synchronous version)."""
        return self._load_model_sync()
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimension
    
    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text (synchronous)."""
        model = self._load_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    async def embed_async(self, text: str) -> list[float]:
        """Generate embedding for a single text (async, non-blocking)."""
        model = await self._load_model_async()
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: model.encode(text, convert_to_numpy=True)
        )
        return embedding.tolist()
    
    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Generate embeddings for multiple texts (synchronous)."""
        model = self._load_model()
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=len(texts) > 100,
            convert_to_numpy=True,
        )
        return embeddings.tolist()
    
    async def embed_batch_async(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Generate embeddings for multiple texts (async, non-blocking)."""
        model = await self._load_model_async()
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=len(texts) > 100,
                convert_to_numpy=True,
            )
        )
        return embeddings.tolist()
    
    def similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity between two texts."""
        model = self._load_model()
        embeddings = model.encode([text1, text2], convert_to_numpy=True)
        
        # Cosine similarity
        from numpy import dot
        from numpy.linalg import norm
        
        cos_sim = dot(embeddings[0], embeddings[1]) / (norm(embeddings[0]) * norm(embeddings[1]))
        return float(cos_sim)
    
    def get_model_info(self) -> dict[str, Any]:
        """Get information about the model."""
        return {
            "model_name": self.model_name,
            "dimension": self._dimension,
            "device": self.device or "auto",
            "loaded": self._model is not None,
        }


def get_embeddings(model_name: str = "all-MiniLM-L6-v2") -> LocalEmbeddings:
    """Get or create a singleton embeddings instance."""
    global _embeddings_instance
    
    if _embeddings_instance is None or _embeddings_instance.model_name != model_name:
        _embeddings_instance = LocalEmbeddings(model_name=model_name)
    
    return _embeddings_instance
