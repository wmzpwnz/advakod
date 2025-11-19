import React, { useState, useEffect, useMemo } from 'react';
import { 
  Users, 
  Search, 
  Filter, 
  Edit, 
  Trash2, 
  Shield, 
  ShieldOff,
  Eye,
  MoreVertical,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import axios from 'axios';
import { getApiUrl } from '../config/api';
import { useAuth } from '../contexts/AuthContext';

const UserManagement = () => {
  const { token } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [roles, setRoles] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    is_active: null,
    is_premium: null,
    is_admin: null
  });
  const [pagination, setPagination] = useState({
    skip: 0,
    limit: 20,
    total: 0
  });
  const [selectedUser, setSelectedUser] = useState(null);
  const [showEditModal, setShowEditModal] = useState(false);

  useEffect(() => {
    // сперва загрузим роли (для быстрых действий), затем пользователей
    const init = async () => {
      await loadRoles();
      await loadUsers();
    };
    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    // реагируем на фильтры/поиск/страницу
    loadUsers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchTerm, filters, pagination.skip]);

  const rolesByName = useMemo(() => {
    const map = {};
    roles.forEach(r => { if (r?.name) map[r.name] = r; });
    return map;
  }, [roles]);

  const loadRoles = async () => {
    try {
      const response = await axios.get(getApiUrl('/admin/roles/'), {
        headers: token ? { 'Authorization': `Bearer ${token}` } : undefined
      });
      setRoles(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      setRoles([]);
    }
  };

  const loadUsers = async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams({
        skip: pagination.skip.toString(),
        limit: pagination.limit.toString(),
        _ts: Date.now().toString()
      });

      if (searchTerm) params.append('search', searchTerm);
      if (filters.is_active !== null) params.append('is_active', filters.is_active.toString());
      if (filters.is_premium !== null) params.append('is_premium', filters.is_premium.toString());
      if (filters.is_admin !== null) params.append('is_admin', filters.is_admin.toString());

      const response = await axios.get(`${getApiUrl('/admin/users')}?${params}`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : undefined
      });
      // Бэкенд возвращает массив пользователей
      const usersData = Array.isArray(response.data) ? response.data : (response.data?.users || []);
      const list = Array.isArray(usersData) ? usersData : [];
      setUsers(list);
      // Обновляем общее количество для пагинации (пока нет отдельного total из API)
      setPagination(prev => ({ ...prev, total: Math.max(prev.total, pagination.skip + list.length) }));
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail || err.message;
      setError(status ? `Ошибка загрузки пользователей (${status}): ${detail}` : 'Ошибка загрузки пользователей');
      console.error('Users error:', err);
      // Устанавливаем пустой массив в случае ошибки
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  const deleteUser = async (userId, username) => {
    if (!window.confirm(`Вы уверены, что хотите удалить пользователя "${username}"? Это действие нельзя отменить!`)) {
      return;
    }

    try {
      setLoading(true);
      const response = await axios.delete(`${getApiUrl('/admin/users')}/${userId}`);
      
      if (response.data.message) {
        alert(`✅ ${response.data.message}`);
        // Перезагружаем список пользователей
        await loadUsers();
      }
    } catch (err) {
      console.error('Delete user error:', err);
      const errorMessage = err.response?.data?.detail || 'Ошибка удаления пользователя';
      alert(`❌ ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const toggleUserStatus = async (userId, username, currentStatus) => {
    const action = currentStatus ? 'деактивировать' : 'активировать';
    if (!window.confirm(`Вы уверены, что хотите ${action} пользователя "${username}"?`)) {
      return;
    }

    try {
      setLoading(true);
      const response = await axios.patch(`${getApiUrl('/admin/users')}/${userId}/toggle-status`);
      
      if (response.data.message) {
        alert(`✅ ${response.data.message}`);
        // Перезагружаем список пользователей
        await loadUsers();
      }
    } catch (err) {
      console.error('Toggle user status error:', err);
      const errorMessage = err.response?.data?.detail || 'Ошибка изменения статуса пользователя';
      alert(`❌ ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
    setPagination(prev => ({ ...prev, skip: 0 }));
  };

  const handleFilterChange = (filter, value) => {
    setFilters(prev => ({ ...prev, [filter]: value }));
    setPagination(prev => ({ ...prev, skip: 0 }));
  };

  const handlePageChange = (direction) => {
    setPagination(prev => ({
      ...prev,
      skip: direction === 'next' 
        ? Math.min(prev.skip + prev.limit, prev.total - prev.limit)
        : Math.max(prev.skip - prev.limit, 0)
    }));
  };

  const toggleAdmin = async (userId) => {
    try {
      setLoading(true);
      const resp = await axios.post(getApiUrl(`/admin/users/${userId}/toggle-admin`), {}, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : undefined
      });
      // Успех — перезагружаем список и показываем уведомление
      await loadUsers();
      try { console.info('Admin status toggled for', userId, resp?.data); } catch (_) {}
    } catch (err) {
      const data = err.response?.data;
      const status = err.response?.status;
      let msg = typeof data?.detail === 'string' ? data.detail : '';
      if (!msg && data) {
        try { msg = JSON.stringify(data); } catch (_) {}
      }
      if (!msg) msg = err.message;
      if (status === 401) msg = 'Сессия истекла. Войдите в админку заново.';
      if (status === 403) msg = 'Недостаточно прав для операции.';
      if (status === 422) msg = 'Запрос отклонён валидатором. Обновите страницу и повторите.';
      setError(`Не удалось изменить статус администратора: ${msg}`);
      try { console.error('toggleAdmin error', status, data || err); } catch (_) {}
    } finally {
      setLoading(false);
    }
  };

  const grantModerator = async (userId) => {
    const role = rolesByName['moderator'];
    if (!role?.id) {
      setError('Роль moderator не найдена. Создайте её в разделе Роли.');
      return;
    }
    try {
      await axios.post(getApiUrl(`/admin/roles/users/${userId}/roles/`), {
        role_id: role.id,
        reason: 'Назначение модератора'
      }, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : undefined
      });
      await loadUsers();
    } catch (err) {
      const msg = err.response?.data?.detail || err.message;
      setError(`Не удалось назначить модератора: ${msg}`);
    }
  };

  const revokeModerator = async (userId) => {
    const role = rolesByName['moderator'];
    if (!role?.id) {
      setError('Роль moderator не найдена.');
      return;
    }
    try {
      await axios.delete(getApiUrl(`/admin/roles/users/${userId}/roles/${role.id}`), {
        headers: token ? { 'Authorization': `Bearer ${token}` } : undefined
      });
      await loadUsers();
    } catch (err) {
      const msg = err.response?.data?.detail || err.message;
      setError(`Не удалось отозвать роль модератора: ${msg}`);
    }
  };


  const getStatusBadge = (user) => {
    if (!user.is_active) {
      return <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800">Неактивен</span>;
    }
    if (user.is_admin) {
      return <span className="px-2 py-1 text-xs rounded-full bg-purple-100 text-purple-800">Админ</span>;
    }
    if (user.is_premium) {
      return <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">Премиум</span>;
    }
    return <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800">Базовый</span>;
  };

  const getSubscriptionBadge = (subscriptionType) => {
    const colors = {
      free: 'bg-gray-100 text-gray-800',
      basic: 'bg-blue-100 text-blue-800',
      premium: 'bg-green-100 text-green-800',
      enterprise: 'bg-purple-100 text-purple-800'
    };
    return (
      <span className={`px-2 py-1 text-xs rounded-full ${colors[subscriptionType] || colors.free}`}>
        {subscriptionType}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Заголовок и действия */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Управление пользователями</h2>
        <button
          onClick={loadUsers}
          className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Users className="h-4 w-4 mr-2" />
          Обновить
        </button>
      </div>

      {/* Поиск и фильтры */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Поиск */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Поиск пользователей..."
              value={searchTerm}
              onChange={handleSearch}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
            />
          </div>

          {/* Фильтр по статусу */}
          <select
            value={filters.is_active === null ? '' : filters.is_active.toString()}
            onChange={(e) => handleFilterChange('is_active', e.target.value === '' ? null : e.target.value === 'true')}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
          >
            <option value="">Все статусы</option>
            <option value="true">Активные</option>
            <option value="false">Неактивные</option>
          </select>

          {/* Фильтр по подписке */}
          <select
            value={filters.is_premium === null ? '' : filters.is_premium.toString()}
            onChange={(e) => handleFilterChange('is_premium', e.target.value === '' ? null : e.target.value === 'true')}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
          >
            <option value="">Все подписки</option>
            <option value="true">Премиум</option>
            <option value="false">Базовые</option>
          </select>

          {/* Фильтр по роли */}
          <select
            value={filters.is_admin === null ? '' : filters.is_admin.toString()}
            onChange={(e) => handleFilterChange('is_admin', e.target.value === '' ? null : e.target.value === 'true')}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
          >
            <option value="">Все роли</option>
            <option value="true">Администраторы</option>
            <option value="false">Пользователи</option>
          </select>
        </div>
      </div>

      {/* Ошибка */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <span className="text-red-800">{error}</span>
          </div>
        </div>
      )}

      {/* Таблица пользователей */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Пользователь
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Статус
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Подписка
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Дата регистрации
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Действия
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {users.map((user) => (
                    <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10">
                            <div className="h-10 w-10 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
                              <span className="text-sm font-medium text-primary-600 dark:text-primary-400">
                                {user.username?.charAt(0).toUpperCase()}
                              </span>
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900 dark:text-white">
                              {user.full_name || user.username}
                            </div>
                            <div className="text-sm text-gray-500 dark:text-gray-400">
                              {user.email}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(user)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getSubscriptionBadge(user.subscription_type)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {new Date(user.created_at).toLocaleDateString('ru-RU')}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => toggleUserStatus(user.id, user.username || user.full_name, user.is_active)}
                            className={`p-2 rounded-lg transition-colors ${
                              user.is_active
                                ? 'text-red-600 hover:bg-red-100 dark:hover:bg-red-900'
                                : 'text-green-600 hover:bg-green-100 dark:hover:bg-green-900'
                            }`}
                            title={user.is_active ? 'Деактивировать пользователя' : 'Активировать пользователя'}
                          >
                            {user.is_active ? <ShieldOff className="h-4 w-4" /> : <Shield className="h-4 w-4" />}
                          </button>
                          <button
                            onClick={() => toggleAdmin(user.id)}
                            className="p-2 text-purple-700 hover:bg-purple-100 dark:hover:bg-purple-900 rounded-lg transition-colors"
                            title={user.is_admin ? 'Снять администратора' : 'Сделать администратором'}
                          >
                            {user.is_admin ? <ShieldOff className="h-4 w-4" /> : <Shield className="h-4 w-4" />}
                          </button>
                          {rolesByName['moderator'] && (
                            <>
                              <button
                                onClick={() => grantModerator(user.id)}
                                className="p-2 text-blue-700 hover:bg-blue-100 dark:hover:bg-blue-900 rounded-lg transition-colors"
                                title="Назначить модератора"
                              >
                                <Shield className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() => revokeModerator(user.id)}
                                className="p-2 text-blue-700 hover:bg-blue-100 dark:hover:bg-blue-900 rounded-lg transition-colors"
                                title="Отозвать модератора"
                              >
                                <ShieldOff className="h-4 w-4" />
                              </button>
                            </>
                          )}
                          <button
                            onClick={() => setSelectedUser(user)}
                            className="p-2 text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                            title="Просмотр профиля"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => deleteUser(user.id, user.username || user.full_name)}
                            className="p-2 text-red-600 hover:bg-red-100 dark:hover:bg-red-900 rounded-lg transition-colors"
                            title="Удалить пользователя"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Пагинация */}
            <div className="bg-white dark:bg-gray-800 px-4 py-3 flex items-center justify-between border-t border-gray-200 dark:border-gray-700 sm:px-6">
              <div className="flex-1 flex justify-between sm:hidden">
                <button
                  onClick={() => handlePageChange('prev')}
                  disabled={pagination.skip === 0}
                  className="relative inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Предыдущая
                </button>
                <button
                  onClick={() => handlePageChange('next')}
                  disabled={pagination.skip + pagination.limit >= pagination.total}
                  className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Следующая
                </button>
              </div>
              <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm text-gray-700 dark:text-gray-300">
                    Показано <span className="font-medium">{pagination.skip + 1}</span> - <span className="font-medium">
                      {Math.min(pagination.skip + pagination.limit, pagination.total)}
                    </span> из <span className="font-medium">{pagination.total}</span> результатов
                  </p>
                </div>
                <div>
                  <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                    <button
                      onClick={() => handlePageChange('prev')}
                      disabled={pagination.skip === 0}
                      className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm font-medium text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <ChevronLeft className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => handlePageChange('next')}
                      disabled={pagination.skip + pagination.limit >= pagination.total}
                      className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm font-medium text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <ChevronRight className="h-5 w-5" />
                    </button>
                  </nav>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default UserManagement;
