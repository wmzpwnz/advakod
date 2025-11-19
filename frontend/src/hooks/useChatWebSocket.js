import { useAuth } from '../contexts/AuthContext';
import { useCallback, useEffect, useRef, useState } from 'react';
import ResilientWebSocket from '../services/ResilientWebSocket';
import { WS_BASE_URL } from '../config/api';

/**
 * Обработка закрытия WebSocket соединения
 */
const handleWebSocketClose = (code, reason) => {
  const errorMap = {
    1008: 'Authentication failed',
    1003: 'Access denied', 
    1011: 'Server error',
    1006: 'Connection lost',
    1000: 'Normal closure'
  };
  
  const message = errorMap[code] || 'Unknown error';
  console.log(`WebSocket closed: ${code} - ${message} (${reason})`);
  
  // Не переподключаемся при ошибках аутентификации и доступа
  const permanentErrors = [1008, 1003];
  return !permanentErrors.includes(code);
};

/**
 * Хук для WebSocket чата с использованием ResilientWebSocket
 * Реализует требования 2.2, 2.3, 6.3 из спецификации
 */
export const useChatWebSocket = (sessionId, onNewMessage, onTyping, onSessionUpdate) => {
  const { user } = useAuth();
  const typingTimeoutRef = useRef(null);
  const isTypingRef = useRef(false);
  const websocketRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionState, setConnectionState] = useState('disconnected');

  // Функция создания ResilientWebSocket соединения
  const createWebSocket = useCallback(() => {
    if (!user) return null;
    
    const token = localStorage.getItem('token');
    if (!token) return null;
    
    // Закрываем старое соединение перед созданием нового
    if (websocketRef.current) {
      websocketRef.current.disconnect();
      websocketRef.current = null;
    }
    
    // Защита от некорректных sessionId
    const cleanSessionId = sessionId ? String(sessionId).replace(/[^0-9]/g, '') : null;
    
    // Используем общий конфиг для WebSocket URL (без localhost по умолчанию)
    const wsBaseUrl = process.env.REACT_APP_WS_URL || WS_BASE_URL;
    
    let url;
    if (cleanSessionId && cleanSessionId.length > 0) {
      url = `${wsBaseUrl}/session/${cleanSessionId}?token=${token}`;
    } else {
      url = `${wsBaseUrl}/general?token=${token}`;
    }
    
    console.log('Creating ResilientWebSocket connection to:', url);
    
    try {
      const ws = new ResilientWebSocket(url, {
        maxReconnectAttempts: 10,
        reconnectDelay: 1000,
        maxReconnectDelay: 30000,
        pingInterval: 30000,
        pongTimeout: 10000
      });
      
      websocketRef.current = ws;
      
      // Обработчики событий
      ws.on('open', () => {
        console.log('ResilientWebSocket connected successfully');
        setIsConnected(true);
      });
      
      ws.on('close', ({ code, reason }) => {
        console.log('ResilientWebSocket closed:', code, reason);
        setIsConnected(false);
      });
      
      ws.on('stateChange', (state) => {
        console.log('ResilientWebSocket state changed:', state);
        setConnectionState(state);
        setIsConnected(state === 'connected');
      });
      
      ws.on('message', (data) => {
        console.log('ResilientWebSocket message received:', data);
        
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
            console.log('Generation stopped:', data.message);
            break;
          default:
            console.log('Unknown message type:', data.type);
            break;
        }
      });
      
      ws.on('error', (error) => {
        console.error('ResilientWebSocket error:', error);
      });
      
      // Подключаемся
      ws.connect().catch(error => {
        console.error('Failed to connect ResilientWebSocket:', error);
      });
      
      return ws;
    } catch (err) {
      console.error('Failed to create ResilientWebSocket:', err);
      return null;
    }
  }, [user, sessionId, onNewMessage, onTyping, onSessionUpdate]);

  // Ping/pong обрабатывается автоматически в ResilientWebSocket

  // Подключение при монтировании
  useEffect(() => {
    if (user && sessionId !== undefined) {
      createWebSocket();
    }

    return () => {
      // Очистка при размонтировании
      if (typingTimeoutRef.current) {
        clearTimeout(typingTimeoutRef.current);
      }
      if (websocketRef.current) {
        websocketRef.current.disconnect();
        websocketRef.current = null;
      }
    };
  }, [user, sessionId, createWebSocket]);

  // Функция для отправки сообщений
  const sendMessage = useCallback((message) => {
    if (websocketRef.current) {
      // Добавляем sessionId ко всем сообщениям
      const payload = {
        ...message,
        session_id: sessionId
      };
      return websocketRef.current.send(payload);
    }
    console.warn('ResilientWebSocket not available, message queued');
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
    if (websocketRef.current && websocketRef.current.isConnected) {
      console.log('ResilientWebSocket already connected');
      return;
    }
    createWebSocket();
  }, [createWebSocket]);

  // Функция для отключения
  const disconnect = useCallback(() => {
    if (websocketRef.current) {
      websocketRef.current.disconnect();
      websocketRef.current = null;
    }
    setIsConnected(false);
    setConnectionState('disconnected');
  }, []);

  // Функция для принудительного переподключения
  const forceReconnect = useCallback(() => {
    if (websocketRef.current) {
      websocketRef.current.reconnect();
    } else {
      createWebSocket();
    }
  }, [createWebSocket]);

  return {
    isConnected,
    connectionState,
    websocket: websocketRef.current,
    sendTyping,
    joinSession,
    sendChatMessage,
    stopGeneration,
    connect,
    disconnect,
    forceReconnect
  };
};
