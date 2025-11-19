const puppeteer = require('puppeteer');
const lighthouse = require('lighthouse');
const fs = require('fs');
const path = require('path');

class PerformanceTestRunner {
  constructor() {
    this.browser = null;
    this.results = {
      lighthouse: {},
      customMetrics: {},
      timestamp: new Date().toISOString()
    };
  }

  async initialize() {
    this.browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-dev-shm-usage']
    });
  }

  async runLighthouseTests() {
    console.log('Running Lighthouse performance tests...');
    
    const urls = [
      'http://localhost:3000/admin',
      'http://localhost:3000/admin/users',
      'http://localhost:3000/admin/moderation',
      'http://localhost:3000/admin/marketing'
    ];

    for (const url of urls) {
      try {
        console.log(`Testing ${url}...`);
        
        const { lhr } = await lighthouse(url, {
          port: 9222,
          onlyCategories: ['performance'],
          settings: {
            onlyAudits: [
              'first-contentful-paint',
              'largest-contentful-paint',
              'first-meaningful-paint',
              'speed-index',
              'interactive',
              'total-blocking-time',
              'cumulative-layout-shift'
            ]
          }
        });

        const pageName = url.split('/').pop() || 'admin';
        this.results.lighthouse[pageName] = {
          score: lhr.categories.performance.score * 100,
          metrics: {
            fcp: lhr.audits['first-contentful-paint'].numericValue,
            lcp: lhr.audits['largest-contentful-paint'].numericValue,
            fmp: lhr.audits['first-meaningful-paint'].numericValue,
            si: lhr.audits['speed-index'].numericValue,
            tti: lhr.audits['interactive'].numericValue,
            tbt: lhr.audits['total-blocking-time'].numericValue,
            cls: lhr.audits['cumulative-layout-shift'].numericValue
          }
        };

        console.log(`${pageName} Performance Score: ${this.results.lighthouse[pageName].score}`);
      } catch (error) {
        console.error(`Error testing ${url}:`, error.message);
      }
    }
  }

  async runCustomPerformanceTests() {
    console.log('Running custom performance tests...');
    
    const page = await this.browser.newPage();
    
    // Test admin login performance
    await this.testLoginPerformance(page);
    
    // Test dashboard load performance
    await this.testDashboardPerformance(page);
    
    // Test large dataset rendering
    await this.testLargeDatasetPerformance(page);
    
    // Test real-time updates performance
    await this.testRealTimePerformance(page);
    
    await page.close();
  }

  async testLoginPerformance(page) {
    console.log('Testing login performance...');
    
    const startTime = Date.now();
    
    await page.goto('http://localhost:3000/admin/login');
    await page.waitForSelector('[data-testid="login-form"]');
    
    await page.type('[data-testid="email-input"]', 'admin@test.com');
    await page.type('[data-testid="password-input"]', 'testpassword123');
    
    const loginStartTime = Date.now();
    await page.click('[data-testid="login-button"]');
    await page.waitForSelector('[data-testid="admin-dashboard"]');
    const loginEndTime = Date.now();
    
    this.results.customMetrics.login = {
      pageLoadTime: loginStartTime - startTime,
      authenticationTime: loginEndTime - loginStartTime,
      totalTime: loginEndTime - startTime
    };
    
    console.log(`Login completed in ${loginEndTime - startTime}ms`);
  }

  async testDashboardPerformance(page) {
    console.log('Testing dashboard performance...');
    
    const startTime = Date.now();
    
    // Measure dashboard rendering time
    await page.evaluate(() => {
      window.dashboardStartTime = performance.now();
    });
    
    await page.goto('http://localhost:3000/admin');
    await page.waitForSelector('[data-testid="admin-dashboard"]');
    
    const renderTime = await page.evaluate(() => {
      return performance.now() - window.dashboardStartTime;
    });
    
    // Measure widget loading times
    const widgets = await page.$$('[data-testid^="widget-"]');
    const widgetLoadTimes = [];
    
    for (const widget of widgets) {
      const widgetStartTime = Date.now();
      await widget.waitForSelector('.widget-content', { timeout: 5000 });
      widgetLoadTimes.push(Date.now() - widgetStartTime);
    }
    
    this.results.customMetrics.dashboard = {
      renderTime,
      widgetCount: widgets.length,
      averageWidgetLoadTime: widgetLoadTimes.reduce((a, b) => a + b, 0) / widgetLoadTimes.length,
      totalLoadTime: Date.now() - startTime
    };
    
    console.log(`Dashboard loaded in ${Date.now() - startTime}ms`);
  }

  async testLargeDatasetPerformance(page) {
    console.log('Testing large dataset performance...');
    
    await page.goto('http://localhost:3000/admin/users');
    
    // Mock large dataset response
    await page.setRequestInterception(true);
    page.on('request', (request) => {
      if (request.url().includes('/api/v1/admin/users')) {
        request.respond({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            users: Array.from({ length: 1000 }, (_, i) => ({
              id: i + 1,
              email: `user${i + 1}@example.com`,
              name: `User ${i + 1}`,
              role: 'user',
              created_at: new Date().toISOString()
            })),
            total: 1000
          })
        });
      } else {
        request.continue();
      }
    });
    
    const startTime = Date.now();
    await page.reload();
    await page.waitForSelector('[data-testid="users-table"]');
    
    // Wait for all rows to render
    await page.waitForFunction(() => {
      const rows = document.querySelectorAll('[data-testid="users-table"] tbody tr');
      return rows.length >= 100; // First page should have at least 100 rows
    });
    
    const renderTime = Date.now() - startTime;
    
    // Test scrolling performance
    const scrollStartTime = Date.now();
    await page.evaluate(() => {
      const table = document.querySelector('[data-testid="users-table"]');
      table.scrollTop = table.scrollHeight;
    });
    
    await page.waitForTimeout(1000); // Wait for scroll to complete
    const scrollTime = Date.now() - scrollStartTime;
    
    this.results.customMetrics.largeDataset = {
      renderTime,
      scrollTime,
      rowCount: await page.$$eval('[data-testid="users-table"] tbody tr', rows => rows.length)
    };
    
    console.log(`Large dataset rendered in ${renderTime}ms`);
  }

  async testRealTimePerformance(page) {
    console.log('Testing real-time updates performance...');
    
    await page.goto('http://localhost:3000/admin');
    
    // Mock WebSocket for testing
    await page.evaluateOnNewDocument(() => {
      window.WebSocket = class MockWebSocket {
        constructor(url) {
          this.url = url;
          this.readyState = 1;
          setTimeout(() => this.onopen && this.onopen(), 100);
        }
        send() {}
        close() {}
      };
    });
    
    await page.reload();
    await page.waitForSelector('[data-testid="admin-dashboard"]');
    
    // Simulate rapid updates
    const updateCount = 100;
    const startTime = Date.now();
    
    for (let i = 0; i < updateCount; i++) {
      await page.evaluate((i) => {
        if (window.adminWebSocket && window.adminWebSocket.onmessage) {
          window.adminWebSocket.onmessage({
            data: JSON.stringify({
              type: 'dashboard_update',
              data: { active_users: 100 + i }
            })
          });
        }
      }, i);
      
      if (i % 10 === 0) {
        await page.waitForTimeout(10); // Small delay every 10 updates
      }
    }
    
    const updateTime = Date.now() - startTime;
    
    // Verify final state
    const finalValue = await page.$eval('[data-testid="active-users-count"]', el => el.textContent);
    
    this.results.customMetrics.realTimeUpdates = {
      updateCount,
      totalTime: updateTime,
      averageUpdateTime: updateTime / updateCount,
      finalValue: parseInt(finalValue) || 0
    };
    
    console.log(`${updateCount} real-time updates processed in ${updateTime}ms`);
  }

  async generateReport() {
    console.log('Generating performance report...');
    
    const reportPath = path.join(__dirname, '../cypress/reports/performance-report.json');
    const reportDir = path.dirname(reportPath);
    
    if (!fs.existsSync(reportDir)) {
      fs.mkdirSync(reportDir, { recursive: true });
    }
    
    fs.writeFileSync(reportPath, JSON.stringify(this.results, null, 2));
    
    // Generate HTML report
    const htmlReport = this.generateHTMLReport();
    const htmlPath = path.join(__dirname, '../cypress/reports/performance-report.html');
    fs.writeFileSync(htmlPath, htmlReport);
    
    console.log(`Performance report generated: ${htmlPath}`);
    
    // Check if performance meets requirements
    this.validatePerformanceRequirements();
  }

  generateHTMLReport() {
    return `
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel Performance Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .metric { margin: 10px 0; padding: 10px; border-left: 4px solid #007cba; }
        .good { border-color: #28a745; }
        .warning { border-color: #ffc107; }
        .error { border-color: #dc3545; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; }
    </style>
</head>
<body>
    <h1>Admin Panel Performance Report</h1>
    <p>Generated: ${this.results.timestamp}</p>
    
    <h2>Lighthouse Scores</h2>
    <table>
        <tr><th>Page</th><th>Score</th><th>FCP</th><th>LCP</th><th>TTI</th><th>CLS</th></tr>
        ${Object.entries(this.results.lighthouse).map(([page, data]) => `
        <tr>
            <td>${page}</td>
            <td class="${data.score >= 90 ? 'good' : data.score >= 70 ? 'warning' : 'error'}">${data.score.toFixed(1)}</td>
            <td>${(data.metrics.fcp / 1000).toFixed(2)}s</td>
            <td>${(data.metrics.lcp / 1000).toFixed(2)}s</td>
            <td>${(data.metrics.tti / 1000).toFixed(2)}s</td>
            <td>${data.metrics.cls.toFixed(3)}</td>
        </tr>
        `).join('')}
    </table>
    
    <h2>Custom Metrics</h2>
    ${Object.entries(this.results.customMetrics).map(([test, data]) => `
        <div class="metric">
            <h3>${test}</h3>
            <pre>${JSON.stringify(data, null, 2)}</pre>
        </div>
    `).join('')}
</body>
</html>
    `;
  }

  validatePerformanceRequirements() {
    console.log('Validating performance requirements...');
    
    const failures = [];
    
    // Check Lighthouse scores
    Object.entries(this.results.lighthouse).forEach(([page, data]) => {
      if (data.score < 70) {
        failures.push(`${page} Lighthouse score (${data.score}) below threshold (70)`);
      }
      if (data.metrics.lcp > 4000) {
        failures.push(`${page} LCP (${data.metrics.lcp}ms) above threshold (4000ms)`);
      }
      if (data.metrics.cls > 0.25) {
        failures.push(`${page} CLS (${data.metrics.cls}) above threshold (0.25)`);
      }
    });
    
    // Check custom metrics
    if (this.results.customMetrics.login?.totalTime > 5000) {
      failures.push(`Login time (${this.results.customMetrics.login.totalTime}ms) above threshold (5000ms)`);
    }
    
    if (this.results.customMetrics.dashboard?.totalLoadTime > 3000) {
      failures.push(`Dashboard load time (${this.results.customMetrics.dashboard.totalLoadTime}ms) above threshold (3000ms)`);
    }
    
    if (this.results.customMetrics.largeDataset?.renderTime > 2000) {
      failures.push(`Large dataset render time (${this.results.customMetrics.largeDataset.renderTime}ms) above threshold (2000ms)`);
    }
    
    if (failures.length > 0) {
      console.error('Performance requirements not met:');
      failures.forEach(failure => console.error(`- ${failure}`));
      process.exit(1);
    } else {
      console.log('All performance requirements met!');
    }
  }

  async cleanup() {
    if (this.browser) {
      await this.browser.close();
    }
  }
}

async function runPerformanceTests() {
  const runner = new PerformanceTestRunner();
  
  try {
    await runner.initialize();
    await runner.runLighthouseTests();
    await runner.runCustomPerformanceTests();
    await runner.generateReport();
  } catch (error) {
    console.error('Performance tests failed:', error);
    process.exit(1);
  } finally {
    await runner.cleanup();
  }
}

if (require.main === module) {
  runPerformanceTests();
}

module.exports = PerformanceTestRunner;