import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Shield, 
  Users, 
  Key, 
  Plus, 
  Edit, 
  Trash2, 
  Eye, 
  UserCheck,
  XCircle,
  Search,
  Filter,
  Download,
  Upload,
  Settings,
  AlertTriangle,
  CheckCircle,
  Clock,
  ArrowRight,
  Grid,
  List,
  Zap
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import ModuleCard from './ModuleCard';
import EnhancedButton from './EnhancedButton';
import LoadingSpinner from './LoadingSpinner';
import ModuleErrorBoundary from './ModuleErrorBoundary';

const EnhancedRoleManagement = () => {
  const { getModuleColor } = useTheme();
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('roles');
  const [viewMode, setViewMode] = useState('grid'); // grid or list
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  
  // Modal states
  const [showCreateRole, setShowCreateRole] = useState(false);
  const [showAssignRole, setShowAssignRole] = useState(false);
  const [showPermissionMatrix, setShowPermissionMatrix] = useState(false);
  const [showRoleHierarchy, setShowRoleHierarchy] = useState(false);
  const [selectedRole, setSelectedRole] = useState(null);

  // Forms
  const [newRole, setNewRole] = useState({
    name: '',
    display_name: '',
    description: '',
    permissions: [],
    parent_role: null,
    color: 'system'
  });

  const [roleAssignment, setRoleAssignment] = useState({
    user_id: '',
    role_id: '',
    reason: '',
    expires_at: null
  });

  // Permission matrix state
  const [permissionMatrix, setPermissionMatrix] = useState({});
  const [draggedPermission, setDraggedPermission] = useState(null);

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
        buildPermissionMatrix(rolesData);
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

  const buildPermissionMatrix = (rolesData) => {
    const matrix = {};
    rolesData.forEach(role => {
      matrix[role.id] = role.permissions || [];
    });
    setPermissionMatrix(matrix);
  };

  const getRoleModuleColor = (roleName) => {
    const roleModuleMap = {
      'super_admin': 'system',
      'admin': 'system', 
      'moderator': 'moderation',
      'marketing_manager': 'marketing',
      'project_manager': 'project',
      'analyst': 'analytics'
    };
    return roleModuleMap[roleName] || 'system';
  };

  const getRoleIcon = (roleName) => {
    const icons = {
      'super_admin': Shield,
      'admin': Settings,
      'moderator': Eye,
      'marketing_manager': Zap,
      'project_manager': Grid,
      'analyst': List
    };
    return icons[roleName] || Shield;
  };

  const filteredRoles = roles.filter(role => {
    const matchesSearch = role.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         role.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterStatus === 'all' || 
                         (filterStatus === 'active' && role.is_active) ||
                         (filterStatus === 'inactive' && !role.is_active) ||
                         (filterStatus === 'system' && role.is_system);
    return matchesSearch && matchesFilter;
  });

  const handleDragStart = (e, permission) => {
    setDraggedPermission(permission);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e, roleId) => {
    e.preventDefault();
    if (draggedPermission) {
      togglePermission(roleId, draggedPermission.id);
      setDraggedPermission(null);
    }
  };

  const togglePermission = async (roleId, permissionId) => {
    try {
      const currentPermissions = permissionMatrix[roleId] || [];
      const hasPermission = currentPermissions.some(p => p.id === permissionId);
      
      const response = await fetch(`/api/v1/admin/roles/${roleId}/permissions/${permissionId}`, {
        method: hasPermission ? 'DELETE' : 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        loadData(); // Reload to get updated permissions
      }
    } catch (err) {
      setError('Ошибка изменения прав доступа');
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
        setNewRole({ 
          name: '', 
          display_name: '', 
          description: '', 
          permissions: [],
          parent_role: null,
          color: 'system'
        });
        loadData();
      } else {
        const error = await response.json();
        setError(error.detail || 'Ошибка создания роли');
      }
    } catch (err) {
      setError('Ошибка создания роли');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <LoadingSpinner 
          size="lg" 
          module="system" 
          variant="neon"
          text="Загрузка системы ролей..."
        />
      </div>
    );
  }

  return (
    <ModuleErrorBoundary module="system" componentName="RoleManagement">
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Enhanced Header */}
          <motion.div 
            className="mb-8"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
              <div className="flex-1">
                <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 flex items-center">
                  <Shield className="h-8 w-8 text-red-500 mr-3" />
                  Управление ролями и правами
                </h1>
                <p className="mt-2 text-gray-600 dark:text-gray-400">
                  Расширенная система управления ролями с визуальной матрицей прав и drag-and-drop
                </p>
                
                {/* Stats */}
                <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
                    <div className="text-sm text-gray-500 dark:text-gray-400">Всего ролей</div>
                    <div className="text-xl font-semibold text-gray-900 dark:text-gray-100">{roles.length}</div>
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
                    <div className="text-sm text-gray-500 dark:text-gray-400">Активных</div>
                    <div className="text-xl font-semibold text-green-600">{roles.filter(r => r.is_active).length}</div>
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
                    <div className="text-sm text-gray-500 dark:text-gray-400">Системных</div>
                    <div className="text-xl font-semibold text-blue-600">{roles.filter(r => r.is_system).length}</div>
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
                    <div className="text-sm text-gray-500 dark:text-gray-400">Прав доступа</div>
                    <div className="text-xl font-semibold text-purple-600">{permissions.length}</div>
                  </div>
                </div>
              </div>
              
              <div className="mt-6 lg:mt-0 flex flex-wrap gap-3">
                <EnhancedButton
                  variant="module"
                  module="system"
                  onClick={() => setShowRoleHierarchy(true)}
                  icon={<Grid className="h-4 w-4" />}
                >
                  Иерархия ролей
                </EnhancedButton>
                <EnhancedButton
                  variant="module"
                  module="system"
                  onClick={() => setShowPermissionMatrix(true)}
                  icon={<Key className="h-4 w-4" />}
                >
                  Матрица прав
                </EnhancedButton>
                <EnhancedButton
                  variant="module-neon"
                  module="system"
                  onClick={() => setShowCreateRole(true)}
                  icon={<Plus className="h-4 w-4" />}
                >
                  Создать роль
                </EnhancedButton>
              </div>
            </div>
          </motion.div>

          {/* Error Message */}
          <AnimatePresence>
            {error && (
              <motion.div 
                className="mb-6"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
              >
                <ModuleCard module="system" variant="module" className="border-red-300 bg-red-50 dark:bg-red-900/20">
                  <div className="flex items-center">
                    <XCircle className="h-5 w-5 text-red-500 mr-3" />
                    <div>
                      <h3 className="text-sm font-medium text-red-800 dark:text-red-300">Ошибка</h3>
                      <p className="text-sm text-red-700 dark:text-red-400 mt-1">{error}</p>
                    </div>
                    <button 
                      onClick={() => setError('')}
                      className="ml-auto text-red-500 hover:text-red-700"
                    >
                      <XCircle className="h-4 w-4" />
                    </button>
                  </div>
                </ModuleCard>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Enhanced Tabs */}
          <div className="mb-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4">
              <nav className="flex space-x-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
                {[
                  { id: 'roles', name: 'Роли', icon: Shield, count: roles.length },
                  { id: 'permissions', name: 'Права', icon: Key, count: permissions.length },
                  { id: 'users', name: 'Пользователи', icon: Users, count: users.length }
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`${
                      activeTab === tab.id
                        ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
                        : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                    } px-4 py-2 rounded-md font-medium text-sm flex items-center transition-all duration-200`}
                  >
                    <tab.icon className="h-4 w-4 mr-2" />
                    {tab.name}
                    <span className="ml-2 bg-gray-200 dark:bg-gray-600 text-xs px-2 py-1 rounded-full">
                      {tab.count}
                    </span>
                  </button>
                ))}
              </nav>

              {/* Controls */}
              <div className="flex items-center space-x-3 mt-4 sm:mt-0">
                {/* Search */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Поиск..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  />
                </div>

                {/* Filter */}
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-red-500"
                >
                  <option value="all">Все роли</option>
                  <option value="active">Активные</option>
                  <option value="inactive">Неактивные</option>
                  <option value="system">Системные</option>
                </select>

                {/* View Mode */}
                <div className="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
                  <button
                    onClick={() => setViewMode('grid')}
                    className={`p-2 rounded ${viewMode === 'grid' ? 'bg-white dark:bg-gray-700 shadow-sm' : ''}`}
                  >
                    <Grid className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => setViewMode('list')}
                    className={`p-2 rounded ${viewMode === 'list' ? 'bg-white dark:bg-gray-700 shadow-sm' : ''}`}
                  >
                    <List className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Roles Tab */}
          {activeTab === 'roles' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              {viewMode === 'grid' ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {filteredRoles.map((role) => {
                    const RoleIcon = getRoleIcon(role.name);
                    const moduleColor = getRoleModuleColor(role.name);
                    
                    return (
                      <motion.div
                        key={role.id}
                        layout
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.9 }}
                        transition={{ duration: 0.2 }}
                      >
                        <ModuleCard 
                          module={moduleColor} 
                          variant="module-neon"
                          className="h-full"
                        >
                          <div className="flex items-start justify-between mb-4">
                            <div className="flex items-center">
                              <div 
                                className="p-3 rounded-lg mr-3"
                                style={{ 
                                  backgroundColor: `${getModuleColor(moduleColor)}20`,
                                  border: `1px solid ${getModuleColor(moduleColor)}40`
                                }}
                              >
                                <RoleIcon 
                                  className="h-6 w-6" 
                                  style={{ color: getModuleColor(moduleColor) }}
                                />
                              </div>
                              <div>
                                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                                  {role.display_name}
                                </h3>
                                <p className="text-sm text-gray-500 dark:text-gray-400">
                                  {role.name}
                                </p>
                              </div>
                            </div>
                            
                            <div className="flex flex-col space-y-1">
                              {role.is_system && (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300">
                                  Системная
                                </span>
                              )}
                              {!role.is_active && (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300">
                                  Неактивна
                                </span>
                              )}
                            </div>
                          </div>

                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 line-clamp-2">
                            {role.description || 'Описание отсутствует'}
                          </p>

                          <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400 mb-4">
                            <span>Прав: {(permissionMatrix[role.id] || []).length}</span>
                            <span>ID: {role.id}</span>
                          </div>

                          <div className="flex items-center justify-between">
                            <div className="flex space-x-2">
                              <button
                                onClick={() => {
                                  setSelectedRole(role);
                                  setShowPermissionMatrix(true);
                                }}
                                className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 p-1"
                                title="Просмотр прав"
                              >
                                <Eye className="h-4 w-4" />
                              </button>
                              {!role.is_system && (
                                <>
                                  <button
                                    className="text-yellow-600 dark:text-yellow-400 hover:text-yellow-800 dark:hover:text-yellow-300 p-1"
                                    title="Редактировать"
                                  >
                                    <Edit className="h-4 w-4" />
                                  </button>
                                  <button
                                    className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 p-1"
                                    title="Удалить"
                                  >
                                    <Trash2 className="h-4 w-4" />
                                  </button>
                                </>
                              )}
                            </div>
                            
                            <EnhancedButton
                              variant="module-outline"
                              module={moduleColor}
                              size="sm"
                              onClick={() => {
                                setRoleAssignment({...roleAssignment, role_id: role.id});
                                setShowAssignRole(true);
                              }}
                            >
                              Назначить
                            </EnhancedButton>
                          </div>
                        </ModuleCard>
                      </motion.div>
                    );
                  })}
                </div>
              ) : (
                // List view
                <ModuleCard module="system" variant="module">
                  <div className="divide-y divide-gray-200 dark:divide-gray-700">
                    {filteredRoles.map((role) => {
                      const RoleIcon = getRoleIcon(role.name);
                      const moduleColor = getRoleModuleColor(role.name);
                      
                      return (
                        <motion.div 
                          key={role.id} 
                          className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ duration: 0.2 }}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center flex-1">
                              <div 
                                className="p-2 rounded-lg mr-4"
                                style={{ 
                                  backgroundColor: `${getModuleColor(moduleColor)}20`,
                                  border: `1px solid ${getModuleColor(moduleColor)}40`
                                }}
                              >
                                <RoleIcon 
                                  className="h-5 w-5" 
                                  style={{ color: getModuleColor(moduleColor) }}
                                />
                              </div>
                              <div className="flex-1">
                                <div className="flex items-center">
                                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mr-3">
                                    {role.display_name}
                                  </h3>
                                  <div className="flex space-x-2">
                                    {role.is_system && (
                                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300">
                                        Системная
                                      </span>
                                    )}
                                    {!role.is_active && (
                                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300">
                                        Неактивна
                                      </span>
                                    )}
                                  </div>
                                </div>
                                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                  {role.description || 'Описание отсутствует'}
                                </p>
                                <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
                                  <span>ID: {role.id}</span>
                                  <span>Имя: {role.name}</span>
                                  <span>Прав: {(permissionMatrix[role.id] || []).length}</span>
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center space-x-2">
                              <button
                                onClick={() => {
                                  setSelectedRole(role);
                                  setShowPermissionMatrix(true);
                                }}
                                className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 p-2"
                                title="Просмотр прав"
                              >
                                <Eye className="h-4 w-4" />
                              </button>
                              {!role.is_system && (
                                <>
                                  <button
                                    className="text-yellow-600 dark:text-yellow-400 hover:text-yellow-800 dark:hover:text-yellow-300 p-2"
                                    title="Редактировать"
                                  >
                                    <Edit className="h-4 w-4" />
                                  </button>
                                  <button
                                    className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 p-2"
                                    title="Удалить"
                                  >
                                    <Trash2 className="h-4 w-4" />
                                  </button>
                                </>
                              )}
                            </div>
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </ModuleCard>
              )}
            </motion.div>
          )}

          {/* Permission Matrix Modal */}
          <AnimatePresence>
            {showPermissionMatrix && (
              <motion.div 
                className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <motion.div 
                  className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden"
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.9, opacity: 0 }}
                >
                  <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                    <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 flex items-center">
                      <Key className="h-6 w-6 mr-3 text-red-500" />
                      Матрица прав доступа
                    </h3>
                    <button
                      onClick={() => setShowPermissionMatrix(false)}
                      className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    >
                      <XCircle className="h-6 w-6" />
                    </button>
                  </div>
                  
                  <div className="p-6 overflow-auto max-h-[calc(90vh-120px)]">
                    <div className="mb-4 text-sm text-gray-600 dark:text-gray-400">
                      Перетащите права из левой панели на роли для назначения. Кликните по ячейке для переключения.
                    </div>
                    
                    <div className="grid grid-cols-12 gap-4">
                      {/* Permissions List */}
                      <div className="col-span-4">
                        <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-3">Доступные права</h4>
                        <div className="space-y-2 max-h-96 overflow-y-auto">
                          {permissions.map((permission) => (
                            <div
                              key={permission.id}
                              draggable
                              onDragStart={(e) => handleDragStart(e, permission)}
                              className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg cursor-move hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
                            >
                              <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                {permission.display_name}
                              </div>
                              <div className="text-xs text-gray-500 dark:text-gray-400">
                                {permission.resource}.{permission.action}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      {/* Roles Matrix */}
                      <div className="col-span-8">
                        <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-3">Роли</h4>
                        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                          {roles.map((role) => {
                            const rolePermissions = permissionMatrix[role.id] || [];
                            const moduleColor = getRoleModuleColor(role.name);
                            
                            return (
                              <div
                                key={role.id}
                                onDragOver={handleDragOver}
                                onDrop={(e) => handleDrop(e, role.id)}
                                className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-4 min-h-[200px] hover:border-gray-400 dark:hover:border-gray-500 transition-colors"
                              >
                                <div className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
                                  {role.display_name}
                                </div>
                                <div className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                                  {rolePermissions.length} прав
                                </div>
                                <div className="space-y-1">
                                  {rolePermissions.map((permission) => (
                                    <div
                                      key={permission.id}
                                      onClick={() => togglePermission(role.id, permission.id)}
                                      className="text-xs p-2 rounded cursor-pointer transition-colors"
                                      style={{
                                        backgroundColor: `${getModuleColor(moduleColor)}20`,
                                        color: getModuleColor(moduleColor)
                                      }}
                                    >
                                      {permission.display_name}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Create Role Modal */}
          <AnimatePresence>
            {showCreateRole && (
              <motion.div 
                className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <motion.div 
                  className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-md w-full"
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.9, opacity: 0 }}
                >
                  <div className="p-6">
                    <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-6 flex items-center">
                      <Plus className="h-6 w-6 mr-3 text-red-500" />
                      Создать новую роль
                    </h3>
                    
                    <form onSubmit={createRole} className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Название роли
                        </label>
                        <input
                          type="text"
                          value={newRole.name}
                          onChange={(e) => setNewRole({...newRole, name: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-red-500 focus:border-transparent"
                          placeholder="marketing_manager"
                          required
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Отображаемое название
                        </label>
                        <input
                          type="text"
                          value={newRole.display_name}
                          onChange={(e) => setNewRole({...newRole, display_name: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-red-500 focus:border-transparent"
                          placeholder="Маркетинг-менеджер"
                          required
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Описание
                        </label>
                        <textarea
                          value={newRole.description}
                          onChange={(e) => setNewRole({...newRole, description: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-red-500 focus:border-transparent"
                          rows="3"
                          placeholder="Описание роли и её назначение"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Модуль
                        </label>
                        <select
                          value={newRole.color}
                          onChange={(e) => setNewRole({...newRole, color: e.target.value})}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-red-500 focus:border-transparent"
                        >
                          <option value="system">Система</option>
                          <option value="marketing">Маркетинг</option>
                          <option value="moderation">Модерация</option>
                          <option value="project">Проект</option>
                          <option value="analytics">Аналитика</option>
                        </select>
                      </div>
                      
                      <div className="flex justify-end space-x-3 pt-4">
                        <EnhancedButton
                          variant="secondary"
                          onClick={() => setShowCreateRole(false)}
                        >
                          Отмена
                        </EnhancedButton>
                        <EnhancedButton
                          variant="module"
                          module="system"
                          type="submit"
                        >
                          Создать
                        </EnhancedButton>
                      </div>
                    </form>
                  </div>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </ModuleErrorBoundary>
  );
};

export default EnhancedRoleManagement;