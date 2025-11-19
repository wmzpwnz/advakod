import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Settings, 
  X, 
  Palette, 
  Layout, 
  Monitor, 
  Smartphone, 
  Tablet,
  Save,
  RotateCcw,
  Eye,
  Grid,
  Sidebar,
  Maximize2,
  Minimize2
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import ModernButton from './ModernButton';
import GlassCard from './GlassCard';

const SettingsPanel = ({ isOpen, onClose, onSettingsChange }) => {
  const { theme, toggleTheme, getModuleColor } = useTheme();
  
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
      notificationPosition: 'top-right'
    };
  });

  const [previewMode, setPreviewMode] = useState(false);
  const [activeTab, setActiveTab] = useState('appearance');

  // Сохранение настроек
  useEffect(() => {
    localStorage.setItem('adminPanelSettings', JSON.stringify(settings));
    if (onSettingsChange) {
      onSettingsChange(settings);
    }
  }, [settings, onSettingsChange]);

  const updateSetting = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const resetToDefaults = () => {
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
      notificationPosition: 'top-right'
    };
    setSettings(defaultSettings);
  };

  const accentColors = [
    { name: 'blue', color: '#3b82f6', label: 'Синий' },
    { name: 'purple', color: '#8b5cf6', label: 'Фиолетовый' },
    { name: 'green', color: '#10b981', label: 'Зеленый' },
    { name: 'orange', color: '#f97316', label: 'Оранжевый' },
    { name: 'red', color: '#ef4444', label: 'Красный' },
    { name: 'pink', color: '#ec4899', label: 'Розовый' },
    { name: 'indigo', color: '#6366f1', label: 'Индиго' },
    { name: 'teal', color: '#14b8a6', label: 'Бирюзовый' }
  ];

  const tabs = [
    { id: 'appearance', name: 'Внешний вид', icon: Palette },
    { id: 'layout', name: 'Макет', icon: Layout },
    { id: 'dashboard', name: 'Дашборд', icon: Grid },
    { id: 'performance', name: 'Производительность', icon: Monitor }
  ];

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

          {/* Settings Panel */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 h-full w-full max-w-2xl bg-white dark:bg-gray-900 shadow-2xl z-50 overflow-hidden"
          >
            <div className="flex flex-col h-full">
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                    <Settings className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                      Настройки интерфейса
                    </h2>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Кастомизация админ-панели
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setPreviewMode(!previewMode)}
                    className={`p-2 rounded-lg transition-colors ${
                      previewMode 
                        ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                        : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'
                    }`}
                    title="Режим предварительного просмотра"
                  >
                    <Eye className="h-5 w-5" />
                  </button>
                  
                  <button
                    onClick={onClose}
                    className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>
              </div>

              {/* Tabs */}
              <div className="flex border-b border-gray-200 dark:border-gray-700 px-6">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
                        activeTab === tab.id
                          ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                          : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      <span className="text-sm font-medium">{tab.name}</span>
                    </button>
                  );
                })}
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-6">
                {/* Appearance Tab */}
                {activeTab === 'appearance' && (
                  <div className="space-y-6">
                    {/* Theme Selection */}
                    <div>
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                        Тема оформления
                      </h3>
                      <div className="grid grid-cols-3 gap-3">
                        {[
                          { value: 'light', label: 'Светлая', icon: '☀️' },
                          { value: 'dark', label: 'Темная', icon: '🌙' },
                          { value: 'auto', label: 'Авто', icon: '🔄' }
                        ].map((themeOption) => (
                          <button
                            key={themeOption.value}
                            onClick={() => updateSetting('theme', themeOption.value)}
                            className={`p-4 rounded-lg border-2 transition-all ${
                              settings.theme === themeOption.value
                                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                            }`}
                          >
                            <div className="text-2xl mb-2">{themeOption.icon}</div>
                            <div className="text-sm font-medium text-gray-900 dark:text-white">
                              {themeOption.label}
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Accent Color */}
                    <div>
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                        Акцентный цвет
                      </h3>
                      <div className="grid grid-cols-4 gap-3">
                        {accentColors.map((color) => (
                          <button
                            key={color.name}
                            onClick={() => updateSetting('accentColor', color.name)}
                            className={`p-3 rounded-lg border-2 transition-all ${
                              settings.accentColor === color.name
                                ? 'border-gray-400 dark:border-gray-500'
                                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                            }`}
                          >
                            <div 
                              className="w-8 h-8 rounded-full mx-auto mb-2"
                              style={{ backgroundColor: color.color }}
                            />
                            <div className="text-xs text-gray-600 dark:text-gray-400">
                              {color.label}
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Border Radius */}
                    <div>
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                        Скругление углов
                      </h3>
                      <div className="grid grid-cols-3 gap-3">
                        {[
                          { value: 'sharp', label: 'Острые', preview: 'rounded-none' },
                          { value: 'rounded', label: 'Скругленные', preview: 'rounded-lg' },
                          { value: 'pill', label: 'Капсула', preview: 'rounded-full' }
                        ].map((radius) => (
                          <button
                            key={radius.value}
                            onClick={() => updateSetting('borderRadius', radius.value)}
                            className={`p-4 border-2 transition-all ${radius.preview} ${
                              settings.borderRadius === radius.value
                                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                            }`}
                          >
                            <div className="text-sm font-medium text-gray-900 dark:text-white">
                              {radius.label}
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Layout Tab */}
                {activeTab === 'layout' && (
                  <div className="space-y-6">
                    {/* Sidebar Width */}
                    <div>
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                        Ширина боковой панели
                      </h3>
                      <div className="space-y-3">
                        <input
                          type="range"
                          min="240"
                          max="400"
                          step="20"
                          value={settings.sidebarWidth}
                          onChange={(e) => updateSetting('sidebarWidth', parseInt(e.target.value))}
                          className="w-full"
                        />
                        <div className="flex justify-between text-sm text-gray-500 dark:text-gray-400">
                          <span>240px</span>
                          <span className="font-medium">{settings.sidebarWidth}px</span>
                          <span>400px</span>
                        </div>
                      </div>
                    </div>

                    {/* Layout Options */}
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                            Компактный режим
                          </h4>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            Уменьшенные отступы и размеры элементов
                          </p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={settings.compactMode}
                            onChange={(e) => updateSetting('compactMode', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                        </label>
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                            Показывать хлебные крошки
                          </h4>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            Навигационная цепочка в заголовке
                          </p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={settings.showBreadcrumbs}
                            onChange={(e) => updateSetting('showBreadcrumbs', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                        </label>
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                            Показывать подсказки
                          </h4>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            Всплывающие подсказки при наведении
                          </p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={settings.showTooltips}
                            onChange={(e) => updateSetting('showTooltips', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                        </label>
                      </div>
                    </div>
                  </div>
                )}

                {/* Dashboard Tab */}
                {activeTab === 'dashboard' && (
                  <div className="space-y-6">
                    {/* Dashboard Layout */}
                    <div>
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                        Макет дашборда
                      </h3>
                      <div className="grid grid-cols-2 gap-3">
                        {[
                          { value: 'grid', label: 'Сетка', icon: Grid },
                          { value: 'list', label: 'Список', icon: Sidebar }
                        ].map((layout) => {
                          const Icon = layout.icon;
                          return (
                            <button
                              key={layout.value}
                              onClick={() => updateSetting('dashboardLayout', layout.value)}
                              className={`p-4 rounded-lg border-2 transition-all ${
                                settings.dashboardLayout === layout.value
                                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                              }`}
                            >
                              <Icon className="h-6 w-6 mx-auto mb-2 text-gray-600 dark:text-gray-400" />
                              <div className="text-sm font-medium text-gray-900 dark:text-white">
                                {layout.label}
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    {/* Widget Spacing */}
                    <div>
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                        Расстояние между виджетами
                      </h3>
                      <div className="grid grid-cols-3 gap-3">
                        {[
                          { value: 'compact', label: 'Компактно' },
                          { value: 'normal', label: 'Обычно' },
                          { value: 'spacious', label: 'Просторно' }
                        ].map((spacing) => (
                          <button
                            key={spacing.value}
                            onClick={() => updateSetting('widgetSpacing', spacing.value)}
                            className={`p-3 rounded-lg border-2 transition-all ${
                              settings.widgetSpacing === spacing.value
                                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                            }`}
                          >
                            <div className="text-sm font-medium text-gray-900 dark:text-white">
                              {spacing.label}
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Dashboard Options */}
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                            Показывать заголовки виджетов
                          </h4>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            Отображение названий виджетов
                          </p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={settings.showWidgetTitles}
                            onChange={(e) => updateSetting('showWidgetTitles', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                        </label>
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                            Анимации
                          </h4>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            Плавные переходы и анимации
                          </p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={settings.animationsEnabled}
                            onChange={(e) => updateSetting('animationsEnabled', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                        </label>
                      </div>
                    </div>
                  </div>
                )}

                {/* Performance Tab */}
                {activeTab === 'performance' && (
                  <div className="space-y-6">
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                            Уменьшенная анимация
                          </h4>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            Отключение анимаций для лучшей производительности
                          </p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={settings.reducedMotion}
                            onChange={(e) => updateSetting('reducedMotion', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                        </label>
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                            Ленивая загрузка
                          </h4>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            Загрузка контента по мере необходимости
                          </p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={settings.lazyLoading}
                            onChange={(e) => updateSetting('lazyLoading', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                        </label>
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                            Кэширование
                          </h4>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            Сохранение данных для быстрого доступа
                          </p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input
                            type="checkbox"
                            checked={settings.cacheEnabled}
                            onChange={(e) => updateSetting('cacheEnabled', e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                        </label>
                      </div>
                    </div>

                    {/* Notification Position */}
                    <div>
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                        Позиция уведомлений
                      </h3>
                      <div className="grid grid-cols-2 gap-3">
                        {[
                          { value: 'top-right', label: 'Верх справа' },
                          { value: 'top-left', label: 'Верх слева' },
                          { value: 'bottom-right', label: 'Низ справа' },
                          { value: 'bottom-left', label: 'Низ слева' }
                        ].map((position) => (
                          <button
                            key={position.value}
                            onClick={() => updateSetting('notificationPosition', position.value)}
                            className={`p-3 rounded-lg border-2 transition-all ${
                              settings.notificationPosition === position.value
                                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                            }`}
                          >
                            <div className="text-sm font-medium text-gray-900 dark:text-white">
                              {position.label}
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="border-t border-gray-200 dark:border-gray-700 p-6">
                <div className="flex items-center justify-between">
                  <ModernButton
                    variant="glass-ghost"
                    size="sm"
                    onClick={resetToDefaults}
                    className="flex items-center space-x-2"
                  >
                    <RotateCcw className="h-4 w-4" />
                    <span>Сбросить</span>
                  </ModernButton>

                  <div className="flex items-center space-x-3">
                    <ModernButton
                      variant="glass-ghost"
                      size="sm"
                      onClick={onClose}
                    >
                      Отмена
                    </ModernButton>
                    
                    <ModernButton
                      variant="glass-primary"
                      size="sm"
                      onClick={onClose}
                      className="flex items-center space-x-2"
                    >
                      <Save className="h-4 w-4" />
                      <span>Сохранить</span>
                    </ModernButton>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default SettingsPanel;