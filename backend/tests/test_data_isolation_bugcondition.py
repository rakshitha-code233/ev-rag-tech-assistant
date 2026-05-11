"""
Bug Condition Exploration Test for Data Isolation Fix

This test demonstrates the data isolation bug where users can see each other's
manuals and chat history. When one user uploads a manual or creates a chat,
all other users can see it.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

Bug Condition: Multiple users are logged in. User A's data is visible to User B.
Expected Behavior: Each user should only see their own manuals and chat history
Current Behavior (Unfixed): User B can see User A's manuals and chat history
"""

import pytest
import sqlite3
import os
import sys
import json
from pathlib import Path
from io import BytesIO

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask_api import app, get_db, init_chat_history_table
from db import register_user, init_db, DB_NAME


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Setup: Create fresh database and app context. Teardown: Clean up."""
    # Remove existing database if it exists
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    
    # Clean up data directory (user-specific directories)
    from rag_improved import DATA_DIR
    if DATA_DIR.exists():
        import shutil
        shutil.rmtree(DATA_DIR)
    
    # Initialize fresh database
    init_db()
    init_chat_history_table()
    
    yield
    
    # Cleanup after test
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    
    # Clean up data directory
    if DATA_DIR.exists():
        import shutil
        shutil.rmtree(DATA_DIR)


@pytest.fixture
def client():
    """Create Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def register_and_login(client, username, email, password):
    """Helper function to register and login a user."""
    # Register
    response = client.post('/api/auth/register', json={
        'username': username,
        'email': email,
        'password': password
    })
    assert response.status_code == 201, f"Registration failed: {response.get_json()}"
    
    # Login
    response = client.post('/api/auth/login', json={
        'email': email,
        'password': password
    })
    assert response.status_code == 200, f"Login failed: {response.get_json()}"
    
    data = response.get_json()
    token = data['token']
    return token


def get_auth_headers(token):
    """Create authorization headers with token."""
    return {'Authorization': f'Bearer {token}'}


def test_user_b_can_see_user_a_manual_bugcondition():
    """
    Bug Condition Exploration Test: User B Sees User A's Manual
    
    Demonstrates the data isolation bug:
    1. Register and login User A
    2. User A uploads a manual "EV_TestManual_UserA.pdf"
    3. Register and login User B
    4. User B lists manuals
    5. Assert that User B can see User A's manual (BUG - should not see it)
    
    EXPECTED OUTCOME ON UNFIXED CODE: Test FAILS (proves bug exists)
    EXPECTED OUTCOME ON FIXED CODE: Test PASSES
    
    **Validates: Requirements 1.1, 2.1**
    """
    client = app.test_client()
    
    # Step 1: Register and login User A
    token_a = register_and_login(client, 'userA', 'userA@example.com', 'PasswordA123')
    
    # Step 2: User A uploads a manual
    pdf_content = b'%PDF-1.4\n%fake pdf content for testing'
    response = client.post(
        '/api/manuals/upload',
        data={'file': (BytesIO(pdf_content), 'EV_TestManual_UserA.pdf')},
        headers=get_auth_headers(token_a)
    )
    assert response.status_code == 201, f"Upload failed: {response.get_json()}"
    
    # Step 3: Register and login User B
    token_b = register_and_login(client, 'userB', 'userB@example.com', 'PasswordB123')
    
    # Step 4: User B lists manuals
    response = client.get('/api/manuals', headers=get_auth_headers(token_b))
    assert response.status_code == 200
    
    manuals_b = response.get_json()
    
    # Step 5: Assert that User B can see User A's manual (BUG)
    # On unfixed code, this will FAIL because User B will see the manual
    # On fixed code, this will PASS because User B won't see the manual
    manual_names = [m['filename'] for m in manuals_b]
    
    # BUG CONDITION: User B should NOT see User A's manual
    # If this assertion fails, it means the bug exists (User B can see User A's manual)
    assert 'EV_TestManual_UserA.pdf' not in manual_names, \
        "BUG: User B should NOT see User A's manual, but they can!"


