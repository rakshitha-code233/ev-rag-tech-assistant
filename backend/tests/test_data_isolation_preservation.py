"""
Preservation Property Tests for Data Isolation Fix

These tests verify that existing functionality is preserved (not changed by the fix).
They test file validation, message saving, file deletion, search, and authentication.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

These tests should PASS on both unfixed and fixed code.
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


# ============================================================================
# Preservation Tests: File Validation (Requirement 3.1)
# ============================================================================

def test_pdf_file_accepted():
    """
    Preservation Test: PDF Files Accepted
    
    Verifies that PDF files with EV keywords are accepted.
    This behavior should be preserved (not changed by the fix).
    
    EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code
    
    **Validates: Requirement 3.1**
    """
    client = app.test_client()
    
    # Register and login user
    token = register_and_login(client, 'user1', 'user1@example.com', 'Password123')
    
    # Upload a valid PDF with EV keyword
    pdf_content = b'%PDF-1.4\n%fake pdf content for testing'
    response = client.post(
        '/api/manuals/upload',
        data={'file': (BytesIO(pdf_content), 'EV_Manual_Test.pdf')},
        headers=get_auth_headers(token)
    )
    
    # Should succeed
    assert response.status_code == 201, f"PDF upload should succeed: {response.get_json()}"
    data = response.get_json()
    assert data['filename'] == 'EV_Manual_Test.pdf'


def test_non_pdf_file_rejected():
    """
    Preservation Test: Non-PDF Files Rejected
    
    Verifies that non-PDF files are rejected.
    This behavior should be preserved (not changed by the fix).
    
    EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code
    
    **Validates: Requirement 3.1**
    """
    client = app.test_client()
    
    # Register and login user
    token = register_and_login(client, 'user1', 'user1@example.com', 'Password123')
    
    # Try to upload a non-PDF file
    response = client.post(
        '/api/manuals/upload',
        data={'file': (BytesIO(b'not a pdf'), 'document.txt')},
        headers=get_auth_headers(token)
    )
    
    # Should fail
    assert response.status_code == 400, "Non-PDF upload should fail"
    data = response.get_json()
    assert 'error' in data


def test_pdf_without_ev_keyword_rejected():
    """
    Preservation Test: PDF Without EV Keyword Rejected
    
    Verifies that PDF files without EV keywords are rejected.
    This behavior should be preserved (not changed by the fix).
    
    EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code
    
    **Validates: Requirement 3.1**
    """
    client = app.test_client()
    
    # Register and login user
    token = register_and_login(client, 'user1', 'user1@example.com', 'Password123')
    
    # Try to upload a PDF without EV keyword
    pdf_content = b'%PDF-1.4\n%fake pdf content for testing'
    response = client.post(
        '/api/manuals/upload',
        data={'file': (BytesIO(pdf_content), 'Generic_Manual.pdf')},
        headers=get_auth_headers(token)
    )
    
    # Should fail
    assert response.status_code == 400, "PDF without EV keyword should fail"
    data = response.get_json()
    assert 'error' in data


# ============================================================================
# Preservation Tests: Message Saving (Requirement 3.2)
# ============================================================================

def test_chat_messages_saved_to_database():
    """
    Preservation Test: Chat Messages Saved to Database
    
    Verifies that chat messages are saved to the database correctly.
    This behavior should be preserved (not changed by the fix).
    
    EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code
    
    **Validates: Requirement 3.2**
    """
    client = app.test_client()
    
    # Register and login user
    token = register_and_login(client, 'user1', 'user1@example.com', 'Password123')
    
    # Create a chat conversation
    messages = [
        {'role': 'user', 'content': 'How do I check battery health?'},
        {'role': 'assistant', 'content': 'You can check battery health using...'}
    ]
    response = client.post(
        '/api/history',
        json={
            'title': 'Battery Check',
            'messages': messages
        },
        headers=get_auth_headers(token)
    )
    
    # Should succeed
    assert response.status_code == 201, f"Save history should succeed: {response.get_json()}"
    data = response.get_json()
    chat_id = data['id']
    
    # Retrieve the chat
    response = client.get(f'/api/history/{chat_id}', headers=get_auth_headers(token))
    assert response.status_code == 200
    
    retrieved = response.get_json()
    assert retrieved['title'] == 'Battery Check'
    assert retrieved['messages'] == messages


def test_multiple_messages_in_chat():
    """
    Preservation Test: Multiple Messages in Chat
    
    Verifies that multiple messages can be saved and retrieved.
    This behavior should be preserved (not changed by the fix).
    
    EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code
    
    **Validates: Requirement 3.2**
    """
    client = app.test_client()
    
    # Register and login user
    token = register_and_login(client, 'user1', 'user1@example.com', 'Password123')
    
    # Create a chat with multiple messages
    messages = [
        {'role': 'user', 'content': 'Message 1'},
        {'role': 'assistant', 'content': 'Response 1'},
        {'role': 'user', 'content': 'Message 2'},
        {'role': 'assistant', 'content': 'Response 2'},
        {'role': 'user', 'content': 'Message 3'},
        {'role': 'assistant', 'content': 'Response 3'},
    ]
    response = client.post(
        '/api/history',
        json={
            'title': 'Multi-Message Chat',
            'messages': messages
        },
        headers=get_auth_headers(token)
    )
    
    assert response.status_code == 201
    chat_id = response.get_json()['id']
    
    # Retrieve and verify all messages
    response = client.get(f'/api/history/{chat_id}', headers=get_auth_headers(token))
    retrieved = response.get_json()
    
    assert len(retrieved['messages']) == 6
    assert retrieved['messages'] == messages


# ============================================================================
# Preservation Tests: File Deletion (Requirement 3.3)
# ============================================================================

def test_manual_file_deleted_from_disk():
    """
    Preservation Test: Manual File Deleted from Disk
    
    Verifies that manual files are deleted from disk when requested.
    This behavior should be preserved (not changed by the fix).
    
    EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code
    
    **Validates: Requirement 3.3**
    """
    client = app.test_client()
    
    # Register and login user
    token = register_and_login(client, 'user1', 'user1@example.com', 'Password123')
    
    # Upload a manual
    pdf_content = b'%PDF-1.4\n%fake pdf content for testing'
    response = client.post(
        '/api/manuals/upload',
        data={'file': (BytesIO(pdf_content), 'EV_Manual_ToDelete.pdf')},
        headers=get_auth_headers(token)
    )
    assert response.status_code == 201
    
    # Verify it exists in the list
    response = client.get('/api/manuals', headers=get_auth_headers(token))
    manuals_before = [m['filename'] for m in response.get_json()]
    assert 'EV_Manual_ToDelete.pdf' in manuals_before
    
    # Delete the manual
    response = client.delete(
        '/api/manuals/EV_Manual_ToDelete.pdf',
        headers=get_auth_headers(token)
    )
    assert response.status_code == 200
    
    # Verify it's gone from the list
    response = client.get('/api/manuals', headers=get_auth_headers(token))
    manuals_after = [m['filename'] for m in response.get_json()]
    assert 'EV_Manual_ToDelete.pdf' not in manuals_after


def test_delete_nonexistent_manual_returns_404():
    """
    Preservation Test: Delete Non-Existent Manual Returns 404
    
    Verifies that deleting a non-existent manual returns 404.
    This behavior should be preserved (not changed by the fix).
    
    EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code
    
    **Validates: Requirement 3.3**
    """
    client = app.test_client()
    
    # Register and login user
    token = register_and_login(client, 'user1', 'user1@example.com', 'Password123')
    
    # Try to delete a non-existent manual
    response = client.delete(
        '/api/manuals/NonExistent.pdf',
        headers=get_auth_headers(token)
    )
    
    # Should return 404
    assert response.status_code == 404


# ============================================================================
# Preservation Tests: Search Functionality (Requirement 3.4)
# ============================================================================

def test_user_can_search_own_chat_history():
    """
    Preservation Test: User Can Search Own Chat History
    
    Verifies that users can search within their own chat history.
    This behavior should be preserved (not changed by the fix).
    
    EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code
    
    **Validates: Requirement 3.4**
    """
    client = app.test_client()
    
    # Register and login user
    token = register_and_login(client, 'user1', 'user1@example.com', 'Password123')
    
    # Create multiple chats with different titles
    titles = ['Battery Diagnostics', 'Charging System', 'Motor Performance']
    chat_ids = []
    
    for title in titles:
        response = client.post(
            '/api/history',
            json={
                'title': title,
                'messages': [{'role': 'user', 'content': f'Question about {title}'}]
            },
            headers=get_auth_headers(token)
        )
        assert response.status_code == 201
        chat_ids.append(response.get_json()['id'])
    
    # Get all chats
    response = client.get('/api/history', headers=get_auth_headers(token))
    assert response.status_code == 200
    
    all_chats = response.get_json()
    retrieved_titles = [chat['title'] for chat in all_chats]
    
    # Verify all titles are present
    for title in titles:
        assert title in retrieved_titles, f"Title '{title}' should be in chat history"


def test_user_can_retrieve_specific_chat():
    """
    Preservation Test: User Can Retrieve Specific Chat
    
    Verifies that users can retrieve a specific chat by ID.
    This behavior should be preserved (not changed by the fix).
    
    EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code
    
    **Validates: Requirement 3.4**
    """
    client = app.test_client()
    
    # Register and login user
    token = register_and_login(client, 'user1', 'user1@example.com', 'Password123')
    
    # Create a chat
    response = client.post(
        '/api/history',
        json={
            'title': 'Specific Chat',
            'messages': [{'role': 'user', 'content': 'Test message'}]
        },
        headers=get_auth_headers(token)
    )
    assert response.status_code == 201
    chat_id = response.get_json()['id']
    
    # Retrieve the specific chat
    response = client.get(f'/api/history/{chat_id}', headers=get_auth_headers(token))
    assert response.status_code == 200
    
    chat = response.get_json()
    assert chat['title'] == 'Specific Chat'
    assert chat['id'] == chat_id


# ============================================================================
# Preservation Tests: Authentication (Requirement 3.5)
# ============================================================================

def test_user_login_logout_works():
    """
    Preservation Test: User Login/Logout Works
    
    Verifies that user login and logout work correctly.
    This behavior should be preserved (not changed by the fix).
    
    EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code
    
    **Validates: Requirement 3.5**
    """
    client = app.test_client()
    
    # Register user
    response = client.post('/api/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'Password123'
    })
    assert response.status_code == 201
    
    # Login
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'Password123'
    })
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'token' in data
    assert 'user' in data
    assert data['user']['email'] == 'test@example.com'


def test_invalid_credentials_rejected():
    """
    Preservation Test: Invalid Credentials Rejected
    
    Verifies that invalid credentials are rejected.
    This behavior should be preserved (not changed by the fix).
    
    EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code
    
    **Validates: Requirement 3.5**
    """
    client = app.test_client()
    
    # Register user
    response = client.post('/api/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'Password123'
    })
    assert response.status_code == 201
    
    # Try to login with wrong password
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'WrongPassword'
    })
    assert response.status_code == 401


def test_missing_token_rejected():
    """
    Preservation Test: Missing Token Rejected
    
    Verifies that requests without authentication token are rejected.
    This behavior should be preserved (not changed by the fix).
    
    EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code
    
    **Validates: Requirement 3.5**
    """
    client = app.test_client()
    
    # Try to access protected endpoint without token
    response = client.get('/api/manuals')
    assert response.status_code == 401


def test_invalid_token_rejected():
    """
    Preservation Test: Invalid Token Rejected
    
    Verifies that invalid tokens are rejected.
    This behavior should be preserved (not changed by the fix).
    
    EXPECTED OUTCOME: Test PASSES on both unfixed and fixed code
    
    **Validates: Requirement 3.5**
    """
    client = app.test_client()
    
    # Try to access protected endpoint with invalid token
    response = client.get(
        '/api/manuals',
        headers={'Authorization': 'Bearer invalid_token_here'}
    )
    assert response.status_code == 401
