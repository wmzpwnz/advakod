import { useState, useEffect, useCallback, useRef } from 'react';
import pushNotificationService from '../services/pushNotificationService';

export const usePushNotifications = (options = {}) => {
  const {
    autoInitialize = true,
    onPermissionChange = null,
    onSubscriptionChange = null,
    onNotificationReceived = null,
    onError = null
  } = options;

  const [isSupported, setIsSupported] = useState(false);
  const [permission, setPermission] = useState('default');
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [initialized, setInitialized] = useState(false);

  const mountedRef = useRef(true);

  // Initialize push notifications
  const initialize = useCallback(async () => {
    if (!mountedRef.current) return;

    setLoading(true);
    setError(null);

    try {
      const success = await pushNotificationService.initialize();
      
      if (!mountedRef.current) return;

      const settings = pushNotificationService.getSettings();
      setIsSupported(settings.isSupported);
      setPermission(settings.permission);
      setIsSubscribed(settings.isSubscribed);
      setSubscription(settings.subscription);
      setInitialized(true);

      return success;
    } catch (err) {
      if (mountedRef.current) {
        setError(err.message);
        if (onError) onError(err);
      }
      return false;
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, [onError]);

  // Request permission
  const requestPermission = useCallback(async () => {
    if (!mountedRef.current) return false;

    setLoading(true);
    setError(null);

    try {
      const granted = await pushNotificationService.requestPermission();
      
      if (!mountedRef.current) return granted;

      const newPermission = pushNotificationService.getPermission();
      setPermission(newPermission);
      
      if (onPermissionChange) {
        onPermissionChange(newPermission);
      }

      return granted;
    } catch (err) {
      if (mountedRef.current) {
        setError(err.message);
        if (onError) onError(err);
      }
      return false;
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, [onPermissionChange, onError]);

  // Subscribe to push notifications
  const subscribe = useCallback(async () => {
    if (!mountedRef.current) return null;

    setLoading(true);
    setError(null);

    try {
      const newSubscription = await pushNotificationService.subscribe();
      
      if (!mountedRef.current) return newSubscription;

      setIsSubscribed(true);
      setSubscription(newSubscription);
      setPermission('granted');
      
      if (onSubscriptionChange) {
        onSubscriptionChange(true, newSubscription);
      }

      return newSubscription;
    } catch (err) {
      if (mountedRef.current) {
        setError(err.message);
        if (onError) onError(err);
      }
      return null;
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, [onSubscriptionChange, onError]);

  // Unsubscribe from push notifications
  const unsubscribe = useCallback(async () => {
    if (!mountedRef.current) return false;

    setLoading(true);
    setError(null);

    try {
      const success = await pushNotificationService.unsubscribe();
      
      if (!mountedRef.current) return success;

      if (success) {
        setIsSubscribed(false);
        setSubscription(null);
        
        if (onSubscriptionChange) {
          onSubscriptionChange(false, null);
        }
      }

      return success;
    } catch (err) {
      if (mountedRef.current) {
        setError(err.message);
        if (onError) onError(err);
      }
      return false;
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, [onSubscriptionChange, onError]);

  // Show local notification
  const showNotification = useCallback(async (title, options = {}) => {
    if (!mountedRef.current) return false;

    try {
      await pushNotificationService.showNotification(title, options);
      
      if (onNotificationReceived) {
        onNotificationReceived({ title, options, type: 'local' });
      }

      return true;
    } catch (err) {
      if (mountedRef.current) {
        setError(err.message);
        if (onError) onError(err);
      }
      return false;
    }
  }, [onNotificationReceived, onError]);

  // Test push notification
  const testNotification = useCallback(async () => {
    if (!mountedRef.current) return false;

    setLoading(true);
    setError(null);

    try {
      await pushNotificationService.testNotification();
      return true;
    } catch (err) {
      if (mountedRef.current) {
        setError(err.message);
        if (onError) onError(err);
      }
      return false;
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, [onError]);

  // Get current settings
  const getSettings = useCallback(() => {
    return {
      isSupported,
      permission,
      isSubscribed,
      subscription,
      loading,
      error,
      initialized
    };
  }, [isSupported, permission, isSubscribed, subscription, loading, error, initialized]);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Listen to push notification service events
  useEffect(() => {
    const handlePushEvent = (event, data) => {
      if (!mountedRef.current) return;

      switch (event) {
        case 'permission_changed':
          setPermission(data);
          if (onPermissionChange) {
            onPermissionChange(data);
          }
          break;

        case 'subscribed':
          setIsSubscribed(true);
          setSubscription(data);
          if (onSubscriptionChange) {
            onSubscriptionChange(true, data);
          }
          break;

        case 'unsubscribed':
          setIsSubscribed(false);
          setSubscription(null);
          if (onSubscriptionChange) {
            onSubscriptionChange(false, null);
          }
          break;

        case 'notification_shown':
          if (onNotificationReceived) {
            onNotificationReceived({ ...data, type: 'shown' });
          }
          break;

        case 'error':
          setError(data.message || 'Unknown error');
          if (onError) {
            onError(data);
          }
          break;

        case 'initialized':
          setInitialized(true);
          break;

        default:
          break;
      }
    };

    const unsubscribe = pushNotificationService.addListener(handlePushEvent);
    return unsubscribe;
  }, [onPermissionChange, onSubscriptionChange, onNotificationReceived, onError]);

  // Auto-initialize
  useEffect(() => {
    if (autoInitialize && !initialized) {
      initialize();
    }
  }, [autoInitialize, initialized, initialize]);

  // Cleanup
  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  return {
    // State
    isSupported,
    permission,
    isSubscribed,
    subscription,
    loading,
    error,
    initialized,

    // Actions
    initialize,
    requestPermission,
    subscribe,
    unsubscribe,
    showNotification,
    testNotification,
    getSettings,
    clearError
  };
};

// Simplified hook for basic push notification status
export const usePushNotificationStatus = () => {
  const [status, setStatus] = useState({
    isSupported: false,
    permission: 'default',
    isSubscribed: false,
    canSubscribe: false
  });

  useEffect(() => {
    const updateStatus = () => {
      const settings = pushNotificationService.getSettings();
      setStatus({
        isSupported: settings.isSupported,
        permission: settings.permission,
        isSubscribed: settings.isSubscribed,
        canSubscribe: settings.isSupported && settings.permission !== 'denied'
      });
    };

    // Initial update
    updateStatus();

    // Listen for changes
    const unsubscribe = pushNotificationService.addListener(() => {
      updateStatus();
    });

    return unsubscribe;
  }, []);

  return status;
};

export default usePushNotifications;