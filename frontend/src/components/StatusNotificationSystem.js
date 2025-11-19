import React, { useState, useEffect, useCallback, useRef } from 'react';
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
  const lastNotificationRef = useRef({});
  const debounceTimersRef = useRef({});

  // Удаление уведомления
  const removeNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  // Добавление уведомления с дедупликацией и дебаунсингом
  const addNotification = useCallback((notification) => {
    // Создаем ключ для дедупликации на основе типа и сообщения
    const notificationKey = `${notification.type}_${notification.title}_${notification.message}`;
    
    // Проверяем, не было ли уже показано такое же уведомление недавно
    const lastShown = lastNotificationRef.current[notificationKey];
    const now = Date.now();
    if (lastShown && (now - lastShown) < 5000) {
      // Такое же уведомление уже было показано менее 5 секунд назад - пропускаем
      return null;
    }

    // Дебаунсинг для частых изменений состояния
    if (debounceTimersRef.current[notificationKey]) {
      clearTimeout(debounceTimersRef.current[notificationKey]);
    }

    const timerId = setTimeout(() => {
      const id = Date.now() + Math.random();
      const newNotification = {
        id,
        timestamp: Date.now(),
        autoHide: true,
        duration: 5000,
        ...notification,
        key: notificationKey
      };

      setNotifications(prev => {
        // Удаляем старые уведомления того же типа и ключа
        const filtered = prev.filter(n => 
          !(n.key === notificationKey && n.type === notification.type)
        );
        return [...filtered, newNotification];
      });

      lastNotificationRef.current[notificationKey] = now;

      // Автоматическое скрытие
      if (newNotification.autoHide) {
        setTimeout(() => {
          removeNotification(id);
        }, newNotification.duration);
      }
    }, notification.type === 'error' ? 500 : 100); // Дебаунсинг для ошибок 500мс, для остальных 100мс

    debounceTimersRef.current[notificationKey] = timerId;

    return notificationKey;
  }, [removeNotification]);

  // Очистка таймеров при размонтировании
  useEffect(() => {
    return () => {
      Object.values(debounceTimersRef.current).forEach(timer => {
        if (timer) clearTimeout(timer);
      });
    };
  }, []);

  // Мониторинг состояния WebSocket с улучшенной обработкой
  useEffect(() => {
    if (!websocket) return;

    let stateChangeTimer = null;
    let errorTimer = null;
    let lastState = null;
    let errorCount = 0;

    const handleStateChange = (state) => {
      // Пропускаем повторные изменения на то же состояние
      if (lastState === state) return;
      lastState = state;

      // Очищаем предыдущий таймер
      if (stateChangeTimer) {
        clearTimeout(stateChangeTimer);
      }

      // Дебаунсинг изменений состояния
      stateChangeTimer = setTimeout(() => {
        switch (state) {
          case 'connected':
            setConnectionError(null);
            errorCount = 0; // Сбрасываем счетчик ошибок при успешном подключении
            // Удаляем все предыдущие уведомления об ошибках соединения
            setNotifications(prev => prev.filter(n => 
              !(n.type === 'error' && n.title === 'Ошибка соединения')
            ));
            addNotification({
              type: 'success',
              title: 'Соединение восстановлено',
              message: 'Связь с сервером успешно установлена',
              duration: 3000
            });
            break;
          
          case 'reconnecting':
            // Показываем уведомление о переподключении только один раз
            addNotification({
              type: 'info',
              title: 'Переподключение',
              message: 'Попытка восстановить соединение с сервером...',
              autoHide: false
            });
            break;
          
          case 'failed':
            errorCount++;
            // Показываем ошибку только если не было слишком много попыток
            if (errorCount <= 3) {
              const error = { code: 1006, message: 'Не удалось подключиться к серверу' };
              setConnectionError(error);
              // Удаляем старые уведомления об ошибках перед добавлением нового
              setNotifications(prev => prev.filter(n => 
                !(n.type === 'error' && n.title === 'Ошибка соединения')
              ));
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
            }
            break;
        }
      }, 300); // Дебаунсинг 300мс
    };

    const handleError = (error) => {
      console.error('WebSocket error:', error);
      
      // Очищаем предыдущий таймер ошибок
      if (errorTimer) {
        clearTimeout(errorTimer);
      }

      // Дебаунсинг ошибок
      errorTimer = setTimeout(() => {
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

        // Удаляем старые уведомления того же типа перед добавлением нового
        setNotifications(prev => prev.filter(n => 
          !(n.type === 'error' && n.title === errorNotification.title)
        ));

        addNotification(errorNotification);
      }, 500); // Дебаунсинг ошибок 500мс
    };

    websocket.on('stateChange', handleStateChange);
    websocket.on('error', handleError);

    return () => {
      if (stateChangeTimer) clearTimeout(stateChangeTimer);
      if (errorTimer) clearTimeout(errorTimer);
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