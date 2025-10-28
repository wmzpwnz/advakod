import React, { useState, useEffect } from 'react';
import { XMarkIcon, BellIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

const MetricAlertModal = ({ alert, metrics, selectedMetric, onSave, onClose }) => {
  const [formData, setFormData] = useState({
    metric_id: '',
    name: '',
    condition: 'gt',
    threshold: 0,
    notification_channels: [],
    is_active: true
  });

  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (alert) {
      setFormData({
        metric_id: alert.metric_id,
        name: alert.name || '',
        condition: alert.condition || 'gt',
        threshold: alert.threshold || 0,
        notification_channels: alert.notification_channels || [],
        is_active: alert.is_active !== false
      });
    } else if (selectedMetric) {
      setFormData(prev => ({
        ...prev,
        metric_id: selectedMetric.id,
        name: `Алерт для ${selectedMetric.name}`
      }));
    }
  }, [alert, selectedMetric]);

  const conditions = [
    { value: 'gt', label: 'Больше чем' },
    { value: 'lt', label: 'Меньше чем' },
    { value: 'eq', label: 'Равно' },
    { value: 'gte', label: 'Больше или равно' },
    { value: 'lte', label: 'Меньше или равно' }
  ];

  const notificationChannels = [
    { value: 'push', label: 'Push-уведомления', description: 'Уведомления в браузере' },
    { value: 'email', label: 'Email', description: 'Отправка на email' },
    { value: 'slack', label: 'Slack', description: 'Сообщения в Slack' },
    { value: 'telegram', label: 'Telegram', description: 'Сообщения в Telegram' }
  ];

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleChannelToggle = (channel) => {
    setFormData(prev => ({
      ...prev,
      notification_channels: prev.notification_channels.includes(channel)
        ? prev.notification_channels.filter(c => c !== channel)
        : [...prev.notification_channels, channel]
    }));
  };

  const getSelectedMetric = () => {
    return metrics.find(m => m.id === parseInt(formData.metric_id));
  };

  const getConditionDescription = () => {
    const metric = getSelectedMetric();
    const conditionLabel = conditions.find(c => c.value === formData.condition)?.label || '';
    const unit = metric?.unit || '';
    
    return `Срабатывает когда значение метрики ${conditionLabel.toLowerCase()} ${formData.threshold}${unit ? ` ${unit}` : ''}`;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      toast.error('Введите название алерта');
      return;
    }

    if (!formData.metric_id) {
      toast.error('Выберите метрику');
      return;
    }

    if (formData.notification_channels.length === 0) {
      toast.error('Выберите хотя бы один канал уведомлений');
      return;
    }

    try {
      setLoading(true);
      
      const submitData = {
        ...formData,
        metric_id: parseInt(formData.metric_id),
        threshold: parseFloat(formData.threshold)
      };

      await onSave(submitData);
    } catch (error) {
      console.error('Error saving alert:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            {alert ? 'Редактировать алерт' : 'Создать алерт'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Название алерта *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Например: Высокая нагрузка на систему"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Метрика *
            </label>
            <select
              value={formData.metric_id}
              onChange={(e) => handleInputChange('metric_id', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              required
            >
              <option value="">Выберите метрику</option>
              {metrics.map(metric => (
                <option key={metric.id} value={metric.id}>
                  {metric.name} {metric.unit && `(${metric.unit})`}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Условие *
              </label>
              <select
                value={formData.condition}
                onChange={(e) => handleInputChange('condition', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                {conditions.map(condition => (
                  <option key={condition.value} value={condition.value}>
                    {condition.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Пороговое значение *
              </label>
              <input
                type="number"
                step="any"
                value={formData.threshold}
                onChange={(e) => handleInputChange('threshold', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                required
              />
            </div>
          </div>

          {/* Condition Description */}
          {formData.metric_id && (
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                {getConditionDescription()}
              </p>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Каналы уведомлений *
            </label>
            <div className="space-y-3">
              {notificationChannels.map(channel => (
                <div key={channel.value} className="flex items-start">
                  <input
                    type="checkbox"
                    id={channel.value}
                    checked={formData.notification_channels.includes(channel.value)}
                    onChange={() => handleChannelToggle(channel.value)}
                    className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 mt-1"
                  />
                  <div className="ml-3">
                    <label htmlFor={channel.value} className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      {channel.label}
                    </label>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {channel.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) => handleInputChange('is_active', e.target.checked)}
              className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label htmlFor="is_active" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Активный алерт
            </label>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 ml-6">
            Неактивные алерты не проверяются и не отправляют уведомления
          </p>

          {/* Alert Info */}
          <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
            <div className="flex items-start space-x-2">
              <BellIcon className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-yellow-900 dark:text-yellow-100 mb-1">
                  Как работают алерты?
                </h4>
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  Алерты проверяются автоматически каждые 5 минут. При срабатывании условия 
                  уведомления отправляются по выбранным каналам.
                </p>
              </div>
            </div>
          </div>
        </form>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200 dark:border-gray-700">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
          >
            Отмена
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading || !formData.name.trim() || !formData.metric_id || formData.notification_channels.length === 0}
            className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 disabled:opacity-50 flex items-center"
          >
            {loading && (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
            )}
            {alert ? 'Сохранить' : 'Создать алерт'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default MetricAlertModal;