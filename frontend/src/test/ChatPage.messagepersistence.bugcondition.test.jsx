import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import ChatPage from '../pages/ChatPage'
import * as historyService from '../services/historyService'
import * as chatService from '../services/chatService'
import { useAuth } from '../contexts/AuthContext'

// Mock the services
vi.mock('../services/historyService')
vi.mock('../services/chatService')
vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}))

/**
 * Bug Condition Exploration Test
 * 
 * Property 1: Bug Condition - Message Loss on Navigation During Loading
 * 
 * CRITICAL: This test MUST FAIL on unfixed code — failure confirms the bug exists
 * 
 * The bug manifests when:
 * 1. User sends a message
 * 2. Response is loading (isLoading = true)
 * 3. User navigates away (component unmounts)
 * 4. Message is lost because it was never persisted to the database
 * 
 * Expected behavior (after fix):
 * - User message is persisted immediately to the database
 * - Message is not lost when navigating away during loading
 * - When user returns to Chat, the message is still there
 */

describe('ChatPage - Bug Condition: Message Persistence During Navigation', () => {
  const mockUser = { username: 'testuser', sub: 'user123' }
  const mockConversation = {
    id: 1,
    title: 'Test conversation',
    messages: [],
    created_at: new Date().toISOString(),
  }

  beforeEach(() => {
    // Mock useAuth hook
    vi.mocked(useAuth).mockReturnValue({
      user: mockUser,
      isAuthenticated: true,
    })

    // Mock API calls
    vi.mocked(historyService.getHistory).mockResolvedValue([])
    vi.mocked(historyService.getConversation).mockResolvedValue(mockConversation)
    vi.mocked(historyService.saveConversation).mockResolvedValue({ id: 1 })
    vi.mocked(historyService.updateConversation).mockResolvedValue({ id: 1 })

    // Mock sendMessage to simulate slow response
    vi.mocked(chatService.sendMessage).mockImplementation(
      () =>
        new Promise((resolve) => {
          setTimeout(() => {
            resolve({
              answer: 'This is the assistant response.',
            })
          }, 2000) // 2 second delay to simulate loading
        })
    )
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  /**
   * Test Case 1: Message is persisted immediately when sent
   * 
   * EXPECTED OUTCOME on UNFIXED code: FAIL
   * - saveConversation is NOT called immediately
   * - saveConversation is only called after response arrives
   * 
   * EXPECTED OUTCOME on FIXED code: PASS
   * - saveConversation is called immediately with the user message
   */
  it('should persist user message immediately to database when sent (not wait for response)', async () => {
    const { unmount } = render(
      <BrowserRouter>
        <ChatPage />
      </BrowserRouter>
    )

    // Wait for component to load
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/ask me anything/i)).toBeInTheDocument()
    })

    const input = screen.getByPlaceholderText(/ask me anything/i)
    const sendButton = screen.getByRole('button', { name: /send/i })

    // Send a message
    await userEvent.type(input, 'How to charge Tesla Model 3?')
    fireEvent.click(sendButton)

    // CRITICAL: On UNFIXED code, saveConversation should NOT be called yet
    // because the response is still loading
    // On FIXED code, saveConversation should be called immediately
    await waitFor(() => {
      expect(historyService.saveConversation).toHaveBeenCalled()
    })

    // Verify the message was saved with the user message
    const saveCall = vi.mocked(historyService.saveConversation).mock.calls[0]
    expect(saveCall[0]).toBe('How to charge Tesla Model 3?') // title
    expect(saveCall[1]).toHaveLength(1) // one message (user message)
    expect(saveCall[1][0].role).toBe('user')
    expect(saveCall[1][0].content).toBe('How to charge Tesla Model 3?')

    // Unmount component (simulate navigation away)
    unmount()
  })

  /**
   * Test Case 2: Message is not lost when navigating away during loading
   * 
   * EXPECTED OUTCOME on UNFIXED code: FAIL
   * - Message is lost because it was never persisted
   * - When component remounts, messages array is empty
   * 
   * EXPECTED OUTCOME on FIXED code: PASS
   * - Message is persisted immediately
   * - When component remounts, message is still there
   */
  it('should not lose message when navigating away during response loading', async () => {
    const { unmount, rerender } = render(
      <BrowserRouter>
        <ChatPage />
      </BrowserRouter>
    )

    // Wait for component to load
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/ask me anything/i)).toBeInTheDocument()
    })

    const input = screen.getByPlaceholderText(/ask me anything/i)
    const sendButton = screen.getByRole('button', { name: /send/i })

    // Send a message
    await userEvent.type(input, 'How to charge Tesla Model 3?')
    fireEvent.click(sendButton)

    // Wait for message to be added to state
    await waitFor(() => {
      expect(screen.getByText('How to charge Tesla Model 3?')).toBeInTheDocument()
    })

    // Verify saveConversation was called immediately (on FIXED code)
    expect(historyService.saveConversation).toHaveBeenCalled()
    const conversationId = 1

    // Simulate navigation away (component unmounts) while response is loading
    unmount()

    // Simulate returning to Chat (component remounts)
    // On FIXED code, the message should be persisted in the database
    // On UNFIXED code, the message is lost
    vi.mocked(historyService.getConversation).mockResolvedValue({
      id: conversationId,
      title: 'How to charge Tesla Model 3?',
      messages: [
        {
          role: 'user',
          content: 'How to charge Tesla Model 3?',
          timestamp: new Date().toISOString(),
        },
      ],
      created_at: new Date().toISOString(),
    })

    const { rerender: rerenderAfterReturn } = render(
      <BrowserRouter>
        <ChatPage />
      </BrowserRouter>
    )

    // Wait for conversation to load
    await waitFor(() => {
      expect(screen.getByText('How to charge Tesla Model 3?')).toBeInTheDocument()
    })

    // CRITICAL: On UNFIXED code, this will fail because the message is lost
    // On FIXED code, this will pass because the message was persisted
    expect(screen.getByText('How to charge Tesla Model 3?')).toBeInTheDocument()
  })

  /**
   * Test Case 3: New conversation is created immediately when sending first message
   * 
   * EXPECTED OUTCOME on UNFIXED code: FAIL
   * - Conversation is not created until response arrives
   * - If user navigates away during loading, conversation is never created
   * 
   * EXPECTED OUTCOME on FIXED code: PASS
   * - Conversation is created immediately when first message is sent
   * - Message is persisted even if user navigates away
   */
  it('should create new conversation immediately when sending first message (not wait for response)', async () => {
    const { unmount } = render(
      <BrowserRouter>
        <ChatPage />
      </BrowserRouter>
    )

    // Wait for component to load
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/ask me anything/i)).toBeInTheDocument()
    })

    const input = screen.getByPlaceholderText(/ask me anything/i)
    const sendButton = screen.getByRole('button', { name: /send/i })

    // Send first message (no conversationId yet)
    await userEvent.type(input, 'First message')
    fireEvent.click(sendButton)

    // CRITICAL: On UNFIXED code, saveConversation should NOT be called yet
    // On FIXED code, saveConversation should be called immediately
    await waitFor(() => {
      expect(historyService.saveConversation).toHaveBeenCalled()
    })

    // Verify conversation was created with the message
    expect(historyService.saveConversation).toHaveBeenCalledWith(
      'First message',
      expect.arrayContaining([
        expect.objectContaining({
          role: 'user',
          content: 'First message',
        }),
      ])
    )

    // Unmount before response arrives
    unmount()
  })

  /**
   * Test Case 4: Existing conversation is updated immediately when sending message
   * 
   * EXPECTED OUTCOME on UNFIXED code: FAIL
   * - Conversation is not updated until response arrives
   * - If user navigates away during loading, message is never added to conversation
   * 
   * EXPECTED OUTCOME on FIXED code: PASS
   * - Conversation is updated immediately with the new message
   * - Message is persisted even if user navigates away
   */
  it('should update existing conversation immediately when sending message (not wait for response)', async () => {
    const { unmount } = render(
      <BrowserRouter>
        <ChatPage />
      </BrowserRouter>
    )

    // Wait for component to load
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/ask me anything/i)).toBeInTheDocument()
    })

    const input = screen.getByPlaceholderText(/ask me anything/i)
    const sendButton = screen.getByRole('button', { name: /send/i })

    // Send first message to create conversation
    await userEvent.type(input, 'First message')
    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(historyService.saveConversation).toHaveBeenCalled()
    })

    // Clear mocks to track second message
    vi.clearAllMocks()

    // Send second message (conversation already exists)
    await userEvent.type(input, 'Second message')
    fireEvent.click(sendButton)

    // CRITICAL: On UNFIXED code, updateConversation should NOT be called yet
    // On FIXED code, updateConversation should be called immediately
    await waitFor(() => {
      expect(historyService.updateConversation).toHaveBeenCalled()
    })

    // Verify conversation was updated with the new message
    const updateCall = vi.mocked(historyService.updateConversation).mock.calls[0]
    expect(updateCall[0]).toBe(1) // conversation ID
    expect(updateCall[1]).toContainEqual(
      expect.objectContaining({
        role: 'user',
        content: 'Second message',
      })
    )

    // Unmount before response arrives
    unmount()
  })

  /**
   * Test Case 5: Response is appended to persisted conversation when it arrives
   * 
   * EXPECTED OUTCOME on UNFIXED code: FAIL
   * - Response is never appended because message was never persisted
   * 
   * EXPECTED OUTCOME on FIXED code: PASS
   * - Response is appended to the persisted conversation
   * - Both message and response are in the database
   */
  it('should append response to persisted conversation when response arrives', async () => {
    render(
      <BrowserRouter>
        <ChatPage />
      </BrowserRouter>
    )

    // Wait for component to load
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/ask me anything/i)).toBeInTheDocument()
    })

    const input = screen.getByPlaceholderText(/ask me anything/i)
    const sendButton = screen.getByRole('button', { name: /send/i })

    // Send a message
    await userEvent.type(input, 'How to charge?')
    fireEvent.click(sendButton)

    // Wait for message to be persisted
    await waitFor(() => {
      expect(historyService.saveConversation).toHaveBeenCalled()
    })

    // Wait for response to arrive and be appended
    await waitFor(
      () => {
        expect(screen.getByText('This is the assistant response.')).toBeInTheDocument()
      },
      { timeout: 3000 }
    )

    // Verify updateConversation was called with both message and response
    const updateCalls = vi.mocked(historyService.updateConversation).mock.calls
    expect(updateCalls.length).toBeGreaterThan(0)

    // Last call should have both message and response
    const lastCall = updateCalls[updateCalls.length - 1]
    const messages = lastCall[1]
    expect(messages).toContainEqual(
      expect.objectContaining({
        role: 'user',
        content: 'How to charge?',
      })
    )
    expect(messages).toContainEqual(
      expect.objectContaining({
        role: 'assistant',
        content: 'This is the assistant response.',
      })
    )
  })
})
