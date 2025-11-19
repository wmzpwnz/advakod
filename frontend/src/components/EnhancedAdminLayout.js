import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Settings } from 'lucide-react';

// Import all UX enhancement components
import { SettingsProvider } from '../contexts/SettingsContext';
import SettingsPanel from './SettingsPanel';
import DashboardCustomizer from './DashboardCustomizer';
import GlobalHotkeyManager from './GlobalHotkeyManager';
import MobileNavigation from './MobileNavigation';
import ResponsiveContainer, { useResponsive } from './ResponsiveContainer';
import { useContextMenu } from './ContextMenu';
import HotkeyTooltip from './HotkeyTooltip';

// Import responsive styles
import '../styles/responsive.css';

const EnhancedAdminLayout = () => {
  const [settingsPanelOpen, setSettingsPanelOpen] = useState(false);
  const [dashboardCustomizerOpen, setDashboardCustomizerOpen] = useState(false);
  const [settings, setSettings] = useState({});
  
  const { isMobile, isTablet, isDesktop, isTouchDevice } = useResponsive();
  const { ContextMenuComponent } = useContextMenu();

  // Listen for settings panel open events
  useEffect(() => {
    const handleOpenSettingsPanel = () => {
      setSettingsPanelOpen(true);
    };

    const handleOpenDashboardCustomizer = () => {
      setDashboardCustomizerOpen(true);
    };

    window.addEventListener('openSettingsPanel', handleOpenSettingsPanel);
    window.addEventListener('openDashboardCustomizer', handleOpenDashboardCustomizer);

    return () => {
      window.removeEventListener('openSettingsPanel', handleOpenSettingsPanel);
      window.removeEventListener('openDashboardCustomizer', handleOpenDashboardCustomizer);
    };
  }, []);

  // Apply settings to layout
  const handleSettingsChange = (newSettings) => {
    setSettings(newSettings);
    
    // Apply CSS custom properties
    const root = document.documentElement;
    
    if (newSettings.sidebarWidth) {
      root.style.setProperty('--sidebar-width', `${newSettings.sidebarWidth}px`);
    }
    
    if (newSettings.borderRadius) {
      const radiusValue = newSettings.borderRadius === 'sharp' ? '0px' :
                         newSettings.borderRadius === 'pill' ? '9999px' : '0.5rem';
      root.style.setProperty('--border-radius', radiusValue);
    }
    
    // Apply theme classes
    if (newSettings.compactMode) {
      root.classList.add('compact-mode');
    } else {
      root.classList.remove('compact-mode');
    }
    
    if (newSettings.reducedMotion) {
      root.classList.add('reduce-motion');
    } else {
      root.classList.remove('reduce-motion');
    }
  };

  const handleDashboardLayoutSave = (layout) => {
    setSettings(prev => ({
      ...prev,
      dashboardWidgets: layout
    }));
  };

  return (
    <SettingsProvider>
      <ResponsiveContainer
        className={`min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200 ${
          settings.compactMode ? 'compact-mode' : ''
        } ${
          settings.reducedMotion ? 'reduce-motion' : ''
        } ${
          isTouchDevice ? 'touch-device' : ''
        }`}
        mobileClassName="mobile-layout"
        tabletClassName="tablet-layout"
        desktopClassName="desktop-layout"
      >
        {({ screenSize, isTouchDevice: isTouch }) => (
          <>
            {/* Mobile Navigation */}
            {screenSize === 'mobile' && <MobileNavigation />}

            {/* Settings Button - Desktop Only */}
            {screenSize === 'desktop' && (
              <HotkeyTooltip 
                hotkey="Ctrl+," 
                description="Открыть настройки интерфейса"
              >
                <motion.button
                  onClick={() => setSettingsPanelOpen(true)}
                  className="fixed bottom-6 right-6 z-40 p-4 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-200"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  aria-label="Настройки интерфейса"
                >
                  <Settings className="h-6 w-6" />
                </motion.button>
              </HotkeyTooltip>
            )}

            {/* Main Content Area */}
            <div className={`
              ${screenSize === 'mobile' ? 'pt-20' : ''}
              ${settings.compactMode ? 'compact-spacing' : 'normal-spacing'}
              transition-all duration-200
            `}>
              <main className="responsive-container">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={screenSize}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.3 }}
                    className={`
                      ${screenSize === 'mobile' ? 'mobile-content' : ''}
                      ${screenSize === 'tablet' ? 'tablet-content' : ''}
                      ${screenSize === 'desktop' ? 'desktop-content' : ''}
                    `}
                  >
                    <Outlet />
                  </motion.div>
                </AnimatePresence>
              </main>
            </div>

            {/* Settings Panel */}
            <SettingsPanel
              isOpen={settingsPanelOpen}
              onClose={() => setSettingsPanelOpen(false)}
              onSettingsChange={handleSettingsChange}
            />

            {/* Dashboard Customizer */}
            <DashboardCustomizer
              isOpen={dashboardCustomizerOpen}
              onClose={() => setDashboardCustomizerOpen(false)}
              onSave={handleDashboardLayoutSave}
              initialLayout={settings.dashboardWidgets || []}
            />

            {/* Global Hotkey Manager */}
            <GlobalHotkeyManager />

            {/* Context Menu */}
            <ContextMenuComponent />

            {/* Responsive Indicator (Development Only) */}
            {process.env.NODE_ENV === 'development' && (
              <div className="fixed top-4 right-4 z-50 px-3 py-1 bg-black/80 text-white text-xs rounded-full font-mono">
                {screenSize} {isTouch ? '(touch)' : '(mouse)'}
              </div>
            )}
          </>
        )}
      </ResponsiveContainer>
    </SettingsProvider>
  );
};

