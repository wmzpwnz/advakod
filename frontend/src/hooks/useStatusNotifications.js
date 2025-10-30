import { useCallback } from 'react';

/**
 * Хук для работы с системой уведомлений о статусе
 * Предоставляет удобный API для показа различных типов уведомлений
 */
export const useStatusNotifications = () => {
  const showError = useCallback((error, options = {}) => {
    if (window.statusNotifications) {
      return window.statusNotifications.showError(error, options);
    }
    console.error('Status notifications not available:', error);
  }, []);

  const showSuccess = useCallback((message, options = {}) => {
    if (window.statusNotifications) {
      return window.statusNotifications.showSuccess(message, options);
    }
    console.log('Success:', message);
  }, []);

  const showInfo = useCallback((message, options = {}) => {
    if (window.statusNotifications) {
      return window.statusNotifications.showInfo(message, options);
    }
    console.info('Info:', message);
  }, []);

  const showModelUnavailable = useCallback(() => {
    if (window.statusNotifications) {
      return window.statusNotifications.showModelUnavailable();
    }
    console.error('Model unavailable');
  }, []);

  const removeNotification = useCallback((id) => {
    if (window.statusNotifications) {
      return window.statusNotifications.removeNotification(id);
    }
  }, []);

  // Специализированные методы для частых случаев
  const showConnectionError = useCallback((error) => {
    return showError(error, {
      title: 'Ошибка соединения',
      autoHide: false,
      actions: [
        {
          label: 'Переподключить',
          action: () => window.location.reload(),
          primary: true
        }
      ]
    });
  }, [showError]);

  const showAuthError = useCallback(() => {
    return showError('Ваша сессия истекла', {
      title: 'Требуется авторизация',
      autoHide: false,
      actions: [
        {
          label: 'Войти',
          action: () => window.location.href = '/login',
          primary: true
        }
      ]
    });
  }, [showError]);

  const showGenerationStopped = useCallback(() => {
    return showInfo('Генерация ответа остановлена пользователем', {
      duration: 3000
    });
  }, [showInfo]);

  const showGenerationTimeout = useCallback(() => {
    return showError('Превышено время ожидания ответа', {
      title: 'Таймаут генерации',
      autoHide: false,
      actions: [
        {
          label: 'Попробовать снова',
          action: () => window.location.reload(),
          primary: true
        }
      ]
    });
  }, [showError]);

  return {
    showError,
    showSuccess,
    showInfo,
    showModelUnavailable,
    removeNotification,
    // Специализированные методы
    showConnectionError,
    showAuthError,
    showGenerationStopped,
    showGenerationTimeout
  };
};

export default useStatusNotifications;