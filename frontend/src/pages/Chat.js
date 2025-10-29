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
  const [isGenerating, setIsGenerating] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [attachedFiles, setAttachedFiles] = useState([]);
  const [showFileUpload, setShowFileUpload] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [showVoiceRecorder, setShowVoiceRecorder] = useState(false);
  const [showRAGSettings, setShowRAGSettings] = useState(false);
  const [isHistoryCollapsed, setIsHistoryCollapsed] = useState(false);
  const messagesEndRef = useRef(null);
  const currentStreamRef = useRef(null);
  const initializedRef = useRef(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Функция остановки генерации
  const stopGeneration = () => {
    if (currentStreamRef.current) {
      currentStreamRef.current.abort();
      currentStreamRef.current = null;
    }

    if (wsStopGeneration) {
      wsStopGeneration();
    }

    setIsGenerating(false);
  };

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
    sendMessage: wsSendMessage,
    stopGeneration: wsStopGeneration
  } = useChatWebSocket(sessionId, handleNewMessage);

  // Инициализация сессии
  useEffect(() => {
    if (!initializedRef.current) {
      initializedRef.current = true;
      const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      setSessionId(newSessionId);
      
      // Добавляем приветственное сообщение
      setMessages([{
        id: 'welcome',
        type: 'ai',
        content: 'Добро пожаловать в ИИ-Юрист! Я готов помочь вам с правовыми вопросами. Задайте ваш вопрос или загрузите документ для анализа.',
        timestamp: new Date().toISOString()
      }]);
    }
  }, []);

  // Автоскролл при новых сообщениях
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Отправка сообщения
  const sendMessage = async () => {
    if (!inputMessage.trim() || isGenerating) return;

    const userMessage = {
      id: `msg_${Date.now()}`,
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString(),
      files: attachedFiles
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setAttachedFiles([]);
    setIsGenerating(true);

    try {
      // Отправляем через WebSocket если подключен, иначе через HTTP
      if (isConnected) {
        wsSendMessage(inputMessage, sessionId, attachedFiles);
      } else {
        // HTTP fallback
        const response = await axios.post(`${getApiUrl()}/chat/send`, {
          message: inputMessage,
          session_id: sessionId,
          files: attachedFiles
        });

        const aiMessage = {
          id: `ai_${Date.now()}`,
          type: 'ai',
          content: response.data.response,
          timestamp: new Date().toISOString()
        };

        setMessages(prev => [...prev, aiMessage]);
        setIsGenerating(false);
      }
    } catch (error) {
      console.error('Ошибка отправки сообщения:', error);
      const errorMessage = {
        id: `error_${Date.now()}`,
        type: 'error',
        content: 'Произошла ошибка при отправке сообщения. Попробуйте еще раз.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
      setIsGenerating(false);
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
                <h1 className="text-xl font-semibold text-gray-900">ИИ-Юрист</h1>
                <div className="flex items-center space-x-2">
                  {isConnected ? (
                    <div className="flex items-center text-green-600">
                      <Wifi className="w-4 h-4" />
                      <span className="text-sm">Подключено</span>
                    </div>
                  ) : (
                    <div className="flex items-center text-red-600">
                      <WifiOff className="w-4 h-4" />
                      <span className="text-sm">Отключено</span>
                    </div>
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
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
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
                  
                  <div className={`px-4 py-3 rounded-lg ${
                    message.type === 'user' 
                      ? 'bg-blue-600 text-white' 
                      : message.type === 'error'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-white text-gray-900 border border-gray-200'
                  }`}>
                    <EnhancedResponse message={message} />
                    <div className="text-xs opacity-70 mt-2">
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {isGenerating && (
            <div className="flex justify-start">
              <div className="max-w-3xl">
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                  <div className="px-4 py-3 rounded-lg bg-white border border-gray-200">
                    <div className="flex items-center space-x-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                      <span className="text-gray-600">ИИ думает...</span>
                    </div>
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
    </div>
  );
};

export default Chat;
