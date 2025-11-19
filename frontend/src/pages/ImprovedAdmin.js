import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { 
  Users, 
  MessageSquare, 
  Database, 
  Brain, 
  Settings, 
  BarChart3, 
  Play, 
  Pause, 
  CheckCircle, 
  AlertCircle,
  RefreshCw,
  TrendingUp,
  Activity
} from 'lucide-react';

const ImprovedAdmin = () => {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState({});
  const [systemStatus, setSystemStatus] = useState({});
  const [loraStatus, setLoraStatus] = useState({});
  const [ragStatus, setRagStatus] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!user || !user.is_admin) {
      navigate('/admin-login');
      return;
    }
    loadAllData();
  }, [user, navigate]);

  const loadAllData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        loadDashboardStats(),
        loadSystemStatus(),
        loadLoraStatus(),
        loadRagStatus()
      ]);
    } catch (err) {
      setError('Ошибка загрузки данных');
      console.error('Ошибка загрузки:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadDashboardStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/admin/dashboard', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setStats(data);
    } catch (err) {
      console.error('Ошибка загрузки статистики:', err);
    }
  };

  const loadSystemStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/system/status', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setSystemStatus(data);
    } catch (err) {
      console.error('Ошибка загрузки статуса системы:', err);
    }
  };

  const loadLoraStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/lora/status', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setLoraStatus(data);
    } catch (err) {
      console.error('Ошибка загрузки статуса LoRA:', err);
    }
  };

  const loadRagStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/rag/status', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setRagStatus(data);
    } catch (err) {
      console.error('Ошибка загрузки статуса RAG:', err);
    }
  };

  const initializeRag = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/rag/initialize', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      alert(data.message);
      loadRagStatus();
    } catch (err) {
      alert('Ошибка инициализации RAG');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'online':
      case 'ready':
      case 'connected':
        return 'text-green-600 bg-green-100';
      case 'initializing':
        return 'text-yellow-600 bg-yellow-100';
      case 'error':
      case 'offline':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'online':
      case 'ready':
      case 'connected':
        return <CheckCircle className="w-4 h-4" />;
      case 'initializing':
        return <RefreshCw className="w-4 h-4 animate-spin" />;
      case 'error':
      case 'offline':
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <Activity className="w-4 h-4" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">Загрузка админ панели...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Заголовок */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <h1 className="text-3xl font-bold text-gray-900">🛡️ Админ панель АДВАКОД</h1>
            <p className="mt-2 text-gray-600">Управление системой ИИ-юриста</p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Навигация */}
        <div className="mb-8">
          <nav className="flex space-x-8">
            {[
              { id: 'dashboard', name: 'Дашборд', icon: BarChart3 },
              { id: 'users', name: 'Пользователи', icon: Users },
              { id: 'chat', name: 'Чат', icon: MessageSquare },
              { id: 'rag', name: 'RAG', icon: Database },
              { id: 'lora', name: 'LoRA', icon: Brain },
              { id: 'system', name: 'Система', icon: Settings }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium ${
                  activeTab === tab.id
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                <span>{tab.name}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Дашборд */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* Статистика */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <Users className="w-8 h-8 text-blue-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Пользователи</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {stats.users?.total || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <MessageSquare className="w-8 h-8 text-green-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Сессии чата</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {stats.chats?.total_sessions || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <Database className="w-8 h-8 text-purple-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">RAG статус</p>
                    <p className="text-sm font-semibold text-gray-900">
                      {ragStatus.status || 'Неизвестно'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <Brain className="w-8 h-8 text-orange-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">LoRA статус</p>
                    <p className="text-sm font-semibold text-gray-900">
                      {loraStatus.status || 'Неизвестно'}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Статус системы */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Статус системы</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium text-gray-700">Backend</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(systemStatus.backend?.status)}`}>
                    {systemStatus.backend?.status || 'Неизвестно'}
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium text-gray-700">База данных</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(systemStatus.database?.status)}`}>
                    {systemStatus.database?.status || 'Неизвестно'}
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium text-gray-700">Saiga AI</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(systemStatus.ai_services?.saiga)}`}>
                    {systemStatus.ai_services?.saiga || 'Неизвестно'}
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium text-gray-700">RAG</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(systemStatus.ai_services?.rag)}`}>
                    {systemStatus.ai_services?.rag || 'Неизвестно'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* RAG Система */}
        {activeTab === 'rag' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">RAG Система</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-md font-medium text-gray-700 mb-2">Статус</h4>
                  <p className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(ragStatus.status)}`}>
                    {getStatusIcon(ragStatus.status)}
                    <span className="ml-2">{ragStatus.status || 'Неизвестно'}</span>
                  </p>
                </div>
                <div>
                  <h4 className="text-md font-medium text-gray-700 mb-2">Эмбеддинги</h4>
                  <p className="text-sm text-gray-600">
                    {ragStatus.embeddings?.loaded ? 'Загружены' : 'Не загружены'}
                  </p>
                </div>
                <div>
                  <h4 className="text-md font-medium text-gray-700 mb-2">Векторное хранилище</h4>
                  <p className="text-sm text-gray-600">
                    Документов: {ragStatus.vector_store?.documents || 0}
                  </p>
                </div>
                <div>
                  <h4 className="text-md font-medium text-gray-700 mb-2">AI Модель</h4>
                  <p className="text-sm text-gray-600">
                    {ragStatus.ai_model?.model || 'Неизвестно'}
                  </p>
                </div>
              </div>
              <div className="mt-6">
                <button
                  onClick={initializeRag}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <Play className="w-4 h-4" />
                  <span>Инициализировать RAG</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* LoRA Система */}
        {activeTab === 'lora' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">LoRA Система</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-md font-medium text-gray-700 mb-2">Статус</h4>
                  <p className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(loraStatus.status)}`}>
                    {getStatusIcon(loraStatus.status)}
                    <span className="ml-2">{loraStatus.status || 'Неизвестно'}</span>
                  </p>
                </div>
                <div>
                  <h4 className="text-md font-medium text-gray-700 mb-2">Данные для обучения</h4>
                  <p className="text-sm text-gray-600">
                    Всего: {loraStatus.training_data?.total || 0} | 
                    Одобрено: {loraStatus.training_data?.approved || 0} | 
                    Ожидает: {loraStatus.training_data?.pending || 0}
                  </p>
                </div>
                <div>
                  <h4 className="text-md font-medium text-gray-700 mb-2">Модели</h4>
                  <p className="text-sm text-gray-600">
                    Доступно: {loraStatus.models?.available?.length || 0} | 
                    Активная: {loraStatus.models?.active || 'Нет'}
                  </p>
                </div>
                <div>
                  <h4 className="text-md font-medium text-gray-700 mb-2">Обучение</h4>
                  <p className="text-sm text-gray-600">
                    Активных задач: {loraStatus.training?.active_jobs || 0}
                  </p>
                </div>
              </div>
              <div className="mt-6">
                <button
                  onClick={() => navigate('/lora-training')}
                  className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                  <Brain className="w-4 h-4" />
                  <span>Управление LoRA</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Система */}
        {activeTab === 'system' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Мониторинг системы</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium text-gray-700">Версия Backend</span>
                  <span className="text-sm text-gray-600">{systemStatus.backend?.version || 'Неизвестно'}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium text-gray-700">Пользователей в БД</span>
                  <span className="text-sm text-gray-600">{systemStatus.database?.users || 0}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm font-medium text-gray-700">Последнее обновление</span>
                  <span className="text-sm text-gray-600">
                    {systemStatus.timestamp ? new Date(systemStatus.timestamp).toLocaleString() : 'Неизвестно'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ImprovedAdmin;
