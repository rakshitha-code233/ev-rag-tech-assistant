# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - History Item Click Discards Conversation ID
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bug exists
  - **Scoped PBT Approach**: Scope the property to concrete failing cases — any conversation object with a valid `id` clicked in `HistoryPage`
  - Test that clicking a conversation item in `HistoryPage` calls `navigate('/chat/<conv.id>')` for all conversations with a valid `id` (from Bug Condition in design: `isBugCondition` returns true when `input.eventType = 'history-item-click'` AND `input.conversation.id IS NOT NULL` AND `navigatedRoute` does not contain the ID)
  - The test assertions should match the Expected Behavior from design: `navigate` is called with `` `/chat/${conv.id}` `` and `ChatPage` renders the conversation's messages rather than `EmptyState`
  - Run test on UNFIXED code — `navigate` will be called with `'/chat'` instead of `'/chat/42'`
  - **EXPECTED OUTCOME**: Test FAILS (this is correct — it proves the bug exists)
  - Document counterexamples found (e.g., "`navigate` called with `'/chat'` instead of `'/chat/42'`; `ChatPage` renders `EmptyState` even when `useParams` returns `{ id: '42' }`")
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - New-Chat and Other Flows Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Observe: navigating to `/chat` (no ID) renders `EmptyState` on unfixed code
  - Observe: submitting a message on a fresh `/chat` session calls `sendMessage` and appends the assistant response on unfixed code
  - Observe: `HistoryPage` fetches and renders all conversations with titles and timestamps on unfixed code
  - Observe: filtering conversations by title on `HistoryPage` correctly narrows the list on unfixed code
  - Write property-based tests capturing these observed behaviors from Preservation Requirements in design:
    - For all direct `/chat` navigations (no `:id` param), `ChatPage` renders `EmptyState` and does NOT call the history API
    - For all new-message submissions on a fresh session, `sendMessage` is called and the response is appended to `messages`
    - For all history list loads, `getHistory()` is called and all returned conversations are rendered
    - For all search queries, the filtered list matches conversations whose titles include the query string
  - Verify all tests PASS on UNFIXED code (confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Fix: history item click navigates to conversation and loads messages

  - [x] 3.1 Update `HistoryPage.jsx` navigation call to include conversation ID
    - Change `onClick={() => navigate('/chat')}` to `onClick={() => navigate(\`/chat/${conv.id}\`)}`
    - This is the primary bug fix — ensures the conversation ID is included in the route
    - _Bug_Condition: `isBugCondition(input)` where `input.eventType = 'history-item-click'` AND `input.conversation.id IS NOT NULL` AND `navigatedRoute` does not contain the ID_
    - _Expected_Behavior: `navigate` is called with `` `/chat/${conv.id}` `` so the URL carries the conversation identifier_
    - _Preservation: All other `navigate` calls and page interactions remain unchanged_
    - _Requirements: 2.1_

  - [x] 3.2 Add `/chat/:id` parameterized route in `App.jsx`
    - Add `<Route path="/chat/:id" element={<ChatPage />} />` inside the `ProtectedRoute` block, directly after the existing `<Route path="/chat" element={<ChatPage />} />`
    - Both routes render `ChatPage`; the existing `/chat` route is untouched
    - _Bug_Condition: React Router cannot match `/chat/42` without this route, so the URL change from 3.1 would result in a redirect to `/`_
    - _Expected_Behavior: `/chat/:id` resolves to `ChatPage` with the `:id` param available via `useParams`_
    - _Preservation: The existing `/chat` route and all other routes are unchanged_
    - _Requirements: 2.1_

  - [x] 3.3 Add `GET /api/history/<int:conversation_id>` endpoint to `flask_api.py`
    - Add a new route that fetches a single conversation by ID for the authenticated user
    - Query: `SELECT id, title, messages, created_at FROM chat_history WHERE id=? AND user_id=?`
    - Return 404 with `{"error": "Conversation not found"}` if the row does not exist or belongs to another user
    - Parse `messages` JSON field before returning, defaulting to `[]` on parse error
    - _Bug_Condition: Without this endpoint, `ChatPage` would need to fetch all conversations and filter client-side, which is inefficient and couples the fix to `getHistory()`_
    - _Expected_Behavior: `GET /api/history/<id>` returns `{id, title, messages, created_at}` for the authenticated user's conversation_
    - _Preservation: Existing `GET /api/history` and `POST /api/history` endpoints are unchanged_
    - _Requirements: 2.2_

  - [x] 3.4 Add `getConversation(id)` helper to `historyService.js`
    - Add `export async function getConversation(id) { const response = await api.get(\`/api/history/${id}\`); return response.data }`
    - Existing `getHistory()` and `saveConversation()` functions are unchanged
    - _Requirements: 2.2_

  - [x] 3.5 Update `ChatPage.jsx` to read URL param and load conversation
    - Import `useParams` from `react-router-dom`
    - Read `const { id } = useParams()` at the top of the component
    - Add a `useEffect` that depends on `id`:
      - If `id` is present: call `getConversation(id)` from `historyService`, set `messages` state with the returned messages; handle loading and error states
      - If `id` is absent: ensure `messages` remains `[]` (new-chat flow — no change to existing behavior)
    - Import `getConversation` from `../services/historyService`
    - _Bug_Condition: Without `useParams`, `ChatPage` ignores the `:id` segment and always renders `EmptyState`_
    - _Expected_Behavior: When `id` is present, `ChatPage` fetches the conversation and populates `messages`, replacing `EmptyState` with the conversation's message list_
    - _Preservation: When `id` is absent (`/chat` route), `messages` stays `[]` and `EmptyState` renders exactly as before; `handleSubmit`, voice input, and all other interactions are unchanged_
    - _Requirements: 2.2, 3.1, 3.2_

  - [x] 3.6 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - History Item Click Loads Conversation
    - **IMPORTANT**: Re-run the SAME test from task 1 — do NOT write a new test
    - The test from task 1 encodes the expected behavior: `navigate` called with `` `/chat/${conv.id}` `` and `ChatPage` renders conversation messages
    - When this test passes, it confirms the expected behavior is satisfied
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bug is fixed)
    - _Requirements: 2.1, 2.2_

  - [x] 3.7 Verify preservation tests still pass
    - **Property 2: Preservation** - New-Chat and Other Flows Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all preservation tests still pass after the fix (no regressions in new-chat flow, message sending, history list, or search)

- [x] 4. Checkpoint — Ensure all tests pass
  - Run the full test suite and confirm all tests pass
  - Verify the bug condition exploration test (Property 1) passes — bug is fixed
  - Verify all preservation tests (Property 2) pass — no regressions
  - Manually verify the end-to-end flow: log in → History page → click a conversation → URL changes to `/chat/:id` → conversation messages are displayed
  - Manually verify the new-chat flow is unaffected: navigate to `/chat` directly → `EmptyState` renders → send a message → response appears
  - Ask the user if any questions arise before closing the spec
