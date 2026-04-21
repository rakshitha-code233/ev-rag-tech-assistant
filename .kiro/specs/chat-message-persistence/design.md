# Chat Message Persistence Bugfix Design

## Overview

When a user sends a message and navigates away while the response is loading, the message is lost because it's only saved to the database after the response arrives. The fix implements **optimistic persistence**: save the user message immediately to the database, then append the response when it arrives.

The fix has two coordinated parts:
1. **ChatPage.jsx** — save user message immediately (optimistic persistence), then append response when it arrives
2. **Abort handling** — cancel pending requests on component unmount to prevent memory leaks

The fix is surgical and preserves all existing behavior for normal message sending flows.

---

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — a user sends a message and navigates away before the response arrives
- **Property (P)**: The desired behavior when the bug condition holds — the user message is persisted immediately, not lost on navigation
- **Preservation**: All behaviors that must remain unchanged — new conversation creation, message sending, error handling
- **Optimistic persistence**: Saving the user message to the database immediately, before waiting for the response
- **Abort controller**: A mechanism to cancel pending requests when the component unmounts
- **`handleSubmit`**: The function in ChatPage that handles message submission
- **`saveConversation`**: The function that creates a new conversation in the database
- **`updateConversation`**: The function that updates an existing conversation with new messages
- **`sendMessage`**: The function that sends a message to the assistant API and returns the response

---

## Bug Details

### Bug Condition

The bug manifests when a user sends a message and navigates away before the response arrives. The current flow is:

1. User sends message → `handleSubmit` adds message to state
2. `sendMessage` API call starts (async)
3. User navigates away → ChatPage component unmounts
4. Component unmounts → pending state updates are canceled
5. Response arrives → callback never executes → message never saved to database
6. User returns to Chat → component remounts with empty state → message is lost

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input — a user interaction event with timing
  OUTPUT: boolean

  RETURN input.eventType = 'send-message'
         AND input.navigationTiming = 'during-response-loading'
         AND messagePersistedBeforeNavigation = false
