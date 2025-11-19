import React, { useState, useRef, useCallback } from 'react';
import { Upload, X, File, FileText, Image, FileSpreadsheet } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import axios from 'axios';

const FileUpload = ({ onFileUpload, onFileRemove, maxFiles = 5, maxSize = 10 }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);
  const { isDark } = useTheme();

  const getFileIcon = (filename) => {
    const extension = filename.split('.').pop().toLowerCase();
    
    switch (extension) {
      case 'pdf':
      case 'doc':
      case 'docx':
      case 'txt':
      case 'rtf':
        return <FileText className="h-5 w-5" />;
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
      case 'bmp':
        return <Image className="h-5 w-5" />;
      case 'xls':
      case 'xlsx':
      case 'csv':
        return <FileSpreadsheet className="h-5 w-5" />;
      default:
        return <File className="h-5 w-5" />;
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const validateFile = (file) => {
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
      'application/rtf',
      'image/jpeg',
      'image/png',
      'image/gif',
      'image/bmp',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'text/csv'
    ];

    const maxSizeBytes = maxSize * 1024 * 1024; // Convert MB to bytes

    if (!allowedTypes.includes(file.type)) {
      return `Тип файла ${file.type} не поддерживается`;
    }

    if (file.size > maxSizeBytes) {
      return `Размер файла превышает ${maxSize}MB`;
    }

    return null;
  };

  const uploadFile = async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('/api/v1/files/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 30000, // 30 seconds timeout
      });

      return response.data;
    } catch (error) {
      console.error('Upload error:', error);
      throw new Error(error.response?.data?.detail || 'Ошибка при загрузке файла');
    }
  };

  const handleFiles = useCallback(async (files) => {
    const fileList = Array.from(files);
    
    if (fileList.length + uploadedFiles.length > maxFiles) {
      setError(`Максимум ${maxFiles} файлов`);
      return;
    }

    setError(null);
    setUploading(true);

    try {
      const uploadPromises = fileList.map(async (file) => {
        const validationError = validateFile(file);
        if (validationError) {
          throw new Error(validationError);
        }

        const uploadResult = await uploadFile(file);
        return {
          ...uploadResult,
          originalFile: file,
          id: Date.now() + Math.random()
        };
      });

      const results = await Promise.all(uploadPromises);
      const newFiles = [...uploadedFiles, ...results];
      
      setUploadedFiles(newFiles);
      
      if (onFileUpload) {
        onFileUpload(results);
      }
    } catch (error) {
      setError(error.message);
    } finally {
      setUploading(false);
    }
  }, [uploadedFiles, maxFiles, onFileUpload]);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFiles(files);
    }
  }, [handleFiles]);

  const handleFileInput = useCallback((e) => {
    const files = e.target.files;
    if (files.length > 0) {
      handleFiles(files);
    }
    // Reset input
    e.target.value = '';
  }, [handleFiles]);

  const removeFile = useCallback((fileId) => {
    const fileToRemove = uploadedFiles.find(f => f.id === fileId);
    if (fileToRemove) {
      setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
      
      if (onFileRemove) {
        onFileRemove(fileToRemove);
      }
    }
  }, [uploadedFiles, onFileRemove]);

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="w-full">
      {/* Drag & Drop Area */}
      <div
        className={`
          relative border-2 border-dashed rounded-lg p-6 text-center cursor-pointer
          transition-all duration-200 ease-in-out
          ${isDragOver 
            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20' 
            : 'border-gray-300 dark:border-gray-600 hover:border-primary-400 dark:hover:border-primary-500'
          }
          ${uploading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={openFileDialog}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.doc,.docx,.txt,.rtf,.jpg,.jpeg,.png,.gif,.bmp,.xls,.xlsx,.csv"
          onChange={handleFileInput}
          className="hidden"
          disabled={uploading}
        />
        
        <div className="flex flex-col items-center space-y-2">
          <Upload className={`h-8 w-8 ${isDragOver ? 'text-primary-500' : 'text-gray-400 dark:text-gray-500'}`} />
          <div className="text-sm">
            <span className="text-primary-600 dark:text-primary-400 font-medium">
              Нажмите для выбора файлов
            </span>
            {' '}или перетащите их сюда
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Поддерживаются: PDF, DOC, DOCX, TXT, RTF, JPG, PNG, XLS, XLSX, CSV
            <br />
            Максимум {maxFiles} файлов, до {maxSize}MB каждый
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      {/* Uploaded Files */}
      {uploadedFiles.length > 0 && (
        <div className="mt-4 space-y-2">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Загруженные файлы ({uploadedFiles.length})
          </h4>
          {uploadedFiles.map((file) => (
            <div
              key={file.id}
              className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
            >
              <div className="flex items-center space-x-3">
                <div className="text-gray-500 dark:text-gray-400">
                  {getFileIcon(file.filename)}
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {file.filename}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {formatFileSize(file.file_size)}
                  </p>
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile(file.id);
                }}
                className="p-1 text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors duration-200"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Upload Progress */}
      {uploading && (
        <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            <p className="text-sm text-blue-600 dark:text-blue-400">
              Загрузка файлов...
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUpload;
