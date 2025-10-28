import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Keyboard, X } from 'lucide-react';

const HotkeyTooltip = ({ children, hotkey, description, disabled = false }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });

  const handleMouseEnter = (event) => {
    if (disabled) return;
    
    const rect = event.currentTarget.getBoundingClientRect();
    setPosition({
      x: rect.left + rect.width / 2,
      y: rect.top - 10
    });
    setIsVisible(true);
  };

  const handleMouseLeave = () => {
    setIsVisible(false);
  };

  const formatHotkey = (hotkey) => {
    if (!hotkey) return '';
    
    return hotkey
      .split('+')
      .map(key => key.trim())
      .map(key => {
        // Замена названий клавиш на символы
        const keyMap = {
          'ctrl': '⌃',
          'cmd': '⌘',
          'alt': '⌥',
          'shift': '⇧',
          'enter': '↵',
          'escape': '⎋',
          'tab': '⇥',
          'space': '␣',
          'backspace': '⌫',
          'delete': '⌦',
          'up': '↑',
          'down': '↓',
          'left': '←',
          'right': '→'
        };
        
        return keyMap[key.toLowerCase()] || key.toUpperCase();
      })
      .join(' + ');
  };

  return (
    <>
      <div
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        className="relative"
      >
        {children}
      </div>

      <AnimatePresence>
        {isVisible && hotkey && (
          <motion.div
            initial={{ opacity: 0, y: 5, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 5, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className="fixed z-50 pointer-events-none"
            style={{
              left: position.x,
              top: position.y,
              transform: 'translateX(-50%) translateY(-100%)'
            }}
          >
            <div className="bg-gray-900 dark:bg-gray-700 text-white text-sm rounded-lg px-3 py-2 shadow-lg border border-gray-700 dark:border-gray-600 max-w-xs">
              <div className="flex items-center space-x-2">
                <Keyboard className="h-3 w-3 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  {description && (
                    <div className="font-medium truncate mb-1">
                      {description}
                    </div>
                  )}
                  <div className="flex items-center space-x-1">
                    {formatHotkey(hotkey).split(' + ').map((key, index, array) => (
                      <React.Fragment key={index}>
                        <kbd className="px-1.5 py-0.5 bg-gray-800 dark:bg-gray-600 rounded text-xs font-mono">
                          {key}
                        </kbd>
                        {index < array.length - 1 && (
                          <span className="text-gray-400">+</span>
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              </div>
              
              {/* Стрелка */}
              <div className="absolute top-full left-1/2 transform -translate-x-1/2">
                <div className="w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900 dark:border-t-gray-700"></div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

// Компонент для отображения справки по горячим клавишам
export const HotkeyHelp = ({ isOpen, onClose }) => {
  const [category, setCategory] = useState('navigation');

  const hotkeyCategories = {
    navigation: {
      name: 'Навигация',
      hotkeys: [
        { key: 'Ctrl + H', description: 'Перейти к дашборду' },
        { key: 'Ctrl + U', description: 'Управление пользователями' },
        { key: 'Ctrl + D', description: 'Управление документами' },
        { key: 'Ctrl + A', description: 'Аналитика' },
        { key: 'Ctrl + M', description: 'Модерация' },
        { key: 'Ctrl + N', description: 'Уведомления' },
        { key: 'Ctrl + B', description: 'Резервное копирование' }
      ]
    },
    actions: {
      name: 'Действия',
      hotkeys: [
        { key: 'Ctrl + K', description: 'Открыть командную палитру' },
        { key: 'Ctrl + ,', description: 'Настройки интерфейса' },
        { key: 'Ctrl + Shift + T', description: 'Переключить тему' },
        { key: 'F5', description: 'Обновить страницу' },
        { key: 'Ctrl + Shift + Q', description: 'Выйти из системы' },
        { key: 'Escape', description: 'Закрыть модальные окна' }
      ]
    },
    editing: {
      name: 'Редактирование',
      hotkeys: [
        { key: 'Ctrl + S', description: 'Сохранить изменения' },
        { key: 'Ctrl + Z', description: 'Отменить действие' },
        { key: 'Ctrl + Y', description: 'Повторить действие' },
        { key: 'Ctrl + C', description: 'Копировать' },
        { key: 'Ctrl + V', description: 'Вставить' },
        { key: 'Ctrl + X', description: 'Вырезать' }
      ]
    },
    search: {
      name: 'Поиск',
      hotkeys: [
        { key: 'Ctrl + F', description: 'Поиск на странице' },
        { key: '/', description: 'Быстрый поиск' },
        { key: 'Enter', description: 'Выполнить поиск' },
        { key: 'Escape', description: 'Очистить поиск' },
        { key: '↑ ↓', description: 'Навигация по результатам' }
      ]
    }
  };

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, onClose]);

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

          {/* Help Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-full max-w-4xl mx-4 bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 z-50 overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                  <Keyboard className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                    Горячие клавиши
                  </h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Быстрые команды для эффективной работы
                  </p>
                </div>
              </div>
              
              <button
                onClick={onClose}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="flex h-96">
              {/* Categories Sidebar */}
              <div className="w-48 border-r border-gray-200 dark:border-gray-700 p-4">
                <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                  Категории
                </h3>
                <div className="space-y-1">
                  {Object.entries(hotkeyCategories).map(([key, cat]) => (
                    <button
                      key={key}
                      onClick={() => setCategory(key)}
                      className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                        category === key
                          ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                          : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                      }`}
                    >
                      {cat.name}
                    </button>
                  ))}
                </div>
              </div>

              {/* Hotkeys List */}
              <div className="flex-1 p-6 overflow-y-auto">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                  {hotkeyCategories[category].name}
                </h3>
                
                <div className="space-y-3">
                  {hotkeyCategories[category].hotkeys.map((hotkey, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
                    >
                      <div className="text-gray-900 dark:text-white">
                        {hotkey.description}
                      </div>
                      <div className="flex items-center space-x-1">
                        {hotkey.key.split(' + ').map((key, keyIndex, array) => (
                          <React.Fragment key={keyIndex}>
                            <kbd className="px-2 py-1 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded text-sm font-mono">
                              {key}
                            </kbd>
                            {keyIndex < array.length - 1 && (
                              <span className="text-gray-400">+</span>
                            )}
                          </React.Fragment>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
              <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
                <div>
                  Нажмите <kbd className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-600 rounded">?</kbd> для открытия справки
                </div>
                <div>
                  <kbd className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-600 rounded">Esc</kbd> для закрытия
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default HotkeyTooltip;