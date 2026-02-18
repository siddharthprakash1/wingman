"""
Document Ingestion Module.

Handles loading, chunking, and processing documents (PDF, TXT, MD, etc.)
for extraction and embedding storage.
"""

from src.ingestion.loader import DocumentLoader, load_document
from src.ingestion.chunker import TextChunker, chunk_text
from src.ingestion.processor import DocumentProcessor

__all__ = [
    "DocumentLoader",
    "load_document",
    "TextChunker", 
    "chunk_text",
    "DocumentProcessor",
]