def test_user_b_can_see_user_a_chat_bugcondition():
    """
    Bug Condition Exploration Test: User B Sees User A's Chat History
    
    Demonstrates the data isolation bug:
    1. Register and login User A
    2. User A creates a chat conversation
    3. Register and login User B
    4. User B lists chat history
    5. Assert that User B can see User A's chat (BUG - should not see it)
    
    EXPECTED OUTCOME ON UNFIXED CODE: Test FAILS (proves bug exists)
    EXPECTED OUTCOME ON FIXED CODE: Test PASSES
    
    **Validates: Requirements 1.2, 2.2**
    """
    client = app.test_client()
    
    # Step 1: Register and login User A
    token_a = register_and_login(client, 'userA', 'userA@example.com', 'PasswordA123')
    
    # Step 2: User A creates a chat conversation
    response = client.post(
        '/api/history',
        json={
            'title': 'Battery Diagnostics',
            'messages': [
                {'role': 'user', 'content': 'How do I check battery health?'},
                {'role': 'assistant', 'content': 'You can check battery health using...'}
            ]
        },
        headers=get_auth_headers(token_a)
    )
    assert response.status_code == 201, f"Save history failed: {response.get_json()}"
    
    # Step 3: Register and login User B
    token_b = register_and_login(client, 'userB', 'userB@example.com', 'PasswordB123')
    
    # Step 4: User B lists chat history
    response = client.get('/api/history', headers=get_auth_headers(token_b))
    assert response.status_code == 200
    
    history_b = response.get_json()
    
    # Step 5: Assert that User B can see User A's chat (BUG)
    # On unfixed code, this will FAIL because User B will see the chat
    # On fixed code, this will PASS because User B won't see the chat
    chat_titles = [h['title'] for h in history_b]
    
    # BUG CONDITION: User B should NOT see User A's chat
    # If this assertion fails, it means the bug exists (User B can see User A's chat)
    assert 'Battery Diagnostics' not in chat_titles, \
        "BUG: User B should NOT see User A's chat, but they can!"


def test_user_a_delete_manual_affects_user_b_bugcondition():
    """
    Bug Condition Exploration Test: User A's Delete Affects User B
    
    Demonstrates the data isolation bug:
    1. Register and login User A
    2. User A uploads a manual
    3. Register and login User B
    4. User B lists manuals and sees User A's manual (BUG)
    5. User A deletes the manual
    6. User B lists manuals again
    7. Assert that User B's manual list changed (BUG - should not be affected)
    
    EXPECTED OUTCOME ON UNFIXED CODE: Test FAILS (proves bug exists)
    EXPECTED OUTCOME ON FIXED CODE: Test PASSES
    
    **Validates: Requirements 1.3, 2.3**
    """
    client = app.test_client()
    
    # Step 1: Register and login User A
    token_a = register_and_login(client, 'userA', 'userA@example.com', 'PasswordA123')
    
    # Step 2: User A uploads a manual
    pdf_content = b'%PDF-1.4\n%fake pdf content for testing'
    response = client.post(
        '/api/manuals/upload',
        data={'file': (BytesIO(pdf_content), 'EV_TestManual_Delete.pdf')},
        headers=get_auth_headers(token_a)
    )
    assert response.status_code == 201
    
    # Step 3: Register and login User B
    token_b = register_and_login(client, 'userB', 'userB@example.com', 'PasswordB123')
    
    # Step 4: User B lists manuals and sees User A's manual (BUG)
    response = client.get('/api/manuals', headers=get_auth_headers(token_b))
    manuals_b_before = response.get_json()
    manual_names_before = [m['filename'] for m in manuals_b_before]
    
    # At this point, User B can see User A's manual (BUG)
    # We'll use this to demonstrate the bug
    
    # Step 5: User A deletes the manual
    response = client.delete(
        '/api/manuals/EV_TestManual_Delete.pdf',
        headers=get_auth_headers(token_a)
    )
    assert response.status_code == 200
    
    # Step 6: User B lists manuals again
    response = client.get('/api/manuals', headers=get_auth_headers(token_b))
    manuals_b_after = response.get_json()
    manual_names_after = [m['filename'] for m in manuals_b_after]
    
    # Step 7: Assert that User B's manual list changed (BUG)
    # On unfixed code, this will FAIL because User B's list will change
    # On fixed code, this will PASS because User B's list won't change
    
    # BUG CONDITION: User B's manual list should NOT change when User A deletes
    # If this assertion fails, it means the bug exists (User B's list changed)
    assert manual_names_before == manual_names_after, \
        "BUG: User B's manual list should NOT change when User A deletes, but it did!"


