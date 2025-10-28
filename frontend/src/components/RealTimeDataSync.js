import React, { useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { 
  useAdminWebSocket, 
  useAdminDashboard, 
  useUserActivity, 
  useSystemAlerts, 
  useModerationQueue, 
  useAdminNotifications 
} from '../hooks/useAdminWebSocket';
import { 
  useDashboardSync,
  useNotificationSync,
  useUserActivitySync,
  useSystemAlertsSync,
  useModerationQueueSync
} from '../hooks/useTabSync';

/**
 * RealTimeDataSync - компонент для синхронизации данных в реальном времени
 * Объединяет WebSocket обновления с синхронизацией между вкладками
 */
const RealTimeDataSync = ({ 
  onDashboardUpdate,
  onUserActivityUpdate,
  onSystemAlert,
  onModerationQueueUpdate,
  onNotificationUpdate,
  children 
}) => {
  const { user, token } = useAuth();

  // WebSocket connection for real-time updates
  const { 
    connectionStatus, 
    isConnected, 
    sendAdminAction,
    requestRefresh 
  } = useAdminWebSocket({
    autoConnect: true,
    subscriptions: [
      'admin_dashboard', 
      'user_activity', 
      'system_alerts', 
      'moderation_queue', 
      'notifications',
      'real_time_metrics',
      'backup_status',
      'task_updates'
    ],
    onMessage: (data) => {
      console.log('Real-time message received:', data.type, data.payload);
    },
    onConnect: () => {
      console.log('Real-time connection established');
      // Request initial data refresh
      requestRefresh('dashboard');
      requestRefresh('user_activity');
      requestRefresh('system_metrics');
    },
    onDisconnect: () => {
      console.log('Real-time connection lost');
    },
    onError: (error) => {
      console.error('Real-time connection error:', error);
    }
  });

  // Real-time dashboard data
  const { 
    dashboardData: realtimeDashboardData, 
    lastUpdate: dashboardLastUpdate 
  } = useAdminDashboard();

  // Real-time user activity
  const { 
    userActivity, 
    onlineUsers 
  } = useUserActivity();

  // Real-time system alerts
  const { 
    alerts: systemAlerts, 
    criticalAlerts, 
    dismissAlert,
    clearCriticalCount 
  } = useSystemAlerts();

  // Real-time moderation queue
  const { 
    queueSize: moderationQueueSize, 
    pendingReviews,
    recentActions: moderationActions,
    submitReview 
  } = useModerationQueue();

  // Real-time notifications
  const { 
    notifications, 
    unreadCount: notificationCount, 
    markAsRead, 
    markAllAsRead 
  } = useAdminNotifications();

  // Tab synchronization hooks
  const { 
    syncedDashboardData, 
    syncDashboard 
  } = useDashboardSync();

  const { 
    syncedNotifications, 
    unreadCount: syncedUnreadCount, 
    syncNotifications,
    markAsReadAcrossTabs 
  } = useNotificationSync();

  const { 
    syncedUserActivity, 
    onlineUsers: syncedOnlineUsers, 
    syncUserActivity 
  } = useUserActivitySync();

  const { 
    syncedAlerts, 
    criticalCount: syncedCriticalCount, 
    syncSystemAlerts,
    dismissAlertAcrossTabs 
  } = useSystemAlertsSync();

  const { 
    syncedQueueSize, 
    syncModerationQueue 
  } = useModerationQueueSync();

  // Handle dashboard updates
  useEffect(() => {
    if (realtimeDashboardData) {
      // Sync data across tabs
      syncDashboard(realtimeDashboardData);
      
      // Notify parent component
      if (onDashboardUpdate) {
        onDashboardUpdate(realtimeDashboardData);
      }
    }
  }, [realtimeDashboardData, syncDashboard, onDashboardUpdate]);

  // Handle user activity updates
  useEffect(() => {
    if (userActivity.length > 0 || onlineUsers > 0) {
      const activityData = { activity: userActivity, onlineUsers };
      
      // Sync data across tabs
      syncUserActivity(userActivity, onlineUsers);
      
      // Notify parent component
      if (onUserActivityUpdate) {
        onUserActivityUpdate(activityData);
      }
    }
  }, [userActivity, onlineUsers, syncUserActivity, onUserActivityUpdate]);

  // Handle system alerts
  useEffect(() => {
    if (systemAlerts.length > 0) {
      // Sync alerts across tabs
      syncSystemAlerts(systemAlerts, criticalAlerts);
      
      // Notify parent component
      if (onSystemAlert) {
        systemAlerts.forEach(alert => {
          if (!alert.notified) {
            onSystemAlert(alert);
            alert.notified = true; // Mark as notified to prevent duplicates
          }
        });
      }
    }
  }, [systemAlerts, criticalAlerts, syncSystemAlerts, onSystemAlert]);

  // Handle moderation queue updates
  useEffect(() => {
    if (moderationQueueSize > 0 || pendingReviews.length > 0) {
      const queueData = {
        queueSize: moderationQueueSize,
        pendingReviews,
        recentActions: moderationActions
      };
      
      // Sync data across tabs
      syncModerationQueue(moderationQueueSize, pendingReviews, moderationActions);
      
      // Notify parent component
      if (onModerationQueueUpdate) {
        onModerationQueueUpdate(queueData);
      }
    }
  }, [moderationQueueSize, pendingReviews, moderationActions, syncModerationQueue, onModerationQueueUpdate]);

  // Handle notifications
  useEffect(() => {
    if (notifications.length > 0) {
      // Sync notifications across tabs
      syncNotifications(notifications, notificationCount);
      
      // Notify parent component
      if (onNotificationUpdate) {
        notifications.forEach(notification => {
          if (!notification.notified) {
            onNotificationUpdate(notification);
            notification.notified = true; // Mark as notified to prevent duplicates
          }
        });
      }
    }
  }, [notifications, notificationCount, syncNotifications, onNotificationUpdate]);

  // Provide methods to parent components
  const realTimeAPI = {
    // Connection status
    isConnected,
    connectionStatus,
    
    // Dashboard
    dashboardData: syncedDashboardData || realtimeDashboardData,
    refreshDashboard: () => requestRefresh('dashboard'),
    
    // User activity
    userActivity: syncedUserActivity || userActivity,
    onlineUsers: syncedOnlineUsers || onlineUsers,
    refreshUserActivity: () => requestRefresh('user_activity'),
    
    // System alerts
    systemAlerts: syncedAlerts || systemAlerts,
    criticalAlerts: syncedCriticalCount || criticalAlerts,
    dismissAlert: (alertId) => {
      dismissAlert(alertId);
      dismissAlertAcrossTabs(alertId);
    },
    clearCriticalCount,
    
    // Moderation queue
    moderationQueueSize: syncedQueueSize || moderationQueueSize,
    pendingReviews,
    moderationActions,
    submitReview,
    
    // Notifications
    notifications: syncedNotifications || notifications,
    notificationCount: syncedUnreadCount || notificationCount,
    markNotificationAsRead: (notificationId) => {
      markAsRead(notificationId);
      markAsReadAcrossTabs(notificationId);
    },
    markAllNotificationsAsRead: () => {
      markAllAsRead();
      syncNotifications(notifications.map(n => ({ ...n, read: true })), 0);
    },
    
    // Admin actions
    sendAdminAction,
    requestRefresh
  };

  // Pass real-time API to children
  return React.Children.map(children, child => {
    if (React.isValidElement(child)) {
      return React.cloneElement(child, { realTimeAPI });
    }
    return child;
  });
};

export default RealTimeDataSync;