import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ErrorMessage from './ErrorMessage';
import AIThinkingIndicator from './AIThinkingIndicator';
import EnhancedConnectionStatus from './EnhancedConnectionStatus';

/**
 * Система уведомлений о статусе для всего приложения
 * Реализует требования 6.1, 6.2, 6.3, 6.4, 6.5 из спецификации
 */
const StatusNotificationSystem = ({ 
  websocket,
  isGenerating,
  generationStartTime,
  onStopGeneration,
  onReconnect,
  onForceReconnect,
  className = ""
}) => {
  const [notifications, setNotifications] = useState([]);
  const [connectionError, setConnectionError] = useState(null);
  const [modelError, setModelError] = useState(null);

  // Добавление уведомления
  const addNotification = useCallback((notification) => {
    const id = Date.now() + Math.random();
    const newNotification = {
      id,
      timestamp: Date.now(),
      autoHide: true,
      duration: 5000,
      ...notification
    };

    setNotifications(prev => [...prev, newNotification]);

    // Автоматическое скрытие
    if (newNotification.autoHide) {
      setTimeout(() => {
        removeNotification(id);
      }, newNotification.duration);
    }

    return id;
  }, []);

  // Удаление уведомления
  const removeNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  // Мониторинг состояния WebSocket
  useEffect(() => {
    if (!websocket) return;

    const handleStateChange = (state) => {
      switch (state) {
        case 'connected':
          setConnectionError(null);
          addNotification({
            type: 'success',
            title: 'Соединение восстановлено',
            message: 'Связь с сервером успешно установлена',
            duration: 3000
          });
          break;
        
        case 'reconnecting':
          addNotification({
            type: 'info',
            title: 'Переподключение',
            message: 'Попытка восстановить соединение с сервером...',
            autoHide: false
          });
          break;
        
        case 'failed':
          const error = { code: 1006, message: 'Не удалось подключиться к серверу' };
          setConnectionError(error);
          addNotification({
            type: 'error',
            title: 'Ошибка соединения',
            message: 'Не удалось подключиться к серверу. Проверьте интернет-соединение.',
            autoHide: false,
            actions: [
              {
                label: 'Переподключить',
                action: onForceReconnect || onReconnect,
                primary: true
              }
            ]
          });
          break;
      }
    };

    const handleError = (error) => {
      console.error('WebSocket error:', error);
      
      let errorNotification = {
        type: 'error',
        title: 'Ошибка соединения',
        message: 'Произошла ошибка при работе с сервером',
        autoHide: false
      };

      if (error.code === 1008) {
        errorNotification = {
          type: 'error',
          title: 'Ошибка аутентификации',
          message: 'Ваша сессия истекла. Необходимо войти в систему заново.',
          autoHide: false,
          actions: [
            {
              label: 'Войти',
              action: () => window.location.href = '/login',
              primary: true
            }
          ]
        };
      }

      addNotification(errorNotification);
    };

    websocket.on('stateChange', handleStateChange);
    websocket.on('error', handleError);

    return () => {
      websocket.off('stateChange', handleStateChange);
      websocket.off('error', handleError);
    };
  }, [websocket, addNotification, onReconnect, onForceReconnect]);

  // API для внешнего использования
  const showError = useCallback((error, options = {}) => {
    return addNotification({
      type: 'error',
      title: 'Ошибка',
      message: typeof error === 'string' ? error : error.message,
      ...options
    });
  }, [addNotification]);

  const showSuccess = useCallback((message, options = {}) => {
    return addNotification({
      type: 'success',
      title: 'Успешно',
      message,
      ...options
    });
  }, [addNotification]);

  const showInfo = useCallback((message, options = {}) => {
    return addNotification({
      type: 'info',
      title: 'Информация',
      message,
      ...options
    });
  }, [addNotification]);

  const showModelUnavailable = useCallback(() => {
    setModelError({ message: 'Модель ИИ временно недоступна' });
    return addNotification({
      type: 'warning',
      title: 'Модель ИИ недоступна',
      message: 'Модель искусственного интеллекта временно недоступна. Попробуйте позже.',
      autoHide: false,
      actions: [
        {
          label: 'Повторить',
          action: () => window.location.reload(),
          primary: true
        }
      ]
    });
  }, [addNotification]);

  // Экспорт API для использования в других компонентах
  useEffect(() => {
    window.statusNotifications = {
      showError,
      showSuccess,
      showInfo,
      showModelUnavailable,
      removeNotification
    };

    return () => {
      delete window.statusNotifications;
    };
  }, [showError, showSuccess, showInfo, showModelUnavailable, removeNotification]);

  return (
    <div className={`fixed inset-0 pointer-events-none z-50 ${className}`}>
      {/* Индикатор генерации ИИ */}
      {isGenerating && (
        <div className="absolute top-20 left-1/2 transform -translate-x-1/2 pointer-events-auto">
          <AIThinkingIndicator
            isGenerating={isGenerating}
            startTime={generationStartTime}
            onStop={onStopGeneration}
            variant="detailed"
          />
        </div>
      )}

      {/* Статус соединения */}
      <div className="absolute top-4 right-4 pointer-events-auto">
        <EnhancedConnectionStatus
          websocket={websocket}
          onReconnect={onReconnect}
          onForceReconnect={onForceReconnect}
          showDetails={false}
          autoHide={true}
        />
      </div>

      {/* Уведомления */}
      <div className="absolute top-4 left-4 space-y-2 pointer-events-auto max-w-sm">
        <AnimatePresence>
          {notifications.map((notification) => (
            <motion.div
              key={notification.id}
              initial={{ opacity: 0, x: -100, scale: 0.9 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: -100, scale: 0.9 }}
              transition={{ duration: 0.3 }}
            >
              <StatusNotification
                notification={notification}
                onClose={() => removeNotification(notification.id)}
              />
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};

// Компонент отдельного уведомления
const StatusNotification = ({ notification, onClose }) => {
  const getNotificationStyles = (type) => {
    const styles = {
      success: 'bg-green-50 border-green-200 text-green-800',
      error: 'bg-red-50 border-red-200 text-red-800',
      warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
      info: 'bg-blue-50 border-blue-200 text-blue-800'
    };
    return styles[type] || styles.info;
  };

  return (
    <div className={`p-4 rounded-lg border shadow-lg ${getNotificationStyles(notification.type)}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h4 className="text-sm font-medium mb-1">{notification.title}</h4>
          <p className="text-sm opacity-90">{notification.message}</p>
          
          {notification.actions && (
            <div className="flex space-x-2 mt-3">
              {notification.actions.map((action, index) => (
                <button
                  key={index}
                  onClick={action.action}
                  className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
                    action.primary
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : 'bg-white border hover:bg-gray-50'
                  }`}
                >
                  {action.label}
                </button>
              ))}
            </div>
          )}
        </div>
        
        <button
          onClick={onClose}
          className="ml-3 text-gray-400 hover:text-gray-600 transition-colors"
        >
          ×
        </button>
      </div>
    </div>
  );
};

export default StatusNotificationSystem;