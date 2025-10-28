import React, { useState, useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

const CohortCreateModal = ({ onSave, onClose }) => {
  const [formData, setFormData] = useState({
    name: '',
    cohort_type: 'registration',
    period_type: 'monthly',
    start_date: '',
    end_date: ''
  });

  const [cohortTypes, setCohortTypes] = useState({});
  const [periodTypes, setPeriodTypes] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadConfigurationData();
    
    // Устанавливаем дефолтные даты
    const endDate = new Date();
    const startDate = new Date();
    startDate.setMonth(startDate.getMonth() - 6); // 6 месяцев назад
    
    setFormData(prev => ({
      ...prev,
      start_date: startDate.toISOString().split('T')[0],
      end_date: endDate.toISOString().split('T')[0]
    }));
  }, []);

  const loadConfigurationData = async () => {
    try {
      const [cohortTypesResponse, periodTypesResponse] = await Promise.all([
        fetch('/api/v1/advanced-analytics/cohort-types', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }),
        fetch('/api/v1/advanced-analytics/period-types', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        })
      ]);

      if (cohortTypesResponse.ok) {
        const cohortTypesData = await cohortTypesResponse.json();
        setCohortTypes(cohortTypesData);
      }

      if (periodTypesResponse.ok) {
        const periodTypesData = await periodTypesResponse.json();
        setPeriodTypes(periodTypesData);
      }
    } catch (error) {
      console.error('Error loading configuration data:', error);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      toast.error('Введите название анализа');
      return;
    }

    if (!formData.start_date || !formData.end_date) {
      toast.error('Выберите период анализа');
      return;
    }

    if (new Date(formData.start_date) >= new Date(formData.end_date)) {
      toast.error('Дата начала должна быть раньше даты окончания');
      return;
    }

    try {
      setLoading(true);
      
      const submitData = {
        ...formData,
        start_date: new Date(formData.start_date).toISOString(),
        end_date: new Date(formData.end_date).toISOString()
      };

      await onSave(submitData);
    } catch (error) {
      console.error('Error creating cohort analysis:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCohortTypeDescription = (type) => {
    const descriptions = {
      'registration': 'Анализ удержания пользователей с момента регистрации',
      'first_purchase': 'Анализ удержания пользователей с момента первой покупки',
      'first_query': 'Анализ удержания пользователей с момента первого запроса к ИИ',
      'subscription': 'Анализ удержания пользователей с момента оформления подписки'
    };
    return descriptions[type] || '';
  };

  const getPeriodTypeDescription = (type) => {
    const descriptions = {
      'daily': 'Группировка пользователей по дням',
      'weekly': 'Группировка пользователей по неделям',
      'monthly': 'Группировка пользователей по месяцам'
    };
    return descriptions[type] || '';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Создать когортный анализ
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
              Название анализа *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Например: Анализ удержания за Q4 2024"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Тип когорты *
            </label>
            <select
              value={formData.cohort_type}
              onChange={(e) => handleInputChange('cohort_type', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              {Object.entries(cohortTypes).map(([key, value]) => (
                <option key={key} value={key}>
                  {value}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {getCohortTypeDescription(formData.cohort_type)}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Период группировки *
            </label>
            <select
              value={formData.period_type}
              onChange={(e) => handleInputChange('period_type', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              {Object.entries(periodTypes).map(([key, value]) => (
                <option key={key} value={key}>
                  {value}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {getPeriodTypeDescription(formData.period_type)}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Дата начала *
              </label>
              <input
                type="date"
                value={formData.start_date}
                onChange={(e) => handleInputChange('start_date', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Дата окончания *
              </label>
              <input
                type="date"
                value={formData.end_date}
                onChange={(e) => handleInputChange('end_date', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                required
              />
            </div>
          </div>

          {/* Info Box */}
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
            <h4 className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">
              Что такое когортный анализ?
            </h4>
            <p className="text-sm text-blue-800 dark:text-blue-200">
              Когортный анализ помогает понять, как изменяется поведение пользователей со временем. 
              Он группирует пользователей по времени их первого действия (регистрация, покупка и т.д.) 
              и отслеживает их активность в последующие периоды.
            </p>
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
            disabled={loading || !formData.name.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center"
          >
            {loading && (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
            )}
            Создать анализ
          </button>
        </div>
      </div>
    </div>
  );
};

export default CohortCreateModal;