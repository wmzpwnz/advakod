import { getApiUrl } from '../config/api';

class AdminWebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.listeners = new Map();
    this.isConnected = false;
    this.token = null;
    this.userId = null;
    this.heartbeatInterval = null;
    this.lastHeartbeat = null;
  }

  // Initialize WebSocket connection
  connect(token, userId) {
    this.token = token;
    this.userId = userId;
    
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      try {
        // Convert HTTP URL to WebSocket URL
        const wsUrl = getApiUrl('/ws/admin')
          .replace('http://', 'ws://')
          .replace('https://', 'wss://');
        
        this.ws = new WebSocket(`${wsUrl}?token=${token}&user_id=${userId}`);

        this.ws.onopen = () => {
          console.log('Admin WebSocket connected');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          this.emit('connected');
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('Admin WebSocket disconnected:', event.code, event.reason);
          this.isConnected = false;
          this.stopHeartbeat();
          this.emit('disconnected', { code: event.code, reason: event.reason });
          
          // Attempt to reconnect if not a normal closure
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('Admin WebSocket error:', error);
          this.emit('error', error);
          reject(error);
        };

      } catch (error) {
        console.error('Error creating WebSocket connection:', error);
        reject(error);
      }
    });
  }

  // Handle incoming messages
  handleMessage(data) {
    const { type, payload, timestamp, sender_id } = data;
    
    // Update last heartbeat
    if (type === 'heartbeat') {
      this.lastHeartbeat = Date.now();
      return;
    }

    // Handle connection established message
    if (type === 'connection_established') {
      console.log('Admin WebSocket connection established:', payload);
      this.emit('connectionEstablished', payload);
      
      // Auto-subscribe to default channels based on user role
      const availableChannels = payload.available_channels || [];
      availableChannels.forEach(channel => {
        this.send('subscribe', { channel });
      });
      
      return;
    }

    // Handle subscription results
    if (type === 'subscription_result' || type === 'unsubscription_result') {
      console.log('Subscription result:', payload);
      this.emit('subscriptionResult', payload);
      return;
    }

    // Handle errors
    if (type === 'error') {
      console.error('Admin WebSocket error:', payload);
      this.emit('error', payload);
      return;
    }

    // Emit to specific listeners
    this.emit(type, payload, timestamp, sender_id);
    
    // Emit to general message listeners
    this.emit('message', data);

    // Handle specific admin events and sync data between tabs
    switch (type) {
      case 'dashboard_update':
        this.emit('dashboardUpdate', payload);
        this.syncBetweenTabs('dashboard', payload);
        break;
      case 'user_activity':
        this.emit('userActivity', payload);
        this.syncBetweenTabs('user_activity', payload);
        break;
      case 'system_alert':
        this.emit('systemAlert', payload);
        this.syncBetweenTabs('system_alerts', payload);
        break;
      case 'moderation_queue_update':
        this.emit('moderationQueueUpdate', payload);
        this.syncBetweenTabs('moderation_queue', payload);
        break;
      case 'notification':
        this.emit('notification', payload);
        this.syncBetweenTabs('notifications', payload);
        break;
      case 'real_time_metrics':
        this.emit('realTimeMetrics', payload);
        this.syncBetweenTabs('metrics', payload);
        break;
      case 'backup_status':
        this.emit('backupStatus', payload);
        this.syncBetweenTabs('backup_status', payload);
        break;
      case 'task_update':
        this.emit('taskUpdate', payload);
        this.syncBetweenTabs('task_updates', payload);
        break;
      case 'notification_marked_read':
        this.emit('notificationMarkedRead', payload);
        break;
      case 'review_submitted':
        this.emit('reviewSubmitted', payload);
        break;
      default:
        console.log('Unknown admin message type:', type, payload);
    }
  }

  // Send message to server
  send(type, payload) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = {
        type,
        payload,
        timestamp: Date.now(),
        user_id: this.userId
      };
      this.ws.send(JSON.stringify(message));
      return true;
    }
    console.warn('WebSocket not connected, cannot send message');
    return false;
  }

  // Subscribe to admin dashboard updates
  subscribeToDashboard() {
    this.send('subscribe', { channel: 'admin_dashboard' });
  }

  // Subscribe to user activity updates
  subscribeToUserActivity() {
    this.send('subscribe', { channel: 'user_activity' });
  }

  // Subscribe to system alerts
  subscribeToSystemAlerts() {
    this.send('subscribe', { channel: 'system_alerts' });
  }

  // Subscribe to moderation queue updates
  subscribeToModerationQueue() {
    this.send('subscribe', { channel: 'moderation_queue' });
  }

  // Subscribe to notifications
  subscribeToNotifications() {
    this.send('subscribe', { channel: 'notifications' });
  }

  // Subscribe to real-time metrics
  subscribeToMetrics() {
    this.send('subscribe', { channel: 'real_time_metrics' });
  }

  // Subscribe to backup status updates
  subscribeToBackupStatus() {
    this.send('subscribe', { channel: 'backup_status' });
  }

  // Subscribe to task updates
  subscribeToTaskUpdates() {
    this.send('subscribe', { channel: 'task_updates' });
  }

  // Unsubscribe from channel
  unsubscribe(channel) {
    this.send('unsubscribe', { channel });
  }

  // Start heartbeat to keep connection alive
  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.send('heartbeat', { timestamp: Date.now() });
      }
      
      // Check if we haven't received a heartbeat response
      if (this.lastHeartbeat && Date.now() - this.lastHeartbeat > 30000) {
        console.warn('Heartbeat timeout, reconnecting...');
        this.reconnect();
      }
    }, 10000); // Send heartbeat every 10 seconds
  }

  // Stop heartbeat
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  // Schedule reconnection
  scheduleReconnect() {
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
    
    setTimeout(() => {
      if (!this.isConnected) {
        this.connect(this.token, this.userId).catch(error => {
          console.error('Reconnection failed:', error);
        });
      }
    }, delay);
  }

  // Force reconnection
  reconnect() {
    if (this.ws) {
      this.ws.close();
    }
    this.connect(this.token, this.userId);
  }

  // Disconnect WebSocket
  disconnect() {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    this.isConnected = false;
    this.listeners.clear();
  }

  // Event listener management
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).delete(callback);
    }
  }

  emit(event, ...args) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(...args);
        } catch (error) {
          console.error(`Error in WebSocket event listener for ${event}:`, error);
        }
      });
    }
  }

  // Get connection status
  getConnectionStatus() {
    return {
      connected: this.isConnected,
      readyState: this.ws ? this.ws.readyState : WebSocket.CLOSED,
      reconnectAttempts: this.reconnectAttempts,
      lastHeartbeat: this.lastHeartbeat
    };
  }

  // Sync data between tabs using localStorage
  syncBetweenTabs(key, data) {
    const syncData = {
      timestamp: Date.now(),
      data,
      source: 'admin_websocket'
    };
    localStorage.setItem(`admin_sync_${key}`, JSON.stringify(syncData));
    
    // Dispatch custom event for other tabs
    window.dispatchEvent(new CustomEvent('admin_data_sync', {
      detail: { key, data: syncData }
    }));
  }

  // Listen for sync events from other tabs
  setupTabSync() {
    window.addEventListener('admin_data_sync', (event) => {
      const { key, data } = event.detail;
      this.emit('tabSync', { key, data: data.data, timestamp: data.timestamp });
    });

    // Listen for storage changes (for cross-tab sync)
    window.addEventListener('storage', (event) => {
      if (event.key && event.key.startsWith('admin_sync_')) {
        const key = event.key.replace('admin_sync_', '');
        try {
          const data = JSON.parse(event.newValue);
          this.emit('tabSync', { key, data: data.data, timestamp: data.timestamp });
        } catch (error) {
          console.error('Error parsing sync data:', error);
        }
      }
    });
  }

  // Request real-time data refresh
  requestDataRefresh(dataType) {
    this.send('request_refresh', { data_type: dataType });
  }

  // Send admin action for real-time updates
  sendAdminAction(action, data) {
    this.send('admin_action', { action, data });
  }
}

// Create singleton instance
const adminWebSocketService = new AdminWebSocketService();

export default adminWebSocketService;