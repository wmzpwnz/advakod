import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BarChart3, 
  Users, 
  FileText, 
  Shield, 
  Settings, 
  Brain,
  TrendingUp,
  Calendar,
  Bell,
  Database,
  Zap,
  Target,
  MessageSquare,
  Award,
  DollarSign,
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  Search,
  Filter,
  Download,
  RefreshCw,
  Menu,
  X,
  ChevronRight,
  Home,
  HelpCircle
} from 'lucide-react';

// Import all module components
import UserManagement from '../components/UserManagement';
import DocumentManagement from '../components/DocumentManagement';
import EnhancedRoleManagement from '../components/EnhancedRoleManagement';
import EnhancedModerationPanel from '../components/EnhancedModerationPanel';
import ModerationAnalytics from '../components/ModerationAnalytics';
import ModerationGamification from '../components/ModerationGamification';
import MarketingDashboard from '../components/MarketingDashboard';
import PromoCodeManager from '../components/PromoCodeManager';
import TrafficAnalytics from '../components/TrafficAnalytics';
import ABTestManager from '../components/ABTestManager';
import ProjectDashboard from '../components/ProjectDashboard';
import TaskManager from '../components/TaskManager';
import ProjectCalendar from '../components/ProjectCalendar';
import ResourceTracker from '../components/ResourceTracker';
import NotificationCenter from '../components/NotificationCenter';
import PushNotificationSettings from '../components/PushNotificationSettings';
import DashboardBuilder from '../components/DashboardBuilder';
import CohortAnalysis from '../components/CohortAnalysis';
import MetricsBuilder from '../components/MetricsBuilder';
import MLInsights from '../components/MLInsights';
import BackupManager from '../components/BackupManager';
import RestoreManager from '../components/RestoreManager';
import BackupIntegrityMonitor from '../components/BackupIntegrityMonitor';
import LogsViewer from '../components/LogsViewer';
import ModuleCard from '../components/ModuleCard';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorBoundary from '../components/ErrorBoundary';

// Import UX enhancement components
import EnhancedAdminLayout from '../components/EnhancedAdminLayout';
import GlobalHotkeyManager from '../components/GlobalHotkeyManager';
import CommandPalette from '../components/CommandPalette';
import { SettingsProvider } from '../contexts/SettingsContext';

// Import documentation and training components
import AdminTourManager from '../components/AdminTourManager';
import VideoGuideLibrary from '../components/VideoGuideLibrary';
import HelpSystem from '../components/HelpSystem';

import { getApiUrl } from '../config/api';
import axios from 'axios';

// Import WebSocket hooks
import { 
  useAdminWebSocket, 
  useAdminDashboard, 
  useUserActivity, 
  useSystemAlerts, 
  useModerationQueue, 
  useAdminNotifications 
} from '../hooks/useAdminWebSocket';

// Import tab sync hooks
import { 
  useTabSync,
  useDashboardSync,
  useNotificationSync,
  useUserActivitySync,
  useSystemAlertsSync,
  useModerationQueueSync,
  useUIStateSync
} from '../hooks/useTabSync';

