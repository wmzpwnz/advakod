import { useEffect, useState, useCallback, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import adminWebSocketService from '../services/adminWebSocketService';

export const useAdminWebSocket = (options = {}) => {
  const { user, token } = useAuth();
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [lastMessage, setLastMessage] = useState(null);
  const [error, setError] = useState(null);
  const reconnectTimeoutRef = useRef(null);
  
  const {
    autoConnect = true,
    subscriptions = [],
    onMessage,
    onError,
    onConnect,
    onDisconnect
  } = options;

  // Connect to WebSocket
  const connect = useCallback(async () => {
    if (!user?.is_admin || !token) {
      console.warn('Cannot connect to admin WebSocket: user not admin or no token');
      return;
    }

    try {
      setConnectionStatus('connecting');
      await adminWebSocketService.connect(token, user.id);
      setConnectionStatus('connected');
      setError(null);
      
      // Subscribe to requested channels
      subscriptions.forEach(subscription => {
        if (typeof subscription === 'string') {
          adminWebSocketService.send('subscribe', { channel: subscription });
        } else if (subscription.channel) {
          adminWebSocketService.send('subscribe', subscription);
        }
      });
      
      if (onConnect) onConnect();
    } catch (err) {
      setConnectionStatus('error');
      setError(err.message);
      if (onError) onError(err);
    }
  }, [user, token, subscriptions, onConnect, onError]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    adminWebSocketService.disconnect();
    setConnectionStatus('disconnected');
    if (onDisconnect) onDisconnect();
  }, [onDisconnect]);

  // Send message
  const sendMessage = useCallback((type, payload) => {
    return adminWebSocketService.send(type, payload);
  }, []);

  // Subscribe to channel
  const subscribe = useCallback((channel, options = {}) => {
    adminWebSocketService.send('subscribe', { channel, ...options });
  }, []);

  // Unsubscribe from channel
  const unsubscribe = useCallback((channel) => {
    adminWebSocketService.unsubscribe(channel);
  }, []);

  // Request data refresh
  const requestRefresh = useCallback((dataType) => {
    adminWebSocketService.requestDataRefresh(dataType);
  }, []);

  // Send admin action
  const sendAdminAction = useCallback((action, data) => {
    adminWebSocketService.sendAdminAction(action, data);
  }, []);

  // Setup event listeners
  useEffect(() => {
    const handleMessage = (data) => {
      setLastMessage(data);
      if (onMessage) onMessage(data);
    };

    const handleConnect = () => {
      setConnectionStatus('connected');
      setError(null);
      if (onConnect) onConnect();
    };

    const handleDisconnect = (event) => {
      setConnectionStatus('disconnected');
      if (onDisconnect) onDisconnect(event);
      
      // Auto-reconnect after delay
      if (autoConnect && event.code !== 1000) {
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 3000);
      }
    };

    const handleError = (error) => {
      setConnectionStatus('error');
      setError(error.message || 'WebSocket error');
      if (onError) onError(error);
    };

    // Add event listeners
    adminWebSocketService.on('message', handleMessage);
    adminWebSocketService.on('connected', handleConnect);
    adminWebSocketService.on('disconnected', handleDisconnect);
    adminWebSocketService.on('error', handleError);

    return () => {
      // Remove event listeners
      adminWebSocketService.off('message', handleMessage);
      adminWebSocketService.off('connected', handleConnect);
      adminWebSocketService.off('disconnected', handleDisconnect);
      adminWebSocketService.off('error', handleError);
      
      // Clear reconnect timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [onMessage, onConnect, onDisconnect, onError, autoConnect, connect]);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect && user?.is_admin && token) {
      connect();
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [autoConnect, connect, user, token]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (autoConnect) {
        disconnect();
      }
    };
  }, [disconnect, autoConnect]);

  return {
    connectionStatus,
    lastMessage,
    error,
    connect,
    disconnect,
    sendMessage,
    subscribe,
    unsubscribe,
    requestRefresh,
    sendAdminAction,
    isConnected: connectionStatus === 'connected',
    isConnecting: connectionStatus === 'connecting',
    hasError: connectionStatus === 'error'
  };
};

// Hook for dashboard real-time updates
export const useAdminDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);

  const { isConnected, subscribe, unsubscribe } = useAdminWebSocket({
    subscriptions: ['admin_dashboard'],
    onMessage: (data) => {
      if (data.type === 'dashboard_update') {
        setDashboardData(data.payload);
        setLastUpdate(new Date());
      }
    }
  });

  useEffect(() => {
    if (isConnected) {
      subscribe('admin_dashboard');
    }
    
    return () => {
      unsubscribe('admin_dashboard');
    };
  }, [isConnected, subscribe, unsubscribe]);

  return {
    dashboardData,
    lastUpdate,
    isConnected
  };
};

