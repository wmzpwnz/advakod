import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import useHotkeys from '../hooks/useHotkeys';
import CommandPalette from './CommandPalette';
import { HotkeyHelp } from './HotkeyTooltip';

const GlobalHotkeyManager = () => {
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [hotkeyHelpOpen, setHotkeyHelpOpen] = useState(false);
  const [settingsPanelOpen, setSettingsPanelOpen] = useState(false);
  
  const navigate = useNavigate();
  const { logout } = useAuth();
  const { toggleTheme } = useTheme();

  // Глобальные горячие клавиши
  const globalHotkeys = {
    // Командная палитра
    'ctrl+k': (e) => {
      e.preventDefault();
      setCommandPaletteOpen(true);
    },
    
    // Навигация
    'ctrl+h': () => navigate('/admin'),
    'ctrl+u': () => navigate('/admin/users'),
    'ctrl+d': () => navigate('/admin/documents'),
    'ctrl+a': () => navigate('/admin/analytics'),
    'ctrl+m': () => navigate('/admin/moderation'),
    'ctrl+n': () => navigate('/admin/notifications'),
    'ctrl+b': () => navigate('/admin/backup'),
    
    // Настройки
    'ctrl+,': () => {
      setSettingsPanelOpen(true);
      // Отправляем событие для открытия панели настроек
      window.dispatchEvent(new CustomEvent('openSettingsPanel'));
    },
    
    // Тема
    'ctrl+shift+t': toggleTheme,
    
    // Справка
    '?': () => setHotkeyHelpOpen(true),
    'f1': () => setHotkeyHelpOpen(true),
    
    // Системные действия
    'f5': () => window.location.reload(),
    'ctrl+shift+q': () => {
      if (window.confirm('Вы уверены, что хотите выйти из системы?')) {
        logout();
      }
    },
    
    // Закрытие модальных окон
    'escape': () => {
      if (commandPaletteOpen) {
        setCommandPaletteOpen(false);
      } else if (hotkeyHelpOpen) {
        setHotkeyHelpOpen(false);
      } else if (settingsPanelOpen) {
        setSettingsPanelOpen(false);
      }
    }
  };

  // Регистрируем горячие клавиши
  useHotkeys(globalHotkeys);

  // Слушаем события для открытия панелей
  useEffect(() => {
    const handleOpenSettingsPanel = () => {
      setSettingsPanelOpen(true);
    };

    const handleOpenCommandPalette = () => {
      setCommandPaletteOpen(true);
    };

    const handleOpenHotkeyHelp = () => {
      setHotkeyHelpOpen(true);
    };

    window.addEventListener('openSettingsPanel', handleOpenSettingsPanel);
    window.addEventListener('openCommandPalette', handleOpenCommandPalette);
    window.addEventListener('openHotkeyHelp', handleOpenHotkeyHelp);

    return () => {
      window.removeEventListener('openSettingsPanel', handleOpenSettingsPanel);
      window.removeEventListener('openCommandPalette', handleOpenCommandPalette);
      window.removeEventListener('openHotkeyHelp', handleOpenHotkeyHelp);
    };
  }, []);

  // Показываем уведомление о доступности горячих клавиш при первом посещении
  useEffect(() => {
    const hasSeenHotkeyNotification = localStorage.getItem('hasSeenHotkeyNotification');
    
    if (!hasSeenHotkeyNotification) {
      const timer = setTimeout(() => {
        // Показываем небольшое уведомление
        const notification = document.createElement('div');
        notification.className = 'fixed bottom-4 right-4 bg-blue-600 text-white px-4 py-3 rounded-lg shadow-lg z-50 max-w-sm';
        notification.innerHTML = `
          <div class="flex items-center space-x-2">
            <div class="flex-1">
              <div class="font-medium">Горячие клавиши доступны!</div>
              <div class="text-sm opacity-90">Нажмите <kbd class="px-1 py-0.5 bg-blue-700 rounded text-xs">Ctrl+K</kbd> для командной палитры</div>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" class="text-blue-200 hover:text-white">
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
              </svg>
            </button>
          </div>
        `;
        
        document.body.appendChild(notification);
        
        // Автоматически скрываем через 5 секунд
        setTimeout(() => {
          if (notification.parentElement) {
            notification.remove();
          }
        }, 5000);
        
        localStorage.setItem('hasSeenHotkeyNotification', 'true');
      }, 2000);

      return () => clearTimeout(timer);
    }
  }, []);

  return (
    <>
      {/* Command Palette */}
      <CommandPalette
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
      />

      {/* Hotkey Help */}
      <HotkeyHelp
        isOpen={hotkeyHelpOpen}
        onClose={() => setHotkeyHelpOpen(false)}
      />
    </>
  );
};

export default GlobalHotkeyManager;