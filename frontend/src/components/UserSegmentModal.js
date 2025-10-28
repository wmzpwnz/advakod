import React, { useState, useEffect } from 'react';
import { XMarkIcon, PlusIcon, TrashIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

const UserSegmentModal = ({ segment, onSave, onClose }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    criteria: [],
    is_dynamic: true
  });

  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (segment) {
      setFormData({
        name: segment.name || '',
        description: segment.description || '',
        criteria: segment.criteria || [],
        is_dynamic: segment.is_dynamic !== false
      });
    }
  }, [segment]);

  const availableFields = [
    { name: 'email', label: 'Email', type: 'string' },
    { name: 'username', label: 'Имя пользователя', type: 'string' },
    { name: 'is_active', label: 'Активен', type: 'boolean' },
    { name: 'is_premium', label: 'Премиум', type: 'boolean' },
    { name: 'subscription_type', label: 'Тип подписки', type: 'string' },
    { name: 'created_at', label: 'Дата регистрации', type: 'datetime' },
    { name: 'company_name', label: 'Название компании', type: 'string' },
    { name: 'legal_form', label: 'Правовая форма', type: 'string' }
  ];

  const operatorOptions = {
    string: [
      { value: 'eq', label: 'Равно' },
      { value: 'ne', label: 'Не равно' },
      { value: 'contains', label: 'Содержит' },
      { value: 'in', label: 'В списке' },
      { value: 'not_in', label: 'Не в списке' }
    ],
    boolean: [
      { value: 'eq', label: 'Равно' }
    ],
    datetime: [
      { value: 'gt', label: 'Позже' },
      { value: 'lt', label: 'Раньше' },
      { value: 'gte', label: 'Позже или равно' },
      { value: 'lte', label: 'Раньше или равно' }
    ],
    number: [
      { value: 'eq', label: 'Равно' },
      { value: 'ne', label: 'Не равно' },
      { value: 'gt', label: 'Больше' },
      { value: 'lt', label: 'Меньше' },
      { value: 'gte', label: 'Больше или равно' },
      { value: 'lte', label: 'Меньше или равно' }
    ]
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleCriteriaChange = (index, field, value) => {
    const newCriteria = [...formData.criteria];
    newCriteria[index] = {
      ...newCriteria[index],
      [field]: value
    };

    // Сбрасываем значение при изменении поля или оператора
    if (field === 'field' || field === 'operator') {
      newCriteria[index].value = '';
    }

    setFormData(prev => ({
      ...prev,
      criteria: newCriteria
    }));
  };

  const addCriteria = () => {
    setFormData(prev => ({
      ...prev,
      criteria: [
        ...prev.criteria,
        {
          field: 'is_active',
          operator: 'eq',
          value: true
        }
      ]
    }));
  };

  const removeCriteria = (index) => {
    setFormData(prev => ({
      ...prev,
      criteria: prev.criteria.filter((_, i) => i !== index)
    }));
  };

  const getFieldType = (fieldName) => {
    const field = availableFields.find(f => f.name === fieldName);
    return field?.type || 'string';
  };

  const renderValueInput = (criteria, index) => {
    const fieldType = getFieldType(criteria.field);
    const operator = criteria.operator;

    if (fieldType === 'boolean') {
      return (
        <select
          value={criteria.value}
          onChange={(e) => handleCriteriaChange(index, 'value', e.target.value === 'true')}
          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        >
          <option value="true">Да</option>
          <option value="false">Нет</option>
        </select>
      );
    }

    if (fieldType === 'datetime') {
      return (
        <input
          type="date"
          value={criteria.value}
          onChange={(e) => handleCriteriaChange(index, 'value', e.target.value)}
          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        />
      );
    }

    if (operator === 'in' || operator === 'not_in') {
      return (
        <input
          type="text"
          value={Array.isArray(criteria.value) ? criteria.value.join(', ') : criteria.value}
          onChange={(e) => {
            const values = e.target.value.split(',').map(v => v.trim()).filter(v => v);
            handleCriteriaChange(index, 'value', values);
          }}
          placeholder="Значения через запятую"
          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        />
      );
    }

    // Предустановленные значения для некоторых полей
    if (criteria.field === 'subscription_type') {
      return (
        <select
          value={criteria.value}
          onChange={(e) => handleCriteriaChange(index, 'value', e.target.value)}
          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        >
          <option value="">Выберите тип</option>
          <option value="free">Бесплатная</option>
          <option value="basic">Базовая</option>
          <option value="premium">Премиум</option>
        </select>
      );
    }

    if (criteria.field === 'legal_form') {
      return (
        <select
          value={criteria.value}
          onChange={(e) => handleCriteriaChange(index, 'value', e.target.value)}
          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
        >
          <option value="">Выберите форму</option>
          <option value="ИП">ИП</option>
          <option value="ООО">ООО</option>
          <option value="АО">АО</option>
          <option value="ПАО">ПАО</option>
        </select>
      );
    }

    return (
      <input
        type="text"
        value={criteria.value}
        onChange={(e) => handleCriteriaChange(index, 'value', e.target.value)}
        placeholder="Введите значение"
        className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
      />
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      toast.error('Введите название сегмента');
      return;
    }

    if (formData.criteria.length === 0) {
      toast.error('Добавьте хотя бы один критерий');
      return;
    }

    // Проверяем, что все критерии заполнены
    for (let i = 0; i < formData.criteria.length; i++) {
      const criteria = formData.criteria[i];
      if (!criteria.field || !criteria.operator || (criteria.value === '' || criteria.value === null || criteria.value === undefined)) {
        toast.error(`Заполните все поля в критерии ${i + 1}`);
        return;
      }
    }

    try {
      setLoading(true);
      await onSave(formData);
    } catch (error) {
      console.error('Error saving user segment:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            {segment ? 'Редактировать сегмент' : 'Создать сегмент пользователей'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Form */}
        <div className="overflow-y-auto max-h-[calc(90vh-120px)]">
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Название сегмента *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="Например: Активные премиум пользователи"
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
                placeholder="Описание сегмента (необязательно)"
              />
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="is_dynamic"
                checked={formData.is_dynamic}
                onChange={(e) => handleInputChange('is_dynamic', e.target.checked)}
                className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="is_dynamic" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                Динамический сегмент
              </label>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 ml-6">
              Динамические сегменты автоматически обновляются при изменении данных пользователей
            </p>

            {/* Criteria */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Критерии сегментации *
                </label>
                <button
                  type="button"
                  onClick={addCriteria}
                  className="flex items-center px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  <PlusIcon className="h-4 w-4 mr-1" />
                  Добавить критерий
                </button>
              </div>

              {formData.criteria.length === 0 ? (
                <div className="text-center py-8 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
                  <p className="text-gray-500 dark:text-gray-400 mb-2">
                    Нет критериев сегментации
                  </p>
                  <button
                    type="button"
                    onClick={addCriteria}
                    className="text-blue-600 hover:text-blue-800 text-sm"
                  >
                    Добавить первый критерий
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  {formData.criteria.map((criteria, index) => (
                    <div key={index} className="flex items-center space-x-3 p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                      <div className="flex-1 grid grid-cols-3 gap-3">
                        {/* Field */}
                        <select
                          value={criteria.field}
                          onChange={(e) => handleCriteriaChange(index, 'field', e.target.value)}
                          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        >
                          {availableFields.map(field => (
                            <option key={field.name} value={field.name}>
                              {field.label}
                            </option>
                          ))}
                        </select>

                        {/* Operator */}
                        <select
                          value={criteria.operator}
                          onChange={(e) => handleCriteriaChange(index, 'operator', e.target.value)}
                          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        >
                          {operatorOptions[getFieldType(criteria.field)]?.map(op => (
                            <option key={op.value} value={op.value}>
                              {op.label}
                            </option>
                          ))}
                        </select>

                        {/* Value */}
                        {renderValueInput(criteria, index)}
                      </div>

                      <button
                        type="button"
                        onClick={() => removeCriteria(index)}
                        className="p-2 text-gray-400 hover:text-red-600"
                        title="Удалить критерий"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Info */}
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
              <h4 className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">
                Как работают критерии?
              </h4>
              <p className="text-sm text-blue-800 dark:text-blue-200">
                Все критерии объединяются логическим оператором "И" (AND). 
                Пользователь попадет в сегмент только если соответствует всем указанным критериям.
              </p>
            </div>
          </form>
        </div>

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
            disabled={loading || !formData.name.trim() || formData.criteria.length === 0}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center"
          >
            {loading && (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
            )}
            {segment ? 'Сохранить' : 'Создать сегмент'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default UserSegmentModal;