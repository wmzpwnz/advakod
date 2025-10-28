import { useEffect, useState, useCallback } from 'react';
import tabSyncService from '../services/tabSyncService';

export const useTabSync = (options = {}) => {
  const [isLeader, setIsLeader] = useState(tabSyncService.isLeader);
  const [tabId, setTabId] = useState(tabSyncService.tabId);
  const [leaderId, setLeaderId] = useState(tabSyncService.leaderId);

  const { onDataSync, onLeaderChange } = options;

  useEffect(() => {
    const handleLeaderChange = (data) => {
      setIsLeader(data.isLeader);
      setLeaderId(data.leaderId);
      if (onLeaderChange) onLeaderChange(data);
    };

    const handleDataSync = (data) => {
      if (onDataSync) onDataSync(data);
    };

    tabSyncService.on('leaderChanged', handleLeaderChange);
    tabSyncService.on('dataSync', handleDataSync);

    return () => {
      tabSyncService.off('leaderChanged', handleLeaderChange);
      tabSyncService.off('dataSync', handleDataSync);
    };
  }, [onDataSync, onLeaderChange]);

  const syncData = useCallback((dataType, data, options) => {
    tabSyncService.syncData(dataType, data, options);
  }, []);

  const getSyncedData = useCallback((dataType) => {
    return tabSyncService.getSyncedData(dataType);
  }, []);

  const requestData = useCallback((dataType) => {
    tabSyncService.requestData(dataType);
  }, []);

  const broadcast = useCallback((message, data) => {
    tabSyncService.broadcast(message, data);
  }, []);

  return {
    isLeader,
    tabId,
    leaderId,
    syncData,
    getSyncedData,
    requestData,
    broadcast
  };
};

// Hook for syncing dashboard data across tabs
export const useDashboardSync = () => {
  const [syncedDashboardData, setSyncedDashboardData] = useState(null);
  const [lastSyncTime, setLastSyncTime] = useState(null);

  const { syncData, getSyncedData } = useTabSync({
    onDataSync: (data) => {
      if (data.dataType === 'dashboard') {
        setSyncedDashboardData(data.data);
        setLastSyncTime(new Date(data.timestamp));
      }
    }
  });

  // Sync dashboard data to other tabs
  const syncDashboard = useCallback((dashboardData) => {
    tabSyncService.syncDashboardData(dashboardData);
    setSyncedDashboardData(dashboardData);
    setLastSyncTime(new Date());
  }, []);

  // Get initial synced data
  useEffect(() => {
    const initialData = getSyncedData('dashboard');
    if (initialData) {
      setSyncedDashboardData(initialData);
    }
  }, [getSyncedData]);

  return {
    syncedDashboardData,
    lastSyncTime,
    syncDashboard
  };
};

