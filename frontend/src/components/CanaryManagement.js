import React, { useState, useEffect } from 'react';
import { 
  Rocket, 
  CheckCircle, 
  AlertTriangle, 
  RotateCcw, 
  BarChart3, 
  Settings,
  Play,
  Pause,
  Trash2
} from 'lucide-react';
import axios from 'axios';
import { getApiUrl } from '../config/api';

const CanaryManagement = ({ isVisible, onClose }) => {
  const [canaryStatus, setCanaryStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [newModel, setNewModel] = useState({
    model_name: '',
    version: '',
    canary_percentage: 10,
    rollback_threshold: 0.7,
    evaluation_period_hours: 24
  });

  useEffect(() => {
    if (isVisible) {
      loadCanaryStatus();
    }
  }, [isVisible]);

  const loadCanaryStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(getApiUrl('/api/v1/canary-lora/canary/status'), {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCanaryStatus(response.data.status);
    } catch (error) {
      console.error('Error loading canary status:', error);
      setMessage('Ошибка загрузки статуса Canary');
    }
  };

  const deployCanary = async () => {
    if (!newModel.model_name || !newModel.version) {
      setMessage('Заполните название модели и версию');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(getApiUrl('/api/v1/canary-lora/canary/deploy'), {
        model_name: newModel.model_name,
        version: newModel.version,
        canary_percentage: newModel.canary_percentage,
        rollback_threshold: newModel.rollback_threshold,
        evaluation_period_hours: newModel.evaluation_period_hours
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setMessage(response.data.message);
      await loadCanaryStatus();
      setNewModel({
        model_name: '',
        version: '',
        canary_percentage: 10,
        rollback_threshold: 0.7,
        evaluation_period_hours: 24
      });
    } catch (error) {
      console.error('Error deploying canary:', error);
      setMessage('Ошибка развертывания Canary');
    } finally {
      setLoading(false);
    }
  };

  const promoteCanary = async (modelId) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(getApiUrl(`/api/v1/canary-lora/canary/promote/${modelId}`), {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setMessage(response.data.message);
      await loadCanaryStatus();
    } catch (error) {
      console.error('Error promoting canary:', error);
      setMessage('Ошибка продвижения Canary');
    } finally {
      setLoading(false);
    }
  };

  const rollbackCanary = async (modelId) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(getApiUrl(`/api/v1/canary-lora/canary/rollback/${modelId}`), {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setMessage(response.data.message);
      await loadCanaryStatus();
    } catch (error) {
      console.error('Error rolling back canary:', error);
      setMessage('Ошибка отката Canary');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-100';
      case 'canary': return 'text-blue-600 bg-blue-100';
      case 'deprecated': return 'text-gray-600 bg-gray-100';
      case 'failed': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return <CheckCircle className="w-4 h-4" />;
      case 'canary': return <Rocket className="w-4 h-4" />;
      case 'deprecated': return <Pause className="w-4 h-4" />;
      case 'failed': return <AlertTriangle className="w-4 h-4" />;
      default: return <Settings className="w-4 h-4" />;
    }
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <Rocket className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              Управление Canary-релизами
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Развертывание новой Canary-версии */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-4 flex items-center">
              <Rocket className="w-5 h-5 mr-2" />
              Развертывание новой Canary-версии
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Название модели
                </label>
                <input
                  type="text"
                  value={newModel.model_name}
                  onChange={(e) => setNewModel({...newModel, model_name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  placeholder="Saiga Mistral 7B"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Версия
                </label>
                <input
                  type="text"
                  value={newModel.version}
                  onChange={(e) => setNewModel({...newModel, version: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  placeholder="1.1.0"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Процент трафика (%)
                </label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={newModel.canary_percentage}
                  onChange={(e) => setNewModel({...newModel, canary_percentage: parseInt(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Порог отката
                </label>
                <input
                  type="number"
                  min="0.1"
                  max="1.0"
                  step="0.1"
                  value={newModel.rollback_threshold}
                  onChange={(e) => setNewModel({...newModel, rollback_threshold: parseFloat(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                />
              </div>
            </div>
            
            <button
              onClick={deployCanary}
              disabled={loading}
              className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Развертывание...' : 'Развернуть Canary'}
            </button>
          </div>

          {/* Статус моделей */}
          {canaryStatus && (
            <div className="space-y-4">
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 flex items-center">
                <BarChart3 className="w-5 h-5 mr-2" />
                Статус моделей
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(canaryStatus.models || {}).map(([modelId, model]) => (
                  <div key={modelId} className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-900 dark:text-gray-100">
                        {model.name} v{model.version}
                      </h4>
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(model.status)}`}>
                        {getStatusIcon(model.status)}
                        <span className="ml-1 capitalize">{model.status}</span>
                      </span>
                    </div>
                    
                    <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                      <div>Трафик: {model.canary_percentage}%</div>
                      <div>Создана: {new Date(model.created_at).toLocaleDateString()}</div>
                    </div>
                    
                    {model.status === 'canary' && (
                      <div className="mt-3 flex space-x-2">
                        <button
                          onClick={() => promoteCanary(modelId)}
                          disabled={loading}
                          className="flex-1 bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700 disabled:opacity-50 transition-colors"
                        >
                          <CheckCircle className="w-4 h-4 inline mr-1" />
                          Продвинуть
                        </button>
                        <button
                          onClick={() => rollbackCanary(modelId)}
                          disabled={loading}
                          className="flex-1 bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700 disabled:opacity-50 transition-colors"
                        >
                          <RotateCcw className="w-4 h-4 inline mr-1" />
                          Откатить
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Метрики Canary */}
          {canaryStatus && canaryStatus.canary_metrics && Object.keys(canaryStatus.canary_metrics).length > 0 && (
            <div className="bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
                <BarChart3 className="w-5 h-5 mr-2" />
                Метрики Canary-тестирования
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {Object.entries(canaryStatus.canary_metrics).map(([modelId, metrics]) => (
                  <div key={modelId} className="bg-white dark:bg-gray-800 rounded-lg p-3">
                    <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">
                      {canaryStatus.models[modelId]?.name || modelId}
                    </h4>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span>Запросов:</span>
                        <span>{metrics.total_requests}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Success Rate:</span>
                        <span className={metrics.success_rate >= 0.7 ? 'text-green-600' : 'text-red-600'}>
                          {(metrics.success_rate * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Response Time:</span>
                        <span>{metrics.avg_response_time.toFixed(2)}s</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Quality Score:</span>
                        <span className={metrics.quality_score >= 0.6 ? 'text-green-600' : 'text-red-600'}>
                          {(metrics.quality_score * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Сообщения */}
          {message && (
            <div className={`p-4 rounded-lg ${
              message.includes('успешно') || message.includes('развернута') 
                ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-200'
                : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-200'
            }`}>
              {message}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CanaryManagement;
