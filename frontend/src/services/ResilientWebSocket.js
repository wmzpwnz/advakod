/**
 * ResilientWebSocket - Устойчивый WebSocket клиент с автоматическим переподключением
 * Реализует требования 2.2, 2.3, 6.3 из спецификации
 */
class ResilientWebSocket {
  constructor(url, options = {}) {
    this.url = url;
    this.options = {
      maxReconnectAttempts: 10,
      reconnectDelay: 1000,
      maxReconnectDelay: 30000,
      pingInterval: 30000,
      pongTimeout: 10000,
      connectionTimeout: 10000,
      maxMessageSize: 65536, // 64KB
      enableHeartbeat: true,
      enableAutoReconnect: true,
      enableErrorRecovery: true,
      ...options
    };

    this.ws = null;
    this.reconnectAttempts = 0;
    this.isConnected = false;
    this.isConnecting = false;
    this.shouldReconnect = true;

    // Event listeners
    this.listeners = new Map();

    // Ping/Pong для поддержания соединения
    this.pingInterval = null;
    this.pongTimeout = null;
    this.lastPong = null;

    // Очередь сообщений для отправки при переподключении
    this.messageQueue = [];
    this.maxQueueSize = 100;

    // Статистика соединения
    this.connectionStats = {
      totalConnections: 0,
      totalReconnections: 0,
      totalMessages: 0,
      totalErrors: 0,
      lastConnectedAt: null,
      lastDisconnectedAt: null,
      connectionDuration: 0,
      averageLatency: 0,
      errorRate: 0
    };

    // Состояние соединения для UI
    this.connectionState = 'disconnected'; // 'connecting', 'connected', 'reconnecting', 'disconnected', 'failed'
    
    // Система восстановления после ошибок
    this.errorRecovery = {
      consecutiveErrors: 0,
      lastErrorTime: null,
      errorTypes: new Map(),
      recoveryStrategies: new Map()
    };
    
    // Инициализируем стратегии восстановления
    this.initializeRecoveryStrategies();
  }

  /**
   * Инициализация стратегий восстановления после ошибок
   */
  initializeRecoveryStrategies() {
    // Стратегия для ошибок аутентификации
    this.errorRecovery.recoveryStrategies.set('auth_error', {
      maxAttempts: 3,
      delay: 5000,
      action: async () => {
        console.log('ResilientWebSocket: Attempting auth recovery...');
        // Можно добавить логику обновления токена
        this.emit('authRecoveryNeeded');
      }
    });
    
    // Стратегия для сетевых ошибок
    this.errorRecovery.recoveryStrategies.set('network_error', {
      maxAttempts: 5,
      delay: 2000,
      action: async () => {
        console.log('ResilientWebSocket: Attempting network recovery...');
        // Проверяем сетевое соединение
        if (navigator.onLine) {
          return true; // Сеть доступна, можно переподключаться
        }
        return false; // Сеть недоступна, ждем
      }
    });
    
    // Стратегия для ошибок сервера
    this.errorRecovery.recoveryStrategies.set('server_error', {
      maxAttempts: 3,
      delay: 10000,
      action: async () => {
        console.log('ResilientWebSocket: Attempting server error recovery...');
        // Увеличиваем задержку для серверных ошибок
        return true;
      }
    });
  }