def test_user_a_rename_chat_affects_user_b_bugcondition():
    """
    Bug Condition Exploration Test: User A's Rename Affects User B
    
    Demonstrates the data isolation bug:
    1. Register and login User A
    2. User A creates a chat conversation
    3. Register and login User B
    4. User B lists chat history and sees User A's chat (BUG)
    5. User A renames the chat
    6. User B lists chat history again
    7. Assert that User B's chat title changed (BUG - should not be affected)
    
    EXPECTED OUTCOME ON UNFIXED CODE: Test FAILS (proves bug exists)
    EXPECTED OUTCOME ON FIXED CODE: Test PASSES
    
    **Validates: Requirements 1.4, 2.4**
    """
    client = app.test_client()
    
    # Step 1: Register and login User A
    token_a = register_and_login(client, 'userA', 'userA@example.com', 'PasswordA123')
    
    # Step 2: User A creates a chat conversation
    response = client.post(
        '/api/history',
        json={
            'title': 'Original Title',
            'messages': [
                {'role': 'user', 'content': 'Test message'}
            ]
        },
        headers=get_auth_headers(token_a)
    )
    assert response.status_code == 201
    chat_id = response.get_json()['id']
    
    # Step 3: Register and login User B
    token_b = register_and_login(client, 'userB', 'userB@example.com', 'PasswordB123')
    
    # Step 4: User B lists chat history and sees User A's chat (BUG)
    response = client.get('/api/history', headers=get_auth_headers(token_b))
    history_b_before = response.get_json()
    
    # At this point, User B can see User A's chat (BUG)
    # We'll use this to demonstrate the bug
    
    # Step 5: User A renames the chat
    response = client.patch(
        f'/api/history/{chat_id}',
        json={'title': 'Renamed Title'},
        headers=get_auth_headers(token_a)
    )
    assert response.status_code == 200
    
    # Step 6: User B lists chat history again
    response = client.get('/api/history', headers=get_auth_headers(token_b))
    history_b_after = response.get_json()
    
    # Step 7: Assert that User B's chat title changed (BUG)
    # On unfixed code, this will FAIL because User B's chat title will change
    # On fixed code, this will PASS because User B won't see the chat at all
    
    # BUG CONDITION: User B's chat should NOT be affected by User A's rename
    # If this assertion fails, it means the bug exists (User B's chat changed)
    
    # Extract titles before and after
    titles_before = [h['title'] for h in history_b_before]
    titles_after = [h['title'] for h in history_b_after]
    
    assert titles_before == titles_after, \
        "BUG: User B's chat title should NOT change when User A renames, but it did!"


def test_user_a_can_see_own_manual():
    """
    Preservation Test: User A Can See Own Manual
    
    Verifies that a user can see their own uploaded manual.
    This behavior should be preserved (not changed by the fix).
    
    EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code
    """
    client = app.test_client()
    
    # Register and login User A
    token_a = register_and_login(client, 'userA', 'userA@example.com', 'PasswordA123')
    
    # User A uploads a manual
    pdf_content = b'%PDF-1.4\n%fake pdf content for testing'
    response = client.post(
        '/api/manuals/upload',
        data={'file': (BytesIO(pdf_content), 'EV_TestManual_Own.pdf')},
        headers=get_auth_headers(token_a)
    )
    assert response.status_code == 201
    
    # User A lists manuals
    response = client.get('/api/manuals', headers=get_auth_headers(token_a))
    assert response.status_code == 200
    
    manuals = response.get_json()
    manual_names = [m['filename'] for m in manuals]
    
    # User A should see their own manual
    assert 'EV_TestManual_Own.pdf' in manual_names, \
        "User A should see their own uploaded manual"


def test_user_a_can_see_own_chat():
    """
    Preservation Test: User A Can See Own Chat
    
    Verifies that a user can see their own chat history.
    This behavior should be preserved (not changed by the fix).
    
    EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code
    """
    client = app.test_client()
    
    # Register and login User A
    token_a = register_and_login(client, 'userA', 'userA@example.com', 'PasswordA123')
    
    # User A creates a chat conversation
    response = client.post(
        '/api/history',
        json={
            'title': 'My Chat',
            'messages': [
                {'role': 'user', 'content': 'Test message'}
            ]
        },
        headers=get_auth_headers(token_a)
    )
    assert response.status_code == 201
    
    # User A lists chat history
    response = client.get('/api/history', headers=get_auth_headers(token_a))
    assert response.status_code == 200
    
    history = response.get_json()
    chat_titles = [h['title'] for h in history]
    
    # User A should see their own chat
    assert 'My Chat' in chat_titles, \
        "User A should see their own chat history"
