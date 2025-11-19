describe('Moderation System Workflow', () => {
  beforeEach(() => {
    cy.loginAsAdmin();
    cy.navigateToModule('moderation');
  });

  it('should display moderation queue with pending messages', () => {
    cy.get('[data-testid="moderation-queue"]').should('be.visible');
    cy.get('[data-testid="queue-filters"]').should('be.visible');
    cy.get('[data-testid="queue-stats"]').should('contain', 'Pending');
  });

  it('should moderate a message successfully', () => {
    // Create a test message for moderation
    cy.createTestMessage('Test message that needs moderation').then((response) => {
      const messageId = response.body.id;
      
      // Refresh to see the new message
      cy.reload();
      
      // Find and moderate the message
      cy.get(`[data-testid="message-${messageId}"]`).within(() => {
        cy.get('[data-testid="moderate-button"]').click();
      });
      
      // Fill moderation form
      cy.get('[data-testid="rating-input"]').click();
      cy.get('[data-testid="rating-8"]').click(); // 8 stars
      cy.get('[data-testid="comment-input"]').type('Good response, approved');
      cy.get('[data-testid="approve-button"]').click();
      
      // Verify moderation was successful
      cy.get('[data-testid="success-message"]').should('contain', 'Message moderated successfully');
      cy.get(`[data-testid="message-${messageId}"]`).should('contain', 'Approved');
    });
  });

  it('should reject a message with feedback', () => {
    cy.createTestMessage('Inappropriate test message').then((response) => {
      const messageId = response.body.id;
      cy.reload();
      
      cy.get(`[data-testid="message-${messageId}"]`).within(() => {
        cy.get('[data-testid="moderate-button"]').click();
      });
      
      // Select problem categories
      cy.get('[data-testid="problem-category-inappropriate"]').check();
      cy.get('[data-testid="problem-category-inaccurate"]').check();
      
      cy.get('[data-testid="rating-input"]').click();
      cy.get('[data-testid="rating-3"]').click(); // 3 stars
      cy.get('[data-testid="comment-input"]').type('Contains inappropriate content');
      cy.get('[data-testid="reject-button"]').click();
      
      cy.get('[data-testid="success-message"]').should('contain', 'Message rejected');
      cy.get(`[data-testid="message-${messageId}"]`).should('contain', 'Rejected');
    });
  });

  it('should filter messages by status and priority', () => {
    // Test status filter
    cy.get('[data-testid="status-filter"]').select('pending');
    cy.get('[data-testid="message-row"]').each(($el) => {
      cy.wrap($el).should('contain', 'Pending');
    });
    
    // Test priority filter
    cy.get('[data-testid="priority-filter"]').select('high');
    cy.get('[data-testid="message-row"]').each(($el) => {
      cy.wrap($el).should('contain', 'High');
    });
  });

  it('should show moderator leaderboard and stats', () => {
    cy.get('[data-testid="leaderboard-tab"]').click();
    
    cy.get('[data-testid="moderator-leaderboard"]').should('be.visible');
    cy.get('[data-testid="moderator-stats"]').should('contain', 'Messages Moderated');
    cy.get('[data-testid="moderator-stats"]').should('contain', 'Average Rating');
    cy.get('[data-testid="moderator-badges"]').should('be.visible');
  });

  it('should assign moderator badges based on performance', () => {
    // Moderate several messages to earn badges
    for (let i = 0; i < 5; i++) {
      cy.createTestMessage(`Test message ${i} for badge testing`).then((response) => {
        const messageId = response.body.id;
        cy.reload();
        
        cy.get(`[data-testid="message-${messageId}"]`).within(() => {
          cy.get('[data-testid="moderate-button"]').click();
        });
        
        cy.get('[data-testid="rating-input"]').click();
        cy.get('[data-testid="rating-9"]').click();
        cy.get('[data-testid="comment-input"]').type(`Quality moderation ${i}`);
        cy.get('[data-testid="approve-button"]').click();
        
        cy.wait(1000); // Wait between moderations
      });
    }
    
    // Check if badges were awarded
    cy.get('[data-testid="leaderboard-tab"]').click();
    cy.get('[data-testid="user-badges"]').should('contain', 'Quality Moderator');
  });

  it('should show moderation analytics and trends', () => {
    cy.get('[data-testid="analytics-tab"]').click();
    
    cy.get('[data-testid="moderation-chart"]').should('be.visible');
    cy.get('[data-testid="quality-trends"]').should('be.visible');
    cy.get('[data-testid="response-time-stats"]').should('be.visible');
    
    // Test date range filter
    cy.get('[data-testid="date-range-picker"]').click();
    cy.get('[data-testid="last-7-days"]').click();
    
    cy.get('[data-testid="moderation-chart"]').should('be.visible');
  });

  it('should handle bulk moderation actions', () => {
    // Select multiple messages
    cy.get('[data-testid="select-all-checkbox"]').check();
    
    // Perform bulk action
    cy.get('[data-testid="bulk-actions-dropdown"]').select('approve');
    cy.get('[data-testid="bulk-comment-input"]').type('Bulk approval for testing');
    cy.get('[data-testid="confirm-bulk-action"]').click();
    
    cy.get('[data-testid="success-message"]').should('contain', 'Bulk action completed');
  });

  it('should export moderation reports', () => {
    cy.get('[data-testid="analytics-tab"]').click();
    cy.get('[data-testid="export-report-button"]').click();
    
    cy.get('[data-testid="export-format-select"]').select('csv');
    cy.get('[data-testid="export-date-range"]').click();
    cy.get('[data-testid="last-30-days"]').click();
    cy.get('[data-testid="confirm-export"]').click();
    
    cy.get('[data-testid="success-message"]').should('contain', 'Report exported successfully');
  });
});