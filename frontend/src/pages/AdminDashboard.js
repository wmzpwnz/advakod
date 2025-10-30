import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import CanaryManagement from '../components/CanaryManagement';
import LoRAManagement from '../components/LoRAManagement';

const AdminDashboard = () => {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [securityEvents, setSecurityEvents] = useState([]);
  const [systemHealth, setSystemHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCanaryManagement, setShowCanaryManagement] = useState(false);
  const [showLoRAManagement, setShowLoRAManagement] = useState(false);

  // Проверяем права администратора
  useEffect(() => {
    if (!user || !user.is_admin) {
      navigate('/');
      return;
    }
    loadDashboardData();
  }, [user, navigate, loadDashboardData]);

  const loadDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      // Загружаем статистику
      const statsResponse = await fetch('/api/v1/admin/dashboard', { headers });
      if (statsResponse.status === 401 || statsResponse.status === 403) {
        setError('Сессия администратора истекла или нет прав. Войдите заново через Админ.');
        setStats(null);
        setUsers([]);
        return;
      }
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData);
      }

      // Загружаем состояние системы
      const healthResponse = await fetch('/api/v1/monitoring/health', { headers });
      if (healthResponse.ok) {
        const healthData = await healthResponse.json();
        setSystemHealth(healthData);
      }

      // Загружаем пользователей
      const usersResponse = await fetch('/api/v1/admin/users?limit=10&_ts=' + Date.now(), { headers });
      if (usersResponse.ok) {
        const usersData = await usersResponse.json();
        setUsers(Array.isArray(usersData?.users) ? usersData.users : (Array.isArray(usersData) ? usersData : []));
      }

      // Загружаем логи аудита
      const auditResponse = await fetch('/api/v1/admin/audit-logs?limit=20', { headers });
      if (auditResponse.ok) {
        const auditData = await auditResponse.json();
        setAuditLogs(auditData.logs);
      }

      // Загружаем события безопасности
      const securityResponse = await fetch('/api/v1/admin/security-events?limit=10', { headers });
      if (securityResponse.ok) {
        const securityData = await securityResponse.json();
        setSecurityEvents(securityData.events);
      }

    } catch (err) {
      setError(`Ошибка загрузки данных: ${err.message}`);
      console.error('Admin dashboard error:', err);
    } finally {
      setLoading(false);
    }
  }, [token]);

  const toggleUserStatus = async (userId, currentStatus) => {
    try {
      const response = await fetch(`/api/v1/admin/users/${userId}/toggle-status`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        // Обновляем локальное состояние
        setUsers(users.map(user => 
          user.id === userId 
            ? { ...user, is_active: !currentStatus }
            : user
        ));
        // Перезагружаем статистику
        loadDashboardData();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Ошибка изменения статуса пользователя');
      }
    } catch (err) {
      setError('Ошибка изменения статуса пользователя');
      console.error('Toggle user status error:', err);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('ru-RU');
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return 'text-red-500';
      case 'medium': return 'text-yellow-500';
      case 'low': return 'text-green-500';
      default: return 'text-gray-500';
    }
  };

  const getThreatLevelColor = (level) => {
    switch (level) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Загрузка админ-панели...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-white">🛡️ Админ-панель АДВАКОД</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-300">Добро пожаловать, {user?.email}</span>
              <button
                onClick={() => navigate('/')}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors"
              >
                Выйти
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {[
              { id: 'dashboard', name: '📊 Дашборд', icon: '📊' },
              { id: 'users', name: '👥 Пользователи', icon: '👥' },
              { id: 'roles', name: '🔐 Роли', icon: '🔐' },
              { id: 'audit', name: '📋 Аудит', icon: '📋' },
              { id: 'security', name: '🔒 Безопасность', icon: '🔒' },
              { id: 'system', name: '⚙️ Система', icon: '⚙️' },
              { id: 'canary', name: '🚀 Canary', icon: '🚀' },
              { id: 'lora', name: '🧠 LoRA', icon: '🧠' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-red-500 text-red-400'
                    : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                }`}
              >
                {tab.name}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
            <button
              onClick={() => setError('')}
              className="float-right text-red-700 hover:text-red-900"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && stats && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                <div className="flex items-center">
                  <div className="p-2 bg-blue-500 rounded-lg">
                    <span className="text-white text-xl">👥</span>
                  </div>
                  <div className="ml-4">
                    <p className="text-gray-400 text-sm">Всего пользователей</p>
                    <p className="text-white text-2xl font-bold">{stats.users.total}</p>
                    <p className="text-green-400 text-sm">+{stats.users.new_24h} за 24ч</p>
                  </div>
                </div>
              </div>

              <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                <div className="flex items-center">
                  <div className="p-2 bg-green-500 rounded-lg">
                    <span className="text-white text-xl">💬</span>
                  </div>
                  <div className="ml-4">
                    <p className="text-gray-400 text-sm">Всего сообщений</p>
                    <p className="text-white text-2xl font-bold">{stats.chats.total_messages}</p>
                    <p className="text-green-400 text-sm">+{stats.chats.new_messages_24h} за 24ч</p>
                  </div>
                </div>
              </div>

              <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                <div className="flex items-center">
                  <div className="p-2 bg-yellow-500 rounded-lg">
                    <span className="text-white text-xl">⭐</span>
                  </div>
                  <div className="ml-4">
                    <p className="text-gray-400 text-sm">Премиум пользователи</p>
                    <p className="text-white text-2xl font-bold">{stats.users.premium}</p>
                    <p className="text-gray-400 text-sm">{Math.round((stats.users.premium / stats.users.total) * 100)}% от общего</p>
                  </div>
                </div>
              </div>

              <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                <div className="flex items-center">
                  <div className="p-2 bg-red-500 rounded-lg">
                    <span className="text-white text-xl">🔒</span>
                  </div>
                  <div className="ml-4">
                    <p className="text-gray-400 text-sm">События безопасности</p>
                    <p className="text-white text-2xl font-bold">{stats.security.events_24h}</p>
                    <p className="text-gray-400 text-sm">за 24 часа</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Top Users */}
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">🏆 Топ активных пользователей</h3>
              <div className="space-y-3">
                {stats.top_users.map((user, index) => (
                  <div key={user.id} className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                    <div className="flex items-center">
                      <span className="text-gray-400 mr-3">#{index + 1}</span>
                      <div>
                        <p className="text-white font-medium">{user.username || user.email}</p>
                        <p className="text-gray-400 text-sm">{user.email}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {user.is_premium && (
                        <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded">Premium</span>
                      )}
                      <span className="text-gray-400 text-sm">{formatDate(user.created_at)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Users Tab */}
        {activeTab === 'users' && (
          <div className="space-y-6">
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">👥 Управление пользователями</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead>
                    <tr className="border-b border-gray-700">
                      <th className="text-left text-gray-400 py-3">ID</th>
                      <th className="text-left text-gray-400 py-3">Email</th>
                      <th className="text-left text-gray-400 py-3">Имя</th>
                      <th className="text-left text-gray-400 py-3">Статус</th>
                      <th className="text-left text-gray-400 py-3">Premium</th>
                      <th className="text-left text-gray-400 py-3">Создан</th>
                      <th className="text-left text-gray-400 py-3">Действия</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((user) => (
                      <tr key={user.id} className="border-b border-gray-700">
                        <td className="text-white py-3">{user.id}</td>
                        <td className="text-white py-3">{user.email}</td>
                        <td className="text-white py-3">{user.full_name || '-'}</td>
                        <td className="py-3">
                          <span className={`px-2 py-1 rounded text-xs ${
                            user.is_active 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {user.is_active ? 'Активен' : 'Заблокирован'}
                          </span>
                        </td>
                        <td className="py-3">
                          {user.is_premium && (
                            <span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs">
                              Premium
                            </span>
                          )}
                        </td>
                        <td className="text-gray-400 py-3 text-sm">{formatDate(user.created_at)}</td>
                        <td className="py-3">
                          <button
                            onClick={() => toggleUserStatus(user.id, user.is_active)}
                            className={`px-3 py-1 rounded text-xs transition-colors ${
                              user.is_active
                                ? 'bg-red-600 hover:bg-red-700 text-white'
                                : 'bg-green-600 hover:bg-green-700 text-white'
                            }`}
                          >
                            {user.is_active ? 'Заблокировать' : 'Активировать'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Roles Tab */}
        {activeTab === 'roles' && (
          <div className="space-y-6">
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-white">🔐 Управление ролями и правами</h3>
                <button
                  onClick={() => navigate('/role-management')}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors flex items-center"
                >
                  <span className="mr-2">🔧</span>
                  Расширенное управление
                </button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="bg-gray-700 p-4 rounded-lg border border-gray-600">
                  <div className="flex items-center mb-2">
                    <span className="text-red-400 text-xl mr-2">👑</span>
                    <h4 className="text-white font-medium">Супер-админ</h4>
                  </div>
                  <p className="text-gray-400 text-sm mb-3">Полный доступ ко всем функциям системы</p>
                  <div className="flex flex-wrap gap-1">
                    <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded">Все права</span>
                  </div>
                </div>

                <div className="bg-gray-700 p-4 rounded-lg border border-gray-600">
                  <div className="flex items-center mb-2">
                    <span className="text-purple-400 text-xl mr-2">🛡️</span>
                    <h4 className="text-white font-medium">Администратор</h4>
                  </div>
                  <p className="text-gray-400 text-sm mb-3">Управление пользователями и контентом</p>
                  <div className="flex flex-wrap gap-1">
                    <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">Пользователи</span>
                    <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">Документы</span>
                    <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded">Чаты</span>
                  </div>
                </div>

                <div className="bg-gray-700 p-4 rounded-lg border border-gray-600">
                  <div className="flex items-center mb-2">
                    <span className="text-blue-400 text-xl mr-2">👮</span>
                    <h4 className="text-white font-medium">Модератор</h4>
                  </div>
                  <p className="text-gray-400 text-sm mb-3">Модерация контента и пользователей</p>
                  <div className="flex flex-wrap gap-1">
                    <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">Модерация</span>
                    <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">Документы</span>
                  </div>
                </div>

                <div className="bg-gray-700 p-4 rounded-lg border border-gray-600">
                  <div className="flex items-center mb-2">
                    <span className="text-green-400 text-xl mr-2">📄</span>
                    <h4 className="text-white font-medium">Контент-менеджер</h4>
                  </div>
                  <p className="text-gray-400 text-sm mb-3">Управление документами и контентом</p>
                  <div className="flex flex-wrap gap-1">
                    <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">Документы</span>
                    <span className="bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded">Аналитика</span>
                  </div>
                </div>

                <div className="bg-gray-700 p-4 rounded-lg border border-gray-600">
                  <div className="flex items-center mb-2">
                    <span className="text-yellow-400 text-xl mr-2">🎧</span>
                    <h4 className="text-white font-medium">Поддержка</h4>
                  </div>
                  <p className="text-gray-400 text-sm mb-3">Просмотр пользователей и чатов</p>
                  <div className="flex flex-wrap gap-1">
                    <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">Пользователи</span>
                    <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded">Чаты</span>
                    <span className="bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded">Логи</span>
                  </div>
                </div>

                <div className="bg-gray-700 p-4 rounded-lg border border-gray-600">
                  <div className="flex items-center mb-2">
                    <span className="text-indigo-400 text-xl mr-2">📊</span>
                    <h4 className="text-white font-medium">Аналитик</h4>
                  </div>
                  <p className="text-gray-400 text-sm mb-3">Просмотр аналитики и отчетов</p>
                  <div className="flex flex-wrap gap-1">
                    <span className="bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded">Аналитика</span>
                    <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">Экспорт</span>
                  </div>
                </div>
              </div>

              <div className="mt-6 p-4 bg-gray-700 rounded-lg border border-gray-600">
                <h4 className="text-white font-medium mb-2">🛡️ Защита суперадмина</h4>
                <p className="text-gray-400 text-sm mb-3">
                  Ваш аккаунт защищен специальными мерами безопасности:
                </p>
                <ul className="text-gray-400 text-sm space-y-1">
                  <li>• Резервные коды доступа</li>
                  <li>• Экстренный токен восстановления</li>
                  <li>• Защита от отзыва роли super_admin</li>
                  <li>• Дополнительные проверки безопасности</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Audit Tab */}
        {activeTab === 'audit' && (
          <div className="space-y-6">
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">📋 Логи аудита</h3>
              <div className="space-y-3">
                {auditLogs.map((log) => (
                  <div key={log.id} className="p-4 bg-gray-700 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <span className={`px-2 py-1 rounded text-xs ${getSeverityColor(log.severity)}`}>
                          {log.severity}
                        </span>
                        <span className="text-white font-medium">{log.action}</span>
                        <span className="text-gray-400">{log.description}</span>
                      </div>
                      <span className="text-gray-400 text-sm">{formatDate(log.created_at)}</span>
                    </div>
                    {log.ip_address && (
                      <div className="mt-2 text-sm text-gray-400">
                        IP: {log.ip_address} | User ID: {log.user_id || 'N/A'}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Security Tab */}
        {activeTab === 'security' && (
          <div className="space-y-6">
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">🔒 События безопасности</h3>
              <div className="space-y-3">
                {securityEvents.map((event) => (
                  <div key={event.id} className="p-4 bg-gray-700 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <span className={`px-2 py-1 rounded text-xs ${getThreatLevelColor(event.threat_level)}`}>
                          {event.threat_level}
                        </span>
                        <span className="text-white font-medium">{event.event_type}</span>
                        <span className="text-gray-400">{event.description}</span>
                      </div>
                      <span className="text-gray-400 text-sm">{formatDate(event.created_at)}</span>
                    </div>
                    {event.ip_address && (
                      <div className="mt-2 text-sm text-gray-400">
                        IP: {event.ip_address} | User ID: {event.user_id || 'N/A'} | Status: {event.status}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* System Tab */}
        {activeTab === 'system' && systemHealth && (
          <div className="space-y-6">
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
              <h3 className="text-lg font-semibold text-white mb-4">⚙️ Состояние системы</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-white font-medium mb-3">🤖 AI Модели</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400">Saiga Mistral 7B</span>
                      <span className={`px-2 py-1 rounded text-xs ${
                        systemHealth.ai_models.saiga_ready 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {systemHealth.ai_models.saiga_ready ? 'Готов' : 'Загружается'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400">Embeddings</span>
                      <span className={`px-2 py-1 rounded text-xs ${
                        systemHealth.ai_models.embeddings_ready 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {systemHealth.ai_models.embeddings_ready ? 'Готов' : 'Загружается'}
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="text-white font-medium mb-3">🗄️ Векторная БД</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400">ChromaDB</span>
                      <span className={`px-2 py-1 rounded text-xs ${
                        systemHealth.vector_store.ready 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {systemHealth.vector_store.ready ? 'Готов' : 'Не готов'}
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="text-white font-medium mb-3">🧠 RAG Система</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400">Общий статус</span>
                      <span className={`px-2 py-1 rounded text-xs ${
                        systemHealth.rag_system.ready 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {systemHealth.rag_system.ready ? 'Готов' : 'Не готов'}
                      </span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="text-white font-medium mb-3">💾 База данных</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400">SQLite</span>
                      <span className="px-2 py-1 rounded text-xs bg-green-100 text-green-800">
                        Подключена
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Canary Tab */}
        {activeTab === 'canary' && (
          <div className="space-y-6">
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
              <h2 className="text-xl font-bold text-white mb-4">🚀 Управление Canary-релизами</h2>
              <p className="text-gray-400 mb-6">
                Безопасное тестирование новых версий моделей с автоматическим откатом при деградации метрик.
              </p>
              <button
                onClick={() => setShowCanaryManagement(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Открыть Canary Management
              </button>
            </div>
          </div>
        )}

        {/* LoRA Tab */}
        {activeTab === 'lora' && (
          <div className="space-y-6">
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
              <h2 className="text-xl font-bold text-white mb-4">🧠 Управление LoRA обучением</h2>
              <p className="text-gray-400 mb-6">
                Управление обучением LoRA с интеграцией метрик качества и приоритизацией примеров.
              </p>
              <button
                onClick={() => setShowLoRAManagement(true)}
                className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors"
              >
                Открыть LoRA Management
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      <CanaryManagement
        isVisible={showCanaryManagement}
        onClose={() => setShowCanaryManagement(false)}
      />

      <LoRAManagement
        isVisible={showLoRAManagement}
        onClose={() => setShowLoRAManagement(false)}
      />
    </div>
  );
};

export default AdminDashboard;
