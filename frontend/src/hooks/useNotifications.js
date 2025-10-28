import { useState, useEffect, useCallback, useRef } from 'react';
import notificationService from '../services/notificationService';

export const useNotifications = (options = {}) => {
  const {
    autoRefresh = true,
    refreshInterval = 30000, // 30 seconds
    initialFilters = {},
    limit = 50
  } = options;

  const [notifications, setNotifications] = useState([]);
  const [groups, setGroups] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState(initialFilters);
  const [hasMore, setHasMore] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  const refreshIntervalRef = useRef(null);
  const mountedRef = useRef(true);

  // Fetch notifications
  const fetchNotifications = useCallback(async (newFilters = filters, reset = false) => {
    if (!mountedRef.current) return;

    setLoading(true);
    setError(null);

    try {
      const params = {
        ...newFilters,
        limit,
        skip: reset ? 0 : notifications.length
      };

      const data = await notificationService.getNotificationCenter(params);

      if (!mountedRef.current) return;

      if (reset) {
        setNotifications(data.notifications || []);
      } else {
        setNotifications(prev => [...prev, ...(data.notifications || [])]);
      }

      setGroups(data.groups || []);
      setUnreadCount(data.unread_count || 0);
      setTotalCount(data.total_count || 0);
      setHasMore(data.has_more || false);
      setLastUpdated(new Date(data.last_updated));

    } catch (err) {
      if (mountedRef.current) {
        setError(err.message);
        console.error('Error fetching notifications:', err);
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, [filters, limit, notifications.length]);

  // Refresh notifications (reset)
  const refreshNotifications = useCallback(async (newFilters = filters) => {
    await fetchNotifications(newFilters, true);
  }, [fetchNotifications, filters]);

  // Load more notifications
  const loadMore = useCallback(async () => {
    if (!hasMore || loading) return;
    await fetchNotifications(filters, false);
  }, [hasMore, loading, fetchNotifications, filters]);

  // Update filters
  const updateFilters = useCallback(async (newFilters) => {
    setFilters(newFilters);
    await fetchNotifications(newFilters, true);
  }, [fetchNotifications]);

  // Mark notifications as read
  const markAsRead = useCallback(async (notificationIds) => {
    try {
      await notificationService.markAsRead(notificationIds);
      
      // Update local state
      setNotifications(prev => 
        prev.map(notification => 
          notificationIds.includes(notification.id)
            ? { ...notification, is_read: true, read_at: new Date().toISOString() }
            : notification
        )
      );

      // Update unread count
      const unreadNotifications = notifications.filter(n => 
        notificationIds.includes(n.id) && !n.is_read
      );
      setUnreadCount(prev => Math.max(0, prev - unreadNotifications.length));

    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [notifications]);

  // Mark notifications as starred
  const markAsStarred = useCallback(async (notificationIds, starred = true) => {
    try {
      await notificationService.markAsStarred(notificationIds, starred);
      
      // Update local state
      setNotifications(prev => 
        prev.map(notification => 
          notificationIds.includes(notification.id)
            ? { ...notification, is_starred: starred }
            : notification
        )
      );

    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  // Dismiss notifications
  const dismissNotifications = useCallback(async (notificationIds) => {
    try {
      await notificationService.dismissNotifications(notificationIds);
      
      // Remove from local state
      setNotifications(prev => 
        prev.filter(notification => !notificationIds.includes(notification.id))
      );

      // Update counts
      const dismissedNotifications = notifications.filter(n => 
        notificationIds.includes(n.id)
      );
      const unreadDismissed = dismissedNotifications.filter(n => !n.is_read);
      
      setTotalCount(prev => Math.max(0, prev - dismissedNotifications.length));
      setUnreadCount(prev => Math.max(0, prev - unreadDismissed.length));

    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [notifications]);

  // Delete notification
  const deleteNotification = useCallback(async (notificationId) => {
    try {
      await notificationService.deleteNotification(notificationId);
      
      // Remove from local state
      const notification = notifications.find(n => n.id === notificationId);
      if (notification) {
        setNotifications(prev => prev.filter(n => n.id !== notificationId));
        setTotalCount(prev => Math.max(0, prev - 1));
        
        if (!notification.is_read) {
          setUnreadCount(prev => Math.max(0, prev - 1));
        }
      }

    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, [notifications]);

  // Get notification statistics
  const getStats = useCallback(async (period = '30d') => {
    try {
      return await notificationService.getNotificationStats(period);
    } catch (err) {
      setError(err.message);
      throw err;
    }
  }, []);

  // Setup auto-refresh
  useEffect(() => {
    if (autoRefresh && refreshInterval > 0) {
      refreshIntervalRef.current = setInterval(() => {
        refreshNotifications();
      }, refreshInterval);

      return () => {
        if (refreshIntervalRef.current) {
          clearInterval(refreshIntervalRef.current);
        }
      };
    }
  }, [autoRefresh, refreshInterval, refreshNotifications]);

  // Listen to notification service events
  useEffect(() => {
    const handleNotificationUpdate = (event, data) => {
      switch (event) {
        case 'unread_count_updated':
          setUnreadCount(data);
          break;
        case 'notifications_updated':
          // Refresh notifications when they're updated externally
          refreshNotifications();
          break;
        default:
          break;
      }
    };

    const unsubscribe = notificationService.addListener(handleNotificationUpdate);
    return unsubscribe;
  }, [refreshNotifications]);

  // Initial fetch
  useEffect(() => {
    refreshNotifications();
  }, []);

  // Cleanup
  useEffect(() => {
    return () => {
      mountedRef.current = false;
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, []);

  return {
    // Data
    notifications,
    groups,
    unreadCount,
    totalCount,
    hasMore,
    lastUpdated,
    
    // State
    loading,
    error,
    filters,
    
    // Actions
    refreshNotifications,
    loadMore,
    updateFilters,
    markAsRead,
    markAsStarred,
    dismissNotifications,
    deleteNotification,
    getStats,
    
    // Utility
    clearError: () => setError(null)
  };
};

// Hook for unread count only (lightweight)
export const useUnreadCount = (options = {}) => {
  const { autoRefresh = true, refreshInterval = 30000 } = options;
  
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const refreshIntervalRef = useRef(null);
  const mountedRef = useRef(true);

  const fetchUnreadCount = useCallback(async () => {
    if (!mountedRef.current) return;

    setLoading(true);
    setError(null);

    try {
      const count = await notificationService.getUnreadCount();
      if (mountedRef.current) {
        setUnreadCount(count);
      }
    } catch (err) {
      if (mountedRef.current) {
        setError(err.message);
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, []);

  // Setup auto-refresh
  useEffect(() => {
    if (autoRefresh && refreshInterval > 0) {
      refreshIntervalRef.current = setInterval(fetchUnreadCount, refreshInterval);
      return () => {
        if (refreshIntervalRef.current) {
          clearInterval(refreshIntervalRef.current);
        }
      };
    }
  }, [autoRefresh, refreshInterval, fetchUnreadCount]);

  // Listen to notification service events
  useEffect(() => {
    const handleUnreadCountUpdate = (event, data) => {
      if (event === 'unread_count_updated') {
        setUnreadCount(data);
      }
    };

    const unsubscribe = notificationService.addListener(handleUnreadCountUpdate);
    return unsubscribe;
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchUnreadCount();
  }, [fetchUnreadCount]);

  // Cleanup
  useEffect(() => {
    return () => {
      mountedRef.current = false;
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, []);

  return {
    unreadCount,
    loading,
    error,
    refresh: fetchUnreadCount,
    clearError: () => setError(null)
  };
};

export default useNotifications;