import React, { useState, useEffect } from 'react';
import { 
  FunnelIcon,
  XMarkIcon,
  CheckIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  StarIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline';
import { motion, AnimatePresence } from 'framer-motion';

const NotificationFilters = ({ 
  filters, 
  onFiltersChange, 
  onClearFilters,
  className = '' 
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [localFilters, setLocalFilters] = useState(filters);

  // Update local filters when props change
  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  // Apply filters
  const applyFilters = () => {
    onFiltersChange(localFilters);
    setIsOpen(false);
  };

  // Clear all filters
  const clearAllFilters = () => {
    const emptyFilters = {
      category: [],
      priority: [],
      status: [],
      type: [],
      is_read: null,
      is_starred: null,
      date_from: null,
      date_to: null,
      group_key: null
    };
    setLocalFilters(emptyFilters);
    onFiltersChange(emptyFilters);
    onClearFilters?.();
  };

  // Toggle array filter
  const toggleArrayFilter = (filterKey, value) => {
    setLocalFilters(prev => {
      const currentArray = prev[filterKey] || [];
      const newArray = currentArray.includes(value)
        ? currentArray.filter(item => item !== value)
        : [...currentArray, value];
      
      return {
        ...prev,
        [filterKey]: newArray
      };
    });
  };

  // Set boolean filter
  const setBooleanFilter = (filterKey, value) => {
    setLocalFilters(prev => ({
      ...prev,
      [filterKey]: prev[filterKey] === value ? null : value
    }));
  };

  // Set date filter
  const setDateFilter = (filterKey, value) => {
    setLocalFilters(prev => ({
      ...prev,
      [filterKey]: value || null
    }));
  };

  // Get active filter count
  const getActiveFilterCount = () => {
    let count = 0;
    
    if (localFilters.category?.length > 0) count++;
    if (localFilters.priority?.length > 0) count++;
    if (localFilters.status?.length > 0) count++;
    if (localFilters.type?.length > 0) count++;
    if (localFilters.is_read !== null) count++;
    if (localFilters.is_starred !== null) count++;
    if (localFilters.date_from) count++;
    if (localFilters.date_to) count++;
    if (localFilters.group_key) count++;
    
    return count;
  };

  const activeFilterCount = getActiveFilterCount();

  // Category options
  const categoryOptions = [
    { value: 'system', label: 'Система', color: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200' },
    { value: 'marketing', label: 'Маркетинг', color: 'bg-orange-100 text-orange-800 dark:bg-orange-800 dark:text-orange-200' },
    { value: 'moderation', label: 'Модерация', color: 'bg-purple-100 text-purple-800 dark:bg-purple-800 dark:text-purple-200' },
    { value: 'project', label: 'Проект', color: 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-200' },
    { value: 'analytics', label: 'Аналитика', color: 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-200' },
    { value: 'security', label: 'Безопасность', color: 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-200' }
  ];

  // Priority options
  const priorityOptions = [
    { value: 'low', label: 'Низкий', color: 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-200' },
    { value: 'medium', label: 'Средний', color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-200' },
    { value: 'high', label: 'Высокий', color: 'bg-orange-100 text-orange-800 dark:bg-orange-800 dark:text-orange-200' },
    { value: 'critical', label: 'Критический', color: 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-200' }
  ];

  // Type options
  const typeOptions = [
    { value: 'info', label: 'Информация', color: 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-200' },
    { value: 'success', label: 'Успех', color: 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-200' },
    { value: 'warning', label: 'Предупреждение', color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-200' },
    { value: 'error', label: 'Ошибка', color: 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-200' }
  ];

  // Status options
  const statusOptions = [
    { value: 'pending', label: 'Ожидание', color: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200' },
    { value: 'sent', label: 'Отправлено', color: 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-200' },
    { value: 'delivered', label: 'Доставлено', color: 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-200' },
    { value: 'read', label: 'Прочитано', color: 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-200' },
    { value: 'failed', label: 'Ошибка', color: 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-200' },
    { value: 'dismissed', label: 'Скрыто', color: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200' }
  ];

  return (
    <div className={`relative ${className}`}>
      {/* Filter Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center space-x-2 px-3 py-2 rounded-lg border transition-colors ${
          isOpen || activeFilterCount > 0
            ? 'bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-900/20 dark:border-blue-800 dark:text-blue-300'
            : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700'
        }`}
      >
        <FunnelIcon className="w-4 h-4" />
        <span className="text-sm font-medium">Фильтры</span>
        {activeFilterCount > 0 && (
          <span className="bg-blue-600 text-white text-xs px-2 py-0.5 rounded-full">
            {activeFilterCount}
          </span>
        )}
      </button>

      {/* Filter Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute top-full left-0 mt-2 w-96 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50"
          >
            <div className="p-4">
              {/* Header */}
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Фильтры уведомлений
                </h3>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <XMarkIcon className="w-5 h-5 text-gray-500" />
                </button>
              </div>

              <div className="space-y-4 max-h-96 overflow-y-auto">
                {/* Category Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Категория
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {categoryOptions.map(option => (
                      <button
                        key={option.value}
                        onClick={() => toggleArrayFilter('category', option.value)}
                        className={`px-3 py-1 text-xs rounded-full transition-colors ${
                          localFilters.category?.includes(option.value)
                            ? option.color
                            : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                        }`}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Priority Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Приоритет
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {priorityOptions.map(option => (
                      <button
                        key={option.value}
                        onClick={() => toggleArrayFilter('priority', option.value)}
                        className={`px-3 py-1 text-xs rounded-full transition-colors ${
                          localFilters.priority?.includes(option.value)
                            ? option.color
                            : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                        }`}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Type Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Тип
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {typeOptions.map(option => (
                      <button
                        key={option.value}
                        onClick={() => toggleArrayFilter('type', option.value)}
                        className={`px-3 py-1 text-xs rounded-full transition-colors ${
                          localFilters.type?.includes(option.value)
                            ? option.color
                            : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                        }`}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Status Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Статус
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {statusOptions.map(option => (
                      <button
                        key={option.value}
                        onClick={() => toggleArrayFilter('status', option.value)}
                        className={`px-3 py-1 text-xs rounded-full transition-colors ${
                          localFilters.status?.includes(option.value)
                            ? option.color
                            : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                        }`}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Read Status */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Статус прочтения
                  </label>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setBooleanFilter('is_read', false)}
                      className={`flex items-center space-x-2 px-3 py-2 text-sm rounded-lg transition-colors ${
                        localFilters.is_read === false
                          ? 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-200'
                          : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                      }`}
                    >
                      <EyeSlashIcon className="w-4 h-4" />
                      <span>Непрочитанные</span>
                    </button>
                    <button
                      onClick={() => setBooleanFilter('is_read', true)}
                      className={`flex items-center space-x-2 px-3 py-2 text-sm rounded-lg transition-colors ${
                        localFilters.is_read === true
                          ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-200'
                          : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                      }`}
                    >
                      <EyeIcon className="w-4 h-4" />
                      <span>Прочитанные</span>
                    </button>
                  </div>
                </div>

                {/* Starred Status */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Избранные
                  </label>
                  <button
                    onClick={() => setBooleanFilter('is_starred', true)}
                    className={`flex items-center space-x-2 px-3 py-2 text-sm rounded-lg transition-colors ${
                      localFilters.is_starred === true
                        ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-200'
                        : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                    }`}
                  >
                    <StarIcon className="w-4 h-4" />
                    <span>Только избранные</span>
                  </button>
                </div>

                {/* Date Range */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Период
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">
                        С
                      </label>
                      <input
                        type="date"
                        value={localFilters.date_from || ''}
                        onChange={(e) => setDateFilter('date_from', e.target.value)}
                        className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">
                        До
                      </label>
                      <input
                        type="date"
                        value={localFilters.date_to || ''}
                        onChange={(e) => setDateFilter('date_to', e.target.value)}
                        className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between pt-4 mt-4 border-t border-gray-200 dark:border-gray-700">
                <button
                  onClick={clearAllFilters}
                  className="px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                >
                  Очистить все
                </button>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setIsOpen(false)}
                    className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                  >
                    Отмена
                  </button>
                  <button
                    onClick={applyFilters}
                    className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Применить
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Backdrop */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-25 z-40"
            onClick={() => setIsOpen(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
};

export default NotificationFilters;