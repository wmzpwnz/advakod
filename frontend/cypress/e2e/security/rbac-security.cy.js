describe('RBAC Security Tests', () => {
  beforeEach(() => {
    // Clear any existing auth state
    cy.clearLocalStorage();
    cy.clearCookies();
  });

  it('should prevent unauthorized access to admin routes', () => {
    // Try to access admin routes without authentication
    const protectedRoutes = [
      '/admin',
      '/admin/users',
      '/admin/roles',
      '/admin/moderation',
      '/admin/marketing',
      '/admin/project',
      '/admin/notifications',
      '/admin/backup'
    ];

    protectedRoutes.forEach(route => {
      cy.visit(route, { failOnStatusCode: false });
      cy.url().should('include', '/admin/login');
    });
  });

  it('should enforce role-based access restrictions', () => {
    // Login as moderator (limited permissions)
    cy.loginAsModerator();

    // Should have access to moderation
    cy.visit('/admin/moderation');
    cy.get('[data-testid="moderation-panel"]').should('be.visible');

    // Should NOT have access to user management
    cy.visit('/admin/users', { failOnStatusCode: false });
    cy.get('[data-testid="access-denied"]').should('be.visible');

    // Should NOT have access to role management
    cy.visit('/admin/roles', { failOnStatusCode: false });
    cy.get('[data-testid="access-denied"]').should('be.visible');

    // Should NOT have access to marketing tools
    cy.visit('/admin/marketing', { failOnStatusCode: false });
    cy.get('[data-testid="access-denied"]').should('be.visible');
  });

  it('should validate JWT token integrity', () => {
    cy.loginAsAdmin();

    // Get the current token
    cy.window().then((win) => {
      const token = win.localStorage.getItem('adminToken');
      expect(token).to.exist;

      // Tamper with the token
      const tamperedToken = token.slice(0, -10) + 'tampered123';
      win.localStorage.setItem('adminToken', tamperedToken);
    });

    // Try to access protected resource
    cy.visit('/admin/users', { failOnStatusCode: false });
    
    // Should be redirected to login due to invalid token
    cy.url().should('include', '/admin/login');
    cy.get('[data-testid="error-message"]').should('contain', 'Invalid token');
  });

  it('should handle token expiration correctly', () => {
    cy.loginAsAdmin();

    // Mock expired token
    cy.window().then((win) => {
      // Create a token with expired timestamp
      const expiredPayload = {
        user_id: 1,
        role: 'admin',
        exp: Math.floor(Date.now() / 1000) - 3600 // Expired 1 hour ago
      };
      
      const expiredToken = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.' + 
        btoa(JSON.stringify(expiredPayload)) + 
        '.expired_signature';
      
      win.localStorage.setItem('adminToken', expiredToken);
    });

    // Try to access protected resource
    cy.visit('/admin/users', { failOnStatusCode: false });
    
    // Should be redirected to login
    cy.url().should('include', '/admin/login');
  });

  it('should prevent privilege escalation attacks', () => {
    cy.loginAsModerator();

    // Try to modify role via API manipulation
    cy.request({
      method: 'POST',
      url: `${Cypress.env('apiUrl')}/admin/users/1/roles`,
      headers: {
        'Authorization': `Bearer ${window.localStorage.getItem('adminToken')}`
      },
      body: {
        role_id: 1 // Try to assign super admin role
      },
      failOnStatusCode: false
    }).then((response) => {
      expect(response.status).to.equal(403); // Forbidden
    });
  });

  it('should validate API endpoint permissions', () => {
    cy.loginAsModerator();

    // Test various API endpoints that should be restricted
    const restrictedEndpoints = [
      { method: 'GET', url: '/admin/users', expectedStatus: 403 },
      { method: 'POST', url: '/admin/roles', expectedStatus: 403 },
      { method: 'DELETE', url: '/admin/users/1', expectedStatus: 403 },
      { method: 'PUT', url: '/admin/roles/1', expectedStatus: 403 },
      { method: 'GET', url: '/admin/backup', expectedStatus: 403 }
    ];

    restrictedEndpoints.forEach(({ method, url, expectedStatus }) => {
      cy.request({
        method,
        url: `${Cypress.env('apiUrl')}${url}`,
        headers: {
          'Authorization': `Bearer ${window.localStorage.getItem('adminToken')}`
        },
        failOnStatusCode: false
      }).then((response) => {
        expect(response.status).to.equal(expectedStatus);
      });
    });
  });

  it('should prevent CSRF attacks', () => {
    cy.loginAsAdmin();

    // Try to make request without proper CSRF token
    cy.request({
      method: 'POST',
      url: `${Cypress.env('apiUrl')}/admin/users`,
      headers: {
        'Authorization': `Bearer ${window.localStorage.getItem('adminToken')}`,
        'Origin': 'https://malicious-site.com'
      },
      body: {
        email: 'malicious@example.com',
        password: 'password123',
        role: 'admin'
      },
      failOnStatusCode: false
    }).then((response) => {
      // Should be rejected due to CORS/CSRF protection
      expect(response.status).to.be.oneOf([403, 400]);
    });
  });

  it('should sanitize user inputs to prevent XSS', () => {
    cy.loginAsAdmin();
    cy.navigateToModule('users');

    // Try to inject malicious script in user creation form
    cy.get('[data-testid="create-user-button"]').click();
    
    const maliciousScript = '<script>alert("XSS")</script>';
    const maliciousName = `<img src=x onerror=alert("XSS")>`;
    
    cy.get('[data-testid="user-name-input"]').type(maliciousName);
    cy.get('[data-testid="user-email-input"]').type('test@example.com');
    cy.get('[data-testid="user-password-input"]').type('password123');
    
    cy.get('[data-testid="save-user-button"]').click();

    // Verify that script is not executed and is properly escaped
    cy.get('[data-testid="users-table"]').should('not.contain', '<script>');
    cy.get('[data-testid="users-table"]').should('not.contain', '<img');
    
    // Check that no alert was triggered
    cy.on('window:alert', (text) => {
      throw new Error(`Unexpected alert: ${text}`);
    });
  });

  it('should prevent SQL injection in search queries', () => {
    cy.loginAsAdmin();
    cy.navigateToModule('users');

    // Try SQL injection in search field
    const sqlInjectionPayloads = [
      "'; DROP TABLE users; --",
      "' OR '1'='1",
      "' UNION SELECT * FROM admin_users --",
      "'; INSERT INTO users (email) VALUES ('hacked@example.com'); --"
    ];

    sqlInjectionPayloads.forEach(payload => {
      cy.get('[data-testid="user-search-input"]').clear().type(payload);
      cy.get('[data-testid="search-button"]').click();
      
      // Should not cause any database errors or unauthorized data access
      cy.get('[data-testid="error-message"]').should('not.contain', 'SQL');
      cy.get('[data-testid="error-message"]').should('not.contain', 'database');
    });
  });

  it('should enforce rate limiting on sensitive operations', () => {
    cy.loginAsAdmin();

    // Try to make rapid requests to sensitive endpoint
    const requests = [];
    for (let i = 0; i < 20; i++) {
      requests.push(
        cy.request({
          method: 'POST',
          url: `${Cypress.env('apiUrl')}/admin/roles`,
          headers: {
            'Authorization': `Bearer ${window.localStorage.getItem('adminToken')}`
          },
          body: {
            name: `Test Role ${i}`,
            description: 'Test role for rate limiting'
          },
          failOnStatusCode: false
        })
      );
    }

    // Some requests should be rate limited
    Promise.all(requests).then(responses => {
      const rateLimitedResponses = responses.filter(r => r.status === 429);
      expect(rateLimitedResponses.length).to.be.greaterThan(0);
    });
  });

  it('should validate file upload security', () => {
    cy.loginAsAdmin();
    cy.navigateToModule('backup');

    // Try to upload malicious file types
    const maliciousFiles = [
      'malicious.exe',
      'script.js',
      'backdoor.php',
      'virus.bat'
    ];

    maliciousFiles.forEach(filename => {
      cy.get('[data-testid="file-upload-input"]').selectFile({
        contents: 'malicious content',
        fileName: filename,
        mimeType: 'application/octet-stream'
      }, { force: true });

      cy.get('[data-testid="upload-button"]').click();
      
      // Should reject malicious file types
      cy.get('[data-testid="error-message"]').should('contain', 'Invalid file type');
    });
  });

  it('should protect against session fixation attacks', () => {
    // Set a session ID before login
    cy.window().then((win) => {
      win.localStorage.setItem('sessionId', 'fixed-session-id');
    });

    cy.loginAsAdmin();

    // Session ID should change after successful login
    cy.window().then((win) => {
      const newSessionId = win.localStorage.getItem('sessionId');
      expect(newSessionId).to.not.equal('fixed-session-id');
    });
  });

  it('should implement proper logout and session cleanup', () => {
    cy.loginAsAdmin();

    // Verify user is logged in
    cy.get('[data-testid="admin-dashboard"]').should('be.visible');

    // Logout
    cy.get('[data-testid="user-menu"]').click();
    cy.get('[data-testid="logout-button"]').click();

    // Verify session is completely cleared
    cy.window().then((win) => {
      expect(win.localStorage.getItem('adminToken')).to.be.null;
      expect(win.localStorage.getItem('userRole')).to.be.null;
      expect(win.localStorage.getItem('sessionId')).to.be.null;
    });

    // Try to access protected route after logout
    cy.visit('/admin/users', { failOnStatusCode: false });
    cy.url().should('include', '/admin/login');
  });

  it('should validate password security requirements', () => {
    cy.loginAsAdmin();
    cy.navigateToModule('users');

    cy.get('[data-testid="create-user-button"]').click();

    // Test weak passwords
    const weakPasswords = [
      '123456',
      'password',
      'admin',
      'qwerty',
      '12345678'
    ];

    weakPasswords.forEach(password => {
      cy.get('[data-testid="user-password-input"]').clear().type(password);
      cy.get('[data-testid="save-user-button"]').click();
      
      cy.get('[data-testid="password-error"]').should('contain', 'Password too weak');
    });

    // Test strong password
    cy.get('[data-testid="user-password-input"]').clear().type('StrongP@ssw0rd123!');
    cy.get('[data-testid="user-email-input"]').clear().type('secure@example.com');
    cy.get('[data-testid="save-user-button"]').click();
    
    cy.get('[data-testid="success-message"]').should('contain', 'User created');
  });
});