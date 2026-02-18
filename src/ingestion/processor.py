"""
Document Processor - Full pipeline for document ingestion.

Combines loading, chunking, embedding, and storage.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.ingestion.loader import DocumentLoader, Document
from src.ingestion.chunker import TextChunker, Chunk

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of document processing."""
    success: bool
    document_id: str
    source: str
    num_chunks: int
    total_chars: int
    metadata: dict[str, Any]
    error: str | None = None


class DocumentProcessor:
    """
    Full document processing pipeline.
    
    Loads documents, chunks them, generates embeddings,
    and stores in vector database.
    """
    
    def __init__(
        self,
        vector_store: "VectorStore | None" = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        chunk_strategy: str = "sentence",
    ):
        self.vector_store = vector_store
        self.chunker = TextChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            strategy=chunk_strategy,
        )
    
    def process_file(
        self,
        file_path: str | Path,
        collection_name: str = "documents",
        extra_metadata: dict | None = None,
    ) -> ProcessingResult:
        """
        Process a single file through the full pipeline.
        
        Args:
            file_path: Path to the document
            collection_name: Vector store collection name
            extra_metadata: Additional metadata to store
            
        Returns:
            ProcessingResult with status and stats
        """
        file_path = Path(file_path).expanduser().resolve()
        
        try:
            # Load document
            loader = DocumentLoader(file_path)
            doc = loader.load()
            
            # Generate document ID
            doc_id = f"{file_path.stem}_{hash(str(file_path)) % 10000:04d}"
            
            # Chunk the document
            base_metadata = {
                "source": str(file_path),
                "filename": file_path.name,
                "doc_id": doc_id,
                **(doc.metadata or {}),
                **(extra_metadata or {}),
            }
            
            chunks = self.chunker.chunk(doc.content, base_metadata)
            
            logger.info(f"Processed {file_path.name}: {len(chunks)} chunks, {doc.char_count} chars")
            
            # Store in vector database if available
            if self.vector_store:
                for chunk in chunks:
                    chunk_metadata = {
                        **base_metadata,
                        "chunk_index": chunk.index,
                        "start_char": chunk.start_char,
                        "end_char": chunk.end_char,
                    }
                    self.vector_store.add(
                        text=chunk.text,
                        metadata=chunk_metadata,
                        collection=collection_name,
                    )
                
                logger.info(f"Stored {len(chunks)} chunks in collection '{collection_name}'")
            
            return ProcessingResult(
                success=True,
                document_id=doc_id,
                source=str(file_path),
                num_chunks=len(chunks),
                total_chars=doc.char_count,
                metadata=base_metadata,
            )
            
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            return ProcessingResult(
                success=False,
                document_id="",
                source=str(file_path),
                num_chunks=0,
                total_chars=0,
                metadata={},
                error=str(e),
            )
    
    def process_directory(
        self,
        directory: str | Path,
        collection_name: str = "documents",
        recursive: bool = True,
        extensions: set[str] | None = None,
    ) -> list[ProcessingResult]:
        """
        Process all supported files in a directory.
        
        Args:
            directory: Directory path
            collection_name: Vector store collection
            recursive: Whether to process subdirectories
            extensions: File extensions to process (default: all supported)
            
        Returns:
            List of ProcessingResults
        """
        directory = Path(directory).expanduser().resolve()
        
        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory}")
        
        extensions = extensions or DocumentLoader.SUPPORTED_EXTENSIONS
        
        # Find files
        if recursive:
            files = [
                f for f in directory.rglob("*")
                if f.is_file() and f.suffix.lower() in extensions
            ]
        else:
            files = [
                f for f in directory.iterdir()
                if f.is_file() and f.suffix.lower() in extensions
            ]
        
        logger.info(f"Found {len(files)} files to process in {directory}")
        
        results = []
        for file_path in files:
            result = self.process_file(
                file_path,
                collection_name=collection_name,
                extra_metadata={"directory": str(directory)},
            )
            results.append(result)
        
        successful = sum(1 for r in results if r.success)
        logger.info(f"Processed {successful}/{len(results)} files successfully")
        
        return results
    
    def process_text(
        self,
        text: str,
        source_name: str = "direct_input",
        collection_name: str = "documents",
        extra_metadata: dict | None = None,
    ) -> ProcessingResult:
        """
        Process raw text directly.
        
        Args:
            text: The text content
            source_name: Identifier for the text
            collection_name: Vector store collection
            extra_metadata: Additional metadata
            
        Returns:
            ProcessingResult
        """
        try:
            doc_id = f"{source_name}_{hash(text) % 10000:04d}"
            
            base_metadata = {
                "source": source_name,
                "doc_id": doc_id,
                **(extra_metadata or {}),
            }
            
            chunks = self.chunker.chunk(text, base_metadata)
            
            if self.vector_store:
                for chunk in chunks:
                    chunk_metadata = {
                        **base_metadata,
                        "chunk_index": chunk.index,
                        "start_char": chunk.start_char,
                        "end_char": chunk.end_char,
                    }
                    self.vector_store.add(
                        text=chunk.text,
                        metadata=chunk_metadata,
                        collection=collection_name,
                    )
            
            return ProcessingResult(
                success=True,
                document_id=doc_id,
                source=source_name,
                num_chunks=len(chunks),
                total_chars=len(text),
                metadata=base_metadata,
            )
            
        except Exception as e:
            logger.error(f"Failed to process text: {e}")
            return ProcessingResult(
                success=False,
                document_id="",
                source=source_name,
                num_chunks=0,
                total_chars=0,
                metadata={},
                error=str(e),
            )
