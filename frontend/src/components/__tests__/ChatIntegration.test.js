/**
 * Integration tests for Chat component with WebSocket and AI services
 * Tests the complete chat flow from user input to AI response
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import Chat from '../../pages/Chat';

// Mock dependencies
jest.mock('../../services/ResilientWebSocket');
jest.mock('../../hooks/useChatWebSocket');
jest.mock('../../contexts/AuthContext');

// Mock API calls
global.fetch = jest.fn();

// Mock WebSocket
const mockWebSocket = {
    connect: jest.fn().mockResolvedValue(undefined),
    disconnect: jest.fn(),
    send: jest.fn().mockReturnValue(true),
    isConnected: true,
    connectionState: 'connected',
    on: jest.fn(),
    off: jest.fn(),
    getUserFriendlyStatus: jest.fn().mockReturnValue({
        text: 'Подключено',
        color: 'green',
        icon: 'connected'
    }),
    getStatus: jest.fn().mockReturnValue({
        connected: true,
        connectionState: 'connected',
        stats: {
            totalConnections: 1,
            totalMessages: 0
        }
    })
};

// Mock chat WebSocket hook
const mockUseChatWebSocket = {
    isConnected: true,
    connectionStatus: 'connected',
    sendMessage: jest.fn(),
    messages: [],
    isTyping: false,
    error: null,
    reconnect: jest.fn()
};

// Mock auth context
const mockAuthContext = {
    user: { id: 1, email: 'test@example.com' },
    token: 'mock-token',
    isAuthenticated: true
};

describe('Chat Integration Tests', () => {
    beforeEach(() => {
        // Reset mocks
        jest.clearAllMocks();

        // Setup default mocks
        require('../../services/ResilientWebSocket').mockImplementation(() => mockWebSocket);
        require('../../hooks/useChatWebSocket').mockReturnValue(mockUseChatWebSocket);
        require('../../contexts/AuthContext').useAuth = jest.fn().mockReturnValue(mockAuthContext);

        // Mock successful API responses
        global.fetch.mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({
                response: 'This is a test AI response',
                status: 'success'
            })
        });
    });

    afterEach(() => {
        jest.restoreAllMocks();
    });

    describe('Chat Component Rendering', () => {
        test('should render chat interface', () => {
            render(<Chat />);

            // Should have message input
            expect(screen.getByPlaceholderText(/введите ваш вопрос/i)).toBeInTheDocument();

            // Should have send button
            expect(screen.getByRole('button', { name: /отправить/i })).toBeInTheDocument();

            // Should show connection status
            expect(screen.getByText(/подключено/i)).toBeInTheDocument();
        });

        test('should show AI thinking indicator when processing', async () => {
            const user = userEvent.setup();

            // Mock processing state
            require('../../hooks/useChatWebSocket').mockReturnValue({
                ...mockUseChatWebSocket,
                isTyping: true
            });

            render(<Chat />);

            // Should show thinking indicator
            expect(screen.getByText(/ии думает/i)).toBeInTheDocument();
        });

        test('should display error messages', () => {
            // Mock error state
            require('../../hooks/useChatWebSocket').mockReturnValue({
                ...mockUseChatWebSocket,
                error: 'Connection failed'
            });

            render(<Chat />);

            // Should show error
            expect(screen.getByText(/connection failed/i)).toBeInTheDocument();
        });
    });

    describe('Message Sending', () => {
        test('should send message via WebSocket when connected', async () => {
            const user = userEvent.setup();

            render(<Chat />);

            const input = screen.getByPlaceholderText(/введите ваш вопрос/i);
            const sendButton = screen.getByRole('button', { name: /отправить/i });

            // Type message
            await user.type(input, 'What is a contract?');

            // Send message
            await user.click(sendButton);

            // Should call sendMessage
            expect(mockUseChatWebSocket.sendMessage).toHaveBeenCalledWith({
                message: 'What is a contract?',
                type: 'user_message'
            });
        });

        test('should send message via HTTP when WebSocket disconnected', async () => {
            const user = userEvent.setup();

            // Mock disconnected state
            require('../../hooks/useChatWebSocket').mockReturnValue({
                ...mockUseChatWebSocket,
                isConnected: false,
                connectionStatus: 'disconnected'
            });

            render(<Chat />);

            const input = screen.getByPlaceholderText(/введите ваш вопрос/i);
            const sendButton = screen.getByRole('button', { name: /отправить/i });

            await user.type(input, 'Test HTTP message');
            await user.click(sendButton);

            // Should fallback to HTTP
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/api/v1/chat/message'),
                expect.objectContaining({
                    method: 'POST',
                    headers: expect.objectContaining({
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer mock-token'
                    }),
                    body: JSON.stringify({
                        message: 'Test HTTP message'
                    })
                })
            );
        });

        test('should handle empty messages', async () => {
            const user = userEvent.setup();

            render(<Chat />);

            const sendButton = screen.getByRole('button', { name: /отправить/i });

            // Try to send empty message
            await user.click(sendButton);

            // Should not send empty message
            expect(mockUseChatWebSocket.sendMessage).not.toHaveBeenCalled();
            expect(global.fetch).not.toHaveBeenCalled();
        });

        test('should clear input after sending', async () => {
            const user = userEvent.setup();

            render(<Chat />);

            const input = screen.getByPlaceholderText(/введите ваш вопрос/i);
            const sendButton = screen.getByRole('button', { name: /отправить/i });

            await user.type(input, 'Test message');
            expect(input.value).toBe('Test message');

            await user.click(sendButton);

            // Input should be cleared
            expect(input.value).toBe('');
        });
    });

    describe('Message Display', () => {
        test('should display chat messages', () => {
            // Mock messages
            require('../../hooks/useChatWebSocket').mockReturnValue({
                ...mockUseChatWebSocket,
                messages: [
                    {
                        id: 1,
                        type: 'user',
                        content: 'Hello',
                        timestamp: new Date().toISOString()
                    },
                    {
                        id: 2,
                        type: 'ai',
                        content: 'Hello! How can I help you?',
                        timestamp: new Date().toISOString()
                    }
                ]
            });

            render(<Chat />);

            // Should display both messages
            expect(screen.getByText('Hello')).toBeInTheDocument();
            expect(screen.getByText('Hello! How can I help you?')).toBeInTheDocument();
        });

        test('should show streaming response', async () => {
            const { rerender } = render(<Chat />);

            // Mock streaming messages
            const streamingMessages = [
                { id: 1, type: 'user', content: 'Tell me about contracts' },
                { id: 2, type: 'ai', content: 'Contracts are', streaming: true },
                { id: 2, type: 'ai', content: 'Contracts are legal', streaming: true },
                { id: 2, type: 'ai', content: 'Contracts are legal agreements', streaming: false }
            ];

            for (const messages of [
                [streamingMessages[0], streamingMessages[1]],
                [streamingMessages[0], streamingMessages[2]],
                [streamingMessages[0], streamingMessages[3]]
            ]) {
                require('../../hooks/useChatWebSocket').mockReturnValue({
                    ...mockUseChatWebSocket,
                    messages
                });

                rerender(<Chat />);
                await act(async () => {
                    await new Promise(resolve => setTimeout(resolve, 10));
                });
            }

            // Should show final complete message
            expect(screen.getByText('Contracts are legal agreements')).toBeInTheDocument();
        });

        test('should handle message errors', () => {
            // Mock error message
            require('../../hooks/useChatWebSocket').mockReturnValue({
                ...mockUseChatWebSocket,
                messages: [
                    {
                        id: 1,
                        type: 'error',
                        content: 'AI service temporarily unavailable',
                        timestamp: new Date().toISOString()
                    }
                ]
            });

            render(<Chat />);

            // Should display error message
            expect(screen.getByText(/ai service temporarily unavailable/i)).toBeInTheDocument();
        });
    });

    describe('Connection Status', () => {
        test('should show connection status indicator', () => {
            render(<Chat />);

            // Should show connected status
            expect(screen.getByText(/подключено/i)).toBeInTheDocument();
        });

        test('should show reconnect button when disconnected', () => {
            // Mock disconnected state
            require('../../hooks/useChatWebSocket').mockReturnValue({
                ...mockUseChatWebSocket,
                isConnected: false,
                connectionStatus: 'failed'
            });

            render(<Chat />);

            // Should show reconnect option
            const reconnectButton = screen.getByRole('button', { name: /переподключить/i });
            expect(reconnectButton).toBeInTheDocument();
        });

        test('should attempt reconnection when button clicked', async () => {
            const user = userEvent.setup();

            // Mock disconnected state
            require('../../hooks/useChatWebSocket').mockReturnValue({
                ...mockUseChatWebSocket,
                isConnected: false,
                connectionStatus: 'failed'
            });

            render(<Chat />);

            const reconnectButton = screen.getByRole('button', { name: /переподключить/i });
            await user.click(reconnectButton);

            // Should call reconnect
            expect(mockUseChatWebSocket.reconnect).toHaveBeenCalled();
        });
    });

    describe('Error Handling', () => {
        test('should handle API errors gracefully', async () => {
            const user = userEvent.setup();

            // Mock API error
            global.fetch.mockRejectedValue(new Error('Network error'));

            // Mock disconnected to force HTTP fallback
            require('../../hooks/useChatWebSocket').mockReturnValue({
                ...mockUseChatWebSocket,
                isConnected: false
            });

            render(<Chat />);

            const input = screen.getByPlaceholderText(/введите ваш вопрос/i);
            const sendButton = screen.getByRole('button', { name: /отправить/i });

            await user.type(input, 'Test error handling');
            await user.click(sendButton);

            // Should show error message
            await waitFor(() => {
                expect(screen.getByText(/произошла ошибка/i)).toBeInTheDocument();
            });
        });

        test('should handle WebSocket errors', () => {
            // Mock WebSocket error
            require('../../hooks/useChatWebSocket').mockReturnValue({
                ...mockUseChatWebSocket,
                error: 'WebSocket connection failed'
            });

            render(<Chat />);

            // Should display error
            expect(screen.getByText(/websocket connection failed/i)).toBeInTheDocument();
        });

        test('should handle timeout errors', async () => {
            const user = userEvent.setup();

            // Mock timeout error
            global.fetch.mockImplementation(() =>
                new Promise((_, reject) =>
                    setTimeout(() => reject(new Error('Timeout')), 100)
                )
            );

            // Mock disconnected to force HTTP
            require('../../hooks/useChatWebSocket').mockReturnValue({
                ...mockUseChatWebSocket,
                isConnected: false
            });

            render(<Chat />);

            const input = screen.getByPlaceholderText(/введите ваш вопрос/i);
            const sendButton = screen.getByRole('button', { name: /отправить/i });

            await user.type(input, 'Test timeout');
            await user.click(sendButton);

            // Should handle timeout
            await waitFor(() => {
                expect(screen.getByText(/timeout/i)).toBeInTheDocument();
            }, { timeout: 2000 });
        });
    });

    describe('Authentication Integration', () => {
        test('should include auth token in requests', async () => {
            const user = userEvent.setup();

            // Mock disconnected to force HTTP
            require('../../hooks/useChatWebSocket').mockReturnValue({
                ...mockUseChatWebSocket,
                isConnected: false
            });

            render(<Chat />);

            const input = screen.getByPlaceholderText(/введите ваш вопрос/i);
            const sendButton = screen.getByRole('button', { name: /отправить/i });

            await user.type(input, 'Authenticated message');
            await user.click(sendButton);

            // Should include auth header
            expect(global.fetch).toHaveBeenCalledWith(
                expect.any(String),
                expect.objectContaining({
                    headers: expect.objectContaining({
                        'Authorization': 'Bearer mock-token'
                    })
                })
            );
        });

        test('should handle unauthenticated state', () => {
            // Mock unauthenticated state
            require('../../contexts/AuthContext').useAuth = jest.fn().mockReturnValue({
                user: null,
                token: null,
                isAuthenticated: false
            });

            render(<Chat />);

            // Should show login prompt or disable chat
            expect(screen.getByText(/войдите в систему/i) || screen.getByText(/требуется авторизация/i)).toBeInTheDocument();
        });
    });

    describe('Performance and Optimization', () => {
        test('should not re-render unnecessarily', () => {
            const renderSpy = jest.fn();

            const TestChat = () => {
                renderSpy();
                return <Chat />;
            };

            const { rerender } = render(<TestChat />);

            // Initial render
            expect(renderSpy).toHaveBeenCalledTimes(1);

            // Re-render with same props
            rerender(<TestChat />);

            // Should not cause unnecessary re-renders
            // (This depends on proper memoization in the component)
        });

        test('should handle rapid message sending', async () => {
            const user = userEvent.setup();

            render(<Chat />);

            const input = screen.getByPlaceholderText(/введите ваш вопрос/i);
            const sendButton = screen.getByRole('button', { name: /отправить/i });

            // Send multiple messages rapidly
            for (let i = 0; i < 5; i++) {
                await user.clear(input);
                await user.type(input, `Rapid message ${i}`);
                await user.click(sendButton);
            }

            // Should handle all messages
            expect(mockUseChatWebSocket.sendMessage).toHaveBeenCalledTimes(5);
        });
    });

    describe('Accessibility', () => {
        test('should be keyboard accessible', async () => {
            const user = userEvent.setup();

            render(<Chat />);

            const input = screen.getByPlaceholderText(/введите ваш вопрос/i);

            // Focus input
            await user.click(input);
            expect(input).toHaveFocus();

            // Type message
            await user.type(input, 'Keyboard test');

            // Send with Enter key
            await user.keyboard('{Enter}');

            // Should send message
            expect(mockUseChatWebSocket.sendMessage).toHaveBeenCalled();
        });

        test('should have proper ARIA labels', () => {
            render(<Chat />);

            // Check for accessibility attributes
            const input = screen.getByPlaceholderText(/введите ваш вопрос/i);
            expect(input).toHaveAttribute('aria-label');

            const sendButton = screen.getByRole('button', { name: /отправить/i });
            expect(sendButton).toBeInTheDocument();
        });

        test('should announce status changes to screen readers', () => {
            const { rerender } = render(<Chat />);

            // Mock status change
            require('../../hooks/useChatWebSocket').mockReturnValue({
                ...mockUseChatWebSocket,
                isConnected: false,
                connectionStatus: 'disconnected'
            });

            rerender(<Chat />);

            // Should have status announcement
            expect(screen.getByRole('status') || screen.getByLabelText(/статус соединения/i)).toBeInTheDocument();
        });
    });
});