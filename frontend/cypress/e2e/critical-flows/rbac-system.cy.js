describe('RBAC System Critical Flows', () => {
  beforeEach(() => {
    cy.loginAsAdmin();
    cy.navigateToModule('roles');
  });

  it('should create a new role with specific permissions', () => {
    cy.get('[data-testid="create-role-button"]').click();
    cy.get('[data-testid="role-name-input"]').type('Test Manager');
    cy.get('[data-testid="role-description-input"]').type('Test role for E2E testing');
    
    // Select specific permissions
    cy.get('[data-testid="permission-users-read"]').check();
    cy.get('[data-testid="permission-users-write"]').check();
    cy.get('[data-testid="permission-moderation-read"]').check();
    
    cy.get('[data-testid="save-role-button"]').click();
    
    // Verify role was created
    cy.get('[data-testid="roles-table"]').should('contain', 'Test Manager');
    cy.get('[data-testid="success-message"]').should('contain', 'Role created successfully');
  });

  it('should edit existing role permissions', () => {
    // Find and edit a role
    cy.get('[data-testid="role-row"]').first().within(() => {
      cy.get('[data-testid="edit-role-button"]').click();
    });
    
    // Modify permissions
    cy.get('[data-testid="permission-marketing-read"]').check();
    cy.get('[data-testid="save-role-button"]').click();
    
    cy.get('[data-testid="success-message"]').should('contain', 'Role updated successfully');
  });

  it('should assign role to user', () => {
    cy.navigateToModule('users');
    
    // Find a user and assign role
    cy.get('[data-testid="user-row"]').first().within(() => {
      cy.get('[data-testid="assign-role-button"]').click();
    });
    
    cy.get('[data-testid="role-select"]').select('Test Manager');
    cy.get('[data-testid="confirm-assign-button"]').click();
    
    cy.get('[data-testid="success-message"]').should('contain', 'Role assigned successfully');
  });

  it('should prevent unauthorized access to protected functions', () => {
    // Login as moderator (limited permissions)
    cy.loginAsModerator();
    
    // Try to access user management directly via URL
    cy.visit('/admin/users', { failOnStatusCode: false });
    
    // Should be redirected or show access denied
    cy.get('[data-testid="access-denied"]').should('be.visible');
  });

  it('should show role hierarchy correctly', () => {
    cy.get('[data-testid="role-hierarchy-view"]').click();
    
    // Verify hierarchy structure
    cy.get('[data-testid="hierarchy-super-admin"]').should('be.visible');
    cy.get('[data-testid="hierarchy-admin"]').should('be.visible');
    cy.get('[data-testid="hierarchy-moderator"]').should('be.visible');
    
    // Check parent-child relationships
    cy.get('[data-testid="hierarchy-super-admin"]').within(() => {
      cy.get('[data-testid="child-roles"]').should('contain', 'admin');
    });
  });

  it('should audit role changes', () => {
    // Make a role change
    cy.get('[data-testid="role-row"]').first().within(() => {
      cy.get('[data-testid="edit-role-button"]').click();
    });
    
    cy.get('[data-testid="role-name-input"]').clear().type('Updated Role Name');
    cy.get('[data-testid="save-role-button"]').click();
    
    // Check audit log
    cy.get('[data-testid="view-audit-log"]').click();
    cy.get('[data-testid="audit-entries"]').should('contain', 'Role updated');
    cy.get('[data-testid="audit-entries"]').should('contain', 'Updated Role Name');
  });

  it('should handle super admin protection', () => {
    // Try to delete or modify super admin role
    cy.get('[data-testid="role-row"]').contains('super_admin').within(() => {
      cy.get('[data-testid="delete-role-button"]').should('be.disabled');
      cy.get('[data-testid="edit-role-button"]').click();
    });
    
    // Should show protection warning
    cy.get('[data-testid="protection-warning"]').should('contain', 'Super admin role cannot be modified');
  });

  it('should validate permission dependencies', () => {
    cy.get('[data-testid="create-role-button"]').click();
    
    // Try to assign write permission without read permission
    cy.get('[data-testid="permission-users-write"]').check();
    
    // Should automatically check read permission or show warning
    cy.get('[data-testid="permission-users-read"]').should('be.checked');
  });
});