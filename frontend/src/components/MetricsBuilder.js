import React, { useState, useEffect } from 'react';
import { 
  PlusIcon, 
  TrashIcon, 
  PencilIcon,
  BellIcon,
  ChartBarIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import LoadingSpinner from './LoadingSpinner';
import MetricCreateModal from './MetricCreateModal';
import MetricAlertModal from './MetricAlertModal';
import KPITemplatesModal from './KPITemplatesModal';

const MetricsBuilder = () => {
  const [customMetrics, setCustomMetrics] = useState([]);
  const [metricAlerts, setMetricAlerts] = useState([]);
  const [predefinedKPIs, setPredefinedKPIs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('metrics');
  
  // Модальные окна
  const [showCreateMetric, setShowCreateMetric] = useState(false);
  const [showCreateAlert, setShowCreateAlert] = useState(false);
  const [showKPITemplates, setShowKPITemplates] = useState(false);
  const [editingMetric, setEditingMetric] = useState(null);
  const [editingAlert, setEditingAlert] = useState(null);
  const [selectedMetricForAlert, setSelectedMetricForAlert] = useState(null);

  // Значения метрик
  const [metricValues, setMetricValues] = useState({});
  const [calculatingMetrics, setCalculatingMetrics] = useState(new Set());

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        loadCustomMetrics(),
        loadMetricAlerts(),
        loadPredefinedKPIs()
      ]);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const loadCustomMetrics = async () => {
    try {
      const response = await fetch('/api/v1/advanced-analytics/custom-metrics', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load custom metrics');
      }

      const data = await response.json();
      setCustomMetrics(data);

      // Загружаем значения метрик
      for (const metric of data) {
        calculateMetricValue(metric.id);
      }
    } catch (error) {
      console.error('Error loading custom metrics:', error);
      throw error;
    }
  };

  const loadMetricAlerts = async () => {
    try {
      const response = await fetch('/api/v1/advanced-analytics/metric-alerts', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load metric alerts');
      }

      const data = await response.json();
      setMetricAlerts(data);
    } catch (error) {
      console.error('Error loading metric alerts:', error);
      throw error;
    }
  };

  const loadPredefinedKPIs = async () => {
    try {
      const response = await fetch('/api/v1/advanced-analytics/predefined-kpis', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load predefined KPIs');
      }

      const data = await response.json();
      setPredefinedKPIs(data);
    } catch (error) {
      console.error('Error loading predefined KPIs:', error);
      throw error;
    }
  };

  const calculateMetricValue = async (metricId) => {
    try {
      setCalculatingMetrics(prev => new Set([...prev, metricId]));

      const response = await fetch(`/api/v1/advanced-analytics/custom-metrics/${metricId}/calculate`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to calculate metric value');
      }

      const data = await response.json();
      setMetricValues(prev => ({
        ...prev,
        [metricId]: data
      }));
    } catch (error) {
      console.error(`Error calculating metric ${metricId}:`, error);
      setMetricValues(prev => ({
        ...prev,
        [metricId]: {
          value: null,
          formatted_value: 'Ошибка',
          error: error.message
        }
      }));
    } finally {
      setCalculatingMetrics(prev => {
        const newSet = new Set(prev);
        newSet.delete(metricId);
        return newSet;
      });
    }
  };

  const handleCreateMetric = async (metricData) => {
    try {
      const response = await fetch('/api/v1/advanced-analytics/custom-metrics', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(metricData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create metric');
      }

      const newMetric = await response.json();
      setCustomMetrics(prev => [newMetric, ...prev]);
      setShowCreateMetric(false);
      
      // Вычисляем значение новой метрики
      calculateMetricValue(newMetric.id);
      
      toast.success('Метрика создана');
    } catch (error) {
      console.error('Error creating metric:', error);
      toast.error(error.message || 'Ошибка создания метрики');
    }
  };

  const handleUpdateMetric = async (metricId, metricData) => {
    try {
      const response = await fetch(`/api/v1/advanced-analytics/custom-metrics/${metricId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(metricData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update metric');
      }

      const updatedMetric = await response.json();
      setCustomMetrics(prev => prev.map(m => m.id === metricId ? updatedMetric : m));
      setEditingMetric(null);
      setShowCreateMetric(false);
      
      // Пересчитываем значение метрики
      calculateMetricValue(metricId);
      
      toast.success('Метрика обновлена');
    } catch (error) {
      console.error('Error updating metric:', error);
      toast.error(error.message || 'Ошибка обновления метрики');
    }
  };

  const handleDeleteMetric = async (metricId) => {
    if (!window.confirm('Удалить метрику? Все связанные алерты также будут удалены.')) return;

    try {
      const response = await fetch(`/api/v1/advanced-analytics/custom-metrics/${metricId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete metric');
      }

      setCustomMetrics(prev => prev.filter(m => m.id !== metricId));
      setMetricValues(prev => {
        const newValues = { ...prev };
        delete newValues[metricId];
        return newValues;
      });
      
      // Удаляем связанные алерты
      setMetricAlerts(prev => prev.filter(a => a.metric_id !== metricId));
      
      toast.success('Метрика удалена');
    } catch (error) {
      console.error('Error deleting metric:', error);
      toast.error('Ошибка удаления метрики');
    }
  };

  const handleCreateAlert = async (alertData) => {
    try {
      const response = await fetch('/api/v1/advanced-analytics/metric-alerts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(alertData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create alert');
      }

      const newAlert = await response.json();
      setMetricAlerts(prev => [newAlert, ...prev]);
      setShowCreateAlert(false);
      setSelectedMetricForAlert(null);
      
      toast.success('Алерт создан');
    } catch (error) {
      console.error('Error creating alert:', error);
      toast.error(error.message || 'Ошибка создания алерта');
    }
  };

  const handleUpdateAlert = async (alertId, alertData) => {
    try {
      const response = await fetch(`/api/v1/advanced-analytics/metric-alerts/${alertId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(alertData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update alert');
      }

      const updatedAlert = await response.json();
      setMetricAlerts(prev => prev.map(a => a.id === alertId ? updatedAlert : a));
      setEditingAlert(null);
      setShowCreateAlert(false);
      
      toast.success('Алерт обновлен');
    } catch (error) {
      console.error('Error updating alert:', error);
      toast.error(error.message || 'Ошибка обновления алерта');
    }
  };

  const handleDeleteAlert = async (alertId) => {
    if (!window.confirm('Удалить алерт?')) return;

    try {
      const response = await fetch(`/api/v1/advanced-analytics/metric-alerts/${alertId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete alert');
      }

      setMetricAlerts(prev => prev.filter(a => a.id !== alertId));
      toast.success('Алерт удален');
    } catch (error) {
      console.error('Error deleting alert:', error);
      toast.error('Ошибка удаления алерта');
    }
  };

  const handleCreateFromTemplate = async (template) => {
    try {
      const response = await fetch('/api/v1/advanced-analytics/custom-metrics/from-template', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(template)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create metric from template');
      }

      const newMetric = await response.json();
      setCustomMetrics(prev => [newMetric, ...prev]);
      setShowKPITemplates(false);
      
      // Вычисляем значение новой метрики
      calculateMetricValue(newMetric.id);
      
      toast.success('Метрика создана из шаблона');
    } catch (error) {
      console.error('Error creating metric from template:', error);
      toast.error(error.message || 'Ошибка создания метрики');
    }
  };

  const getMetricStatusColor = (metricId) => {
    const value = metricValues[metricId];
    if (!value) return 'text-gray-500';
    if (value.error) return 'text-red-500';
    return 'text-green-500';
  };

  const getAlertStatusColor = (alert) => {
    if (!alert.is_active) return 'text-gray-500';
    if (alert.last_triggered) {
      const lastTriggered = new Date(alert.last_triggered);
      const now = new Date();
      const hoursSinceTriggered = (now - lastTriggered) / (1000 * 60 * 60);
      
      if (hoursSinceTriggered < 24) return 'text-red-500';
      if (hoursSinceTriggered < 168) return 'text-yellow-500'; // 7 days
    }
    return 'text-green-500';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('ru-RU');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Пользовательские метрики и KPI
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Создание кастомных метрик и настройка алертов
            </p>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowKPITemplates(true)}
              className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors"
            >
              <ChartBarIcon className="h-4 w-4 mr-2" />
              Шаблоны KPI
            </button>
            
            <button
              onClick={() => setShowCreateMetric(true)}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              <PlusIcon className="h-4 w-4 mr-2" />
              Новая метрика
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="mt-6">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('metrics')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'metrics'
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              Метрики ({customMetrics.length})
            </button>
            <button
              onClick={() => setActiveTab('alerts')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'alerts'
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              Алерты ({metricAlerts.length})
            </button>
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'metrics' ? (
          /* Metrics Tab */
          <div>
            {customMetrics.length === 0 ? (
              <div className="text-center py-12">
                <ChartBarIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  Нет созданных метрик
                </h3>
                <p className="text-gray-500 dark:text-gray-400 mb-4">
                  Создайте первую метрику или используйте готовые шаблоны KPI
                </p>
                <div className="flex items-center justify-center space-x-3">
                  <button
                    onClick={() => setShowKPITemplates(true)}
                    className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
                  >
                    Шаблоны KPI
                  </button>
                  <button
                    onClick={() => setShowCreateMetric(true)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Создать метрику
                  </button>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {customMetrics.map(metric => {
                  const value = metricValues[metric.id];
                  const isCalculating = calculatingMetrics.has(metric.id);
                  
                  return (
                    <div
                      key={metric.id}
                      className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                          {metric.name}
                        </h3>
                        <div className="flex items-center space-x-1">
                          <button
                            onClick={() => calculateMetricValue(metric.id)}
                            disabled={isCalculating}
                            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                            title="Пересчитать"
                          >
                            <ClockIcon className={`h-4 w-4 ${isCalculating ? 'animate-spin' : ''}`} />
                          </button>
                          
                          <button
                            onClick={() => {
                              setSelectedMetricForAlert(metric);
                              setShowCreateAlert(true);
                            }}
                            className="p-1 text-gray-400 hover:text-yellow-600"
                            title="Создать алерт"
                          >
                            <BellIcon className="h-4 w-4" />
                          </button>
                          
                          <button
                            onClick={() => {
                              setEditingMetric(metric);
                              setShowCreateMetric(true);
                            }}
                            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                            title="Редактировать"
                          >
                            <PencilIcon className="h-4 w-4" />
                          </button>
                          
                          <button
                            onClick={() => handleDeleteMetric(metric.id)}
                            className="p-1 text-gray-400 hover:text-red-600"
                            title="Удалить"
                          >
                            <TrashIcon className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                      
                      {/* Metric Value */}
                      <div className="mb-4">
                        {isCalculating ? (
                          <div className="flex items-center justify-center h-16">
                            <LoadingSpinner size="sm" />
                          </div>
                        ) : (
                          <div className="text-center">
                            <div className={`text-3xl font-bold ${getMetricStatusColor(metric.id)}`}>
                              {value?.formatted_value || 'N/A'}
                            </div>
                            {value?.calculated_at && (
                              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                Обновлено: {new Date(value.calculated_at).toLocaleString()}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                      
                      {metric.description && (
                        <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
                          {metric.description}
                        </p>
                      )}
                      
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-500 dark:text-gray-400">Категория:</span>
                          <span className="text-gray-900 dark:text-white">{metric.category || 'Общая'}</span>
                        </div>
                        
                        <div className="flex justify-between">
                          <span className="text-gray-500 dark:text-gray-400">Формат:</span>
                          <span className="text-gray-900 dark:text-white">{metric.format_type}</span>
                        </div>
                        
                        {metric.tags && metric.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {metric.tags.map((tag, index) => (
                              <span
                                key={index}
                                className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                      
                      {value?.error && (
                        <div className="mt-3 p-2 bg-red-50 dark:bg-red-900/20 rounded text-xs text-red-600 dark:text-red-400">
                          Ошибка: {value.error}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ) : (
          /* Alerts Tab */
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white">
                Алерты метрик
              </h2>
              <button
                onClick={() => setShowCreateAlert(true)}
                className="flex items-center px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 transition-colors"
              >
                <BellIcon className="h-4 w-4 mr-2" />
                Новый алерт
              </button>
            </div>
            
            {metricAlerts.length === 0 ? (
              <div className="text-center py-12">
                <BellIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  Нет настроенных алертов
                </h3>
                <p className="text-gray-500 dark:text-gray-400 mb-4">
                  Создайте алерты для отслеживания важных метрик
                </p>
                <button
                  onClick={() => setShowCreateAlert(true)}
                  className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700"
                >
                  Создать алерт
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {metricAlerts.map(alert => {
                  const metric = customMetrics.find(m => m.id === alert.metric_id);
                  
                  return (
                    <div
                      key={alert.id}
                      className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3">
                            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                              {alert.name}
                            </h3>
                            
                            <div className={`flex items-center space-x-1 ${getAlertStatusColor(alert)}`}>
                              {alert.is_active ? (
                                alert.last_triggered ? (
                                  <ExclamationTriangleIcon className="h-4 w-4" />
                                ) : (
                                  <CheckCircleIcon className="h-4 w-4" />
                                )
                              ) : (
                                <ClockIcon className="h-4 w-4" />
                              )}
                              <span className="text-sm">
                                {alert.is_active ? 
                                  (alert.last_triggered ? 'Сработал' : 'Активен') : 
                                  'Неактивен'
                                }
                              </span>
                            </div>
                          </div>
                          
                          <div className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                            <div>Метрика: {metric?.name || 'Неизвестная метрика'}</div>
                            <div>
                              Условие: {alert.condition} {alert.threshold}
                              {metric?.unit && ` ${metric.unit}`}
                            </div>
                            {alert.last_triggered && (
                              <div>
                                Последнее срабатывание: {new Date(alert.last_triggered).toLocaleString()}
                              </div>
                            )}
                          </div>
                          
                          {alert.notification_channels.length > 0 && (
                            <div className="mt-2 flex flex-wrap gap-1">
                              {alert.notification_channels.map((channel, index) => (
                                <span
                                  key={index}
                                  className="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 rounded"
                                >
                                  {channel}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                        
                        <div className="flex items-center space-x-2 ml-4">
                          <button
                            onClick={() => {
                              setEditingAlert(alert);
                              setShowCreateAlert(true);
                            }}
                            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                            title="Редактировать"
                          >
                            <PencilIcon className="h-4 w-4" />
                          </button>
                          
                          <button
                            onClick={() => handleDeleteAlert(alert.id)}
                            className="p-2 text-gray-400 hover:text-red-600"
                            title="Удалить"
                          >
                            <TrashIcon className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modals */}
      {showCreateMetric && (
        <MetricCreateModal
          metric={editingMetric}
          onSave={editingMetric ? 
            (data) => handleUpdateMetric(editingMetric.id, data) : 
            handleCreateMetric
          }
          onClose={() => {
            setShowCreateMetric(false);
            setEditingMetric(null);
          }}
        />
      )}

      {showCreateAlert && (
        <MetricAlertModal
          alert={editingAlert}
          metrics={customMetrics}
          selectedMetric={selectedMetricForAlert}
          onSave={editingAlert ? 
            (data) => handleUpdateAlert(editingAlert.id, data) : 
            handleCreateAlert
          }
          onClose={() => {
            setShowCreateAlert(false);
            setEditingAlert(null);
            setSelectedMetricForAlert(null);
          }}
        />
      )}

      {showKPITemplates && (
        <KPITemplatesModal
          templates={predefinedKPIs}
          onSelectTemplate={handleCreateFromTemplate}
          onClose={() => setShowKPITemplates(false)}
        />
      )}
    </div>
  );
};

export default MetricsBuilder;