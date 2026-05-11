# Data Isolation Bugfix Design

## Overview

The data isolation bug occurs because the backend does not properly filter manuals and chat history by user_id. When retrieving manuals or chat history, the system returns all records instead of only records belonging to the authenticated user. The fix involves adding user_id filtering to all relevant API endpoints and database queries.

## Bug Details

### Bug Condition

The bug manifests when multiple users are logged in. User A's manuals and chat history are visible to User B because the backend returns all records without filtering by user_id.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type UserAction {user_id: int, action: string}
  OUTPUT: boolean
  
  RETURN (input.action IN ['list_manuals', 'get_history', 'delete_manual', 'rename_chat']
         AND backendDoesNotFilterByUserId(input.user_id))
END FUNCTION
```

### Root Cause Analysis

1. **Manual Listing**: `/api/manuals` endpoint returns all manuals without filtering by user_id
2. **Chat History**: `/api/history` endpoint returns all chat history without filtering by user_id
3. **Manual Deletion**: `/api/manuals/<filename>` doesn't verify user ownership before deletion
4. **Chat Operations**: Rename/delete chat operations don't verify user ownership

### Examples

- **Example 1**: User A uploads "Tesla_Model3.pdf". User B logs in and sees the same manual in their list (BUG)
- **Example 2**: User A creates chat "Battery Diagnostics". User B can see this chat in their history (BUG)
- **Example 3**: User A deletes a manual. The manual is deleted for all users, not just User A (BUG)

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- File validation (PDF only) must continue to work
- Message saving must continue to work
- File deletion from disk must continue to work
- Search functionality must continue to work
- Authentication must continue to work

**Scope:**
All functionality that does NOT involve data isolation should be completely unaffected by this fix.

## Hypothesized Root Cause

Based on the bug description and code analysis, the most likely issues are:

1. **Missing user_id in Manual Storage**: Manuals stored without user_id association
2. **Missing user_id Filtering**: Backend queries don't filter by user_id
3. **Missing Ownership Verification**: Delete/rename operations don't verify user owns the resource
4. **Shared Manual Directory**: All manuals stored in single directory instead of per-user

## Correctness Properties

Property 1: Data Isolation - User Can Only See Own Data

_For any_ user action (list manuals, get history, delete manual, rename chat), the system SHALL return or modify ONLY data belonging to that user, not data from other users.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**

Property 2: Preservation - File Operations and Authentication

_For any_ file operation or authentication action, the system SHALL produce the same result as the original code, preserving all existing functionality for file validation, message saving, and authentication.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

**File 1**: `backend/flask_api.py`

**Changes for Manual Endpoints**:

1. **List Manuals** - Filter by user_id:
   ```python
   # BEFORE (Bug - returns all manuals)
   @app.route("/api/manuals", methods=["GET"])
   @require_auth
   def list_manuals():
       manuals = [_manual_meta(p) for p in list_manual_files()]
       return jsonify(manuals)
   
   # AFTER (Fixed - returns only user's manuals)
   @app.route("/api/manuals", methods=["GET"])
   @require_auth
   def list_manuals():
       user_id = request.current_user["sub"]
       user_dir = DATA_DIR / f"user_{user_id}"
       manuals = [_manual_meta(p) for p in user_dir.glob("*.pdf")]
       return jsonify(manuals)
   ```

2. **Upload Manual** - Store in user directory:
   ```python
   # BEFORE (Bug - stores in shared directory)
   @app.route("/api/manuals/upload", methods=["POST"])
   @require_auth
   def upload_manual():
       dest = DATA_DIR / uploaded.filename
       uploaded.save(str(dest))
   
   # AFTER (Fixed - stores in user directory)
   @app.route("/api/manuals/upload", methods=["POST"])
   @require_auth
   def upload_manual():
       user_id = request.current_user["sub"]
       user_dir = DATA_DIR / f"user_{user_id}"
       user_dir.mkdir(parents=True, exist_ok=True)
       dest = user_dir / uploaded.filename
       uploaded.save(str(dest))
   ```

3. **Delete Manual** - Verify ownership:
   ```python
   # BEFORE (Bug - deletes for all users)
   @app.route("/api/manuals/<path:filename>", methods=["DELETE"])
   @require_auth
   def delete_manual(filename: str):
       target = DATA_DIR / filename
       target.unlink()
   
   # AFTER (Fixed - only deletes user's manual)
   @app.route("/api/manuals/<path:filename>", methods=["DELETE"])
   @require_auth
   def delete_manual(filename: str):
       user_id = request.current_user["sub"]
       user_dir = DATA_DIR / f"user_{user_id}"
       target = user_dir / filename
       if not target.exists():
           return jsonify({"error": "Manual not found"}), 404
       target.unlink()
   ```

**Changes for Chat History Endpoints**:

1. **Get History** - Already filters by user_id (verify it works):
   ```python
   @app.route("/api/history", methods=["GET"])
   @require_auth
   def get_history():
       user_id = request.current_user["sub"]
       # Already filters by user_id - good!
       rows = conn.execute(
           "SELECT * FROM chat_history WHERE user_id=?",
           (user_id,)
       ).fetchall()
   ```

2. **Get Conversation** - Verify user ownership:
   ```python
   # BEFORE (Bug - returns any conversation)
   @app.route("/api/history/<int:conversation_id>", methods=["GET"])
   @require_auth
   def get_conversation(conversation_id: int):
       row = conn.execute(
           "SELECT * FROM chat_history WHERE id=?",
           (conversation_id,)
       ).fetchone()
   
   # AFTER (Fixed - only returns user's conversation)
   @app.route("/api/history/<int:conversation_id>", methods=["GET"])
   @require_auth
   def get_conversation(conversation_id: int):
       user_id = request.current_user["sub"]
       row = conn.execute(
           "SELECT * FROM chat_history WHERE id=? AND user_id=?",
           (conversation_id, user_id)
       ).fetchone()
       if row is None:
           return jsonify({"error": "Conversation not found"}), 404
   ```

3. **Delete Conversation** - Verify user ownership:
   ```python
   # BEFORE (Bug - deletes any conversation)
   @app.route("/api/history/<int:conversation_id>", methods=["DELETE"])
   @require_auth
   def delete_conversation(conversation_id: int):
       conn.execute(
           "DELETE FROM chat_history WHERE id=?",
           (conversation_id,)
       )
   
   # AFTER (Fixed - only deletes user's conversation)
   @app.route("/api/history/<int:conversation_id>", methods=["DELETE"])
   @require_auth
   def delete_conversation(conversation_id: int):
       user_id = request.current_user["sub"]
       result = conn.execute(
           "DELETE FROM chat_history WHERE id=? AND user_id=?",
           (conversation_id, user_id)
       )
       if result.rowcount == 0:
           return jsonify({"error": "Conversation not found"}), 404
   ```

**File 2**: `backend/rag_improved.py`

**Changes for Manual Indexing**:

1. **Build Index** - Use user-specific directory:
   ```python
   # BEFORE (Bug - indexes all manuals)
   def build_manual_index():
       files = list(DATA_DIR.glob("*.pdf"))
       # Indexes all files
   
   # AFTER (Fixed - indexes only user's manuals)
   def build_manual_index(user_id):
       user_dir = DATA_DIR / f"user_{user_id}"
       files = list(user_dir.glob("*.pdf"))
       # Indexes only user's files
   ```

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the data isolation bug, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate data isolation bug BEFORE implementing the fix.

**Test Cases**:
1. **User A uploads manual, User B sees it**: Register User A, upload manual, login as User B, verify manual appears (BUG)
2. **User A creates chat, User B sees it**: Register User A, create chat, login as User B, verify chat appears (BUG)
3. **User A deletes manual, affects User B**: Register User A, upload manual, User B sees it, User A deletes, User B's manual also deleted (BUG)

**Expected Counterexamples**:
- User B can list User A's manuals
- User B can see User A's chat history
- User B's manual list changes when User A deletes a manual

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed system produces the expected behavior (data isolation).

**Pseudocode:**
```
FOR ALL users IN [userA, userB] DO
  FOR ALL actions IN [upload_manual, create_chat, delete_manual] DO
    result_userA := perform_action(userA, action)
    result_userB := get_data(userB)
    ASSERT result_userB does NOT contain result_userA
  END FOR
END FOR
```

### Preservation Checking

**Goal**: Verify that for all functionality that does NOT involve data isolation, the fixed system produces the same result as the original system.

**Test Cases**:
1. **File Validation**: PDF files accepted, non-PDF rejected
2. **Message Saving**: Messages saved to database correctly
3. **File Deletion**: Files deleted from disk correctly
4. **Search**: Search works within user's own data
5. **Authentication**: Login/logout works correctly

