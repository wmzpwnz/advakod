import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  History, 
  Search, 
  Filter, 
  Download, 
  Calendar,
  User,
  Shield,
  Plus,
  Minus,
  Edit,
  Eye,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  FileText,
  ArrowRight,
  ArrowLeft,
  RotateCcw
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import ModuleCard from './ModuleCard';
import EnhancedButton from './EnhancedButton';
import LoadingSpinner from './LoadingSpinner';

const RoleAuditHistory = () => {
  const { getModuleColor } = useTheme();
  const [auditLogs, setAuditLogs] = useState([]);
  const [filteredLogs, setFilteredLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Filters
  const [filters, setFilters] = useState({
    dateFrom: '',
    dateTo: '',
    action: 'all',
    user: '',
    role: '',
    status: 'all'
  });
  
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedLog, setSelectedLog] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20);
  const [totalItems, setTotalItems] = useState(0);

  // Statistics
  const [stats, setStats] = useState({
    totalChanges: 0,
    todayChanges: 0,
    successRate: 0,
    topUsers: [],
    actionBreakdown: {}
  });

  useEffect(() => {
    loadAuditData();
  }, [currentPage, filters]);

  useEffect(() => {
    applyFilters();
  }, [auditLogs, searchTerm, filters]);

  const loadAuditData = async () => {
    try {
      setLoading(true);
      const queryParams = new URLSearchParams({
        page: currentPage,
        limit: itemsPerPage,
        ...filters
      });

      const [logsRes, statsRes] = await Promise.all([
        fetch(`/api/v1/admin/roles/audit?${queryParams}`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        fetch('/api/v1/admin/roles/audit/stats', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        })
      ]);

      if (logsRes.ok) {
        const logsData = await logsRes.json();
        setAuditLogs(logsData.logs || []);
        setTotalItems(logsData.total || 0);
      }

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }

    } catch (err) {
      setError('Ошибка загрузки данных аудита');
      console.error('Error loading audit data:', err);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...auditLogs];

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(log => 
        log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.userName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.details?.roleName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.details?.reason?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredLogs(filtered);
  };

  const exportAuditReport = async () => {
    try {
      const queryParams = new URLSearchParams(filters);
      const response = await fetch(`/api/v1/admin/roles/audit/export?${queryParams}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `role-audit-${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (err) {
      setError('Ошибка экспорта отчета');
    }
  };

  const getActionIcon = (action) => {
    const icons = {
      'role_created': Plus,
      'role_updated': Edit,
      'role_deleted': Minus,
      'role_assigned': User,
      'role_revoked': XCircle,
      'permission_added': CheckCircle,
      'permission_removed': XCircle,
      'role_activated': CheckCircle,
      'role_deactivated': XCircle
    };
    return icons[action] || Shield;
  };

  const getActionColor = (action) => {
    const colors = {
      'role_created': 'text-green-600',
      'role_updated': 'text-blue-600',
      'role_deleted': 'text-red-600',
      'role_assigned': 'text-purple-600',
      'role_revoked': 'text-orange-600',
      'permission_added': 'text-green-600',
      'permission_removed': 'text-red-600',
      'role_activated': 'text-green-600',
      'role_deactivated': 'text-gray-600'
    };
    return colors[action] || 'text-gray-600';
  };

  const getActionText = (action) => {
    const texts = {
      'role_created': 'Роль создана',
      'role_updated': 'Роль обновлена',
      'role_deleted': 'Роль удалена',
      'role_assigned': 'Роль назначена',
      'role_revoked': 'Роль отозвана',
      'permission_added': 'Право добавлено',
      'permission_removed': 'Право удалено',
      'role_activated': 'Роль активирована',
      'role_deactivated': 'Роль деактивирована'
    };
    return texts[action] || action;
  };

  const totalPages = Math.ceil(totalItems / itemsPerPage);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <LoadingSpinner 
          size="lg" 
          module="system" 
          variant="neon"
          text="Загрузка истории изменений..."
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <motion.div 
          className="mb-8"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 flex items-center">
                <History className="h-8 w-8 text-red-500 mr-3" />
                История изменений ролей
              </h1>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                Полный аудит всех изменений в системе ролей и прав доступа
              </p>
            </div>
            
            <div className="mt-6 lg:mt-0 flex flex-wrap gap-3">
              <EnhancedButton
                variant="module-outline"
                module="system"
                onClick={exportAuditReport}
                icon={<Download className="h-4 w-4" />}
              >
                Экспорт отчета
              </EnhancedButton>
              <EnhancedButton
                variant="module"
                module="system"
                onClick={loadAuditData}
                icon={<RotateCcw className="h-4 w-4" />}
              >
                Обновить
              </EnhancedButton>
            </div>
          </div>
        </motion.div>

        {/* Statistics Cards */}
        <motion.div 
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <ModuleCard module="system" variant="module">
            <div className="flex items-center">
              <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <FileText className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">Всего изменений</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                  {stats.totalChanges.toLocaleString()}
                </p>
              </div>
            </div>
          </ModuleCard>

          <ModuleCard module="system" variant="module">
            <div className="flex items-center">
              <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                <Calendar className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">Сегодня</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                  {stats.todayChanges}
                </p>
              </div>
            </div>
          </ModuleCard>

          <ModuleCard module="system" variant="module">
            <div className="flex items-center">
              <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <CheckCircle className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">Успешность</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                  {stats.successRate}%
                </p>
              </div>
            </div>
          </ModuleCard>

          <ModuleCard module="system" variant="module">
            <div className="flex items-center">
              <div className="p-3 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
                <User className="h-6 w-6 text-orange-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">Активных админов</p>
                <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                  {stats.topUsers.length}
                </p>
              </div>
            </div>
          </ModuleCard>
        </motion.div>

        {/* Filters */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <ModuleCard module="system" variant="module" className="mb-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
              {/* Search */}
              <div className="lg:col-span-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Поиск по действиям, пользователям..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 pr-4 py-2 w-full border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Date From */}
              <div>
                <input
                  type="date"
                  value={filters.dateFrom}
                  onChange={(e) => setFilters(prev => ({...prev, dateFrom: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-red-500 focus:border-transparent"
                />
              </div>

              {/* Date To */}
              <div>
                <input
                  type="date"
                  value={filters.dateTo}
                  onChange={(e) => setFilters(prev => ({...prev, dateTo: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-red-500 focus:border-transparent"
                />
              </div>

              {/* Action Filter */}
              <div>
                <select
                  value={filters.action}
                  onChange={(e) => setFilters(prev => ({...prev, action: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-red-500 focus:border-transparent"
                >
                  <option value="all">Все действия</option>
                  <option value="role_created">Создание ролей</option>
                  <option value="role_updated">Обновление ролей</option>
                  <option value="role_deleted">Удаление ролей</option>
                  <option value="role_assigned">Назначение ролей</option>
                  <option value="role_revoked">Отзыв ролей</option>
                  <option value="permission_added">Добавление прав</option>
                  <option value="permission_removed">Удаление прав</option>
                </select>
              </div>

              {/* Status Filter */}
              <div>
                <select
                  value={filters.status}
                  onChange={(e) => setFilters(prev => ({...prev, status: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-red-500 focus:border-transparent"
                >
                  <option value="all">Все статусы</option>
                  <option value="success">Успешные</option>
                  <option value="failed">Неудачные</option>
                </select>
              </div>
            </div>
          </ModuleCard>
        </motion.div>

        {/* Audit Log Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          <ModuleCard module="system" variant="module">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-800">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Время
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Действие
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Пользователь
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Роль/Объект
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Статус
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Действия
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                  {filteredLogs.map((log, index) => {
                    const ActionIcon = getActionIcon(log.action);
                    const actionColor = getActionColor(log.action);
                    
                    return (
                      <motion.tr 
                        key={log.id}
                        className="hover:bg-gray-50 dark:hover:bg-gray-800"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.2, delay: index * 0.05 }}
                      >
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                          <div className="flex items-center">
                            <Clock className="h-4 w-4 text-gray-400 mr-2" />
                            {new Date(log.timestamp).toLocaleString()}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <ActionIcon className={`h-4 w-4 mr-2 ${actionColor}`} />
                            <span className="text-sm text-gray-900 dark:text-gray-100">
                              {getActionText(log.action)}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="h-8 w-8 bg-gray-300 dark:bg-gray-600 rounded-full flex items-center justify-center mr-3">
                              <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                                {log.userName.charAt(0).toUpperCase()}
                              </span>
                            </div>
                            <div>
                              <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                {log.userName}
                              </div>
                              <div className="text-sm text-gray-500 dark:text-gray-400">
                                {log.userRole}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                          <div>
                            <div className="font-medium">
                              {log.details?.roleName || log.details?.targetUser || 'N/A'}
                            </div>
                            {log.details?.permission && (
                              <div className="text-xs text-gray-500 dark:text-gray-400">
                                {log.details.permission}
                              </div>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {log.success ? (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300">
                              <CheckCircle className="h-3 w-3 mr-1" />
                              Успешно
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300">
                              <XCircle className="h-3 w-3 mr-1" />
                              Ошибка
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <button
                            onClick={() => {
                              setSelectedLog(log);
                              setShowDetails(true);
                            }}
                            className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                        </td>
                      </motion.tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 dark:border-gray-700">
                <div className="text-sm text-gray-700 dark:text-gray-300">
                  Показано {((currentPage - 1) * itemsPerPage) + 1} - {Math.min(currentPage * itemsPerPage, totalItems)} из {totalItems}
                </div>
                <div className="flex space-x-2">
                  <EnhancedButton
                    variant="secondary"
                    size="sm"
                    onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                    disabled={currentPage === 1}
                    icon={<ArrowLeft className="h-4 w-4" />}
                  >
                    Назад
                  </EnhancedButton>
                  <span className="px-3 py-2 text-sm text-gray-700 dark:text-gray-300">
                    {currentPage} из {totalPages}
                  </span>
                  <EnhancedButton
                    variant="secondary"
                    size="sm"
                    onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                    disabled={currentPage === totalPages}
                    icon={<ArrowRight className="h-4 w-4" />}
                  >
                    Далее
                  </EnhancedButton>
                </div>
              </div>
            )}
          </ModuleCard>
        </motion.div>

        {/* Log Details Modal */}
        <AnimatePresence>
          {showDetails && selectedLog && (
            <motion.div 
              className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <motion.div 
                className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden"
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
              >
                <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 flex items-center">
                    <FileText className="h-6 w-6 mr-3 text-red-500" />
                    Детали изменения
                  </h3>
                  <button
                    onClick={() => setShowDetails(false)}
                    className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  >
                    <XCircle className="h-6 w-6" />
                  </button>
                </div>
                
                <div className="p-6 overflow-auto max-h-[calc(90vh-120px)]">
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Время
                        </label>
                        <p className="text-sm text-gray-900 dark:text-gray-100">
                          {new Date(selectedLog.timestamp).toLocaleString()}
                        </p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Действие
                        </label>
                        <p className="text-sm text-gray-900 dark:text-gray-100">
                          {getActionText(selectedLog.action)}
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Пользователь
                        </label>
                        <p className="text-sm text-gray-900 dark:text-gray-100">
                          {selectedLog.userName} ({selectedLog.userRole})
                        </p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          IP адрес
                        </label>
                        <p className="text-sm text-gray-900 dark:text-gray-100">
                          {selectedLog.ipAddress}
                        </p>
                      </div>
                    </div>

                    {selectedLog.details?.reason && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                          Причина
                        </label>
                        <p className="text-sm text-gray-900 dark:text-gray-100">
                          {selectedLog.details.reason}
                        </p>
                      </div>
                    )}

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Детали изменения
                      </label>
                      <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                        <pre className="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                          {JSON.stringify(selectedLog.details, null, 2)}
                        </pre>
                      </div>
                    </div>

                    {!selectedLog.success && selectedLog.errorMessage && (
                      <div>
                        <label className="block text-sm font-medium text-red-700 dark:text-red-300 mb-1">
                          Ошибка
                        </label>
                        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                          <p className="text-sm text-red-700 dark:text-red-400">
                            {selectedLog.errorMessage}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default RoleAuditHistory;