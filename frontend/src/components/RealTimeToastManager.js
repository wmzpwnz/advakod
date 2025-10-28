import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CheckCircle, 
  AlertTriangle, 
  AlertCircle, 
  Info, 
  X,
  Bell,
  Users,
  Activity,
  Database,
  Shield,
  TrendingUp
} from 'lucide-react';

const RealTimeToastManager = ({ 
  realTimeAPI,
  maxToasts = 5,
  autoHideDuration = 5000,
  position = 'top-right' 
}) => {
  const [toasts, setToasts] = useState([]);
  const [toastId, setToastId] = useState(0);

  // Generate unique toast ID
  const generateToastId = useCallback(() => {
    setToastId(prev => prev + 1);
    return toastId + 1;
  }, [toastId]);

  // Add toast
  const addToast = useCallback((toast) => {
    const id = generateToastId();
    const newToast = {
      id,
      timestamp: Date.now(),
      autoHide: toast.autoHide !== false,
      ...toast
    };

    setToasts(prev => {
      const updated = [newToast, ...prev];
      // Keep only the latest toasts
      return updated.slice(0, maxToasts);
    });

    // Auto-hide toast
    if (newToast.autoHide) {
      setTimeout(() => {
        removeToast(id);
      }, autoHideDuration);
    }

    return id;
  }, [generateToastId, maxToasts, autoHideDuration]);

  // Remove toast
  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  // Clear all toasts
  const clearAllToasts = useCallback(() => {
    setToasts([]);
  }, []);

  // Listen for real-time events
  useEffect(() => {
    if (!realTimeAPI) return;

    // Dashboard updates
    const handleDashboardUpdate = (data) => {
      addToast({
        type: 'info',
        title: 'Дашборд обновлен',
        message: 'Получены новые данные дашборда',
        icon: TrendingUp,
        data: data
      });
    };

    // User activity updates
    const handleUserActivity = (data) => {
      if (data.activity && data.activity.length > 0) {
        const latestActivity = data.activity[0];
        addToast({
          type: 'info',
          title: 'Активность пользователей',
          message: `${data.onlineUsers} пользователей онлайн`,
          icon: Users,
          data: data
        });
      }
    };

    // System alerts
    const handleSystemAlert = (alert) => {
      const alertTypes = {
        info: { type: 'info', icon: Info },
        warning: { type: 'warning', icon: AlertTriangle },
        error: { type: 'error', icon: AlertCircle },
        critical: { type: 'error', icon: AlertCircle }
      };

      const config = alertTypes[alert.severity] || alertTypes.info;

      addToast({
        type: config.type,
        title: alert.title || 'Системное уведомление',
        message: alert.message,
        icon: config.icon,
        autoHide: alert.severity !== 'critical',
        data: alert
      });
    };

    // Moderation queue updates
    const handleModerationUpdate = (data) => {
      if (data.queueSize > 0) {
        addToast({
          type: 'info',
          title: 'Очередь модерации',
          message: `${data.queueSize} сообщений ожидают модерации`,
          icon: Shield,
          data: data
        });
      }
    };

    // Notifications
    const handleNotification = (notification) => {
      const priorityTypes = {
        low: 'info',
        normal: 'info',
        high: 'warning',
        critical: 'error'
      };

      addToast({
        type: priorityTypes[notification.priority] || 'info',
        title: notification.title,
        message: notification.message,
        icon: Bell,
        autoHide: notification.priority !== 'critical',
        data: notification,
        actions: [
          {
            label: 'Отметить как прочитанное',
            onClick: () => realTimeAPI.markNotificationAsRead(notification.id)
          }
        ]
      });
    };

    // Connection status changes
    const handleConnectionChange = (status) => {
      if (status === 'connected') {
        addToast({
          type: 'success',
          title: 'Подключение восстановлено',
          message: 'Real-time обновления активны',
          icon: CheckCircle
        });
      } else if (status === 'disconnected' || status === 'error') {
        addToast({
          type: 'error',
          title: 'Соединение потеряно',
          message: 'Real-time обновления недоступны',
          icon: AlertCircle,
          autoHide: false
        });
      }
    };

    // Subscribe to events (if realTimeAPI provides event emitter)
    if (realTimeAPI.on) {
      realTimeAPI.on('dashboardUpdate', handleDashboardUpdate);
      realTimeAPI.on('userActivity', handleUserActivity);
      realTimeAPI.on('systemAlert', handleSystemAlert);
      realTimeAPI.on('moderationUpdate', handleModerationUpdate);
      realTimeAPI.on('notification', handleNotification);
      realTimeAPI.on('connectionChange', handleConnectionChange);
    }

    return () => {
      if (realTimeAPI.off) {
        realTimeAPI.off('dashboardUpdate', handleDashboardUpdate);
        realTimeAPI.off('userActivity', handleUserActivity);
        realTimeAPI.off('systemAlert', handleSystemAlert);
        realTimeAPI.off('moderationUpdate', handleModerationUpdate);
        realTimeAPI.off('notification', handleNotification);
        realTimeAPI.off('connectionChange', handleConnectionChange);
      }
    };
  }, [realTimeAPI, addToast]);

  // Get toast style based on type
  const getToastStyle = (type) => {
    const styles = {
      success: {
        bg: 'bg-green-50 dark:bg-green-900/20',
        border: 'border-green-200 dark:border-green-800',
        text: 'text-green-800 dark:text-green-200',
        icon: 'text-green-500'
      },
      error: {
        bg: 'bg-red-50 dark:bg-red-900/20',
        border: 'border-red-200 dark:border-red-800',
        text: 'text-red-800 dark:text-red-200',
        icon: 'text-red-500'
      },
      warning: {
        bg: 'bg-yellow-50 dark:bg-yellow-900/20',
        border: 'border-yellow-200 dark:border-yellow-800',
        text: 'text-yellow-800 dark:text-yellow-200',
        icon: 'text-yellow-500'
      },
      info: {
        bg: 'bg-blue-50 dark:bg-blue-900/20',
        border: 'border-blue-200 dark:border-blue-800',
        text: 'text-blue-800 dark:text-blue-200',
        icon: 'text-blue-500'
      }
    };
    return styles[type] || styles.info;
  };

  // Get position classes
  const getPositionClasses = () => {
    const positions = {
      'top-right': 'top-4 right-4',
      'top-left': 'top-4 left-4',
      'bottom-right': 'bottom-4 right-4',
      'bottom-left': 'bottom-4 left-4',
      'top-center': 'top-4 left-1/2 transform -translate-x-1/2',
      'bottom-center': 'bottom-4 left-1/2 transform -translate-x-1/2'
    };
    return positions[position] || positions['top-right'];
  };

  return (
    <div className={`fixed z-50 ${getPositionClasses()}`}>
      <AnimatePresence>
        {toasts.map((toast) => {
          const style = getToastStyle(toast.type);
          const ToastIcon = toast.icon || Info;

          return (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, x: position.includes('right') ? 300 : -300, scale: 0.9 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: position.includes('right') ? 300 : -300, scale: 0.9 }}
              className={`
                mb-3 max-w-sm w-full rounded-lg border shadow-lg
                ${style.bg} ${style.border}
              `}
            >
              <div className="p-4">
                <div className="flex items-start">
                  <div className={`flex-shrink-0 ${style.icon}`}>
                    <ToastIcon className="w-5 h-5" />
                  </div>
                  
                  <div className="ml-3 flex-1">
                    <div className={`text-sm font-medium ${style.text}`}>
                      {toast.title}
                    </div>
                    {toast.message && (
                      <div className={`mt-1 text-sm ${style.text} opacity-80`}>
                        {toast.message}
                      </div>
                    )}
                    
                    {/* Actions */}
                    {toast.actions && toast.actions.length > 0 && (
                      <div className="mt-2 flex space-x-2">
                        {toast.actions.map((action, index) => (
                          <button
                            key={index}
                            onClick={() => {
                              action.onClick();
                              removeToast(toast.id);
                            }}
                            className={`
                              text-xs px-2 py-1 rounded border
                              ${style.text} ${style.border}
                              hover:bg-opacity-20 hover:bg-current
                              transition-colors
                            `}
                          >
                            {action.label}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  
                  <div className="ml-4 flex-shrink-0">
                    <button
                      onClick={() => removeToast(toast.id)}
                      className={`
                        inline-flex rounded-md p-1.5 focus:outline-none focus:ring-2 focus:ring-offset-2
                        ${style.text} hover:bg-opacity-20 hover:bg-current
                      `}
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
              
              {/* Progress bar for auto-hide */}
              {toast.autoHide && (
                <motion.div
                  className={`h-1 ${style.icon.replace('text-', 'bg-')} opacity-30`}
                  initial={{ width: '100%' }}
                  animate={{ width: '0%' }}
                  transition={{ duration: autoHideDuration / 1000, ease: 'linear' }}
                />
              )}
            </motion.div>
          );
        })}
      </AnimatePresence>
      
      {/* Clear all button */}
      {toasts.length > 1 && (
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          onClick={clearAllToasts}
          className="mt-2 w-full text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
        >
          Очистить все ({toasts.length})
        </motion.button>
      )}
    </div>
  );
};

export default RealTimeToastManager;