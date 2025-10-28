import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { 
  CloudUploadIcon, 
  DocumentIcon, 
  CheckCircleIcon, 
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

const SmartUpload = ({ onUploadComplete }) => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState([]);
  const [showStats, setShowStats] = useState(false);
  const [databaseStats, setDatabaseStats] = useState(null);

  // Загрузка файлов
  const onDrop = useCallback((acceptedFiles) => {
    const newFiles = acceptedFiles.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      status: 'pending',
      progress: 0,
      result: null,
      error: null
    }));
    
    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt']
    },
    maxSize: 50 * 1024 * 1024, // 50MB
    multiple: true
  });

  // Загрузка документов
  const handleUpload = async () => {
    if (files.length === 0) return;

    setUploading(true);
    setUploadResults([]);

    try {
      const formData = new FormData();
      files.forEach(({ file }) => {
        formData.append('files', file);
      });

      const response = await fetch('/api/smart-upload/upload-multiple', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (result.success) {
        setUploadResults(result.results);
        setFiles([]);
        onUploadComplete?.(result);
        await fetchDatabaseStats();
      } else {
        throw new Error('Ошибка загрузки документов');
      }
    } catch (error) {
      console.error('Ошибка загрузки:', error);
      setUploadResults([{
        error: error.message,
        success: false
      }]);
    } finally {
      setUploading(false);
    }
  };

  // Получение статистики базы данных
  const fetchDatabaseStats = async () => {
    try {
      const response = await fetch('/api/smart-upload/database-stats');
      const stats = await response.json();
      setDatabaseStats(stats);
    } catch (error) {
      console.error('Ошибка получения статистики:', error);
    }
  };

  // Удаление файла из списка
  const removeFile = (fileId) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  // Форматирование размера файла
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Получение иконки по типу документа
  const getDocumentIcon = (filename) => {
    const ext = filename.split('.').pop().toLowerCase();
    switch (ext) {
      case 'pdf':
        return '📄';
      case 'docx':
        return '📝';
      case 'txt':
        return '📃';
      default:
        return '📄';
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg">
        {/* Заголовок */}
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900">
            🧠 Интеллектуальная загрузка документов
          </h2>
          <p className="text-gray-600 mt-2">
            Система автоматически анализирует документы, извлекает структуру и создает умные чанки для поиска
          </p>
        </div>

        {/* Область загрузки */}
        <div className="p-6">
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-blue-400 bg-blue-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            <input {...getInputProps()} />
            <CloudUploadIcon className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-4 text-lg text-gray-600">
              {isDragActive
                ? 'Отпустите файлы здесь...'
                : 'Перетащите файлы сюда или нажмите для выбора'}
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Поддерживаются: PDF, DOCX, TXT (максимум 50MB)
            </p>
          </div>

          {/* Список файлов */}
          {files.length > 0 && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Выбранные файлы ({files.length})
              </h3>
              <div className="space-y-3">
                {files.map(({ id, file, status }) => (
                  <div
                    key={id}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">
                        {getDocumentIcon(file.name)}
                      </span>
                      <div>
                        <p className="font-medium text-gray-900">{file.name}</p>
                        <p className="text-sm text-gray-500">
                          {formatFileSize(file.size)}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => removeFile(id)}
                      className="text-red-500 hover:text-red-700"
                    >
                      <XMarkIcon className="h-5 w-5" />
                    </button>
                  </div>
                ))}
              </div>

              <div className="mt-6 flex space-x-4">
                <button
                  onClick={handleUpload}
                  disabled={uploading}
                  className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {uploading ? 'Обрабатываем...' : 'Загрузить и проанализировать'}
                </button>
                <button
                  onClick={() => setFiles([])}
                  className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50"
                >
                  Очистить
                </button>
              </div>
            </div>
          )}

          {/* Результаты загрузки */}
          {uploadResults.length > 0 && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Результаты обработки
              </h3>
              <div className="space-y-3">
                {uploadResults.map((result, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-lg ${
                      result.success
                        ? 'bg-green-50 border border-green-200'
                        : 'bg-red-50 border border-red-200'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      {result.success ? (
                        <CheckCircleIcon className="h-6 w-6 text-green-500" />
                      ) : (
                        <ExclamationTriangleIcon className="h-6 w-6 text-red-500" />
                      )}
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">
                          {result.filename}
                        </p>
                        {result.success ? (
                          <div className="mt-2 text-sm text-gray-600">
                            <p>✅ Создано чанков: {result.chunks_created}</p>
                            <p>📋 Найдено статей: {result.articles_found}</p>
                            <p>📁 Тип документа: {result.document_type}</p>
                          </div>
                        ) : (
                          <p className="text-sm text-red-600 mt-1">
                            ❌ {result.error}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Статистика базы данных */}
          <div className="mt-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Статистика базы данных
              </h3>
              <button
                onClick={fetchDatabaseStats}
                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
              >
                Обновить
              </button>
            </div>

            {databaseStats ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="flex items-center">
                    <DocumentIcon className="h-8 w-8 text-blue-500" />
                    <div className="ml-3">
                      <p className="text-sm font-medium text-blue-900">
                        Всего чанков
                      </p>
                      <p className="text-2xl font-bold text-blue-600">
                        {databaseStats.total_chunks}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="flex items-center">
                    <CheckCircleIcon className="h-8 w-8 text-green-500" />
                    <div className="ml-3">
                      <p className="text-sm font-medium text-green-900">
                        Документов
                      </p>
                      <p className="text-2xl font-bold text-green-600">
                        {databaseStats.document_count}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-purple-50 p-4 rounded-lg">
                  <div className="flex items-center">
                    <InformationCircleIcon className="h-8 w-8 text-purple-500" />
                    <div className="ml-3">
                      <p className="text-sm font-medium text-purple-900">
                        Качество
                      </p>
                      <p className="text-2xl font-bold text-purple-600">
                        {databaseStats.quality_analysis?.high_quality || 0}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <InformationCircleIcon className="h-12 w-12 mx-auto mb-4" />
                <p>Нажмите "Обновить" для получения статистики</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SmartUpload;
