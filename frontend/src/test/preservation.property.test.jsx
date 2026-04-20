/**
 * Preservation Property Tests — Property 2
 *
 * **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
 *
 * These tests capture baseline behaviors that MUST remain unchanged after the
 * bug fix is applied. They are written against UNFIXED code and MUST PASS on
 * unfixed code — passing here establishes the baseline to preserve.
 *
 * Observation-first methodology:
 *  - Observed: /chat (no ID) always renders EmptyState on unfixed code (no useParams)
 *  - Observed: submitting a message calls sendMessage and appends the response
 *  - Observed: HistoryPage calls getHistory() on mount and renders all conversations
 *  - Observed: HistoryPage filters by title substring match (case-insensitive)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within, cleanup, act } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import * as fc from 'fast-check'
import * as historyService from '../services/historyService'
import * as chatService from '../services/chatService'

// ---------------------------------------------------------------------------
// Mock layout components (no relevant context for these tests)
// ---------------------------------------------------------------------------
vi.mock('../components/layout/Sidebar', () => ({
  default: () => <nav data-testid="sidebar" />,
}))

vi.mock('../components/layout/Header', () => ({
  default: () => <header data-testid="header" />,
}))

// Mock AuthContext so ChatPage can read user without a real auth provider
vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ user: { username: 'testuser' }, isAuthenticated: true }),
  AuthProvider: ({ children }) => children,
}))

// Mock ThemeContext to avoid provider errors
vi.mock('../contexts/ThemeContext', () => ({
  useTheme: () => ({ theme: 'light', toggleTheme: vi.fn() }),
  ThemeProvider: ({ children }) => children,
}))

// Mock the health-check API call made by ChatPage on mount
vi.mock('../services/api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: { transcription_available: false } }),
    post: vi.fn(),
  },
}))

// ---------------------------------------------------------------------------
// Arbitraries
// ---------------------------------------------------------------------------

/** A conversation object with a valid positive integer id and non-empty title.
 *  Titles are trimmed to avoid leading/trailing whitespace issues in getByText.
 *  IDs are unique per list (ensured by uniqueArray below). */
const conversationArb = fc.record({
  id: fc.integer({ min: 1, max: 100_000 }),
  title: fc
    .string({ minLength: 1, maxLength: 80 })
    .filter((s) => s.trim().length > 0 && !s.includes('\0'))
    .map((s) => s.trim()), // trim to avoid whitespace-only differences
  created_at: fc.constant('2024-01-01T00:00:00Z'),
})

/**
 * A non-empty list of conversations with unique IDs and unique titles.
 * Unique titles prevent false positives when asserting getByText.
 */
const conversationListArb = fc
  .uniqueArray(conversationArb, {
    minLength: 1,
    maxLength: 5,
    selector: (c) => c.title, // deduplicate by title
  })

/** A non-empty, printable search query string */
const searchQueryArb = fc
  .string({ minLength: 1, maxLength: 20 })
  .filter((s) => s.trim().length > 0 && !s.includes('\0'))

/** A non-empty message text */
const messageTextArb = fc
  .string({ minLength: 1, maxLength: 200 })
  .filter((s) => s.trim().length > 0 && !s.includes('\0'))

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function renderChatPage() {
  const { default: ChatPage } = await import('../pages/ChatPage')
  return render(
    <MemoryRouter initialEntries={['/chat']}>
      <Routes>
        <Route path="/chat" element={<ChatPage />} />
      </Routes>
    </MemoryRouter>
  )
}

