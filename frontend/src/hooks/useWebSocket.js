import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * Хук для работы с WebSocket соединением
 */
export const useWebSocket = (url, options = {}) => {
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  const [lastMessage, setLastMessage] = useState(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = options.maxReconnectAttempts || 3; // Уменьшили до 3 попыток
  const reconnectInterval = options.reconnectInterval || 5000; // Увеличили интервал

  const connect = useCallback(() => {
    if (!url) return;
    
    try {
      console.log('Connecting to WebSocket:', url);
      const ws = new WebSocket(url);
      
      ws.onopen = () => {
        console.log('WebSocket connected to:', url);
        setIsConnected(true);
        setError(null);
        reconnectAttempts.current = 0;
        
        // Отправляем ping для поддержания соединения
        if (options.autoPing) {
          const pingInterval = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
              console.log('Sending ping...');
              ws.send(JSON.stringify({
                type: 'ping',
                timestamp: Date.now()
              }));
            } else {
              console.log('WebSocket not open, clearing ping interval');
              clearInterval(pingInterval);
            }
          }, 10000); // Ping каждые 10 секунд для быстрого тестирования
        }
      };

      ws.onmessage = (event) => {
        try {
          console.log('WebSocket message received:', event.data);
          const data = JSON.parse(event.data);
          setLastMessage(data);
          
          // Обрабатываем pong ответы
          if (data.type === 'pong') {
            console.log('WebSocket pong received:', data);
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setIsConnected(false);
        
        // Автоматическое переподключение с экспоненциальной задержкой
        if (options.autoReconnect && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++;
          const delay = Math.min(reconnectInterval * Math.pow(2, reconnectAttempts.current - 1), 30000);
          console.log(`Attempting to reconnect... (${reconnectAttempts.current}/${maxReconnectAttempts}) in ${delay}ms`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        } else if (reconnectAttempts.current >= maxReconnectAttempts) {
          console.error('Max reconnection attempts reached. WebSocket will not reconnect automatically.');
          setError('Connection failed after maximum retry attempts');
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('WebSocket connection error');
      };

      setSocket(ws);
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setError('Failed to create WebSocket connection');
    }
  }, [url, options, maxReconnectAttempts, reconnectInterval]);

  const disconnect = useCallback(() => {
    console.log('Disconnecting WebSocket');
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (socket) {
      socket.close();
      setSocket(null);
      setIsConnected(false);
    }
  }, [socket]);

  const sendMessage = useCallback((message) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
      return true;
    }
    return false;
  }, [socket]);

  // Подключение при монтировании
  useEffect(() => {
    if (options.autoConnect !== false && url) {
      // Защита от множественных подключений
      if (socket && socket.readyState === WebSocket.OPEN) {
        return;
      }
      connect();
    }

    return () => {
      disconnect();
    };
  }, [connect, disconnect, options.autoConnect, url, socket]);

  return {
    socket,
    isConnected,
    error,
    lastMessage,
    connect,
    disconnect,
    sendMessage
  };
};
