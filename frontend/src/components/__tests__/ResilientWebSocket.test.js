/**
 * Comprehensive tests for ResilientWebSocket
 * Tests reconnection, timeout handling, and error recovery
 */

import ResilientWebSocket from '../../services/ResilientWebSocket';

// Enhanced WebSocket mock
global.WebSocket = class MockWebSocket {
  constructor(url, protocols) {
    this.url = url;
    this.protocols = protocols;
    this.readyState = WebSocket.CONNECTING;
    this.onopen = null;
    this.onclose = null;
    this.onmessage = null;
    this.onerror = null;
    this.sentMessages = [];
    
    // Simulate connection behavior
    setTimeout(() => {
      if (this.shouldFail) {
        this.readyState = WebSocket.CLOSED;
        if (this.onerror) this.onerror(new Error('Connection failed'));
        if (this.onclose) this.onclose({ code: 1006, reason: 'Connection failed' });
      } else {
        this.readyState = WebSocket.OPEN;
        if (this.onopen) this.onopen();
      }
    }, 10);
  }
  
  send(data) {
    if (this.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket is not open');
    }
    this.sentMessages.push(data);
  }
  
  close(code = 1000, reason = '') {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      this.onclose({ code, reason });
    }
  }
  
  // Test helper methods
  simulateMessage(data) {
    if (this.onmessage) {
      this.onmessage({ data: JSON.stringify(data) });
    }
  }
  
  simulateError(error) {
    if (this.onerror) {
      this.onerror(error);
    }
  }
};

// WebSocket constants
WebSocket.CONNECTING = 0;
WebSocket.OPEN = 1;
WebSocket.CLOSING = 2;
WebSocket.CLOSED = 3;