async function renderHistoryPage() {
  const { default: HistoryPage } = await import('../pages/HistoryPage')
  return render(
    <MemoryRouter initialEntries={['/history']}>
      <Routes>
        <Route path="/history" element={<HistoryPage />} />
      </Routes>
    </MemoryRouter>
  )
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('Property 2 — Preservation: New-Chat and Other Flows Unchanged', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    cleanup()
  })

  // -------------------------------------------------------------------------
  // 3.1 — Direct /chat navigation renders EmptyState, no history API call
  // -------------------------------------------------------------------------

  /**
   * **Validates: Requirements 3.1**
   *
   * For all direct /chat navigations (no :id param), ChatPage renders EmptyState
   * and does NOT call the history API.
   *
   * Observed on unfixed code: ChatPage has no useParams call, so it always
   * renders EmptyState and never touches historyService.
   *
   * EXPECTED OUTCOME: PASSES on unfixed code (baseline behavior to preserve)
   */
  it('direct /chat navigation renders EmptyState and does not call getHistory', async () => {
    await fc.assert(
      fc.asyncProperty(fc.constant(null), async () => {
        cleanup()
        vi.clearAllMocks()
        const getHistorySpy = vi.spyOn(historyService, 'getHistory')

        const { container } = await renderChatPage()

        // EmptyState is identified by its heading text
        expect(
          within(container).getByText('EV Diagnostic Assistant')
        ).toBeInTheDocument()

        // getHistory must NOT have been called
        expect(getHistorySpy).not.toHaveBeenCalled()

        cleanup()
      }),
      { numRuns: 5 }
    )
  })

  // -------------------------------------------------------------------------
  // 3.2 — New-message submission calls sendMessage and appends response
  // -------------------------------------------------------------------------

  /**
   * **Validates: Requirements 3.2**
   *
   * For all new-message submissions on a fresh /chat session, sendMessage is
   * called with the user's text and the assistant response is appended to the
   * message list.
   *
   * Observed on unfixed code: handleSubmit calls sendMessage and sets messages
   * state with both the user message and the assistant response.
   * ChatInput submits via Enter keydown (no form element).
   *
   * EXPECTED OUTCOME: PASSES on unfixed code (baseline behavior to preserve)
   */
  it('submitting a message calls sendMessage and appends the assistant response', async () => {
    await fc.assert(
      fc.asyncProperty(messageTextArb, async (messageText) => {
        cleanup()
        vi.clearAllMocks()

        const answerText = `Answer for: ${messageText}`
        vi.spyOn(chatService, 'sendMessage').mockResolvedValue({ answer: answerText })
        // saveConversation is best-effort; mock it to avoid network errors
        vi.spyOn(historyService, 'saveConversation').mockResolvedValue({ id: 1 })

        const { container } = await renderChatPage()

        // Find the text input scoped to this render's container
        const input = within(container).getByLabelText('Chat message input')
        fireEvent.change(input, { target: { value: messageText } })

        // Submit by pressing Enter (ChatInput listens for Enter keydown)
        await act(async () => {
          fireEvent.keyDown(input, { key: 'Enter', code: 'Enter', charCode: 13 })
        })

        // sendMessage must have been called with the user's text (trimmed, as ChatPage does)
        expect(chatService.sendMessage).toHaveBeenCalledWith(messageText.trim())

        // The assistant response must appear in the DOM
        await waitFor(() => {
          expect(within(container).getByText(answerText)).toBeInTheDocument()
        })

        cleanup()
      }),
      { numRuns: 5 }
    )
  })

  // -------------------------------------------------------------------------
  // 3.3 — History list load: getHistory() called and all conversations rendered
  // -------------------------------------------------------------------------

  /**
   * **Validates: Requirements 3.3**
   *
   * For all history list loads, getHistory() is called and all returned
   * conversations are rendered with their titles.
   *
   * Observed on unfixed code: HistoryPage calls getHistory() in a useEffect on
   * mount and renders each conversation as a button with its title.
   *
   * EXPECTED OUTCOME: PASSES on unfixed code (baseline behavior to preserve)
   */
  it('HistoryPage calls getHistory and renders all returned conversations', async () => {
    await fc.assert(
      fc.asyncProperty(conversationListArb, async (conversations) => {
        cleanup()
        vi.clearAllMocks()
        vi.spyOn(historyService, 'getHistory').mockResolvedValue(conversations)

        const { container } = await renderHistoryPage()

        // getHistory must have been called
        await waitFor(() => {
          expect(historyService.getHistory).toHaveBeenCalledTimes(1)
        })

        // Every conversation title must appear in the DOM.
        // Titles are unique within the generated list (uniqueArray by title),
        // so getByText is safe here.
        for (const conv of conversations) {
          await waitFor(() => {
            expect(within(container).getByText(conv.title)).toBeInTheDocument()
          })
        }

        cleanup()
      }),
      { numRuns: 8, timeout: 30000 }
    )
  }, 60000)

  // -------------------------------------------------------------------------
  // 3.4 — Search filtering: filtered list matches titles containing the query
  // -------------------------------------------------------------------------

  /**
   * **Validates: Requirements 3.4**
   *
   * For all search queries, the filtered list matches conversations whose titles
   * include the query string (case-insensitive), and conversations that do NOT
   * match are not rendered.
   *
   * Observed on unfixed code: HistoryPage filters `conversations` by
   * `c.title.toLowerCase().includes(debouncedQuery.toLowerCase())`.
   *
   * EXPECTED OUTCOME: PASSES on unfixed code (baseline behavior to preserve)
   */
  it('search query filters conversations to those whose titles include the query', async () => {
    await fc.assert(
      fc.asyncProperty(
        conversationListArb,
        searchQueryArb,
        async (conversations, query) => {
          cleanup()
          vi.clearAllMocks()
          vi.spyOn(historyService, 'getHistory').mockResolvedValue(conversations)

          const { container } = await renderHistoryPage()

          // Wait for conversations to load
          await waitFor(() => {
            expect(historyService.getHistory).toHaveBeenCalledTimes(1)
          })

          // Type the search query into the search input scoped to this container
          const searchInput = within(container).getByRole('searchbox')

          await act(async () => {
            fireEvent.change(searchInput, { target: { value: query } })
            // Advance past the 300ms debounce
            await new Promise((resolve) => setTimeout(resolve, 350))
          })

          const lowerQuery = query.toLowerCase()
          const matching = conversations.filter((c) =>
            c.title.toLowerCase().includes(lowerQuery)
          )
          const nonMatching = conversations.filter(
            (c) => !c.title.toLowerCase().includes(lowerQuery)
          )

          // All matching conversations must be visible.
          // Titles are unique within the list (uniqueArray by title).
          for (const conv of matching) {
            expect(within(container).getByText(conv.title)).toBeInTheDocument()
          }

          // Non-matching conversations must NOT be visible.
          for (const conv of nonMatching) {
            expect(within(container).queryByText(conv.title)).not.toBeInTheDocument()
          }

          cleanup()
        }
      ),
      { numRuns: 8, timeout: 30000 }
    )
  }, 60000)
})
