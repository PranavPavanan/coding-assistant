#!/usr/bin/env python3
"""
Test script to debug the RAG query method.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.rag_service import RAGService
from src.models.query import QueryRequest

def test_rag_query():
    """Test the RAG query method."""
    print("Testing RAG query method...")
    
    # Create RAG service instance
    rag_service = RAGService()
    
    # Initialize the service
    print("Initializing RAG service...")
    import asyncio
    result = asyncio.run(rag_service.initialize())
    print(f"Initialization result: {result}")
    
    if not result:
        print("RAG service initialization failed!")
        return
    
    # Test query
    query_request = QueryRequest(
        query="What files are in this repository?",
        max_sources=5,
        temperature=0.7
    )
    
    print(f"Query: {query_request.query}")
    
    try:
        response = rag_service.query(query_request)
        print(f"Response: {response.response}")
        print(f"Sources count: {len(response.sources)}")
        
        if response.sources:
            print("\nSources found:")
            for i, source in enumerate(response.sources):
                print(f"{i+1}. {source.file} (score: {source.score})")
                print(f"   Content preview: {source.content[:200]}...")
                print()
        else:
            print("No sources found!")
            
    except Exception as e:
        print(f"Error during query: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rag_query()

