#!/usr/bin/env python3
"""Test script to verify index detection is working."""

import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_index_detection():
    """Test that the backend properly detects existing indexed repositories."""
    
    print("Testing Index Detection")
    print("=" * 50)
    
    try:
        # Test the index stats endpoint
        print("\n1. Testing /api/index/stats endpoint")
        response = requests.get(f"{BASE_URL}/api/index/stats")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"SUCCESS: Index stats retrieved successfully")
            print(f"Repository Name: {stats.get('repository_name', 'None')}")
            print(f"Is Indexed: {stats.get('is_indexed', False)}")
            print(f"File Count: {stats.get('file_count', 0)}")
            print(f"Total Size: {stats.get('total_size', 0)} bytes")
            print(f"Vector Count: {stats.get('vector_count', 0)}")
            print(f"Last Updated: {stats.get('last_updated', 'None')}")
            print(f"Created At: {stats.get('created_at', 'None')}")
            
            if stats.get('is_indexed'):
                print("\nSUCCESS: Repository is properly detected as indexed!")
                print("   The query button should now be enabled in the frontend.")
            else:
                print("\nISSUE: Repository is not detected as indexed.")
                print("   Check the metadata files in backend/storage/metadata/")
        else:
            print(f"FAILED: Failed to get index stats: {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to backend. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"ERROR: {e}")

def test_chat_query():
    """Test that chat query works with the detected repository."""
    
    print("\n" + "=" * 50)
    print("2. Testing Chat Query with Detected Repository")
    
    try:
        # Test a simple query
        query_data = {
            "query": "What is the main function in this codebase?"
        }
        
        print(f"Sending query: {query_data['query']}")
        response = requests.post(f"{BASE_URL}/api/chat/query", json=query_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: Query successful!")
            print(f"Session ID: {result.get('session_id', 'None')}")
            print(f"Conversation ID: {result.get('conversation_id', 'None')}")
            print(f"Response Length: {len(result.get('response', ''))} characters")
            print(f"Sources Found: {len(result.get('sources', []))}")
            print(f"Response Preview: {result.get('response', '')[:200]}...")
            
            if result.get('response'):
                print("\nSUCCESS: Chat query is working with the indexed repository!")
            else:
                print("\nWARNING: Query succeeded but no response content.")
        else:
            print(f"FAILED: Query failed: {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to backend. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_index_detection()
    test_chat_query()
    print("\nIndex detection test completed!")