// Hook for syncing notifications across tabs
export const useNotificationSync = () => {
  const [syncedNotifications, setSyncedNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  const { syncData, getSyncedData } = useTabSync({
    onDataSync: (data) => {
      if (data.dataType === 'notifications') {
        setSyncedNotifications(data.data.notifications || []);
        setUnreadCount(data.data.unreadCount || 0);
      }
    }
  });

  // Sync notifications to other tabs
  const syncNotifications = useCallback((notifications, unreadCount) => {
    const notificationData = { notifications, unreadCount };
    tabSyncService.syncNotifications(notificationData);
    setSyncedNotifications(notifications);
    setUnreadCount(unreadCount);
  }, []);

  // Mark notification as read across all tabs
  const markAsReadAcrossTabs = useCallback((notificationId) => {
    const updatedNotifications = syncedNotifications.map(n => 
      n.id === notificationId ? { ...n, read: true } : n
    );
    const newUnreadCount = Math.max(0, unreadCount - 1);
    syncNotifications(updatedNotifications, newUnreadCount);
  }, [syncedNotifications, unreadCount, syncNotifications]);

  // Get initial synced data
  useEffect(() => {
    const initialData = getSyncedData('notifications');
    if (initialData) {
      setSyncedNotifications(initialData.notifications || []);
      setUnreadCount(initialData.unreadCount || 0);
    }
  }, [getSyncedData]);

  return {
    syncedNotifications,
    unreadCount,
    syncNotifications,
    markAsReadAcrossTabs
  };
};

// Hook for syncing user activity across tabs
export const useUserActivitySync = () => {
  const [syncedUserActivity, setSyncedUserActivity] = useState([]);
  const [onlineUsers, setOnlineUsers] = useState(0);

  const { syncData, getSyncedData } = useTabSync({
    onDataSync: (data) => {
      if (data.dataType === 'user_activity') {
        setSyncedUserActivity(data.data.activity || []);
        setOnlineUsers(data.data.onlineUsers || 0);
      }
    }
  });

  // Sync user activity to other tabs
  const syncUserActivity = useCallback((activity, onlineUsers) => {
    const activityData = { activity, onlineUsers };
    tabSyncService.syncUserActivity(activityData);
    setSyncedUserActivity(activity);
    setOnlineUsers(onlineUsers);
  }, []);

  // Get initial synced data
  useEffect(() => {
    const initialData = getSyncedData('user_activity');
    if (initialData) {
      setSyncedUserActivity(initialData.activity || []);
      setOnlineUsers(initialData.onlineUsers || 0);
    }
  }, [getSyncedData]);

  return {
    syncedUserActivity,
    onlineUsers,
    syncUserActivity
  };
};

// Hook for syncing system alerts across tabs
export const useSystemAlertsSync = () => {
  const [syncedAlerts, setSyncedAlerts] = useState([]);
  const [criticalCount, setCriticalCount] = useState(0);

  const { syncData, getSyncedData } = useTabSync({
    onDataSync: (data) => {
      if (data.dataType === 'system_alerts') {
        setSyncedAlerts(data.data.alerts || []);
        setCriticalCount(data.data.criticalCount || 0);
      }
    }
  });

  // Sync system alerts to other tabs
  const syncSystemAlerts = useCallback((alerts, criticalCount) => {
    const alertData = { alerts, criticalCount };
    tabSyncService.syncSystemAlerts(alertData);
    setSyncedAlerts(alerts);
    setCriticalCount(criticalCount);
  }, []);

  // Dismiss alert across all tabs
  const dismissAlertAcrossTabs = useCallback((alertId) => {
    const updatedAlerts = syncedAlerts.filter(alert => alert.id !== alertId);
    const alert = syncedAlerts.find(a => a.id === alertId);
    const newCriticalCount = alert && alert.severity === 'critical' 
      ? Math.max(0, criticalCount - 1) 
      : criticalCount;
    
    syncSystemAlerts(updatedAlerts, newCriticalCount);
  }, [syncedAlerts, criticalCount, syncSystemAlerts]);

  // Get initial synced data
  useEffect(() => {
    const initialData = getSyncedData('system_alerts');
    if (initialData) {
      setSyncedAlerts(initialData.alerts || []);
      setCriticalCount(initialData.criticalCount || 0);
    }
  }, [getSyncedData]);

  return {
    syncedAlerts,
    criticalCount,
    syncSystemAlerts,
    dismissAlertAcrossTabs
  };
};

// Hook for syncing moderation queue across tabs
export const useModerationQueueSync = () => {
  const [syncedQueueSize, setSyncedQueueSize] = useState(0);
  const [syncedPendingReviews, setSyncedPendingReviews] = useState([]);
  const [syncedRecentActions, setSyncedRecentActions] = useState([]);

  const { syncData, getSyncedData } = useTabSync({
    onDataSync: (data) => {
      if (data.dataType === 'moderation_queue') {
        setSyncedQueueSize(data.data.queueSize || 0);
        setSyncedPendingReviews(data.data.pendingReviews || []);
        setSyncedRecentActions(data.data.recentActions || []);
      }
    }
  });

  // Sync moderation queue to other tabs
  const syncModerationQueue = useCallback((queueSize, pendingReviews, recentActions) => {
    const queueData = { queueSize, pendingReviews, recentActions };
    tabSyncService.syncModerationQueue(queueData);
    setSyncedQueueSize(queueSize);
    setSyncedPendingReviews(pendingReviews);
    setSyncedRecentActions(recentActions);
  }, []);

  // Get initial synced data
  useEffect(() => {
    const initialData = getSyncedData('moderation_queue');
    if (initialData) {
      setSyncedQueueSize(initialData.queueSize || 0);
      setSyncedPendingReviews(initialData.pendingReviews || []);
      setSyncedRecentActions(initialData.recentActions || []);
    }
  }, [getSyncedData]);

  return {
    syncedQueueSize,
    syncedPendingReviews,
    syncedRecentActions,
    syncModerationQueue
  };
};

// Hook for syncing UI state across tabs
export const useUIStateSync = () => {
  const [syncedActiveModule, setSyncedActiveModule] = useState('dashboard');
  const [syncedSidebarOpen, setSyncedSidebarOpen] = useState(true);

  const { syncData, getSyncedData } = useTabSync({
    onDataSync: (data) => {
      if (data.dataType === 'active_module') {
        setSyncedActiveModule(data.data.moduleId);
      } else if (data.dataType === 'sidebar_state') {
        setSyncedSidebarOpen(data.data.isOpen);
      }
    }
  });

  // Sync active module to other tabs
  const syncActiveModule = useCallback((moduleId) => {
    tabSyncService.syncActiveModule(moduleId);
    setSyncedActiveModule(moduleId);
  }, []);

  // Sync sidebar state to other tabs
  const syncSidebarState = useCallback((isOpen) => {
    tabSyncService.syncSidebarState(isOpen);
    setSyncedSidebarOpen(isOpen);
  }, []);

  // Get initial synced data
  useEffect(() => {
    const activeModuleData = getSyncedData('active_module');
    if (activeModuleData) {
      setSyncedActiveModule(activeModuleData.moduleId);
    }

    const sidebarData = getSyncedData('sidebar_state');
    if (sidebarData) {
      setSyncedSidebarOpen(sidebarData.isOpen);
    }
  }, [getSyncedData]);

  return {
    syncedActiveModule,
    syncedSidebarOpen,
    syncActiveModule,
    syncSidebarState
  };
};

export default useTabSync;