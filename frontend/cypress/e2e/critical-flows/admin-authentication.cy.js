describe('Admin Authentication Flow', () => {
  beforeEach(() => {
    cy.visit('/admin/login');
  });

  it('should successfully login as super admin', () => {
    cy.get('[data-testid="email-input"]').type(Cypress.env('adminEmail'));
    cy.get('[data-testid="password-input"]').type(Cypress.env('adminPassword'));
    cy.get('[data-testid="login-button"]').click();

    // Should redirect to admin dashboard
    cy.url().should('include', '/admin');
    cy.get('[data-testid="admin-dashboard"]').should('be.visible');
    
    // Should show all admin modules for super admin
    cy.get('[data-testid="nav-users"]').should('be.visible');
    cy.get('[data-testid="nav-roles"]').should('be.visible');
    cy.get('[data-testid="nav-moderation"]').should('be.visible');
    cy.get('[data-testid="nav-marketing"]').should('be.visible');
    cy.get('[data-testid="nav-project"]').should('be.visible');
    cy.get('[data-testid="nav-notifications"]').should('be.visible');
    cy.get('[data-testid="nav-backup"]').should('be.visible');
  });

  it('should show limited access for moderator role', () => {
    cy.loginAsModerator();
    
    // Should only show moderation-related modules
    cy.get('[data-testid="nav-moderation"]').should('be.visible');
    cy.get('[data-testid="nav-users"]').should('not.exist');
    cy.get('[data-testid="nav-roles"]').should('not.exist');
    cy.get('[data-testid="nav-marketing"]').should('not.exist');
  });

  it('should handle invalid credentials', () => {
    cy.get('[data-testid="email-input"]').type('invalid@example.com');
    cy.get('[data-testid="password-input"]').type('wrongpassword');
    cy.get('[data-testid="login-button"]').click();

    cy.get('[data-testid="error-message"]').should('contain', 'Invalid credentials');
    cy.url().should('include', '/admin/login');
  });

  it('should logout successfully', () => {
    cy.loginAsAdmin();
    
    cy.get('[data-testid="user-menu"]').click();
    cy.get('[data-testid="logout-button"]').click();
    
    cy.url().should('include', '/admin/login');
    cy.get('[data-testid="login-form"]').should('be.visible');
  });

  it('should redirect to login when accessing protected routes', () => {
    cy.visit('/admin/users');
    cy.url().should('include', '/admin/login');
  });

  it('should maintain session across page refreshes', () => {
    cy.loginAsAdmin();
    cy.reload();
    
    cy.get('[data-testid="admin-dashboard"]').should('be.visible');
    cy.url().should('include', '/admin');
  });
});