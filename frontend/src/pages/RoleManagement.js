import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Users, 
  Key, 
  Plus, 
  Edit, 
  Trash2, 
  Eye, 
  UserCheck,
  XCircle
} from 'lucide-react';

const RoleManagement = () => {
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('roles');
  
  // Состояния для модальных окон
  const [showCreateRole, setShowCreateRole] = useState(false);
  const [showAssignRole, setShowAssignRole] = useState(false);

  // Формы
  const [newRole, setNewRole] = useState({
    name: '',
    display_name: '',
    description: ''
  });
  const [roleAssignment, setRoleAssignment] = useState({
    user_id: '',
    role_id: '',
    reason: ''
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [rolesRes, permissionsRes, usersRes] = await Promise.all([
        fetch('/api/v1/admin/roles/', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        fetch('/api/v1/admin/roles/permissions/', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        fetch('/api/v1/admin/users?limit=100', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        })
      ]);

      if (rolesRes.ok) {
        const rolesData = await rolesRes.json();
        setRoles(rolesData);
      }

      if (permissionsRes.ok) {
        const permissionsData = await permissionsRes.json();
        setPermissions(permissionsData);
      }

      if (usersRes.ok) {
        const usersData = await usersRes.json();
        setUsers(usersData.users || []);
      }

    } catch (err) {
      setError('Ошибка загрузки данных');
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  const createRole = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/v1/admin/roles/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(newRole)
      });

      if (response.ok) {
        setShowCreateRole(false);
        setNewRole({ name: '', display_name: '', description: '' });
        loadData();
      } else {
        const error = await response.json();
        setError(error.detail || 'Ошибка создания роли');
      }
    } catch (err) {
      setError('Ошибка создания роли');
    }
  };

  const assignRole = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`/api/v1/admin/roles/users/${roleAssignment.user_id}/roles/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          role_id: parseInt(roleAssignment.role_id),
          reason: roleAssignment.reason
        })
      });

      if (response.ok) {
        setShowAssignRole(false);
        setRoleAssignment({ user_id: '', role_id: '', reason: '' });
        loadData();
      } else {
        const error = await response.json();
        setError(error.detail || 'Ошибка назначения роли');
      }
    } catch (err) {
      setError('Ошибка назначения роли');
    }
  };

  const revokeRole = async (userId, roleId) => {
    if (!window.confirm('Вы уверены, что хотите отозвать роль?')) return;

    try {
      const response = await fetch(`/api/v1/admin/roles/users/${userId}/roles/${roleId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        loadData();
      } else {
        const error = await response.json();
        setError(error.detail || 'Ошибка отзыва роли');
      }
    } catch (err) {
      setError('Ошибка отзыва роли');
    }
  };

  const deleteRole = async (roleId) => {
    if (!window.confirm('Вы уверены, что хотите удалить роль? Это действие необратимо.')) return;

    try {
      const response = await fetch(`/api/v1/admin/roles/${roleId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        loadData();
      } else {
        const error = await response.json();
        setError(error.detail || 'Ошибка удаления роли');
      }
    } catch (err) {
      setError('Ошибка удаления роли');
    }
  };

  const getRoleColor = (roleName) => {
    const colors = {
      'super_admin': 'bg-red-100 text-red-800 border-red-200',
      'admin': 'bg-purple-100 text-purple-800 border-purple-200',
      'moderator': 'bg-blue-100 text-blue-800 border-blue-200',
      'content_manager': 'bg-green-100 text-green-800 border-green-200',
      'support': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'analyst': 'bg-indigo-100 text-indigo-800 border-indigo-200'
    };
    return colors[roleName] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Загрузка системы ролей...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                <Shield className="h-8 w-8 text-blue-600 mr-3" />
                Управление ролями и правами
              </h1>
              <p className="mt-2 text-gray-600">
                Управление системой ролей, правами доступа и назначением ролей пользователям
              </p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => setShowCreateRole(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center"
              >
                <Plus className="h-4 w-4 mr-2" />
                Создать роль
              </button>
              <button
                onClick={() => setShowAssignRole(true)}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 flex items-center"
              >
                <UserCheck className="h-4 w-4 mr-2" />
                Назначить роль
              </button>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex">
              <XCircle className="h-5 w-5 text-red-400 mr-3" />
              <div>
                <h3 className="text-sm font-medium text-red-800">Ошибка</h3>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {[
                { id: 'roles', name: 'Роли', icon: Shield },
                { id: 'permissions', name: 'Права доступа', icon: Key },
                { id: 'users', name: 'Пользователи', icon: Users }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center`}
                >
                  <tab.icon className="h-4 w-4 mr-2" />
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Roles Tab */}
        {activeTab === 'roles' && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Системные роли</h3>
              <p className="text-sm text-gray-600">Управление ролями и их правами доступа</p>
            </div>
            <div className="divide-y divide-gray-200">
              {roles.map((role) => (
                <div key={role.id} className="px-6 py-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getRoleColor(role.name)}`}>
                          {role.display_name}
                        </span>
                        {role.is_system && (
                          <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            Системная
                          </span>
                        )}
                        {!role.is_active && (
                          <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            Неактивна
                          </span>
                        )}
                      </div>
                      <p className="mt-1 text-sm text-gray-600">{role.description}</p>
                      <p className="text-xs text-gray-500">ID: {role.id} | Имя: {role.name}</p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        className="text-blue-600 hover:text-blue-800 p-1"
                        title="Просмотр прав"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      {!role.is_system && (
                        <>
                          <button
                            className="text-yellow-600 hover:text-yellow-800 p-1"
                            title="Редактировать"
                          >
                            <Edit className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => deleteRole(role.id)}
                            className="text-red-600 hover:text-red-800 p-1"
                            title="Удалить"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Permissions Tab */}
        {activeTab === 'permissions' && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Права доступа</h3>
              <p className="text-sm text-gray-600">Все доступные права в системе</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-6">
              {permissions.map((permission) => (
                <div key={permission.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="text-sm font-medium text-gray-900">{permission.display_name}</h4>
                      <p className="text-xs text-gray-500 mt-1">{permission.name}</p>
                      <p className="text-xs text-gray-600 mt-2">{permission.description}</p>
                      <div className="mt-2 flex items-center space-x-2">
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {permission.resource}
                        </span>
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          {permission.action}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Users Tab */}
        {activeTab === 'users' && (
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Пользователи и их роли</h3>
              <p className="text-sm text-gray-600">Управление ролями пользователей</p>
            </div>
            <div className="divide-y divide-gray-200">
              {users.map((user) => (
                <div key={user.id} className="px-6 py-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                            <span className="text-sm font-medium text-gray-700">
                              {user.full_name ? user.full_name.charAt(0).toUpperCase() : user.email.charAt(0).toUpperCase()}
                            </span>
                          </div>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                            {user.full_name || user.username || 'Без имени'}
                          </div>
                          <div className="text-sm text-gray-500">{user.email}</div>
                          <div className="flex items-center space-x-2 mt-1">
                            {user.is_admin && (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                Админ
                              </span>
                            )}
                            {user.is_premium && (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                Премиум
                              </span>
                            )}
                            {!user.is_active && (
                              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                Неактивен
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setShowAssignRole(true)}
                        className="text-blue-600 hover:text-blue-800 p-1"
                        title="Назначить роль"
                      >
                        <UserCheck className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Create Role Modal */}
        {showCreateRole && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Создать новую роль</h3>
                <form onSubmit={createRole}>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Название роли
                    </label>
                    <input
                      type="text"
                      value={newRole.name}
                      onChange={(e) => setNewRole({...newRole, name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="admin, moderator, etc."
                      required
                    />
                  </div>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Отображаемое название
                    </label>
                    <input
                      type="text"
                      value={newRole.display_name}
                      onChange={(e) => setNewRole({...newRole, display_name: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Администратор"
                      required
                    />
                  </div>
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Описание
                    </label>
                    <textarea
                      value={newRole.description}
                      onChange={(e) => setNewRole({...newRole, description: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      rows="3"
                      placeholder="Описание роли и её назначение"
                    />
                  </div>
                  <div className="flex justify-end space-x-3">
                    <button
                      type="button"
                      onClick={() => setShowCreateRole(false)}
                      className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
                    >
                      Отмена
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md"
                    >
                      Создать
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* Assign Role Modal */}
        {showAssignRole && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Назначить роль пользователю</h3>
                <form onSubmit={assignRole}>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Пользователь
                    </label>
                    <select
                      value={roleAssignment.user_id}
                      onChange={(e) => setRoleAssignment({...roleAssignment, user_id: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    >
                      <option value="">Выберите пользователя</option>
                      {users.map((user) => (
                        <option key={user.id} value={user.id}>
                          {user.full_name || user.username || user.email}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="mb-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Роль
                    </label>
                    <select
                      value={roleAssignment.role_id}
                      onChange={(e) => setRoleAssignment({...roleAssignment, role_id: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    >
                      <option value="">Выберите роль</option>
                      {roles.map((role) => (
                        <option key={role.id} value={role.id}>
                          {role.display_name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Причина назначения
                    </label>
                    <textarea
                      value={roleAssignment.reason}
                      onChange={(e) => setRoleAssignment({...roleAssignment, reason: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      rows="3"
                      placeholder="Обоснование назначения роли"
                    />
                  </div>
                  <div className="flex justify-end space-x-3">
                    <button
                      type="button"
                      onClick={() => setShowAssignRole(false)}
                      className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
                    >
                      Отмена
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-md"
                    >
                      Назначить
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RoleManagement;
