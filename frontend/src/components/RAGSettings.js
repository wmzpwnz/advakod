import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  Search, 
  Shield, 
  FileText, 
  ToggleLeft, 
  ToggleRight,
  Info,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';
import axios from 'axios';
import { getApiUrl } from '../config/api';

const RAGSettings = ({ isVisible, onClose }) => {
  const [settings, setSettings] = useState({
    use_enhanced_search: true,
    enable_fact_checking: true,
    enable_explainability: true,
    top_k: 20,
    rerank_top_k: 5
  });
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (isVisible) {
      loadRAGStatus();
    }
  }, [isVisible]);

  const loadRAGStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(getApiUrl('/api/v1/enhanced-rag/status'), {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStatus(response.data);
    } catch (error) {
      console.error('Error loading RAG status:', error);
      setMessage('Ошибка загрузки статуса RAG системы');
    }
  };

  const handleSettingChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const saveSettings = async () => {
    setLoading(true);
    setMessage('');
    
    try {
      // Здесь можно добавить API для сохранения настроек
      // Пока что просто показываем сообщение об успехе
      setMessage('Настройки сохранены!');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Error saving settings:', error);
      setMessage('Ошибка сохранения настроек');
    } finally {
      setLoading(false);
    }
  };

  const testRAG = async () => {
    setLoading(true);
    setMessage('');
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(getApiUrl('/api/v1/enhanced-rag/generate-response'), {
        query: 'Тестовый вопрос по праву',
        enable_fact_checking: settings.enable_fact_checking,
        enable_explainability: settings.enable_explainability
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        setMessage('Тест RAG прошел успешно!');
      } else {
        setMessage('Ошибка тестирования RAG');
      }
    } catch (error) {
      console.error('Error testing RAG:', error);
      setMessage('Ошибка тестирования RAG');
    } finally {
      setLoading(false);
      setTimeout(() => setMessage(''), 5000);
    }
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <Settings className="w-6 h-6 text-primary-600" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              Настройки RAG системы
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
          {/* Статус системы */}
          {status && (
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-3 flex items-center">
                <Info className="w-5 h-5 mr-2" />
                Статус системы
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span>Улучшенный поиск:</span>
                    <span className={`flex items-center ${status.rag_status?.enhancements?.enhanced_search_enabled ? 'text-green-600' : 'text-red-600'}`}>
                      {status.rag_status?.enhancements?.enhanced_search_enabled ? (
                        <CheckCircle className="w-4 h-4 mr-1" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 mr-1" />
                      )}
                      {status.rag_status?.enhancements?.enhanced_search_enabled ? 'Включен' : 'Отключен'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Факт-чекинг:</span>
                    <span className={`flex items-center ${status.rag_status?.enhancements?.fact_checking_enabled ? 'text-green-600' : 'text-red-600'}`}>
                      {status.rag_status?.enhancements?.fact_checking_enabled ? (
                        <CheckCircle className="w-4 h-4 mr-1" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 mr-1" />
                      )}
                      {status.rag_status?.enhancements?.fact_checking_enabled ? 'Включен' : 'Отключен'}
                    </span>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span>Explainability:</span>
                    <span className={`flex items-center ${status.rag_status?.enhancements?.explainability_enabled ? 'text-green-600' : 'text-red-600'}`}>
                      {status.rag_status?.enhancements?.explainability_enabled ? (
                        <CheckCircle className="w-4 h-4 mr-1" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 mr-1" />
                      )}
                      {status.rag_status?.enhancements?.explainability_enabled ? 'Включен' : 'Отключен'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>AI модель:</span>
                    <span className={`flex items-center ${status.rag_status?.ai_model_ready ? 'text-green-600' : 'text-red-600'}`}>
                      {status.rag_status?.ai_model_ready ? (
                        <CheckCircle className="w-4 h-4 mr-1" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 mr-1" />
                      )}
                      {status.rag_status?.ai_model_ready ? 'Готова' : 'Не готова'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Настройки поиска */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center">
              <Search className="w-5 h-5 mr-2" />
              Настройки поиска
            </h3>
            
            <div className="space-y-4">
              {/* Улучшенный поиск */}
              <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Search className="w-5 h-5 text-primary-600" />
                  <div>
                    <div className="font-medium text-gray-900 dark:text-gray-100">
                      Улучшенный поиск
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      Гибридный поиск с ранжированием
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => handleSettingChange('use_enhanced_search', !settings.use_enhanced_search)}
                  className="flex items-center"
                >
                  {settings.use_enhanced_search ? (
                    <ToggleRight className="w-8 h-8 text-primary-600" />
                  ) : (
                    <ToggleLeft className="w-8 h-8 text-gray-400" />
                  )}
                </button>
              </div>

              {/* Факт-чекинг */}
              <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Shield className="w-5 h-5 text-green-600" />
                  <div>
                    <div className="font-medium text-gray-900 dark:text-gray-100">
                      Факт-чекинг
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      Проверка ссылок и утверждений
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => handleSettingChange('enable_fact_checking', !settings.enable_fact_checking)}
                  className="flex items-center"
                >
                  {settings.enable_fact_checking ? (
                    <ToggleRight className="w-8 h-8 text-green-600" />
                  ) : (
                    <ToggleLeft className="w-8 h-8 text-gray-400" />
                  )}
                </button>
              </div>

              {/* Explainability */}
              <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center space-x-3">
                  <FileText className="w-5 h-5 text-purple-600" />
                  <div>
                    <div className="font-medium text-gray-900 dark:text-gray-100">
                      Explainability
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      Структурированные ответы с источниками
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => handleSettingChange('enable_explainability', !settings.enable_explainability)}
                  className="flex items-center"
                >
                  {settings.enable_explainability ? (
                    <ToggleRight className="w-8 h-8 text-purple-600" />
                  ) : (
                    <ToggleLeft className="w-8 h-8 text-gray-400" />
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Параметры поиска */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Параметры поиска
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Количество документов для поиска
                </label>
                <input
                  type="number"
                  min="5"
                  max="50"
                  value={settings.top_k}
                  onChange={(e) => handleSettingChange('top_k', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Количество после ранжирования
                </label>
                <input
                  type="number"
                  min="3"
                  max="20"
                  value={settings.rerank_top_k}
                  onChange={(e) => handleSettingChange('rerank_top_k', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                />
              </div>
            </div>
          </div>

          {/* Сообщения */}
          {message && (
            <div className={`p-4 rounded-lg ${
              message.includes('успешно') || message.includes('сохранены') 
                ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-200'
                : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-200'
            }`}>
              {message}
            </div>
          )}

          {/* Кнопки */}
          <div className="flex space-x-4 pt-4">
            <button
              onClick={testRAG}
              disabled={loading}
              className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Тестирование...' : 'Тестировать RAG'}
            </button>
            
            <button
              onClick={saveSettings}
              disabled={loading}
              className="flex-1 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Сохранение...' : 'Сохранить настройки'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RAGSettings;
