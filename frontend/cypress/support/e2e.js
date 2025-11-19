// Import commands.js using ES2015 syntax:
import './commands';
import 'cypress-axe';
import 'cypress-real-events';

// Alternatively you can use CommonJS syntax:
// require('./commands')

// Global error handling
Cypress.on('uncaught:exception', (err, runnable) => {
  // Prevent Cypress from failing on uncaught exceptions
  // that are not related to our tests
  if (err.message.includes('ResizeObserver loop limit exceeded')) {
    return false;
  }
  if (err.message.includes('Non-Error promise rejection captured')) {
    return false;
  }
  return true;
});

// Add custom commands for admin panel testing
Cypress.Commands.add('loginAsAdmin', () => {
  cy.visit('/admin/login');
  cy.get('[data-testid="email-input"]').type(Cypress.env('adminEmail'));
  cy.get('[data-testid="password-input"]').type(Cypress.env('adminPassword'));
  cy.get('[data-testid="login-button"]').click();
  cy.url().should('include', '/admin');
  cy.get('[data-testid="admin-dashboard"]').should('be.visible');
});

Cypress.Commands.add('loginAsModerator', () => {
  cy.visit('/admin/login');
  cy.get('[data-testid="email-input"]').type(Cypress.env('moderatorEmail'));
  cy.get('[data-testid="password-input"]').type(Cypress.env('moderatorPassword'));
  cy.get('[data-testid="login-button"]').click();
  cy.url().should('include', '/admin');
  cy.get('[data-testid="moderation-panel"]').should('be.visible');
});

Cypress.Commands.add('navigateToModule', (moduleName) => {
  cy.get(`[data-testid="nav-${moduleName}"]`).click();
  cy.get(`[data-testid="${moduleName}-module"]`).should('be.visible');
});

Cypress.Commands.add('waitForApiResponse', (alias) => {
  cy.wait(alias).then((interception) => {
    expect(interception.response.statusCode).to.be.oneOf([200, 201, 204]);
  });
});

Cypress.Commands.add('checkAccessibility', () => {
  cy.injectAxe();
  cy.checkA11y(null, {
    rules: {
      'color-contrast': { enabled: false }, // Disable for dark theme
    }
  });
});

Cypress.Commands.add('mockWebSocket', () => {
  cy.window().then((win) => {
    win.WebSocket = class MockWebSocket {
      constructor(url) {
        this.url = url;
        this.readyState = 1; // OPEN
        setTimeout(() => {
          if (this.onopen) this.onopen();
        }, 100);
      }
      send() {}
      close() {}
    };
  });
});