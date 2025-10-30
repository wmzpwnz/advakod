import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Send, Paperclip, Bot, User, Wifi, WifiOff, File, X, Lightbulb, Search, Mic, Square, Settings, RefreshCw } from 'lucide-react';
import { useChatWebSocket } from '../hooks/useChatWebSocket';
import { useStatusNotifications } from '../hooks/useStatusNotifications';
import {
  LazyFileUpload,
  LazyQuestionTemplates,
  LazyMessageSearch
} from '../components/LazyComponent';
import VoiceRecorder from '../components/VoiceRecorder';
import VoicePlayer from '../components/VoicePlayer';
import ChatHistory from '../components/ChatHistory';
import EnhancedResponse from '../components/EnhancedResponse';
import RAGSettings from '../components/RAGSettings';
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
  const [showSearch, setShowSearch] = useState(false);
  const [showVoiceRecorder, setShowVoiceRecorder] = useState(false);
  const [showRAGSettings, setShowRAGSettings] = useState(false);
  const [isHistoryCollapsed, setIsHistoryCollapsed] = useState(false);
  const [lastError, setLastError] = useState(null);
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const autoScrollRef = useRef(true);
  const currentStreamRef = useRef(null);
  const initializedRef = useRef(false);

  // Хук для уведомлений
  const { showGenerationStopped, showError } = useStatusNotifications();

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

  // Автоскролл при новых сообщениях
  useEffect(() => {
    if (autoScrollRef.current) {
      scrollToBottom();
    }
  }, [messages]);

  const handleContainerScroll = () => {
    // Обновляем флаг автоскролла: включен только если пользователь близко к низу
    autoScrollRef.current = isNearBottom();
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
        session_id: cleanSessionId
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
            if (evt.type === 'chunk' && typeof evt.content === 'string') {
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
      
      // Показываем пользователю информативное сообщение об ошибке
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
      
      // Также добавляем сообщение об ошибке в чат для контекста
      let errorText = 'Произошла ошибка при отправке сообщения.';
      
      if (error.response) {
        const status = error.response.status;
        const data = error.response.data;
        
        if (status === 408) {
          errorText = 'Превышено время ожидания ответа. Попробуйте упростить вопрос.';
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
      
      const errorMessage = {
        id: `error_${Date.now()}`,
        type: 'error',
        content: errorText,
        timestamp: new Date().toISOString(),
        error: error
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  // Обработка клавиш
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Боковая панель с историей */}
      <div className={`${isHistoryCollapsed ? 'w-16' : 'w-80'} transition-all duration-300 bg-white border-r border-gray-200`}>
        <ChatHistory 
          isCollapsed={isHistoryCollapsed}
          onToggle={() => setIsHistoryCollapsed(!isHistoryCollapsed)}
        />
      </div>

      {/* Основной чат */}
      <div className="flex-1 flex flex-col">
        {/* Заголовок */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">Чат с АДВАКОД</h1>
                <p className="text-sm text-gray-600 mt-1">Ваш персональный AI юрист-консультант</p>
                <div className="flex items-center space-x-4 mt-2">
                  <WebSocketStatus 
                    websocket={websocket}
                    onReconnect={forceReconnect}
                    className="flex-1"
                  />
                  
                  {/* Кнопка переподключения для критических ситуаций */}
                  {(!isConnected && connectionState === 'failed') && (
                    <button
                      onClick={forceReconnect}
                      className="flex items-center space-x-1 px-3 py-1 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                      title="Переподключиться к серверу"
                    >
                      <RefreshCw className="w-4 h-4" />
                      <span>Переподключить</span>
                    </button>
                  )}
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowRAGSettings(!showRAGSettings)}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
                title="Настройки RAG"
              >
                <Settings className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Область сообщений */}
        <div
          className="flex-1 overflow-y-auto p-6 space-y-4"
          ref={messagesContainerRef}
          onScroll={handleContainerScroll}
        >
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-3xl ${message.type === 'user' ? 'order-2' : 'order-1'}`}>
                <div className={`flex items-start space-x-3 ${message.type === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    message.type === 'user' ? 'bg-blue-600' : 'bg-gray-600'
                  }`}>
                    {message.type === 'user' ? (
                      <User className="w-4 h-4 text-white" />
                    ) : (
                      <Bot className="w-4 h-4 text-white" />
                    )}
                  </div>
                  
                  <div className={`${
                    message.type === 'user' 
                      ? 'px-4 py-3 rounded-lg bg-blue-600 text-white' 
                      : message.type === 'error'
                      ? ''
                      : 'px-4 py-3 rounded-lg bg-white text-gray-900 border border-gray-200'
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
              <div className="max-w-3xl w-full">
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center">
                    <Bot className="w-4 h-4 text-white" />
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

        {/* Панель ввода */}
        <div className="bg-white border-t border-gray-200 p-6">
          {/* Прикрепленные файлы */}
          {attachedFiles.length > 0 && (
            <div className="mb-4 flex flex-wrap gap-2">
              {attachedFiles.map((file, index) => (
                <div key={index} className="flex items-center space-x-2 bg-gray-100 px-3 py-2 rounded-lg">
                  <File className="w-4 h-4 text-gray-600" />
                  <span className="text-sm text-gray-700">{file.name}</span>
                  <button
                    onClick={() => setAttachedFiles(prev => prev.filter((_, i) => i !== index))}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="flex items-end space-x-4">
            <div className="flex-1">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Задайте ваш правовой вопрос..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows={3}
                disabled={isGenerating}
              />
            </div>
            
            <div className="flex flex-col space-y-2">
              <button
                onClick={() => setShowFileUpload(!showFileUpload)}
                className="p-3 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
                title="Прикрепить файл"
              >
                <Paperclip className="w-5 h-5" />
              </button>
              
              <button
                onClick={() => setShowVoiceRecorder(!showVoiceRecorder)}
                className="p-3 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
                title="Голосовой ввод"
              >
                <Mic className="w-5 h-5" />
              </button>
              
              <button
                onClick={sendMessage}
                disabled={!inputMessage.trim() || isGenerating}
                className="p-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Отправить сообщение"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
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
          onClose={() => setShowTemplates(false)}
          onTemplateSelect={(template) => setInputMessage(template)}
        />
      )}
      
      {showSearch && (
        <LazyMessageSearch
          onClose={() => setShowSearch(false)}
          messages={messages}
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
      
      {showRAGSettings && (
        <RAGSettings
          onClose={() => setShowRAGSettings(false)}
        />
      )}

      {/* Система уведомлений о статусе */}
      <StatusNotificationSystem
        websocket={websocket}
        isGenerating={isGenerating}
        generationStartTime={generationStartTime}
        onStopGeneration={stopGeneration}
        onReconnect={forceReconnect}
        onForceReconnect={forceReconnect}
      />
    </div>
  );
};

export default Chat;
