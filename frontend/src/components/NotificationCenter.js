import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  BellIcon, 
  XMarkIcon, 
  StarIcon,
  CheckIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  CheckCircleIcon,
  XCircleIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  EllipsisVerticalIcon
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';
import { motion, AnimatePresence } from 'framer-motion';

const NotificationCenter = ({ isOpen, onClose, className = '' }) => {
  const [notifications, setNotifications] = useState([]);
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const [filters, setFilters] = useState({
    category: [],
    priority: [],
    is_read: null,
    is_starred: null
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNotifications, setSelectedNotifications] = useState(new Set());
  const [showFilters, setShowFilters] = useState(false);

  // Fetch notifications
  const fetchNotifications = useCallback(async () => {
    if (!isOpen) return;
    
    setLoading(true);
    try {
      const params = new URLSearchParams();
      
      // Add filters
      if (filters.category.length > 0) {
        filters.category.forEach(cat => params.append('category', cat));
      }
      if (filters.priority.length > 0) {
        filters.priority.forEach(pri => params.append('priority', pri));
      }
      if (filters.is_read !== null) {
        params.append('is_read', filters.is_read);
      }
      if (filters.is_starred !== null) {
        params.append('is_starred', filters.is_starred);
      }

      const response = await fetch(`/api/v1/admin/notifications/center?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setNotifications(data.notifications || []);
        setGroups(data.groups || []);
        setUnreadCount(data.unread_count || 0);
        setTotalCount(data.total_count || 0);
      }
    } catch (error) {
      console.error('Error fetching notifications:', error);
    } finally {
      setLoading(false);
    }
  }, [isOpen, filters]);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  // Filter notifications by search query
  const filteredNotifications = useMemo(() => {
    if (!searchQuery) return notifications;
    
    const query = searchQuery.toLowerCase();
    return notifications.filter(notification => 
      notification.title.toLowerCase().includes(query) ||
      notification.content.toLowerCase().includes(query)
    );
  }, [notifications, searchQuery]);

  // Mark notifications as read
  const markAsRead = async (notificationIds) => {
    try {
      const response = await fetch('/api/v1/admin/notifications/mark-read', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ notification_ids: notificationIds })
      });

      if (response.ok) {
        await fetchNotifications();
        setSelectedNotifications(new Set());
      }
    } catch (error) {
      console.error('Error marking notifications as read:', error);
    }
  };

  // Mark notifications as starred
  const markAsStarred = async (notificationIds, starred = true) => {
    try {
      const response = await fetch('/api/v1/admin/notifications/mark-starred', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ notification_ids: notificationIds, starred })
      });

      if (response.ok) {
        await fetchNotifications();
        setSelectedNotifications(new Set());
      }
    } catch (error) {
      console.error('Error marking notifications as starred:', error);
    }
  };

  // Dismiss notifications
  const dismissNotifications = async (notificationIds) => {
    try {
      const response = await fetch('/api/v1/admin/notifications/dismiss', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ notification_ids: notificationIds })
      });

      if (response.ok) {
        await fetchNotifications();
        setSelectedNotifications(new Set());
      }
    } catch (error) {
      console.error('Error dismissing notifications:', error);
    }
  };

  // Get notification icon
  const getNotificationIcon = (type, priority) => {
    const iconClass = "w-5 h-5";
    
    switch (type) {
      case 'success':
        return <CheckCircleIcon className={`${iconClass} text-green-500`} />;
      case 'warning':
        return <ExclamationTriangleIcon className={`${iconClass} text-yellow-500`} />;
      case 'error':
        return <XCircleIcon className={`${iconClass} text-red-500`} />;
      default:
        return <InformationCircleIcon className={`${iconClass} text-blue-500`} />;
    }
  };

  // Get priority color
  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'critical':
        return 'border-l-red-500 bg-red-50 dark:bg-red-900/20';
      case 'high':
        return 'border-l-orange-500 bg-orange-50 dark:bg-orange-900/20';
      case 'medium':
        return 'border-l-yellow-500 bg-yellow-50 dark:bg-yellow-900/20';
      default:
        return 'border-l-blue-500 bg-blue-50 dark:bg-blue-900/20';
    }
  };

  // Get category color
  const getCategoryColor = (category) => {
    switch (category) {
      case 'system':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200';
      case 'marketing':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-800 dark:text-orange-200';
      case 'moderation':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-800 dark:text-purple-200';
      case 'project':
        return 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-200';
      case 'analytics':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-200';
      case 'security':
        return 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200';
    }
  };

  // Format time ago
  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) return 'только что';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} мин назад`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} ч назад`;
    if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)} дн назад`;
    
    return date.toLocaleDateString('ru-RU');
  };

  // Handle notification selection
  const toggleNotificationSelection = (notificationId) => {
    const newSelection = new Set(selectedNotifications);
    if (newSelection.has(notificationId)) {
      newSelection.delete(notificationId);
    } else {
      newSelection.add(notificationId);
    }
    setSelectedNotifications(newSelection);
  };

  // Select all notifications
  const selectAllNotifications = () => {
    const allIds = new Set(filteredNotifications.map(n => n.id));
    setSelectedNotifications(allIds);
  };

  // Clear selection
  const clearSelection = () => {
    setSelectedNotifications(new Set());
  };

  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ opacity: 0, x: 300 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 300 }}
      transition={{ duration: 0.3 }}
      className={`fixed right-0 top-0 h-full w-96 bg-white dark:bg-gray-900 shadow-2xl z-50 flex flex-col ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-2">
          <BellIcon className="w-6 h-6 text-gray-600 dark:text-gray-400" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Уведомления
          </h2>
          {unreadCount > 0 && (
            <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full">
              {unreadCount}
            </span>
          )}
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
        >
          <XMarkIcon className="w-5 h-5 text-gray-500" />
        </button>
      </div>

      {/* Search and Filters */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-2 mb-3">
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Поиск уведомлений..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`p-2 rounded-lg transition-colors ${
              showFilters 
                ? 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400' 
                : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            <FunnelIcon className="w-4 h-4" />
          </button>
        </div>

        {/* Filters */}
        <AnimatePresence>
          {showFilters && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="space-y-3"
            >
              {/* Category Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Категория
                </label>
                <div className="flex flex-wrap gap-1">
                  {['system', 'marketing', 'moderation', 'project', 'analytics', 'security'].map(category => (
                    <button
                      key={category}
                      onClick={() => {
                        const newFilters = { ...filters };
                        if (newFilters.category.includes(category)) {
                          newFilters.category = newFilters.category.filter(c => c !== category);
                        } else {
                          newFilters.category.push(category);
                        }
                        setFilters(newFilters);
                      }}
                      className={`px-2 py-1 text-xs rounded-full transition-colors ${
                        filters.category.includes(category)
                          ? getCategoryColor(category)
                          : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                      }`}
                    >
                      {category}
                    </button>
                  ))}
                </div>
              </div>

              {/* Priority Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Приоритет
                </label>
                <div className="flex flex-wrap gap-1">
                  {['low', 'medium', 'high', 'critical'].map(priority => (
                    <button
                      key={priority}
                      onClick={() => {
                        const newFilters = { ...filters };
                        if (newFilters.priority.includes(priority)) {
                          newFilters.priority = newFilters.priority.filter(p => p !== priority);
                        } else {
                          newFilters.priority.push(priority);
                        }
                        setFilters(newFilters);
                      }}
                      className={`px-2 py-1 text-xs rounded-full transition-colors ${
                        filters.priority.includes(priority)
                          ? 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-200'
                          : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                      }`}
                    >
                      {priority}
                    </button>
                  ))}
                </div>
              </div>

              {/* Status Filter */}
              <div className="flex space-x-2">
                <button
                  onClick={() => setFilters({ ...filters, is_read: filters.is_read === false ? null : false })}
                  className={`px-3 py-1 text-xs rounded-full transition-colors ${
                    filters.is_read === false
                      ? 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-200'
                      : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                >
                  Непрочитанные
                </button>
                <button
                  onClick={() => setFilters({ ...filters, is_starred: filters.is_starred === true ? null : true })}
                  className={`px-3 py-1 text-xs rounded-full transition-colors ${
                    filters.is_starred === true
                      ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-200'
                      : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                >
                  Избранные
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Bulk Actions */}
      {selectedNotifications.size > 0 && (
        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <span className="text-sm text-blue-700 dark:text-blue-300">
              Выбрано: {selectedNotifications.size}
            </span>
            <div className="flex space-x-2">
              <button
                onClick={() => markAsRead(Array.from(selectedNotifications))}
                className="px-3 py-1 text-xs bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Прочитать
              </button>
              <button
                onClick={() => markAsStarred(Array.from(selectedNotifications))}
                className="px-3 py-1 text-xs bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors"
              >
                В избранное
              </button>
              <button
                onClick={() => dismissNotifications(Array.from(selectedNotifications))}
                className="px-3 py-1 text-xs bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                Скрыть
              </button>
              <button
                onClick={clearSelection}
                className="px-3 py-1 text-xs bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Отменить
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Notifications List */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : filteredNotifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-gray-500 dark:text-gray-400">
            <BellIcon className="w-12 h-12 mb-2 opacity-50" />
            <p className="text-sm">Нет уведомлений</p>
          </div>
        ) : (
          <div className="space-y-1 p-2">
            {filteredNotifications.map((notification) => (
              <motion.div
                key={notification.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className={`p-3 rounded-lg border-l-4 cursor-pointer transition-all hover:shadow-md ${
                  getPriorityColor(notification.priority)
                } ${
                  !notification.is_read ? 'ring-2 ring-blue-200 dark:ring-blue-800' : ''
                } ${
                  selectedNotifications.has(notification.id) ? 'ring-2 ring-blue-500' : ''
                }`}
                onClick={() => toggleNotificationSelection(notification.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    <div className="flex-shrink-0 mt-1">
                      {getNotificationIcon(notification.type, notification.priority)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <h4 className={`text-sm font-medium truncate ${
                          notification.is_read 
                            ? 'text-gray-700 dark:text-gray-300' 
                            : 'text-gray-900 dark:text-white'
                        }`}>
                          {notification.title}
                        </h4>
                        <span className={`px-2 py-0.5 text-xs rounded-full ${getCategoryColor(notification.category)}`}>
                          {notification.category}
                        </span>
                      </div>
                      <p className={`text-sm mb-2 ${
                        notification.is_read 
                          ? 'text-gray-500 dark:text-gray-400' 
                          : 'text-gray-700 dark:text-gray-300'
                      }`}>
                        {notification.content}
                      </p>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-400">
                          {formatTimeAgo(notification.created_at)}
                        </span>
                        <div className="flex items-center space-x-1">
                          {notification.is_starred && (
                            <StarIconSolid className="w-4 h-4 text-yellow-500" />
                          )}
                          {notification.action_url && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                window.open(notification.action_url, '_blank');
                              }}
                              className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                            >
                              {notification.action_text || 'Открыть'}
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-1 ml-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        markAsStarred([notification.id], !notification.is_starred);
                      }}
                      className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
                    >
                      {notification.is_starred ? (
                        <StarIconSolid className="w-4 h-4 text-yellow-500" />
                      ) : (
                        <StarIcon className="w-4 h-4 text-gray-400" />
                      )}
                    </button>
                    {!notification.is_read && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          markAsRead([notification.id]);
                        }}
                        className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
                      >
                        <CheckIcon className="w-4 h-4 text-gray-400" />
                      </button>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
          <span>Всего: {totalCount}</span>
          <div className="flex space-x-2">
            <button
              onClick={selectAllNotifications}
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              Выбрать все
            </button>
            <button
              onClick={() => markAsRead(filteredNotifications.map(n => n.id))}
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              Прочитать все
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default NotificationCenter;