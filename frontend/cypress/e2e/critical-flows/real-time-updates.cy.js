describe('Real-time Updates and WebSocket Integration', () => {
  beforeEach(() => {
    cy.loginAsAdmin();
    cy.mockWebSocket();
  });

  it('should establish WebSocket connection on admin panel load', () => {
    cy.waitForWebSocketConnection();
    
    // Verify connection status indicator
    cy.get('[data-testid="connection-status"]').should('contain', 'Connected');
    cy.get('[data-testid="connection-indicator"]').should('have.class', 'bg-green-500');
  });

  it('should receive real-time dashboard updates', () => {
    cy.navigateToModule('dashboard');
    
    // Simulate WebSocket message for dashboard update
    cy.simulateWebSocketMessage('dashboard_update', {
      active_users: 150,
      total_messages: 1250,
      system_status: 'healthy'
    });
    
    // Verify dashboard updates
    cy.get('[data-testid="active-users-count"]').should('contain', '150');
    cy.get('[data-testid="total-messages-count"]').should('contain', '1250');
    cy.get('[data-testid="system-status"]').should('contain', 'healthy');
  });

  it('should show real-time notifications', () => {
    // Simulate notification WebSocket message
    cy.simulateWebSocketMessage('notification', {
      id: 'test-notification-1',
      type: 'warning',
      title: 'System Alert',
      message: 'High CPU usage detected',
      timestamp: new Date().toISOString()
    });
    
    // Verify notification appears
    cy.get('[data-testid="notification-bell"]').should('have.class', 'animate-pulse');
    cy.get('[data-testid="notification-bell"]').click();
    cy.get('[data-testid="notification-dropdown"]').should('contain', 'System Alert');
    cy.get('[data-testid="notification-dropdown"]').should('contain', 'High CPU usage detected');
  });

  it('should update moderation queue in real-time', () => {
    cy.navigateToModule('moderation');
    
    // Simulate new message for moderation
    cy.simulateWebSocketMessage('new_moderation_message', {
      id: 'msg-123',
      content: 'New message requiring moderation',
      user_id: 456,
      priority: 'high',
      created_at: new Date().toISOString()
    });
    
    // Verify message appears in queue
    cy.get('[data-testid="moderation-queue"]').should('contain', 'New message requiring moderation');
    cy.get('[data-testid="queue-count"]').should('be.visible');
  });

  it('should sync data across multiple browser tabs', () => {
    // Open admin panel in current tab
    cy.navigateToModule('users');
    
    // Simulate tab sync message (as if another tab made changes)
    cy.window().then((win) => {
      win.localStorage.setItem('tab-sync-event', JSON.stringify({
        type: 'user_updated',
        data: { id: 1, name: 'Updated User Name' },
        timestamp: Date.now()
      }));
      
      // Trigger storage event
      win.dispatchEvent(new StorageEvent('storage', {
        key: 'tab-sync-event',
        newValue: win.localStorage.getItem('tab-sync-event')
      }));
    });
    
    // Verify data is synced
    cy.get('[data-testid="user-row-1"]').should('contain', 'Updated User Name');
  });

  it('should handle WebSocket reconnection', () => {
    cy.waitForWebSocketConnection();
    
    // Simulate connection loss
    cy.window().then((win) => {
      if (win.adminWebSocket) {
        win.adminWebSocket.readyState = 3; // CLOSED
        if (win.adminWebSocket.onclose) {
          win.adminWebSocket.onclose();
        }
      }
    });
    
    // Verify reconnection indicator
    cy.get('[data-testid="connection-status"]').should('contain', 'Reconnecting');
    cy.get('[data-testid="connection-indicator"]').should('have.class', 'bg-yellow-500');
    
    // Simulate successful reconnection
    cy.wait(2000);
    cy.mockWebSocket();
    
    cy.get('[data-testid="connection-status"]').should('contain', 'Connected');
    cy.get('[data-testid="connection-indicator"]').should('have.class', 'bg-green-500');
  });

  it('should show real-time system status updates', () => {
    cy.navigateToModule('dashboard');
    
    // Simulate system status updates
    cy.simulateWebSocketMessage('system_status', {
      cpu_usage: 85,
      memory_usage: 70,
      disk_usage: 45,
      active_connections: 120,
      ai_model_status: 'healthy'
    });
    
    // Verify status updates
    cy.get('[data-testid="cpu-usage"]').should('contain', '85%');
    cy.get('[data-testid="memory-usage"]').should('contain', '70%');
    cy.get('[data-testid="disk-usage"]').should('contain', '45%');
    cy.get('[data-testid="ai-model-status"]').should('contain', 'healthy');
  });

  it('should update project task status in real-time', () => {
    cy.navigateToModule('project');
    
    // Simulate task status update
    cy.simulateWebSocketMessage('task_updated', {
      id: 'task-456',
      title: 'Fix authentication bug',
      status: 'completed',
      assigned_to: 'John Doe',
      updated_at: new Date().toISOString()
    });
    
    // Verify task status update
    cy.get('[data-testid="task-456"]').should('contain', 'completed');
    cy.get('[data-testid="task-456"]').should('have.class', 'bg-green-100');
  });

  it('should show real-time backup status updates', () => {
    cy.navigateToModule('backup');
    
    // Simulate backup progress update
    cy.simulateWebSocketMessage('backup_progress', {
      backup_id: 'backup-789',
      status: 'in_progress',
      progress: 65,
      current_step: 'Backing up database',
      estimated_completion: '2 minutes'
    });
    
    // Verify backup progress
    cy.get('[data-testid="backup-789"]').should('contain', 'in_progress');
    cy.get('[data-testid="backup-progress-789"]').should('contain', '65%');
    cy.get('[data-testid="backup-step-789"]').should('contain', 'Backing up database');
  });

  it('should handle WebSocket message queuing during disconnection', () => {
    cy.waitForWebSocketConnection();
    
    // Simulate disconnection
    cy.window().then((win) => {
      if (win.adminWebSocket) {
        win.adminWebSocket.readyState = 3; // CLOSED
      }
    });
    
    // Try to send messages while disconnected (should be queued)
    cy.get('[data-testid="test-websocket-button"]').click();
    
    // Reconnect
    cy.mockWebSocket();
    cy.waitForWebSocketConnection();
    
    // Verify queued messages are sent
    cy.get('[data-testid="message-queue-status"]').should('contain', 'All messages sent');
  });
});