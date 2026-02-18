"""
Retrieval Module - Embeddings and Vector Store.

Provides local embedding generation and ChromaDB-based vector storage
for semantic search over documents.
"""

from src.retrieval.embeddings import LocalEmbeddings, get_embeddings
from src.retrieval.vector_store import VectorStore, get_vector_store

__all__ = [
    "LocalEmbeddings",
    "get_embeddings",
    "VectorStore",
    "get_vector_store",
]
