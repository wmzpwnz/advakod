import React, { useState, useEffect } from 'react';
import { 
  Brain, 
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
  TrendingUp,
  Activity,
  RefreshCw
} from 'lucide-react';
import axios from 'axios';
import { getApiUrl } from '../config/api';

const LoRAManagement = () => {
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
  const [error, setError] = useState('');

  // Загрузка данных
  useEffect(() => {
    loadStats();
    loadTrainingData();
  }, []);

  const loadStats = async () => {
    try {
      const response = await axios.get(getApiUrl('/lora/data/stats?days=7'));
      setStats(response.data);
    } catch (error) {
      console.error('Ошибка загрузки статистики:', error);
      // Устанавливаем заглушку статистики
      setStats({
        total_data: 0,
        approved_data: 0,
        pending_data: 0,
        quality_score: 0
      });
    }
  };

  const loadTrainingData = async () => {
    try {
      setIsLoading(true);
      const params = new URLSearchParams();
      if (filters.complexity !== 'all') params.append('complexity', filters.complexity);
      if (filters.approved !== 'all') params.append('approved_only', filters.approved === 'approved');
      
      const response = await axios.get(`${getApiUrl('/lora/data')}?${params}`);
      setTrainingData(response.data || []);
    } catch (error) {
      console.error('Ошибка загрузки данных:', error);
      // Устанавливаем заглушку данных
      setTrainingData([]);
    } finally {
      setIsLoading(false);
    }
  };

  const collectData = async () => {
    try {
      setIsLoading(true);
      const response = await axios.post(getApiUrl('/lora/data/collect'), {
        limit: 1000,
        days_back: 30,
        collection_type: 'auto'
      });
      
      if (response.data.error) {
        setError(`Ошибка сбора данных: ${response.data.error}`);
      } else {
        alert(`Собрано ${response.data.total_processed} диалогов, одобрено ${response.data.total_approved}`);
        loadStats();
        loadTrainingData();
      }
    } catch (error) {
      console.error('Ошибка сбора данных:', error);
      setError('Ошибка сбора данных');
    } finally {
      setIsLoading(false);
    }
  };

  const approveData = async (dataId) => {
    try {
      await axios.post(`${getApiUrl('/lora/data')}/${dataId}/approve`);
      loadTrainingData();
      loadStats();
    } catch (error) {
      console.error('Ошибка одобрения:', error);
    }
  };

  const rejectData = async (dataId) => {
    try {
      await axios.post(`${getApiUrl('/lora/data')}/${dataId}/reject`, {
        reason: 'Не соответствует требованиям'
      });
      loadTrainingData();
      loadStats();
    } catch (error) {
      console.error('Ошибка отклонения:', error);
    }
  };

  const batchApprove = async () => {
    try {
      setIsLoading(true);
      const response = await axios.post(getApiUrl('/lora/data/batch-approve'), {
        data_ids: selectedData
      });
      
      if (response.data.error) {
        setError(`Ошибка пакетного одобрения: ${response.data.error}`);
      } else {
        alert(`Одобрено ${response.data.approved_count} записей`);
        setSelectedData([]);
        loadTrainingData();
        loadStats();
      }
    } catch (error) {
      console.error('Ошибка пакетного одобрения:', error);
      setError('Ошибка пакетного одобрения');
    } finally {
      setIsLoading(false);
    }
  };

  const startTraining = async () => {
    try {
      setIsLoading(true);
      const response = await axios.post(getApiUrl('/lora/training/start'), {
        job_name: 'Обучение v1.0.0',
        hyperparameters: {
          learning_rate: 0.0001,
          num_epochs: 3,
          batch_size: 4
        }
      });
      
      alert('Обучение запущено!');
      loadStats();
    } catch (error) {
      console.error('Ошибка запуска обучения:', error);
      setError('Ошибка запуска обучения');
    } finally {
      setIsLoading(false);
    }
  };

  const renderStars = (rating) => {
    const stars = [];
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <Star
          key={i}
          className={`w-4 h-4 ${
            i <= rating ? 'text-yellow-400 fill-current' : 'text-gray-300'
          }`}
        />
      );
    }
    return stars;
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Заголовок */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">🎯 Управление LoRA</h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">Обучение и настройка модели ИИ-юриста</p>
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
                    ? 'bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
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
              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <Database className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Всего данных</p>
                    <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                      {stats.total_data || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Одобрено</p>
                    <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                      {stats.approved_data || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <Clock className="w-8 h-8 text-yellow-600 dark:text-yellow-400" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Ожидает</p>
                    <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                      {stats.pending_data || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <Star className="w-8 h-8 text-purple-600 dark:text-purple-400" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Качество</p>
                    <p className="text-2xl font-semibold text-gray-900 dark:text-white">
                      {stats.quality_score || 0}%
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Быстрые действия */}
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Быстрые действия</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <button
                  onClick={collectData}
                  disabled={isLoading}
                  className="flex items-center justify-center space-x-2 px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-800 disabled:opacity-50"
                >
                  <Database className="w-4 h-4" />
                  <span>Собрать данные</span>
                </button>
                
                <button
                  onClick={startTraining}
                  disabled={isLoading}
                  className="flex items-center justify-center space-x-2 px-4 py-2 bg-green-600 dark:bg-green-700 text-white rounded-lg hover:bg-green-700 dark:hover:bg-green-800 disabled:opacity-50"
                >
                  <Play className="w-4 h-4" />
                  <span>Запустить обучение</span>
                </button>
                
                <button
                  onClick={loadStats}
                  className="flex items-center justify-center space-x-2 px-4 py-2 bg-gray-600 dark:bg-gray-700 text-white rounded-lg hover:bg-gray-700 dark:hover:bg-gray-800"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span>Обновить</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Данные */}
        {activeTab === 'data' && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Управление данными</h3>
              
              {/* Фильтры */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Сложность
                  </label>
                  <select
                    value={filters.complexity}
                    onChange={(e) => setFilters({...filters, complexity: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">Все</option>
                    <option value="simple">Простая</option>
                    <option value="medium">Средняя</option>
                    <option value="complex">Сложная</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Статус
                  </label>
                  <select
                    value={filters.approved}
                    onChange={(e) => setFilters({...filters, approved: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">Все</option>
                    <option value="approved">Одобрено</option>
                    <option value="pending">Ожидает</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Качество
                  </label>
                  <select
                    value={filters.quality}
                    onChange={(e) => setFilters({...filters, quality: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">Все</option>
                    <option value="high">Высокое</option>
                    <option value="medium">Среднее</option>
                    <option value="low">Низкое</option>
                  </select>
                </div>
              </div>

              {/* Действия */}
              <div className="flex space-x-4 mb-6">
                <button
                  onClick={batchApprove}
                  disabled={selectedData.length === 0}
                  className="flex items-center space-x-2 px-4 py-2 bg-green-600 dark:bg-green-700 text-white rounded-lg hover:bg-green-700 dark:hover:bg-green-800 disabled:opacity-50"
                >
                  <CheckSquare className="w-4 h-4" />
                  <span>Одобрить выбранные ({selectedData.length})</span>
                </button>
                
                <button
                  onClick={loadTrainingData}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-800"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span>Обновить</span>
                </button>
              </div>

              {/* Таблица данных */}
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        <input
                          type="checkbox"
                          checked={selectedData.length === trainingData.length && trainingData.length > 0}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedData(trainingData.map(item => item.id));
                            } else {
                              setSelectedData([]);
                            }
                          }}
                          className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                        />
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Вопрос
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Ответ
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Качество
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Статус
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                        Действия
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {isLoading ? (
                      <tr>
                        <td colSpan="6" className="px-6 py-4 text-center">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 dark:border-blue-400 mx-auto"></div>
                        </td>
                      </tr>
                    ) : trainingData.length === 0 ? (
                      <tr>
                        <td colSpan="6" className="px-6 py-4 text-center text-gray-500 dark:text-gray-400">
                          Нет данных для отображения
                        </td>
                      </tr>
                    ) : (
                      trainingData.map((item) => (
                        <tr key={item.id}>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <input
                              type="checkbox"
                              checked={selectedData.includes(item.id)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedData([...selectedData, item.id]);
                                } else {
                                  setSelectedData(selectedData.filter(id => id !== item.id));
                                }
                              }}
                              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                            />
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100 max-w-xs truncate">
                            {item.question || 'Нет вопроса'}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100 max-w-xs truncate">
                            {item.answer || 'Нет ответа'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex">
                              {renderStars(item.quality_score || 0)}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                              item.is_approved 
                                ? 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-400' 
                                : 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-400'
                            }`}>
                              {item.is_approved ? 'Одобрено' : 'Ожидает'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex space-x-2">
                              <button
                                onClick={() => approveData(item.id)}
                                className="text-green-600 dark:text-green-400 hover:text-green-900 dark:hover:text-green-300"
                              >
                                <CheckCircle className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => rejectData(item.id)}
                                className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300"
                              >
                                <XCircle className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Обучение */}
        {activeTab === 'training' && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Запуск обучения</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Настройте параметры и запустите обучение модели LoRA
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Название задачи
                  </label>
                  <input
                    type="text"
                    placeholder="Например: Обучение v1.1.0"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white placeholder-gray-400 dark:placeholder-gray-400 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Количество эпох
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    defaultValue="3"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white placeholder-gray-400 dark:placeholder-gray-400 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="mt-6">
                <button
                  onClick={startTraining}
                  disabled={isLoading}
                  className="flex items-center space-x-2 px-6 py-3 bg-blue-600 dark:bg-blue-700 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-800 disabled:opacity-50"
                >
                  <Play className="w-4 h-4" />
                  <span>Запустить обучение</span>
                </button>
              </div>
            </div>

            {/* Активные задачи */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Активные задачи обучения</h3>
              </div>
              <div className="p-6">
                <p className="text-gray-500 dark:text-gray-400 text-center">Нет активных задач обучения</p>
              </div>
            </div>
          </div>
        )}

        {/* Модели */}
        {activeTab === 'models' && (
          <div className="space-y-6">
            <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Управление моделями</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Просматривайте и управляйте версиями моделей
              </p>
              
              <div className="mt-6">
                <button className="flex items-center space-x-2 px-4 py-2 bg-blue-600 dark:bg-blue-700 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-800">
                  <Upload className="w-4 h-4" />
                  <span>Создать новую версию</span>
                </button>
              </div>
            </div>

            {/* Список моделей */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Версии моделей</h3>
              </div>
              <div className="p-6">
                <p className="text-gray-500 dark:text-gray-400 text-center">Нет доступных моделей</p>
              </div>
            </div>
          </div>
        )}

        {/* Ошибки */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4">
            <div className="flex">
              <AlertCircle className="h-5 w-5 text-red-400 dark:text-red-500" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800 dark:text-red-400">Ошибка</h3>
                <div className="mt-2 text-sm text-red-700 dark:text-red-300">
                  {typeof error === 'string' ? error : (error.message || error.detail || 'Произошла ошибка')}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LoRAManagement;
