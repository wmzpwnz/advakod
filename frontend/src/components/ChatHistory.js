import React, { useState, useEffect, useCallback } from 'react';
import { 
  MessageSquare, 
  Plus, 
  Trash2, 
  Edit3, 
  Check, 
  X, 
  Calendar,
  Clock,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import axios from 'axios';
import { getApiUrl } from '../config/api';

const ChatHistory = ({ 
  currentSessionId, 
  onSessionSelect, 
  onNewChat,
  isCollapsed,
  onToggleCollapse 
}) => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingSession, setEditingSession] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [showEmptyChats, setShowEmptyChats] = useState(false); // Показывать ли пустые чаты

  // Загружаем список сессий
  const loadSessions = useCallback(async () => {
    try {
      setLoading(true);
      // Запрашиваем чаты с параметром include_empty
      const response = await axios.get(getApiUrl('/chat/sessions'), {
        params: { include_empty: showEmptyChats }
      });
      const sessionsData = response.data || [];
      
      // Сортируем сессии: новые сверху (по updated_at или created_at)
      const sortedSessions = sessionsData.sort((a, b) => {
        const dateA = new Date(a.updated_at || a.created_at);
        const dateB = new Date(b.updated_at || b.created_at);
        return dateB - dateA; // Новые сверху
      });
      
      setSessions(sortedSessions);
      setError(null);
    } catch (err) {
      console.error('Error loading sessions:', err);
      setError('Ошибка загрузки истории чатов');
    } finally {
      setLoading(false);
    }
  }, [showEmptyChats]);

  useEffect(() => {
    loadSessions();
  }, [loadSessions, showEmptyChats]); // Перезагружаем при изменении фильтра

  // Создание новой сессии
  const handleNewChat = async () => {
    try {
      const response = await axios.post(getApiUrl('/chat/sessions'), {
        title: `Новый чат ${new Date().toLocaleDateString('ru-RU')}`
      });
      
      const newSession = response.data;
      // Добавляем новую сессию в начало списка (новые сверху)
      setSessions(prev => [newSession, ...prev]);
      onNewChat(newSession.id);
    } catch (err) {
      console.error('Error creating new session:', err);
      setError('Ошибка создания нового чата');
    }
  };

  // Удаление сессии
  const handleDeleteSession = async (sessionId) => {
    if (!window.confirm('Удалить этот чат? Все сообщения будут потеряны.')) {
      return;
    }

    try {
      await axios.delete(getApiUrl(`/chat/sessions/${sessionId}`));
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      
      // Если удаляем текущую сессию, создаем новую
      if (sessionId === currentSessionId) {
        handleNewChat();
      }
    } catch (err) {
      console.error('Error deleting session:', err);
      setError('Ошибка удаления чата');
    }
  };

  // Начало редактирования названия
  const startEditing = (session) => {
    setEditingSession(session.id);
    setEditTitle(session.title || 'Без названия');
  };

  // Сохранение нового названия
  const saveTitle = async (sessionId) => {
    try {
      await axios.put(getApiUrl(`/chat/sessions/${sessionId}`), {
        title: editTitle.trim() || 'Без названия'
      });
      
      setSessions(prev => prev.map(s => 
        s.id === sessionId 
          ? { ...s, title: editTitle.trim() || 'Без названия' }
          : s
      ));
      
      setEditingSession(null);
      setEditTitle('');
    } catch (err) {
      console.error('Error updating session title:', err);
      setError('Ошибка обновления названия');
    }
  };

  // Отмена редактирования
  const cancelEditing = () => {
    setEditingSession(null);
    setEditTitle('');
  };

  // Форматирование даты
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays === 1) {
      return 'Вчера';
    } else if (diffDays < 7) {
      return `${diffDays} дн. назад`;
    } else {
      return date.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit' });
    }
  };

  // Сокращение названия для компактного режима
  const truncateTitle = (title, maxLength = 25) => {
    if (!title) return 'Без названия';
    return title.length > maxLength ? title.substring(0, maxLength) + '...' : title;
  };

  if (loading) {
    return (
      <div className={`bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-all duration-300 ${
        isCollapsed ? 'w-16' : 'w-80'
      }`}>
        <div className="p-4 flex items-center justify-center">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-all duration-300 flex flex-col ${
      isCollapsed ? 'w-16' : 'w-80'
    }`}>
      {/* Заголовок */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-4">
          {!isCollapsed && (
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              История чатов
            </h2>
          )}
          
          <button
            onClick={onToggleCollapse}
            className="p-2 text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-all duration-200"
            title={isCollapsed ? "Развернуть" : "Свернуть"}
          >
            {isCollapsed ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
          </button>
        </div>
        
        {/* Большая красивая кнопка "Новый чат" */}
        <button
          onClick={handleNewChat}
          className={`w-full btn-glass-primary font-semibold rounded-xl transition-all duration-300 ${
            isCollapsed ? 'p-3' : 'py-3 px-4'
          }`}
        >
          <div className="flex items-center justify-center space-x-2">
            <Plus className={`${isCollapsed ? 'h-5 w-5' : 'h-5 w-5'}`} />
            {!isCollapsed && <span>Новый чат</span>}
          </div>
        </button>
      </div>

      {/* Список сессий */}
      <div className="flex-1 overflow-y-auto">
        {error && (
          <div className="p-4">
            <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg p-3 text-sm text-red-600 dark:text-red-400">
              {error}
            </div>
          </div>
        )}

        {sessions.length === 0 && !loading && !error ? (
          <div className="p-4 text-center">
            <MessageSquare className="h-12 w-12 text-gray-400 dark:text-gray-500 mx-auto mb-3" />
            {!isCollapsed && (
              <>
                <p className="text-gray-600 dark:text-gray-400 text-sm mb-3">
                  {showEmptyChats ? "Нет активных чатов с сообщениями" : "Пока нет истории чатов"}
                </p>
                <button
                  onClick={handleNewChat}
                  className="btn-glass-primary text-sm px-4 py-2"
                >
                  Начать первый чат
                </button>
              </>
            )}
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {sessions.map((session) => (
              <div
                key={session.id}
                className={`group relative rounded-lg transition-all duration-200 ${
                  session.id === currentSessionId
                    ? 'bg-primary-100 dark:bg-primary-900/50 border border-primary-200 dark:border-primary-800'
                    : 'hover:bg-gray-100 dark:hover:bg-gray-700 border border-transparent'
                }`}
              >
                <button
                  onClick={() => onSessionSelect(session.id)}
                  className={`w-full p-3 text-left transition-all duration-200 ${
                    isCollapsed ? 'px-2' : ''
                  }`}
                  title={isCollapsed ? session.title || 'Без названия' : ''}
                >
                  <div className="flex items-center space-x-3">
                    <MessageSquare className={`flex-shrink-0 ${
                      session.id === currentSessionId
                        ? 'text-primary-600 dark:text-primary-400'
                        : 'text-gray-500 dark:text-gray-400'
                    } ${isCollapsed ? 'h-5 w-5' : 'h-4 w-4'}`} />
                    
                    {!isCollapsed && (
                      <div className="flex-1 min-w-0">
                        {editingSession === session.id ? (
                          <div className="flex items-center space-x-2">
                            <input
                              type="text"
                              value={editTitle}
                              onChange={(e) => setEditTitle(e.target.value)}
                              onKeyPress={(e) => {
                                if (e.key === 'Enter') saveTitle(session.id);
                                if (e.key === 'Escape') cancelEditing();
                              }}
                              className="flex-1 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                              autoFocus
                            />
                            <button
                              onClick={() => saveTitle(session.id)}
                              className="p-1 text-green-600 hover:text-green-700"
                            >
                              <Check className="h-3 w-3" />
                            </button>
                            <button
                              onClick={cancelEditing}
                              className="p-1 text-red-600 hover:text-red-700"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </div>
                        ) : (
                          <>
                            <p className={`text-sm font-medium truncate ${
                              session.id === currentSessionId
                                ? 'text-primary-800 dark:text-primary-200'
                                : 'text-gray-900 dark:text-gray-100'
                            }`}>
                              {truncateTitle(session.title)}
                            </p>
                            
                            {/* Превью последнего сообщения */}
                            {session.last_message_preview && (
                              <p className="text-xs text-gray-500 dark:text-gray-400 truncate mt-1">
                                {session.last_message_preview}
                              </p>
                            )}
                            
                            <p className="text-xs text-gray-400 dark:text-gray-500 flex items-center mt-1">
                              <Clock className="h-3 w-3 mr-1" />
                              {formatDate(session.last_message_time || session.updated_at || session.created_at)}
                            </p>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                </button>

                {/* Кнопки управления сессией */}
                {!isCollapsed && editingSession !== session.id && (
                  <div className="absolute right-2 top-1/2 transform -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                    <div className="flex items-center space-x-1">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          startEditing(session);
                        }}
                        className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-white dark:hover:bg-gray-800 rounded transition-all duration-200"
                        title="Переименовать"
                      >
                        <Edit3 className="h-3 w-3" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteSession(session.id);
                        }}
                        className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-white dark:hover:bg-gray-800 rounded transition-all duration-200"
                        title="Удалить"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Статистика и настройки внизу */}
      {!isCollapsed && (
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <div className="space-y-3">
            {/* Переключатель пустых чатов */}
            <label className="flex items-center justify-between text-xs">
              <span className="text-gray-600 dark:text-gray-400">Показывать пустые чаты</span>
              <button
                onClick={() => setShowEmptyChats(!showEmptyChats)}
                className={`relative inline-flex h-4 w-7 items-center rounded-full transition-colors duration-200 ${
                  showEmptyChats 
                    ? 'bg-primary-600' 
                    : 'bg-gray-300 dark:bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform duration-200 ${
                    showEmptyChats ? 'translate-x-3.5' : 'translate-x-0.5'
                  }`}
                />
              </button>
            </label>
            
            {/* Статистика */}
            <div className="text-xs text-gray-500 dark:text-gray-400 flex items-center justify-between">
              <span>Всего чатов: {sessions.length}</span>
              <span className="flex items-center">
                <Calendar className="h-3 w-3 mr-1" />
                Сегодня
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatHistory;
