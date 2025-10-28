import { useState, useEffect, useCallback } from 'react';
import { getApiUrl } from '../config/api';

export const useServiceWorker = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [swRegistration, setSwRegistration] = useState(null);
  const [isUpdateAvailable, setIsUpdateAvailable] = useState(false);
  const [notificationPermission, setNotificationPermission] = useState('default');

  // Регистрация Service Worker (только в production). В dev — гарантированно удаляем SW
  useEffect(() => {
    if (!('serviceWorker' in navigator)) {
      return;
    }

    if (process.env.NODE_ENV === 'production') {
      navigator.serviceWorker
        .register('/sw.js')
        .then((registration) => {
          console.log('Service Worker registered:', registration);
          setSwRegistration(registration);

          // Проверяем обновления
          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            if (newWorker) {
              newWorker.addEventListener('statechange', () => {
                if (
                  newWorker.state === 'installed' &&
                  navigator.serviceWorker.controller
                ) {
                  setIsUpdateAvailable(true);
                }
              });
            }
          });
        })
        .catch((error) => {
          console.error('Service Worker registration failed:', error);
        });
    } else {
      // Development: удаляем все существующие SW, чтобы избежать конфликтов с HMR
      navigator.serviceWorker
        .getRegistrations()
        .then((regs) => Promise.all(regs.map((r) => r.unregister())))
        .catch(() => {});
    }
  }, []);

  // Отслеживание статуса подключения
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Проверка разрешений на уведомления
  useEffect(() => {
    if ('Notification' in window) {
      setNotificationPermission(Notification.permission);
    }
  }, []);

  // Обновление Service Worker
  const updateServiceWorker = useCallback(() => {
    if (swRegistration && swRegistration.waiting) {
      swRegistration.waiting.postMessage({ type: 'SKIP_WAITING' });
      window.location.reload();
    }
  }, [swRegistration]);

  // Запрос разрешения на уведомления
  const requestNotificationPermission = useCallback(async () => {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission();
      setNotificationPermission(permission);
      return permission;
    }
    return 'denied';
  }, []);

  // Отправка push уведомления
  const sendPushNotification = useCallback((title, options = {}) => {
    if (notificationPermission === 'granted') {
      const notification = new Notification(title, {
        icon: '/logo192.png',
        badge: '/logo192.png',
        tag: 'ai-lawyer-notification',
        ...options
      });

      notification.onclick = () => {
        window.focus();
        notification.close();
      };

      return notification;
    }
    return null;
  }, [notificationPermission]);

  // Подписка на push уведомления
  const subscribeToPush = useCallback(async () => {
    if (!swRegistration) return null;

    try {
      const subscription = await swRegistration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: process.env.REACT_APP_VAPID_PUBLIC_KEY
      });

      // Отправляем подписку на сервер
      const response = await fetch(getApiUrl('/notifications/subscribe'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(subscription)
      });

      if (response.ok) {
        return subscription;
      }
    } catch (error) {
      console.error('Push subscription failed:', error);
    }

    return null;
  }, [swRegistration]);

  // Отписка от push уведомлений
  const unsubscribeFromPush = useCallback(async () => {
    if (!swRegistration) return false;

    try {
      const subscription = await swRegistration.pushManager.getSubscription();
      if (subscription) {
        await subscription.unsubscribe();
        
        // Уведомляем сервер об отписке
        await fetch(getApiUrl('/notifications/unsubscribe'), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ endpoint: subscription.endpoint })
        });

        return true;
      }
    } catch (error) {
      console.error('Push unsubscription failed:', error);
    }

    return false;
  }, [swRegistration]);

  // Синхронизация в фоне
  const triggerBackgroundSync = useCallback((tag = 'background-sync') => {
    if (swRegistration && 'sync' in window.ServiceWorkerRegistration.prototype) {
      return swRegistration.sync.register(tag);
    }
    return Promise.resolve();
  }, [swRegistration]);

  // Кэширование данных
  const cacheData = useCallback(async (key, data) => {
    if ('caches' in window) {
      const cache = await caches.open('ai-lawyer-data');
      await cache.put(key, new Response(JSON.stringify(data)));
    }
  }, []);

  // Получение данных из кэша
  const getCachedData = useCallback(async (key) => {
    if ('caches' in window) {
      const cache = await caches.open('ai-lawyer-data');
      const response = await cache.match(key);
      if (response) {
        return response.json();
      }
    }
    return null;
  }, []);

  // Очистка кэша
  const clearCache = useCallback(async () => {
    if ('caches' in window) {
      const cacheNames = await caches.keys();
      await Promise.all(
        cacheNames.map(cacheName => caches.delete(cacheName))
      );
    }
  }, []);

  // Получение информации о кэше
  const getCacheInfo = useCallback(async () => {
    if ('caches' in window) {
      const cacheNames = await caches.keys();
      const cacheInfo = {};

      for (const cacheName of cacheNames) {
        const cache = await caches.open(cacheName);
        const keys = await cache.keys();
        cacheInfo[cacheName] = keys.length;
      }

      return cacheInfo;
    }
    return {};
  }, []);

  return {
    isOnline,
    swRegistration,
    isUpdateAvailable,
    notificationPermission,
    updateServiceWorker,
    requestNotificationPermission,
    sendPushNotification,
    subscribeToPush,
    unsubscribeFromPush,
    triggerBackgroundSync,
    cacheData,
    getCachedData,
    clearCache,
    getCacheInfo
  };
};

export default useServiceWorker;
