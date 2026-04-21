import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
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
 * Preservation Property Tests
 * 
 * Property 3: Preservation - Existing Message Sending Flows Unchanged
 * 
 * IMPORTANT: Follow observation-first methodology
 * 
 * These tests verify that normal message sending flows (without navigation during loading)
 * continue to work exactly as before after the fix is implemented.
 * 
 * All tests should PASS on UNFIXED code (confirms baseline behavior to preserve)
 */

describe('ChatPage - Preservation: Existing Message Sending Flows Unchanged', () => {
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

    // Mock sendMessage with quick response
    vi.mocked(chatService.sendMessage).mockResolvedValue({
      answer: 'This is the assistant response.',
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  /**
   * Test Case 1: New conversation creation on first message
   * 
   * EXPECTED OUTCOME: PASS on UNFIXED code
   * - Sending first message creates a new conversation
   * - Conversation is saved to history
   * - Message and response are both persisted
   */
  it('should create new conversation when sending first message on fresh chat', async () => {
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

    // Send first message
    await userEvent.type(input, 'First question')
    fireEvent.click(sendButton)

    // Verify conversation was created
    await waitFor(() => {
      expect(historyService.saveConversation).toHaveBeenCalled()
    })

    // Verify the conversation was created with correct title and message
    expect(historyService.saveConversation).toHaveBeenCalledWith(
      'First question',
      expect.arrayContaining([
        expect.objectContaining({
          role: 'user',
          content: 'First question',
        }),
      ])
    )
  })

  /**
   * Test Case 2: Existing conversation update on subsequent messages
   * 
   * EXPECTED OUTCOME: PASS on UNFIXED code
   * - Sending message to existing conversation updates it
   * - New message is added to the conversation
   * - Both old and new messages are persisted
   */
  it('should update existing conversation when sending message', async () => {
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

    // Send first message
    await userEvent.type(input, 'First message')
    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(historyService.saveConversation).toHaveBeenCalled()
    })

    // Clear mocks to track second message
    vi.clearAllMocks()

    // Send second message
    await userEvent.type(input, 'Second message')
    fireEvent.click(sendButton)

    // Verify conversation was updated
    await waitFor(() => {
      expect(historyService.updateConversation).toHaveBeenCalled()
    })

    // Verify the update includes the new message
    const updateCall = vi.mocked(historyService.updateConversation).mock.calls[0]
    expect(updateCall[1]).toContainEqual(
      expect.objectContaining({
        role: 'user',
        content: 'Second message',
      })
    )
  })

  /**
   * Test Case 3: Multiple messages in sequence are handled correctly
   * 
   * EXPECTED OUTCOME: PASS on UNFIXED code
   * - Sending multiple messages in sequence works correctly
   * - Each message is added to the conversation
   * - No race conditions or lost messages
   */
  it('should handle multiple messages in sequence without race conditions', async () => {
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

    // Send first message
    await userEvent.type(input, 'Message 1')
    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(screen.getByText('Message 1')).toBeInTheDocument()
    })

    // Send second message
    await userEvent.type(input, 'Message 2')
    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(screen.getByText('Message 2')).toBeInTheDocument()
    })

    // Send third message
    await userEvent.type(input, 'Message 3')
    fireEvent.click(sendButton)

    await waitFor(() => {
      expect(screen.getByText('Message 3')).toBeInTheDocument()
    })

    // Verify all messages are displayed
    expect(screen.getByText('Message 1')).toBeInTheDocument()
    expect(screen.getByText('Message 2')).toBeInTheDocument()
    expect(screen.getByText('Message 3')).toBeInTheDocument()
  })

  /**
   * Test Case 4: Error handling shows errors to user
   * 
   * EXPECTED OUTCOME: PASS on UNFIXED code
   * - Network errors are shown to the user
   * - Error message is displayed
   * - User can retry
   */
  it('should show error message when message sending fails', async () => {
    // Mock sendMessage to fail
    vi.mocked(chatService.sendMessage).mockRejectedValue(new Error('Network error'))

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

    // Send message
    await userEvent.type(input, 'Test message')
    fireEvent.click(sendButton)

    // Verify error is shown
    await waitFor(() => {
      expect(screen.getByText(/unable to get a response/i)).toBeInTheDocument()
    })
  })

  /**
   * Test Case 5: Response is displayed after message is sent
   * 
   * EXPECTED OUTCOME: PASS on UNFIXED code
   * - Message is sent and response is received
   * - Both message and response are displayed
   * - Response is shown after message
   */
  it('should display response after message is sent', async () => {
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

    // Send message
    await userEvent.type(input, 'How to charge?')
    fireEvent.click(sendButton)

    // Wait for response to be displayed
    await waitFor(() => {
      expect(screen.getByText('This is the assistant response.')).toBeInTheDocument()
    })

    // Verify both message and response are displayed
    expect(screen.getByText('How to charge?')).toBeInTheDocument()
    expect(screen.getByText('This is the assistant response.')).toBeInTheDocument()
  })

  /**
   * Test Case 6: Empty state is shown when no messages
   * 
   * EXPECTED OUTCOME: PASS on UNFIXED code
   * - Fresh chat shows empty state
   * - Empty state has suggestions
   * - User can click suggestions to send message
   */
  it('should show empty state on fresh chat', async () => {
    render(
      <BrowserRouter>
        <ChatPage />
      </BrowserRouter>
    )

    // Wait for empty state to render
    await waitFor(() => {
      expect(screen.getByText(/EV Diagnostic Assistant/i)).toBeInTheDocument()
    })

    // Verify empty state is shown
    expect(screen.getByText(/ask me anything about ev diagnostics/i)).toBeInTheDocument()
  })

  /**
   * Test Case 7: Typing indicator shows while response is loading
   * 
   * EXPECTED OUTCOME: PASS on UNFIXED code
   * - Typing indicator is shown while response is loading
   * - Typing indicator disappears when response arrives
   */
  it('should show typing indicator while response is loading', async () => {
    // Mock sendMessage with delay
    vi.mocked(chatService.sendMessage).mockImplementation(
      () =>
        new Promise((resolve) => {
          setTimeout(() => {
            resolve({ answer: 'Response' })
          }, 500)
        })
    )

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

    // Send message
    await userEvent.type(input, 'Test')
    fireEvent.click(sendButton)

    // Verify typing indicator is shown
    await waitFor(() => {
      expect(screen.getByTestId('typing-indicator')).toBeInTheDocument()
    })

    // Wait for response
    await waitFor(() => {
      expect(screen.getByText('Response')).toBeInTheDocument()
    })

    // Verify typing indicator is gone
    expect(screen.queryByTestId('typing-indicator')).not.toBeInTheDocument()
  })

  /**
   * Test Case 8: Input field is cleared after message is sent
   * 
   * EXPECTED OUTCOME: PASS on UNFIXED code
   * - Input field is cleared after message is sent
   * - User can type new message immediately
   */
  it('should clear input field after message is sent', async () => {
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

    // Send message
    await userEvent.type(input, 'Test message')
    fireEvent.click(sendButton)

    // Wait for response
    await waitFor(() => {
      expect(screen.getByText('This is the assistant response.')).toBeInTheDocument()
    })

    // Verify input field is cleared
    expect(input).toHaveValue('')
  })
})