describe('ResilientWebSocket Comprehensive Tests', () => {
  let resilientWS;
  
  beforeEach(() => {
    resilientWS = new ResilientWebSocket('ws://test.example.com', {
      maxReconnectAttempts: 5,
      reconnectDelay: 100,
      pingInterval: 1000,
      timeout: 5000
    });
  });
  
  afterEach(() => {
    if (resilientWS) {
      resilientWS.disconnect();
    }
  });

  describe('Connection Management', () => {
    test('should establish initial connection', async () => {
      await resilientWS.connect();
      
      expect(resilientWS.isConnected).toBe(true);
      expect(resilientWS.connectionState).toBe('connected');
      expect(resilientWS.connectionStats.totalConnections).toBe(1);
    });

    test('should handle connection failure', async () => {
      // Mock connection failure
      global.WebSocket.prototype.shouldFail = true;
      
      const stateChanges = [];
      resilientWS.on('stateChange', (state) => {
        stateChanges.push(state);
      });

      try {
        await resilientWS.connect();
      } catch (error) {
        // Expected to fail
      }

      expect(stateChanges).toContain('connecting');
      expect(stateChanges).toContain('failed');
      expect(resilientWS.isConnected).toBe(false);
      
      // Clean up
      delete global.WebSocket.prototype.shouldFail;
    });

    test('should reconnect after connection loss', (done) => {
      let reconnectAttempted = false;
      
      resilientWS.on('stateChange', (state) => {
        if (state === 'reconnecting') {
          reconnectAttempted = true;
        }
        if (state === 'connected' && reconnectAttempted) {
          expect(resilientWS.connectionStats.totalReconnections).toBeGreaterThan(0);
          done();
        }
      });

      resilientWS.connect().then(() => {
        // Simulate connection loss
        resilientWS.ws.close(1006, 'Connection lost');
      });
    });

    test('should respect max reconnect attempts', async () => {
      resilientWS.options.maxReconnectAttempts = 2;
      global.WebSocket.prototype.shouldFail = true;
      
      const errorEvents = [];
      resilientWS.on('error', (error) => {
        errorEvents.push(error);
      });

      try {
        await resilientWS.connect();
      } catch (error) {
        // Expected
      }

      // Should eventually give up
      expect(resilientWS.reconnectAttempts).toBeLessThanOrEqual(2);
      
      // Clean up
      delete global.WebSocket.prototype.shouldFail;
    });
  });

  describe('Message Handling', () => {
    beforeEach(async () => {
      await resilientWS.connect();
    });

    test('should send messages when connected', () => {
      const message = { type: 'test', data: 'hello' };
      const result = resilientWS.send(message);
      
      expect(result).toBe(true);
      expect(resilientWS.ws.sentMessages).toHaveLength(1);
      expect(JSON.parse(resilientWS.ws.sentMessages[0])).toEqual(message);
    });

    test('should queue messages when disconnected', () => {
      resilientWS.ws.close();
      
      const message = { type: 'test', data: 'queued' };
      const result = resilientWS.send(message);
      
      expect(result).toBe(false);
      expect(resilientWS.messageQueue).toHaveLength(1);
      expect(resilientWS.messageQueue[0]).toEqual(message);
    });

    test('should process queued messages on reconnect', async () => {
      // Queue messages while disconnected
      resilientWS.ws.close();
      resilientWS.send({ type: 'queued1' });
      resilientWS.send({ type: 'queued2' });
      
      expect(resilientWS.messageQueue).toHaveLength(2);
      
      // Reconnect
      await resilientWS.connect();
      
      // Messages should be sent
      expect(resilientWS.messageQueue).toHaveLength(0);
      expect(resilientWS.ws.sentMessages.length).toBeGreaterThanOrEqual(2);
    });

    test('should handle incoming messages', (done) => {
      const testMessage = { type: 'response', data: 'test data' };
      
      resilientWS.on('message', (message) => {
        expect(message).toEqual(testMessage);
        done();
      });

      resilientWS.ws.simulateMessage(testMessage);
    });

    test('should handle message parsing errors', () => {
      const errorEvents = [];
      resilientWS.on('error', (error) => {
        errorEvents.push(error);
      });

      // Simulate invalid JSON
      if (resilientWS.ws.onmessage) {
        resilientWS.ws.onmessage({ data: 'invalid json {' });
      }

      expect(errorEvents.length).toBeGreaterThan(0);
    });
  });

  describe('Ping/Pong Mechanism', () => {
    beforeEach(async () => {
      await resilientWS.connect();
    });

    test('should send ping messages', (done) => {
      resilientWS.options.pingInterval = 50; // Fast ping for testing
      
      setTimeout(() => {
        const sentMessages = resilientWS.ws.sentMessages;
        const pingMessages = sentMessages.filter(msg => {
          try {
            const parsed = JSON.parse(msg);
            return parsed.type === 'ping';
          } catch {
            return false;
          }
        });
        
        expect(pingMessages.length).toBeGreaterThan(0);
        done();
      }, 100);
    });

    test('should handle pong responses', () => {
      const pongMessage = { type: 'pong', timestamp: Date.now() };
      
      resilientWS.ws.simulateMessage(pongMessage);
      
      expect(resilientWS.lastPong).toBeGreaterThan(0);
    });

    test('should detect connection timeout', (done) => {
      resilientWS.options.timeout = 100; // Short timeout for testing
      
      resilientWS.on('stateChange', (state) => {
        if (state === 'timeout') {
          done();
        }
      });

      // Don't respond to pings to simulate timeout
      resilientWS.ws.simulateMessage = () => {}; // Override to not respond
    });
  });

  describe('Error Handling', () => {
    test('should handle WebSocket errors gracefully', (done) => {
      resilientWS.on('error', (error) => {
        expect(error).toBeDefined();
        done();
      });

      resilientWS.connect().then(() => {
        resilientWS.ws.simulateError(new Error('Test error'));
      });
    });

    test('should handle network errors during send', async () => {
      await resilientWS.connect();
      
      // Mock send to throw error
      resilientWS.ws.send = () => {
        throw new Error('Network error');
      };
      
      const result = resilientWS.send({ type: 'test' });
      expect(result).toBe(false);
    });

    test('should recover from temporary errors', async () => {
      let connectionAttempts = 0;
      const originalWebSocket = global.WebSocket;
      
      global.WebSocket = class extends originalWebSocket {
        constructor(...args) {
          super(...args);
          connectionAttempts++;
          
          // Fail first attempt, succeed second
          if (connectionAttempts === 1) {
            this.shouldFail = true;
          }
        }
      };

      const stateChanges = [];
      resilientWS.on('stateChange', (state) => {
        stateChanges.push(state);
      });

      await resilientWS.connect();
      
      // Should eventually connect after retry
      expect(stateChanges).toContain('connected');
      expect(connectionAttempts).toBeGreaterThan(1);
      
      // Restore
      global.WebSocket = originalWebSocket;
    });
  });

  describe('Status and Statistics', () => {
    test('should provide accurate connection status', async () => {
      // Initially disconnected
      let status = resilientWS.getUserFriendlyStatus();
      expect(status.text).toBe('Отключено');
      expect(status.color).toBe('gray');

      // After connection
      await resilientWS.connect();
      status = resilientWS.getUserFriendlyStatus();
      expect(status.text).toBe('Подключено');
      expect(status.color).toBe('green');
    });

    test('should track connection statistics', async () => {
      await resilientWS.connect();
      
      resilientWS.send({ type: 'test1' });
      resilientWS.send({ type: 'test2' });
      
      const stats = resilientWS.getStatus();
      expect(stats.connected).toBe(true);
      expect(stats.stats.totalConnections).toBe(1);
      expect(stats.stats.totalMessages).toBe(2);
    });

    test('should track reconnection statistics', async () => {
      await resilientWS.connect();
      
      // Force reconnection
      resilientWS.ws.close(1006);
      
      // Wait for reconnection
      await new Promise(resolve => {
        resilientWS.on('stateChange', (state) => {
          if (state === 'connected') {
            resolve();
          }
        });
      });
      
      const stats = resilientWS.getStatus();
      expect(stats.stats.totalReconnections).toBeGreaterThan(0);
    });
  });

  describe('Configuration Options', () => {
    test('should respect custom reconnect delay', () => {
      const customWS = new ResilientWebSocket('ws://test.com', {
        reconnectDelay: 500
      });
      
      expect(customWS.options.reconnectDelay).toBe(500);
    });

    test('should respect custom max attempts', () => {
      const customWS = new ResilientWebSocket('ws://test.com', {
        maxReconnectAttempts: 10
      });
      
      expect(customWS.options.maxReconnectAttempts).toBe(10);
    });

    test('should use exponential backoff', async () => {
      resilientWS.options.maxReconnectAttempts = 3;
      global.WebSocket.prototype.shouldFail = true;
      
      const delays = [];
      const originalSetTimeout = global.setTimeout;
      global.setTimeout = (fn, delay) => {
        delays.push(delay);
        return originalSetTimeout(fn, 0); // Execute immediately for testing
      };

      try {
        await resilientWS.connect();
      } catch (error) {
        // Expected to fail
      }

      // Should have exponential backoff delays
      expect(delays.length).toBeGreaterThan(0);
      if (delays.length > 1) {
        expect(delays[1]).toBeGreaterThan(delays[0]);
      }
      
      // Restore
      global.setTimeout = originalSetTimeout;
      delete global.WebSocket.prototype.shouldFail;
    });
  });

  describe('Event System', () => {
    test('should support event listeners', () => {
      const events = [];
      
      resilientWS.on('stateChange', (state) => events.push(`state:${state}`));
      resilientWS.on('error', (error) => events.push(`error:${error.message}`));
      
      // Trigger events
      resilientWS.emit('stateChange', 'connecting');
      resilientWS.emit('error', new Error('test error'));
      
      expect(events).toContain('state:connecting');
      expect(events).toContain('error:test error');
    });

    test('should support removing event listeners', () => {
      const handler = jest.fn();
      
      resilientWS.on('test', handler);
      resilientWS.emit('test', 'data');
      expect(handler).toHaveBeenCalledWith('data');
      
      resilientWS.off('test', handler);
      resilientWS.emit('test', 'data2');
      expect(handler).toHaveBeenCalledTimes(1); // Should not be called again
    });
  });

  describe('Integration Scenarios', () => {
    test('should handle rapid connect/disconnect cycles', async () => {
      for (let i = 0; i < 3; i++) {
        await resilientWS.connect();
        expect(resilientWS.isConnected).toBe(true);
        
        resilientWS.disconnect();
        expect(resilientWS.isConnected).toBe(false);
      }
    });

    test('should handle message flood', async () => {
      await resilientWS.connect();
      
      // Send many messages quickly
      const messages = [];
      for (let i = 0; i < 100; i++) {
        messages.push({ type: 'flood', id: i });
        resilientWS.send(messages[i]);
      }
      
      // Should handle all messages
      expect(resilientWS.ws.sentMessages.length).toBe(100);
    });

    test('should maintain connection during browser visibility changes', async () => {
      await resilientWS.connect();
      
      // Simulate page visibility change
      Object.defineProperty(document, 'hidden', {
        writable: true,
        value: true
      });
      
      document.dispatchEvent(new Event('visibilitychange'));
      
      // Connection should remain stable
      expect(resilientWS.isConnected).toBe(true);
      
      // Restore
      Object.defineProperty(document, 'hidden', {
        writable: true,
        value: false
      });
    });
  });
});