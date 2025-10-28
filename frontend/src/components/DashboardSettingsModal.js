import React, { useState, useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

const DashboardSettingsModal = ({ dashboard, onSave, onClose }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    is_public: false,
    is_default: false
  });

  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (dashboard) {
      setFormData({
        name: dashboard.name || '',
        description: dashboard.description || '',
        is_public: dashboard.is_public || false,
        is_default: dashboard.is_default || false
      });
    }
  }, [dashboard]);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      toast.error('Введите название дашборда');
      return;
    }

    try {
      setLoading(true);

      if (dashboard) {
        // Обновление существующего дашборда
        const response = await fetch(`/api/v1/advanced-analytics/dashboards/${dashboard.id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify(formData)
        });

        if (!response.ok) {
          throw new Error('Failed to update dashboard');
        }

        toast.success('Дашборд обновлен');
      } else {
        // Создание нового дашборда
        if (onSave) {
          await onSave(formData);
        }
      }

      onClose();
    } catch (error) {
      console.error('Error saving dashboard:', error);
      toast.error('Ошибка сохранения дашборда');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!dashboard) return;

    if (!window.confirm('Вы уверены, что хотите удалить этот дашборд? Все виджеты будут также удалены.')) {
      return;
    }

    try {
      setLoading(true);

      const response = await fetch(`/api/v1/advanced-analytics/dashboards/${dashboard.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete dashboard');
      }

      toast.success('Дашборд удален');
      onClose();
      
      // Перезагружаем страницу для обновления списка дашбордов
      window.location.reload();
    } catch (error) {
      console.error('Error deleting dashboard:', error);
      toast.error('Ошибка удаления дашборда');
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
            {dashboard ? 'Настройки дашборда' : 'Создать дашборд'}
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
              Название дашборда *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Введите название дашборда"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Описание
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Описание дашборда (необязательно)"
            />
          </div>

          <div className="space-y-3">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="is_public"
                checked={formData.is_public}
                onChange={(e) => handleInputChange('is_public', e.target.checked)}
                className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="is_public" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                Публичный дашборд
              </label>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 ml-6">
              Публичные дашборды видны всем пользователям системы
            </p>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="is_default"
                checked={formData.is_default}
                onChange={(e) => handleInputChange('is_default', e.target.checked)}
                className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="is_default" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                Дашборд по умолчанию
              </label>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 ml-6">
              Этот дашборд будет открываться при входе в аналитику
            </p>
          </div>

          {/* Dashboard Info */}
          {dashboard && (
            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Информация о дашборде
              </h4>
              <div className="space-y-1 text-xs text-gray-500 dark:text-gray-400">
                <div>Создан: {new Date(dashboard.created_at).toLocaleString()}</div>
                <div>Обновлен: {new Date(dashboard.updated_at).toLocaleString()}</div>
                <div>Виджетов: {dashboard.widgets?.length || 0}</div>
              </div>
            </div>
          )}
        </form>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 dark:border-gray-700">
          <div>
            {dashboard && (
              <button
                type="button"
                onClick={handleDelete}
                disabled={loading}
                className="px-4 py-2 text-red-600 border border-red-300 rounded-md hover:bg-red-50 dark:hover:bg-red-900 disabled:opacity-50"
              >
                Удалить
              </button>
            )}
          </div>
          
          <div className="flex items-center space-x-3">
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
              disabled={loading || !formData.name.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center"
            >
              {loading && (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              )}
              {dashboard ? 'Сохранить' : 'Создать'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardSettingsModal;