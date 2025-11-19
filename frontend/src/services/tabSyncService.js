class TabSyncService {
  constructor() {
    this.listeners = new Map();
    this.isLeader = false;
    this.leaderId = null;
    this.tabId = this.generateTabId();
    this.heartbeatInterval = null;
    this.leaderCheckInterval = null;
    
    this.setupLeaderElection();
    this.setupStorageListener();
    this.setupBeforeUnload();
  }

  // Generate unique tab ID
  generateTabId() {
    return `tab_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // Setup leader election mechanism
  setupLeaderElection() {
    // Check if there's already a leader
    const currentLeader = localStorage.getItem('admin_tab_leader');
    const leaderHeartbeat = localStorage.getItem('admin_leader_heartbeat');
    
    if (!currentLeader || !leaderHeartbeat || Date.now() - parseInt(leaderHeartbeat) > 5000) {
      this.becomeLeader();
    } else {
      this.leaderId = currentLeader;
    }

    // Start checking for leader status
    this.leaderCheckInterval = setInterval(() => {
      this.checkLeaderStatus();
    }, 2000);
  }

  // Become the leader tab
  becomeLeader() {
    this.isLeader = true;
    this.leaderId = this.tabId;
    localStorage.setItem('admin_tab_leader', this.tabId);
    this.startHeartbeat();
    
    this.emit('leaderChanged', { isLeader: true, leaderId: this.tabId });
    console.log(`Tab ${this.tabId} became leader`);
  }

  // Start leader heartbeat
  startHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }
    
    this.heartbeatInterval = setInterval(() => {
      if (this.isLeader) {
        localStorage.setItem('admin_leader_heartbeat', Date.now().toString());
      }
    }, 1000);
  }

  // Check leader status
  checkLeaderStatus() {
    const currentLeader = localStorage.getItem('admin_tab_leader');
    const leaderHeartbeat = localStorage.getItem('admin_leader_heartbeat');
    
    // If no leader or leader is dead, try to become leader
    if (!currentLeader || !leaderHeartbeat || Date.now() - parseInt(leaderHeartbeat) > 5000) {
      if (!this.isLeader) {
        this.becomeLeader();
      }
    } else if (currentLeader !== this.tabId && this.isLeader) {
      // Another tab became leader
      this.isLeader = false;
      this.leaderId = currentLeader;
      if (this.heartbeatInterval) {
        clearInterval(this.heartbeatInterval);
        this.heartbeatInterval = null;
      }
      this.emit('leaderChanged', { isLeader: false, leaderId: currentLeader });
      console.log(`Tab ${this.tabId} is no longer leader`);
    }
  }

  // Setup storage event listener for cross-tab communication
  setupStorageListener() {
    window.addEventListener('storage', (event) => {
      if (event.key && event.key.startsWith('admin_sync_')) {
        const dataType = event.key.replace('admin_sync_', '');
        try {
          const data = JSON.parse(event.newValue);
          if (data.sourceTab !== this.tabId) {
            this.emit('dataSync', { dataType, data: data.payload, timestamp: data.timestamp });
          }
        } catch (error) {
          console.error('Error parsing sync data:', error);
        }
      } else if (event.key === 'admin_tab_leader') {
        const newLeader = event.newValue;
        if (newLeader !== this.tabId && this.isLeader) {
          this.isLeader = false;
          this.leaderId = newLeader;
          if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
          }
          this.emit('leaderChanged', { isLeader: false, leaderId: newLeader });
        }
      }
    });
  }

  // Setup beforeunload to cleanup
  setupBeforeUnload() {
    window.addEventListener('beforeunload', () => {
      this.cleanup();
    });
  }

  // Sync data across tabs
  syncData(dataType, data, options = {}) {
    const syncData = {
      payload: data,
      timestamp: Date.now(),
      sourceTab: this.tabId,
      ttl: options.ttl || 60000, // 1 minute default TTL
      ...options
    };

    localStorage.setItem(`admin_sync_${dataType}`, JSON.stringify(syncData));
    
    // Emit to current tab listeners
    this.emit('dataSync', { dataType, data, timestamp: syncData.timestamp });
  }

  // Get synced data
  getSyncedData(dataType) {
    try {
      const stored = localStorage.getItem(`admin_sync_${dataType}`);
      if (stored) {
        const data = JSON.parse(stored);
        
        // Check TTL
        if (data.ttl && Date.now() - data.timestamp > data.ttl) {
          localStorage.removeItem(`admin_sync_${dataType}`);
          return null;
        }
        
        return data.payload;
      }
    } catch (error) {
      console.error('Error getting synced data:', error);
    }
    return null;
  }

  // Clear old synced data
  clearOldSyncData() {
    const keys = Object.keys(localStorage);
    const now = Date.now();
    
    keys.forEach(key => {
      if (key.startsWith('admin_sync_')) {
        try {
          const data = JSON.parse(localStorage.getItem(key));
          if (data.ttl && now - data.timestamp > data.ttl) {
            localStorage.removeItem(key);
          }
        } catch (error) {
          // Invalid data, remove it
          localStorage.removeItem(key);
        }
      }
    });
  }

  // Sync dashboard data
  syncDashboardData(data) {
    this.syncData('dashboard', data, { ttl: 30000 }); // 30 seconds TTL
  }

  // Sync user activity
  syncUserActivity(activity) {
    this.syncData('user_activity', activity, { ttl: 60000 }); // 1 minute TTL
  }

  // Sync notifications
  syncNotifications(notifications) {
    this.syncData('notifications', notifications, { ttl: 300000 }); // 5 minutes TTL
  }

  // Sync system alerts
  syncSystemAlerts(alerts) {
    this.syncData('system_alerts', alerts, { ttl: 120000 }); // 2 minutes TTL
  }

  // Sync moderation queue
  syncModerationQueue(queueData) {
    this.syncData('moderation_queue', queueData, { ttl: 60000 }); // 1 minute TTL
  }

  // Sync active module across tabs
  syncActiveModule(moduleId) {
    this.syncData('active_module', { moduleId }, { ttl: 10000 }); // 10 seconds TTL
  }

  // Sync sidebar state
  syncSidebarState(isOpen) {
    this.syncData('sidebar_state', { isOpen }, { ttl: 300000 }); // 5 minutes TTL
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

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in tab sync event listener for ${event}:`, error);
        }
      });
    }
  }

  // Request data from leader tab
  requestData(dataType) {
    if (this.isLeader) {
      // We are the leader, emit request to ourselves
      this.emit('dataRequest', { dataType, requesterId: this.tabId });
    } else {
      // Send request to leader
      const request = {
        type: 'data_request',
        dataType,
        requesterId: this.tabId,
        timestamp: Date.now()
      };
      localStorage.setItem('admin_tab_request', JSON.stringify(request));
    }
  }

  // Broadcast message to all tabs
  broadcast(message, data) {
    const broadcastData = {
      message,
      data,
      sourceTab: this.tabId,
      timestamp: Date.now()
    };
    localStorage.setItem('admin_broadcast', JSON.stringify(broadcastData));
  }

  // Get tab info
  getTabInfo() {
    return {
      tabId: this.tabId,
      isLeader: this.isLeader,
      leaderId: this.leaderId
    };
  }

  // Cleanup on tab close
  cleanup() {
    if (this.isLeader) {
      localStorage.removeItem('admin_tab_leader');
      localStorage.removeItem('admin_leader_heartbeat');
    }
    
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }
    
    if (this.leaderCheckInterval) {
      clearInterval(this.leaderCheckInterval);
    }
    
    // Clear old sync data
    this.clearOldSyncData();
  }

  // Force become leader (for debugging)
  forceLeader() {
    this.becomeLeader();
  }
}

// Create singleton instance
const tabSyncService = new TabSyncService();

// Cleanup old data periodically
setInterval(() => {
  tabSyncService.clearOldSyncData();
}, 60000); // Every minute

export default tabSyncService;