describe('Page Load Performance Tests', () => {
  beforeEach(() => {
    cy.loginAsAdmin();
  });

  it('should load admin dashboard within performance budget', () => {
    cy.measurePageLoad('admin-dashboard');
    cy.visit('/admin');
    cy.get('[data-testid="admin-dashboard"]').should('be.visible');
    cy.checkPageLoadTime(3000); // 3 second budget
  });

  it('should load user management page efficiently', () => {
    cy.measurePageLoad('user-management');
    cy.navigateToModule('users');
    cy.get('[data-testid="users-table"]').should('be.visible');
    cy.checkPageLoadTime(2500);
  });

  it('should handle large datasets without performance degradation', () => {
    cy.navigateToModule('users');
    
    // Simulate loading 1000+ users
    cy.intercept('GET', '/api/v1/admin/users*', {
      fixture: 'large-user-dataset.json'
    }).as('loadUsers');
    
    cy.get('[data-testid="load-more-users"]').click();
    cy.waitForApiResponse('@loadUsers');
    
    // Measure rendering time
    cy.window().then((win) => {
      const startTime = win.performance.now();
      cy.get('[data-testid="users-table"] tbody tr').should('have.length.greaterThan', 100);
      
      cy.window().then((win2) => {
        const endTime = win2.performance.now();
        const renderTime = endTime - startTime;
        expect(renderTime).to.be.lessThan(1000); // 1 second render budget
      });
    });
  });

  it('should maintain performance with multiple real-time updates', () => {
    cy.navigateToModule('dashboard');
    cy.mockWebSocket();
    
    // Simulate rapid WebSocket updates
    for (let i = 0; i < 50; i++) {
      cy.simulateWebSocketMessage('dashboard_update', {
        active_users: 100 + i,
        timestamp: Date.now()
      });
    }
    
    // Check that UI remains responsive
    cy.get('[data-testid="active-users-count"]').should('be.visible');
    cy.get('[data-testid="refresh-button"]').click();
    cy.get('[data-testid="dashboard-loading"]').should('not.exist');
  });

  it('should lazy load components efficiently', () => {
    // Test lazy loading of heavy components
    cy.visit('/admin');
    
    // Initially, heavy components should not be loaded
    cy.window().then((win) => {
      const modules = Object.keys(win.__webpack_require__.cache || {});
      expect(modules.filter(m => m.includes('MarketingDashboard'))).to.have.length(0);
    });
    
    // Navigate to marketing module
    cy.measurePageLoad('marketing-module');
    cy.navigateToModule('marketing');
    
    // Component should load within budget
    cy.get('[data-testid="marketing-dashboard"]').should('be.visible');
    cy.checkPageLoadTime(2000);
  });

  it('should optimize image and asset loading', () => {
    cy.visit('/admin');
    
    // Check that images are properly optimized
    cy.get('img').each(($img) => {
      cy.wrap($img).should('have.attr', 'loading', 'lazy');
      
      // Check image size is reasonable
      cy.wrap($img).then(($el) => {
        const img = $el[0];
        img.onload = () => {
          expect(img.naturalWidth).to.be.lessThan(2000);
          expect(img.naturalHeight).to.be.lessThan(2000);
        };
      });
    });
  });

  it('should handle memory usage efficiently', () => {
    cy.visit('/admin');
    
    // Navigate through multiple modules to test memory leaks
    const modules = ['users', 'roles', 'moderation', 'marketing', 'project'];
    
    modules.forEach((module) => {
      cy.navigateToModule(module);
      cy.wait(1000);
      
      // Check memory usage doesn't grow excessively
      cy.window().then((win) => {
        if (win.performance.memory) {
          const memoryUsage = win.performance.memory.usedJSHeapSize;
          expect(memoryUsage).to.be.lessThan(100 * 1024 * 1024); // 100MB limit
        }
      });
    });
  });

  it('should optimize bundle size and code splitting', () => {
    cy.visit('/admin');
    
    // Check that initial bundle is not too large
    cy.window().then((win) => {
      const scripts = Array.from(document.querySelectorAll('script[src]'));
      const mainScript = scripts.find(script => 
        script.src.includes('main') || script.src.includes('bundle')
      );
      
      if (mainScript) {
        cy.request(mainScript.src).then((response) => {
          const sizeInKB = response.body.length / 1024;
          expect(sizeInKB).to.be.lessThan(500); // 500KB initial bundle limit
        });
      }
    });
  });

  it('should handle concurrent API requests efficiently', () => {
    cy.visit('/admin');
    
    // Simulate multiple concurrent API calls
    const apiCalls = [
      '/api/v1/admin/dashboard/stats',
      '/api/v1/admin/users?limit=10',
      '/api/v1/admin/moderation/queue',
      '/api/v1/admin/notifications/unread'
    ];
    
    apiCalls.forEach((endpoint, index) => {
      cy.intercept('GET', endpoint).as(`apiCall${index}`);
    });
    
    // Trigger all API calls
    cy.get('[data-testid="refresh-all-data"]').click();
    
    // All should complete within reasonable time
    apiCalls.forEach((_, index) => {
      cy.wait(`@apiCall${index}`, { timeout: 5000 });
    });
  });

  it('should maintain performance with complex animations', () => {
    cy.visit('/admin');
    
    // Test performance with animations enabled
    cy.get('[data-testid="enable-animations"]').click();
    
    // Navigate through modules with animations
    cy.navigateToModule('marketing');
    cy.get('[data-testid="animated-chart"]').should('be.visible');
    
    // Check frame rate during animations
    cy.window().then((win) => {
      let frameCount = 0;
      let startTime = win.performance.now();
      
      const countFrames = () => {
        frameCount++;
        if (win.performance.now() - startTime < 1000) {
          win.requestAnimationFrame(countFrames);
        } else {
          expect(frameCount).to.be.greaterThan(30); // At least 30 FPS
        }
      };
      
      win.requestAnimationFrame(countFrames);
    });
  });
});