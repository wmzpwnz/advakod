import React, { useState, useEffect } from 'react';
import { 
  Brain, 
  BarChart3, 
  Download, 
  Upload, 
  Settings, 
  TrendingUp,
  Target,
  CheckCircle,
  AlertTriangle,
  Star
} from 'lucide-react';
import axios from 'axios';
import { getApiUrl } from '../config/api';

const LoRAManagement = ({ isVisible, onClose }) => {
  const [loraStatus, setLoraStatus] = useState(null);
  const [qualityStats, setQualityStats] = useState(null);
  const [trainingBatch, setTrainingBatch] = useState([]);
  const [priorityExamples, setPriorityExamples] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (isVisible) {
      loadLoRAStatus();
      loadQualityStatistics();
    }
  }, [isVisible]);

  const loadLoRAStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(getApiUrl('/api/v1/canary-lora/lora/status'), {
        headers: { Authorization: `Bearer ${token}` }
      });
      setLoraStatus(response.data.status);
    } catch (error) {
      console.error('Error loading LoRA status:', error);
      setMessage('Ошибка загрузки статуса LoRA');
    }
  };

  const loadQualityStatistics = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(getApiUrl('/api/v1/canary-lora/lora/quality-statistics'), {
        headers: { Authorization: `Bearer ${token}` }
      });
      setQualityStats(response.data.statistics);
    } catch (error) {
      console.error('Error loading quality statistics:', error);
      setMessage('Ошибка загрузки статистики качества');
    }
  };

  const loadTrainingBatch = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(getApiUrl('/api/v1/canary-lora/lora/training-batch'), {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTrainingBatch(response.data.batch);
      setMessage(`Загружено ${response.data.count} примеров для обучения`);
    } catch (error) {
      console.error('Error loading training batch:', error);
      setMessage('Ошибка загрузки батча для обучения');
    } finally {
      setLoading(false);
    }
  };

  const loadPriorityExamples = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(getApiUrl('/api/v1/canary-lora/lora/priority-examples'), {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPriorityExamples(response.data.examples);
      setMessage(`Загружено ${response.data.count} приоритетных примеров`);
    } catch (error) {
      console.error('Error loading priority examples:', error);
      setMessage('Ошибка загрузки приоритетных примеров');
    } finally {
      setLoading(false);
    }
  };

  const exportTrainingData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(getApiUrl('/api/v1/canary-lora/lora/export-data'), {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Создаем и скачиваем файл
      const blob = new Blob([response.data.data], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `training_data_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      setMessage('Данные для обучения экспортированы');
    } catch (error) {
      console.error('Error exporting training data:', error);
      setMessage('Ошибка экспорта данных');
    } finally {
      setLoading(false);
    }
  };

  const getQualityColor = (value, threshold = 0.6) => {
    if (value >= threshold) return 'text-green-600';
    if (value >= threshold * 0.8) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getPriorityColor = (priority) => {
    if (priority >= 0.8) return 'text-red-600 bg-red-100';
    if (priority >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-green-600 bg-green-100';
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <Brain className="w-6 h-6 text-purple-600" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              Управление LoRA обучением
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            ✕
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 dark:border-gray-700">
          <nav className="flex space-x-8 px-6">
            {[
              { id: 'overview', label: 'Обзор', icon: BarChart3 },
              { id: 'training', label: 'Обучение', icon: Brain },
              { id: 'examples', label: 'Примеры', icon: Target },
              { id: 'export', label: 'Экспорт', icon: Download }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-purple-500 text-purple-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <tab.icon className="w-4 h-4 mr-2" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Обзор */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Статус LoRA */}
              {loraStatus && (
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                  <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-4 flex items-center">
                    <Settings className="w-5 h-5 mr-2" />
                    Статус LoRA системы
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">{loraStatus.total_examples}</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">Всего примеров</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">{loraStatus.approved_examples}</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">Одобренных</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600">
                        {loraStatus.approved_examples > 0 ? Math.round((loraStatus.approved_examples / loraStatus.total_examples) * 100) : 0}%
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">Процент одобрения</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Статистика качества */}
              {qualityStats && (
                <div className="bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
                    <TrendingUp className="w-5 h-5 mr-2" />
                    Статистика качества
                  </h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-white dark:bg-gray-800 rounded-lg p-3">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Среднее качество</div>
                      <div className={`text-2xl font-bold ${getQualityColor(qualityStats.average_quality)}`}>
                        {(qualityStats.average_quality * 100).toFixed(1)}%
                      </div>
                    </div>
                    
                    <div className="bg-white dark:bg-gray-800 rounded-lg p-3">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Citation Recall</div>
                      <div className={`text-2xl font-bold ${getQualityColor(qualityStats.average_metrics?.citation_recall)}`}>
                        {((qualityStats.average_metrics?.citation_recall || 0) * 100).toFixed(1)}%
                      </div>
                    </div>
                    
                    <div className="bg-white dark:bg-gray-800 rounded-lg p-3">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Support Coverage</div>
                      <div className={`text-2xl font-bold ${getQualityColor(qualityStats.average_metrics?.support_coverage)}`}>
                        {((qualityStats.average_metrics?.support_coverage || 0) * 100).toFixed(1)}%
                      </div>
                    </div>
                    
                    <div className="bg-white dark:bg-gray-800 rounded-lg p-3">
                      <div className="text-sm text-gray-600 dark:text-gray-400">Hallucination Rate</div>
                      <div className={`text-2xl font-bold ${getQualityColor(1 - (qualityStats.average_metrics?.hallucination_score || 0), 0.7)}`}>
                        {((qualityStats.average_metrics?.hallucination_score || 0) * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>

                  {/* Распределение качества */}
                  <div className="mt-4">
                    <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Распределение качества</h4>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="text-center">
                        <div className="text-lg font-bold text-green-600">{qualityStats.quality_distribution?.high || 0}</div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Высокое (≥80%)</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-yellow-600">{qualityStats.quality_distribution?.medium || 0}</div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Среднее (60-79%)</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-red-600">{qualityStats.quality_distribution?.low || 0}</div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Низкое (&lt;60%)</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Обучение */}
          {activeTab === 'training' && (
            <div className="space-y-6">
              <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
                <h3 className="font-semibold text-purple-900 dark:text-purple-100 mb-4 flex items-center">
                  <Brain className="w-5 h-5 mr-2" />
                  Управление обучением
                </h3>
                
                <div className="space-y-4">
                  <button
                    onClick={loadTrainingBatch}
                    disabled={loading}
                    className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {loading ? 'Загрузка...' : 'Загрузить батч для обучения'}
                  </button>
                  
                  <button
                    onClick={loadPriorityExamples}
                    disabled={loading}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors ml-4"
                  >
                    {loading ? 'Загрузка...' : 'Загрузить приоритетные примеры'}
                  </button>
                </div>
              </div>

              {/* Батч для обучения */}
              {trainingBatch.length > 0 && (
                <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-4">
                    Батч для обучения ({trainingBatch.length} примеров)
                  </h4>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {trainingBatch.slice(0, 10).map((example, index) => (
                      <div key={example.id} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                        <div className="flex justify-between items-start mb-2">
                          <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                            {example.query.substring(0, 100)}...
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className={`px-2 py-1 rounded-full text-xs ${example.is_approved ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                              {example.is_approved ? 'Одобрен' : 'Не одобрен'}
                            </span>
                            <span className="text-xs text-gray-500">
                              Приоритет: {(example.priority * 100).toFixed(1)}%
                            </span>
                          </div>
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-400">
                          Качество: {(example.metrics.overall_quality * 100).toFixed(1)}% | 
                          Citation: {(example.metrics.citation_recall * 100).toFixed(1)}% | 
                          Hallucination: {(example.metrics.hallucination_score * 100).toFixed(1)}%
                        </div>
                      </div>
                    ))}
                    {trainingBatch.length > 10 && (
                      <div className="text-center text-sm text-gray-500">
                        ... и еще {trainingBatch.length - 10} примеров
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Примеры */}
          {activeTab === 'examples' && (
            <div className="space-y-6">
              {priorityExamples.length > 0 && (
                <div className="bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
                    <Star className="w-5 h-5 mr-2" />
                    Приоритетные примеры ({priorityExamples.length})
                  </h4>
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {priorityExamples.map((example, index) => (
                      <div key={example.id} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                        <div className="flex justify-between items-start mb-2">
                          <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                            {example.query.substring(0, 150)}...
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className={`px-2 py-1 rounded-full text-xs ${getPriorityColor(example.priority)}`}>
                              Приоритет: {(example.priority * 100).toFixed(1)}%
                            </span>
                            <span className={`px-2 py-1 rounded-full text-xs ${example.is_approved ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                              {example.is_approved ? 'Одобрен' : 'Не одобрен'}
                            </span>
                          </div>
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-400">
                          Качество: {(example.metrics.overall_quality * 100).toFixed(1)}% | 
                          Citation: {(example.metrics.citation_recall * 100).toFixed(1)}% | 
                          Удовлетворенность: {(example.metrics.user_satisfaction * 100).toFixed(1)}%
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Экспорт */}
          {activeTab === 'export' && (
            <div className="space-y-6">
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                <h3 className="font-semibold text-green-900 dark:text-green-100 mb-4 flex items-center">
                  <Download className="w-5 h-5 mr-2" />
                  Экспорт данных для обучения
                </h3>
                
                <div className="space-y-4">
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Экспортируйте одобренные примеры для обучения LoRA модели в формате JSON.
                  </p>
                  
                  <button
                    onClick={exportTrainingData}
                    disabled={loading}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {loading ? 'Экспорт...' : 'Экспортировать данные'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Сообщения */}
          {message && (
            <div className={`p-4 rounded-lg ${
              message.includes('успешно') || message.includes('загружено') || message.includes('экспортированы')
                ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-200'
                : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-200'
            }`}>
              {typeof message === 'string' ? message : (message.message || message.detail || 'Сообщение')}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LoRAManagement;
