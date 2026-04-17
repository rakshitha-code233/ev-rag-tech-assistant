/**
 * Bug Condition Exploration Test — Property 1
 *
 * **Validates: Requirements 1.1, 1.2**
 *
 * CRITICAL: This test is EXPECTED TO FAIL on unfixed code.
 * Failure confirms the bug exists:
 *   - navigate('/chat') is called instead of navigate('/chat/<id>')
 *
 * DO NOT fix the test or the code when it fails.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import * as fc from 'fast-check'
import * as historyService from '../services/historyService'

// ---------------------------------------------------------------------------
// Mock layout components that depend on contexts not relevant to this test
// ---------------------------------------------------------------------------
vi.mock('../components/layout/Sidebar', () => ({
  default: () => <nav data-testid="sidebar" />,
}))

vi.mock('../components/layout/Header', () => ({
  default: () => <header data-testid="header" />,
}))

// ---------------------------------------------------------------------------
// Mock useNavigate at module level so we can capture calls
// ---------------------------------------------------------------------------
const mockNavigate = vi.fn()

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal()
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// ---------------------------------------------------------------------------
// Arbitraries
// ---------------------------------------------------------------------------

/**
 * Generates a conversation object with a valid (non-null, positive integer) id.
 * This matches the isBugCondition predicate:
 *   input.eventType = 'history-item-click'
 *   AND input.conversation.id IS NOT NULL
 *   AND navigatedRoute DOES NOT CONTAIN input.conversation.id  ← bug
 */
const validConversationArb = fc.record({
  id: fc.integer({ min: 1, max: 100_000 }),
  title: fc
    .string({ minLength: 1, maxLength: 80 })
    .filter((s) => s.trim().length > 0 && !s.includes('\0')),
  created_at: fc.constant('2024-01-01T00:00:00Z'),
})

const nonEmptyConversationListArb = fc.array(validConversationArb, {
  minLength: 1,
  maxLength: 5,
})

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('Property 1 — Bug Condition: History Item Click Discards Conversation ID', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  /**
   * **Validates: Requirements 1.1**
   *
   * For any list of conversations with valid IDs, clicking a conversation item
   * MUST call navigate('/chat/<conv.id>').
   *
   * On UNFIXED code: navigate('/chat') is called — the ID is discarded.
   * EXPECTED OUTCOME: PASSES after fix (confirms bug is fixed)
   * Counterexample: navigate called with '/chat' instead of '/chat/<id>'
   */
  it('clicking a history item calls navigate with the conversation id in the path', async () => {
    const { default: HistoryPage } = await import('../pages/HistoryPage')

    await fc.assert(
      fc.asyncProperty(nonEmptyConversationListArb, async (conversations) => {
        vi.clearAllMocks()
        vi.spyOn(historyService, 'getHistory').mockResolvedValue(conversations)

        const { unmount, container } = render(
          <MemoryRouter initialEntries={['/history']}>
            <Routes>
              <Route path="/history" element={<HistoryPage />} />
            </Routes>
          </MemoryRouter>
        )

        // Wait for the first conversation button to appear (scoped to this render)
        const firstConv = conversations[0]
        const button = await within(container).findByText(firstConv.title)

        // Click the conversation item
        fireEvent.click(button)

        // ASSERTION: navigate must be called with '/chat/<id>'
        // On UNFIXED code this FAILS because navigate('/chat') is called (no id)
        expect(mockNavigate).toHaveBeenCalledWith(`/chat/${firstConv.id}`)

        unmount()
      }),
      { numRuns: 10 }
    )
  }, 30000)
})