  /**
   * Подключение к WebSocket
   */
  async connect() {
    if (this.isConnecting || this.isConnected) {
      return Promise.resolve();
    }

    this.isConnecting = true;
    this.shouldReconnect = true;

    return new Promise((resolve, reject) => {
      try {
        console.log('ResilientWebSocket: Connecting to', this.url);
        this.ws = new WebSocket(this.url);

        this.connectionState = 'connecting';
        this.emit('stateChange', this.connectionState);

        const connectTimeout = setTimeout(() => {
          if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
            this.ws.close();
            this.connectionState = 'failed';
            this.emit('stateChange', this.connectionState);
            reject(new Error('Connection timeout'));
          }
        }, this.options.connectionTimeout);

        this.ws.onopen = () => {
          clearTimeout(connectTimeout);
          console.log('ResilientWebSocket: Connected successfully');
          this.isConnected = true;
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.connectionState = 'connected';

          // Обновляем статистику
          this.connectionStats.totalConnections++;
          this.connectionStats.lastConnectedAt = new Date();

          this.startPingPong();
          this.flushMessageQueue();
          this.emit('open');
          this.emit('stateChange', this.connectionState);
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            // Обработка pong сообщений
            if (data.type === 'pong') {
              this.handlePong(data);
              return;
            }

            this.emit('message', data);
          } catch (error) {
            console.error('ResilientWebSocket: Error parsing message:', error);
            this.emit('error', error);
          }
        };

        this.ws.onclose = (event) => {
          clearTimeout(connectTimeout);
          console.log('ResilientWebSocket: Connection closed:', event.code, event.reason);

          this.isConnected = false;
          this.isConnecting = false;
          this.stopPingPong();

          // Обновляем статистику
          this.connectionStats.lastDisconnectedAt = new Date();
          if (this.connectionStats.lastConnectedAt) {
            this.connectionStats.connectionDuration +=
              this.connectionStats.lastDisconnectedAt - this.connectionStats.lastConnectedAt;
          }

          const shouldReconnect = this.handleClose(event.code, event.reason);

          if (shouldReconnect && this.shouldReconnect) {
            this.connectionState = 'reconnecting';
            this.connectionStats.totalReconnections++;
            this.emit('stateChange', this.connectionState);
            this.scheduleReconnect();
          } else {
            this.connectionState = event.code === 1000 ? 'disconnected' : 'failed';
            this.emit('stateChange', this.connectionState);
          }

          this.emit('close', { code: event.code, reason: event.reason, shouldReconnect });
        };

        this.ws.onerror = (error) => {
          clearTimeout(connectTimeout);
          console.error('ResilientWebSocket: Connection error:', error);
          
          // Обновляем статистику ошибок
          this.connectionStats.totalErrors++;
          this.errorRecovery.consecutiveErrors++;
          this.errorRecovery.lastErrorTime = Date.now();
          
          // Определяем тип ошибки и применяем стратегию восстановления
          const errorType = this.classifyError(error);
          this.handleErrorRecovery(errorType);
          
          this.isConnecting = false;
          this.connectionState = 'failed';
          this.emit('stateChange', this.connectionState);
          this.emit('error', { ...error, type: errorType, recoverable: this.isErrorRecoverable(errorType) });
          reject(error);
        };

      } catch (error) {
        this.isConnecting = false;
        console.error('ResilientWebSocket: Failed to create connection:', error);
        reject(error);
      }
    });
  }

  /**
   * Отключение от WebSocket
   */
  disconnect() {
    console.log('ResilientWebSocket: Disconnecting...');
    this.shouldReconnect = false;
    this.stopPingPong();

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }

    this.isConnected = false;
    this.isConnecting = false;
    this.messageQueue = [];
  }

  /**
   * Отправка сообщения с улучшенной обработкой ошибок
   */
  send(data) {
    const message = typeof data === 'string' ? data : JSON.stringify(data);

    // Проверяем размер сообщения
    if (message.length > this.options.maxMessageSize) {
      console.error('ResilientWebSocket: Message too large:', message.length, 'bytes');
      this.emit('error', {
        type: 'message_too_large',
        message: 'Message exceeds maximum size',
        size: message.length,
        maxSize: this.options.maxMessageSize
      });
      return false;
    }

    if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(message);
        this.connectionStats.totalMessages++;
        this.emit('messageSent', { size: message.length });
        return true;
      } catch (error) {
        console.error('ResilientWebSocket: Error sending message:', error);
        this.connectionStats.totalErrors++;
        
        // Классифицируем ошибку отправки
        const errorType = this.classifyError(error);
        this.handleErrorRecovery(errorType);
        
        // Добавляем в очередь для повторной отправки
        this.queueMessage(message);
        
        this.emit('error', {
          type: 'send_error',
          originalError: error,
          message: 'Failed to send message',
          queued: true
        });
        
        return false;
      }
    } else {
      // Соединение не активно - добавляем в очередь
      this.queueMessage(message);
      
      // Пытаемся переподключиться если нужно
      if (!this.isConnecting && this.shouldReconnect && this.options.enableAutoReconnect) {
        console.log('ResilientWebSocket: Connection lost, attempting to reconnect for message delivery');
        this.connect().catch(error => {
          console.error('ResilientWebSocket: Failed to reconnect for message delivery:', error);
        });
      }
      
      return false;
    }
  }

  /**
   * Добавление сообщения в очередь
   */
  queueMessage(message) {
    if (this.messageQueue.length >= this.maxQueueSize) {
      this.messageQueue.shift(); // Удаляем старое сообщение
    }
    this.messageQueue.push(message);
  }

  /**
   * Отправка всех сообщений из очереди
   */
  flushMessageQueue() {
    while (this.messageQueue.length > 0 && this.isConnected) {
      const message = this.messageQueue.shift();
      try {
        this.ws.send(message);
      } catch (error) {
        console.error('ResilientWebSocket: Error flushing message queue:', error);
        // Возвращаем сообщение в очередь
        this.messageQueue.unshift(message);
        break;
      }
    }
  }

  /**
   * Классификация ошибок для выбора стратегии восстановления
   */
  classifyError(error) {
    if (error.code === 1008 || error.code === 1003) {
      return 'auth_error';
    } else if (error.code === 1011 || error.code === 1001) {
      return 'server_error';
    } else if (error.code === 1006 || !navigator.onLine) {
      return 'network_error';
    } else {
      return 'unknown_error';
    }
  }

  /**
   * Проверка, можно ли восстановиться после ошибки
   */
  isErrorRecoverable(errorType) {
    const nonRecoverableErrors = ['auth_error'];
    return !nonRecoverableErrors.includes(errorType) && this.options.enableErrorRecovery;
  }

  /**
   * Обработка восстановления после ошибки
   */
  async handleErrorRecovery(errorType) {
    if (!this.options.enableErrorRecovery) {
      return false;
    }

    const strategy = this.errorRecovery.recoveryStrategies.get(errorType);
    if (!strategy) {
      console.warn(`ResilientWebSocket: No recovery strategy for error type: ${errorType}`);
      return false;
    }

    // Проверяем количество попыток
    const errorCount = this.errorRecovery.errorTypes.get(errorType) || 0;
    if (errorCount >= strategy.maxAttempts) {
      console.warn(`ResilientWebSocket: Max recovery attempts reached for ${errorType}`);
      this.emit('maxRecoveryAttemptsReached', { errorType, attempts: errorCount });
      return false;
    }

    // Увеличиваем счетчик попыток
    this.errorRecovery.errorTypes.set(errorType, errorCount + 1);

    try {
      // Выполняем стратегию восстановления
      const canRecover = await strategy.action();
      
      if (canRecover !== false) {
        console.log(`ResilientWebSocket: Recovery strategy for ${errorType} completed`);
        this.emit('errorRecoveryAttempt', { errorType, attempt: errorCount + 1 });
        return true;
      }
    } catch (recoveryError) {
      console.error(`ResilientWebSocket: Recovery strategy failed for ${errorType}:`, recoveryError);
    }

    return false;
  }

  /**
   * Обработка закрытия соединения
   */
  handleClose(code, reason) {
    const errorMap = {
      1008: 'Authentication failed',
      1003: 'Access denied', 
      1011: 'Server error',
      1006: 'Connection lost',
      1000: 'Normal closure',
      1001: 'Going away',
      1009: 'Message too big'
    };

    const message = errorMap[code] || 'Unknown error';
    console.log(`ResilientWebSocket closed: ${code} - ${message} (${reason})`);

    // Классифицируем ошибку
    const errorType = this.classifyError({ code, reason });
    
    // Обновляем статистику
    if (code !== 1000) { // Не считаем нормальное закрытие ошибкой
      this.connectionStats.totalErrors++;
      this.errorRecovery.consecutiveErrors++;
    } else {
      this.errorRecovery.consecutiveErrors = 0; // Сбрасываем при нормальном закрытии
    }

    // Определяем, можно ли переподключаться
    const permanentErrors = [1008, 1003]; // Ошибки аутентификации и доступа
    const shouldReconnect = !permanentErrors.includes(code) && this.isErrorRecoverable(errorType);
    
    if (shouldReconnect) {
      // Применяем стратегию восстановления
      this.handleErrorRecovery(errorType);
    }

    return shouldReconnect;
  }

  /**
   * Планирование переподключения с улучшенной логикой восстановления
   */
  scheduleReconnect() {
    if (!this.options.enableAutoReconnect) {
      console.log('ResilientWebSocket: Auto-reconnect disabled');
      return;
    }

    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      console.log('ResilientWebSocket: Max reconnection attempts reached');
      this.connectionState = 'failed';
      this.emit('stateChange', this.connectionState);
      this.emit('maxReconnectAttemptsReached', {
        attempts: this.reconnectAttempts,
        consecutiveErrors: this.errorRecovery.consecutiveErrors
      });
      return;
    }

    // Проверяем состояние сети перед переподключением
    if (!navigator.onLine) {
      console.log('ResilientWebSocket: Network offline, waiting for connection...');
      this.waitForNetworkRecovery();
      return;
    }

    this.reconnectAttempts++;
    
    // Адаптивная задержка на основе типа ошибки
    let baseDelay = this.options.reconnectDelay;
    
    // Увеличиваем задержку при множественных ошибках
    if (this.errorRecovery.consecutiveErrors > 3) {
      baseDelay *= 2;
    }
    
    const delay = Math.min(
      baseDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.options.maxReconnectDelay
    );

    console.log(`ResilientWebSocket: Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
    
    this.emit('reconnectScheduled', {
      attempt: this.reconnectAttempts,
      delay: delay,
      consecutiveErrors: this.errorRecovery.consecutiveErrors
    });

    setTimeout(() => {
      if (this.shouldReconnect && !this.isConnected && !this.isConnecting) {
        this.attemptReconnect();
      }
    }, delay);
  }

  /**
   * Попытка переподключения с предварительными проверками
   */
  async attemptReconnect() {
    try {
      // Проверяем сетевое соединение
      if (!navigator.onLine) {
        console.log('ResilientWebSocket: Network still offline, postponing reconnect');
        this.scheduleReconnect();
        return;
      }

      // Проверяем, не слишком ли много ошибок
      if (this.errorRecovery.consecutiveErrors > 10) {
        console.warn('ResilientWebSocket: Too many consecutive errors, extending delay');
        setTimeout(() => this.scheduleReconnect(), 30000); // 30 секунд дополнительной задержки
        return;
      }

      console.log(`ResilientWebSocket: Attempting reconnect ${this.reconnectAttempts}/${this.options.maxReconnectAttempts}`);
      await this.connect();
      
      // Успешное переподключение - сбрасываем счетчики ошибок
      this.errorRecovery.consecutiveErrors = 0;
      this.errorRecovery.errorTypes.clear();
      
    } catch (error) {
      console.error('ResilientWebSocket: Reconnection failed:', error);
      // scheduleReconnect будет вызван автоматически через обработчик ошибок
    }
  }

  /**
   * Ожидание восстановления сетевого соединения
   */
  waitForNetworkRecovery() {
    const checkNetwork = () => {
      if (navigator.onLine && this.shouldReconnect) {
        console.log('ResilientWebSocket: Network recovered, attempting reconnect');
        window.removeEventListener('online', checkNetwork);
        this.scheduleReconnect();
      }
    };

    window.addEventListener('online', checkNetwork);
    
    // Также проверяем периодически на случай, если событие не сработает
    const intervalCheck = setInterval(() => {
      if (navigator.onLine && this.shouldReconnect) {
        clearInterval(intervalCheck);
        window.removeEventListener('online', checkNetwork);
        this.scheduleReconnect();
      } else if (!this.shouldReconnect) {
        clearInterval(intervalCheck);
        window.removeEventListener('online', checkNetwork);
      }
    }, 5000);
  }

  /**
   * Запуск ping/pong механизма
   */
  startPingPong() {
    this.stopPingPong();

    this.pingInterval = setInterval(() => {
      if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
        const pingData = {
          type: 'ping',
          timestamp: Date.now()
        };

        this.ws.send(JSON.stringify(pingData));

        // Устанавливаем таймаут для pong
        this.pongTimeout = setTimeout(() => {
          console.warn('ResilientWebSocket: Pong timeout, reconnecting...');
          this.ws.close(1006, 'Pong timeout');
        }, this.options.pongTimeout);
      }
    }, this.options.pingInterval);
  }

  /**
   * Остановка ping/pong механизма
   */
  stopPingPong() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }

    if (this.pongTimeout) {
      clearTimeout(this.pongTimeout);
      this.pongTimeout = null;
    }
  }

  /**
   * Обработка pong сообщения
   */
  handlePong(data) {
    if (this.pongTimeout) {
      clearTimeout(this.pongTimeout);
      this.pongTimeout = null;
    }

    this.lastPong = Date.now();
    console.log('ResilientWebSocket: Pong received');
  }

  /**
   * Добавление обработчика событий
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
  }

  /**
   * Удаление обработчика событий
   */
  off(event, callback) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).delete(callback);
    }
  }

  /**
   * Вызов обработчиков событий
   */
  emit(event, ...args) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(...args);
        } catch (error) {
          console.error(`ResilientWebSocket: Error in event listener for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Получение статуса соединения
   */
  getStatus() {
    return {
      connected: this.isConnected,
      connecting: this.isConnecting,
      readyState: this.ws ? this.ws.readyState : WebSocket.CLOSED,
      reconnectAttempts: this.reconnectAttempts,
      lastPong: this.lastPong,
      queuedMessages: this.messageQueue.length,
      connectionState: this.connectionState,
      stats: { ...this.connectionStats }
    };
  }

  /**
   * Получение пользовательского статуса для UI
   */
  getUserFriendlyStatus() {
    const statusMap = {
      'connecting': { text: 'Подключение...', color: 'yellow', icon: 'connecting' },
      'connected': { text: 'Подключено', color: 'green', icon: 'connected' },
      'reconnecting': { text: 'Переподключение...', color: 'orange', icon: 'reconnecting' },
      'disconnected': { text: 'Отключено', color: 'gray', icon: 'disconnected' },
      'failed': { text: 'Ошибка подключения', color: 'red', icon: 'error' }
    };

    return statusMap[this.connectionState] || statusMap['disconnected'];
  }

  /**
   * Принудительное переподключение
   */
  reconnect() {
    console.log('ResilientWebSocket: Force reconnecting...');
    
    // Сбрасываем счетчики ошибок при ручном переподключении
    this.errorRecovery.consecutiveErrors = 0;
    this.errorRecovery.errorTypes.clear();
    this.reconnectAttempts = 0;
    
    if (this.ws) {
      this.ws.close(1000, 'Force reconnect');
    }
    
    this.shouldReconnect = true;
    this.connect();
  }

  /**
   * Сброс системы восстановления после ошибок
   */
  resetErrorRecovery() {
    console.log('ResilientWebSocket: Resetting error recovery system');
    this.errorRecovery.consecutiveErrors = 0;
    this.errorRecovery.lastErrorTime = null;
    this.errorRecovery.errorTypes.clear();
    this.reconnectAttempts = 0;
    this.emit('errorRecoveryReset');
  }

  /**
   * Проверка здоровья соединения
   */
  checkConnectionHealth() {
    const now = Date.now();
    const health = {
      connected: this.isConnected,
      connectionState: this.connectionState,
      consecutiveErrors: this.errorRecovery.consecutiveErrors,
      reconnectAttempts: this.reconnectAttempts,
      queuedMessages: this.messageQueue.length,
      lastPong: this.lastPong,
      timeSinceLastPong: this.lastPong ? now - this.lastPong : null,
      networkOnline: navigator.onLine,
      stats: { ...this.connectionStats }
    };

    // Вычисляем показатели здоровья
    health.isHealthy = this.isConnected && 
                      this.errorRecovery.consecutiveErrors < 3 &&
                      (!this.lastPong || (now - this.lastPong) < 60000); // Последний pong не старше минуты

    health.errorRate = this.connectionStats.totalMessages > 0 ? 
                      this.connectionStats.totalErrors / this.connectionStats.totalMessages : 0;

    return health;
  }

  /**
   * Получение рекомендаций по восстановлению
   */
  getRecoveryRecommendations() {
    const health = this.checkConnectionHealth();
    const recommendations = [];

    if (!navigator.onLine) {
      recommendations.push({
        type: 'network',
        message: 'Проверьте подключение к интернету',
        action: 'checkNetwork'
      });
    }

    if (health.consecutiveErrors > 5) {
      recommendations.push({
        type: 'errors',
        message: 'Слишком много ошибок подряд. Попробуйте обновить страницу',
        action: 'pageReload'
      });
    }

    if (health.reconnectAttempts > 5) {
      recommendations.push({
        type: 'reconnect',
        message: 'Множественные попытки переподключения. Проверьте сервер',
        action: 'checkServer'
      });
    }

    if (health.queuedMessages > 10) {
      recommendations.push({
        type: 'queue',
        message: 'Накопилось много неотправленных сообщений',
        action: 'clearQueue'
      });
    }

    if (health.errorRate > 0.1) {
      recommendations.push({
        type: 'errorRate',
        message: 'Высокий уровень ошибок. Возможны проблемы с сервером',
        action: 'contactSupport'
      });
    }

    return recommendations;
  }

  /**
   * Применение рекомендации по восстановлению
   */
  applyRecoveryRecommendation(action) {
    switch (action) {
      case 'checkNetwork':
        // Проверяем сеть и ждем восстановления
        this.waitForNetworkRecovery();
        break;
        
      case 'pageReload':
        // Предлагаем перезагрузить страницу
        this.emit('recommendPageReload');
        break;
        
      case 'checkServer':
        // Увеличиваем интервал переподключения
        this.options.reconnectDelay = Math.min(this.options.reconnectDelay * 2, 30000);
        break;
        
      case 'clearQueue':
        // Очищаем очередь сообщений
        this.messageQueue = [];
        this.emit('queueCleared');
        break;
        
      case 'contactSupport':
        // Уведомляем о необходимости обратиться в поддержку
        this.emit('contactSupportRecommended', {
          errorRate: this.connectionStats.totalErrors / this.connectionStats.totalMessages,
          totalErrors: this.connectionStats.totalErrors
        });
        break;
    }
  }
}

export default ResilientWebSocket;