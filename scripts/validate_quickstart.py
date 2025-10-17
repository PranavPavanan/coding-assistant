#!/usr/bin/env python3
"""
Quickstart validation script.
Tests that the application is set up correctly and can perform basic operations.
"""
import sys
import requests
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api"
TIMEOUT = 30


def print_test(name: str, passed: bool, message: str = ""):
    """Print test result with color."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name}")
    if message:
        print(f"   {message}")


def test_health_check() -> bool:
    """Test that the backend is running."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        passed = response.status_code == 200 and response.json().get("status") == "healthy"
        print_test("Health Check", passed)
        return passed
    except Exception as e:
        print_test("Health Check", False, str(e))
        return False


def test_repository_search() -> Dict[str, Any]:
    """Test repository search functionality."""
    try:
        response = requests.post(
            f"{BASE_URL}/search/repositories",
            json={"query": "python", "limit": 5},
            timeout=10
        )
        passed = response.status_code == 200
        data = response.json() if passed else {}
        
        if passed and data.get("repositories"):
            print_test("Repository Search", True, f"Found {len(data['repositories'])} repositories")
            return data["repositories"][0]
        else:
            print_test("Repository Search", False, "No repositories found")
            return {}
    except Exception as e:
        print_test("Repository Search", False, str(e))
        return {}


def test_url_validation() -> bool:
    """Test URL validation."""
    try:
        response = requests.post(
            f"{BASE_URL}/validate/url",
            json={"url": "https://github.com/python/cpython"},
            timeout=10
        )
        passed = response.status_code == 200
        data = response.json() if passed else {}
        is_valid = data.get("is_valid", False)
        
        print_test("URL Validation", passed and is_valid)
        return passed
    except Exception as e:
        print_test("URL Validation", False, str(e))
        return False


def test_index_stats() -> bool:
    """Test getting index statistics."""
    try:
        response = requests.get(f"{BASE_URL}/index/stats", timeout=5)
        passed = response.status_code == 200
        data = response.json() if passed else {}
        
        print_test("Index Stats", passed, f"Indexed: {data.get('is_indexed', False)}")
        return passed
    except Exception as e:
        print_test("Index Stats", False, str(e))
        return False


def test_chat_context() -> bool:
    """Test getting chat context."""
    try:
        response = requests.get(f"{BASE_URL}/chat/context", timeout=5)
        passed = response.status_code in [200, 422]  # 422 is ok if no conversation
        
        print_test("Chat Context", passed)
        return passed
    except Exception as e:
        print_test("Chat Context", False, str(e))
        return False


def test_chat_history() -> bool:
    """Test getting chat history."""
    try:
        response = requests.get(f"{BASE_URL}/chat/history", timeout=5)
        passed = response.status_code == 200
        
        print_test("Chat History", passed)
        return passed
    except Exception as e:
        print_test("Chat History", False, str(e))
        return False


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("RAG GitHub Assistant - Quickstart Validation")
    print("=" * 60)
    print()
    
    print("Testing Backend Connectivity...")
    print("-" * 60)
    
    # Critical tests
    if not test_health_check():
        print("\n❌ Backend is not running!")
        print("Please start the backend with: uvicorn src.main:app --reload")
        sys.exit(1)
    
    print()
    print("Testing Core Functionality...")
    print("-" * 60)
    
    # Core functionality tests
    results = []
    results.append(test_repository_search())
    results.append(test_url_validation())
    results.append(test_index_stats())
    results.append(test_chat_context())
    results.append(test_chat_history())
    
    print()
    print("=" * 60)
    
    # Summary
    passed_count = sum(1 for r in results if r)
    total_count = len(results) + 1  # +1 for health check
    
    print(f"Results: {passed_count + 1}/{total_count} tests passed")
    
    if passed_count == len(results):
        print("✅ All tests passed! The application is working correctly.")
        print()
        print("Next steps:")
        print("1. Start the frontend: cd frontend && npm run dev")
        print("2. Open http://localhost:3000 in your browser")
        print("3. Search for a repository and start indexing")
        print("4. Ask questions about the code")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
