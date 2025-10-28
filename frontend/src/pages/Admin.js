import React, { useState, useEffect } from 'react';
import { 
  Users, 
  FileText, 
  BarChart3, 
  Shield, 
  Settings, 
  Brain,
  Upload,
  Search,
  Download,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Clock
} from 'lucide-react';
import axios from 'axios';
import { getApiUrl } from '../config/api';
import UserManagement from '../components/UserManagement';
import DocumentManagement from '../components/DocumentManagement';
import LogsViewer from '../components/LogsViewer';
import LoRAManagement from './LoRAManagement';

const Admin = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (activeTab === 'dashboard') {
      loadDashboardData();
    }
  }, [activeTab]);

  const loadDashboardData = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await axios.get(getApiUrl('/admin/dashboard'));
      setDashboardData(response.data);
    } catch (err) {
      setError('Ошибка загрузки данных дашборда');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'dashboard', name: 'Дашборд', icon: BarChart3 },
    { id: 'users', name: 'Пользователи', icon: Users },
    { id: 'documents', name: 'Документы', icon: FileText },
    { id: 'lora', name: 'LoRA', icon: Brain },
    { id: 'logs', name: 'Логи', icon: Shield },
    { id: 'settings', name: 'Настройки', icon: Settings }
  ];

  const renderDashboard = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-400 mr-2" />
            <span className="text-red-800">{error}</span>
          </div>
        </div>
      );
    }

    if (!dashboardData) return null;

    const { users, chats, system } = dashboardData;

    return (
      <div className="space-y-6">
        {/* Статистические карточки */}
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
                <FileText className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Сессий чата</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{chats.total_sessions}</p>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg">
                <BarChart3 className="h-6 w-6 text-orange-600 dark:text-orange-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Сообщений</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{chats.total_messages}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Дополнительная статистика */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Пользователи</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Премиум пользователи</span>
                <span className="font-medium">{users.premium}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Новых за 30 дней</span>
                <span className="font-medium">{users.new_last_30d}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Администраторы</span>
                <span className="font-medium">{users.admins}</span>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Статус системы</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">RAG система</span>
                <span className={`px-2 py-1 rounded-full text-xs ${
                  system.rag_status?.embeddings_ready && system.rag_status?.vector_store_ready && system.rag_status?.ai_model_ready ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {system.rag_status?.embeddings_ready && system.rag_status?.vector_store_ready && system.rag_status?.ai_model_ready ? 'Работает' : 'Ошибка'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600 dark:text-gray-400">Векторная БД</span>
                <span className={`px-2 py-1 rounded-full text-xs ${
                  system.vector_store_status?.initialized ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {system.vector_store_status?.initialized ? 'Работает' : 'Ошибка'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Быстрые действия */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Быстрые действия</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => setActiveTab('users')}
              className="flex items-center p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <Users className="h-5 w-5 text-gray-400 mr-3" />
              <span>Управление пользователями</span>
            </button>
            <button
              onClick={() => setActiveTab('documents')}
              className="flex items-center p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <Upload className="h-5 w-5 text-gray-400 mr-3" />
              <span>Загрузить документы</span>
            </button>
            <button
              onClick={() => setActiveTab('logs')}
              className="flex items-center p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <Shield className="h-5 w-5 text-gray-400 mr-3" />
              <span>Просмотр логов</span>
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderUsers = () => <UserManagement />;

  const renderDocuments = () => <DocumentManagement />;

  const renderLoRA = () => <LoRAManagement />;

  const renderLogs = () => <LogsViewer />;

  const renderSettings = () => (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Настройки системы</h3>
      <p className="text-gray-600 dark:text-gray-400">Функция в разработке...</p>
    </div>
  );

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return renderDashboard();
      case 'users':
        return renderUsers();
      case 'documents':
        return renderDocuments();
      case 'lora':
        return renderLoRA();
      case 'logs':
        return renderLogs();
      case 'settings':
        return renderSettings();
      default:
        return renderDashboard();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Заголовок */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Админ панель</h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Управление системой ИИ-Юрист
          </p>
        </div>

        {/* Навигация */}
        <div className="mb-8">
          <nav className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center px-1 py-2 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-4 w-4 mr-2" />
                  {tab.name}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Контент */}
        {renderContent()}
      </div>
    </div>
  );
};

export default Admin;
