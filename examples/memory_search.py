#!/usr/bin/env python3
"""
Semantic Memory Search Example - Search Conversation History

This example demonstrates how to use Wingman's semantic search to:
1. Index past conversations
2. Search by meaning (not just keywords)
3. Retrieve relevant context
4. Build a searchable knowledge base

Usage:
    python examples/memory_search.py
"""

import asyncio
from datetime import datetime
from pathlib import Path

from src.config.settings import get_settings
from src.memory.search import LocalEmbeddings, MemorySearch
from src.retrieval.vector_store import get_vector_store


async def index_and_search_example():
    """Demonstrate semantic search over memory."""
    
    print("🧠 Semantic Memory Search Example")
    print("=" * 60)
    
    # Setup
    settings = get_settings()
    workspace = Path(settings.workspace.path).expanduser()
    
    # Initialize embedding provider
    print("\n📦 Loading embeddings model...")
    embeddings = LocalEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Initialize memory search
    memory_search = MemorySearch(
        workspace=workspace,
        embedding_provider=embeddings
    )
    
    print("✅ Model loaded\n")
    
    # Add some sample memories
    print("➕ Adding sample memories...")
    
    sample_memories = [
        {
            "content": "I learned how to use Python's asyncio for concurrent programming. It's great for I/O-bound tasks.",
            "source": "session:python_learning",
            "timestamp": datetime(2026, 2, 10, 10, 30),
        },
        {
            "content": "Discussed quantum computing principles. Qubits can be in superposition, unlike classical bits.",
            "source": "session:quantum_research",
            "timestamp": datetime(2026, 2, 12, 14, 15),
        },
        {
            "content": "Explored machine learning model training. Important to use validation sets to prevent overfitting.",
            "source": "session:ml_project",
            "timestamp": datetime(2026, 2, 15, 9, 0),
        },
        {
            "content": "Implemented a REST API using FastAPI. It's much faster than Flask for async operations.",
            "source": "session:api_development",
            "timestamp": datetime(2026, 2, 16, 16, 45),
        },
        {
            "content": "Read about database indexing strategies. B-trees are commonly used for primary keys.",
            "source": "session:database_optimization",
            "timestamp": datetime(2026, 2, 17, 11, 20),
        },
    ]
    
    for memory in sample_memories:
        await memory_search.add_entry(**memory)
        print(f"  ✓ Added: {memory['content'][:50]}...")
    
    print(f"\n✅ Added {len(sample_memories)} memories\n")
    
    # Perform semantic searches
    print("🔍 Semantic Search Tests:")
    print("=" * 60)
    
    queries = [
        "How do I handle concurrent operations in Python?",
        "Tell me about quantum mechanics in computing",
        "What's important when training AI models?",
        "Building web APIs efficiently",
    ]
    
    for query in queries:
        print(f"\n💭 Query: {query}")
        results = await memory_search.search(
            query=query,
            limit=2,
            min_score=0.3
        )
        
        if results:
            print(f"   Found {len(results)} relevant memories:\n")
            for i, (entry, score) in enumerate(results, 1):
                print(f"   {i}. [Score: {score:.2f}] {entry.content[:80]}...")
                print(f"      Source: {entry.source}")
                print(f"      Time: {entry.timestamp.strftime('%Y-%m-%d %H:%M')}\n")
        else:
            print("   No relevant memories found.\n")


async def vector_store_example():
    """Demonstrate vector store for document search."""
    
    print("\n\n📚 Vector Store Document Search Example")
    print("=" * 60)
    
    # Get vector store instance
    vector_store = get_vector_store()
    
    # Add sample documents
    print("\n➕ Adding sample documents...")
    
    documents = [
        {
            "text": "Python is a high-level programming language known for its simplicity and readability.",
            "metadata": {"category": "programming", "language": "python"},
        },
        {
            "text": "JavaScript is essential for web development, running in browsers and on servers via Node.js.",
            "metadata": {"category": "programming", "language": "javascript"},
        },
        {
            "text": "Machine learning models learn patterns from data without being explicitly programmed.",
            "metadata": {"category": "AI", "topic": "machine_learning"},
        },
        {
            "text": "FastAPI is a modern Python web framework for building APIs with automatic documentation.",
            "metadata": {"category": "programming", "framework": "fastapi"},
        },
    ]
    
    for doc in documents:
        doc_id = vector_store.add(
            text=doc["text"],
            metadata=doc["metadata"]
        )
        print(f"  ✓ Added document: {doc_id}")
    
    print(f"\n✅ Added {len(documents)} documents")
    print(f"📊 Vector store stats: {vector_store.get_stats()}\n")
    
    # Search documents
    print("🔍 Document Search:")
    print("=" * 60)
    
    search_queries = [
        ("What programming languages are good for beginners?", {}),
        ("Tell me about web frameworks", {"category": "programming"}),
        ("How does AI work?", {}),
    ]
    
    for query, filter_criteria in search_queries:
        print(f"\n💭 Query: {query}")
        if filter_criteria:
            print(f"   Filter: {filter_criteria}")
        
        results = vector_store.search(
            query=query,
            n_results=2,
            where=filter_criteria if filter_criteria else None
        )
        
        if results:
            print(f"   Found {len(results)} relevant documents:\n")
            for i, result in enumerate(results, 1):
                print(f"   {i}. [Score: {result['score']:.2f}] {result['text'][:80]}...")
                print(f"      Metadata: {result['metadata']}\n")
        else:
            print("   No relevant documents found.\n")


async def main():
    """Run memory search examples."""
    
    print("""
╔══════════════════════════════════════════════════════════╗
║        Wingman Semantic Memory Search Example            ║
╚══════════════════════════════════════════════════════════╝

This example demonstrates:
- Semantic search (meaning-based, not keyword matching)
- Memory indexing and retrieval
- Vector store for document search
- Contextual information retrieval
    """)
    
    # Choose example
    print("\nSelect an example:")
    print("1. Semantic memory search (conversation history)")
    print("2. Vector store search (document collection)")
    print("3. Run both examples")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    try:
        if choice == "1":
            await index_and_search_example()
        elif choice == "2":
            await vector_store_example()
        elif choice == "3":
            await index_and_search_example()
            await vector_store_example()
        else:
            print("Invalid choice. Running both examples...")
            await index_and_search_example()
            await vector_store_example()
        
        print("\n" + "=" * 60)
        print("✅ Examples complete!")
        print("\n💡 Tip: Semantic search finds results by meaning, not just keywords.")
        print("   Try asking questions in different ways to see similar results!")
        
    except ImportError as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 To use semantic search, install sentence-transformers:")
        print("   pip install sentence-transformers")


if __name__ == "__main__":
    asyncio.run(main())
