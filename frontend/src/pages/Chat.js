import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Send, Paperclip, Bot, User, Wifi, WifiOff, File, X, Lightbulb, Search, Mic, Square, Settings } from 'lucide-react';
import { useChatWebSocket } from '../hooks/useChatWebSocket';
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
import axios from 'axios';
import { getApiUrl } from '../config/api';

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isGenerating, setIsGenerating] = useState(false); // Состояние генерации
  const [sessionId, setSessionId] = useState(null);
  const [attachedFiles, setAttachedFiles] = useState([]);
  const [showFileUpload, setShowFileUpload] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [showVoiceRecorder, setShowVoiceRecorder] = useState(false);
  const [showRAGSettings, setShowRAGSettings] = useState(false);
  const [isHistoryCollapsed, setIsHistoryCollapsed] = useState(false);
  const messagesEndRef = useRef(null);
  const currentStreamRef = useRef(null); // Ref для текущего стрима
  const initializedRef = useRef(false); // защита от двойного вызова в React StrictMode

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Функция остановки генерации
  const stopGeneration = () => {
    // Останавливаем HTTP стрим если есть
    if (currentStreamRef.current) {
      currentStreamRef.current.abort();
      currentStreamRef.current = null;
    }

    // Отправляем команду остановки через WebSocket
    if (wsStopGeneration) {
      wsStopGeneration();
    }

    setIsGenerating(false);

    // Обновляем последнее сообщение ИИ, убирая флаг стриминга
    setMessages(prev => {
      const updated = [...prev];
      const lastMessage = updated[updated.length - 1];
      if (lastMessage && lastMessage.role === 'assistant' && lastMessage.isStreaming) {
        lastMessage.isStreaming = false;
        lastMessage.content = lastMessage.content + '\n\n[Генерация остановлена пользователем]';
      }
      return updated;
    });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Инициализация настроек один раз при монтировании
    axios.defaults.timeout = 180000;
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }, []);

  // WebSocket обработчики - обернуты в useCallback для стабильности
  const handleNewMessage = useCallback((messageData) => {
    console.log('handleNewMessage called with:', messageData);
    // Дедупликация сообщений, приходящих по WS, если такой id уже есть (после SSE)
    setMessages(prev => {
      const exists = prev.some(m => m.id === messageData.id);
      console.log('Message exists:', exists, 'Current messages count:', prev.length);
      if (exists) {
        console.log('Message already exists, not adding');
        return prev;
      } else {
        console.log('Adding new message to chat');
        return [...prev, messageData];
      }
    });
  }, []);

  const handleTyping = useCallback((userId, isTyping) => {
    // Индикатор печати отключен для упрощения
    console.log(`User ${userId} is ${isTyping ? 'typing' : 'stopped typing'}`);
  }, []);

  const handleSessionUpdate = useCallback((sessionData) => {
    // Обновляем информацию о сессии
    console.log('Session updated:', sessionData);
  }, []);

  // Обработчики для файлов
  const handleFileUpload = (files) => {
    setAttachedFiles(prev => [...prev, ...files]);
    setShowFileUpload(false);
  };

  const handleFileRemove = (fileToRemove) => {
    setAttachedFiles(prev => prev.filter(f => f.id !== fileToRemove.id));
  };

  // Обработчик для выбора шаблона вопроса
  const handleTemplateSelect = (question) => {
    setInputMessage(question);
    setShowTemplates(false);
    // Фокусируемся на textarea
    setTimeout(() => {
      const textarea = document.querySelector('textarea');
      if (textarea) {
        textarea.focus();
      }
    }, 100);
  };

  // Обработчик для выбора сообщения из поиска
  const handleMessageSelect = (message) => {
    // Прокручиваем к выбранному сообщению
    const messageElement = document.querySelector(`[data-message-id="${message.id}"]`);
    if (messageElement) {
      messageElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      // Подсвечиваем сообщение
      messageElement.classList.add('ring-2', 'ring-primary-500', 'ring-opacity-50');
      setTimeout(() => {
        messageElement.classList.remove('ring-2', 'ring-primary-500', 'ring-opacity-50');
      }, 3000);
    }
  };

  // Обработчик для отправки голосового сообщения
  const handleVoiceMessage = async (audioBlob, duration) => {
    try {
      // setIsLoading(true); // Отключено

      // Создаем FormData для отправки аудио
      const formData = new FormData();
      formData.append('audio', audioBlob, 'voice-message.webm');
      formData.append('session_id', sessionId);
      formData.append('duration', duration);

      // Отправляем голосовое сообщение
      const response = await axios.post(getApiUrl('/chat/voice-message'), formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 180000, // 3 минуты для обработки аудио
      });

      // Добавляем сообщения в чат
      if (response.data.user_message) {
        setMessages(prev => [...prev, response.data.user_message]);
      }
      if (response.data.ai_message) {
        setMessages(prev => [...prev, response.data.ai_message]);
      }

      // Обновляем session_id если нужно
      if (response.data.session_id) {
        setSessionId(response.data.session_id);
      }

      setShowVoiceRecorder(false);
      scrollToBottom();

    } catch (error) {
      console.error('Error sending voice message:', error);
      alert('Ошибка отправки голосового сообщения');
    } finally {
      // setIsLoading(false); // Отключено
    }
  };

  // WebSocket соединение - ВКЛЮЧЕНО с исправленной логикой
  const { isConnected, sendTyping, stopGeneration: wsStopGeneration } = useChatWebSocket(
    sessionId,
    handleNewMessage,
    handleTyping,
    handleSessionUpdate
  );

  useEffect(() => {
    // Создаем новую сессию чата при загрузке (один раз, даже в StrictMode)
    if (initializedRef.current) return;
    initializedRef.current = true;
    createNewSession();
  }, []);

  const createNewSession = async () => {
    try {
      const response = await axios.post(
        getApiUrl('/chat/sessions'),
        { title: 'Новый чат' },
        { timeout: 180000 }
      );
      setSessionId(response.data.id);

      // Очищаем сообщения и добавляем приветственное
      setMessages([{
        id: 'welcome',
        role: 'assistant',
        content: 'Привет! Я ваш АдваКОД AI-помощник. Задавайте любые вопросы по российскому законодательству, и я помогу вам разобраться. Можете также загружать документы для анализа.',
        created_at: new Date().toISOString()
      }]);
    } catch (error) {
      console.error('Error creating session:', error);
    }
  };

  // Функция выбора сессии из истории
  const handleSessionSelect = async (selectedSessionId) => {
    try {
      setSessionId(selectedSessionId);

      // Загружаем сообщения выбранной сессии
      const response = await axios.get(getApiUrl(`/chat/sessions/${selectedSessionId}/messages`));
      const sessionMessages = response.data || [];

      // Если сессия пустая, добавляем приветственное сообщение
      if (sessionMessages.length === 0) {
        setMessages([{
          id: 'welcome',
          role: 'assistant',
          content: 'Привет! Я ваш АдваКОД AI-помощник. Задавайте любые вопросы по российскому законодательству, и я помогу вам разобраться. Можете также загружать документы для анализа.',
          created_at: new Date().toISOString()
        }]);
      } else {
        setMessages(sessionMessages);
      }

      // Очищаем состояние ввода
      setInputMessage('');
      setAttachedFiles([]);
      setIsGenerating(false);

    } catch (error) {
      console.error('Error loading session messages:', error);
    }
  };

  // Функция создания нового чата из истории
  const handleNewChatFromHistory = (newSessionId) => {
    setSessionId(newSessionId);
    setMessages([{
      id: 'welcome',
      role: 'assistant',
      content: 'Привет! Я ваш АдваКОД AI-помощник. Задавайте любые вопросы по российскому законодательству, и я помогу вам разобраться. Можете также загружать документы для анализа.',
      created_at: new Date().toISOString()
    }]);
    setInputMessage('');
    setAttachedFiles([]);
    setIsGenerating(false);
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isGenerating) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: inputMessage,
      created_at: new Date().toISOString(),
      attachments: attachedFiles
    };

    setMessages(prev => [...prev, userMessage]);
    const currentMessage = inputMessage;
    setInputMessage('');
    setAttachedFiles([]); // Очищаем прикрепленные файлы
    setIsGenerating(true);

    try {
      // Создаем placeholder для ответа ИИ
      const assistantMessageId = Date.now() + 1;
      const assistantMessage = {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        created_at: new Date().toISOString(),
        isStreaming: true
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Используем правильный эндпоинт для стриминга чата
      // getApiUrl() уже добавляет /api/v1/, поэтому используем только путь без префикса
      const endpoint = '/chat/message/stream';

      const response = await fetch(getApiUrl(endpoint), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: currentMessage,
          session_id: sessionId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Обработка SSE потока от /chat/message/stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullResponse = '';
      let sources = [];
      let processingTime = 0;
      let buffer = '';

      const applyChunk = (text) => {
        if (!text) return;
        fullResponse += text;
        setMessages(prev => prev.map(msg =>
          msg.id === assistantMessageId
            ? { ...msg, content: fullResponse }
            : msg
        ));
      };

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          // SSE события разделены двойным переносом строки
          const events = buffer.split('\n\n');
          // Последний элемент может быть неполным, оставляем его в буфере
          buffer = events.pop() || '';

          for (const event of events) {
            if (!event.trim()) continue;
            
            // Ищем строку с "data: "
            const dataLine = event.split('\n').find(line => line.startsWith('data: '));
            if (!dataLine) continue;
            
            const data = dataLine.slice(6).trim();
            if (!data || data === '[DONE]') continue;

            try {
              const parsed = JSON.parse(data);

              if (parsed.type === 'start') {
                // Обновляем session_id, если он пришел
                if (parsed.session_id && !sessionId) {
                  setSessionId(parsed.session_id);
                }
              } else if (parsed.type === 'chunk' && typeof parsed.content === 'string') {
                applyChunk(parsed.content);
              } else if (parsed.type === 'end') {
                processingTime = parsed.processing_time || processingTime;
                // Завершаем стриминг
              } else if (parsed.type === 'error') {
                const errorContent = parsed.content || 'stream error';
                if (
                  typeof errorContent === 'string' &&
                  (errorContent.includes('RAG система не готова') || 
                   errorContent.includes('Модель ИИ временно недоступна') ||
                   errorContent.includes('временно недоступен'))
                ) {
                  applyChunk(`\n\n⚠️ ${errorContent}\n\n`);
                } else {
                  throw new Error(errorContent);
                }
              }
            } catch (parseError) {
              // Если не удалось распарсить JSON, пробуем обработать как текст
              if (
                typeof data === 'string' &&
                (data.includes('RAG система не готова') ||
                 data.includes('Модель ИИ временно недоступна') ||
                 data.includes('временно недоступен'))
              ) {
                applyChunk(`\n\n⚠️ ${data}\n\n`);
              } else {
                console.warn('Ошибка парсинга JSON:', parseError, 'Data:', data);
              }
            }
          }
        }

        // Финальное обновление сообщения
        setMessages(prev => prev.map(msg =>
          msg.id === assistantMessageId
            ? {
              ...msg,
              content: fullResponse || 'Ответ не был сформирован. Попробуйте ещё раз.',
              isStreaming: false,
              sources: sources.length > 0 ? sources : undefined,
              processing_time: processingTime
            }
            : msg
        ));

      } catch (streamError) {
        console.error('Ошибка обработки потока:', streamError);
        throw streamError;
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `Извините, произошла ошибка при обработке вашего запроса. ${error.message || ''}`,
        created_at: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !isGenerating) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTime = useCallback((timestamp) => {
    return new Date(timestamp).toLocaleTimeString('ru-RU', {
      hour: '2-digit',
      minute: '2-digit'
    });
  }, []);

  return (
    <div className="h-screen flex bg-gradient-to-br from-gray-50 via-white to-blue-50/30 dark:from-gray-900 dark:via-gray-800 dark:to-purple-900/20 overflow-hidden transition-colors duration-300">
      {/* История чатов - боковая панель */}
      <ChatHistory
        currentSessionId={sessionId}
        onSessionSelect={handleSessionSelect}
        onNewChat={handleNewChatFromHistory}
        isCollapsed={isHistoryCollapsed}
        onToggleCollapse={() => setIsHistoryCollapsed(!isHistoryCollapsed)}
      />

      {/* Основная область чата */}
      <div className="flex-1 flex flex-col max-w-4xl mx-auto bg-transparent">
        {/* Header */}
        <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl border-b border-purple-200/30 dark:border-purple-500/20 px-4 sm:px-6 py-3 sm:py-4 transition-colors duration-200 shadow-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 sm:space-x-3">
              <Bot className="h-6 w-6 sm:h-8 sm:w-8 text-primary-600" />
              <div>
                <h1 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100">Чат с <span className="gradient-text">АДВАКОД</span></h1>
                <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 hidden sm:block">Ваш персональный <span className="gradient-text">AI юрист-консультант</span></p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowRAGSettings(true)}
                className="p-1.5 rounded-lg bg-white/50 dark:bg-gray-800/50 backdrop-blur-md border border-gray-300/30 dark:border-gray-600/30 text-gray-600 dark:text-gray-400 hover:bg-purple-500/10 hover:border-purple-400/30 hover:text-purple-600 dark:hover:text-purple-400 transition-all duration-300"
                title="Настройки RAG"
              >
                <Settings className="h-4 w-4" />
              </button>
              <button
                onClick={() => setShowSearch(true)}
                className="p-1.5 rounded-lg bg-white/50 dark:bg-gray-800/50 backdrop-blur-md border border-gray-300/30 dark:border-gray-600/30 text-gray-600 dark:text-gray-400 hover:bg-blue-500/10 hover:border-blue-400/30 hover:text-blue-600 dark:hover:text-blue-400 transition-all duration-300"
                title="Поиск по истории"
              >
                <Search className="h-4 w-4" />
              </button>
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 hidden sm:inline">
                {isConnected ? 'Онлайн' : 'Офлайн'}
              </span>
              {isConnected ? (
                <Wifi className="w-4 h-4 text-green-500" />
              ) : (
                <WifiOff className="w-4 h-4 text-red-500" />
              )}
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-3 sm:px-6 py-1 space-y-3 sm:space-y-4 bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
          {messages.map((message, index) => (
            <div
              key={message.id}
              data-message-id={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div
                className={`max-w-xs sm:max-w-md md:max-w-3xl flex space-x-2 sm:space-x-3 ${message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                  }`}
              >
                {/* Avatar */}
                <div
                  className={`flex-shrink-0 w-8 h-8 sm:w-10 sm:h-10 rounded-full flex items-center justify-center transition-all duration-300 shadow-lg ${message.role === 'user'
                    ? 'bg-gradient-to-r from-primary-500 to-primary-600 text-white'
                    : 'bg-gradient-to-r from-accent-purple to-accent-pink text-white'
                    }`}
                >
                  {message.role === 'user' ? (
                    <User className="h-3 w-3 sm:h-5 sm:w-5" />
                  ) : (
                    <Bot className="h-3 w-3 sm:h-5 sm:w-5" />
                  )}
                </div>

                {/* Message Content */}
                <div
                  className={`rounded-2xl px-4 py-3 sm:px-5 sm:py-4 transition-all duration-300 shadow-lg ${message.role === 'user'
                    ? 'bg-gradient-to-r from-primary-500 to-primary-600 text-white'
                    : 'bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm text-gray-900 dark:text-gray-100 border border-gray-200/50 dark:border-gray-700/50'
                    }`}
                >
                  {message.role === 'assistant' && message.enhancements ? (
                    <EnhancedResponse message={message} enhancements={message.enhancements} />
                  ) : (
                    <div className="whitespace-pre-wrap">
                      {message.content}
                      {message.isStreaming && (
                        <span className="inline-block w-2 h-4 bg-primary-600 ml-1 animate-pulse"></span>
                      )}
                    </div>
                  )}

                  {/* Голосовое сообщение */}
                  {message.audio_url && (
                    <div className="mt-3">
                      <VoicePlayer
                        audioUrl={message.audio_url}
                        duration={message.audio_duration}
                        showControls={true}
                      />
                    </div>
                  )}

                  {/* Отображение прикрепленных файлов */}
                  {message.attachments && message.attachments.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {message.attachments.map((file, index) => (
                        <div
                          key={index}
                          className="flex items-center space-x-2 p-2 bg-gray-100 dark:bg-gray-700 rounded-lg"
                        >
                          <File className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                          <span className="text-sm text-gray-700 dark:text-gray-300">
                            {file.filename}
                          </span>
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            ({(file.file_size / 1024).toFixed(1)} KB)
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Sources */}
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-300 dark:border-gray-600">
                      <p className="text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">Источники:</p>
                      <div className="space-y-2">
                        {message.sources.map((source, index) => (
                          <div key={index} className="text-sm bg-gray-50 dark:bg-gray-700 p-2 rounded-lg">
                            <div className="font-medium text-gray-800 dark:text-gray-200">
                              {source.title || source.source || 'Правовой документ'}
                            </div>
                            {source.content_preview && (
                              <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                                {source.content_preview.length > 100
                                  ? source.content_preview.substring(0, 100) + '...'
                                  : source.content_preview}
                              </div>
                            )}
                            {source.similarity && (
                              <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                                Релевантность: {(source.similarity * 100).toFixed(1)}%
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Processing time */}
                  {message.processing_time && (
                    <div className="mt-2 text-xs opacity-70">
                      Обработано за {typeof message.processing_time === 'number' ? message.processing_time.toFixed(2) : message.processing_time}с
                    </div>
                  )}

                  {/* Streaming indicator */}
                  {message.isStreaming && (
                    <div className="mt-2 text-xs text-primary-600">
                      печатает...
                    </div>
                  )}

                  {/* Feedback Buttons - только для ответов ассистента */}
                  {message.role === 'assistant' && !message.isStreaming && message.id && (
                    <div className="mt-3 pt-3 border-t border-gray-200/50 dark:border-gray-700/50">
                      <FeedbackButtons 
                        messageId={message.id}
                        onFeedbackSubmitted={(rating) => {
                          console.log('Feedback submitted:', rating);
                        }}
                      />
                    </div>
                  )}

                  {/* Timestamp */}
                  <div className="mt-2 text-xs opacity-70">
                    {formatTime(message.created_at)}
                  </div>
                </div>
              </div>
            </div>
          ))}

          {/* Индикатор загрузки отключен */}

          {/* Индикатор печати отключен */}

          <div ref={messagesEndRef} />

          {/* Question Templates */}
          <LazyQuestionTemplates
            onTemplateSelect={handleTemplateSelect}
            isVisible={showTemplates}
            onToggle={() => setShowTemplates(!showTemplates)}
          />

          {/* Voice Recorder */}
          {showVoiceRecorder && (
            <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-6 py-4 transition-colors duration-200">
              <VoiceRecorder
                onSendVoiceMessage={handleVoiceMessage}
                onCancel={() => setShowVoiceRecorder(false)}
                maxDuration={300}
              />
            </div>
          )}

          {/* File Upload Area */}
          {showFileUpload && (
            <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-6 py-4 transition-colors duration-200">
              <LazyFileUpload
                onFileUpload={handleFileUpload}
                onFileRemove={handleFileRemove}
                maxFiles={5}
                maxSize={10}
              />
            </div>
          )}

          {/* Attached Files */}
          {attachedFiles.length > 0 && (
            <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-6 py-3 transition-colors duration-200">
              <div className="flex items-center space-x-2 mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Прикрепленные файлы:
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {attachedFiles.map((file) => (
                  <div
                    key={file.id}
                    className="flex items-center space-x-2 px-3 py-1 bg-gray-100 dark:bg-gray-700 rounded-lg"
                  >
                    <File className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      {file.filename}
                    </span>
                    <button
                      onClick={() => handleFileRemove(file)}
                      className="p-1 text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors duration-200"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Input and Footer Container */}
        <div>
          {/* Input */}
          <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl border-t border-purple-200/30 dark:border-purple-500/20 px-4 sm:px-6 py-2 transition-colors duration-200 shadow-2xl">
            <div className="flex space-x-2 sm:space-x-4">
              <button
                onClick={() => setShowTemplates(!showTemplates)}
                className={`flex-shrink-0 p-1.5 sm:p-2 rounded-lg backdrop-blur-md transition-all duration-300 ${showTemplates
                  ? 'bg-purple-500/20 text-purple-600 dark:text-purple-400 border border-purple-400/40 shadow-lg shadow-purple-500/20'
                  : 'bg-white/50 dark:bg-gray-800/50 text-gray-600 dark:text-gray-400 border border-gray-300/30 dark:border-gray-600/30 hover:bg-purple-500/10 hover:border-purple-400/30 hover:text-purple-600 dark:hover:text-purple-400'
                  }`}
              >
                <Lightbulb className="h-4 w-4 sm:h-5 sm:w-5" />
              </button>

              <button
                onClick={() => setShowFileUpload(!showFileUpload)}
                className={`flex-shrink-0 p-1.5 sm:p-2 rounded-lg backdrop-blur-md transition-all duration-300 ${showFileUpload
                  ? 'bg-blue-500/20 text-blue-600 dark:text-blue-400 border border-blue-400/40 shadow-lg shadow-blue-500/20'
                  : 'bg-white/50 dark:bg-gray-800/50 text-gray-600 dark:text-gray-400 border border-gray-300/30 dark:border-gray-600/30 hover:bg-blue-500/10 hover:border-blue-400/30 hover:text-blue-600 dark:hover:text-blue-400'
                  }`}
              >
                <Paperclip className="h-4 w-4 sm:h-5 sm:w-5" />
              </button>

              <button
                onClick={() => setShowVoiceRecorder(!showVoiceRecorder)}
                className={`flex-shrink-0 p-1.5 sm:p-2 rounded-lg backdrop-blur-md transition-all duration-300 ${showVoiceRecorder
                  ? 'bg-cyan-500/20 text-cyan-600 dark:text-cyan-400 border border-cyan-400/40 shadow-lg shadow-cyan-500/20'
                  : 'bg-white/50 dark:bg-gray-800/50 text-gray-600 dark:text-gray-400 border border-gray-300/30 dark:border-gray-600/30 hover:bg-cyan-500/10 hover:border-cyan-400/30 hover:text-cyan-600 dark:hover:text-cyan-400'
                  }`}
              >
                <Mic className="h-4 w-4 sm:h-5 sm:w-5" />
              </button>

              <div className="flex-1">
                <textarea
                  value={inputMessage}
                  onChange={(e) => {
                    setInputMessage(e.target.value);

                    // Отправляем уведомление о печати
                    if (e.target.value.length > 0) {
                      sendTyping(true);
                    } else {
                      sendTyping(false);
                    }
                  }}
                  onKeyPress={handleKeyPress}
                  placeholder={isGenerating ? "Генерация ответа..." : "Задайте вопрос по российскому законодательству..."}
                  className="w-full px-4 py-3 sm:px-5 sm:py-4 border border-purple-300/30 dark:border-purple-500/30 rounded-2xl focus:outline-none focus:border-purple-400/60 dark:focus:border-purple-400/60 resize-none bg-white/70 dark:bg-gray-800/70 backdrop-blur-md text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 transition-all duration-300 text-sm sm:text-base shadow-lg neon-glow-purple neon-focus"
                  rows={1}
                  disabled={isGenerating}
                />
              </div>

              {isGenerating ? (
                <button
                  onClick={stopGeneration}
                  className="flex-shrink-0 bg-red-500/20 backdrop-blur-md border border-red-400/40 text-red-600 dark:text-red-400 p-2 sm:p-3 rounded-xl hover:bg-red-500/30 hover:shadow-lg hover:shadow-red-500/30 transition-all duration-300 neon-hover"
                  title="Остановить генерацию"
                >
                  <Square className="h-4 w-4 sm:h-5 sm:w-5" />
                </button>
              ) : (
                <button
                  onClick={sendMessage}
                  disabled={!inputMessage.trim()}
                  className="flex-shrink-0 bg-gradient-to-r from-purple-500/20 via-blue-500/20 to-cyan-500/20 backdrop-blur-lg border border-purple-400/40 text-purple-600 dark:text-purple-300 p-2 sm:p-3 rounded-xl hover:from-purple-500/30 hover:via-blue-500/30 hover:to-cyan-500/30 hover:border-purple-400/60 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 shadow-lg hover:shadow-xl hover:shadow-purple-500/30 transform hover:scale-105 neon-hover-intense"
                  title="Отправить сообщение"
                >
                  <Send className="h-4 w-4 sm:h-5 sm:w-5" />
                </button>
              )}
            </div>

            <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Нажмите Enter для отправки, Shift+Enter для новой строки
            </div>
          </div>

          {/* Компактная информационная панель */}
          <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-4 py-1 shadow-lg">
            <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
              <div className="flex items-center space-x-4">
                <span>© 2024 АДВАКОД</span>
                <span>•</span>
                <span>Ваш персональный AI юрист-консультант</span>
              </div>
              <div className="flex items-center space-x-4">
                <a href="/pricing" className="hover:text-primary-600 dark:hover:text-primary-400 transition-colors">Тарифы</a>
                <span>•</span>
                <span>Помощь (скоро)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Message Search Modal */}
        <LazyMessageSearch
          messages={messages}
          onMessageSelect={handleMessageSelect}
          isVisible={showSearch}
          onClose={() => setShowSearch(false)}
        />

        {/* RAG Settings Modal */}
        <RAGSettings
          isVisible={showRAGSettings}
          onClose={() => setShowRAGSettings(false)}
        />
      </div>
    </div>
  );
};

export default Chat;
