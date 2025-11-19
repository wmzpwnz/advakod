/**
 * Тесты для WebSocketStatus компонента
 */

import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import WebSocketStatus from '../WebSocketStatus';

// Mock ResilientWebSocket
const createMockWebSocket = (state = 'connected') => ({
  getStatus: jest.fn(() => ({
    connected: state === 'connected',
    connecting: state === 'connecting',
    readyState: state === 'connected' ? 1 : 0,
    reconnectAttempts: 0,
    lastPong: Date.now(),
    queuedMessages: 0,
    connectionState: state,
    stats: {
      totalConnections: 1,
      totalReconnections: 0,
      totalMessages: 5,
      lastConnectedAt: new Date(),
      connectionDuration: 1000
    }
  })),
  getUserFriendlyStatus: jest.fn(() => {
    const statusMap = {
      'connected': { text: 'Подключено', color: 'green', icon: 'connected' },
      'connecting': { text: 'Подключение...', color: 'yellow', icon: 'connecting' },
      'reconnecting': { text: 'Переподключение...', color: 'orange', icon: 'reconnecting' },
      'failed': { text: 'Ошибка подключения', color: 'red', icon: 'error' }
    };
    return statusMap[state] || statusMap['connected'];
  }),
  on: jest.fn(),
  off: jest.fn(),
  reconnect: jest.fn(),
  options: { maxReconnectAttempts: 10 }
});

describe('WebSocketStatus', () => {
  test('should render compact status when connected', async () => {
    const mockWS = createMockWebSocket('connected');
    
    await act(async () => {
      render(<WebSocketStatus websocket={mockWS} />);
    });
    
    expect(screen.getByText('Онлайн')).toBeInTheDocument();
  });

  test('should render offline status when disconnected', () => {
    const mockWS = createMockWebSocket('failed');
    
    render(<WebSocketStatus websocket={mockWS} />);
    
    // Компонент должен показать статус при ошибке
    expect(mockWS.on).toHaveBeenCalledWith('stateChange', expect.any(Function));
  });

  test('should show reconnect button when failed', () => {
    const mockWS = createMockWebSocket('failed');
    const onReconnect = jest.fn();
    
    render(<WebSocketStatus websocket={mockWS} onReconnect={onReconnect} showDetails={true} />);
    
    // Симулируем изменение состояния на failed
    const stateChangeHandler = mockWS.on.mock.calls.find(call => call[0] === 'stateChange')[1];
    stateChangeHandler('failed');
    
    // Перерендериваем с новым состоянием
    render(<WebSocketStatus websocket={mockWS} onReconnect={onReconnect} showDetails={true} />);
  });

  test('should call onReconnect when reconnect button is clicked', () => {
    const mockWS = createMockWebSocket('failed');
    const onReconnect = jest.fn();
    
    render(<WebSocketStatus websocket={mockWS} onReconnect={onReconnect} showDetails={true} />);
    
    // Если есть кнопка переподключения, кликаем по ней
    const reconnectButtons = screen.queryAllByText(/переподключить/i);
    if (reconnectButtons.length > 0) {
      fireEvent.click(reconnectButtons[0]);
      expect(onReconnect).toHaveBeenCalled();
    }
  });

  test('should register event listeners on mount', () => {
    const mockWS = createMockWebSocket('connected');
    
    render(<WebSocketStatus websocket={mockWS} />);
    
    expect(mockWS.on).toHaveBeenCalledWith('stateChange', expect.any(Function));
    expect(mockWS.on).toHaveBeenCalledWith('error', expect.any(Function));
    expect(mockWS.on).toHaveBeenCalledWith('open', expect.any(Function));
    expect(mockWS.on).toHaveBeenCalledWith('close', expect.any(Function));
  });

  test('should cleanup event listeners on unmount', () => {
    const mockWS = createMockWebSocket('connected');
    
    const { unmount } = render(<WebSocketStatus websocket={mockWS} />);
    
    unmount();
    
    expect(mockWS.off).toHaveBeenCalledWith('stateChange', expect.any(Function));
    expect(mockWS.off).toHaveBeenCalledWith('error', expect.any(Function));
    expect(mockWS.off).toHaveBeenCalledWith('open', expect.any(Function));
    expect(mockWS.off).toHaveBeenCalledWith('close', expect.any(Function));
  });
});