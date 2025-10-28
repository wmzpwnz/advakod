import React, { useState } from 'react';
import { XMarkIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import {
  ChartBarIcon,
  TableCellsIcon,
  PresentationChartLineIcon,
  UsersIcon,
  ClockIcon,
  ArrowTrendingUpIcon,
  ChartPieIcon
} from '@heroicons/react/24/outline';

const WidgetLibrary = ({ templates, onSelectTemplate, onClose }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  const getWidgetIcon = (template) => {
    if (template.icon) {
      switch (template.icon) {
        case 'users':
          return <UsersIcon className="h-8 w-8" />;
        case 'user-check':
          return <UsersIcon className="h-8 w-8" />;
        case 'trending-up':
          return <ArrowTrendingUpIcon className="h-8 w-8" />;
        case 'clock':
          return <ClockIcon className="h-8 w-8" />;
        case 'pie-chart':
          return <ChartPieIcon className="h-8 w-8" />;
        case 'table':
          return <TableCellsIcon className="h-8 w-8" />;
        default:
          return <ChartBarIcon className="h-8 w-8" />;
      }
    }

    switch (template.type) {
      case 'chart':
        return <ChartBarIcon className="h-8 w-8" />;
      case 'table':
        return <TableCellsIcon className="h-8 w-8" />;
      case 'metric':
        return <PresentationChartLineIcon className="h-8 w-8" />;
      default:
        return <ChartBarIcon className="h-8 w-8" />;
    }
  };

  const getWidgetTypeColor = (type) => {
    switch (type) {
      case 'metric':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'chart':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'table':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const getChartTypeLabel = (chartType) => {
    switch (chartType) {
      case 'line':
        return 'Линейный';
      case 'bar':
        return 'Столбчатый';
      case 'pie':
        return 'Круговая диаграмма';
      case 'area':
        return 'Область';
      case 'scatter':
        return 'Точечный';
      default:
        return chartType;
    }
  };

  const categories = [
    { id: 'all', name: 'Все виджеты' },
    { id: 'metric', name: 'Метрики' },
    { id: 'chart', name: 'Графики' },
    { id: 'table', name: 'Таблицы' }
  ];

  const filteredTemplates = templates.filter(template => {
    const matchesSearch = template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (template.description && template.description.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesCategory = selectedCategory === 'all' || template.type === selectedCategory;
    
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Библиотека виджетов
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Search and Filters */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-4">
            {/* Search */}
            <div className="flex-1 relative">
              <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Поиск виджетов..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>

            {/* Category Filter */}
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              {categories.map(category => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Widget Grid */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {filteredTemplates.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-500 dark:text-gray-400 mb-2">
                Виджеты не найдены
              </div>
              <div className="text-sm text-gray-400 dark:text-gray-500">
                Попробуйте изменить поисковый запрос или фильтр
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredTemplates.map(template => (
                <div
                  key={template.id}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer group"
                  onClick={() => onSelectTemplate(template)}
                >
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 text-gray-400 group-hover:text-blue-600 transition-colors">
                      {getWidgetIcon(template)}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {template.name}
                        </h3>
                        <span className={`px-2 py-1 text-xs rounded-full ${getWidgetTypeColor(template.type)}`}>
                          {template.type}
                        </span>
                      </div>
                      
                      {template.description && (
                        <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 line-clamp-2">
                          {template.description}
                        </p>
                      )}
                      
                      <div className="flex items-center justify-between text-xs text-gray-400">
                        <div>
                          Источник: {template.config?.data_source || 'Не указан'}
                        </div>
                        {template.chart_type && (
                          <div>
                            {getChartTypeLabel(template.chart_type)}
                          </div>
                        )}
                      </div>
                      
                      {/* Configuration Preview */}
                      <div className="mt-2 text-xs text-gray-400">
                        {template.config?.aggregation && (
                          <span className="mr-2">
                            Агрегация: {template.config.aggregation}
                          </span>
                        )}
                        {template.config?.time_range && (
                          <span>
                            Период: {template.config.time_range}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {/* Hover Effect */}
                  <div className="mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="text-xs text-blue-600 dark:text-blue-400">
                      Нажмите для добавления →
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 dark:border-gray-700">
          <div className="text-sm text-gray-500 dark:text-gray-400">
            Найдено виджетов: {filteredTemplates.length}
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  );
};

export default WidgetLibrary;