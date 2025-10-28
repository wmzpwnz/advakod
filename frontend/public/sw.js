// Service Worker for Push Notifications
// АДВАКОД - ИИ-Юрист для РФ

const CACHE_NAME = 'advakod-notifications-v1';
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/favicon.ico'
];

// Install event
self.addEventListener('install', (event) => {
  console.log('Service Worker installing...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
      .catch((error) => {
        console.error('Error caching resources:', error);
      })
  );
  
  // Skip waiting to activate immediately
  self.skipWaiting();
});

// Activate event
self.addEventListener('activate', (event) => {
  console.log('Service Worker activating...');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  
  // Claim all clients immediately
  self.clients.claim();
});

// Fetch event (basic caching strategy)
self.addEventListener('fetch', (event) => {
  // Only handle GET requests
  if (event.request.method !== 'GET') {
    return;
  }
  
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached version or fetch from network
        return response || fetch(event.request);
      })
      .catch((error) => {
        console.error('Fetch error:', error);
        // Return a fallback response if needed
        return new Response('Offline', { status: 503 });
      })
  );
});

// Push event - handle incoming push notifications
self.addEventListener('push', (event) => {
  console.log('Push event received:', event);
  
  let notificationData = {
    title: 'АДВАКОД',
    body: 'У вас новое уведомление',
    icon: '/favicon.ico',
    badge: '/favicon.ico',
    tag: 'advakod-notification',
    requireInteraction: false,
    actions: [],
    data: {}
  };
  
  // Parse push data if available
  if (event.data) {
    try {
      const pushData = event.data.json();
      console.log('Push data received:', pushData);
      
      notificationData = {
        ...notificationData,
        title: pushData.title || notificationData.title,
        body: pushData.content || pushData.body || notificationData.body,
        icon: pushData.icon || notificationData.icon,
        badge: pushData.badge || notificationData.badge,
        tag: pushData.tag || notificationData.tag,
        requireInteraction: pushData.priority === 'critical' || pushData.requireInteraction || false,
        data: {
          ...pushData,
          timestamp: Date.now(),
          url: pushData.action_url || pushData.url || '/'
        }
      };
      
      // Add actions based on notification type
      if (pushData.action_url || pushData.url) {
        notificationData.actions = [
          {
            action: 'open',
            title: pushData.action_text || 'Открыть',
            icon: '/favicon.ico'
          },
          {
            action: 'dismiss',
            title: 'Закрыть',
            icon: '/favicon.ico'
          }
        ];
      } else {
        notificationData.actions = [
          {
            action: 'dismiss',
            title: 'Закрыть',
            icon: '/favicon.ico'
          }
        ];
      }
      
      // Set priority-based styling
      if (pushData.priority === 'critical') {
        notificationData.requireInteraction = true;
        notificationData.tag = 'advakod-critical';
      } else if (pushData.priority === 'high') {
        notificationData.tag = 'advakod-high';
      }
      
    } catch (error) {
      console.error('Error parsing push data:', error);
    }
  }
  
  // Show notification
  event.waitUntil(
    self.registration.showNotification(notificationData.title, notificationData)
      .then(() => {
        console.log('Notification shown successfully');
        
        // Send analytics event (optional)
        try {
          fetch('/api/v1/admin/notifications/analytics/push-shown', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              notification_id: notificationData.data.id,
              timestamp: Date.now()
            })
          }).catch(err => console.warn('Failed to send analytics:', err));
        } catch (error) {
          console.warn('Analytics error:', error);
        }
      })
      .catch((error) => {
        console.error('Error showing notification:', error);
      })
  );
});

// Notification click event
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event);
  
  const notification = event.notification;
  const action = event.action;
  const data = notification.data || {};
  
  // Close the notification
  notification.close();
  
  // Handle different actions
  if (action === 'dismiss') {
    console.log('Notification dismissed');
    return;
  }
  
  // Default action or 'open' action
  let urlToOpen = data.url || '/';
  
  // If it's an admin notification, open admin panel
  if (data.category && ['system', 'moderation', 'project', 'analytics', 'security'].includes(data.category)) {
    urlToOpen = '/admin';
  }
  
  // Open URL
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Check if there's already a window/tab open with the target URL
        for (let i = 0; i < clientList.length; i++) {
          const client = clientList[i];
          if (client.url === urlToOpen && 'focus' in client) {
            return client.focus();
          }
        }
        
        // If no existing window/tab, open a new one
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
      .then(() => {
        // Send analytics event (optional)
        try {
          fetch('/api/v1/admin/notifications/analytics/push-clicked', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              notification_id: data.id,
              action: action || 'open',
              timestamp: Date.now()
            })
          }).catch(err => console.warn('Failed to send click analytics:', err));
        } catch (error) {
          console.warn('Click analytics error:', error);
        }
      })
      .catch((error) => {
        console.error('Error handling notification click:', error);
      })
  );
});

// Notification close event
self.addEventListener('notificationclose', (event) => {
  console.log('Notification closed:', event);
  
  const notification = event.notification;
  const data = notification.data || {};
  
  // Send analytics event (optional)
  try {
    fetch('/api/v1/admin/notifications/analytics/push-closed', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        notification_id: data.id,
        timestamp: Date.now()
      })
    }).catch(err => console.warn('Failed to send close analytics:', err));
  } catch (error) {
    console.warn('Close analytics error:', error);
  }
});

// Background sync event (for offline functionality)
self.addEventListener('sync', (event) => {
  console.log('Background sync event:', event);
  
  if (event.tag === 'notification-sync') {
    event.waitUntil(
      // Sync notifications when back online
      syncNotifications()
    );
  }
});

// Sync notifications function
async function syncNotifications() {
  try {
    console.log('Syncing notifications...');
    
    // Get pending notifications from IndexedDB or localStorage
    // This would be implemented based on your offline storage strategy
    
    // For now, just log that sync would happen
    console.log('Notification sync completed');
  } catch (error) {
    console.error('Error syncing notifications:', error);
  }
}

// Message event (for communication with main thread)
self.addEventListener('message', (event) => {
  console.log('Service Worker received message:', event.data);
  
  const { type, data } = event.data;
  
  switch (type) {
    case 'SKIP_WAITING':
      self.skipWaiting();
      break;
      
    case 'GET_VERSION':
      event.ports[0].postMessage({ version: CACHE_NAME });
      break;
      
    case 'CLEAR_CACHE':
      caches.delete(CACHE_NAME).then(() => {
        event.ports[0].postMessage({ success: true });
      });
      break;
      
    default:
      console.log('Unknown message type:', type);
  }
});

// Error event
self.addEventListener('error', (event) => {
  console.error('Service Worker error:', event.error);
});

// Unhandled rejection event
self.addEventListener('unhandledrejection', (event) => {
  console.error('Service Worker unhandled rejection:', event.reason);
});

console.log('Service Worker loaded successfully');