import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Upload, 
  Search, 
  Trash2, 
  Download,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Eye,
  Plus
} from 'lucide-react';
import axios from 'axios';
import { getApiUrl } from '../config/api';
import UploadProgress from './UploadProgress';

const DocumentManagement = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('success');
  const [searchTerm, setSearchTerm] = useState('');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showUrlUploadModal, setShowUrlUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadDescription, setUploadDescription] = useState('');
  const [uploadUrl, setUploadUrl] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({
    isUploading: false,
    progress: 0,
    currentStep: '',
    error: '',
    success: false,
    validationDetails: null,
    chunksInfo: null
  });
  const [pagination, setPagination] = useState({
    skip: 0,
    limit: 20,
    total: 0
  });

  useEffect(() => {
    loadDocuments();
  }, [pagination.skip]);

  const loadDocuments = async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams({
        skip: pagination.skip.toString(),
        limit: pagination.limit.toString()
      });

      const response = await axios.get(`${getApiUrl('/admin/documents')}?${params}`);
      setDocuments(response.data.documents || []);
      setPagination(prev => ({ ...prev, total: response.data.total || 0 }));
    } catch (err) {
      setError('Ошибка загрузки документов');
      console.error('Documents error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchTerm.trim()) {
      loadDocuments();
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await axios.get(`${getApiUrl('/admin/documents/search')}?query=${encodeURIComponent(searchTerm)}`);
      setDocuments(response.data.results || []);
      setPagination(prev => ({ ...prev, total: response.data.total || 0 }));
    } catch (err) {
      setError('Ошибка поиска документов');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;

    // Сброс состояния прогресса
    setUploadProgress({
      isUploading: true,
      progress: 0,
      currentStep: 'upload',
      error: '',
      success: false,
      validationDetails: null,
      chunksInfo: null
    });
    setUploading(true);
    setError('');

    try {
      // Шаг 1: Загрузка файла
      setUploadProgress(prev => ({ ...prev, progress: 20, currentStep: 'upload' }));
      
      const formData = new FormData();
      formData.append('file', uploadFile);
      if (uploadDescription) {
        formData.append('description', uploadDescription);
      }

      // Шаг 2: Валидация документа
      setUploadProgress(prev => ({ ...prev, progress: 40, currentStep: 'validation' }));

      const response = await axios.post(getApiUrl('/admin/documents/upload'), formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.data.success) {
        // Шаг 3: Обработка текста
        setUploadProgress(prev => ({ ...prev, progress: 60, currentStep: 'processing' }));

        // Шаг 4: Разбивка на чанки
        setUploadProgress(prev => ({ 
          ...prev, 
          progress: 80, 
          currentStep: 'chunking',
          chunksInfo: response.data.details
        }));

        // Шаг 5: Векторизация
        setUploadProgress(prev => ({ ...prev, progress: 90, currentStep: 'vectorizing' }));

        // Шаг 6: Завершение
        setUploadProgress(prev => ({ 
          ...prev, 
          progress: 100, 
          currentStep: 'complete',
          success: true,
          validationDetails: {
            document_type: response.data.document_type || response.data.details?.document_type || 'unknown',
            confidence: response.data.validation_confidence || response.data.details?.validation_confidence || 0,
            legal_score: response.data.legal_score || response.data.details?.legal_score || 0,
            chunks_added: response.data.chunks_added || response.data.details?.chunks_added || 0,
            text_length: response.data.text_length || response.data.details?.text_length || 0,
            file_hash: response.data.file_hash || response.data.details?.file_hash || '',
            document_id: response.data.document_id || response.data.details?.document_id || ''
          }
        }));

        // Закрываем модальное окно через 2 секунды
        setTimeout(() => {
          setShowUploadModal(false);
          setUploadFile(null);
          setUploadDescription('');
          setUploadProgress({
            isUploading: false,
            progress: 0,
            currentStep: '',
            error: '',
            success: false,
            validationDetails: null,
            chunksInfo: null
          });
          loadDocuments(); // Перезагружаем список
        }, 2000);

      } else {
        // Ошибка валидации
        const errorMessage = response.data.error || response.data.message || 'Ошибка загрузки файла';
        const suggestions = response.data.suggestions || [];

        setUploadProgress(prev => ({
          ...prev,
          progress: 0,
          currentStep: 'validation',
          error: errorMessage,
          success: false,
          validationDetails: {
            suggestions: suggestions,
            document_type: response.data.validation_details?.document_type || 'unknown',
            confidence: response.data.validation_details?.confidence || 0,
            legal_score: response.data.validation_details?.legal_score || 0
          }
        }));

        setError(errorMessage);
      }
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.response?.data?.message || 'Ошибка загрузки файла';
      const suggestions = err.response?.data?.suggestions || [];

      setUploadProgress(prev => ({
        ...prev,
        progress: 0,
        currentStep: 'upload',
        error: errorMessage,
        success: false,
        validationDetails: {
          suggestions: suggestions
        }
      }));

      setError(errorMessage);
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleUrlUpload = async () => {
    if (!uploadUrl.trim()) {
      setError('Введите URL для загрузки');
      return;
    }

    setUploading(true);
    setError('');
    
    setUploadProgress({
      isUploading: true,
      progress: 0,
      currentStep: 'validating',
      error: '',
      success: false,
      validationDetails: null,
      chunksInfo: null
    });

    try {
      const response = await axios.post(
        getApiUrl('/admin/documents/upload-url'),
        { url: uploadUrl },
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      );

      if (response.data.success) {
        setUploadProgress(prev => ({
          ...prev,
          progress: 100,
          currentStep: 'completed',
          success: true,
          validationDetails: {
            document_type: response.data.document_type || response.data.details?.document_type || 'unknown',
            confidence: response.data.validation_confidence || response.data.details?.validation_confidence || 0,
            legal_score: response.data.legal_score || response.data.details?.legal_score || 0,
            chunks_added: response.data.chunks_added || response.data.details?.chunks_added || 0,
            text_length: response.data.text_length || response.data.details?.text_length || 0,
            file_hash: response.data.file_hash || response.data.details?.file_hash || '',
            document_id: response.data.document_id || response.data.details?.document_id || '',
            source_url: response.data.source_url || uploadUrl
          }
        }));

        // Закрываем модальное окно через 2 секунды
        setTimeout(() => {
          setShowUrlUploadModal(false);
          setUploadUrl('');
          setUploadProgress({
            isUploading: false,
            progress: 0,
            currentStep: '',
            error: '',
            success: false,
            validationDetails: null,
            chunksInfo: null
          });
          loadDocuments(); // Перезагружаем список
        }, 2000);

      } else {
        const errorMessage = response.data.error || response.data.message || 'Ошибка загрузки по URL';
        setUploadProgress(prev => ({
          ...prev,
          progress: 0,
          currentStep: 'error',
          error: errorMessage,
          success: false
        }));
        setError(errorMessage);
      }
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.response?.data?.message || 'Ошибка загрузки по URL';
      setUploadProgress(prev => ({
        ...prev,
        progress: 0,
        currentStep: 'error',
        error: errorMessage,
        success: false
      }));
      setError(errorMessage);
      console.error('URL upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDocument = async (documentId) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот документ?')) {
      return;
    }

    try {
      const response = await axios.delete(`${getApiUrl('/admin/documents')}/${documentId}`);
      
      // Проверяем успешность удаления
      if (response.status === 200 || response.status === 204) {
        // Сначала удаляем документ из локального состояния
        setDocuments(prev => prev.filter(doc => doc.id !== documentId));
        
        // Затем перезагружаем список для синхронизации
        await loadDocuments();
        
        // Показываем детальную информацию об удалении
        const totalChunks = response.data?.total_chunks_deleted || 0;
        const chromaChunks = response.data?.chromadb_chunks_deleted || 0;
        const simpleRagChunks = response.data?.simple_rag_chunks_deleted || 0;
        
        setMessage(`Документ успешно удален! Удалено чанков: ${totalChunks} (ChromaDB: ${chromaChunks}, Simple RAG: ${simpleRagChunks})`);
        setMessageType('success');
        
        // Автоматически скрываем сообщение через 5 секунд
        setTimeout(() => {
          setMessage('');
        }, 5000);
      } else {
        throw new Error('Неожиданный статус ответа');
      }
    } catch (err) {
      console.error('Delete error:', err);
      
      // Определяем тип ошибки и показываем соответствующее сообщение
      let errorMessage = 'Ошибка удаления документа';
      
      if (err.response) {
        const status = err.response.status;
        const data = err.response.data;
        
        switch (status) {
          case 404:
            errorMessage = `Документ с ID "${documentId}" не найден в системе`;
            break;
          case 403:
            errorMessage = 'У вас нет прав для удаления этого документа';
            break;
          case 500:
            errorMessage = data?.detail || data?.error || 'Внутренняя ошибка сервера при удалении документа';
            break;
          case 503:
            errorMessage = 'RAG система временно недоступна. Попробуйте позже';
            break;
          default:
            errorMessage = data?.detail || data?.error || `Ошибка сервера (${status})`;
        }
      } else if (err.request) {
        errorMessage = 'Ошибка сети. Проверьте подключение к интернету';
      } else {
        errorMessage = 'Неожиданная ошибка при удалении документа';
      }
      
      setError(errorMessage);
      
      // Автоматически скрываем ошибку через 7 секунд
      setTimeout(() => {
        setError('');
      }, 7000);
    }
  };

  const getFileTypeIcon = (filename) => {
    const extension = filename?.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'pdf':
        return '📄';
      case 'doc':
      case 'docx':
        return '📝';
      case 'txt':
        return '📃';
      default:
        return '📄';
    }
  };

  const getDocumentTitle = (doc) => {
    // Используем title из metadata или из API ответа
    return doc.metadata?.title || doc.title || doc.filename || 'Документ';
  };

  const getDocumentDate = (doc) => {
    const date = doc.metadata?.added_at || doc.upload_date;
    return date ? new Date(date).toLocaleDateString('ru-RU') : null;
  };

  const getDocumentStatus = (doc) => {
    // Если есть явный статус, используем его
    if (doc.status) {
      return doc.status;
    }
    
    // Если документ имеет контент и метаданные, считаем его обработанным
    if (doc.content && doc.metadata) {
      return 'processed';
    }
    
    // По умолчанию считаем готовым
    return 'ready';
  };

  const getDocumentPreview = (doc) => {
    // Для заглушки показываем информацию о документе
    if (doc.status === 'processed') {
      return 'Документ обработан и готов к использованию в RAG системе.';
    } else if (doc.status === 'processing') {
      return 'Документ обрабатывается...';
    } else if (doc.status === 'error') {
      return 'Ошибка обработки документа.';
    }
    
    return `Тип: ${doc.metadata?.document_type || doc.type || 'legal_document'}, Страниц: ${doc.metadata?.pages || doc.pages || 'неизвестно'}, Язык: ${doc.language || 'ru'}`;
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6">
      {/* Заголовок и действия */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Управление документами</h2>
        <div className="flex space-x-3">
          <button
            onClick={loadDocuments}
            className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Обновить
          </button>
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <Plus className="h-4 w-4 mr-2" />
            Загрузить файл
          </button>
          <button
            onClick={() => setShowUrlUploadModal(true)}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <Plus className="h-4 w-4 mr-2" />
            Загрузить по ссылке
          </button>
        </div>
      </div>

      {/* Индикатор прогресса загрузки */}
      <UploadProgress 
        isUploading={uploadProgress.isUploading}
        progress={uploadProgress.progress}
        currentStep={uploadProgress.currentStep}
        error={uploadProgress.error}
        success={uploadProgress.success}
        validationDetails={uploadProgress.validationDetails}
        chunksInfo={uploadProgress.chunksInfo}
      />

      {/* Экспертный поиск */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">🔍 Экспертный поиск</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Поиск с учетом иерархии документов, версионирования и гибридного алгоритма
          </p>
        </div>
        <div className="flex space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Поиск по содержимому документов с учетом даты ситуации..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
            />
          </div>
          <div className="flex space-x-2">
            <input
              type="date"
              placeholder="Дата ситуации"
              className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
              title="Дата ситуации для поиска актуальных норм"
            />
            <button
              onClick={handleSearch}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              🔍 Экспертный поиск
            </button>
          </div>
        </div>
        <div className="mt-3 text-xs text-gray-500 dark:text-gray-400">
          ✨ Использует токено-ориентированное чанкирование, иерархию документов и гибридный поиск
        </div>
      </div>

      {/* Сообщения */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <AlertCircle className="h-5 w-5 text-red-400 mr-2 mt-0.5 flex-shrink-0" />
            <div className="text-red-800 whitespace-pre-line">
              {typeof error === 'string' ? error : (error.message || error.detail || 'Произошла ошибка')}
            </div>
          </div>
        </div>
      )}

      {message && (
        <div className={`${messageType === 'success' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'} border rounded-lg p-4`}>
          <div className="flex items-start">
            {messageType === 'success' ? (
              <CheckCircle className="h-5 w-5 text-green-400 mr-2 mt-0.5 flex-shrink-0" />
            ) : (
              <AlertCircle className="h-5 w-5 text-red-400 mr-2 mt-0.5 flex-shrink-0" />
            )}
            <div className={`${messageType === 'success' ? 'text-green-800' : 'text-red-800'} whitespace-pre-line`}>{message}</div>
          </div>
        </div>
      )}

      {/* Список документов */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : documents.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">Нет документов</h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Начните с загрузки первого документа.
            </p>
            <div className="mt-6">
              <button
                onClick={() => setShowUploadModal(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
              >
                <Plus className="h-4 w-4 mr-2" />
                Загрузить документ
              </button>
            </div>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {documents.map((doc) => (
              <div key={doc.id} className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0">
                      <div className="h-10 w-10 rounded-lg bg-gray-100 dark:bg-gray-600 flex items-center justify-center">
                        <span className="text-lg">{getFileTypeIcon(doc.filename)}</span>
                      </div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {getDocumentTitle(doc)}
                        </h3>
                        {getDocumentDate(doc) && (
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {getDocumentDate(doc)}
                          </span>
                        )}
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          getDocumentStatus(doc) === 'processed' ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' :
                          getDocumentStatus(doc) === 'processing' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400' :
                          getDocumentStatus(doc) === 'error' ? 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400' :
                          getDocumentStatus(doc) === 'ready' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400' :
                          'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400'
                        }`}>
                          {getDocumentStatus(doc) === 'processed' ? 'Обработан' :
                           getDocumentStatus(doc) === 'processing' ? 'Обрабатывается' :
                           getDocumentStatus(doc) === 'error' ? 'Ошибка' :
                           getDocumentStatus(doc) === 'ready' ? 'Готов' : 'Готов'}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                        {doc.metadata?.filename || doc.metadata?.original_filename || doc.filename || 'Без имени файла'}
                      </p>
                      <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                        <span>Размер: {formatFileSize(doc.metadata?.file_size || doc.length || doc.size || 0)}</span>
                        {(doc.metadata?.pages || doc.pages) && (
                          <span>Страниц: {doc.metadata?.pages || doc.pages}</span>
                        )}
                        {doc.language && (
                          <span>Язык: {doc.language}</span>
                        )}
                        {(doc.metadata?.document_type || doc.metadata?.type || doc.type) && (
                          <span>Тип: {doc.metadata?.document_type || doc.metadata?.type || doc.type}</span>
                        )}
                      </div>
                      <div className="mt-2 text-sm text-gray-600 dark:text-gray-300">
                        {getDocumentPreview(doc)}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleDeleteDocument(doc.id)}
                      className="p-2 text-red-600 hover:bg-red-100 dark:hover:bg-red-900 rounded-lg transition-colors"
                      title="Удалить документ"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Модальное окно загрузки */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-gray-800">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Загрузить документ
              </h3>
              <form onSubmit={handleFileUpload}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Файл
                  </label>
                  <input
                    type="file"
                    accept=".pdf,.doc,.docx,.txt"
                    onChange={(e) => setUploadFile(e.target.files[0])}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                    required
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Описание (необязательно)
                  </label>
                  <textarea
                    value={uploadDescription}
                    onChange={(e) => setUploadDescription(e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                    placeholder="Краткое описание документа..."
                  />
                </div>
                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowUploadModal(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-600 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-500 transition-colors"
                  >
                    Отмена
                  </button>
                  <button
                    type="submit"
                    disabled={!uploadFile || uploading}
                    className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {uploading ? 'Загрузка...' : 'Загрузить'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно загрузки по URL */}
      {showUrlUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Загрузить документ по ссылке
              </h3>
              <form onSubmit={(e) => { e.preventDefault(); handleUrlUpload(); }}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    URL документа
                  </label>
                  <input
                    type="url"
                    value={uploadUrl}
                    onChange={(e) => setUploadUrl(e.target.value)}
                    placeholder="https://example.com/document.pdf"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                    required
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Поддерживаются: PDF, DOCX, TXT, MD файлы и HTML страницы
                  </p>
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Описание (необязательно)
                  </label>
                  <textarea
                    value={uploadDescription}
                    onChange={(e) => setUploadDescription(e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                    placeholder="Краткое описание документа..."
                  />
                </div>
                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowUrlUploadModal(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-600 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-500 transition-colors"
                  >
                    Отмена
                  </button>
                  <button
                    type="submit"
                    disabled={!uploadUrl.trim() || uploading}
                    className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {uploading ? 'Загрузка...' : 'Загрузить по ссылке'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentManagement;
