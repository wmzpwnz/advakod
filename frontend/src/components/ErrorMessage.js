import React from 'react';
import { AlertCircle, RefreshCw, Wifi, WifiOff, Server, Clock, Zap } from 'lucide-react';

/**
 * Компонент для отображения информативных сообщений об ошибках
 * Реализует требование 6.1 из спецификации
 */
const ErrorMessage = ({ 
  error, 
  onRetry, 
  onReconnect, 
  className = "",
  showIcon = true,
  variant = "default" // "default", "inline", "toast"
}) => {
  // Определяем тип ошибки и соответствующее сообщение
  const getErrorInfo = (error) => {
    if (typeof error === 'string') {
      return {
        type: 'general',
        title: 'Ошибка',
        message: error,
        icon: AlertCircle,
        color: 'red',
        actions: ['retry']
      };
    }

    if (error?.code) {
      switch (error.code) {
        case 1008:
          return {
            type: 'auth',
            title: 'Ошибка аутентификации',
            message: 'Ваша сессия истекла. Пожалуйста, войдите в систему заново.',
            icon: AlertCircle,
            color: 'red',
            actions: ['login']
          };
        
        case 1006:
          return {
            type: 'connection',
            title: 'Соединение потеряно',
            message: 'Связь с сервером прервана. Попробуем переподключиться автоматически.',
            icon: WifiOff,
            color: 'orange',
            actions: ['reconnect', 'retry']
          };
        
        case 1011:
          return {
            type: 'server',
            title: 'Ошибка сервера',
            message: 'На сервере произошла ошибка. Попробуйте позже или обратитесь в поддержку.',
            icon: Server,
            color: 'red',
            actions: ['retry', 'support']
          };
        
        case 408:
          return {
            type: 'timeout',
            title: 'Превышено время ожидания',
            message: 'Генерация ответа заняла слишком много времени. Попробуйте упростить вопрос.',
            icon: Clock,
            color: 'orange',
            actions: ['retry']
          };
        
        case 503:
          return {
            type: 'overload',
            title: 'Сервер перегружен',
            message: 'Сервер временно перегружен. Подождите немного и попробуйте снова.',
            icon: Zap,
            color: 'yellow',
            actions: ['retry']
          };
        
        default:
          return {
            type: 'unknown',
            title: 'Неизвестная ошибка',
            message: error.message || 'Произошла неизвестная ошибка. Попробуйте еще раз.',
            icon: AlertCircle,
            color: 'red',
            actions: ['retry']
          };
      }
    }

    // HTTP ошибки
    if (error?.response?.status) {
      const status = error.response.status;
      
      if (status === 401) {
        return {
          type: 'auth',
          title: 'Требуется авторизация',
          message: 'Пожалуйста, войдите в систему для продолжения работы.',
          icon: AlertCircle,
          color: 'red',
          actions: ['login']
        };
      }
      
      if (status === 429) {
        return {
          type: 'rate_limit',
          title: 'Слишком много запросов',
          message: 'Вы отправили слишком много запросов. Подождите немного перед следующим запросом.',
          icon: Clock,
          color: 'orange',
          actions: ['wait']
        };
      }
      
      if (status === 503) {
        return {
          type: 'overload',
          title: 'Сервер перегружен',
          message: 'Сервер временно перегружен. Подождите немного и попробуйте снова.',
          icon: Zap,
          color: 'yellow',
          actions: ['retry']
        };
      }
      
      if (status >= 500) {
        return {
          type: 'server',
          title: 'Ошибка сервера',
          message: 'На сервере произошла ошибка. Мы уже работаем над её устранением.',
          icon: Server,
          color: 'red',
          actions: ['retry', 'support']
        };
      }
    }

    // Ошибки сети
    if (error?.request && !error?.response) {
      return {
        type: 'network',
        title: 'Проблема с сетью',
        message: 'Не удалось соединиться с сервером. Проверьте подключение к интернету.',
        icon: WifiOff,
        color: 'red',
        actions: ['reconnect', 'retry']
      };
    }

    // Ошибки модели ИИ
    if (error?.message?.includes('модель') || error?.message?.includes('ИИ')) {
      return {
        type: 'ai_model',
        title: 'Модель ИИ недоступна',
        message: 'Модель искусственного интеллекта временно недоступна. Попробуйте позже.',
        icon: AlertCircle,
        color: 'orange',
        actions: ['retry', 'support']
      };
    }

    // Общая ошибка
    return {
      type: 'general',
      title: 'Произошла ошибка',
      message: error?.message || 'Что-то пошло не так. Попробуйте еще раз.',
      icon: AlertCircle,
      color: 'red',
      actions: ['retry']
    };
  };

  const errorInfo = getErrorInfo(error);
  const Icon = errorInfo.icon;

  const getColorClasses = (color) => {
    const colorMap = {
      red: 'bg-red-50 border-red-200 text-red-800',
      orange: 'bg-orange-50 border-orange-200 text-orange-800',
      yellow: 'bg-yellow-50 border-yellow-200 text-yellow-800',
      blue: 'bg-blue-50 border-blue-200 text-blue-800'
    };
    return colorMap[color] || colorMap.red;
  };

  const getButtonColorClasses = (color) => {
    const colorMap = {
      red: 'bg-red-600 hover:bg-red-700 text-white',
      orange: 'bg-orange-600 hover:bg-orange-700 text-white',
      yellow: 'bg-yellow-600 hover:bg-yellow-700 text-white',
      blue: 'bg-blue-600 hover:bg-blue-700 text-white'
    };
    return colorMap[color] || colorMap.red;
  };

  const renderActions = () => {
    return errorInfo.actions.map(action => {
      switch (action) {
        case 'retry':
          return (
            <button
              key="retry"
              onClick={onRetry}
              className={`px-3 py-1 text-sm font-medium rounded transition-colors ${getButtonColorClasses(errorInfo.color)}`}
            >
              <RefreshCw className="w-4 h-4 inline mr-1" />
              Повторить
            </button>
          );
        
        case 'reconnect':
          return (
            <button
              key="reconnect"
              onClick={onReconnect}
              className={`px-3 py-1 text-sm font-medium rounded transition-colors ${getButtonColorClasses(errorInfo.color)}`}
            >
              <Wifi className="w-4 h-4 inline mr-1" />
              Переподключить
            </button>
          );
        
        case 'login':
          return (
            <button
              key="login"
              onClick={() => window.location.href = '/login'}
              className={`px-3 py-1 text-sm font-medium rounded transition-colors ${getButtonColorClasses(errorInfo.color)}`}
            >
              Войти
            </button>
          );
        
        case 'support':
          return (
            <button
              key="support"
              onClick={() => window.open('mailto:support@advacodex.com', '_blank')}
              className="px-3 py-1 text-sm font-medium bg-gray-600 hover:bg-gray-700 text-white rounded transition-colors"
            >
              Поддержка
            </button>
          );
        
        case 'wait':
          return (
            <span key="wait" className="text-sm text-gray-600">
              Подождите 1-2 минуты
            </span>
          );
        
        default:
          return null;
      }
    });
  };

  if (variant === "toast") {
    return (
      <div className={`fixed top-4 right-4 z-50 max-w-sm ${className}`}>
        <div className={`p-4 rounded-lg border shadow-lg ${getColorClasses(errorInfo.color)}`}>
          <div className="flex items-start space-x-3">
            {showIcon && <Icon className="w-5 h-5 mt-0.5 flex-shrink-0" />}
            <div className="flex-1">
              <h4 className="text-sm font-medium mb-1">{errorInfo.title}</h4>
              <p className="text-sm opacity-90 mb-3">{errorInfo.message}</p>
              <div className="flex space-x-2">
                {renderActions()}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (variant === "inline") {
    return (
      <div className={`flex items-center space-x-2 p-2 rounded ${getColorClasses(errorInfo.color)} ${className}`}>
        {showIcon && <Icon className="w-4 h-4 flex-shrink-0" />}
        <span className="text-sm flex-1">{errorInfo.message}</span>
        <div className="flex space-x-1">
          {renderActions()}
        </div>
      </div>
    );
  }

  // Default variant
  return (
    <div className={`p-4 rounded-lg border ${getColorClasses(errorInfo.color)} ${className}`}>
      <div className="flex items-start space-x-3">
        {showIcon && <Icon className="w-5 h-5 mt-0.5 flex-shrink-0" />}
        <div className="flex-1">
          <h3 className="text-sm font-medium mb-1">{errorInfo.title}</h3>
          <p className="text-sm opacity-90 mb-3">{errorInfo.message}</p>
          <div className="flex space-x-2">
            {renderActions()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ErrorMessage;