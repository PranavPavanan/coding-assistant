#!/usr/bin/env python3
"""
Test script to debug the retrieval method in RAG service.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.rag_service import RAGService

def test_retrieval():
    """Test the retrieval method."""
    print("Testing RAG retrieval method...")
    
    # Create RAG service instance
    rag_service = RAGService()
    
    # Test retrieval
    query = "What files are in this repository?"
    print(f"Query: {query}")
    
    try:
        retrieved_content, sources = rag_service._retrieve_relevant_content(query)
        print(f"Retrieved content count: {len(retrieved_content)}")
        print(f"Sources count: {len(sources)}")
        
        if sources:
            print("\nSources found:")
            for i, source in enumerate(sources):
                print(f"{i+1}. {source['file_path']} (score: {source['score']})")
                print(f"   Content preview: {source['content'][:200]}...")
                print()
        else:
            print("No sources found!")
            
        if retrieved_content:
            print("Retrieved content:")
            for i, content in enumerate(retrieved_content):
                print(f"Content {i+1}:")
                print(content[:500])
                print("..." if len(content) > 500 else "")
                print()
        else:
            print("No content retrieved!")
            
    except Exception as e:
        print(f"Error during retrieval: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_retrieval()

