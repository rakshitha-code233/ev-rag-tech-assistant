# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Data Isolation Verification
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **GOAL**: Surface counterexamples that demonstrate data isolation bug exists
  - Test implementation details from Bug Condition in design: 
    - Register User A, upload manual, login as User B, verify manual appears (should fail)
    - Register User A, create chat, login as User B, verify chat appears (should fail)
    - Register User A, delete manual, verify User B's manual also deleted (should fail)
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found to understand root cause
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - File Operations and Authentication
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for non-isolation functionality: file validation, message saving, authentication
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Fix data isolation bug

  - [x] 3.1 Implement the fix
    - Update `/api/manuals` endpoint to filter by user_id
    - Update `/api/manuals/upload` endpoint to store in user-specific directory
    - Update `/api/manuals/<filename>` endpoint to verify user ownership
    - Update `/api/history/<id>` endpoints to verify user ownership
    - Create user-specific directories: `DATA_DIR/user_{user_id}/`
    - Update RAG index building to use user-specific directory
    - _Bug_Condition: isBugCondition(input) where user A's data visible to user B_
    - _Expected_Behavior: each user sees only their own manuals and chat history_
    - _Preservation: file validation works, message saving works, authentication works_
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 3.2 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Data Isolation Verification
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 3.3 Verify preservation tests still pass
    - **Property 2: Preservation** - File Operations and Authentication
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix (no regressions)

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

