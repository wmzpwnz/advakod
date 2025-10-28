import { useAuth } from '../contexts/AuthContext';
import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * Упрощенный хук для WebSocket чата - БЕЗ useWebSocket!
 */
export const useChatWebSocket = (sessionId, onNewMessage, onTyping, onSessionUpdate) => {
  const { user } = useAuth();
  const typingTimeoutRef = useRef(null);
  const isTypingRef = useRef(false);
  const websocketRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 3;
  const reconnectTimeoutRef = useRef(null);
  const pingIntervalRef = useRef(null);

  // Функция создания WebSocket соединения
  const createWebSocket = useCallback(() => {
    if (!user) return null;
    
    const token = localStorage.getItem('token');
    if (!token) return null;
    
    // Защита от множественных подключений
    if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected, skipping creation');
      return websocketRef.current;
    }
    
    // Закрываем старое соединение перед созданием нового
    if (websocketRef.current) {
      websocketRef.current.close();
      websocketRef.current = null;
    }
    
    // Защита от некорректных sessionId
    const cleanSessionId = sessionId ? String(sessionId).replace(/[^0-9]/g, '') : null;
    
    // Используем переменные окружения для WebSocket URL
    const wsBaseUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
    const wsProtocol = wsBaseUrl.startsWith('wss://') ? 'wss://' : 'ws://';
    const wsHost = wsBaseUrl.replace(/^wss?:\/\//, '');
    
    let url;
    if (cleanSessionId && cleanSessionId.length > 0) {
      url = `${wsBaseUrl}/session/${cleanSessionId}?token=${token}`;
    } else {
      url = `${wsBaseUrl}/general?token=${token}`;
    }
    
    console.log('Creating WebSocket connection to:', url);
    
    // Закрываем старое соединение перед созданием нового
    if (websocketRef.current) {
      websocketRef.current.close();
      websocketRef.current = null;
    }
    
    try {
      const ws = new WebSocket(url);
      websocketRef.current = ws;
      
      ws.onopen = () => {
        console.log('WebSocket connected successfully');
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket message received:', data);
          
          if (data.type === 'pong') {
            console.log('Pong received');
            return;
          }
          
          // Обрабатываем другие сообщения
          switch (data.type) {
            case 'new_message':
              onNewMessage?.(data.data);
              break;
            case 'typing':
              onTyping?.(data.user_id, data.is_typing);
              break;
            case 'session_update':
              onSessionUpdate?.(data.data);
              break;
            case 'generation_stopped':
              // Обработка остановки генерации
              console.log('Generation stopped:', data.message);
              // Можно добавить callback для обработки остановки
              break;
            default:
              console.log('Unknown message type:', data.type);
              break;
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };
      
      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setIsConnected(false);

        // НЕ переподключаемся при фатальных ошибках
        if (event.code === 1008 || event.code === 404 || event.code === 1003) {
          console.log('Permanent error, not reconnecting');
          return;
        }

        // Переподключение с ограничениями для других ошибок
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          const delay = 1000 * reconnectAttemptsRef.current;
          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            createWebSocket();
          }, delay);
        } else {
          console.log('Max reconnection attempts reached');
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      return ws;
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      return null;
    }
  }, [user, sessionId, onNewMessage, onTyping, onSessionUpdate]);

  // Ping для поддержания соединения
  useEffect(() => {
    if (!isConnected) return;
    
    pingIntervalRef.current = setInterval(() => {
      if (websocketRef.current?.readyState === WebSocket.OPEN) {
        websocketRef.current.send(JSON.stringify({
          type: 'ping',
          timestamp: Date.now()
        }));
      }
    }, 30000); // Каждые 30 секунд
    
    return () => {
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
      }
    };
  }, [isConnected]);

  // Подключение при монтировании
  useEffect(() => {
    if (user && sessionId !== undefined) {
      // Защита от множественных подключений
      if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
        console.log('WebSocket already connected, skipping creation');
        return;
      }
      createWebSocket();
    }

    return () => {
      // Очистка при размонтировании
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
      }
      if (websocketRef.current) {
        websocketRef.current.close();
        websocketRef.current = null;
      }
    };
  }, [user, sessionId, createWebSocket]);

  // Функция для отправки сообщений
  const sendMessage = useCallback((message) => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      try {
        // Добавляем sessionId ко всем сообщениям
        const payload = {
          ...message,
          session_id: sessionId
        };
        websocketRef.current.send(JSON.stringify(payload));
        return true;
      } catch (error) {
        console.error('Error sending WebSocket message:', error);
        return false;
      }
    }
    console.warn('WebSocket not connected, message not sent');
    return false;
  }, [sessionId]);

  // Функция для отправки уведомления о печати с debounce
  const sendTyping = useCallback((isTyping) => {
    if (isTypingRef.current === isTyping) return;

    // При начале печати — отправляем сразу
    if (isTyping) {
      isTypingRef.current = true;
      sendMessage({ type: 'typing', is_typing: true });

      // Авто-сброс через 3 секунды
      clearTimeout(typingTimeoutRef.current);
      typingTimeoutRef.current = setTimeout(() => {
        sendTyping(false);
      }, 3000);
    } else {
      // При окончании — небольшая задержка, чтобы не гасить при быстрой печати
      clearTimeout(typingTimeoutRef.current);
      typingTimeoutRef.current = setTimeout(() => {
        isTypingRef.current = false;
        sendMessage({ type: 'typing', is_typing: false });
      }, 300);
    }
  }, [sendMessage]);

  // Функция для присоединения к новой сессии
  const joinSession = useCallback((newSessionId) => {
    sendMessage({
      type: 'join_session',
      session_id: newSessionId
    });
  }, [sendMessage]);

  // Функция для отправки чат-сообщений
  const sendChatMessage = useCallback((content) => {
    return sendMessage({
      type: 'new_message',
      content: content
    });
  }, [sendMessage]);

  // Функция для остановки генерации
  const stopGeneration = useCallback(() => {
    return sendMessage({
      type: 'stop_generation'
    });
  }, [sendMessage]);

  // Функция для ручного подключения
  const connect = useCallback(() => {
    if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }
    createWebSocket();
  }, [createWebSocket]);

  // Функция для отключения
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (websocketRef.current) {
      websocketRef.current.close();
      websocketRef.current = null;
    }
    setIsConnected(false);
  }, []);

  return {
    isConnected,
    sendTyping,
    joinSession,
    sendChatMessage,
    stopGeneration,
    connect,
    disconnect
  };
};
