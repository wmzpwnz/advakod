import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Search, 
  Command, 
  ArrowRight, 
  Clock, 
  Star,
  Settings,
  Users,
  FileText,
  BarChart3,
  Shield,
  Bell,
  Database,
  Zap,
  Home,
  LogOut,
  Moon,
  Sun,
  Monitor
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import useHotkeys from '../hooks/useHotkeys';

const CommandPalette = ({ isOpen, onClose }) => {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [recentCommands, setRecentCommands] = useState(() => {
    const saved = localStorage.getItem('recentCommands');
    return saved ? JSON.parse(saved) : [];
  });
  
  const navigate = useNavigate();
  const { logout } = useAuth();
  const { theme, toggleTheme, setLightTheme, setDarkTheme } = useTheme();
  const inputRef = useRef(null);
  const listRef = useRef(null);

  // Все доступные команды
  const allCommands = useMemo(() => [
    // Навигация
    {
      id: 'nav-dashboard',
      title: 'Перейти к дашборду',
      description: 'Главная страница админ-панели',
      icon: Home,
      category: 'Навигация',
      keywords: ['дашборд', 'главная', 'home', 'dashboard'],
      action: () => navigate('/admin'),
      shortcut: 'Ctrl+H'
    },
    {
      id: 'nav-users',
      title: 'Управление пользователями',
      description: 'Просмотр и управление пользователями',
      icon: Users,
      category: 'Навигация',
      keywords: ['пользователи', 'users', 'управление'],
      action: () => navigate('/admin/users'),
      shortcut: 'Ctrl+U'
    },
    {
      id: 'nav-documents',
      title: 'Управление документами',
      description: 'RAG система и документы',
      icon: FileText,
      category: 'Навигация',
      keywords: ['документы', 'documents', 'rag', 'файлы'],
      action: () => navigate('/admin/documents'),
      shortcut: 'Ctrl+D'
    },
    {
      id: 'nav-analytics',
      title: 'Аналитика',
      description: 'Статистика и отчеты',
      icon: BarChart3,
      category: 'Навигация',
      keywords: ['аналитика', 'analytics', 'статистика', 'отчеты'],
      action: () => navigate('/admin/analytics'),
      shortcut: 'Ctrl+A'
    },
    {
      id: 'nav-moderation',
      title: 'Модерация',
      description: 'Система модерации контента',
      icon: Shield,
      category: 'Навигация',
      keywords: ['модерация', 'moderation', 'контент'],
      action: () => navigate('/admin/moderation'),
      shortcut: 'Ctrl+M'
    },
    {
      id: 'nav-notifications',
      title: 'Уведомления',
      description: 'Центр уведомлений',
      icon: Bell,
      category: 'Навигация',
      keywords: ['уведомления', 'notifications', 'алерты'],
      action: () => navigate('/admin/notifications'),
      shortcut: 'Ctrl+N'
    },
    {
      id: 'nav-backup',
      title: 'Резервное копирование',
      description: 'Управление бэкапами',
      icon: Database,
      category: 'Навигация',
      keywords: ['бэкап', 'backup', 'резервное', 'копирование'],
      action: () => navigate('/admin/backup'),
      shortcut: 'Ctrl+B'
    },

    // Настройки
    {
      id: 'settings-interface',
      title: 'Настройки интерфейса',
      description: 'Кастомизация админ-панели',
      icon: Settings,
      category: 'Настройки',
      keywords: ['настройки', 'settings', 'интерфейс', 'кастомизация'],
      action: () => {
        // Здесь должен открыться SettingsPanel
        const event = new CustomEvent('openSettingsPanel');
        window.dispatchEvent(event);
      },
      shortcut: 'Ctrl+,'
    },

    // Темы
    {
      id: 'theme-toggle',
      title: 'Переключить тему',
      description: 'Переключение между светлой и темной темой',
      icon: theme === 'dark' ? Sun : Moon,
      category: 'Тема',
      keywords: ['тема', 'theme', 'темная', 'светлая', 'dark', 'light'],
      action: toggleTheme,
      shortcut: 'Ctrl+Shift+T'
    },
    {
      id: 'theme-light',
      title: 'Светлая тема',
      description: 'Переключиться на светлую тему',
      icon: Sun,
      category: 'Тема',
      keywords: ['светлая', 'light', 'тема'],
      action: setLightTheme
    },
    {
      id: 'theme-dark',
      title: 'Темная тема',
      description: 'Переключиться на темную тему',
      icon: Moon,
      category: 'Тема',
      keywords: ['темная', 'dark', 'тема'],
      action: setDarkTheme
    },
    {
      id: 'theme-system',
      title: 'Системная тема',
      description: 'Использовать системные настройки',
      icon: Monitor,
      category: 'Тема',
      keywords: ['системная', 'system', 'авто', 'auto'],
      action: () => {
        // Здесь должна быть логика для системной темы
        console.log('System theme');
      }
    },

    // Быстрые действия
    {
      id: 'action-refresh',
      title: 'Обновить страницу',
      description: 'Перезагрузить текущую страницу',
      icon: Zap,
      category: 'Действия',
      keywords: ['обновить', 'refresh', 'перезагрузить'],
      action: () => window.location.reload(),
      shortcut: 'F5'
    },
    {
      id: 'action-logout',
      title: 'Выйти из системы',
      description: 'Завершить сеанс работы',
      icon: LogOut,
      category: 'Действия',
      keywords: ['выйти', 'logout', 'выход'],
      action: logout,
      shortcut: 'Ctrl+Shift+Q'
    }
  ], [navigate, theme, toggleTheme, setLightTheme, setDarkTheme, logout]);

  // Фильтрация команд по запросу
  const filteredCommands = useMemo(() => {
    if (!query.trim()) {
      // Показываем недавние команды и популярные
      const recent = recentCommands
        .map(id => allCommands.find(cmd => cmd.id === id))
        .filter(Boolean)
        .slice(0, 5);
      
      const popular = allCommands
        .filter(cmd => !recent.some(r => r.id === cmd.id))
        .slice(0, 10);
      
      return [...recent, ...popular];
    }

    const searchQuery = query.toLowerCase();
    return allCommands
      .filter(command => {
        const searchableText = [
          command.title,
          command.description,
          command.category,
          ...command.keywords
        ].join(' ').toLowerCase();
        
        return searchableText.includes(searchQuery);
      })
      .sort((a, b) => {
        // Приоритет по точности совпадения
        const aTitle = a.title.toLowerCase();
        const bTitle = b.title.toLowerCase();
        
        if (aTitle.startsWith(searchQuery) && !bTitle.startsWith(searchQuery)) return -1;
        if (!aTitle.startsWith(searchQuery) && bTitle.startsWith(searchQuery)) return 1;
        
        return 0;
      });
  }, [query, allCommands, recentCommands]);

  // Выполнение команды
  const executeCommand = (command) => {
    if (command && command.action) {
      // Добавляем в недавние команды
      const newRecent = [command.id, ...recentCommands.filter(id => id !== command.id)].slice(0, 10);
      setRecentCommands(newRecent);
      localStorage.setItem('recentCommands', JSON.stringify(newRecent));
      
      // Выполняем команду
      command.action();
      onClose();
    }
  };

  // Навигация по клавиатуре
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!isOpen) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex(prev => 
            prev < filteredCommands.length - 1 ? prev + 1 : 0
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(prev => 
            prev > 0 ? prev - 1 : filteredCommands.length - 1
          );
          break;
        case 'Enter':
          e.preventDefault();
          if (filteredCommands[selectedIndex]) {
            executeCommand(filteredCommands[selectedIndex]);
          }
          break;
        case 'Escape':
          e.preventDefault();
          onClose();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filteredCommands, selectedIndex, onClose]);

  // Сброс выбранного индекса при изменении запроса
  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Фокус на поле ввода при открытии
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Прокрутка к выбранному элементу
  useEffect(() => {
    if (listRef.current && selectedIndex >= 0) {
      const selectedElement = listRef.current.children[selectedIndex];
      if (selectedElement) {
        selectedElement.scrollIntoView({
          block: 'nearest',
          behavior: 'smooth'
        });
      }
    }
  }, [selectedIndex]);

  const groupedCommands = useMemo(() => {
    const groups = {};
    filteredCommands.forEach(command => {
      const category = command.category || 'Другое';
      if (!groups[category]) {
        groups[category] = [];
      }
      groups[category].push(command);
    });
    return groups;
  }, [filteredCommands]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
            onClick={onClose}
          />

          {/* Command Palette */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed top-[20%] left-1/2 transform -translate-x-1/2 w-full max-w-2xl mx-4 bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 z-50 overflow-hidden"
          >
            {/* Search Input */}
            <div className="flex items-center px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <Search className="h-5 w-5 text-gray-400 mr-3" />
              <input
                ref={inputRef}
                type="text"
                placeholder="Поиск команд... (Ctrl+K)"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="flex-1 bg-transparent text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 outline-none text-lg"
              />
              <div className="flex items-center space-x-2 text-xs text-gray-400">
                <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded border">↑↓</kbd>
                <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded border">Enter</kbd>
                <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded border">Esc</kbd>
              </div>
            </div>

            {/* Commands List */}
            <div className="max-h-96 overflow-y-auto">
              {filteredCommands.length === 0 ? (
                <div className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                  <Command className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>Команды не найдены</p>
                  <p className="text-sm mt-1">Попробуйте изменить поисковый запрос</p>
                </div>
              ) : (
                <div ref={listRef} className="py-2">
                  {!query.trim() && recentCommands.length > 0 && (
                    <div className="px-4 py-2">
                      <div className="flex items-center text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                        <Clock className="h-3 w-3 mr-1" />
                        Недавние команды
                      </div>
                    </div>
                  )}
                  
                  {query.trim() ? (
                    // Группированный вывод при поиске
                    Object.entries(groupedCommands).map(([category, commands]) => (
                      <div key={category}>
                        <div className="px-4 py-2">
                          <div className="text-xs font-medium text-gray-500 dark:text-gray-400">
                            {category}
                          </div>
                        </div>
                        {commands.map((command, index) => {
                          const globalIndex = filteredCommands.indexOf(command);
                          const Icon = command.icon;
                          const isSelected = globalIndex === selectedIndex;
                          
                          return (
                            <motion.button
                              key={command.id}
                              onClick={() => executeCommand(command)}
                              className={`w-full px-4 py-3 flex items-center space-x-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors ${
                                isSelected ? 'bg-blue-50 dark:bg-blue-900/20 border-r-2 border-blue-500' : ''
                              }`}
                              whileHover={{ x: 2 }}
                            >
                              <div className={`p-2 rounded-lg ${
                                isSelected 
                                  ? 'bg-blue-100 dark:bg-blue-900/30' 
                                  : 'bg-gray-100 dark:bg-gray-800'
                              }`}>
                                <Icon className={`h-4 w-4 ${
                                  isSelected 
                                    ? 'text-blue-600 dark:text-blue-400' 
                                    : 'text-gray-600 dark:text-gray-400'
                                }`} />
                              </div>
                              
                              <div className="flex-1 text-left">
                                <div className={`font-medium ${
                                  isSelected 
                                    ? 'text-blue-900 dark:text-blue-100' 
                                    : 'text-gray-900 dark:text-white'
                                }`}>
                                  {command.title}
                                </div>
                                <div className="text-sm text-gray-500 dark:text-gray-400">
                                  {command.description}
                                </div>
                              </div>
                              
                              <div className="flex items-center space-x-2">
                                {command.shortcut && (
                                  <kbd className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-800 rounded border">
                                    {command.shortcut}
                                  </kbd>
                                )}
                                <ArrowRight className="h-4 w-4 text-gray-400" />
                              </div>
                            </motion.button>
                          );
                        })}
                      </div>
                    ))
                  ) : (
                    // Простой список без группировки
                    filteredCommands.map((command, index) => {
                      const Icon = command.icon;
                      const isSelected = index === selectedIndex;
                      const isRecent = recentCommands.includes(command.id);
                      
                      return (
                        <motion.button
                          key={command.id}
                          onClick={() => executeCommand(command)}
                          className={`w-full px-4 py-3 flex items-center space-x-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors ${
                            isSelected ? 'bg-blue-50 dark:bg-blue-900/20 border-r-2 border-blue-500' : ''
                          }`}
                          whileHover={{ x: 2 }}
                        >
                          <div className={`p-2 rounded-lg ${
                            isSelected 
                              ? 'bg-blue-100 dark:bg-blue-900/30' 
                              : 'bg-gray-100 dark:bg-gray-800'
                          }`}>
                            <Icon className={`h-4 w-4 ${
                              isSelected 
                                ? 'text-blue-600 dark:text-blue-400' 
                                : 'text-gray-600 dark:text-gray-400'
                            }`} />
                          </div>
                          
                          <div className="flex-1 text-left">
                            <div className={`font-medium flex items-center ${
                              isSelected 
                                ? 'text-blue-900 dark:text-blue-100' 
                                : 'text-gray-900 dark:text-white'
                            }`}>
                              {command.title}
                              {isRecent && (
                                <Star className="h-3 w-3 ml-2 text-yellow-500" />
                              )}
                            </div>
                            <div className="text-sm text-gray-500 dark:text-gray-400">
                              {command.description}
                            </div>
                          </div>
                          
                          <div className="flex items-center space-x-2">
                            {command.shortcut && (
                              <kbd className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-800 rounded border">
                                {command.shortcut}
                              </kbd>
                            )}
                            <ArrowRight className="h-4 w-4 text-gray-400" />
                          </div>
                        </motion.button>
                      );
                    })
                  )}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="px-6 py-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
              <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                <div className="flex items-center space-x-4">
                  <span>Найдено команд: {filteredCommands.length}</span>
                  {recentCommands.length > 0 && (
                    <span>Недавних: {recentCommands.length}</span>
                  )}
                </div>
                <div className="flex items-center space-x-1">
                  <Command className="h-3 w-3" />
                  <span>Командная палитра</span>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default CommandPalette;