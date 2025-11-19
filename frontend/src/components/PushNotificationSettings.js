import React, { useState, useEffect } from 'react';
import { 
  BellIcon, 
  BellSlashIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline';
import { motion, AnimatePresence } from 'framer-motion';
import pushNotificationService from '../services/pushNotificationService';

const PushNotificationSettings = ({ className = '' }) => {
  const [settings, setSettings] = useState({
    isSupported: false,
    permission: 'default',
    isSubscribed: false,
    subscription: null
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Load initial settings
  useEffect(() => {
    const loadSettings = async () => {
      try {
        await pushNotificationService.initialize();
        const currentSettings = pushNotificationService.getSettings();
        setSettings(currentSettings);
      } catch (err) {
        setError('Ошибка загрузки настроек уведомлений');
        console.error('Error loading push notification settings:', err);
      }
    };

    loadSettings();

    // Listen to push notification service events
    const unsubscribe = pushNotificationService.addListener((event, data) => {
      switch (event) {
        case 'permission_changed':
          setSettings(prev => ({ ...prev, permission: data }));
          break;
        case 'subscribed':
          setSettings(prev => ({ ...prev, isSubscribed: true, subscription: data }));
          setSuccess('Push-уведомления успешно включены');
          break;
        case 'unsubscribed':
          setSettings(prev => ({ ...prev, isSubscribed: false, subscription: null }));
          setSuccess('Push-уведомления отключены');
          break;
        case 'error':
          setError(data.message || 'Произошла ошибка');
          break;
        default:
          break;
      }
    });

    return unsubscribe;
  }, []);

  // Clear messages after timeout
  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  // Enable push notifications
  const enablePushNotifications = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await pushNotificationService.subscribe();
      // Settings will be updated via event listener
    } catch (err) {
      setError(err.message || 'Не удалось включить push-уведомления');
      console.error('Error enabling push notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  // Disable push notifications
  const disablePushNotifications = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await pushNotificationService.unsubscribe();
      // Settings will be updated via event listener
    } catch (err) {
      setError(err.message || 'Не удалось отключить push-уведомления');
      console.error('Error disabling push notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  // Test push notification
  const testPushNotification = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      if (settings.isSubscribed) {
        await pushNotificationService.testNotification();
        setSuccess('Тестовое уведомление отправлено');
      } else {
        // Show local notification for testing
        await pushNotificationService.showNotification(
          'Тестовое уведомление',
          {
            body: 'Это тестовое уведомление от системы АДВАКОД',
            icon: '/favicon.ico',
            tag: 'test-notification'
          }
        );
        setSuccess('Локальное уведомление показано');
      }
    } catch (err) {
      setError(err.message || 'Не удалось отправить тестовое уведомление');
      console.error('Error testing push notification:', err);
    } finally {
      setLoading(false);
    }
  };

  // Get status icon and color
  const getStatusIcon = () => {
    if (!settings.isSupported) {
      return <XCircleIcon className="w-5 h-5 text-red-500" />;
    }
    
    if (settings.permission === 'denied') {
      return <BellSlashIcon className="w-5 h-5 text-red-500" />;
    }
    
    if (settings.isSubscribed) {
      return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
    }
    
    if (settings.permission === 'granted') {
      return <BellIcon className="w-5 h-5 text-yellow-500" />;
    }
    
    return <BellIcon className="w-5 h-5 text-gray-500" />;
  };

  const getStatusText = () => {
    if (!settings.isSupported) {
      return 'Не поддерживается браузером';
    }
    
    if (settings.permission === 'denied') {
      return 'Заблокированы браузером';
    }
    
    if (settings.isSubscribed) {
      return 'Включены';
    }
    
    if (settings.permission === 'granted') {
      return 'Разрешены, но не активны';
    }
    
    return 'Отключены';
  };

  const getStatusColor = () => {
    if (!settings.isSupported || settings.permission === 'denied') {
      return 'text-red-600 dark:text-red-400';
    }
    
    if (settings.isSubscribed) {
      return 'text-green-600 dark:text-green-400';
    }
    
    if (settings.permission === 'granted') {
      return 'text-yellow-600 dark:text-yellow-400';
    }
    
    return 'text-gray-600 dark:text-gray-400';
  };

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
            <BellIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Push-уведомления
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Получайте уведомления в браузере
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {getStatusIcon()}
          <span className={`text-sm font-medium ${getStatusColor()}`}>
            {getStatusText()}
          </span>
        </div>
      </div>

      {/* Status Messages */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center space-x-2"
          >
            <XCircleIcon className="w-5 h-5 text-red-500 flex-shrink-0" />
            <span className="text-sm text-red-700 dark:text-red-300">{error}</span>
          </motion.div>
        )}

        {success && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg flex items-center space-x-2"
          >
            <CheckCircleIcon className="w-5 h-5 text-green-500 flex-shrink-0" />
            <span className="text-sm text-green-700 dark:text-green-300">{success}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Browser Support Warning */}
      {!settings.isSupported && (
        <div className="mb-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg flex items-center space-x-2">
          <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500 flex-shrink-0" />
          <div className="text-sm text-yellow-700 dark:text-yellow-300">
            <p className="font-medium">Push-уведомления не поддерживаются</p>
            <p>Ваш браузер не поддерживает push-уведомления. Попробуйте использовать современный браузер.</p>
          </div>
        </div>
      )}

      {/* Permission Denied Warning */}
      {settings.isSupported && settings.permission === 'denied' && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center space-x-2">
          <BellSlashIcon className="w-5 h-5 text-red-500 flex-shrink-0" />
          <div className="text-sm text-red-700 dark:text-red-300">
            <p className="font-medium">Уведомления заблокированы</p>
            <p>Чтобы включить уведомления, разрешите их в настройках браузера для этого сайта.</p>
          </div>
        </div>
      )}

      {/* Controls */}
      {settings.isSupported && settings.permission !== 'denied' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                Статус подписки
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {settings.isSubscribed 
                  ? 'Вы подписаны на push-уведомления'
                  : 'Вы не подписаны на push-уведомления'
                }
              </p>
            </div>
            <div className="flex space-x-2">
              {settings.isSubscribed ? (
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={disablePushNotifications}
                  disabled={loading}
                  className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? 'Отключение...' : 'Отключить'}
                </motion.button>
              ) : (
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={enablePushNotifications}
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? 'Включение...' : 'Включить'}
                </motion.button>
              )}
            </div>
          </div>

          {/* Test Button */}
          <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  Тестирование
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Отправить тестовое уведомление
                </p>
              </div>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={testPushNotification}
                disabled={loading || settings.permission === 'denied'}
                className="px-4 py-2 bg-gray-600 text-white text-sm font-medium rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? 'Отправка...' : 'Тест'}
              </motion.button>
            </div>
          </div>

          {/* Info */}
          <div className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg flex items-start space-x-2">
            <InformationCircleIcon className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-700 dark:text-blue-300">
              <p className="font-medium mb-1">О push-уведомлениях</p>
              <ul className="text-xs space-y-1 list-disc list-inside">
                <li>Получайте уведомления даже когда сайт закрыт</li>
                <li>Критические уведомления требуют взаимодействия</li>
                <li>Вы можете отключить уведомления в любое время</li>
                <li>Настройки сохраняются в браузере</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PushNotificationSettings;