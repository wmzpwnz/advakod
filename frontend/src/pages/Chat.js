import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Send, Paperclip, Bot, User, Wifi, WifiOff, File, X, Lightbulb, Mic, Square, RefreshCw, Menu, Settings, Check, History, Clock, ChevronLeft } from 'lucide-react';
import { useChatWebSocket } from '../hooks/useChatWebSocket';
import { useStatusNotifications } from '../hooks/useStatusNotifications';
import {
  LazyFileUpload,
  LazyQuestionTemplates
} from '../components/LazyComponent';
import VoiceRecorder from '../components/VoiceRecorder';
import VoicePlayer from '../components/VoicePlayer';
import ChatHistory from '../components/ChatHistory';
import EnhancedResponse from '../components/EnhancedResponse';
import FeedbackButtons from '../components/FeedbackButtons';
import WebSocketStatus from '../components/WebSocketStatus';
import ErrorMessage from '../components/ErrorMessage';
import AIThinkingIndicator from '../components/AIThinkingIndicator';
import StatusNotificationSystem from '../components/StatusNotificationSystem';
import axios from 'axios';
import { getApiUrl } from '../config/api';

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationStartTime, setGenerationStartTime] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [attachedFiles, setAttachedFiles] = useState([]);
  const [showFileUpload, setShowFileUpload] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const [showVoiceRecorder, setShowVoiceRecorder] = useState(false);
  const [isInputExpanded, setIsInputExpanded] = useState(false);
  const [showModeMenu, setShowModeMenu] = useState(false);
  const [chatMode, setChatMode] = useState('basic'); // 'basic' или 'expert'
  const [modeNotification, setModeNotification] = useState(null);
  const inputAreaRef = useRef(null);
  const modeMenuRef = useRef(null);
  // На мобильных по умолчанию история скрыта, на десктопе - развернута
  const [isHistoryCollapsed, setIsHistoryCollapsed] = useState(() => {
    // Проверяем размер экрана при инициализации
    if (typeof window !== 'undefined') {
      const isMobile = window.innerWidth < 768; // md breakpoint
      // На мобильных история скрыта (true), на десктопе развернута (false)
      return isMobile;
    }
    return false;
  });
  const [focusHistorySearch, setFocusHistorySearch] = useState(false);

  // Сбрасываем флаг фокуса после использования
  useEffect(() => {
    if (focusHistorySearch) {
      const timeoutId = setTimeout(() => {
        setFocusHistorySearch(false);
      }, 1000); // Сбрасываем через 1 секунду после установки
      return () => clearTimeout(timeoutId);
    }
  }, [focusHistorySearch]);
  const [lastError, setLastError] = useState(null);
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const textareaRef = useRef(null);
  const autoScrollRef = useRef(true);
  const currentStreamRef = useRef(null);
  const initializedRef = useRef(false);
  const [announcement, setAnnouncement] = useState('');

  // Хук для уведомлений
  const { showGenerationStopped, showError, showSuccess } = useStatusNotifications();

  const isNearBottom = () => {
    const el = messagesContainerRef.current;
    if (!el) return true;
    const threshold = 120; // px
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    return distanceFromBottom <= threshold;
  };

  const scrollToBottom = () => {
    const el = messagesContainerRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  };

  // Функция остановки генерации (определяется после инициализации WebSocket-хука ниже)
  let stopGeneration; // будет переопределена после объявления wsStopGeneration

  // Обработчик новых сообщений от WebSocket
  const handleNewMessage = useCallback((messageData) => {
    if (!messageData || !messageData.content) {
      console.warn('Received invalid message data:', messageData);
      return;
    }

    const aiMessage = {
      id: `ai_${Date.now()}`,
      type: 'ai',
      content: messageData.content,
      timestamp: new Date().toISOString(),
      enhancements: messageData.enhancements || {}
    };

    setMessages(prev => [...prev, aiMessage]);
    setIsGenerating(false);
  }, []);

  // WebSocket подключение
  const {
    isConnected,
    connectionState,
    websocket,
    sendChatMessage: wsSendChatMessage,
    stopGeneration: wsStopGeneration,
    forceReconnect
  } = useChatWebSocket(sessionId, handleNewMessage);

  // Теперь можем безопасно объявить stopGeneration, ссылаясь на wsStopGeneration
  stopGeneration = useCallback(() => {
    if (currentStreamRef.current) {
      currentStreamRef.current.abort();
      currentStreamRef.current = null;
    }

    if (wsStopGeneration) {
      wsStopGeneration();
    }

    setIsGenerating(false);
    setGenerationStartTime(null);
    
    // Показываем уведомление об остановке
    showGenerationStopped();
  }, [wsStopGeneration]);

  // Инициализация сессии - ТОЛЬКО ОДИН РАЗ
  useEffect(() => {
    if (initializedRef.current) return;
    
    initializedRef.current = true;
    
    // Принудительная очистка кеша при загрузке
    if ('serviceWorker' in navigator && 'caches' in window) {
      caches.keys().then(cacheNames => {
        cacheNames.forEach(cacheName => {
          if (cacheName.includes('advakod')) {
            console.log('Очищаем старый кеш:', cacheName);
            caches.delete(cacheName);
          }
        });
      }).catch(err => console.error('Ошибка очистки кеша:', err));
    }
    
    // Добавляем приветственное сообщение ТОЛЬКО ОДИН РАЗ
    setMessages([{
      id: 'welcome',
      type: 'ai',
      content: 'Привет! Я ваш АдваКОД AI-помощник. Задавайте любые вопросы по российскому законодательству, и я помогу вам разобраться. Можете также загружать документы для анализа.',
      timestamp: new Date().toISOString()
    }]);
    
    // Session ID будет создан на сервере при первом сообщении
  }, []);

  // Загрузка сообщений при выборе сессии из истории
  useEffect(() => {
    console.log('useEffect sessionId изменился:', sessionId, 'initialized:', initializedRef.current);
    
    const loadSessionMessages = async () => {
      // Пропускаем загрузку при первой инициализации (когда еще нет sessionId и компонент только загрузился)
      if (!initializedRef.current && !sessionId) {
        console.log('Пропуск загрузки - первая инициализация без sessionId');
        return;
      }
      
      if (!sessionId) {
        console.log('Нет sessionId, показываем приветственное сообщение');
        // Если нет sessionId, показываем приветственное сообщение для нового чата
        setMessages([{
          id: 'welcome',
          type: 'ai',
          content: 'Привет! Я ваш АдваКОД AI-помощник. Задавайте любые вопросы по российскому законодательству, и я помогу вам разобраться. Можете также загружать документы для анализа.',
          timestamp: new Date().toISOString()
        }]);
        return;
      }

      console.log('🔄 Загрузка сообщений для сессии:', sessionId);
      
      try {
        const apiUrl = getApiUrl(`/chat/sessions/${sessionId}/messages`);
        console.log('📡 Запрос к API:', apiUrl);
        
        const response = await axios.get(apiUrl, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        const messagesData = response.data || [];
        
        console.log('✅ Получено сообщений:', messagesData.length);
        
        // Загружаем режим чата из сессии, если доступен
        try {
          const sessionResponse = await axios.get(getApiUrl(`/chat/sessions/${sessionId}`), {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          });
          if (sessionResponse.data?.chat_mode) {
            setChatMode(sessionResponse.data.chat_mode);
            console.log('✅ Загружен режим чата из сессии:', sessionResponse.data.chat_mode);
          }
        } catch (err) {
          console.warn('Не удалось загрузить режим чата из сессии:', err);
        }
        
        // Преобразуем сообщения в формат компонента
        const formattedMessages = messagesData.map(msg => ({
          id: `msg_${msg.id}`,
          type: msg.role === 'user' ? 'user' : 'ai',
          content: msg.content,
          timestamp: msg.created_at,
          enhancements: msg.enhancements || {}
        }));

        // Если нет сообщений, показываем приветственное
        if (formattedMessages.length === 0) {
          console.log('⚠️ Сессия пуста, показываем приветственное сообщение');
          setMessages([{
            id: 'welcome',
            type: 'ai',
            content: 'Привет! Я ваш АдваКОД AI-помощник. Задавайте любые вопросы по российскому законодательству, и я помогу вам разобраться. Можете также загружать документы для анализа.',
            timestamp: new Date().toISOString()
          }]);
        } else {
          console.log('✅ Загружено сообщений:', formattedMessages.length);
          setMessages(formattedMessages);
        }
        
        // Прокручиваем вниз после загрузки
        setTimeout(() => {
          scrollToBottom();
          autoScrollRef.current = true;
        }, 100);
      } catch (error) {
        console.error('❌ Ошибка загрузки сообщений сессии:', error);
        console.error('Детали ошибки:', error.response?.data || error.message);
        console.error('Статус:', error.response?.status);
        setLastError(error);
        setMessages([{
          id: 'error',
          type: 'error',
          content: `Не удалось загрузить сообщения: ${error.response?.data?.detail || error.message}. Попробуйте обновить страницу.`,
          timestamp: new Date().toISOString()
        }]);
      }
    };

    loadSessionMessages();
  }, [sessionId]); // Загружаем при изменении sessionId

  // Автоскролл при новых сообщениях
  useEffect(() => {
    if (autoScrollRef.current) {
      scrollToBottom();
    }
  }, [messages]);

  // Screen reader announcements для новых AI сообщений
  useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.type === 'ai') {
        const preview = lastMessage.content.substring(0, 100);
        setAnnouncement(`Assistant: ${preview}${lastMessage.content.length > 100 ? '...' : ''}`);
      }
    }
  }, [messages]);

  // Auto-expand textarea based on content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      textareaRef.current.style.height = `${Math.min(scrollHeight, 120)}px`;
    }
  }, [inputMessage]);

  // Mobile keyboard handling - scroll to bottom when keyboard appears
  useEffect(() => {
    const handleResize = () => {
      if (window.visualViewport) {
        const viewportHeight = window.visualViewport.height;
        // Keyboard is visible if viewport height is significantly reduced
        if (viewportHeight < window.innerHeight * 0.7) {
          scrollToBottom();
        }
      }
    };

    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', handleResize);
      return () => window.visualViewport.removeEventListener('resize', handleResize);
    }
  }, []);

  // Обработка изменения размера окна - закрываем модальное окно на десктопе
  useEffect(() => {
    const handleWindowResize = () => {
      const isMobile = window.innerWidth < 768; // md breakpoint
      // Если перешли на десктоп и модальное окно открыто - закрываем
      if (!isMobile && !isHistoryCollapsed) {
        setIsHistoryCollapsed(true);
      }
    };

    window.addEventListener('resize', handleWindowResize);
    return () => window.removeEventListener('resize', handleWindowResize);
  }, [isHistoryCollapsed]);

  // Блокировка скролла body при открытом модальном окне (только на мобильных)
  useEffect(() => {
    const isMobile = window.innerWidth < 768;
    if (!isHistoryCollapsed && isMobile) {
      // Блокируем скролл body
      document.body.style.overflow = 'hidden';
      return () => {
        // Разблокируем при размонтировании
        document.body.style.overflow = '';
      };
    }
  }, [isHistoryCollapsed]);

  // Обработка Escape для закрытия модального окна
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && !isHistoryCollapsed && window.innerWidth < 768) {
        setIsHistoryCollapsed(true);
      }
    };

    if (!isHistoryCollapsed && window.innerWidth < 768) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isHistoryCollapsed]);

  const handleContainerScroll = () => {
    // Обновляем флаг автоскролла: включен только если пользователь близко к низу
    autoScrollRef.current = isNearBottom();
  };

  // Функция для показа уведомления напрямую через DOM
  const showNotificationDirect = (message, description, type = 'success') => {
    
    // Удаляем старое уведомление если есть
    const old = document.getElementById('mode-notification-overlay-direct');
    if (old) old.remove();
    
    // Определяем тему (dark/light)
    const isDark = document.documentElement.classList.contains('dark') || 
                   window.matchMedia('(prefers-color-scheme: dark)').matches ||
                   document.body.classList.contains('dark');
    
    // Цвета в зависимости от темы
    const bgColor = isDark ? '#1f2937' : '#ffffff'; // gray-800 : white
    const textColor = isDark ? '#f9fafb' : '#111827'; // gray-50 : gray-900
    const borderColor = isDark ? '#374151' : '#e5e7eb'; // gray-700 : gray-200
    const overlayBg = isDark ? 'rgba(0, 0, 0, 0.7)' : 'rgba(0, 0, 0, 0.5)';
    const closeBtnColor = isDark ? '#9ca3af' : '#6b7280'; // gray-400 : gray-500
    
    // Создаем HTML напрямую
    const html = `
      <div id="mode-notification-overlay-direct" style="
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        z-index: 9999999 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background-color: ${overlayBg} !important;
        pointer-events: auto !important;
      ">
        <div style="
          background-color: ${bgColor} !important;
          color: ${textColor} !important;
          padding: 24px 32px !important;
          border-radius: 12px !important;
          border: 1px solid ${borderColor} !important;
          box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.1) !important;
          min-width: 380px !important;
          max-width: 520px !important;
          display: flex !important;
          flex-direction: column !important;
          gap: 12px !important;
          pointer-events: auto !important;
        ">
          <div style="display: flex; align-items: center; gap: 16px;">
            <div style="
              width: 40px;
              height: 40px;
              border-radius: 50%;
              background-color: ${isDark ? '#374151' : '#f3f4f6'};
              display: flex;
              align-items: center;
              justify-content: center;
              flex-shrink: 0;
            ">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M10 2L3 7V17H8V12H12V17H17V7L10 2Z" fill="${isDark ? '#60a5fa' : '#3b82f6'}" />
              </svg>
            </div>
            <div style="flex: 1;">
              <p style="
                margin: 0;
                font-size: 16px;
                font-weight: 600;
                line-height: 1.5;
                color: ${textColor};
              ">${message}</p>
              ${description ? `<p style="
                margin: 4px 0 0 0;
                font-size: 13px;
                font-weight: 400;
                line-height: 1.4;
                color: ${isDark ? '#9ca3af' : '#6b7280'};
              ">${description}</p>` : ''}
            </div>
            <button onclick="this.closest('#mode-notification-overlay-direct').remove()" style="
              background: none !important;
              border: none !important;
              color: ${closeBtnColor} !important;
              cursor: pointer !important;
              padding: 4px !important;
              font-size: 20px !important;
              display: flex;
              align-items: center;
              justify-content: center;
              flex-shrink: 0;
            " aria-label="Закрыть">✕</button>
          </div>
        </div>
      </div>
    `;
    
    // Вставляем в body
    document.body.insertAdjacentHTML('beforeend', html);
    
    // Автоматически удаляем через 3 секунды
    setTimeout(() => {
      const el = document.getElementById('mode-notification-overlay-direct');
      if (el) el.remove();
    }, 3000);
  };

  // Изменение режима чата
  const handleModeChange = async (newMode) => {
    if (newMode === chatMode) {
      setShowModeMenu(false);
      return;
    }
    
    // Показываем уведомление с описанием
    const modeName = newMode === 'basic' ? 'Базовый' : 'Эксперт';
    const modeDescription = newMode === 'basic' 
      ? 'Простой и понятный режим для всех пользователей'
      : 'Профессиональный режим с юридическими терминами';
    showNotificationDirect(`Режим изменен на: ${modeName}`, modeDescription, 'success');

    const cleanSessionId = sessionId ? parseInt(sessionId.toString().replace(/[^0-9]/g, '')) : null;
    
    if (!cleanSessionId) {
      // Если нет сессии, просто меняем режим локально (будет применен при создании сессии)
      setChatMode(newMode);
      setShowModeMenu(false);
      return;
    }

    try {
      // Обновляем режим через API
      const response = await axios.patch(
        getApiUrl(`/chat/sessions/${cleanSessionId}/mode`),
        null,
        {
          params: { chat_mode: newMode },
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      if (response.data) {
        setChatMode(newMode);
        setShowModeMenu(false);
      }
    } catch (error) {
      console.error('Ошибка изменения режима:', error);
      showNotificationDirect('Не удалось изменить режим чата', 'Попробуйте еще раз', 'error');
    }
  };

  // Отправка сообщения
  const sendMessage = async () => {
    const messageText = inputMessage.trim();
    if (!messageText || isGenerating) return;

    // Сохраняем session_id обработанный заранее
    const cleanSessionId = sessionId ? parseInt(sessionId.toString().replace(/[^0-9]/g, '')) : null;

    const userMessage = {
      id: `msg_${Date.now()}`,
      type: 'user',
      content: messageText,
      timestamp: new Date().toISOString(),
      files: attachedFiles
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setAttachedFiles([]);
    setIsGenerating(true);
    setGenerationStartTime(Date.now());
    setLastError(null);

    try {
      // ВСЕГДА отправляем через HTTP API, WebSocket используется только для получения ответов
      const requestPayload = {
        message: messageText,
        session_id: cleanSessionId,
        set_chat_mode: chatMode  // Отправляем текущий режим
      };
      
      console.log('Отправка сообщения:', { 
        message: messageText.substring(0, 50), 
        sessionId: cleanSessionId,
        url: getApiUrl('/chat/message')
      });
      
      // Попытка стриминга через SSE (Server-Sent Events)
      const streamUrl = getApiUrl('/chat/message/stream');
      const controller = new AbortController();
      currentStreamRef.current = controller;

      const authToken = localStorage.getItem('token');
      const resp = await fetch(streamUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Authorization': authToken ? `Bearer ${authToken}` : ''
        },
        cache: 'no-store',
        body: JSON.stringify(requestPayload),
        signal: controller.signal
      });

      if (!resp.ok || !resp.body) {
        const errText = await resp.text().catch(() => '');
        throw new Error(`Streaming request failed: ${resp.status} ${errText}`);
      }

      // Создаем пустое AI-сообщение и постепенно наполняем
      const aiMsgId = `ai_${Date.now()}`;
      setMessages(prev => [...prev, { id: aiMsgId, type: 'ai', content: '', timestamp: new Date().toISOString() }]);

      const reader = resp.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      const applyChunk = (text) => {
        setMessages(prev => prev.map(m => m.id === aiMsgId ? { ...m, content: (m.content || '') + text } : m));
      };

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split(/\n\n/);
        buffer = lines.pop() || '';
        for (const block of lines) {
          // Ожидаем формат SSE: строки вида "data: {json}"
          const dataLine = block.split('\n').find(l => l.startsWith('data:'));
          if (!dataLine) continue;
          const payload = dataLine.replace(/^data:\s?/, '');
          try {
            const evt = JSON.parse(payload);
            if (evt.type === 'start' && evt.session_id) {
              // Обновляем sessionId после получения от сервера (важно для первого сообщения)
              console.log('Получен session_id от сервера:', evt.session_id, 'текущий:', sessionId);
              if (!sessionId || sessionId !== evt.session_id) {
                setSessionId(evt.session_id);
                console.log('✅ sessionId обновлен:', evt.session_id);
              }
            } else if (evt.type === 'chunk' && typeof evt.content === 'string') {
              applyChunk(evt.content);
            } else if (evt.type === 'end') {
              // завершение
            } else if (evt.type === 'error') {
              throw new Error(evt.content || 'stream error');
            }
          } catch (_) {
            // На всякий случай добавляем как текст
            applyChunk(payload);
          }
        }
      }

      setIsGenerating(false);
      setGenerationStartTime(null);
    } catch (error) {
      console.error('Ошибка отправки сообщения:', error);
      
      // Если остановили вручную — не показываем ошибку, просто фиксируем остановку
      const isAborted = (currentStreamRef.current && currentStreamRef.current.signal?.aborted) 
        || error?.name === 'AbortError' 
        || String(error?.message || error).toLowerCase().includes('aborted');
      
      setIsGenerating(false);
      setGenerationStartTime(null);
      
      if (isAborted) {
        showGenerationStopped();
        return; // тихо выходим без отображения ошибки в чате
      }
      
      setLastError(error);
      
      // Показываем пользователю информативное сообщение об ошибке только один раз
      // Статус-система уже покажет уведомление, поэтому здесь мы только логируем
      console.error('Ошибка отправки сообщения:', error);
      
      // Показываем через статус-систему только если это не была отмена
      if (!isAborted) {
        showError(error, {
          autoHide: false,
          actions: [
            {
              label: 'Повторить',
              action: () => sendMessage(),
              primary: true
            }
          ]
        });
      }
      
      // Также добавляем сообщение об ошибке в чат для контекста
      let errorText = 'Произошла ошибка при отправке сообщения.';
      
      // Проверяем на таймаут по сообщению об ошибке
      const errorMessage = String(error?.message || error || '').toLowerCase();
      if (errorMessage.includes('timeout') || errorMessage.includes('[timeout]')) {
        errorText = 'Превышено время ожидания ответа (300 секунд). Модель работает дольше обычного. Рекомендации:\n• Упростите вопрос\n• Разбейте сложный вопрос на несколько простых\n• Попробуйте позже, когда нагрузка на сервер будет меньше';
      } else if (error.response) {
        const status = error.response.status;
        const data = error.response.data;
        
        if (status === 408) {
          errorText = 'Превышено время ожидания ответа. Попробуйте упростить вопрос или разбить его на части.';
        } else if (status === 503) {
          errorText = 'Сервер временно перегружен. Подождите немного и попробуйте снова.';
        } else if (status === 401) {
          errorText = 'Ошибка авторизации. Пожалуйста, войдите снова.';
        } else if (status === 429) {
          errorText = 'Слишком много запросов. Подождите немного перед следующим запросом.';
        } else if (status >= 500) {
          errorText = 'Ошибка сервера. Мы уже работаем над её устранением.';
        } else if (data?.detail || data?.message) {
          errorText = data.detail || data.message;
        }
      } else if (error.request) {
        errorText = 'Не удалось соединиться с сервером. Проверьте подключение к интернету.';
      }
      
      const errorMsg = {
        id: `error_${Date.now()}`,
        type: 'error',
        content: errorText,
        timestamp: new Date().toISOString(),
        error: error
      };
      setMessages(prev => [...prev, errorMsg]);
    }
  };

  // Обработка клавиш
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Закрытие расширенного режима при клике вне области (только на десктопе)
  useEffect(() => {
    const handleClickOutside = (e) => {
      // На мобильных не закрываем при клике вне области
      if (window.innerWidth >= 768 && isInputExpanded) {
        const inputArea = e.target.closest('[data-input-area]');
        if (!inputArea) {
          setIsInputExpanded(false);
        }
      }
    };

    if (isInputExpanded && window.innerWidth >= 768) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isInputExpanded]);

  // Закрытие меню режимов при клике вне области
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (modeMenuRef.current && !modeMenuRef.current.contains(e.target)) {
        setShowModeMenu(false);
      }
    };

    if (showModeMenu) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showModeMenu]);

  return (
    <div className="flex h-full bg-gray-50 dark:bg-gray-900 overflow-x-hidden">
      {/* Боковая панель с историей - скрыта на мобильных, зафиксирована на десктопе */}
      <div className={`hidden md:flex md:flex-col md:h-full ${isHistoryCollapsed ? 'w-16' : 'w-80'} transition-all duration-300 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex-shrink-0 overflow-hidden`}>
        <ChatHistory 
          isCollapsed={isHistoryCollapsed}
          onToggle={() => {
            setIsHistoryCollapsed(!isHistoryCollapsed);
            setFocusHistorySearch(false);
          }}
          onToggleCollapse={() => {
            setIsHistoryCollapsed(!isHistoryCollapsed);
            setFocusHistorySearch(false);
          }}
          currentSessionId={sessionId}
          onSessionSelect={(id) => {
            console.log('onSessionSelect вызван с id:', id, 'Текущий sessionId:', sessionId);
            setSessionId(id);
          }}
          onNewChat={(newSessionId) => {
            setSessionId(newSessionId);
            // Сообщения загрузятся автоматически через useEffect при изменении sessionId
          }}
          focusSearch={focusHistorySearch}
        />
      </div>

      {/* Модальное окно истории для мобильных */}
      {!isHistoryCollapsed && (
        <div 
          className="md:hidden fixed inset-0 z-[60] flex" 
          style={{ zIndex: 60 }}
        >
          {/* Overlay */}
          <div 
            className="fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity duration-300"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              setIsHistoryCollapsed(true);
            }}
          />
          {/* История */}
          <div 
            className="relative w-full max-w-[320px] bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transform transition-transform duration-300 ease-out z-[61] shadow-2xl"
            onClick={(e) => e.stopPropagation()}
            style={{ zIndex: 61 }}
          >
            <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between bg-white dark:bg-gray-800">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">История чатов</h2>
              <button
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setIsHistoryCollapsed(true);
                }}
                className="p-3 min-h-[44px] min-w-[44px] text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-xl transition-all flex items-center justify-center touch-manipulation shadow-sm hover:shadow-md flex-shrink-0"
                aria-label="Закрыть историю"
                title="Закрыть историю"
                type="button"
              >
                <ChevronLeft className="w-6 h-6" />
              </button>
            </div>
            <ChatHistory 
              isCollapsed={false}
              hideHeader={true}
              onToggle={() => {
                setIsHistoryCollapsed(true);
                setFocusHistorySearch(false);
              }}
              onToggleCollapse={() => {
                setIsHistoryCollapsed(true);
                setFocusHistorySearch(false);
              }}
              currentSessionId={sessionId}
              onSessionSelect={(id) => {
                console.log('onSessionSelect (мобильная версия) вызван с id:', id, 'Текущий sessionId:', sessionId);
                setSessionId(id);
                setIsHistoryCollapsed(true);
                setFocusHistorySearch(false);
              }}
              onNewChat={(newSessionId) => {
                setSessionId(newSessionId);
                // Сообщения загрузятся автоматически через useEffect при изменении sessionId
                setIsHistoryCollapsed(true);
                setFocusHistorySearch(false);
              }}
              focusSearch={focusHistorySearch}
            />
          </div>
        </div>
      )}

      {/* Основной чат - занимает всю оставшуюся ширину */}
      <div className="flex-1 flex flex-col overflow-hidden overflow-x-hidden min-w-0 max-w-full">
        {/* Заголовок */}
        <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 sm:px-6 py-4 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {/* Кнопка переключения истории для мобильных */}
              <button
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setIsHistoryCollapsed(prev => !prev);
                }}
                className="md:hidden p-2.5 min-w-[44px] min-h-[44px] text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-xl transition-all flex items-center justify-center touch-manipulation shadow-sm hover:shadow-md"
                aria-label="История запросов"
                title="История запросов"
                type="button"
              >
                <History className="w-5 h-5" />
              </button>
              <div className="w-10 h-10 bg-blue-600 dark:bg-primary-500 rounded-full flex items-center justify-center neon-glow-purple">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Чат с АДВАКОД</h1>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 hidden sm:block">Ваш персональный AI юрист-консультант</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              {/* Кнопка переподключения для критических ситуаций */}
              {(!isConnected && connectionState === 'failed') && (
                <button
                  onClick={forceReconnect}
                  className="flex items-center space-x-1 px-3 py-1 text-sm bg-blue-600 dark:bg-primary-600 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-primary-700 transition-colors neon-button-primary"
                  title="Переподключиться к серверу"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span className="hidden sm:inline">Переподключить</span>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Область сообщений - скроллируемая */}
        <div
          className="flex-1 overflow-y-auto overflow-x-hidden p-3 sm:p-6 space-y-4 dark:bg-gray-900 min-h-0"
          ref={messagesContainerRef}
          onScroll={handleContainerScroll}
          role="log"
          aria-live="polite"
          aria-label="Chat messages"
        >
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`${message.type === 'user' ? 'max-w-[85%] md:max-w-[80%] ml-auto' : 'w-full'}`}>
                <div className={`flex items-start space-x-3 ${message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                  <div className={`w-[35px] h-[35px] md:w-10 md:h-10 rounded-full flex items-center justify-center ${
                    message.type === 'user' ? 'bg-blue-600 dark:bg-primary-600 neon-glow-cyan' : 'bg-gray-600 dark:bg-gray-700 neon-glow-purple'
                  }`}>
                    {message.type === 'user' ? (
                      <User className="w-[18px] h-[18px] md:w-5 md:h-5 text-white" />
                    ) : (
                      <Bot className="w-[18px] h-[18px] md:w-5 md:h-5 text-white" />
                    )}
                  </div>
                  
                  <div className={`${
                    message.type === 'user' 
                      ? 'px-4 py-3 rounded-lg bg-blue-600 dark:bg-primary-600 text-white neon-card' 
                      : message.type === 'error'
                      ? ''
                      : 'px-4 py-3 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 neon-glass-card'
                  }`}>
                    {message.type === 'error' ? (
                      <ErrorMessage
                        error={message.error || message.content}
                        onRetry={() => {
                          // Повторить последнее сообщение
                          const lastUserMessage = messages.slice().reverse().find(m => m.type === 'user');
                          if (lastUserMessage) {
                            setInputMessage(lastUserMessage.content);
                          }
                        }}
                        onReconnect={forceReconnect}
                        variant="default"
                      />
                    ) : (
                      <>
                        <EnhancedResponse message={message} />
                        <div className="flex items-center justify-between mt-3">
                          <div className="text-xs opacity-70">
                            {new Date(message.timestamp).toLocaleTimeString()}
                          </div>
                          {message.type === 'ai' && message.id === 'welcome' && (
                            <FeedbackButtons messageId={message.id} />
                          )}
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {isGenerating && (
            <div className="flex justify-start">
              <div className="w-full">
                <div className="flex items-start space-x-3">
                  <div className="w-[35px] h-[35px] md:w-10 md:h-10 rounded-full bg-gray-600 flex items-center justify-center">
                    <Bot className="w-[18px] h-[18px] md:w-5 md:h-5 text-white" />
                  </div>
                  <div className="flex-1">
                    <AIThinkingIndicator
                      isGenerating={isGenerating}
                      startTime={generationStartTime}
                      onStop={stopGeneration}
                      variant="default"
                      estimatedTime={120} // 2 минуты примерное время
                    />
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Панель ввода - зафиксирована внизу, парящий эффект */}
        <div 
          ref={inputAreaRef}
          data-input-area
          className="bg-transparent p-3 sm:p-4 md:p-6 flex-shrink-0 z-40 transition-all duration-300 safe-bottom"
          style={{
            paddingBottom: 'max(12px, env(safe-area-inset-bottom, 0px))'
          }}
          onMouseEnter={() => {
            if (window.innerWidth >= 768) {
              setIsInputExpanded(true);
            }
          }}
          onMouseLeave={() => {
            if (window.innerWidth >= 768) {
              setIsInputExpanded(false);
            }
          }}
          onTouchStart={() => {
            // На мобильных всегда показываем расширенный режим при тапе
            if (window.innerWidth < 768) {
              setIsInputExpanded(true);
            }
          }}
        >
          {/* Стили для placeholder - по центру вертикально и слева горизонтально */}
          <style>{`
            #chat-input-textarea {
              text-align: left;
            }
            #chat-input-textarea::placeholder {
              text-align: left;
            }
          `}</style>
          {/* Прикрепленные файлы */}
          {attachedFiles.length > 0 && (
            <div className="mb-3 flex flex-wrap gap-2">
              {attachedFiles.map((file, index) => (
                <div key={index} className="flex items-center space-x-2 bg-gray-100 dark:bg-gray-700 px-3 py-2 rounded-xl">
                  <File className="w-4 h-4 text-gray-600 dark:text-gray-300" />
                  <span className="text-sm text-gray-700 dark:text-gray-300">{file.name}</span>
                  <button
                    onClick={() => setAttachedFiles(prev => prev.filter((_, i) => i !== index))}
                    className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Панель функций - появляется при наведении (Вариант 3) */}
          {isInputExpanded && (
            <div className="flex items-center gap-2 mb-3 animate-slide-in-up overflow-x-auto -mx-3 sm:-mx-4 px-3 sm:px-4">
              <button
                onClick={() => setShowFileUpload(!showFileUpload)}
                className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-xl transition-all min-h-[44px] touch-manipulation flex-shrink-0 whitespace-nowrap"
                title="Прикрепить файл"
                aria-label="Attach file"
              >
                <Paperclip className="w-4 h-4 flex-shrink-0" />
                <span className="hidden sm:inline">Файлы</span>
              </button>
              <button
                onClick={() => setShowTemplates(!showTemplates)}
                className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded-xl transition-all min-h-[44px] touch-manipulation flex-shrink-0 whitespace-nowrap"
                title="Шаблоны вопросов"
                aria-label="Question templates"
              >
                <Lightbulb className="w-4 h-4 flex-shrink-0" />
                <span className="hidden sm:inline">Шаблоны</span>
              </button>
            </div>
          )}

          {/* Контейнер поля ввода */}
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Кнопка настроек режима слева - всегда видна, выровнена с полем ввода */}
            <div className="relative" ref={modeMenuRef}>
              <button
                onClick={() => setShowModeMenu(!showModeMenu)}
                className="h-[48px] w-[48px] sm:h-[52px] sm:w-[52px] bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 hover:text-primary-600 dark:hover:text-primary-400 rounded-xl transition-all flex items-center justify-center touch-manipulation shadow-md hover:shadow-lg flex-shrink-0 border border-gray-200 dark:border-gray-600"
                title="Настройки режима"
                aria-label="Mode settings"
              >
                <Settings className="w-5 h-5 sm:w-6 sm:h-6" />
              </button>
              
              {/* Выпадающее меню режимов */}
              {showModeMenu && (
                <>
                  <div 
                    className="fixed inset-0 z-40" 
                    onClick={() => setShowModeMenu(false)}
                  />
                  <div 
                    className="absolute bottom-full left-0 mb-2 w-72 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 py-2 z-50"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700">
                      <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Режим чата</h3>
                    </div>
                    
                    {/* Базовый режим */}
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        handleModeChange('basic').catch(err => console.error('Ошибка:', err));
                      }}
                      className="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Базовый</span>
                            {chatMode === 'basic' && (
                              <Check className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                            )}
                          </div>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            Простой и понятный режим для всех пользователей, без сложных терминов.
                          </p>
                        </div>
                      </div>
                    </button>
                    
                    {/* Эксперт режим */}
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        handleModeChange('expert').catch(err => console.error('Ошибка:', err));
                      }}
                      className="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors border-t border-gray-200 dark:border-gray-700"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">Эксперт</span>
                            {chatMode === 'expert' && (
                              <Check className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                            )}
                          </div>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            Продвинутый режим с профессиональными терминами для опытных пользователей
                          </p>
                        </div>
                      </div>
                    </button>
                  </div>
                </>
              )}
            </div>
            
            {/* Поле ввода с круглыми краями и толстой рамкой (Вариант 3) */}
            <div className="flex-1 relative min-w-0">
              <div 
                className={`
                  rounded-3xl
                  border-[3px] sm:border-[4px]
                  border-primary-500 dark:border-primary-600
                  bg-white dark:bg-gray-700
                  backdrop-blur-xl
                  transition-all duration-300
                  flex items-center
                  ${isInputExpanded 
                    ? 'shadow-[0_0_30px_rgba(37,99,235,0.5),0_10px_40px_rgba(0,0,0,0.3)] border-primary-600 dark:border-primary-500 ring-4 ring-primary-500/20 dark:ring-primary-600/20' 
                    : 'shadow-[0_4px_20px_rgba(0,0,0,0.15),0_8px_30px_rgba(0,0,0,0.1)] border-primary-500 dark:border-primary-600'
                  }
                `}
                style={{ height: '48px', minHeight: '48px' }}
              >
                <textarea
                  ref={textareaRef}
                  id="chat-input-textarea"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  onFocus={() => {
                    setIsInputExpanded(true);
                  }}
                  onTouchStart={() => {
                    setIsInputExpanded(true);
                  }}
                  onBlur={(e) => {
                    // На мобильных не закрываем при blur, только на десктопе
                    if (window.innerWidth >= 768) {
                      const relatedTarget = e.relatedTarget;
                      if (!relatedTarget || !relatedTarget.closest('[data-input-area]')) {
                        setTimeout(() => {
                          if (document.activeElement !== textareaRef.current) {
                            setIsInputExpanded(false);
                          }
                        }, 200);
                      }
                    }
                  }}
                  placeholder="Введите ваш вопрос..."
                  className="
                    w-full px-3 sm:px-4
                    bg-transparent
                    text-gray-900 dark:text-gray-100
                    placeholder-gray-500 dark:placeholder-gray-400
                    text-base
                    transition-all duration-300
                    focus:outline-none
                    focus:ring-0
                    resize-none
                    leading-normal
                    border-0
                    overflow-hidden
                  "
                  style={{
                    height: '100%',
                    paddingTop: '10px',
                    paddingBottom: '10px',
                    lineHeight: '20px',
                    verticalAlign: 'middle',
                    maxHeight: '48px'
                  }}
                  rows={1}
                  disabled={isGenerating}
                  aria-label="Type your message"
                  aria-describedby="input-help"
                />
              </div>
              <span id="input-help" className="sr-only">
                Press Enter to send, Shift+Enter for new line
              </span>
            </div>
            
            {/* Кнопка микрофона справа - всегда видна, выровнена с полем ввода */}
            <button
              onClick={() => setShowVoiceRecorder(!showVoiceRecorder)}
              className="h-[48px] w-[48px] sm:h-[52px] sm:w-[52px] bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 hover:text-primary-600 dark:hover:text-primary-400 rounded-xl transition-all flex items-center justify-center touch-manipulation shadow-md hover:shadow-lg flex-shrink-0 border border-gray-200 dark:border-gray-600"
              title="Голосовой ввод"
              aria-label="Voice input"
            >
              <Mic className="w-5 h-5 sm:w-6 sm:h-6" />
            </button>
            
            {/* Кнопка отправки - показывается только при вводе текста */}
            {inputMessage.trim() && (
              <button
                onClick={sendMessage}
                disabled={!inputMessage.trim() || isGenerating}
                className="h-[48px] w-[48px] sm:h-[52px] sm:w-[52px] p-2.5 sm:p-3 bg-primary-600 text-white rounded-xl hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center shadow-lg touch-manipulation flex-shrink-0"
                title="Отправить сообщение"
                aria-label="Send message"
              >
                <Send className="w-5 h-5" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Модальные окна */}
      {showFileUpload && (
        <LazyFileUpload
          onClose={() => setShowFileUpload(false)}
          onFilesSelected={(files) => setAttachedFiles(prev => [...prev, ...files])}
        />
      )}
      
      {showTemplates && (
        <LazyQuestionTemplates
          isVisible={showTemplates}
          onClose={() => setShowTemplates(false)}
          onTemplateSelect={(template) => {
            setInputMessage(template);
            setShowTemplates(false);
          }}
        />
      )}
      
      {showVoiceRecorder && (
        <VoiceRecorder
          onClose={() => setShowVoiceRecorder(false)}
          onRecordingComplete={(audioBlob) => {
            // Обработка аудио записи
            console.log('Audio recorded:', audioBlob);
          }}
        />
      )}

      {/* Система уведомлений о статусе (без дубля индикатора генерации) */}
      <StatusNotificationSystem
        websocket={websocket}
        isGenerating={false}
        generationStartTime={generationStartTime}
        onStopGeneration={stopGeneration}
        onReconnect={forceReconnect}
        onForceReconnect={forceReconnect}
      />


      {/* Screen reader announcements */}
      <div 
        role="status" 
        aria-live="polite" 
        aria-atomic="true" 
        className="sr-only"
      >
        {announcement}
      </div>
    </div>
  );
};

export default Chat;