// Hook for user activity updates
export const useUserActivity = () => {
  const [userActivity, setUserActivity] = useState([]);
  const [onlineUsers, setOnlineUsers] = useState(0);

  const { isConnected, subscribe, unsubscribe } = useAdminWebSocket({
    subscriptions: ['user_activity'],
    onMessage: (data) => {
      if (data.type === 'user_activity') {
        setUserActivity(prev => [data.payload, ...prev.slice(0, 49)]); // Keep last 50
      } else if (data.type === 'online_users_count') {
        setOnlineUsers(data.payload.count);
      }
    }
  });

  useEffect(() => {
    if (isConnected) {
      subscribe('user_activity');
    }
    
    return () => {
      unsubscribe('user_activity');
    };
  }, [isConnected, subscribe, unsubscribe]);

  return {
    userActivity,
    onlineUsers,
    isConnected
  };
};

// Hook for system alerts
export const useSystemAlerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [criticalAlerts, setCriticalAlerts] = useState(0);

  const { isConnected, subscribe, unsubscribe } = useAdminWebSocket({
    subscriptions: ['system_alerts'],
    onMessage: (data) => {
      if (data.type === 'system_alert') {
        const alert = { ...data.payload, timestamp: new Date() };
        setAlerts(prev => [alert, ...prev.slice(0, 99)]); // Keep last 100
        
        if (alert.severity === 'critical') {
          setCriticalAlerts(prev => prev + 1);
        }
      }
    }
  });

  const dismissAlert = useCallback((alertId) => {
    setAlerts(prev => prev.filter(alert => alert.id !== alertId));
  }, []);

  const clearCriticalCount = useCallback(() => {
    setCriticalAlerts(0);
  }, []);

  useEffect(() => {
    if (isConnected) {
      subscribe('system_alerts');
    }
    
    return () => {
      unsubscribe('system_alerts');
    };
  }, [isConnected, subscribe, unsubscribe]);

  return {
    alerts,
    criticalAlerts,
    dismissAlert,
    clearCriticalCount,
    isConnected
  };
};

// Hook for moderation queue updates
export const useModerationQueue = () => {
  const [queueSize, setQueueSize] = useState(0);
  const [pendingReviews, setPendingReviews] = useState([]);
  const [recentActions, setRecentActions] = useState([]);

  const { isConnected, subscribe, unsubscribe, sendAdminAction } = useAdminWebSocket({
    subscriptions: ['moderation_queue'],
    onMessage: (data) => {
      switch (data.type) {
        case 'moderation_queue_update':
          setQueueSize(data.payload.queue_size);
          setPendingReviews(data.payload.pending_reviews || []);
          break;
        case 'moderation_action':
          setRecentActions(prev => [data.payload, ...prev.slice(0, 19)]); // Keep last 20
          break;
      }
    }
  });

  const submitReview = useCallback((messageId, review) => {
    sendAdminAction('submit_review', { message_id: messageId, review });
  }, [sendAdminAction]);

  useEffect(() => {
    if (isConnected) {
      subscribe('moderation_queue');
    }
    
    return () => {
      unsubscribe('moderation_queue');
    };
  }, [isConnected, subscribe, unsubscribe]);

  return {
    queueSize,
    pendingReviews,
    recentActions,
    submitReview,
    isConnected
  };
};

// Hook for real-time notifications
export const useAdminNotifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  const { isConnected, subscribe, unsubscribe, sendAdminAction } = useAdminWebSocket({
    subscriptions: ['notifications'],
    onMessage: (data) => {
      if (data.type === 'notification') {
        const notification = { ...data.payload, timestamp: new Date() };
        setNotifications(prev => [notification, ...prev.slice(0, 49)]); // Keep last 50
        
        if (!notification.read) {
          setUnreadCount(prev => prev + 1);
        }
      }
    }
  });

  const markAsRead = useCallback((notificationId) => {
    sendAdminAction('mark_notification_read', { notification_id: notificationId });
    setNotifications(prev => 
      prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
    );
    setUnreadCount(prev => Math.max(0, prev - 1));
  }, [sendAdminAction]);

  const markAllAsRead = useCallback(() => {
    sendAdminAction('mark_all_notifications_read', {});
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    setUnreadCount(0);
  }, [sendAdminAction]);

  useEffect(() => {
    if (isConnected) {
      subscribe('notifications');
    }
    
    return () => {
      unsubscribe('notifications');
    };
  }, [isConnected, subscribe, unsubscribe]);

  return {
    notifications,
    unreadCount,
    markAsRead,
    markAllAsRead,
    isConnected
  };
};

export default useAdminWebSocket;