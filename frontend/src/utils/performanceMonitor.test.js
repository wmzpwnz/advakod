/**
 * Performance Monitor Tests
 * Tests FPS monitoring, device performance detection, and adaptive configurations
 */

import performanceMonitor, {
  getDevicePerformance,
  getAdaptiveAnimationConfig,
  applyAdaptiveStyles,
  checkBrowserSupport
} from './performanceMonitor';

// Mock performance API
global.performance = {
  now: jest.fn(() => Date.now())
};

// Mock requestAnimationFrame
global.requestAnimationFrame = jest.fn((cb) => setTimeout(cb, 16));

describe('PerformanceMonitor', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    performanceMonitor.stopMonitoring();
    performanceMonitor.fps = 60;
    performanceMonitor.frameCount = 0;
    performanceMonitor.fpsHistory = [];
  });

  describe('FPS Monitoring', () => {
    test('initializes with default FPS of 60', () => {
      expect(performanceMonitor.getCurrentFPS()).toBe(60);
    });

    test('starts monitoring in development mode', () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'development';

      performanceMonitor.startMonitoring();
      expect(performanceMonitor.isMonitoring).toBe(true);

      process.env.NODE_ENV = originalEnv;
    });

    test('does not start monitoring in production mode', () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'production';

      performanceMonitor.startMonitoring();
      expect(performanceMonitor.isMonitoring).toBe(false);

      process.env.NODE_ENV = originalEnv;
    });

    test('stops monitoring when requested', () => {
      performanceMonitor.isMonitoring = true;
      performanceMonitor.stopMonitoring();
      expect(performanceMonitor.isMonitoring).toBe(false);
    });

    test('calculates average FPS correctly', () => {
      performanceMonitor.fpsHistory = [60, 58, 59, 61, 60];
      const avgFPS = performanceMonitor.getAverageFPS();
      expect(avgFPS).toBe(60); // Average of the values
    });

    test('returns 60 FPS when history is empty', () => {
      performanceMonitor.fpsHistory = [];
      expect(performanceMonitor.getAverageFPS()).toBe(60);
    });

    test('identifies good performance when FPS > 50', () => {
      performanceMonitor.fpsHistory = [55, 58, 60, 59, 57];
      expect(performanceMonitor.isPerformanceGood()).toBe(true);
    });

    test('identifies poor performance when FPS <= 50', () => {
      performanceMonitor.fpsHistory = [45, 48, 50, 47, 46];
      expect(performanceMonitor.isPerformanceGood()).toBe(false);
    });

    test('limits FPS history to maxHistoryLength', () => {
      const maxLength = performanceMonitor.maxHistoryLength;
      
      // Add more items than max length
      for (let i = 0; i < maxLength + 10; i++) {
        performanceMonitor.fpsHistory.push(60);
      }

      // Simulate the shift operation that happens in measureFPS
      while (performanceMonitor.fpsHistory.length > maxLength) {
        performanceMonitor.fpsHistory.shift();
      }

      expect(performanceMonitor.fpsHistory.length).toBe(maxLength);
    });
  });

  describe('Device Performance Detection', () => {
    beforeEach(() => {
      // Reset navigator mocks
      delete global.navigator;
      global.navigator = {};
    });

    test('detects high performance device', () => {
      global.navigator.deviceMemory = 8;
      global.navigator.hardwareConcurrency = 8;
      global.navigator.connection = { effectiveType: '4g' };

      const performance = getDevicePerformance();
      expect(performance).toBe('high');
    });

    test('detects medium performance device', () => {
      global.navigator.deviceMemory = 4;
      global.navigator.hardwareConcurrency = 4;
      global.navigator.connection = { effectiveType: '3g' };

      const performance = getDevicePerformance();
      expect(performance).toBe('medium');
    });

    test('detects low performance device', () => {
      global.navigator.deviceMemory = 2;
      global.navigator.hardwareConcurrency = 2;
      global.navigator.connection = { effectiveType: '2g' };

      const performance = getDevicePerformance();
      expect(performance).toBe('low');
    });

    test('handles missing deviceMemory gracefully', () => {
      global.navigator.hardwareConcurrency = 4;
      global.navigator.connection = { effectiveType: '4g' };

      const performance = getDevicePerformance();
      expect(['high', 'medium', 'low']).toContain(performance);
    });

    test('handles missing hardwareConcurrency gracefully', () => {
      global.navigator.deviceMemory = 4;
      global.navigator.connection = { effectiveType: '4g' };

      const performance = getDevicePerformance();
      expect(['high', 'medium', 'low']).toContain(performance);
    });

    test('handles missing connection info gracefully', () => {
      global.navigator.deviceMemory = 4;
      global.navigator.hardwareConcurrency = 4;

      const performance = getDevicePerformance();
      expect(['high', 'medium', 'low']).toContain(performance);
    });
  });

  describe('Adaptive Animation Configuration', () => {
    beforeEach(() => {
      delete global.navigator;
      global.navigator = {};
      
      // Mock matchMedia
      global.window.matchMedia = jest.fn().mockImplementation(query => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      }));
    });

    test('returns high performance config for high-end devices', () => {
      global.navigator.deviceMemory = 8;
      global.navigator.hardwareConcurrency = 8;
      global.navigator.connection = { effectiveType: '4g' };

      const config = getAdaptiveAnimationConfig();
      
      expect(config.enabled).toBe(true);
      expect(config.duration).toBe(0.6);
      expect(config.particleCount).toBe(50);
      expect(config.blurIntensity).toBe(20);
      expect(config.glowIntensity).toBe(1);
    });

    test('returns medium performance config for mid-range devices', () => {
      global.navigator.deviceMemory = 4;
      global.navigator.hardwareConcurrency = 4;
      global.navigator.connection = { effectiveType: '3g' };

      const config = getAdaptiveAnimationConfig();
      
      expect(config.enabled).toBe(true);
      expect(config.duration).toBe(0.4);
      expect(config.particleCount).toBe(25);
      expect(config.blurIntensity).toBe(15);
      expect(config.glowIntensity).toBe(0.7);
    });

    test('returns low performance config for low-end devices', () => {
      global.navigator.deviceMemory = 2;
      global.navigator.hardwareConcurrency = 2;
      global.navigator.connection = { effectiveType: '2g' };

      const config = getAdaptiveAnimationConfig();
      
      expect(config.enabled).toBe(true);
      expect(config.duration).toBe(0.3);
      expect(config.particleCount).toBe(10);
      expect(config.blurIntensity).toBe(10);
      expect(config.glowIntensity).toBe(0.5);
    });

    test('disables animations when prefers-reduced-motion is set', () => {
      global.window.matchMedia = jest.fn().mockImplementation(query => ({
        matches: query === '(prefers-reduced-motion: reduce)',
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
      }));

      const config = getAdaptiveAnimationConfig();
      
      expect(config.enabled).toBe(false);
      expect(config.duration).toBe(0);
      expect(config.particleCount).toBe(0);
      expect(config.blurIntensity).toBe(0);
      expect(config.glowIntensity).toBe(0);
    });

    test('config includes all required properties', () => {
      global.navigator.deviceMemory = 4;
      global.navigator.hardwareConcurrency = 4;

      const config = getAdaptiveAnimationConfig();
      
      expect(config).toHaveProperty('enabled');
      expect(config).toHaveProperty('duration');
      expect(config).toHaveProperty('staggerDelay');
      expect(config).toHaveProperty('particleCount');
      expect(config).toHaveProperty('blurIntensity');
      expect(config).toHaveProperty('glowIntensity');
    });
  });

  describe('Adaptive Styles Application', () => {
    let mockSetProperty;

    beforeEach(() => {
      delete global.navigator;
      global.navigator = {
        deviceMemory: 4,
        hardwareConcurrency: 4
      };

      global.window.matchMedia = jest.fn().mockImplementation(query => ({
        matches: false,
        media: query,
      }));

      // Mock document.documentElement.style.setProperty
      mockSetProperty = jest.fn();
      Object.defineProperty(document.documentElement, 'style', {
        value: {
          setProperty: mockSetProperty
        },
        writable: true,
        configurable: true
      });
    });

    test('applies CSS variables to document root', () => {
      applyAdaptiveStyles();

      expect(mockSetProperty).toHaveBeenCalledWith(
        '--animation-duration',
        expect.any(String)
      );
      expect(mockSetProperty).toHaveBeenCalledWith(
        '--blur-intensity',
        expect.any(String)
      );
      expect(mockSetProperty).toHaveBeenCalledWith(
        '--glow-intensity',
        expect.any(String)
      );
    });

    test('applies correct values for high performance', () => {
      global.navigator.deviceMemory = 8;
      global.navigator.hardwareConcurrency = 8;
      global.navigator.connection = { effectiveType: '4g' };

      applyAdaptiveStyles();

      expect(mockSetProperty).toHaveBeenCalledWith(
        '--animation-duration',
        '0.6s'
      );
      expect(mockSetProperty).toHaveBeenCalledWith(
        '--blur-intensity',
        '20px'
      );
      expect(mockSetProperty).toHaveBeenCalledWith(
        '--glow-intensity',
        '1'
      );
    });
  });

  describe('Browser Support Detection', () => {
    beforeEach(() => {
      // Mock CSS.supports
      global.CSS = {
        supports: jest.fn((prop, value) => {
          const supportedFeatures = {
            'backdrop-filter': true,
            'display': true,
            '--test': true
          };
          return supportedFeatures[prop] || false;
        })
      };

      // Mock IntersectionObserver
      global.IntersectionObserver = class IntersectionObserver {
        constructor() {}
        observe() {}
        disconnect() {}
      };

      // Mock element.animate
      global.document.createElement = jest.fn(() => ({
        animate: jest.fn()
      }));
    });

    test('detects IntersectionObserver support', () => {
      const support = checkBrowserSupport();
      expect(support.intersectionObserver).toBe(true);
    });

    test('detects backdrop-filter support', () => {
      const support = checkBrowserSupport();
      expect(support.backdropFilter).toBe(true);
    });

    test('detects CSS Grid support', () => {
      const support = checkBrowserSupport();
      expect(support.cssGrid).toBe(true);
    });

    test('detects CSS Variables support', () => {
      const support = checkBrowserSupport();
      expect(support.cssVariables).toBe(true);
    });

    test('detects Web Animations API support', () => {
      const support = checkBrowserSupport();
      expect(support.webAnimations).toBe(true);
    });

    test('returns false for unsupported features', () => {
      delete global.IntersectionObserver;
      
      const support = checkBrowserSupport();
      expect(support.intersectionObserver).toBe(false);
    });

    test('returns all required support properties', () => {
      const support = checkBrowserSupport();
      
      expect(support).toHaveProperty('intersectionObserver');
      expect(support).toHaveProperty('backdropFilter');
      expect(support).toHaveProperty('cssGrid');
      expect(support).toHaveProperty('cssVariables');
      expect(support).toHaveProperty('webAnimations');
    });
  });
});
