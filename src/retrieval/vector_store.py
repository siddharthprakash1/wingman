"""
Vector Store - JSON-file-based storage for document embeddings.

Provides semantic search over stored documents with metadata filtering.
Uses a simple file-based approach for Python 3.14 compatibility.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np

from src.retrieval.embeddings import LocalEmbeddings, get_embeddings

logger = logging.getLogger(__name__)

# Singleton instance
_vector_store_instance: "VectorStore | None" = None


class VectorStore:
    """
    File-based vector store for document embeddings.
    
    Features:
    - Local persistent storage (JSON files)
    - Automatic embedding generation
    - Semantic similarity search (cosine similarity)
    - Metadata filtering
    - Multiple collections
    """
    
    DEFAULT_COLLECTION = "documents"
    
    def __init__(
        self,
        persist_directory: str | Path | None = None,
        embeddings: LocalEmbeddings | None = None,
    ):
        self.persist_directory = Path(persist_directory or "~/.wingman/vector_store").expanduser()
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        self.embeddings = embeddings or get_embeddings()
        self._collections: dict[str, dict] = {}
    
    def _get_collection_path(self, name: str) -> Path:
        """Get path to collection file."""
        return self.persist_directory / f"{name}.json"
    
    def _load_collection(self, name: str) -> dict:
        """Load a collection from disk."""
        if name in self._collections:
            return self._collections[name]
        
        path = self._get_collection_path(name)
        if path.exists():
            with open(path, 'r') as f:
                self._collections[name] = json.load(f)
        else:
            self._collections[name] = {
                "documents": {},
                "metadata": {"dimension": self.embeddings.dimension},
            }
        
        return self._collections[name]
    
    def _save_collection(self, name: str) -> None:
        """Save a collection to disk."""
        if name not in self._collections:
            return
        
        path = self._get_collection_path(name)
        try:
            with open(path, 'w') as f:
                json.dump(self._collections[name], f, default=str)
        except Exception as e:
            logger.error(f"Failed to save collection {name}: {e}")
            raise
    
    def add(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
        doc_id: str | None = None,
        collection: str = DEFAULT_COLLECTION,
    ) -> str:
        """
        Add a single document to the store.
        
        Args:
            text: The text content
            metadata: Optional metadata dict
            doc_id: Optional document ID (auto-generated if not provided)
            collection: Collection name
            
        Returns:
            The document ID
        """
        coll = self._load_collection(collection)
        
        # Generate ID if not provided
        if not doc_id:
            doc_id = f"doc_{hash(text) % 1000000:06d}"
        
        # Generate embedding
        embedding = self.embeddings.embed(text)
        
        # Clean metadata
        clean_metadata = {}
        if metadata:
            for k, v in metadata.items():
                if isinstance(v, (str, int, float, bool)):
                    clean_metadata[k] = v
                elif v is not None:
                    clean_metadata[k] = str(v)
        
        coll["documents"][doc_id] = {
            "text": text,
            "embedding": embedding,
            "metadata": clean_metadata,
        }
        
        self._save_collection(collection)
        return doc_id
    
    def add_batch(
        self,
        texts: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        doc_ids: list[str] | None = None,
        collection: str = DEFAULT_COLLECTION,
    ) -> list[str]:
        """Add multiple documents in batch."""
        coll = self._load_collection(collection)
        
        # Generate IDs if not provided
        if not doc_ids:
            doc_ids = [f"doc_{hash(t) % 1000000:06d}_{i}" for i, t in enumerate(texts)]
        
        # Generate embeddings in batch
        embeddings = self.embeddings.embed_batch(texts)
        
        for i, (doc_id, text, embedding) in enumerate(zip(doc_ids, texts, embeddings)):
            clean_metadata = {}
            if metadatas and i < len(metadatas):
                for k, v in metadatas[i].items():
                    if isinstance(v, (str, int, float, bool)):
                        clean_metadata[k] = v
                    elif v is not None:
                        clean_metadata[k] = str(v)
            
            coll["documents"][doc_id] = {
                "text": text,
                "embedding": embedding,
                "metadata": clean_metadata,
            }
        
        self._save_collection(collection)
        return doc_ids
    
    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        a = np.array(a)
        b = np.array(b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        # Avoid division by zero
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        collection: str = DEFAULT_COLLECTION,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query text
            n_results: Number of results to return
            collection: Collection to search
            where: Metadata filter (e.g., {"source": "file.pdf"})
            where_document: Document content filter (not implemented)
            
        Returns:
            List of results with text, metadata, and score
        """
        coll = self._load_collection(collection)
        
        if not coll["documents"]:
            return []
        
        # Generate query embedding
        query_embedding = self.embeddings.embed(query)
        
        # Calculate similarities
        results = []
        for doc_id, doc in coll["documents"].items():
            # Apply metadata filter
            if where:
                match = True
                for key, value in where.items():
                    if doc["metadata"].get(key) != value:
                        match = False
                        break
                if not match:
                    continue
            
            similarity = self._cosine_similarity(query_embedding, doc["embedding"])
            results.append({
                "id": doc_id,
                "text": doc["text"],
                "metadata": doc["metadata"],
                "score": similarity,
                "distance": 1 - similarity,
            })
        
        # Sort by similarity (descending) and return top n
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:n_results]
    
    def delete(
        self,
        doc_ids: list[str] | None = None,
        where: dict[str, Any] | None = None,
        collection: str = DEFAULT_COLLECTION,
    ) -> None:
        """Delete documents by ID or filter."""
        coll = self._load_collection(collection)
        
        if doc_ids:
            for doc_id in doc_ids:
                coll["documents"].pop(doc_id, None)
        
        if where:
            to_delete = []
            for doc_id, doc in coll["documents"].items():
                match = True
                for key, value in where.items():
                    if doc["metadata"].get(key) != value:
                        match = False
                        break
                if match:
                    to_delete.append(doc_id)
            
            for doc_id in to_delete:
                coll["documents"].pop(doc_id, None)
        
        self._save_collection(collection)
    
    def get(
        self,
        doc_ids: list[str],
        collection: str = DEFAULT_COLLECTION,
    ) -> list[dict[str, Any]]:
        """Get documents by ID."""
        coll = self._load_collection(collection)
        
        results = []
        for doc_id in doc_ids:
            if doc_id in coll["documents"]:
                doc = coll["documents"][doc_id]
                results.append({
                    "id": doc_id,
                    "text": doc["text"],
                    "metadata": doc["metadata"],
                })
        
        return results
    
    def count(self, collection: str = DEFAULT_COLLECTION) -> int:
        """Get total document count in collection."""
        coll = self._load_collection(collection)
        return len(coll["documents"])
    
    def list_collections(self) -> list[str]:
        """List all collections."""
        collections = []
        for path in self.persist_directory.glob("*.json"):
            collections.append(path.stem)
        return collections
    
    def delete_collection(self, name: str) -> None:
        """Delete a collection."""
        path = self._get_collection_path(name)
        if path.exists():
            path.unlink()
        if name in self._collections:
            del self._collections[name]
    
    def get_stats(self, collection: str = DEFAULT_COLLECTION) -> dict[str, Any]:
        """Get statistics about a collection."""
        coll = self._load_collection(collection)
        return {
            "collection": collection,
            "count": len(coll["documents"]),
            "embedding_dimension": self.embeddings.dimension,
            "embedding_model": self.embeddings.model_name,
            "persist_directory": str(self.persist_directory),
        }


def get_vector_store(persist_directory: str | None = None) -> VectorStore:
    """Get or create a singleton vector store instance."""
    global _vector_store_instance
    
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore(persist_directory=persist_directory)
    
    return _vector_store_instance
