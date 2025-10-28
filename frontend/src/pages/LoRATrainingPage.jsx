import React, { useState, useEffect } from 'react';
import { 
  Play, 
  Pause, 
  CheckCircle, 
  XCircle, 
  Star, 
  Filter, 
  Download, 
  Upload,
  Settings,
  BarChart3,
  Clock,
  AlertCircle,
  CheckSquare,
  Square,
  Database,
  RefreshCw
} from 'lucide-react';

const LoRATrainingPage = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [trainingData, setTrainingData] = useState([]);
  const [stats, setStats] = useState({});
  const [selectedData, setSelectedData] = useState([]);
  const [filters, setFilters] = useState({
    complexity: 'all',
    approved: 'all',
    quality: 'all'
  });
  const [isLoading, setIsLoading] = useState(false);

  // Загрузка данных
  useEffect(() => {
    loadStats();
    loadTrainingData();
  }, []);

  const loadStats = async () => {
    try {
      const response = await fetch('/api/lora/data/stats?days=7');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Ошибка загрузки статистики:', error);
    }
  };

  const loadTrainingData = async () => {
    try {
      setIsLoading(true);
      const params = new URLSearchParams();
      if (filters.complexity !== 'all') params.append('complexity', filters.complexity);
      if (filters.approved !== 'all') params.append('approved_only', filters.approved === 'approved');
      
      const response = await fetch(`/api/lora/data?${params}`);
      const data = await response.json();
      setTrainingData(data);
    } catch (error) {
      console.error('Ошибка загрузки данных:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const collectData = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/lora/data/collect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          limit: 1000,
          days_back: 30,
          collection_type: 'auto'
        })
      });
      const result = await response.json();
      
      if (result.error) {
        alert(`Ошибка сбора данных: ${result.error}`);
      } else {
        alert(`Собрано ${result.total_processed} диалогов, одобрено ${result.total_approved}`);
        loadStats();
        loadTrainingData();
      }
    } catch (error) {
      console.error('Ошибка сбора данных:', error);
      alert('Ошибка сбора данных');
    } finally {
      setIsLoading(false);
    }
  };

  const approveData = async (dataId) => {
    try {
      const response = await fetch(`/api/lora/data/${dataId}/approve`, {
        method: 'POST'
      });
      
      if (response.ok) {
        loadTrainingData();
        loadStats();
      }
    } catch (error) {
      console.error('Ошибка одобрения:', error);
    }
  };

  const rejectData = async (dataId) => {
    try {
      const response = await fetch(`/api/lora/data/${dataId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: 'Не соответствует требованиям' })
      });
      
      if (response.ok) {
        loadTrainingData();
        loadStats();
      }
    } catch (error) {
      console.error('Ошибка отклонения:', error);
    }
  };

  const batchApprove = async () => {
    if (selectedData.length === 0) return;
    
    try {
      const response = await fetch('/api/lora/data/batch-approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data_ids: selectedData,
          approve: true
        })
      });
      
      const result = await response.json();
      alert(`Обработано: ${result.processed}, одобрено: ${result.approved}`);
      
      setSelectedData([]);
      loadTrainingData();
      loadStats();
    } catch (error) {
      console.error('Ошибка пакетного одобрения:', error);
    }
  };

  const toggleDataSelection = (dataId) => {
    setSelectedData(prev => 
      prev.includes(dataId) 
        ? prev.filter(id => id !== dataId)
        : [...prev, dataId]
    );
  };

  const selectAll = () => {
    setSelectedData(trainingData.map(item => item.id));
  };

  const deselectAll = () => {
    setSelectedData([]);
  };

  const getComplexityColor = (complexity) => {
    switch (complexity) {
      case 'simple': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'complex': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getQualityStars = (score) => {
    const stars = [];
    const fullStars = Math.floor(score || 0);
    const hasHalfStar = (score || 0) % 1 >= 0.5;
    
    for (let i = 0; i < 5; i++) {
      if (i < fullStars) {
        stars.push(<Star key={i} className="w-4 h-4 text-yellow-400 fill-current" />);
      } else if (i === fullStars && hasHalfStar) {
        stars.push(<Star key={i} className="w-4 h-4 text-yellow-400 fill-current opacity-50" />);
      } else {
        stars.push(<Star key={i} className="w-4 h-4 text-gray-300" />);
      }
    }
    return stars;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Заголовок */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <h1 className="text-3xl font-bold text-gray-900">🎯 Обучение модели LoRA</h1>
            <p className="mt-2 text-gray-600">Полуавтоматический режим сбора и обучения данных</p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Навигация */}
        <div className="mb-8">
          <nav className="flex space-x-8">
            {[
              { id: 'dashboard', name: 'Дашборд', icon: BarChart3 },
              { id: 'data', name: 'Данные', icon: Database },
              { id: 'training', name: 'Обучение', icon: Play },
              { id: 'models', name: 'Модели', icon: Settings }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium ${
                  activeTab === tab.id
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                <span>{tab.name}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Дашборд */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* Статистика */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Database className="w-6 h-6 text-blue-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Всего данных</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.total_data || 0}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <CheckCircle className="w-6 h-6 text-green-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Одобрено</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.approved_data || 0}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="p-2 bg-yellow-100 rounded-lg">
                    <Clock className="w-6 h-6 text-yellow-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Ожидает проверки</p>
                    <p className="text-2xl font-bold text-gray-900">{stats.pending_data || 0}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <BarChart3 className="w-6 h-6 text-purple-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Процент одобрения</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {Math.round(stats.approval_rate || 0)}%
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Быстрые действия */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Быстрые действия</h3>
              <div className="flex flex-wrap gap-4">
                <button
                  onClick={collectData}
                  disabled={isLoading}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  <Download className="w-4 h-4" />
                  <span>Собрать данные</span>
                </button>

                <button
                  onClick={loadTrainingData}
                  disabled={isLoading}
                  className="flex items-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span>Обновить</span>
                </button>

                <button
                  onClick={batchApprove}
                  disabled={selectedData.length === 0}
                  className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  <CheckSquare className="w-4 h-4" />
                  <span>Одобрить выбранные ({selectedData.length})</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Управление данными */}
        {activeTab === 'data' && (
          <div className="space-y-6">
            {/* Фильтры */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Фильтры</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Сложность
                  </label>
                  <select
                    value={filters.complexity}
                    onChange={(e) => setFilters({...filters, complexity: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">Все</option>
                    <option value="simple">Простые</option>
                    <option value="medium">Средние</option>
                    <option value="complex">Сложные</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Статус
                  </label>
                  <select
                    value={filters.approved}
                    onChange={(e) => setFilters({...filters, approved: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">Все</option>
                    <option value="approved">Одобренные</option>
                    <option value="pending">Ожидающие</option>
                  </select>
                </div>

                <div className="flex items-end">
                  <button
                    onClick={loadTrainingData}
                    className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Применить фильтры
                  </button>
                </div>
              </div>
            </div>

            {/* Список данных */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">Данные для обучения</h3>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={selectAll}
                      className="text-sm text-blue-600 hover:text-blue-700"
                    >
                      Выбрать все
                    </button>
                    <span className="text-gray-300">|</span>
                    <button
                      onClick={deselectAll}
                      className="text-sm text-blue-600 hover:text-blue-700"
                    >
                      Снять выбор
                    </button>
                  </div>
                </div>
              </div>

              <div className="divide-y divide-gray-200">
                {isLoading ? (
                  <div className="p-8 text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-2 text-gray-600">Загрузка данных...</p>
                  </div>
                ) : trainingData.length === 0 ? (
                  <div className="p-8 text-center text-gray-500">
                    <Database className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                    <p>Нет данных для отображения</p>
                  </div>
                ) : (
                  trainingData.map((item) => (
                    <div key={item.id} className="p-6 hover:bg-gray-50">
                      <div className="flex items-start space-x-4">
                        <div className="flex-shrink-0">
                          <input
                            type="checkbox"
                            checked={selectedData.includes(item.id)}
                            onChange={() => toggleDataSelection(item.id)}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                        </div>

                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center space-x-2">
                              <span className={`px-2 py-1 text-xs font-medium rounded-full ${getComplexityColor(item.complexity)}`}>
                                {item.complexity || 'unknown'}
                              </span>
                              <div className="flex items-center space-x-1">
                                {getQualityStars(item.quality_score)}
                                <span className="text-sm text-gray-500">
                                  {item.quality_score ? item.quality_score.toFixed(1) : 'N/A'}
                                </span>
                              </div>
                            </div>

                            <div className="flex items-center space-x-2">
                              {item.is_approved ? (
                                <span className="inline-flex items-center px-2 py-1 text-xs font-medium text-green-800 bg-green-100 rounded-full">
                                  <CheckCircle className="w-3 h-3 mr-1" />
                                  Одобрено
                                </span>
                              ) : (
                                <span className="inline-flex items-center px-2 py-1 text-xs font-medium text-yellow-800 bg-yellow-100 rounded-full">
                                  <Clock className="w-3 h-3 mr-1" />
                                  Ожидает
                                </span>
                              )}
                            </div>
                          </div>

                          <div className="mb-3">
                            <p className="text-sm font-medium text-gray-900 mb-1">
                              <strong>Вопрос:</strong> {item.instruction}
                            </p>
                            <p className="text-sm text-gray-600">
                              <strong>Ответ:</strong> {item.output.substring(0, 200)}
                              {item.output.length > 200 && '...'}
                            </p>
                          </div>

                          <div className="flex items-center justify-between">
                            <div className="text-xs text-gray-500">
                              Источник: {item.source} • Создано: {new Date(item.created_at).toLocaleDateString()}
                            </div>

                            <div className="flex items-center space-x-2">
                              {!item.is_approved && (
                                <>
                                  <button
                                    onClick={() => approveData(item.id)}
                                    className="inline-flex items-center px-3 py-1 text-xs font-medium text-green-700 bg-green-100 rounded-md hover:bg-green-200"
                                  >
                                    <CheckCircle className="w-3 h-3 mr-1" />
                                    Одобрить
                                  </button>
                                  <button
                                    onClick={() => rejectData(item.id)}
                                    className="inline-flex items-center px-3 py-1 text-xs font-medium text-red-700 bg-red-100 rounded-md hover:bg-red-200"
                                  >
                                    <XCircle className="w-3 h-3 mr-1" />
                                    Отклонить
                                  </button>
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* Обучение */}
        {activeTab === 'training' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Запуск обучения</h3>
              <p className="text-gray-600 mb-4">
                Настройте параметры и запустите обучение модели LoRA
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Название задачи
                  </label>
                  <input
                    type="text"
                    placeholder="Например: Обучение v1.1.0"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Количество эпох
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    defaultValue="3"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="mt-6">
                <button className="flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  <Play className="w-4 h-4" />
                  <span>Запустить обучение</span>
                </button>
              </div>
            </div>

            {/* Активные задачи */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Активные задачи обучения</h3>
              </div>
              <div className="p-6">
                <p className="text-gray-500 text-center">Нет активных задач обучения</p>
              </div>
            </div>
          </div>
        )}

        {/* Модели */}
        {activeTab === 'models' && (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Управление моделями</h3>
              <p className="text-gray-600 mb-4">
                Просматривайте и управляйте версиями моделей
              </p>
              
              <div className="mt-6">
                <button className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  <Upload className="w-4 h-4" />
                  <span>Создать новую версию</span>
                </button>
              </div>
            </div>

            {/* Список моделей */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900">Версии моделей</h3>
              </div>
              <div className="p-6">
                <p className="text-gray-500 text-center">Нет доступных моделей</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LoRATrainingPage;
