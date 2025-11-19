import React, { useState, useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

const WidgetConfigModal = ({ widget, dataSources, onSave, onClose }) => {
  const [formData, setFormData] = useState({
    widget_type: 'metric',
    title: '',
    data_source: '',
    config: {
      chart_type: 'line',
      aggregation: 'count',
      time_range: '24h',
      filters: {},
      refresh_interval: 300,
      color_scheme: 'default',
      show_legend: true,
      show_grid: true
    },
    position: {
      x: 0,
      y: 0,
      w: 4,
      h: 3
    },
    refresh_interval: 300
  });

  const [previewData, setPreviewData] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  useEffect(() => {
    if (widget) {
      setFormData({
        widget_type: widget.widget_type || 'metric',
        title: widget.title || '',
        data_source: widget.data_source || '',
        config: {
          chart_type: widget.config?.chart_type || 'line',
          aggregation: widget.config?.aggregation || 'count',
          time_range: widget.config?.time_range || '24h',
          filters: widget.config?.filters || {},
          refresh_interval: widget.config?.refresh_interval || 300,
          color_scheme: widget.config?.color_scheme || 'default',
          show_legend: widget.config?.show_legend !== false,
          show_grid: widget.config?.show_grid !== false,
          ...widget.config
        },
        position: widget.position || { x: 0, y: 0, w: 4, h: 3 },
        refresh_interval: widget.refresh_interval || 300
      });
    }
  }, [widget]);

  const handleInputChange = (field, value) => {
    if (field.startsWith('config.')) {
      const configField = field.replace('config.', '');
      setFormData(prev => ({
        ...prev,
        config: {
          ...prev.config,
          [configField]: value
        }
      }));
    } else if (field.startsWith('position.')) {
      const positionField = field.replace('position.', '');
      setFormData(prev => ({
        ...prev,
        position: {
          ...prev.position,
          [positionField]: parseInt(value) || 0
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [field]: value
      }));
    }
  };

  const handlePreview = async () => {
    if (!formData.data_source) {
      toast.error('Выберите источник данных');
      return;
    }

    try {
      setPreviewLoading(true);
      const response = await fetch('/api/v1/advanced-analytics/widgets/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          widget_type: formData.widget_type,
          title: formData.title,
          config: formData.config,
          data_source: formData.data_source
        })
      });

      if (!response.ok) {
        throw new Error('Failed to preview widget');
      }

      const data = await response.json();
      setPreviewData(data);
    } catch (error) {
      console.error('Error previewing widget:', error);
      toast.error('Ошибка предварительного просмотра');
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!formData.title.trim()) {
      toast.error('Введите название виджета');
      return;
    }

    if (!formData.data_source) {
      toast.error('Выберите источник данных');
      return;
    }

    onSave(formData);
  };

  const getDataSourceFields = () => {
    const source = dataSources.find(ds => ds.id === formData.data_source);
    return source?.fields || [];
  };

  const renderPreview = () => {
    if (previewLoading) {
      return (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      );
    }

    if (!previewData) {
      return (
        <div className="flex items-center justify-center h-32 text-gray-500">
          Нажмите "Предварительный просмотр" для отображения данных
        </div>
      );
    }

    if (formData.widget_type === 'metric') {
      const value = previewData.datasets?.[0]?.data?.[0] || 0;
      return (
        <div className="flex items-center justify-center h-32">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {typeof value === 'number' ? value.toLocaleString() : value}
            </div>
            <div className="text-sm text-gray-500">
              {previewData.datasets?.[0]?.label || 'Метрика'}
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="h-32 overflow-auto">
        <pre className="text-xs text-gray-600 dark:text-gray-400">
          {JSON.stringify(previewData, null, 2)}
        </pre>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            {widget ? 'Редактировать виджет' : 'Создать виджет'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <div className="flex h-[calc(90vh-120px)]">
          {/* Configuration Panel */}
          <div className="w-1/2 p-6 border-r border-gray-200 dark:border-gray-700 overflow-y-auto">
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Basic Settings */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Название виджета
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => handleInputChange('title', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Введите название виджета"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Тип виджета
                </label>
                <select
                  value={formData.widget_type}
                  onChange={(e) => handleInputChange('widget_type', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="metric">Метрика</option>
                  <option value="chart">График</option>
                  <option value="table">Таблица</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Источник данных
                </label>
                <select
                  value={formData.data_source}
                  onChange={(e) => handleInputChange('data_source', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="">Выберите источник данных</option>
                  {dataSources.map(source => (
                    <option key={source.id} value={source.id}>
                      {source.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Chart Type (only for chart widgets) */}
              {formData.widget_type === 'chart' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Тип графика
                  </label>
                  <select
                    value={formData.config.chart_type}
                    onChange={(e) => handleInputChange('config.chart_type', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  >
                    <option value="line">Линейный</option>
                    <option value="bar">Столбчатый</option>
                    <option value="pie">Круговая диаграмма</option>
                    <option value="area">Область</option>
                    <option value="scatter">Точечный</option>
                  </select>
                </div>
              )}

              {/* Data Configuration */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Агрегация
                </label>
                <select
                  value={formData.config.aggregation}
                  onChange={(e) => handleInputChange('config.aggregation', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="count">Количество</option>
                  <option value="sum">Сумма</option>
                  <option value="avg">Среднее</option>
                  <option value="min">Минимум</option>
                  <option value="max">Максимум</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Временной диапазон
                </label>
                <select
                  value={formData.config.time_range}
                  onChange={(e) => handleInputChange('config.time_range', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="1h">Последний час</option>
                  <option value="24h">Последние 24 часа</option>
                  <option value="7d">Последние 7 дней</option>
                  <option value="30d">Последние 30 дней</option>
                </select>
              </div>

              {/* Refresh Interval */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Интервал обновления (секунды)
                </label>
                <input
                  type="number"
                  min="30"
                  max="3600"
                  value={formData.refresh_interval}
                  onChange={(e) => handleInputChange('refresh_interval', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>

              {/* Position and Size */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Ширина (колонки)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="12"
                    value={formData.position.w}
                    onChange={(e) => handleInputChange('position.w', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Высота (строки)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="12"
                    value={formData.position.h}
                    onChange={(e) => handleInputChange('position.h', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
              </div>

              {/* Chart Options (only for chart widgets) */}
              {formData.widget_type === 'chart' && (
                <div className="space-y-3">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="show_legend"
                      checked={formData.config.show_legend}
                      onChange={(e) => handleInputChange('config.show_legend', e.target.checked)}
                      className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                    <label htmlFor="show_legend" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                      Показать легенду
                    </label>
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="show_grid"
                      checked={formData.config.show_grid}
                      onChange={(e) => handleInputChange('config.show_grid', e.target.checked)}
                      className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                    <label htmlFor="show_grid" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                      Показать сетку
                    </label>
                  </div>
                </div>
              )}
            </form>
          </div>

          {/* Preview Panel */}
          <div className="w-1/2 p-6">
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Предварительный просмотр
                </h3>
                <button
                  type="button"
                  onClick={handlePreview}
                  className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Обновить
                </button>
              </div>
              
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-gray-50 dark:bg-gray-900">
                {renderPreview()}
              </div>
            </div>

            {/* Data Source Info */}
            {formData.data_source && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Доступные поля
                </h4>
                <div className="text-xs text-gray-600 dark:text-gray-400 space-y-1">
                  {getDataSourceFields().map(field => (
                    <div key={field.name} className="flex justify-between">
                      <span>{field.name}</span>
                      <span className="text-gray-400">{field.type}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200 dark:border-gray-700">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            Отмена
          </button>
          <button
            onClick={handleSubmit}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            {widget ? 'Сохранить' : 'Создать'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default WidgetConfigModal;