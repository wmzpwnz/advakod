import React, { createContext, useContext, useEffect, useState } from 'react';

const ThemeContext = createContext();

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(() => {
    // Проверяем сохраненную тему или системные настройки
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      return savedTheme;
    }
    
    // Проверяем системные настройки
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    
    return 'light';
  });

  useEffect(() => {
    // Применяем тему к документу
    const root = document.documentElement;
    
    if (theme === 'dark') {
      root.classList.add('dark');
      root.classList.remove('light');
    } else {
      root.classList.add('light');
      root.classList.remove('dark');
    }
    
    // Сохраняем тему в localStorage
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prevTheme => prevTheme === 'light' ? 'dark' : 'light');
  };

  const setLightTheme = () => setTheme('light');
  const setDarkTheme = () => setTheme('dark');

  // Module color utilities
  const getModuleColor = (module, variant = 'DEFAULT') => {
    const moduleColors = {
      marketing: {
        DEFAULT: theme === 'dark' ? '#f97316' : '#f97316',
        light: theme === 'dark' ? '#fed7aa' : '#fb923c',
        dark: theme === 'dark' ? '#ea580c' : '#ea580c',
        50: '#fff7ed',
        100: '#ffedd5',
        200: '#fed7aa',
        300: '#fdba74',
        400: '#fb923c',
        500: '#f97316',
        600: '#ea580c',
        700: '#c2410c',
        800: '#9a3412',
        900: '#7c2d12',
      },
      moderation: {
        DEFAULT: theme === 'dark' ? '#8b5cf6' : '#a855f7',
        light: theme === 'dark' ? '#ddd6fe' : '#c084fc',
        dark: theme === 'dark' ? '#7c3aed' : '#9333ea',
        50: '#faf5ff',
        100: '#f3e8ff',
        200: '#e9d5ff',
        300: '#d8b4fe',
        400: '#c084fc',
        500: '#a855f7',
        600: '#9333ea',
        700: '#7c3aed',
        800: '#6b21a8',
        900: '#581c87',
      },
      project: {
        DEFAULT: theme === 'dark' ? '#10b981' : '#10b981',
        light: theme === 'dark' ? '#a7f3d0' : '#34d399',
        dark: theme === 'dark' ? '#059669' : '#059669',
        50: '#ecfdf5',
        100: '#d1fae5',
        200: '#a7f3d0',
        300: '#6ee7b7',
        400: '#34d399',
        500: '#10b981',
        600: '#059669',
        700: '#047857',
        800: '#065f46',
        900: '#064e3b',
      },
      analytics: {
        DEFAULT: theme === 'dark' ? '#3b82f6' : '#3b82f6',
        light: theme === 'dark' ? '#bfdbfe' : '#60a5fa',
        dark: theme === 'dark' ? '#2563eb' : '#2563eb',
        50: '#eff6ff',
        100: '#dbeafe',
        200: '#bfdbfe',
        300: '#93c5fd',
        400: '#60a5fa',
        500: '#3b82f6',
        600: '#2563eb',
        700: '#1d4ed8',
        800: '#1e40af',
        900: '#1e3a8a',
      },
      system: {
        DEFAULT: theme === 'dark' ? '#ef4444' : '#ef4444',
        light: theme === 'dark' ? '#fecaca' : '#f87171',
        dark: theme === 'dark' ? '#dc2626' : '#dc2626',
        50: '#fef2f2',
        100: '#fee2e2',
        200: '#fecaca',
        300: '#fca5a5',
        400: '#f87171',
        500: '#ef4444',
        600: '#dc2626',
        700: '#b91c1c',
        800: '#991b1b',
        900: '#7f1d1d',
      },
    };

    return moduleColors[module]?.[variant] || moduleColors[module]?.DEFAULT || '#6b7280';
  };

  const value = {
    theme,
    toggleTheme,
    setLightTheme,
    setDarkTheme,
    isDark: theme === 'dark',
    isLight: theme === 'light',
    getModuleColor,
    moduleColors: {
      marketing: getModuleColor('marketing'),
      moderation: getModuleColor('moderation'),
      project: getModuleColor('project'),
      analytics: getModuleColor('analytics'),
      system: getModuleColor('system'),
    }
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};
