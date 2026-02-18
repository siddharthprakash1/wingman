#!/usr/bin/env python3
"""Test document ingestion and search with local embeddings."""

import asyncio
import json
from pathlib import Path


async def test_ingest_pdf():
    """Test ingesting a PDF file."""
    print("=" * 60)
    print("TEST 1: Ingest PDF Document")
    print("=" * 60)
    
    from src.tools.documents import ingest_document
    
    # Use the OpenClaw PDF in the project
    pdf_path = Path("OpenClaw Architecture and Code-Level Overview.pdf")
    
    if not pdf_path.exists():
        print(f"⚠️  PDF not found at: {pdf_path}")
        print("   Skipping PDF test...")
        return
    
    result = await ingest_document(
        file_path=str(pdf_path),
        collection="openclaw_docs",
    )
    
    print(result)
    print()


async def test_ingest_text():
    """Test ingesting raw text."""
    print("=" * 60)
    print("TEST 2: Ingest Text Content")
    print("=" * 60)
    
    from src.ingestion.processor import DocumentProcessor
    from src.retrieval.vector_store import get_vector_store
    
    vector_store = get_vector_store()
    processor = DocumentProcessor(vector_store=vector_store)
    
    sample_text = """
    OpenClaw is an AI assistant framework that uses multiple specialized agents.
    The system includes a Router Agent that directs tasks to appropriate specialists.
    
    Key components include:
    - Research Agent: Web search and information gathering
    - Browser Agent: Web automation and scraping
    - Writer Agent: Content creation and editing
    - Data Agent: Analysis and visualization
    - Coding Agents: Planning, Engineering, and Review
    
    The framework uses LangExtract for structured data extraction and
    ChromaDB for vector storage with local embeddings.
    """
    
    result = processor.process_text(
        text=sample_text,
        source_name="openclaw_overview",
        collection_name="test_docs",
    )
    
    print(f"Success: {result.success}")
    print(f"Document ID: {result.document_id}")
    print(f"Chunks: {result.num_chunks}")
    print(f"Characters: {result.total_chars}")
    print()


async def test_search():
    """Test semantic search."""
    print("=" * 60)
    print("TEST 3: Semantic Search")
    print("=" * 60)
    
    from src.tools.documents import search_documents
    
    # Search in test collection
    result = await search_documents(
        query="What agents are available in the system?",
        collection="test_docs",
        num_results=3,
    )
    
    print(result)
    print()


async def test_extraction():
    """Test extraction from knowledge base."""
    print("=" * 60)
    print("TEST 4: Extract from Knowledge Base")
    print("=" * 60)
    
    from src.tools.documents import extract_from_knowledge_base
    
    result = await extract_from_knowledge_base(
        query="agents and components",
        extraction_prompt="Extract all agent types and their purposes",
        collection="test_docs",
        num_chunks=3,
    )
    
    print(result)
    print()


async def test_list_collections():
    """Test listing collections."""
    print("=" * 60)
    print("TEST 5: List Collections")
    print("=" * 60)
    
    from src.tools.documents import list_documents
    
    result = await list_documents()
    print(result)
    print()


async def test_embeddings_directly():
    """Test the embedding model."""
    print("=" * 60)
    print("TEST 6: Local Embeddings")
    print("=" * 60)
    
    from src.retrieval.embeddings import get_embeddings
    
    embeddings = get_embeddings()
    
    # Test embedding generation
    text1 = "The quick brown fox jumps over the lazy dog"
    text2 = "A fast auburn fox leaps above a sleepy canine"
    text3 = "Python is a programming language"
    
    emb1 = embeddings.embed(text1)
    print(f"Embedding dimension: {len(emb1)}")
    print(f"Model: {embeddings.model_name}")
    
    # Test similarity
    sim1 = embeddings.similarity(text1, text2)
    sim2 = embeddings.similarity(text1, text3)
    
    print(f"\nSimilarity (similar sentences): {sim1:.4f}")
    print(f"Similarity (different topics): {sim2:.4f}")
    print()


async def main():
    print("\n📚 Document Ingestion & Search Tests\n")
    
    try:
        await test_embeddings_directly()
    except Exception as e:
        print(f"❌ Test 6 failed: {e}\n")
    
    try:
        await test_ingest_text()
    except Exception as e:
        print(f"❌ Test 2 failed: {e}\n")
    
    try:
        await test_search()
    except Exception as e:
        print(f"❌ Test 3 failed: {e}\n")
    
    try:
        await test_list_collections()
    except Exception as e:
        print(f"❌ Test 5 failed: {e}\n")
    
    try:
        await test_ingest_pdf()
    except Exception as e:
        print(f"❌ Test 1 failed: {e}\n")
    
    # Skip extraction test if no OpenAI key
    print("\n⚠️  Skipping extraction test (requires API key)")
    print("   Run with: OPENAI_API_KEY=... python test_documents.py")


if __name__ == "__main__":
    asyncio.run(main())