// Enhanced Admin Dashboard with UX improvements
export const EnhancedAdminDashboard = () => {
  const { isMobile, isTablet } = useResponsive();
  const [dashboardLayout, setDashboardLayout] = useState([]);

  // Sample dashboard widgets for demonstration
  const sampleWidgets = [
    {
      id: 'user-stats-1',
      type: 'user-stats',
      name: 'Статистика пользователей',
      size: { w: 2, h: 1 },
      position: { x: 0, y: 0 },
      visible: true
    },
    {
      id: 'revenue-chart-1',
      type: 'revenue-chart',
      name: 'График доходов',
      size: { w: 3, h: 2 },
      position: { x: 2, y: 0 },
      visible: true
    },
    {
      id: 'system-health-1',
      type: 'system-health',
      name: 'Состояние системы',
      size: { w: 2, h: 1 },
      position: { x: 0, y: 1 },
      visible: true
    }
  ];

  useEffect(() => {
    // Load dashboard layout from settings
    const savedLayout = localStorage.getItem('dashboardLayout');
    if (savedLayout) {
      setDashboardLayout(JSON.parse(savedLayout));
    } else {
      setDashboardLayout(sampleWidgets);
    }
  }, []);

  const handleCustomizeDashboard = () => {
    window.dispatchEvent(new CustomEvent('openDashboardCustomizer'));
  };

  return (
    <div className="space-y-6">
      {/* Dashboard Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="responsive-text-2xl font-bold text-gray-900 dark:text-white">
            Дашборд админ-панели
          </h1>
          <p className="responsive-text-sm text-gray-600 dark:text-gray-400 mt-1">
            Добро пожаловать в улучшенную админ-панель АДВАКОД
          </p>
        </div>
        
        {!isMobile && (
          <HotkeyTooltip 
            hotkey="Ctrl+Shift+D" 
            description="Настроить дашборд"
          >
            <button
              onClick={handleCustomizeDashboard}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors duration-200 flex items-center space-x-2"
            >
              <Settings className="h-4 w-4" />
              <span>Настроить</span>
            </button>
          </HotkeyTooltip>
        )}
      </div>

      {/* Dashboard Grid */}
      <div className={`
        responsive-grid
        ${isMobile ? 'cols-1' : ''}
        ${isTablet ? 'cols-md-2' : ''}
        cols-lg-3
      `}>
        {dashboardLayout.filter(widget => widget.visible).map((widget) => (
          <motion.div
            key={widget.id}
            className={`
              bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6
              ${widget.size.w === 2 ? 'md:col-span-2' : ''}
              ${widget.size.w === 3 ? 'lg:col-span-3' : ''}
              ${widget.size.h === 2 ? 'row-span-2' : ''}
            `}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            whileHover={{ y: -2 }}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                {widget.name}
              </h3>
              <div className="text-2xl">
                {widget.type === 'user-stats' && '👥'}
                {widget.type === 'revenue-chart' && '💰'}
                {widget.type === 'system-health' && '⚡'}
              </div>
            </div>
            
            <div className="flex items-center justify-center h-32 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <p className="text-gray-500 dark:text-gray-400">
                Содержимое виджета {widget.name}
              </p>
            </div>
          </motion.div>
        ))}
      </div>

      {/* UX Features Showcase */}
      <div className="mt-12 p-6 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <h2 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-4">
          🎉 Новые возможности UX
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="flex items-start space-x-3">
            <div className="text-2xl">⚙️</div>
            <div>
              <h3 className="font-medium text-blue-900 dark:text-blue-100">
                Кастомизация интерфейса
              </h3>
              <p className="text-sm text-blue-700 dark:text-blue-300">
                Настройте тему, цвета и макет под свои предпочтения
              </p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="text-2xl">⌨️</div>
            <div>
              <h3 className="font-medium text-blue-900 dark:text-blue-100">
                Горячие клавиши
              </h3>
              <p className="text-sm text-blue-700 dark:text-blue-300">
                Быстрая навигация с помощью клавиатурных сочетаний
              </p>
            </div>
          </div>
          
          <div className="flex items-start space-x-3">
            <div className="text-2xl">📱</div>
            <div>
              <h3 className="font-medium text-blue-900 dark:text-blue-100">
                Адаптивный дизайн
              </h3>
              <p className="text-sm text-blue-700 dark:text-blue-300">
                Оптимизировано для всех устройств и размеров экранов
              </p>
            </div>
          </div>
        </div>
        
        <div className="mt-4 text-sm text-blue-600 dark:text-blue-400">
          💡 Нажмите <kbd className="px-2 py-1 bg-blue-200 dark:bg-blue-800 rounded text-xs">Ctrl+K</kbd> для открытия командной палитры
        </div>
      </div>
    </div>
  );
};

export default EnhancedAdminLayout;