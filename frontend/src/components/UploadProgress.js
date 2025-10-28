import React from 'react';
import { CheckCircle, AlertCircle, Clock, FileText, Shield, Database, Loader } from 'lucide-react';

const UploadProgress = ({ 
  isUploading, 
  progress, 
  currentStep, 
  error, 
  success, 
  validationDetails,
  chunksInfo 
}) => {
  const steps = [
    { id: 'upload', label: 'Загрузка файла', icon: FileText },
    { id: 'validation', label: 'Валидация документа', icon: Shield },
    { id: 'processing', label: 'Обработка текста', icon: Database },
    { id: 'chunking', label: 'Разбивка на чанки', icon: FileText },
    { id: 'vectorizing', label: 'Векторизация', icon: Database },
    { id: 'complete', label: 'Завершено', icon: CheckCircle }
  ];

  const getStepStatus = (stepId) => {
    if (error && currentStep === stepId) return 'error';
    if (success && stepId === 'complete') return 'success';
    if (currentStep === stepId) return 'active';
    if (steps.findIndex(s => s.id === stepId) < steps.findIndex(s => s.id === currentStep)) return 'completed';
    return 'pending';
  };

  const getStepIcon = (stepId) => {
    const status = getStepStatus(stepId);
    const IconComponent = steps.find(s => s.id === stepId)?.icon || FileText;
    
    switch (status) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      case 'active':
        return <Loader className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStepColor = (stepId) => {
    const status = getStepStatus(stepId);
    switch (status) {
      case 'success':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'active':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'completed':
        return 'text-green-600 bg-green-50 border-green-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  if (!isUploading && !error && !success) return null;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          {error ? 'Ошибка загрузки' : success ? 'Загрузка завершена' : 'Обработка документа'}
        </h3>
        {isUploading && (
          <div className="text-sm text-gray-500">
            {progress}%
          </div>
        )}
      </div>

      {/* Прогресс бар */}
      {isUploading && (
        <div className="w-full bg-gray-200 rounded-full h-2 mb-6">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {/* Шаги обработки */}
      <div className="space-y-3">
        {steps.map((step) => (
          <div
            key={step.id}
            className={`flex items-center p-3 rounded-lg border ${getStepColor(step.id)}`}
          >
            {getStepIcon(step.id)}
            <span className="ml-3 font-medium">{step.label}</span>
            
            {/* Дополнительная информация для текущего шага */}
            {currentStep === step.id && (
              <div className="ml-auto text-sm text-gray-500">
                {step.id === 'validation' && validationDetails && (
                  <span>
                    {validationDetails.document_type} • 
                    Уверенность: {Math.round(validationDetails.confidence * 100)}%
                  </span>
                )}
                {step.id === 'chunking' && validationDetails && (
                  <span>
                    {validationDetails.chunks_added || 0} чанков • 
                    {validationDetails.text_length || 0} символов
                  </span>
                )}
                {step.id === 'vectorizing' && (
                  <span>Создание векторов...</span>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Детали ошибки */}
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start">
            <AlertCircle className="h-5 w-5 text-red-400 mr-2 mt-0.5 flex-shrink-0" />
            <div className="text-red-800">
              <div className="font-medium mb-2">Ошибка обработки документа:</div>
              <div className="whitespace-pre-line text-sm">
                {typeof error === 'string' ? error : (error.message || error.detail || 'Произошла ошибка')}
              </div>
              
              {/* Рекомендации по исправлению */}
              {validationDetails?.suggestions && validationDetails.suggestions.length > 0 && (
                <div className="mt-3">
                  <div className="font-medium mb-1">Рекомендации:</div>
                  <ul className="list-disc list-inside text-sm space-y-1">
                    {validationDetails.suggestions.map((suggestion, index) => (
                      <li key={index}>{suggestion}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Успешное завершение */}
      {success && (
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-start">
            <CheckCircle className="h-5 w-5 text-green-400 mr-2 mt-0.5 flex-shrink-0" />
            <div className="text-green-800">
              <div className="font-medium mb-2">Документ успешно загружен!</div>
              <div className="text-sm">
                {validationDetails && (
                  <div>
                    • Создано чанков: {validationDetails.chunks_added || 0}<br/>
                    • Размер текста: {validationDetails.text_length || 0} символов<br/>
                    • Хеш файла: {validationDetails.file_hash?.substring(0, 16) || 'неизвестно'}...<br/>
                    • Тип документа: {validationDetails.document_type || 'unknown'}<br/>
                    • Уверенность валидации: {Math.round((validationDetails.confidence || 0) * 100)}%<br/>
                    • Юридический балл: {Math.round((validationDetails.legal_score || 0) * 100)}%
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadProgress;
