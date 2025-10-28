describe('Marketing Tools Integration', () => {
  beforeEach(() => {
    cy.loginAsAdmin();
    cy.navigateToModule('marketing');
  });

  it('should display marketing dashboard with key metrics', () => {
    cy.get('[data-testid="marketing-dashboard"]').should('be.visible');
    cy.get('[data-testid="sales-funnel"]').should('be.visible');
    cy.get('[data-testid="conversion-metrics"]').should('be.visible');
    cy.get('[data-testid="traffic-sources"]').should('be.visible');
  });

  it('should create and manage promo codes', () => {
    cy.get('[data-testid="promo-codes-tab"]').click();
    cy.get('[data-testid="create-promo-button"]').click();
    
    // Fill promo code form
    cy.get('[data-testid="promo-code-input"]').type('TEST2024');
    cy.get('[data-testid="discount-type-select"]').select('percentage');
    cy.get('[data-testid="discount-value-input"]').type('20');
    cy.get('[data-testid="usage-limit-input"]').type('100');
    
    // Set validity dates
    cy.get('[data-testid="valid-from-input"]').type('2024-01-01');
    cy.get('[data-testid="valid-to-input"]').type('2024-12-31');
    
    cy.get('[data-testid="save-promo-button"]').click();
    
    // Verify promo code was created
    cy.get('[data-testid="promo-codes-table"]').should('contain', 'TEST2024');
    cy.get('[data-testid="success-message"]').should('contain', 'Promo code created');
  });

  it('should track promo code usage analytics', () => {
    // Create a test promo code first
    cy.createTestPromoCode('ANALYTICS2024', 15).then((response) => {
      const promoId = response.body.id;
      
      cy.reload();
      cy.get('[data-testid="promo-codes-tab"]').click();
      
      // View analytics for the promo code
      cy.get(`[data-testid="promo-${promoId}"]`).within(() => {
        cy.get('[data-testid="view-analytics-button"]').click();
      });
      
      cy.get('[data-testid="promo-analytics-modal"]').should('be.visible');
      cy.get('[data-testid="usage-chart"]').should('be.visible');
      cy.get('[data-testid="conversion-stats"]').should('be.visible');
    });
  });

  it('should display traffic analytics with source breakdown', () => {
    cy.get('[data-testid="traffic-analytics-tab"]').click();
    
    cy.get('[data-testid="traffic-sources-chart"]').should('be.visible');
    cy.get('[data-testid="utm-parameters-table"]').should('be.visible');
    cy.get('[data-testid="channel-performance"]').should('be.visible');
    
    // Test date range filtering
    cy.get('[data-testid="date-range-select"]').select('last-30-days');
    cy.get('[data-testid="traffic-sources-chart"]').should('be.visible');
  });

  it('should create and manage A/B tests', () => {
    cy.get('[data-testid="ab-tests-tab"]').click();
    cy.get('[data-testid="create-ab-test-button"]').click();
    
    // Fill A/B test form
    cy.get('[data-testid="test-name-input"]').type('Button Color Test');
    cy.get('[data-testid="test-description-input"]').type('Testing red vs blue button colors');
    cy.get('[data-testid="test-hypothesis-input"]').type('Red buttons will convert better');
    
    // Add variants
    cy.get('[data-testid="add-variant-button"]').click();
    cy.get('[data-testid="variant-name-input"]').type('Red Button');
    cy.get('[data-testid="variant-description-input"]').type('Red colored button');
    cy.get('[data-testid="traffic-percentage-input"]').type('50');
    
    cy.get('[data-testid="save-ab-test-button"]').click();
    
    // Verify A/B test was created
    cy.get('[data-testid="ab-tests-table"]').should('contain', 'Button Color Test');
    cy.get('[data-testid="success-message"]').should('contain', 'A/B test created');
  });

  it('should start and monitor A/B test', () => {
    // Find a test and start it
    cy.get('[data-testid="ab-test-row"]').first().within(() => {
      cy.get('[data-testid="start-test-button"]').click();
    });
    
    cy.get('[data-testid="confirm-start-test"]').click();
    
    // Verify test is running
    cy.get('[data-testid="ab-test-row"]').first().should('contain', 'Running');
    
    // Check test statistics
    cy.get('[data-testid="ab-test-row"]').first().within(() => {
      cy.get('[data-testid="view-stats-button"]').click();
    });
    
    cy.get('[data-testid="test-statistics-modal"]').should('be.visible');
    cy.get('[data-testid="participant-count"]').should('be.visible');
    cy.get('[data-testid="conversion-rates"]').should('be.visible');
  });

  it('should analyze A/B test results', () => {
    // Find a completed test
    cy.get('[data-testid="ab-test-row"]').contains('Completed').within(() => {
      cy.get('[data-testid="analyze-button"]').click();
    });
    
    cy.get('[data-testid="analysis-results"]').should('be.visible');
    cy.get('[data-testid="statistical-significance"]').should('be.visible');
    cy.get('[data-testid="confidence-interval"]').should('be.visible');
    cy.get('[data-testid="recommendations"]').should('be.visible');
  });

  it('should export marketing reports', () => {
    cy.get('[data-testid="reports-tab"]').click();
    cy.get('[data-testid="generate-report-button"]').click();
    
    // Select report parameters
    cy.get('[data-testid="report-type-select"]').select('conversion-funnel');
    cy.get('[data-testid="date-range-select"]').select('last-quarter');
    cy.get('[data-testid="format-select"]').select('pdf');
    
    cy.get('[data-testid="generate-button"]').click();
    
    cy.get('[data-testid="success-message"]').should('contain', 'Report generated');
    cy.get('[data-testid="download-link"]').should('be.visible');
  });

  it('should show sales funnel visualization', () => {
    cy.get('[data-testid="sales-funnel"]').should('be.visible');
    
    // Check funnel stages
    cy.get('[data-testid="funnel-stage-visitors"]').should('be.visible');
    cy.get('[data-testid="funnel-stage-signups"]').should('be.visible');
    cy.get('[data-testid="funnel-stage-trials"]').should('be.visible');
    cy.get('[data-testid="funnel-stage-conversions"]').should('be.visible');
    
    // Check conversion rates
    cy.get('[data-testid="conversion-rate"]').should('contain', '%');
  });

  it('should handle campaign tracking', () => {
    cy.get('[data-testid="campaigns-tab"]').click();
    cy.get('[data-testid="create-campaign-button"]').click();
    
    // Fill campaign form
    cy.get('[data-testid="campaign-name-input"]').type('Q4 2024 Campaign');
    cy.get('[data-testid="campaign-source-input"]').type('google');
    cy.get('[data-testid="campaign-medium-input"]').type('cpc');
    cy.get('[data-testid="campaign-budget-input"]').type('5000');
    
    cy.get('[data-testid="save-campaign-button"]').click();
    
    // Verify campaign tracking
    cy.get('[data-testid="campaigns-table"]').should('contain', 'Q4 2024 Campaign');
    cy.get('[data-testid="utm-generator"]').should('be.visible');
  });
});