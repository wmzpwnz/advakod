// Custom commands for admin panel testing

// Authentication commands
Cypress.Commands.add('createTestUser', (role = 'user') => {
  return cy.request({
    method: 'POST',
    url: `${Cypress.env('apiUrl')}/admin/users`,
    headers: {
      'Authorization': `Bearer ${window.localStorage.getItem('adminToken')}`
    },
    body: {
      email: `test-${Date.now()}@example.com`,
      password: 'testpassword123',
      role: role,
      is_active: true
    }
  });
});

Cypress.Commands.add('deleteTestUser', (userId) => {
  return cy.request({
    method: 'DELETE',
    url: `${Cypress.env('apiUrl')}/admin/users/${userId}`,
    headers: {
      'Authorization': `Bearer ${window.localStorage.getItem('adminToken')}`
    }
  });
});

// RBAC testing commands
Cypress.Commands.add('createTestRole', (roleName, permissions) => {
  return cy.request({
    method: 'POST',
    url: `${Cypress.env('apiUrl')}/admin/roles`,
    headers: {
      'Authorization': `Bearer ${window.localStorage.getItem('adminToken')}`
    },
    body: {
      name: roleName,
      description: `Test role ${roleName}`,
      permissions: permissions
    }
  });
});

Cypress.Commands.add('assignRoleToUser', (userId, roleId) => {
  return cy.request({
    method: 'POST',
    url: `${Cypress.env('apiUrl')}/admin/users/${userId}/roles`,
    headers: {
      'Authorization': `Bearer ${window.localStorage.getItem('adminToken')}`
    },
    body: {
      role_id: roleId
    }
  });
});

// Moderation testing commands
Cypress.Commands.add('createTestMessage', (content, needsModeration = true) => {
  return cy.request({
    method: 'POST',
    url: `${Cypress.env('apiUrl')}/admin/moderation/messages`,
    headers: {
      'Authorization': `Bearer ${window.localStorage.getItem('adminToken')}`
    },
    body: {
      content: content,
      user_id: 1,
      needs_moderation: needsModeration,
      ai_response: 'Test AI response',
      created_at: new Date().toISOString()
    }
  });
});

// Marketing testing commands
Cypress.Commands.add('createTestPromoCode', (code, discount) => {
  return cy.request({
    method: 'POST',
    url: `${Cypress.env('apiUrl')}/admin/marketing/promo-codes`,
    headers: {
      'Authorization': `Bearer ${window.localStorage.getItem('adminToken')}`
    },
    body: {
      code: code,
      discount_type: 'percentage',
      discount_value: discount,
      usage_limit: 100,
      valid_from: new Date().toISOString(),
      valid_to: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
    }
  });
});

// Project management testing commands
Cypress.Commands.add('createTestTask', (title, assignedTo) => {
  return cy.request({
    method: 'POST',
    url: `${Cypress.env('apiUrl')}/admin/project/tasks`,
    headers: {
      'Authorization': `Bearer ${window.localStorage.getItem('adminToken')}`
    },
    body: {
      title: title,
      description: `Test task: ${title}`,
      status: 'todo',
      priority: 'medium',
      assigned_to: assignedTo,
      due_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()
    }
  });
});

// Notification testing commands
Cypress.Commands.add('createTestNotification', (type, message) => {
  return cy.request({
    method: 'POST',
    url: `${Cypress.env('apiUrl')}/admin/notifications`,
    headers: {
      'Authorization': `Bearer ${window.localStorage.getItem('adminToken')}`
    },
    body: {
      type: type,
      title: 'Test Notification',
      message: message,
      priority: 'medium',
      channels: ['web']
    }
  });
});

// Backup testing commands
Cypress.Commands.add('createTestBackup', () => {
  return cy.request({
    method: 'POST',
    url: `${Cypress.env('apiUrl')}/admin/backup/create`,
    headers: {
      'Authorization': `Bearer ${window.localStorage.getItem('adminToken')}`
    },
    body: {
      backup_type: 'manual',
      components: ['database', 'files']
    }
  });
});

// Performance testing helpers
Cypress.Commands.add('measurePageLoad', (pageName) => {
  cy.window().then((win) => {
    const startTime = win.performance.now();
    return cy.wrap(startTime).as('startTime');
  });
});

Cypress.Commands.add('checkPageLoadTime', (maxTime = 3000) => {
  cy.get('@startTime').then((startTime) => {
    cy.window().then((win) => {
      const endTime = win.performance.now();
      const loadTime = endTime - startTime;
      expect(loadTime).to.be.lessThan(maxTime);
      cy.log(`Page load time: ${loadTime.toFixed(2)}ms`);
    });
  });
});

// Real-time testing helpers
Cypress.Commands.add('waitForWebSocketConnection', () => {
  cy.window().then((win) => {
    return new Cypress.Promise((resolve) => {
      const checkConnection = () => {
        if (win.adminWebSocket && win.adminWebSocket.readyState === 1) {
          resolve();
        } else {
          setTimeout(checkConnection, 100);
        }
      };
      checkConnection();
    });
  });
});

Cypress.Commands.add('simulateWebSocketMessage', (type, data) => {
  cy.window().then((win) => {
    if (win.adminWebSocket && win.adminWebSocket.onmessage) {
      const message = {
        data: JSON.stringify({ type, data })
      };
      win.adminWebSocket.onmessage(message);
    }
  });
});