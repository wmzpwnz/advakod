describe('Admin Panel Accessibility Tests', () => {
  beforeEach(() => {
    cy.loginAsAdmin();
    cy.injectAxe();
  });

  it('should meet accessibility standards on dashboard', () => {
    cy.visit('/admin');
    cy.get('[data-testid="admin-dashboard"]').should('be.visible');
    
    // Check accessibility
    cy.checkA11y(null, {
      rules: {
        'color-contrast': { enabled: false }, // Disable for dark theme testing
      }
    });
  });

  it('should have proper keyboard navigation', () => {
    cy.visit('/admin');
    
    // Test tab navigation through main elements
    cy.get('body').tab();
    cy.focused().should('have.attr', 'data-testid', 'skip-to-content');
    
    cy.tab();
    cy.focused().should('contain', 'Dashboard'); // First nav item
    
    // Test navigation menu keyboard access
    cy.get('[data-testid="nav-users"]').focus().type('{enter}');
    cy.url().should('include', '/admin/users');
  });

  it('should have proper ARIA labels and roles', () => {
    cy.visit('/admin');
    
    // Check main navigation has proper ARIA
    cy.get('[role="navigation"]').should('exist');
    cy.get('[aria-label="Main navigation"]').should('exist');
    
    // Check buttons have accessible names
    cy.get('button').each(($btn) => {
      cy.wrap($btn).should('satisfy', ($el) => {
        const hasAriaLabel = $el.attr('aria-label');
        const hasText = $el.text().trim().length > 0;
        const hasAriaLabelledBy = $el.attr('aria-labelledby');
        return hasAriaLabel || hasText || hasAriaLabelledBy;
      });
    });
  });

  it('should have proper heading hierarchy', () => {
    cy.visit('/admin');
    
    // Check heading hierarchy (h1 -> h2 -> h3, etc.)
    cy.get('h1').should('have.length', 1);
    cy.get('h1').should('contain', 'Admin Dashboard');
    
    // Verify no heading levels are skipped
    cy.get('h1, h2, h3, h4, h5, h6').then(($headings) => {
      const levels = Array.from($headings).map(h => parseInt(h.tagName.charAt(1)));
      
      for (let i = 1; i < levels.length; i++) {
        const diff = levels[i] - levels[i-1];
        expect(diff).to.be.at.most(1); // Should not skip heading levels
      }
    });
  });

  it('should have accessible forms', () => {
    cy.navigateToModule('users');
    cy.get('[data-testid="create-user-button"]').click();
    
    // Check form accessibility
    cy.checkA11y('[data-testid="user-form"]');
    
    // Check form labels
    cy.get('input').each(($input) => {
      const id = $input.attr('id');
      if (id) {
        cy.get(`label[for="${id}"]`).should('exist');
      } else {
        // Should have aria-label or aria-labelledby
        cy.wrap($input).should('satisfy', ($el) => {
          return $el.attr('aria-label') || $el.attr('aria-labelledby');
        });
      }
    });
    
    // Check required field indicators
    cy.get('input[required]').each(($input) => {
      cy.wrap($input).should('have.attr', 'aria-required', 'true');
    });
  });

  it('should have accessible data tables', () => {
    cy.navigateToModule('users');
    
    // Check table accessibility
    cy.get('[data-testid="users-table"]').within(() => {
      // Table should have proper structure
      cy.get('thead').should('exist');
      cy.get('tbody').should('exist');
      
      // Headers should have proper scope
      cy.get('th').each(($th) => {
        cy.wrap($th).should('have.attr', 'scope');
      });
      
      // Table should have caption or aria-label
      cy.get('table').should('satisfy', ($table) => {
        return $table.find('caption').length > 0 || 
               $table.attr('aria-label') || 
               $table.attr('aria-labelledby');
      });
    });
    
    cy.checkA11y('[data-testid="users-table"]');
  });

  it('should have accessible modals and dialogs', () => {
    cy.navigateToModule('users');
    cy.get('[data-testid="create-user-button"]').click();
    
    // Check modal accessibility
    cy.get('[role="dialog"]').should('exist');
    cy.get('[role="dialog"]').should('have.attr', 'aria-modal', 'true');
    cy.get('[role="dialog"]').should('have.attr', 'aria-labelledby');
    
    // Focus should be trapped in modal
    cy.get('[role="dialog"]').within(() => {
      cy.get('input, button, select, textarea, [tabindex]')
        .first()
        .should('be.focused');
    });
    
    // Escape key should close modal
    cy.get('body').type('{esc}');
    cy.get('[role="dialog"]').should('not.exist');
  });

  it('should have accessible notifications', () => {
    // Trigger a notification
    cy.createTestNotification('info', 'Test accessibility notification');
    
    cy.get('[data-testid="notification-bell"]').click();
    
    // Check notification accessibility
    cy.get('[role="alert"]').should('exist');
    cy.get('[aria-live="polite"]').should('exist');
    
    // Notifications should be announced to screen readers
    cy.get('[data-testid="notification-item"]').should('have.attr', 'role', 'listitem');
  });

  it('should support high contrast mode', () => {
    // Simulate high contrast mode
    cy.window().then((win) => {
      win.matchMedia = cy.stub().returns({
        matches: true,
        media: '(prefers-contrast: high)',
        addEventListener: cy.stub(),
        removeEventListener: cy.stub()
      });
    });
    
    cy.reload();
    
    // Check that high contrast styles are applied
    cy.get('[data-testid="admin-dashboard"]').should('be.visible');
    cy.checkA11y();
  });

  it('should support reduced motion preferences', () => {
    // Simulate reduced motion preference
    cy.window().then((win) => {
      win.matchMedia = cy.stub().returns({
        matches: true,
        media: '(prefers-reduced-motion: reduce)',
        addEventListener: cy.stub(),
        removeEventListener: cy.stub()
      });
    });
    
    cy.reload();
    
    // Verify animations are disabled or reduced
    cy.get('[data-testid="animated-element"]').should('have.css', 'animation-duration', '0s');
  });

  it('should have accessible error messages', () => {
    cy.navigateToModule('users');
    cy.get('[data-testid="create-user-button"]').click();
    
    // Submit form with invalid data
    cy.get('[data-testid="user-email-input"]').type('invalid-email');
    cy.get('[data-testid="save-user-button"]').click();
    
    // Check error message accessibility
    cy.get('[role="alert"]').should('exist');
    cy.get('[aria-describedby]').should('exist');
    
    // Error should be associated with the field
    cy.get('[data-testid="user-email-input"]').should('have.attr', 'aria-invalid', 'true');
    cy.get('[data-testid="user-email-input"]').should('have.attr', 'aria-describedby');
  });

  it('should have accessible loading states', () => {
    cy.navigateToModule('users');
    
    // Check loading indicator accessibility
    cy.get('[data-testid="loading-spinner"]').should('have.attr', 'role', 'status');
    cy.get('[data-testid="loading-spinner"]').should('have.attr', 'aria-label', 'Loading');
    
    // Loading content should be announced
    cy.get('[aria-live="polite"]').should('contain', 'Loading');
  });

  it('should have accessible charts and visualizations', () => {
    cy.navigateToModule('marketing');
    
    // Check chart accessibility
    cy.get('[data-testid="sales-funnel-chart"]').should('have.attr', 'role', 'img');
    cy.get('[data-testid="sales-funnel-chart"]').should('have.attr', 'aria-label');
    
    // Should have text alternative for screen readers
    cy.get('[data-testid="chart-data-table"]').should('exist');
    cy.get('[data-testid="chart-description"]').should('exist');
  });

  it('should meet WCAG 2.1 AA standards', () => {
    const pages = [
      '/admin',
      '/admin/users',
      '/admin/roles',
      '/admin/moderation',
      '/admin/marketing',
      '/admin/project',
      '/admin/notifications'
    ];
    
    pages.forEach(page => {
      cy.visit(page);
      cy.get('main').should('be.visible');
      
      // Run comprehensive accessibility check
      cy.checkA11y(null, {
        runOnly: {
          type: 'tag',
          values: ['wcag2a', 'wcag2aa', 'wcag21aa']
        }
      });
    });
  });

  it('should have proper focus management', () => {
    cy.visit('/admin');
    
    // Test focus indicators are visible
    cy.get('[data-testid="nav-users"]').focus();
    cy.get('[data-testid="nav-users"]').should('have.focus');
    cy.get('[data-testid="nav-users"]').should('have.css', 'outline-width').and('not.equal', '0px');
    
    // Test focus doesn't get lost during navigation
    cy.get('[data-testid="nav-users"]').click();
    cy.get('h1').should('be.focused'); // Focus should move to main content
  });

  it('should support screen reader navigation', () => {
    cy.visit('/admin');
    
    // Check landmark regions
    cy.get('[role="banner"]').should('exist'); // Header
    cy.get('[role="navigation"]').should('exist'); // Navigation
    cy.get('[role="main"]').should('exist'); // Main content
    cy.get('[role="contentinfo"]').should('exist'); // Footer (if present)
    
    // Check skip links
    cy.get('[data-testid="skip-to-content"]').should('exist');
    cy.get('[data-testid="skip-to-content"]').click();
    cy.get('[role="main"]').should('be.focused');
  });
});