import React, { useState, useEffect, useRef } from 'react';
import { Search, X, Clock, MessageSquare, ChevronUp, ChevronDown } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

const MessageSearch = ({ messages, onMessageSelect, isVisible, onClose }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [showResults, setShowResults] = useState(false);
  const searchInputRef = useRef(null);
  const { isDark } = useTheme();

  useEffect(() => {
    if (isVisible && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isVisible]);

  useEffect(() => {
    if (searchQuery.trim()) {
      const results = messages
        .filter(message => 
          message.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
          (message.role === 'user' && message.content.toLowerCase().includes(searchQuery.toLowerCase()))
        )
        .map((message, index) => ({
          ...message,
          searchIndex: index,
          highlightedContent: highlightText(message.content, searchQuery)
        }))
        .slice(0, 20); // Ограничиваем результаты
      
      setSearchResults(results);
      setShowResults(true);
      setSelectedIndex(-1);
    } else {
      setSearchResults([]);
      setShowResults(false);
    }
  }, [searchQuery, messages]);

  const highlightText = (text, query) => {
    if (!query.trim()) return text;
    
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) => 
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200 dark:bg-yellow-800 px-1 rounded">
          {part}
        </mark>
      ) : part
    );
  };

  const handleKeyDown = (e) => {
    if (!showResults || searchResults.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < searchResults.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev > 0 ? prev - 1 : searchResults.length - 1
        );
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < searchResults.length) {
          handleMessageSelect(searchResults[selectedIndex]);
        }
        break;
      case 'Escape':
        onClose();
        break;
    }
  };

  const handleMessageSelect = (message) => {
    onMessageSelect(message);
    setSearchQuery('');
    setSearchResults([]);
    setShowResults(false);
    onClose();
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const truncateText = (text, maxLength = 100) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-start justify-center pt-20 animate-fade-in">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl mx-4 animate-scale-in">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center">
            <Search className="h-5 w-5 mr-2 text-primary-600" />
            Поиск по истории
          </h3>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Search Input */}
        <div className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              ref={searchInputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Поиск по сообщениям..."
              className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
          </div>
          
          {searchQuery && (
            <div className="mt-2 text-sm text-gray-500 dark:text-gray-400">
              {searchResults.length > 0 ? (
                `Найдено ${searchResults.length} сообщений`
              ) : (
                'Сообщения не найдены'
              )}
            </div>
          )}
        </div>

        {/* Search Results */}
        {showResults && searchResults.length > 0 && (
          <div className="max-h-96 overflow-y-auto border-t border-gray-200 dark:border-gray-700">
            {searchResults.map((message, index) => (
              <div
                key={`${message.id}-${index}`}
                className={`p-4 border-b border-gray-100 dark:border-gray-700 cursor-pointer transition-colors ${
                  index === selectedIndex
                    ? 'bg-primary-50 dark:bg-primary-900/30'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-700'
                }`}
                onClick={() => handleMessageSelect(message)}
              >
                <div className="flex items-start space-x-3">
                  <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    message.role === 'user'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300'
                  }`}>
                    {message.role === 'user' ? (
                      <MessageSquare className="h-4 w-4" />
                    ) : (
                      <MessageSquare className="h-4 w-4" />
                    )}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {message.role === 'user' ? 'Вы' : 'ИИ-Юрист'}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center">
                        <Clock className="h-3 w-3 mr-1" />
                        {formatTime(message.created_at)}
                      </span>
                    </div>
                    
                    <div className="text-sm text-gray-700 dark:text-gray-300">
                      {highlightText(truncateText(message.content), searchQuery)}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700 rounded-b-lg">
          <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
            <div className="flex items-center space-x-4">
              <span className="flex items-center">
                <ChevronUp className="h-4 w-4 mr-1" />
                <ChevronDown className="h-4 w-4 mr-1" />
                Навигация
              </span>
              <span>Enter - Выбрать</span>
            </div>
            <span>Esc - Закрыть</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MessageSearch;
