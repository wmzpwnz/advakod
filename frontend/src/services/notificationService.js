class NotificationService {
  constructor() {
    this.baseUrl = '/api/v1/admin/notifications';
    this.listeners = new Set();
    this.unreadCount = 0;
  }

  // Get auth headers
  getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
  }

  // Add listener for notification updates
  addListener(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  // Notify all listeners
  notifyListeners(event, data) {
    this.listeners.forEach(callback => {
      try {
        callback(event, data);
      } catch (error) {
        console.error('Error in notification listener:', error);
      }
    });
  }

  // Get notification center data
  async getNotificationCenter(params = {}) {
    try {
      const searchParams = new URLSearchParams();
      
      Object.entries(params).forEach(([key, value]) => {
        if (Array.isArray(value)) {
          value.forEach(v => searchParams.append(key, v));
        } else if (value !== null && value !== undefined) {
          searchParams.append(key, value);
        }
      });

      const response = await fetch(`${this.baseUrl}/center?${searchParams}`, {
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      this.unreadCount = data.unread_count || 0;
      this.notifyListeners('unread_count_updated', this.unreadCount);
      
      return data;
    } catch (error) {
      console.error('Error fetching notification center:', error);
      throw error;
    }
  }

  // Get notifications list
  async getNotifications(params = {}) {
    try {
      const searchParams = new URLSearchParams();
      
      Object.entries(params).forEach(([key, value]) => {
        if (Array.isArray(value)) {
          value.forEach(v => searchParams.append(key, v));
        } else if (value !== null && value !== undefined) {
          searchParams.append(key, value);
        }
      });

      const response = await fetch(`${this.baseUrl}/?${searchParams}`, {
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching notifications:', error);
      throw error;
    }
  }

  // Get single notification
  async getNotification(notificationId) {
    try {
      const response = await fetch(`${this.baseUrl}/${notificationId}`, {
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching notification:', error);
      throw error;
    }
  }

  // Mark notifications as read
  async markAsRead(notificationIds) {
    try {
      const response = await fetch(`${this.baseUrl}/mark-read`, {
        method: 'PATCH',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ notification_ids: notificationIds })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      // Update unread count
      this.unreadCount = Math.max(0, this.unreadCount - result.updated_count);
      this.notifyListeners('unread_count_updated', this.unreadCount);
      this.notifyListeners('notifications_updated', { type: 'mark_read', ids: notificationIds });
      
      return result;
    } catch (error) {
      console.error('Error marking notifications as read:', error);
      throw error;
    }
  }

  // Mark notifications as starred
  async markAsStarred(notificationIds, starred = true) {
    try {
      const response = await fetch(`${this.baseUrl}/mark-starred`, {
        method: 'PATCH',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ notification_ids: notificationIds, starred })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      this.notifyListeners('notifications_updated', { 
        type: starred ? 'mark_starred' : 'mark_unstarred', 
        ids: notificationIds 
      });
      
      return result;
    } catch (error) {
      console.error('Error marking notifications as starred:', error);
      throw error;
    }
  }

  // Dismiss notifications
  async dismissNotifications(notificationIds) {
    try {
      const response = await fetch(`${this.baseUrl}/dismiss`, {
        method: 'PATCH',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ notification_ids: notificationIds })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      this.notifyListeners('notifications_updated', { type: 'dismiss', ids: notificationIds });
      
      return result;
    } catch (error) {
      console.error('Error dismissing notifications:', error);
      throw error;
    }
  }

  // Delete notification
  async deleteNotification(notificationId) {
    try {
      const response = await fetch(`${this.baseUrl}/${notificationId}`, {
        method: 'DELETE',
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      this.notifyListeners('notifications_updated', { type: 'delete', ids: [notificationId] });
      
      return result;
    } catch (error) {
      console.error('Error deleting notification:', error);
      throw error;
    }
  }

  // Get unread count
  async getUnreadCount() {
    try {
      const response = await fetch(`${this.baseUrl}/unread/count`, {
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      this.unreadCount = data.unread_count || 0;
      this.notifyListeners('unread_count_updated', this.unreadCount);
      
      return this.unreadCount;
    } catch (error) {
      console.error('Error fetching unread count:', error);
      return 0;
    }
  }

  // Get notification statistics
  async getNotificationStats(period = '30d') {
    try {
      const response = await fetch(`${this.baseUrl}/stats/summary?period=${period}`, {
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching notification stats:', error);
      throw error;
    }
  }

  // Push subscription management
  async createPushSubscription(subscriptionData) {
    try {
      const response = await fetch(`${this.baseUrl}/push/subscribe`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(subscriptionData)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating push subscription:', error);
      throw error;
    }
  }

  async getPushSubscriptions() {
    try {
      const response = await fetch(`${this.baseUrl}/push/subscriptions`, {
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching push subscriptions:', error);
      throw error;
    }
  }

  // Notification preferences
  async getNotificationPreferences() {
    try {
      const response = await fetch(`${this.baseUrl}/preferences`, {
        headers: this.getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching notification preferences:', error);
      throw error;
    }
  }

  async updateNotificationPreferences(preferences) {
    try {
      const response = await fetch(`${this.baseUrl}/preferences`, {
        method: 'PUT',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(preferences)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error updating notification preferences:', error);
      throw error;
    }
  }

  // Admin functions
  async sendNotification(notificationData) {
    try {
      const response = await fetch(`${this.baseUrl}/send`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(notificationData)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error sending notification:', error);
      throw error;
    }
  }

  async sendBulkNotifications(notifications) {
    try {
      const response = await fetch(`${this.baseUrl}/send/bulk`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ notifications })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error sending bulk notifications:', error);
      throw error;
    }
  }

  async testNotification(testData) {
    try {
      const response = await fetch(`${this.baseUrl}/test`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(testData)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error sending test notification:', error);
      throw error;
    }
  }

  // Utility methods
  getCurrentUnreadCount() {
    return this.unreadCount;
  }

  // Format notification for display
  formatNotification(notification) {
    return {
      ...notification,
      timeAgo: this.formatTimeAgo(notification.created_at),
      priorityColor: this.getPriorityColor(notification.priority),
      categoryColor: this.getCategoryColor(notification.category),
      typeIcon: this.getTypeIcon(notification.type)
    };
  }

  formatTimeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) return 'только что';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} мин назад`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} ч назад`;
    if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)} дн назад`;
    
    return date.toLocaleDateString('ru-RU');
  }

  getPriorityColor(priority) {
    switch (priority) {
      case 'critical':
        return 'border-l-red-500 bg-red-50 dark:bg-red-900/20';
      case 'high':
        return 'border-l-orange-500 bg-orange-50 dark:bg-orange-900/20';
      case 'medium':
        return 'border-l-yellow-500 bg-yellow-50 dark:bg-yellow-900/20';
      default:
        return 'border-l-blue-500 bg-blue-50 dark:bg-blue-900/20';
    }
  }

  getCategoryColor(category) {
    switch (category) {
      case 'system':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200';
      case 'marketing':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-800 dark:text-orange-200';
      case 'moderation':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-800 dark:text-purple-200';
      case 'project':
        return 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-200';
      case 'analytics':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-200';
      case 'security':
        return 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200';
    }
  }

  getTypeIcon(type) {
    switch (type) {
      case 'success':
        return 'CheckCircleIcon';
      case 'warning':
        return 'ExclamationTriangleIcon';
      case 'error':
        return 'XCircleIcon';
      default:
        return 'InformationCircleIcon';
    }
  }
}

// Create and export singleton instance
const notificationService = new NotificationService();
export default notificationService;