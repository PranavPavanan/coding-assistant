#!/usr/bin/env python3
"""
Test runner script for the RAG GitHub Assistant backend.

This script provides a convenient way to run all tests with proper configuration
and reporting.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ {description} - PASSED")
        if result.stdout:
            print("Output:")
            print(result.stdout)
    else:
        print(f"❌ {description} - FAILED")
        if result.stderr:
            print("Error:")
            print(result.stderr)
        if result.stdout:
            print("Output:")
            print(result.stdout)
    
    return result.returncode == 0


def main():
    """Main test runner function."""
    print("🧪 RAG GitHub Assistant - Test Runner")
    print("=" * 60)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Test results
    results = []
    
    # Run unit tests
    print("\n🔬 Running Unit Tests...")
    unit_tests = [
        ("python -m pytest tests/unit/test_github_service.py -v", "GitHub Service Tests"),
        ("python -m pytest tests/unit/test_indexer_service.py -v", "Indexer Service Tests"),
        ("python -m pytest tests/unit/test_rag_service.py -v", "RAG Service Tests"),
        ("python -m pytest tests/unit/test_models.py -v", "Model Tests"),
        ("python -m pytest tests/unit/test_api_health.py -v", "Health API Tests"),
        ("python -m pytest tests/unit/test_api_search.py -v", "Search API Tests"),
        ("python -m pytest tests/unit/test_api_repositories.py -v", "Repositories API Tests"),
        ("python -m pytest tests/unit/test_api_indexing.py -v", "Indexing API Tests"),
        ("python -m pytest tests/unit/test_api_chat.py -v", "Chat API Tests"),
        ("python -m pytest tests/unit/test_websocket.py -v", "WebSocket Tests"),
    ]
    
    for command, description in unit_tests:
        success = run_command(command, description)
        results.append((description, success))
    
    # Run integration tests
    print("\n🔗 Running Integration Tests...")
    integration_tests = [
        ("python -m pytest tests/integration/test_repository_workflow.py -v", "Repository Workflow Tests"),
        ("python -m pytest tests/integration/test_websocket_workflow.py -v", "WebSocket Workflow Tests"),
    ]
    
    for command, description in integration_tests:
        success = run_command(command, description)
        results.append((description, success))
    
    # Run E2E tests
    print("\n🌐 Running End-to-End Tests...")
    e2e_tests = [
        ("python -m pytest tests/e2e/test_complete_workflow.py -v", "Complete Workflow Tests"),
    ]
    
    for command, description in e2e_tests:
        success = run_command(command, description)
        results.append((description, success))
    
    # Run all tests together
    print("\n🚀 Running All Tests Together...")
    all_tests_success = run_command("python -m pytest tests/ -v --tb=short", "All Tests")
    results.append(("All Tests", all_tests_success))
    
    # Generate coverage report
    print("\n📊 Generating Coverage Report...")
    coverage_success = run_command(
        "python -m pytest tests/ --cov=src --cov-report=html --cov-report=term-missing",
        "Coverage Report"
    )
    results.append(("Coverage Report", coverage_success))
    
    # Print summary
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for description, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {description}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed + failed} test suites")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! The application is ready for deployment.")
        return 0
    else:
        print(f"\n⚠️  {failed} test suite(s) failed. Please fix the issues before deploying.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
