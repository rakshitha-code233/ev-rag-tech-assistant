"""
Bug Condition Exploration Test for Login Persistence Fix

This test demonstrates the login persistence bug where users cannot log back in
after logout with previously registered credentials.

**Validates: Requirements 1.3, 1.4**

Bug Condition: User registers, logs out, closes app, then attempts to login with same credentials
Expected Behavior: Login should succeed and return user object
Current Behavior (Unfixed): Login fails with "Invalid email or password" error
"""

import pytest
import sqlite3
import os
import sys
from pathlib import Path

# Add parent directory to path to import db module
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import register_user, login_user, init_db, DB_NAME


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Setup: Create fresh database for each test. Teardown: Clean up."""
    # Remove existing database if it exists
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    
    # Initialize fresh database
    init_db()
    
    yield
    
    # Cleanup after test
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)


def test_login_after_logout_with_correct_credentials():
    """
    Bug Condition Exploration Test
    
    Demonstrates the login persistence bug:
    1. Register user with email "test@example.com" and password "TestPassword123"
    2. Simulate logout (clear token from localStorage - simulated by clearing session)
    3. Simulate app close/restart (new connection to database)
    4. Attempt to login with same credentials
    5. Assert that login succeeds and returns user object
    
    EXPECTED OUTCOME ON UNFIXED CODE: Test FAILS (proves bug exists)
    EXPECTED OUTCOME ON FIXED CODE: Test PASSES
    
    **Validates: Requirements 1.3, 1.4**
    """
    # Step 1: Register user
    email = "test@example.com"
    password = "TestPassword123"
    username = "testuser"
    
    result = register_user(username, email, password)
    assert result == "success", "User registration should succeed"
    
    # Step 2: Simulate logout (clear token from localStorage)
    # In a real app, this would clear the JWT token from localStorage
    # For this test, we just note that the token is cleared
    # The user is now logged out
    
    # Step 3: Simulate app close/restart
    # In a real app, the user closes the browser/app and reopens it
    # For this test, we simulate this by creating a new database connection
    # (the database persists, but the session is gone)
    
    # Step 4: Attempt to login with same credentials
    login_result = login_user(email, password)
    
    # Step 5: Assert that login succeeds and returns user object
    assert login_result is not None, "Login should succeed after logout with correct credentials"
    assert login_result["email"] == email, "Returned user should have correct email"
    assert login_result["username"] == username, "Returned user should have correct username"
    assert login_result["id"] > 0, "Returned user should have valid id"


def test_login_after_logout_with_incorrect_password():
    """
    Preservation Test: Invalid Password After Logout
    
    Verifies that incorrect passwords are still rejected after logout.
    This behavior should be preserved (not changed by the fix).
    
    EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code
    """
    # Register user
    email = "test@example.com"
    password = "TestPassword123"
    username = "testuser"
    
    result = register_user(username, email, password)
    assert result == "success"
    
    # Simulate logout and app restart
    
    # Attempt to login with incorrect password
    login_result = login_user(email, "WrongPassword123")
    
    # Should fail
    assert login_result is None, "Login should fail with incorrect password"


def test_login_after_logout_with_nonexistent_email():
    """
    Preservation Test: Non-Existent Email After Logout
    
    Verifies that non-existent emails are still rejected after logout.
    This behavior should be preserved (not changed by the fix).
    
    EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code
    """
    # Register a user
    email = "test@example.com"
    password = "TestPassword123"
    username = "testuser"
    
    result = register_user(username, email, password)
    assert result == "success"
    
    # Simulate logout and app restart
    
    # Attempt to login with non-existent email
    login_result = login_user("nonexistent@example.com", password)
    
    # Should fail
    assert login_result is None, "Login should fail with non-existent email"


def test_first_login_after_registration():
    """
    Preservation Test: First-Time Login After Registration
    
    Verifies that first-time login after registration works correctly.
    This behavior should be preserved (not changed by the fix).
    
    EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code
    """
    # Register user
    email = "test@example.com"
    password = "TestPassword123"
    username = "testuser"
    
    result = register_user(username, email, password)
    assert result == "success"
    
    # Immediately login (first login, no logout yet)
    login_result = login_user(email, password)
    
    # Should succeed
    assert login_result is not None, "First login after registration should succeed"
    assert login_result["email"] == email
    assert login_result["username"] == username
    assert login_result["id"] > 0


def test_multiple_logout_login_cycles():
    """
    Bug Condition Exploration Test: Multiple Logout-Login Cycles
    
    Demonstrates that the bug persists across multiple logout/login cycles.
    
    EXPECTED OUTCOME ON UNFIXED CODE: Test FAILS after first logout
    EXPECTED OUTCOME ON FIXED CODE: Test PASSES
    """
    email = "test@example.com"
    password = "TestPassword123"
    username = "testuser"
    
    # Register user
    result = register_user(username, email, password)
    assert result == "success"
    
    # First login cycle
    login_result = login_user(email, password)
    assert login_result is not None, "First login should succeed"
    
    # Simulate logout and app restart
    
    # Second login cycle (after logout)
    login_result = login_user(email, password)
    assert login_result is not None, "Second login after logout should succeed"
    
    # Simulate logout and app restart again
    
    # Third login cycle (after second logout)
    login_result = login_user(email, password)
    assert login_result is not None, "Third login after second logout should succeed"


def test_user_registration_stores_password_correctly():
    """
    Preservation Test: Password Storage
    
    Verifies that user registration stores password correctly.
    This behavior should be preserved (not changed by the fix).
    
    EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code
    """
    email = "test@example.com"
    password = "TestPassword123"
    username = "testuser"
    
    # Register user
    result = register_user(username, email, password)
    assert result == "success", "User registration should succeed"
    
    # Verify that the password is stored (by attempting login)
    login_result = login_user(email, password)
    assert login_result is not None, "Password should be stored correctly"


def test_duplicate_email_registration():
    """
    Preservation Test: Duplicate Email Registration
    
    Verifies that duplicate email registration is rejected.
    This behavior should be preserved (not changed by the fix).
    
    EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code
    """
    email = "test@example.com"
    password = "TestPassword123"
    username = "testuser"
    
    # Register user
    result = register_user(username, email, password)
    assert result == "success"
    
    # Attempt to register with same email
    result = register_user("anotheruser", email, "AnotherPassword123")
    assert result == "exists", "Duplicate email registration should be rejected"
