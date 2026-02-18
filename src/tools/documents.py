"""
Document Tools - Ingest documents and search with LangExtract.

Tools for:
- Adding documents (PDF, TXT, etc.) to the knowledge base
- Semantic search over documents
- Extracting structured data from documents
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from src.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


async def ingest_document(
    file_path: str,
    collection: str = "documents",
) -> str:
    """
    Add a document to the knowledge base.
    
    Args:
        file_path: Path to the document (PDF, TXT, MD, HTML, JSON, CSV)
        collection: Collection name for organizing documents
        
    Returns:
        Status message with document stats
    """
    try:
        from src.ingestion.processor import DocumentProcessor
        from src.retrieval.vector_store import get_vector_store
        
        vector_store = get_vector_store()
        processor = DocumentProcessor(vector_store=vector_store)
        
        result = processor.process_file(
            file_path=file_path,
            collection_name=collection,
        )
        
        if result.success:
            return json.dumps({
                "success": True,
                "message": f"Document ingested successfully",
                "document_id": result.document_id,
                "source": result.source,
                "chunks": result.num_chunks,
                "characters": result.total_chars,
                "collection": collection,
            }, indent=2)
        else:
            return json.dumps({
                "success": False,
                "error": result.error,
            }, indent=2)
            
    except Exception as e:
        return f"❌ Failed to ingest document: {e}"


async def ingest_directory(
    directory: str,
    collection: str = "documents",
    recursive: bool = True,
) -> str:
    """
    Add all documents in a directory to the knowledge base.
    
    Args:
        directory: Path to the directory
        collection: Collection name
        recursive: Whether to process subdirectories
        
    Returns:
        Status message with processing stats
    """
    try:
        from src.ingestion.processor import DocumentProcessor
        from src.retrieval.vector_store import get_vector_store
        
        vector_store = get_vector_store()
        processor = DocumentProcessor(vector_store=vector_store)
        
        results = processor.process_directory(
            directory=directory,
            collection_name=collection,
            recursive=recursive,
        )
        
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        return json.dumps({
            "success": True,
            "total_files": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "total_chunks": sum(r.num_chunks for r in successful),
            "total_characters": sum(r.total_chars for r in successful),
            "collection": collection,
            "errors": [{"file": r.source, "error": r.error} for r in failed] if failed else None,
        }, indent=2)
        
    except Exception as e:
        return f"❌ Failed to ingest directory: {e}"


async def search_documents(
    query: str,
    collection: str = "documents",
    num_results: int = 5,
) -> str:
    """
    Search the knowledge base for relevant documents.
    
    Args:
        query: Search query (natural language)
        collection: Collection to search
        num_results: Number of results to return
        
    Returns:
        Matching document chunks with relevance scores
    """
    try:
        from src.retrieval.vector_store import get_vector_store
        
        vector_store = get_vector_store()
        results = vector_store.search(
            query=query,
            n_results=num_results,
            collection=collection,
        )
        
        if not results:
            return json.dumps({
                "query": query,
                "results": [],
                "message": "No matching documents found",
            }, indent=2)
        
        formatted_results = []
        for r in results:
            formatted_results.append({
                "score": round(r["score"], 4),
                "text": r["text"][:500] + "..." if len(r["text"]) > 500 else r["text"],
                "source": r["metadata"].get("source", "unknown"),
                "chunk_index": r["metadata"].get("chunk_index"),
            })
        
        return json.dumps({
            "query": query,
            "collection": collection,
            "num_results": len(formatted_results),
            "results": formatted_results,
        }, indent=2)
        
    except Exception as e:
        return f"❌ Search failed: {e}"


async def extract_from_knowledge_base(
    query: str,
    extraction_prompt: str,
    collection: str = "documents",
    num_chunks: int = 5,
) -> str:
    """
    Search documents and extract structured information using LangExtract.
    
    Args:
        query: Search query to find relevant documents
        extraction_prompt: What information to extract
        collection: Collection to search
        num_chunks: Number of chunks to process
        
    Returns:
        Extracted information from matching documents
    """
    try:
        from src.retrieval.vector_store import get_vector_store
        from src.extraction.extractor import Extractor
        
        # Search for relevant chunks
        vector_store = get_vector_store()
        results = vector_store.search(
            query=query,
            n_results=num_chunks,
            collection=collection,
        )
        
        if not results:
            return json.dumps({
                "success": False,
                "error": "No matching documents found",
            }, indent=2)
        
        # Combine relevant text
        combined_text = "\n\n---\n\n".join([
            f"[Source: {r['metadata'].get('source', 'unknown')}]\n{r['text']}"
            for r in results
        ])
        
        # Extract using LangExtract
        extractor = Extractor(model_id="gpt-4o")
        extraction_result = extractor.extract(
            text=combined_text,
            prompt=extraction_prompt,
        )
        
        if extraction_result.success:
            return json.dumps({
                "success": True,
                "query": query,
                "sources": [r["metadata"].get("source") for r in results],
                "extraction_prompt": extraction_prompt,
                "extractions": extraction_result.extractions,
            }, indent=2)
        else:
            return json.dumps({
                "success": False,
                "error": extraction_result.error,
            }, indent=2)
            
    except Exception as e:
        return f"❌ Extraction failed: {e}"


async def list_documents(collection: str = "documents") -> str:
    """
    List all collections and document stats.
    
    Args:
        collection: Collection to get stats for
        
    Returns:
        Collection statistics
    """
    try:
        from src.retrieval.vector_store import get_vector_store
        
        vector_store = get_vector_store()
        collections = vector_store.list_collections()
        
        stats = []
        for coll in collections:
            count = vector_store.count(coll)
            stats.append({
                "collection": coll,
                "document_count": count,
            })
        
        return json.dumps({
            "collections": stats,
            "embedding_model": vector_store.embeddings.model_name,
            "embedding_dimension": vector_store.embeddings.dimension,
        }, indent=2)
        
    except Exception as e:
        return f"❌ Failed to list documents: {e}"


async def delete_document(
    doc_id: str | None = None,
    source: str | None = None,
    collection: str = "documents",
) -> str:
    """
    Delete documents from the knowledge base.
    
    Args:
        doc_id: Document ID to delete
        source: Delete all docs from this source file
        collection: Collection to delete from
        
    Returns:
        Confirmation message
    """
    try:
        from src.retrieval.vector_store import get_vector_store
        
        vector_store = get_vector_store()
        
        if doc_id:
            vector_store.delete(doc_ids=[doc_id], collection=collection)
            return f"✅ Deleted document: {doc_id}"
        elif source:
            vector_store.delete(where={"source": source}, collection=collection)
            return f"✅ Deleted all documents from source: {source}"
        else:
            return "❌ Please provide either doc_id or source to delete"
            
    except Exception as e:
        return f"❌ Delete failed: {e}"


def register_document_tools(registry: ToolRegistry) -> None:
    """Register document tools with the registry."""
    
    registry.register(
        name="ingest_document",
        description=(
            "Add a document (PDF, TXT, MD, HTML, JSON, CSV) to the knowledge base. "
            "The document will be chunked and embedded for semantic search."
        ),
        parameters={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the document file",
                },
                "collection": {
                    "type": "string",
                    "description": "Collection name for organizing documents (default: 'documents')",
                    "default": "documents",
                },
            },
            "required": ["file_path"],
        },
        func=ingest_document,
    )
    
    registry.register(
        name="ingest_directory",
        description=(
            "Add all supported documents in a directory to the knowledge base. "
            "Processes PDF, TXT, MD, HTML, JSON, and CSV files."
        ),
        parameters={
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Path to the directory",
                },
                "collection": {
                    "type": "string",
                    "description": "Collection name (default: 'documents')",
                    "default": "documents",
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Process subdirectories (default: true)",
                    "default": True,
                },
            },
            "required": ["directory"],
        },
        func=ingest_directory,
    )
    
    registry.register(
        name="search_knowledge",
        description=(
            "Semantic search over the knowledge base. "
            "Finds document chunks most relevant to the query."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query",
                },
                "collection": {
                    "type": "string",
                    "description": "Collection to search (default: 'documents')",
                    "default": "documents",
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results (default: 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
        func=search_documents,
    )
    
    registry.register(
        name="extract_from_docs",
        description=(
            "Search documents and extract structured information using LangExtract. "
            "Combines semantic search with AI-powered extraction."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to find relevant documents",
                },
                "extraction_prompt": {
                    "type": "string",
                    "description": "What information to extract (e.g., 'Extract all company names and their revenue')",
                },
                "collection": {
                    "type": "string",
                    "description": "Collection to search",
                    "default": "documents",
                },
                "num_chunks": {
                    "type": "integer",
                    "description": "Number of document chunks to process",
                    "default": 5,
                },
            },
            "required": ["query", "extraction_prompt"],
        },
        func=extract_from_knowledge_base,
    )
    
    registry.register(
        name="list_knowledge",
        description="List all document collections and their statistics.",
        parameters={
            "type": "object",
            "properties": {
                "collection": {
                    "type": "string",
                    "description": "Collection to get stats for",
                    "default": "documents",
                },
            },
        },
        func=list_documents,
    )
    
    registry.register(
        name="delete_document",
        description="Delete documents from the knowledge base by ID or source file.",
        parameters={
            "type": "object",
            "properties": {
                "doc_id": {
                    "type": "string",
                    "description": "Document ID to delete",
                },
                "source": {
                    "type": "string",
                    "description": "Delete all docs from this source file path",
                },
                "collection": {
                    "type": "string",
                    "description": "Collection to delete from",
                    "default": "documents",
                },
            },
        },
        func=delete_document,
    )
