/**
 * Тесты для ResilientWebSocket
 * Проверяем основную функциональность автоматического переподключения
 */

import ResilientWebSocket from '../ResilientWebSocket';

// Mock WebSocket
global.WebSocket = class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING;
    this.onopen = null;
    this.onclose = null;
    this.onmessage = null;
    this.onerror = null;
    
    // Симулируем успешное подключение через небольшую задержку
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) this.onopen();
    }, 10);
  }
  
  send(data) {
    if (this.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not open');
    }
  }
  
  close(code = 1000, reason = '') {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      this.onclose({ code, reason });
    }
  }
};

// WebSocket constants
WebSocket.CONNECTING = 0;
WebSocket.OPEN = 1;
WebSocket.CLOSING = 2;
WebSocket.CLOSED = 3;

describe('ResilientWebSocket', () => {
  let resilientWS;
  
  beforeEach(() => {
    resilientWS = new ResilientWebSocket('ws://test.example.com', {
      maxReconnectAttempts: 3,
      reconnectDelay: 100,
      pingInterval: 1000
    });
  });
  
  afterEach(() => {
    if (resilientWS) {
      resilientWS.disconnect();
    }
  });

  test('should create ResilientWebSocket instance', () => {
    expect(resilientWS).toBeDefined();
    expect(resilientWS.url).toBe('ws://test.example.com');
    expect(resilientWS.isConnected).toBe(false);
  });

  test('should connect successfully', async () => {
    const connectPromise = resilientWS.connect();
    
    await expect(connectPromise).resolves.toBeUndefined();
    expect(resilientWS.isConnected).toBe(true);
    expect(resilientWS.connectionState).toBe('connected');
  });

  test('should handle state changes', async () => {
    const stateChanges = [];
    resilientWS.on('stateChange', (state) => {
      stateChanges.push(state);
    });

    await resilientWS.connect();
    
    expect(stateChanges).toContain('connecting');
    expect(stateChanges).toContain('connected');
  });

  test('should send messages when connected', async () => {
    await resilientWS.connect();
    
    const result = resilientWS.send({ type: 'test', message: 'hello' });
    expect(result).toBe(true);
    expect(resilientWS.connectionStats.totalMessages).toBe(1);
  });

  test('should queue messages when disconnected', () => {
    const result = resilientWS.send({ type: 'test', message: 'hello' });
    expect(result).toBe(false);
    expect(resilientWS.messageQueue.length).toBe(1);
  });

  test('should provide user-friendly status', async () => {
    // Disconnected state
    let status = resilientWS.getUserFriendlyStatus();
    expect(status.text).toBe('Отключено');
    expect(status.color).toBe('gray');

    // Connected state
    await resilientWS.connect();
    status = resilientWS.getUserFriendlyStatus();
    expect(status.text).toBe('Подключено');
    expect(status.color).toBe('green');
  });

  test('should handle connection close and attempt reconnection', (done) => {
    let reconnectAttempted = false;
    
    resilientWS.on('stateChange', (state) => {
      if (state === 'reconnecting') {
        reconnectAttempted = true;
        done();
      }
    });

    resilientWS.connect().then(() => {
      // Симулируем разрыв соединения
      resilientWS.ws.close(1006, 'Connection lost');
    });
  });

  test('should provide detailed status information', async () => {
    await resilientWS.connect();
    
    const status = resilientWS.getStatus();
    expect(status).toHaveProperty('connected', true);
    expect(status).toHaveProperty('connectionState', 'connected');
    expect(status).toHaveProperty('stats');
    expect(status.stats).toHaveProperty('totalConnections', 1);
  });
});