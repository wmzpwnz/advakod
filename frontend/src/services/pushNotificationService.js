class PushNotificationService {
  constructor() {
    this.registration = null;
    this.subscription = null;
    this.isSupported = 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
    this.permission = 'Notification' in window ? Notification.permission : 'denied';
    this.listeners = new Set();
    
    // VAPID public key - should be generated on backend
    this.vapidPublicKey = 'BEl62iUYgUivxIkv69yViEuiBIa40HI80NM9f4LiKiOiWjjBmMpHMFGNdckY9h4MoCWzWKPiPfHbHZ9VLyxzYXM';
  }

  // Add event listener
  addListener(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  // Notify listeners
  notifyListeners(event, data) {
    this.listeners.forEach(callback => {
      try {
        callback(event, data);
      } catch (error) {
        console.error('Error in push notification listener:', error);
      }
    });
  }

  // Check if push notifications are supported
  isSupported() {
    return this.isSupported;
  }

  // Get current permission status
  getPermission() {
    return 'Notification' in window ? Notification.permission : 'denied';
  }

  // Request permission for notifications
  async requestPermission() {
    if (!this.isSupported) {
      throw new Error('Push notifications are not supported in this browser');
    }

    try {
      if ('Notification' in window) {
        const permission = await Notification.requestPermission();
        this.permission = permission;
        
        this.notifyListeners('permission_changed', permission);
        
        if (permission === 'granted') {
          console.log('Push notification permission granted');
          return true;
        } else if (permission === 'denied') {
          console.log('Push notification permission denied');
          return false;
        } else {
          console.log('Push notification permission dismissed');
          return false;
        }
      } else {
        console.log('Notification API not available');
        return false;
      }
    } catch (error) {
      console.error('Error requesting notification permission:', error);
      throw error;
    }
  }

  // Register service worker
  async registerServiceWorker() {
    if (!this.isSupported) {
      throw new Error('Service workers are not supported in this browser');
    }

    try {
      // Register service worker
      this.registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/'
      });

      console.log('Service worker registered successfully');

      // Wait for service worker to be ready
      await navigator.serviceWorker.ready;

      this.notifyListeners('service_worker_registered', this.registration);
      return this.registration;
    } catch (error) {
      console.error('Error registering service worker:', error);
      throw error;
    }
  }

  // Subscribe to push notifications
  async subscribe() {
    if (!this.isSupported) {
      throw new Error('Push notifications are not supported');
    }

    if (this.permission !== 'granted') {
      const granted = await this.requestPermission();
      if (!granted) {
        throw new Error('Push notification permission not granted');
      }
    }

    try {
      // Register service worker if not already registered
      if (!this.registration) {
        await this.registerServiceWorker();
      }

      // Convert VAPID key to Uint8Array
      const applicationServerKey = this.urlBase64ToUint8Array(this.vapidPublicKey);

      // Subscribe to push notifications
      this.subscription = await this.registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: applicationServerKey
      });

      console.log('Push subscription created:', this.subscription);

      // Send subscription to backend
      await this.sendSubscriptionToBackend(this.subscription);

      this.notifyListeners('subscribed', this.subscription);
      return this.subscription;
    } catch (error) {
      console.error('Error subscribing to push notifications:', error);
      throw error;
    }
  }

  // Unsubscribe from push notifications
  async unsubscribe() {
    if (!this.subscription) {
      console.log('No active push subscription to unsubscribe from');
      return true;
    }

    try {
      // Unsubscribe from push manager
      const success = await this.subscription.unsubscribe();
      
      if (success) {
        // Remove subscription from backend
        await this.removeSubscriptionFromBackend(this.subscription);
        
        this.subscription = null;
        console.log('Successfully unsubscribed from push notifications');
        
        this.notifyListeners('unsubscribed', null);
        return true;
      } else {
        throw new Error('Failed to unsubscribe from push notifications');
      }
    } catch (error) {
      console.error('Error unsubscribing from push notifications:', error);
      throw error;
    }
  }

  // Get current subscription
  async getSubscription() {
    if (!this.registration) {
      return null;
    }

    try {
      this.subscription = await this.registration.pushManager.getSubscription();
      return this.subscription;
    } catch (error) {
      console.error('Error getting push subscription:', error);
      return null;
    }
  }

  // Check if currently subscribed
  async isSubscribed() {
    const subscription = await this.getSubscription();
    return subscription !== null;
  }

  // Send subscription to backend
  async sendSubscriptionToBackend(subscription) {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      const subscriptionData = {
        endpoint: subscription.endpoint,
        keys: {
          p256dh: this.arrayBufferToBase64(subscription.getKey('p256dh')),
          auth: this.arrayBufferToBase64(subscription.getKey('auth'))
        },
        user_agent: navigator.userAgent,
        ip_address: null // Will be determined by backend
      };

      const response = await fetch('/api/v1/admin/notifications/push/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(subscriptionData)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log('Subscription sent to backend successfully:', result);
      return result;
    } catch (error) {
      console.error('Error sending subscription to backend:', error);
      throw error;
    }
  }

  // Remove subscription from backend
  async removeSubscriptionFromBackend(subscription) {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        console.warn('No authentication token found for removing subscription');
        return;
      }

      // For now, we don't have a specific endpoint to remove subscriptions
      // The backend will handle inactive subscriptions automatically
      console.log('Subscription removal from backend not implemented yet');
    } catch (error) {
      console.error('Error removing subscription from backend:', error);
    }
  }

  // Show local notification (for testing)
  async showNotification(title, options = {}) {
    if (this.permission !== 'granted') {
      throw new Error('Notification permission not granted');
    }

    try {
      const defaultOptions = {
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        tag: 'advakod-notification',
        requireInteraction: false,
        ...options
      };

      if (this.registration) {
        // Show notification via service worker
        await this.registration.showNotification(title, defaultOptions);
      } else {
        // Show notification directly
        new Notification(title, defaultOptions);
      }

      this.notifyListeners('notification_shown', { title, options: defaultOptions });
    } catch (error) {
      console.error('Error showing notification:', error);
      throw error;
    }
  }

  // Test push notification
  async testNotification() {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      const testData = {
        channel_type: 'push',
        recipient: 'current_user',
        title: 'Тестовое уведомление',
        content: 'Это тестовое push-уведомление от системы АДВАКОД',
        priority: 'medium'
      };

      const response = await fetch('/api/v1/admin/notifications/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(testData)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log('Test notification sent:', result);
      return result;
    } catch (error) {
      console.error('Error sending test notification:', error);
      throw error;
    }
  }

  // Utility functions
  urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
  }

  // Get notification settings
  getSettings() {
    return {
      isSupported: this.isSupported,
      permission: this.permission,
      isSubscribed: this.subscription !== null,
      subscription: this.subscription
    };
  }

  // Initialize push notifications
  async initialize() {
    if (!this.isSupported) {
      console.warn('Push notifications are not supported in this browser');
      return false;
    }

    try {
      // Check if already subscribed
      await this.getSubscription();
      
      if (this.subscription) {
        console.log('Already subscribed to push notifications');
        this.notifyListeners('initialized', { subscribed: true });
        return true;
      } else {
        console.log('Not subscribed to push notifications');
        this.notifyListeners('initialized', { subscribed: false });
        return false;
      }
    } catch (error) {
      console.error('Error initializing push notifications:', error);
      this.notifyListeners('error', error);
      return false;
    }
  }
}

// Create and export singleton instance
const pushNotificationService = new PushNotificationService();
export default pushNotificationService;