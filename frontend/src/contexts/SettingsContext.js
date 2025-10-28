import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useAuth } from './AuthContext';

const SettingsContext = createContext();

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};

export const SettingsProvider = ({ children }) => {
  const { user, token } = useAuth();
  
  // Настройки интерфейса
  const [settings, setSettings] = useState(() => {
    const saved = localStorage.getItem('adminPanelSettings');
    return saved ? JSON.parse(saved) : {
      // Тема и цвета
      theme: 'auto',
      accentColor: 'blue',
      borderRadius: 'rounded',
      
      // Макет
      sidebarWidth: 280,
      compactMode: false,
      showBreadcrumbs: true,
      showTooltips: true,
      
      // Дашборд
      dashboardLayout: 'grid',
      widgetSpacing: 'normal',
      showWidgetTitles: true,
      animationsEnabled: true,
      
      // Производительность
      reducedMotion: false,
      lazyLoading: true,
      cacheEnabled: true,
      
      // Уведомления
      desktopNotifications: true,
      soundEnabled: false,
      notificationPosition: 'top-right',
      
      // Дашборд виджеты
      dashboardWidgets: []
    };
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Загрузка настроек с сервера
  const loadServerSettings = useCallback(async () => {
    if (!user || !token) return;

    try {
      setLoading(true);
      const response = await fetch('/api/v1/admin/settings', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const serverSettings = await response.json();
        // Объединяем локальные и серверные настройки
        setSettings(prev => ({
          ...prev,
          ...serverSettings
        }));
      }
    } catch (err) {
      console.error('Failed to load server settings:', err);
      setError('Не удалось загрузить настройки с сервера');
    } finally {
      setLoading(false);
    }
  }, [user, token]);

  // Сохранение настроек на сервер
  const saveServerSettings = useCallback(async (newSettings) => {
    if (!user || !token) return;

    try {
      const response = await fetch('/api/v1/admin/settings', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newSettings)
      });

      if (!response.ok) {
        throw new Error('Failed to save settings');
      }
    } catch (err) {
      console.error('Failed to save server settings:', err);
      setError('Не удалось сохранить настройки на сервер');
    }
  }, [user, token]);

  // Обновление настроек
  const updateSettings = useCallback((newSettings) => {
    setSettings(prev => {
      const updated = { ...prev, ...newSettings };
      
      // Сохраняем в localStorage
      localStorage.setItem('adminPanelSettings', JSON.stringify(updated));
      
      // Сохраняем на сервер (асинхронно)
      saveServerSettings(updated);
      
      return updated;
    });
  }, [saveServerSettings]);

  // Обновление одной настройки
  const updateSetting = useCallback((key, value) => {
    updateSettings({ [key]: value });
  }, [updateSettings]);

  // Сброс настроек к значениям по умолчанию
  const resetSettings = useCallback(() => {
    const defaultSettings = {
      theme: 'auto',
      accentColor: 'blue',
      borderRadius: 'rounded',
      sidebarWidth: 280,
      compactMode: false,
      showBreadcrumbs: true,
      showTooltips: true,
      dashboardLayout: 'grid',
      widgetSpacing: 'normal',
      showWidgetTitles: true,
      animationsEnabled: true,
      reducedMotion: false,
      lazyLoading: true,
      cacheEnabled: true,
      desktopNotifications: true,
      soundEnabled: false,
      notificationPosition: 'top-right',
      dashboardWidgets: []
    };
    
    updateSettings(defaultSettings);
  }, [updateSettings]);

  // Управление виджетами дашборда
  const updateDashboardLayout = useCallback((widgets) => {
    updateSetting('dashboardWidgets', widgets);
  }, [updateSetting]);

  const addDashboardWidget = useCallback((widget) => {
    setSettings(prev => {
      const updated = {
        ...prev,
        dashboardWidgets: [...prev.dashboardWidgets, widget]
      };
      localStorage.setItem('adminPanelSettings', JSON.stringify(updated));
      saveServerSettings(updated);
      return updated;
    });
  }, [saveServerSettings]);

  const removeDashboardWidget = useCallback((widgetId) => {
    setSettings(prev => {
      const updated = {
        ...prev,
        dashboardWidgets: prev.dashboardWidgets.filter(w => w.id !== widgetId)
      };
      localStorage.setItem('adminPanelSettings', JSON.stringify(updated));
      saveServerSettings(updated);
      return updated;
    });
  }, [saveServerSettings]);

  const updateDashboardWidget = useCallback((widgetId, updates) => {
    setSettings(prev => {
      const updated = {
        ...prev,
        dashboardWidgets: prev.dashboardWidgets.map(w => 
          w.id === widgetId ? { ...w, ...updates } : w
        )
      };
      localStorage.setItem('adminPanelSettings', JSON.stringify(updated));
      saveServerSettings(updated);
      return updated;
    });
  }, [saveServerSettings]);

  // Применение настроек к DOM
  useEffect(() => {
    const root = document.documentElement;
    
    // Применяем CSS переменные для кастомизации
    root.style.setProperty('--sidebar-width', `${settings.sidebarWidth}px`);
    root.style.setProperty('--border-radius', 
      settings.borderRadius === 'sharp' ? '0px' :
      settings.borderRadius === 'pill' ? '9999px' : '0.5rem'
    );
    
    // Применяем класс для компактного режима
    if (settings.compactMode) {
      root.classList.add('compact-mode');
    } else {
      root.classList.remove('compact-mode');
    }
    
    // Применяем настройки анимации
    if (settings.reducedMotion) {
      root.classList.add('reduce-motion');
    } else {
      root.classList.remove('reduce-motion');
    }
    
    // Применяем акцентный цвет
    const accentColors = {
      blue: '#3b82f6',
      purple: '#8b5cf6',
      green: '#10b981',
      orange: '#f97316',
      red: '#ef4444',
      pink: '#ec4899',
      indigo: '#6366f1',
      teal: '#14b8a6'
    };
    
    root.style.setProperty('--accent-color', accentColors[settings.accentColor] || accentColors.blue);
  }, [settings]);

  // Загрузка настроек при входе пользователя
  useEffect(() => {
    if (user && token) {
      loadServerSettings();
    }
  }, [user, token, loadServerSettings]);

  // Очистка ошибок
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const value = {
    settings,
    loading,
    error,
    updateSettings,
    updateSetting,
    resetSettings,
    updateDashboardLayout,
    addDashboardWidget,
    removeDashboardWidget,
    updateDashboardWidget,
    clearError,
    
    // Вспомогательные геттеры
    isCompactMode: settings.compactMode,
    isDarkTheme: settings.theme === 'dark',
    isLightTheme: settings.theme === 'light',
    isAutoTheme: settings.theme === 'auto',
    accentColor: settings.accentColor,
    sidebarWidth: settings.sidebarWidth,
    dashboardWidgets: settings.dashboardWidgets || [],
    animationsEnabled: settings.animationsEnabled && !settings.reducedMotion,
    
    // CSS классы для применения настроек
    getContainerClasses: () => {
      const classes = [];
      
      if (settings.compactMode) classes.push('compact-mode');
      if (settings.reducedMotion) classes.push('reduce-motion');
      if (!settings.animationsEnabled) classes.push('no-animations');
      
      return classes.join(' ');
    },
    
    getBorderRadiusClass: () => {
      switch (settings.borderRadius) {
        case 'sharp': return 'rounded-none';
        case 'pill': return 'rounded-full';
        default: return 'rounded-lg';
      }
    },
    
    getSpacingClass: () => {
      switch (settings.widgetSpacing) {
        case 'compact': return 'gap-2';
        case 'spacious': return 'gap-8';
        default: return 'gap-4';
      }
    }
  };

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
};

export default SettingsContext;