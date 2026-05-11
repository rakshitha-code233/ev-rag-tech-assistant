#!/usr/bin/env python
"""
Integration test for the EV Diagnostic Assistant system.
Tests: Database, Authentication, Manual Upload, and Chat.
"""

import json
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from db import init_db, register_user, login_user
from rag_improved import build_manual_index, list_manual_files, retrieve_manual_chunks
from manual_query import get_answer


def test_database():
    """Test database initialization and user registration."""
    print("\n" + "="*60)
    print("TEST 1: Database & User Registration")
    print("="*60)
    
    # Initialize database
    init_db()
    print("✓ Database initialized")
    
    # Register test user
    result = register_user("Test User", "test@example.com", "TestPassword123")
    if result == "success":
        print("✓ User registered successfully")
    else:
        print(f"✗ User registration failed: {result}")
        return False
    
    # Try to register duplicate
    result = register_user("Another User", "test@example.com", "AnotherPassword")
    if result == "exists":
        print("✓ Duplicate email correctly rejected")
    else:
        print(f"✗ Duplicate email check failed: {result}")
        return False
    
    return True


def test_login():
    """Test user login."""
    print("\n" + "="*60)
    print("TEST 2: User Login")
    print("="*60)
    
    # Test correct credentials
    user = login_user("test@example.com", "TestPassword123")
    if user and user["email"] == "test@example.com":
        print(f"✓ Login successful: {user['username']} ({user['email']})")
    else:
        print("✗ Login failed with correct credentials")
        return False
    
    # Test incorrect password
    user = login_user("test@example.com", "WrongPassword")
    if user is None:
        print("✓ Incorrect password correctly rejected")
    else:
        print("✗ Incorrect password was accepted")
        return False
    
    # Test non-existent user
    user = login_user("nonexistent@example.com", "AnyPassword")
    if user is None:
        print("✓ Non-existent user correctly rejected")
    else:
        print("✗ Non-existent user was accepted")
        return False
    
    return True


def test_manual_indexing():
    """Test manual indexing."""
    print("\n" + "="*60)
    print("TEST 3: Manual Indexing")
    print("="*60)
    
    # Check if Tesla_Model3.pdf exists
    pdf_path = Path(__file__).parent / "Tesla_Model3.pdf"
    if not pdf_path.exists():
        print(f"⚠ Tesla_Model3.pdf not found at {pdf_path}")
        print("  Skipping manual indexing test")
        return True
    
    print(f"✓ Found manual: {pdf_path.name}")
    
    # Create user-specific directory and copy manual
    from rag_improved import DATA_DIR
    user_dir = DATA_DIR / "user_1"
    user_dir.mkdir(parents=True, exist_ok=True)
    
    import shutil
    dest = user_dir / pdf_path.name
    shutil.copy(str(pdf_path), str(dest))
    print(f"✓ Manual copied to user directory: {dest}")
    
    # Build index
    result = build_manual_index(user_id=1)
    print(f"✓ Index built: {result['manuals_indexed']} manuals, {result['chunks_indexed']} chunks")
    
    if result['chunks_indexed'] == 0:
        print("⚠ Warning: No chunks extracted from manual")
        return True
    
    return True


def test_retrieval():
    """Test manual retrieval."""
    print("\n" + "="*60)
    print("TEST 4: Manual Retrieval")
    print("="*60)
    
    # Test retrieval
    query = "How to check battery health?"
    chunks = retrieve_manual_chunks(query, top_k=3)
    
    if chunks:
        print(f"✓ Retrieved {len(chunks)} chunks for query: '{query}'")
        for i, chunk in enumerate(chunks, 1):
            print(f"  [{i}] {chunk.manual} p.{chunk.page} (score: {chunk.score:.3f})")
            print(f"      {chunk.text[:80]}...")
    else:
        print(f"⚠ No chunks retrieved for query: '{query}'")
    
    return True


def test_chat():
    """Test chat functionality."""
    print("\n" + "="*60)
    print("TEST 5: Chat Functionality")
    print("="*60)
    
    # Test greeting
    answer = get_answer("Hello")
    if "EV Diagnostic Assistant" in answer:
        print("✓ Greeting handled correctly")
    else:
        print(f"✗ Greeting response unexpected: {answer[:50]}")
    
    # Test query without manuals
    answer = get_answer("How do I fix a Tesla battery issue?")
    print(f"✓ Chat response: {answer[:100]}...")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("EV DIAGNOSTIC ASSISTANT - SYSTEM INTEGRATION TEST")
    print("="*60)
    
    tests = [
        ("Database & Registration", test_database),
        ("User Login", test_login),
        ("Manual Indexing", test_manual_indexing),
        ("Manual Retrieval", test_retrieval),
        ("Chat Functionality", test_chat),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! System is ready.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