END FUNCTION
```

### Examples

- **Example 1**: User on `/chat` → types "How to charge?" → sends → response loading → clicks Dashboard → returns to Chat → message gone, chat empty
- **Example 2**: User on `/chat/42` → sends message → navigates away during loading → returns → old messages load, but new message missing
- **Example 3**: User sends message → slow network (5+ second response) → navigates away after 2 seconds → returns → message lost

---

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Sending a message on a fresh chat session must still create a new conversation
- Sending a message on an existing conversation must still update that conversation
- Multiple messages in sequence must be handled correctly without race conditions
- Error handling must continue to show errors to the user
- Navigation between pages without pending requests must work as before
- Voice input and transcription must continue to work

**Scope:**
All interactions that do NOT involve navigating away during response loading should be completely unaffected by this fix.

---

## Correctness Properties

**Property 1: Optimistic Message Persistence**

_For any_ user interaction where `isBugCondition` returns true (a message is sent and the user navigates away during loading), the fixed application SHALL immediately persist the user message to the database before waiting for the response, ensuring the message is not lost if the component unmounts.

**Validates: Requirements 2.1, 2.3**

**Property 2: Response Persistence After Navigation**

_For any_ user interaction where a response arrives after navigation, the fixed application SHALL append the response to the persisted conversation when the component remounts or when the response arrives, ensuring the response is not lost.

**Validates: Requirements 2.2, 2.4, 2.5**

**Property 3: Preservation - Existing Flows Unchanged**

_For any_ interaction where `isBugCondition` returns false (normal message sending without navigation during loading), the fixed code SHALL produce exactly the same behavior as the original code, preserving all existing message-sending, conversation-creation, and error-handling functionality.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

---

## Fix Implementation

### Changes Required

**File 1**: `frontend/src/pages/ChatPage.jsx`

**Specific Changes**:

1. **Import AbortController** at the top of the file (built-in browser API)

2. **Create abort controller in component**:
   ```javascript
   const abortControllerRef = useRef(null)
   ```

3. **Add cleanup effect** to abort pending requests on unmount:
   ```javascript
   useEffect(() => {
     return () => {
       if (abortControllerRef.current) {
         abortControllerRef.current.abort()
       }
     }
   }, [])
   ```

4. **Refactor `handleSubmit` to use optimistic persistence**:
   - Add user message to state immediately
   - **Immediately save/update conversation** (optimistic persistence) with just the user message
   - Then send message to assistant API
   - When response arrives, append it to the persisted conversation
   - Handle errors gracefully

   **Pseudocode**:
   ```javascript
   const handleSubmit = async (text) => {
     if (!text.trim() || isLoading) return

     const userMessage = { role: 'user', content: text, timestamp: ... }
     
     // 1. Add to state immediately
     setMessages(prev => [...prev, userMessage])
     setIsLoading(true)
     setChatError('')

     try {
       // 2. Optimistic persistence: save user message immediately
       const title = text.slice(0, 80)
       let convId = conversationId
       if (!convId) {
         const res = await saveConversation(title, [userMessage])
         convId = res.id
         setConversationId(convId)
       } else {
         await updateConversation(convId, [userMessage])
       }

       // 3. Send message to assistant
       const data = await sendMessage(text)
       const assistantMessage = { role: 'assistant', content: data.answer, timestamp: ... }

       // 4. Append response to persisted conversation
       setMessages(prev => [...prev, assistantMessage])
       await updateConversation(convId, [...messages, userMessage, assistantMessage])
     } catch (err) {
       setChatError('Unable to get a response. Please try again.')
     } finally {
       setIsLoading(false)
     }
   }
   ```

5. **Handle abort errors gracefully**:
   - If the request is aborted (component unmounted), don't show an error
   - The message is already persisted, so it will be there when the user returns

---

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on the unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix.

**Test Cases**:
1. **Message loss on navigation**: Send message, navigate away before response arrives, return to Chat → assert message is persisted (will fail on unfixed code)
2. **Conversation creation during loading**: Send first message, navigate away during loading, return → assert conversation was created (will fail on unfixed code)
3. **Response persistence**: Send message, navigate away, wait for response, return → assert response is persisted (will fail on unfixed code)

**Expected Counterexamples**:
- User message is lost when navigating away during loading
- Conversation is not created until response arrives
- Returning to Chat shows empty state instead of pending message

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed application produces the expected behavior.

**Pseudocode**:
```
FOR ALL (message, navigation_timing) WHERE bug_condition(send_message AND navigate_during_loading) DO
  result := fixedApp.handleMessageAndNavigation(message, navigation_timing)
  ASSERT result.messagePersistedImmediately = true
  ASSERT result.messageNotLostOnReturn = true
  ASSERT result.responsePersistedWhenArrives = true
END FOR
```

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed application produces the same behavior as the original.

**Pseudocode**:
```
FOR ALL input WHERE NOT bug_condition(input) DO
  ASSERT fixedApp.behavior(input) = originalApp.behavior(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking.

**Test Cases**:
1. **Normal message sending**: Send message, wait for response, no navigation → behavior unchanged
2. **New conversation creation**: Send first message on `/chat` → conversation created as before
3. **Existing conversation update**: Send message on `/chat/:id` → conversation updated as before
4. **Multiple messages**: Send multiple messages in sequence → all handled correctly
5. **Error handling**: Network error during send → error shown as before

### Unit Tests

- Test that `handleSubmit` immediately persists the user message
- Test that the response is appended to the persisted conversation
- Test that navigating away during loading doesn't lose the message
- Test that returning to Chat shows the persisted message
- Test that new conversations are created correctly
- Test that existing conversations are updated correctly
- Test that error handling works as before
- Test that abort controller cancels pending requests on unmount

### Property-Based Tests

- Generate random message sequences and navigation timings, verify messages are never lost
- Generate random response delays and verify responses are persisted correctly
- Generate random error conditions and verify error handling is unchanged

### Integration Tests

- Full flow: send message → navigate away during loading → return to Chat → message persists
- Full flow: send message → navigate away → response arrives → return to Chat → response persists
- Full flow: send multiple messages → navigate away → return → all messages persist
- Full flow: new conversation → send message → navigate away → return → conversation created and message persists
- Full flow: existing conversation → send message → navigate away → return → message added to conversation

</content>
</invoke>