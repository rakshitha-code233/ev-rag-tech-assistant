# Login Persistence Bugfix Design

## Overview

The login persistence bug occurs because `bcrypt.hashpw()` returns bytes, but SQLite stores and retrieves them without proper encoding/decoding. When a user registers, the password hash is stored as raw bytes. Upon login, the retrieved bytes cannot be properly compared with the newly hashed password due to type mismatches. The fix involves decoding the password hash to a UTF-8 string before storage and encoding it back to bytes before verification.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when a user attempts to log in after logout with previously registered credentials
- **Property (P)**: The desired behavior when logging in with correct credentials - the password verification should succeed and return the user object
- **Preservation**: Existing authentication behavior for invalid credentials and first-time logins that must remain unchanged
- **bcrypt.hashpw()**: Function in `backend/db.py` that returns bytes representing the hashed password
- **bcrypt.checkpw()**: Function in `backend/db.py` that verifies a password against a hash (expects bytes for both parameters)
- **SQLite password column**: The TEXT column in the users table that stores the password hash
- **login_user()**: The function in `backend/db.py` that retrieves user credentials and verifies the password
- **register_user()**: The function in `backend/db.py` that stores new user credentials with hashed password

## Bug Details

### Bug Condition

The bug manifests when a user attempts to log in after logout with previously registered credentials. The `login_user()` function in `backend/db.py` retrieves the hashed password from SQLite as bytes, but the type mismatch between the stored bytes and the verification process causes `bcrypt.checkpw()` to fail.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type LoginAttempt {email: string, password: string}
  OUTPUT: boolean
  
  RETURN userExists(input.email) 
         AND userWasRegisteredPreviously(input.email)
         AND userLoggedOutAndClosedApp()
         AND passwordHashStoredAsRawBytes(input.email)
END FUNCTION
```

### Examples

- **Example 1**: User registers with email "alice@example.com" and password "SecurePass123". Password hash is stored as raw bytes. User logs out and closes app. User attempts to log in with same credentials → receives "Invalid email or password" error (BUG)

- **Example 2**: User registers with email "bob@example.com" and password "MyPassword456". Password hash stored as raw bytes. After logout and app restart, login attempt fails even with correct password (BUG)

- **Example 3**: User registers with email "charlie@example.com" and password "Test789". First login after registration works (password hash just stored). After logout and app restart, login fails (BUG manifests)

- **Edge Case**: User provides incorrect password → should still return "Invalid email or password" (PRESERVED)

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Invalid passwords must continue to be rejected with "Invalid email or password" error
- Non-existent email addresses must continue to be rejected with "Invalid email or password" error
- First-time login after registration must continue to work correctly
- JWT token generation and validation must remain unchanged
- Logout functionality must continue to clear tokens from localStorage

**Scope:**
All inputs that do NOT involve logging in after logout with previously registered credentials should be completely unaffected by this fix. This includes:
- First-time login after registration
- Login attempts with incorrect passwords
- Login attempts with non-existent emails
- Logout and token clearing
- Protected endpoint access with valid tokens

## Hypothesized Root Cause

Based on the bug description and code analysis, the most likely issues are:

1. **Bytes-to-String Encoding Issue**: `bcrypt.hashpw()` returns bytes, but SQLite stores them without proper UTF-8 encoding. When retrieved, the bytes may not match the original bytes due to encoding/decoding mismatches.

2. **Type Mismatch in Password Verification**: The `bcrypt.checkpw()` function expects both parameters to be bytes. If the stored hash is retrieved as a string or improperly encoded bytes, the comparison fails.

3. **SQLite Type Handling**: SQLite's TEXT column may not properly preserve binary data when storing raw bytes without encoding.

4. **Missing Decode Step**: The password hash is never decoded to a string before storage, causing retrieval issues.

## Correctness Properties

Property 1: Bug Condition - Login After Logout with Correct Credentials

_For any_ login attempt where the user was previously registered, logged out, and closed the app, and provides the correct password, the fixed login_user function SHALL verify the password successfully and return the user object with id, username, and email.

**Validates: Requirements 2.3, 2.4**

Property 2: Preservation - Invalid Credentials and First-Time Login

_For any_ login attempt where the bug condition does NOT hold (invalid password, non-existent email, or first-time login after registration), the fixed code SHALL produce the same result as the original code, preserving all existing authentication behavior including rejection of invalid credentials and successful first-time logins.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**File**: `backend/db.py`

**Function**: `register_user()` and `login_user()`

**Specific Changes**:

1. **Decode Password Hash Before Storage (register_user)**:
   - After `bcrypt.hashpw()` returns bytes, decode to UTF-8 string
   - Store the string in SQLite instead of raw bytes
   - Change: `hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode('utf-8')`

2. **Encode Password Hash Before Verification (login_user)**:
   - When retrieving the password hash from SQLite, it comes back as a string
   - Encode it back to bytes before passing to `bcrypt.checkpw()`
   - Change: `if bcrypt.checkpw(password.encode(), hashed_pw.encode('utf-8')):`

3. **Ensure Consistent Encoding**:
   - Use UTF-8 encoding consistently throughout both functions
   - Verify that the stored hash can be retrieved and re-encoded without data loss

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that simulate user registration, logout, and login attempts. Run these tests on the UNFIXED code to observe failures and understand the root cause.

**Test Cases**:
1. **Register and Login Same Session**: Register user, immediately login with same credentials (will pass on unfixed code)
2. **Register, Logout, Login**: Register user, simulate logout (clear token), then login with same credentials (will fail on unfixed code - demonstrates bug)
3. **Multiple Logout-Login Cycles**: Register user, logout/login multiple times (will fail after first logout on unfixed code)
4. **Invalid Password After Logout**: Register user, logout, attempt login with wrong password (should fail on both - preserved behavior)

**Expected Counterexamples**:
- `login_user("user@example.com", "correctpassword")` returns None instead of user object after logout
- Password verification fails even with correct credentials
- Possible causes: bytes/string type mismatch, encoding issues, SQLite storage problems

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := login_user_fixed(input.email, input.password)
  ASSERT result IS NOT None
  ASSERT result.email = input.email
  ASSERT result.id > 0
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT login_user_original(input.email, input.password) = login_user_fixed(input.email, input.password)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED code first for invalid credentials and first-time logins, then write property-based tests capturing that behavior.

**Test Cases**:
1. **Invalid Password Preservation**: Verify that incorrect passwords continue to return None on both original and fixed code
2. **Non-Existent Email Preservation**: Verify that non-existent emails continue to return None on both original and fixed code
3. **First-Time Login Preservation**: Verify that first-time login after registration continues to work on both original and fixed code
4. **Multiple Users Preservation**: Verify that multiple users can be registered and logged in independently

### Unit Tests

- Test password hashing and encoding for single user registration
- Test password verification for single user login
- Test that invalid passwords are rejected
- Test that non-existent emails are rejected
- Test edge cases (empty password, special characters in password)

### Property-Based Tests

- Generate random email/password combinations and verify registration/login cycles work correctly
- Generate random invalid credentials and verify they are rejected consistently
- Test that multiple users can be registered and logged in independently
- Test that logout/login cycles work correctly for multiple users

### Integration Tests

- Test full registration → logout → login flow
- Test multiple logout/login cycles
- Test that JWT tokens are properly generated after successful login
- Test that protected endpoints work with tokens from re-login after logout