const IntegratedAdminPanel = () => {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  
  // State management
  const [activeModule, setActiveModule] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [videoGuideLibraryOpen, setVideoGuideLibraryOpen] = useState(false);
  const [helpSystemOpen, setHelpSystemOpen] = useState(false);

  // WebSocket hooks for real-time updates
  const { 
    connectionStatus, 
    isConnected, 
    sendAdminAction,
    requestRefresh 
  } = useAdminWebSocket({
    autoConnect: true,
    subscriptions: ['admin_dashboard', 'system_alerts', 'notifications'],
    onMessage: (data) => {
      console.log('Admin WebSocket message:', data);
    },
    onConnect: () => {
      console.log('Admin WebSocket connected');
    },
    onDisconnect: () => {
      console.log('Admin WebSocket disconnected');
    }
  });

  // Real-time dashboard data
  const { 
    dashboardData: realtimeDashboardData, 
    lastUpdate: dashboardLastUpdate 
  } = useAdminDashboard();

  // Real-time user activity
  const { 
    userActivity, 
    onlineUsers 
  } = useUserActivity();

  // Real-time system alerts
  const { 
    alerts: systemAlerts, 
    criticalAlerts, 
    dismissAlert,
    clearCriticalCount 
  } = useSystemAlerts();

  // Real-time moderation queue
  const { 
    queueSize: moderationQueueSize, 
    pendingReviews,
    recentActions: moderationActions 
  } = useModerationQueue();

  // Real-time notifications
  const { 
    notifications, 
    unreadCount: notificationCount, 
    markAsRead, 
    markAllAsRead 
  } = useAdminNotifications();

  // Tab synchronization
  const { isLeader, tabId } = useTabSync({
    onDataSync: (data) => {
      console.log('Tab sync data received:', data);
    },
    onLeaderChange: (data) => {
      console.log('Leader changed:', data);
    }
  });

  // Sync dashboard data across tabs
  const { 
    syncedDashboardData, 
    syncDashboard 
  } = useDashboardSync();

  // Sync notifications across tabs
  const { 
    syncedNotifications, 
    unreadCount: syncedUnreadCount, 
    syncNotifications,
    markAsReadAcrossTabs 
  } = useNotificationSync();

  // Sync user activity across tabs
  const { 
    syncedUserActivity, 
    onlineUsers: syncedOnlineUsers, 
    syncUserActivity 
  } = useUserActivitySync();

  // Sync system alerts across tabs
  const { 
    syncedAlerts, 
    criticalCount: syncedCriticalCount, 
    syncSystemAlerts,
    dismissAlertAcrossTabs 
  } = useSystemAlertsSync();

  // Sync moderation queue across tabs
  const { 
    syncedQueueSize, 
    syncModerationQueue 
  } = useModerationQueueSync();

  // Sync UI state across tabs
  const { 
    syncedActiveModule, 
    syncedSidebarOpen, 
    syncActiveModule: syncActiveModuleAcrossTabs, 
    syncSidebarState 
  } = useUIStateSync();

  // Check admin permissions
  useEffect(() => {
    if (!user || !user.is_admin) {
      navigate('/');
      return;
    }
    loadDashboardData();
  }, [user, navigate]);

  // Load dashboard data
  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const response = await axios.get(getApiUrl('/admin/dashboard'), {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setDashboardData(response.data);
      
      // Request real-time refresh if WebSocket is connected
      if (isConnected) {
        requestRefresh('dashboard');
      }
      
      // Sync dashboard data across tabs if we're the leader
      if (isLeader) {
        syncDashboard(response.data);
      }
    } catch (err) {
      setError('Ошибка загрузки данных дашборда');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  }, [token, isConnected, requestRefresh]);

  // Use real-time data if available, fallback to synced data, then static data
  const currentDashboardData = realtimeDashboardData || syncedDashboardData || dashboardData;
  
  // Use synced data when available for cross-tab consistency
  const currentNotifications = syncedNotifications.length > 0 ? syncedNotifications : notifications;
  const currentNotificationCount = syncedUnreadCount > 0 ? syncedUnreadCount : notificationCount;
  const currentOnlineUsers = syncedOnlineUsers > 0 ? syncedOnlineUsers : onlineUsers;
  const currentSystemAlerts = syncedAlerts.length > 0 ? syncedAlerts : systemAlerts;
  const currentCriticalAlerts = syncedCriticalCount > 0 ? syncedCriticalCount : criticalAlerts;
  const currentModerationQueueSize = syncedQueueSize > 0 ? syncedQueueSize : moderationQueueSize;

  // Module definitions with all implemented features
  const modules = [
    {
      id: 'dashboard',
      name: 'Главный дашборд',
      icon: Home,
      color: 'blue',
      description: 'Обзор системы и ключевые метрики',
      permissions: ['admin.dashboard.view']
    },
    {
      id: 'users',
      name: 'Пользователи',
      icon: Users,
      color: 'green',
      description: 'Управление пользователями системы',
      permissions: ['admin.users.view']
    },
    {
      id: 'documents',
      name: 'Документы',
      icon: FileText,
      color: 'purple',
      description: 'Управление документами RAG системы',
      permissions: ['admin.documents.view']
    },
    {
      id: 'roles',
      name: 'Роли и права',
      icon: Shield,
      color: 'red',
      description: 'Управление ролями и правами доступа',
      permissions: ['admin.roles.view']
    },
    {
      id: 'moderation',
      name: 'Модерация',
      icon: MessageSquare,
      color: 'indigo',
      description: 'Система модерации ответов ИИ',
      permissions: ['admin.moderation.view'],
      subModules: [
        { id: 'moderation-queue', name: 'Очередь модерации', component: 'EnhancedModerationPanel' },
        { id: 'moderation-analytics', name: 'Аналитика модерации', component: 'ModerationAnalytics' },
        { id: 'moderation-gamification', name: 'Геймификация', component: 'ModerationGamification' }
      ]
    },
    {
      id: 'marketing',
      name: 'Маркетинг',
      icon: TrendingUp,
      color: 'orange',
      description: 'Маркетинговые инструменты и аналитика',
      permissions: ['admin.marketing.view'],
      subModules: [
        { id: 'marketing-dashboard', name: 'Дашборд маркетинга', component: 'MarketingDashboard' },
        { id: 'promo-codes', name: 'Промокоды', component: 'PromoCodeManager' },
        { id: 'traffic-analytics', name: 'Аналитика трафика', component: 'TrafficAnalytics' },
        { id: 'ab-testing', name: 'A/B тестирование', component: 'ABTestManager' }
      ]
    },
    {
      id: 'project',
      name: 'Управление проектом',
      icon: Target,
      color: 'emerald',
      description: 'Инструменты управления проектом',
      permissions: ['admin.project.view'],
      subModules: [
        { id: 'project-dashboard', name: 'Дашборд проекта', component: 'ProjectDashboard' },
        { id: 'task-manager', name: 'Управление задачами', component: 'TaskManager' },
        { id: 'project-calendar', name: 'Календарь проекта', component: 'ProjectCalendar' },
        { id: 'resource-tracker', name: 'Отслеживание ресурсов', component: 'ResourceTracker' }
      ]
    },
    {
      id: 'notifications',
      name: 'Уведомления',
      icon: Bell,
      color: 'yellow',
      description: 'Система уведомлений и алертов',
      permissions: ['admin.notifications.view'],
      subModules: [
        { id: 'notification-center', name: 'Центр уведомлений', component: 'NotificationCenter' },
        { id: 'push-settings', name: 'Push уведомления', component: 'PushNotificationSettings' }
      ]
    },
    {
      id: 'analytics',
      name: 'Продвинутая аналитика',
      icon: BarChart3,
      color: 'blue',
      description: 'Бизнес-аналитика и отчетность',
      permissions: ['admin.analytics.view'],
      subModules: [
        { id: 'dashboard-builder', name: 'Конструктор дашбордов', component: 'DashboardBuilder' },
        { id: 'cohort-analysis', name: 'Когортный анализ', component: 'CohortAnalysis' },
        { id: 'metrics-builder', name: 'Конструктор метрик', component: 'MetricsBuilder' },
        { id: 'ml-insights', name: 'ML прогнозы', component: 'MLInsights' }
      ]
    },
    {
      id: 'backup',
      name: 'Резервное копирование',
      icon: Database,
      color: 'gray',
      description: 'Система резервного копирования',
      permissions: ['admin.backup.view'],
      subModules: [
        { id: 'backup-manager', name: 'Управление бэкапами', component: 'BackupManager' },
        { id: 'restore-manager', name: 'Восстановление', component: 'RestoreManager' },
        { id: 'backup-integrity', name: 'Мониторинг целостности', component: 'BackupIntegrityMonitor' }
      ]
    },
    {
      id: 'system',
      name: 'Система',
      icon: Settings,
      color: 'slate',
      description: 'Системные настройки и мониторинг',
      permissions: ['admin.system.view'],
      subModules: [
        { id: 'logs', name: 'Логи системы', component: 'LogsViewer' }
      ]
    }
  ];

  // Component mapping
  const componentMap = {
    UserManagement,
    DocumentManagement,
    EnhancedRoleManagement,
    EnhancedModerationPanel,
    ModerationAnalytics,
    ModerationGamification,
    MarketingDashboard,
    PromoCodeManager,
    TrafficAnalytics,
    ABTestManager,
    ProjectDashboard,
    TaskManager,
    ProjectCalendar,
    ResourceTracker,
    NotificationCenter,
    PushNotificationSettings,
    DashboardBuilder,
    CohortAnalysis,
    MetricsBuilder,
    MLInsights,
    BackupManager,
    RestoreManager,
    BackupIntegrityMonitor,
    LogsViewer
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ctrl+K for command palette
      if (e.ctrlKey && e.key === 'k') {
        e.preventDefault();
        setCommandPaletteOpen(true);
      }
      // Ctrl+B for sidebar toggle
      if (e.ctrlKey && e.key === 'b') {
        e.preventDefault();
        setSidebarOpen(!sidebarOpen);
      }
      // Escape to close modals
      if (e.key === 'Escape') {
        setCommandPaletteOpen(false);
        setVideoGuideLibraryOpen(false);
        setHelpSystemOpen(false);
      }
      // Ctrl+Shift+H for help system
      if (e.ctrlKey && e.shiftKey && e.key === 'H') {
        e.preventDefault();
        setHelpSystemOpen(true);
      }
      // F1 for help
      if (e.key === 'F1') {
        e.preventDefault();
        setHelpSystemOpen(true);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [sidebarOpen]);

  // Filter modules based on search
  const filteredModules = modules.filter(module =>
    module.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    module.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Render main dashboard
  const renderDashboard = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner />
        </div>
      );
    }

    if (error) {
      return (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-red-400 mr-2" />
            <span className="text-red-800 dark:text-red-200">{error}</span>
          </div>
        </div>
      );
    }

    if (!currentDashboardData) return null;

    const { users, chats, system } = currentDashboardData;

    return (
      <div className="space-y-6">
        {/* Welcome Section */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold mb-2">
                Добро пожаловать в интегрированную админ-панель АДВАКОД
              </h1>
              <p className="text-blue-100">
                Управляйте всеми аспектами системы из единого интерфейса
              </p>
            </div>
            
            {/* Real-time connection status */}
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${
                isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'
              }`} />
              <span className="text-sm text-blue-100">
                {isConnected ? 'Онлайн' : 'Офлайн'}
              </span>
              {currentOnlineUsers > 0 && (
                <span className="text-sm text-blue-200">
                  • {currentOnlineUsers} пользователей онлайн
                </span>
              )}
            </div>
          </div>
          
          {/* Real-time updates indicator */}
          {dashboardLastUpdate && (
            <div className="mt-2 text-xs text-blue-200">
              Последнее обновление: {dashboardLastUpdate.toLocaleTimeString()}
            </div>
          )}
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                <Users className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Всего пользователей</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{users.total}</p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                <CheckCircle className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Активных</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{users.active}</p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                <MessageSquare className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Сообщений</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{chats.total_messages}</p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg">
                <Activity className="h-6 w-6 text-orange-600 dark:text-orange-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Сессий</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{chats.total_sessions}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Module Grid */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Модули системы
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredModules.slice(1).map((module) => (
              <ModuleCard
                key={module.id}
                module={module}
                onClick={() => setActiveModule(module.id)}
                className="cursor-pointer hover:shadow-lg transition-shadow duration-200"
              />
            ))}
          </div>
        </div>

        {/* System Status */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Статус системы
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-600 dark:text-gray-400">RAG система</span>
              <span className={`px-2 py-1 rounded-full text-xs ${
                system.rag_status?.embeddings_ready && system.rag_status?.vector_store_ready && system.rag_status?.ai_model_ready 
                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                  : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
              }`}>
                {system.rag_status?.embeddings_ready && system.rag_status?.vector_store_ready && system.rag_status?.ai_model_ready ? 'Работает' : 'Ошибка'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600 dark:text-gray-400">Векторная БД</span>
              <span className={`px-2 py-1 rounded-full text-xs ${
                system.vector_store_status?.initialized 
                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                  : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
              }`}>
                {system.vector_store_status?.initialized ? 'Работает' : 'Ошибка'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600 dark:text-gray-400">AI Модель</span>
              <span className="px-2 py-1 rounded-full text-xs bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                Готова
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Render active module content
  const renderModuleContent = () => {
    const module = modules.find(m => m.id === activeModule);
    
    if (!module) return renderDashboard();
    
    if (activeModule === 'dashboard') {
      return renderDashboard();
    }

    // Handle modules with submodules
    if (module.subModules) {
      return (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              {module.name}
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              {module.description}
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {module.subModules.map((subModule) => {
              const Component = componentMap[subModule.component];
              return (
                <div key={subModule.id} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                    {subModule.name}
                  </h3>
                  <ErrorBoundary>
                    {Component ? <Component /> : <div>Компонент не найден</div>}
                  </ErrorBoundary>
                </div>
              );
            })}
          </div>
        </div>
      );
    }

    // Handle single component modules
    const componentName = module.id === 'users' ? 'UserManagement' :
                          module.id === 'documents' ? 'DocumentManagement' :
                          module.id === 'roles' ? 'EnhancedRoleManagement' :
                          module.id === 'system' ? 'LogsViewer' : null;

    const Component = componentMap[componentName];

    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            {module.name}
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            {module.description}
          </p>
        </div>
        
        <ErrorBoundary>
          {Component ? <Component /> : <div>Компонент не найден</div>}
        </ErrorBoundary>
      </div>
    );
  };

  return (
    <SettingsProvider>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex">
        {/* Sidebar */}
        <AnimatePresence>
          {sidebarOpen && (
            <motion.div
              initial={{ x: -300 }}
              animate={{ x: 0 }}
              exit={{ x: -300 }}
              transition={{ duration: 0.3 }}
              className="fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-gray-800 shadow-lg lg:relative lg:z-0"
            >
              <div className="flex flex-col h-full">
                {/* Sidebar Header */}
                <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                    АДВАКОД Админ
                  </h2>
                  <button
                    onClick={() => setSidebarOpen(false)}
                    className="lg:hidden p-1 rounded-md text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  >
                    <X className="h-5 w-5" />
                  </button>
                </div>

                {/* Search */}
                <div className="p-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Поиск модулей..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>

                {/* Navigation */}
                <nav className="flex-1 px-4 pb-4 space-y-1 overflow-y-auto">
                  {filteredModules.map((module) => {
                    const Icon = module.icon;
                    const isActive = activeModule === module.id;
                    
                    return (
                      <motion.button
                        key={module.id}
                        onClick={() => setActiveModule(module.id)}
                        className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                          isActive
                            ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200'
                            : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                        }`}
                        whileHover={{ x: 4 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        <Icon className={`mr-3 h-5 w-5 ${
                          isActive ? 'text-blue-500' : 'text-gray-400'
                        }`} />
                        {module.name}
                        {module.subModules && (
                          <ChevronRight className="ml-auto h-4 w-4" />
                        )}
                      </motion.button>
                    );
                  })}
                </nav>

                {/* User Info */}
                <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="h-8 w-8 bg-blue-500 rounded-full flex items-center justify-center">
                        <span className="text-white text-sm font-medium">
                          {user?.email?.charAt(0).toUpperCase()}
                        </span>
                      </div>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {user?.email}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Администратор
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Content */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Top Bar */}
          <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between px-4 py-3">
              <div className="flex items-center">
                <button
                  onClick={() => setSidebarOpen(!sidebarOpen)}
                  className="p-2 rounded-md text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 lg:hidden"
                >
                  <Menu className="h-5 w-5" />
                </button>
                
                <div className="ml-4 lg:ml-0">
                  <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                    {modules.find(m => m.id === activeModule)?.name || 'Дашборд'}
                  </h1>
                </div>
              </div>

              <div className="flex items-center space-x-4">
                {/* Refresh Button */}
                <button
                  onClick={loadDashboardData}
                  disabled={loading}
                  className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 disabled:opacity-50"
                >
                  <RefreshCw className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
                </button>

                {/* Notifications */}
                <button 
                  className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 relative"
                  onClick={() => setActiveModule('notifications')}
                >
                  <Bell className="h-5 w-5" />
                  {currentNotificationCount > 0 && (
                    <span className="absolute -top-1 -right-1 h-4 w-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                      {currentNotificationCount}
                    </span>
                  )}
                </button>

                {/* System Alerts */}
                {criticalAlerts > 0 && (
                  <button 
                    className="p-2 text-red-400 hover:text-red-600 relative animate-pulse"
                    onClick={() => {
                      setActiveModule('system');
                      clearCriticalCount();
                    }}
                  >
                    <AlertTriangle className="h-5 w-5" />
                    <span className="absolute -top-1 -right-1 h-4 w-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                      {criticalAlerts}
                    </span>
                  </button>
                )}

                {/* Moderation Queue */}
                {moderationQueueSize > 0 && (
                  <button 
                    className="p-2 text-purple-400 hover:text-purple-600 relative"
                    onClick={() => setActiveModule('moderation')}
                  >
                    <MessageSquare className="h-5 w-5" />
                    <span className="absolute -top-1 -right-1 h-4 w-4 bg-purple-500 text-white text-xs rounded-full flex items-center justify-center">
                      {moderationQueueSize}
                    </span>
                  </button>
                )}

                {/* Help System */}
                <button
                  onClick={() => setHelpSystemOpen(true)}
                  className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 relative"
                  title="Справка (F1 или Ctrl+Shift+H)"
                >
                  <HelpCircle className="h-5 w-5" />
                </button>

                {/* Command Palette Trigger */}
                <button
                  onClick={() => setCommandPaletteOpen(true)}
                  className="hidden md:flex items-center px-3 py-1.5 text-sm text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  <Search className="h-4 w-4 mr-2" />
                  Поиск... <kbd className="ml-2 text-xs">Ctrl+K</kbd>
                </button>
              </div>
            </div>
          </header>

          {/* Content Area */}
          <main className="flex-1 p-6 overflow-y-auto">
            <ErrorBoundary>
              {renderModuleContent()}
            </ErrorBoundary>
          </main>
        </div>

        {/* Command Palette */}
        <CommandPalette
          isOpen={commandPaletteOpen}
          onClose={() => setCommandPaletteOpen(false)}
          modules={modules}
          onModuleSelect={(moduleId) => {
            setActiveModule(moduleId);
            setCommandPaletteOpen(false);
          }}
        />

        {/* Global Hotkey Manager */}
        <GlobalHotkeyManager />

        {/* Admin Tour Manager */}
        <AdminTourManager />

        {/* Help System */}
        <HelpSystem
          isOpen={helpSystemOpen}
          onClose={() => setHelpSystemOpen(false)}
        />

        {/* Video Guide Library */}
        <VideoGuideLibrary
          isOpen={videoGuideLibraryOpen}
          onClose={() => setVideoGuideLibraryOpen(false)}
        />

        {/* Overlay for mobile sidebar */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </div>
    </SettingsProvider>
  );
};

export default IntegratedAdminPanel;