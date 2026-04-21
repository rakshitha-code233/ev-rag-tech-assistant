# Implementation Plan: Chat Message Persistence During Navigation

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Message Loss on Navigation During Loading
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: Scope the property to concrete failing cases — any message sent while navigating away during loading
  - Test that sending a message and navigating away during response loading persists the message (from Bug Condition in design: `isBugCondition` returns true when `input.eventType = 'send-message'` AND `input.navigationTiming = 'during-response-loading'` AND `messagePersistedBeforeNavigation = false`)
  - The test assertions should match the Expected Behavior from design: message is persisted immediately and not lost when navigating away
  - Run test on UNFIXED code — message will be lost when navigating away during loading
  - **EXPECTED OUTCOME**: Test FAILS (this is correct — it proves the bug exists)
  - Document counterexamples found (e.g., "message lost when navigating away during loading; conversation not created until response arrives")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 3: Preservation** - Existing Message Sending Flows Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Observe: sending a message on a fresh chat session creates a new conversation on unfixed code
  - Observe: sending a message on an existing conversation updates that conversation on unfixed code
  - Observe: multiple messages in sequence are handled correctly on unfixed code
  - Observe: error handling shows errors to the user on unfixed code
  - Write property-based tests capturing these observed behaviors from Preservation Requirements in design:
    - For all normal message sends (no navigation during loading), behavior is identical to original
    - For all new conversation creates, conversation is created as before
    - For all existing conversation updates, conversation is updated as before
    - For all error conditions, errors are shown as before
  - Verify all tests PASS on UNFIXED code (confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Fix: implement optimistic message persistence
  - **Goal**: Save user message immediately to database, then append response when it arrives

  - [x] 3.1 Add abort controller to ChatPage.jsx for cleanup
    - Import `useRef` (already imported)
    - Create `const abortControllerRef = useRef(null)` at top of component
    - Add cleanup effect that aborts pending requests on unmount:
      ```javascript
      useEffect(() => {
        return () => {
          if (abortControllerRef.current) {
            abortControllerRef.current.abort()
          }
        }
      }, [])
      ```
    - This prevents memory leaks and ensures pending requests don't update unmounted components
    - _Bug_Condition: Without abort handling, pending requests may try to update state after unmount_
    - _Expected_Behavior: Pending requests are canceled when component unmounts_
    - _Preservation: All other component behavior remains unchanged_
    - _Requirements: 2.1, 2.3_

  - [x] 3.2 Refactor handleSubmit to implement optimistic persistence
    - Change the flow from: add to state → wait for response → save to database
    - To: add to state → **immediately save to database** → wait for response → append response to database
    - Specific changes:
      1. Add user message to state immediately (already done)
      2. **Immediately save/update conversation** with just the user message (NEW)
      3. Then send message to assistant API
      4. When response arrives, append it to the persisted conversation (NEW)
      5. Handle errors gracefully
    - Implementation details:
      - For new conversations: call `saveConversation(title, [userMessage])` immediately
      - For existing conversations: call `updateConversation(convId, [...currentMessages, userMessage])` immediately
      - After response arrives: call `updateConversation(convId, [...allMessages, assistantMessage])`
      - If save fails, show error but don't block user from sending
    - _Bug_Condition: `isBugCondition(input)` where `input.eventType = 'send-message'` AND `input.navigationTiming = 'during-response-loading'`_
    - _Expected_Behavior: User message is persisted immediately, not lost on navigation_
    - _Preservation: Normal message sending (without navigation during loading) produces same behavior as before_
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 3.3 Handle abort errors gracefully
    - When a request is aborted (component unmounted), don't show an error to the user
    - The message is already persisted, so it will be there when the user returns
    - Check if error is an AbortError: `if (err.name === 'AbortError') { /* don't show error */ }`
    - For other errors, show the error as before
    - _Bug_Condition: Without abort error handling, users see confusing errors when navigating away_
    - _Expected_Behavior: Abort errors are silently ignored, other errors are shown_
    - _Preservation: Error handling for non-abort errors remains unchanged_
    - _Requirements: 2.1, 2.3_

  - [x] 3.4 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Message Persists on Navigation During Loading
    - **IMPORTANT**: Re-run the SAME test from task 1 — do NOT write a new test
    - The test from task 1 encodes the expected behavior: message is persisted immediately and not lost
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.3_

  - [x] 3.5 Verify preservation tests still pass
    - **Property 3: Preservation** - Existing Message Sending Flows Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all preservation tests still pass after the fix (no regressions in message sending, conversation creation, or error handling)
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 4. Write unit tests for message persistence
  - Create `frontend/src/test/ChatPage.messagepersistence.test.jsx`
  - Test that `handleSubmit` immediately persists the user message
  - Test that the response is appended to the persisted conversation
  - Test that navigating away during loading doesn't lose the message
  - Test that returning to Chat shows the persisted message
  - Test that new conversations are created correctly
  - Test that existing conversations are updated correctly
  - Test that error handling works as before
  - Test that abort controller cancels pending requests on unmount
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 5. Write integration tests for message persistence
  - Create `frontend/src/test/ChatPage.integration.test.jsx`
  - Full flow: send message → navigate away during loading → return to Chat → message persists
  - Full flow: send message → navigate away → response arrives → return to Chat → response persists
  - Full flow: send multiple messages → navigate away → return → all messages persist
  - Full flow: new conversation → send message → navigate away → return → conversation created and message persists
  - Full flow: existing conversation → send message → navigate away → return → message added to conversation
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 6. Checkpoint — Ensure all tests pass
  - Run the full test suite and confirm all tests pass
  - Verify the bug condition exploration test (Property 1) passes — bug is fixed
  - Verify all preservation tests (Property 3) pass — no regressions
  - Manually verify the end-to-end flow: send message → navigate away during loading → return to Chat → message persists
  - Manually verify normal message sending is unaffected: send message → wait for response → message and response both persist
  - Ask the user if any questions arise before closing the spec

</content>
</invoke>