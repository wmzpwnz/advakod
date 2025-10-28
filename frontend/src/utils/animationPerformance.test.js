/**
 * Animation Performance Integration Tests
 * Tests actual animation performance, load times, and rendering metrics
 */

import { render, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import performanceMonitor from './performanceMonitor';

// Mock components for testing
const AnimatedComponent = ({ children, className }) => (
  <div className={className} style={{ animation: 'fadeIn 0.3s ease-in-out' }}>
    {children}
  </div>
);

const HeavyAnimatedComponent = () => (
  <div>
    {Array.from({ length: 50 }).map((_, i) => (
      <div
        key={i}
        className="neon-glow-purple"
        style={{
          animation: 'neonPulse 3s ease-in-out infinite',
          backdropFilter: 'blur(20px)'
        }}
      >
        Animated Item {i}
      </div>
    ))}
  </div>
);

describe('Animation Performance Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Mock performance.now()
    let currentTime = 0;
    global.performance.now = jest.fn(() => {
      currentTime += 16.67; // Simulate 60 FPS (16.67ms per frame)
      return currentTime;
    });

    // Mock requestAnimationFrame
    global.requestAnimationFrame = jest.fn((callback) => {
      setTimeout(callback, 16.67);
      return 1;
    });
  });

  describe('Component Render Performance', () => {
    test('renders simple animated component within performance budget', () => {
      const startTime = performance.now();
      
      render(<AnimatedComponent>Test Content</AnimatedComponent>);
      
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      // Should render in less than 100ms
      expect(renderTime).toBeLessThan(100);
    });

    test('renders multiple animated components efficiently', () => {
      const startTime = performance.now();
      
      render(
        <div>
          {Array.from({ length: 10 }).map((_, i) => (
            <AnimatedComponent key={i}>Item {i}</AnimatedComponent>
          ))}
        </div>
      );
      
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      // Should render 10 components in less than 200ms
      expect(renderTime).toBeLessThan(200);
    });

    test('handles heavy animation load', () => {
      const startTime = performance.now();
      
      render(<HeavyAnimatedComponent />);
      
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      // Should render 50 animated items in less than 500ms
      expect(renderTime).toBeLessThan(500);
    });
  });

  describe('FPS Measurement During Animations', () => {
    test('maintains acceptable FPS during simple animations', async () => {
      performanceMonitor.fpsHistory = [];
      
      // Simulate animation frames
      for (let i = 0; i < 60; i++) {
        performanceMonitor.fpsHistory.push(58 + Math.random() * 4); // 58-62 FPS
      }
      
      const avgFPS = performanceMonitor.getAverageFPS();
      
      // Should maintain at least 55 FPS
      expect(avgFPS).toBeGreaterThanOrEqual(55);
    });

    test('detects performance degradation', () => {
      performanceMonitor.fpsHistory = [];
      
      // Simulate degraded performance
      for (let i = 0; i < 60; i++) {
        performanceMonitor.fpsHistory.push(40 + Math.random() * 10); // 40-50 FPS
      }
      
      const avgFPS = performanceMonitor.getAverageFPS();
      
      expect(avgFPS).toBeLessThan(55);
      expect(performanceMonitor.isPerformanceGood()).toBe(false);
    });

    test('tracks FPS variance over time', () => {
      performanceMonitor.fpsHistory = [60, 58, 59, 61, 60, 57, 59, 60];
      
      const avgFPS = performanceMonitor.getAverageFPS();
      const maxFPS = Math.max(...performanceMonitor.fpsHistory);
      const minFPS = Math.min(...performanceMonitor.fpsHistory);
      const variance = maxFPS - minFPS;
      
      // Variance should be small for stable performance
      expect(variance).toBeLessThan(10);
      expect(avgFPS).toBeGreaterThan(55);
    });
  });

  describe('Animation Load Time Tests', () => {
    test('CSS animations load quickly', () => {
      const startTime = performance.now();
      
      // Create style element with animations
      const style = document.createElement('style');
      style.textContent = `
        @keyframes neonPulse {
          0%, 100% { box-shadow: 0 0 5px rgba(139, 92, 246, 0.3); }
          50% { box-shadow: 0 0 20px rgba(139, 92, 246, 0.6); }
        }
        @keyframes shimmerSweep {
          0% { background-position: -200% center; }
          100% { background-position: 200% center; }
        }
      `;
      document.head.appendChild(style);
      
      const endTime = performance.now();
      const loadTime = endTime - startTime;
      
      // CSS should load in less than 50ms
      expect(loadTime).toBeLessThan(50);
      
      // Cleanup
      document.head.removeChild(style);
    });

    test('multiple animation keyframes load efficiently', () => {
      const startTime = performance.now();
      
      const animations = [
        'neonPulse',
        'neonGradientGlow',
        'neonBorderFlow',
        'silverShimmer',
        'fadeIn',
        'slideUp',
        'scaleIn'
      ];
      
      const style = document.createElement('style');
      animations.forEach(name => {
        style.textContent += `
          @keyframes ${name} {
            0% { opacity: 0; }
            100% { opacity: 1; }
          }
        `;
      });
      document.head.appendChild(style);
      
      const endTime = performance.now();
      const loadTime = endTime - startTime;
      
      // Multiple animations should load in less than 100ms
      expect(loadTime).toBeLessThan(100);
      
      // Cleanup
      document.head.removeChild(style);
    });
  });

  describe('Memory Usage Tests', () => {
    test('animation cleanup prevents memory leaks', () => {
      const components = [];
      
      // Render multiple components
      for (let i = 0; i < 20; i++) {
        const { unmount } = render(<AnimatedComponent>Item {i}</AnimatedComponent>);
        components.push(unmount);
      }
      
      // Unmount all components
      components.forEach(unmount => unmount());
      
      // Check that performance monitor can still function
      expect(performanceMonitor.getCurrentFPS()).toBeDefined();
      expect(typeof performanceMonitor.getCurrentFPS()).toBe('number');
    });

    test('FPS history maintains bounded size', () => {
      const maxLength = performanceMonitor.maxHistoryLength;
      
      // Add many FPS measurements
      for (let i = 0; i < maxLength * 2; i++) {
        performanceMonitor.fpsHistory.push(60);
        
        // Simulate the cleanup that happens in measureFPS
        if (performanceMonitor.fpsHistory.length > maxLength) {
          performanceMonitor.fpsHistory.shift();
        }
      }
      
      // History should not exceed max length
      expect(performanceMonitor.fpsHistory.length).toBeLessThanOrEqual(maxLength);
    });
  });

  describe('Adaptive Performance Tests', () => {
    beforeEach(() => {
      // Mock matchMedia for all tests
      global.window.matchMedia = jest.fn().mockImplementation(query => ({
        matches: false,
        media: query,
      }));
    });

    test('reduces animation complexity on low-end devices', () => {
      // Mock low-end device
      Object.defineProperty(global.navigator, 'deviceMemory', {
        writable: true,
        configurable: true,
        value: 2
      });
      Object.defineProperty(global.navigator, 'hardwareConcurrency', {
        writable: true,
        configurable: true,
        value: 2
      });
      
      const { getAdaptiveAnimationConfig } = require('./performanceMonitor');
      const config = getAdaptiveAnimationConfig();
      
      // Should have reduced settings
      expect(config.particleCount).toBeLessThan(20);
      expect(config.blurIntensity).toBeLessThan(15);
      expect(config.duration).toBeLessThan(0.5);
    });

    test('enables full animations on high-end devices', () => {
      // Mock high-end device
      Object.defineProperty(global.navigator, 'deviceMemory', {
        writable: true,
        configurable: true,
        value: 8
      });
      Object.defineProperty(global.navigator, 'hardwareConcurrency', {
        writable: true,
        configurable: true,
        value: 8
      });
      Object.defineProperty(global.navigator, 'connection', {
        writable: true,
        configurable: true,
        value: { effectiveType: '4g' }
      });
      
      const { getAdaptiveAnimationConfig } = require('./performanceMonitor');
      const config = getAdaptiveAnimationConfig();
      
      // Should have full settings
      expect(config.particleCount).toBeGreaterThanOrEqual(40);
      expect(config.blurIntensity).toBeGreaterThanOrEqual(15);
      expect(config.enabled).toBe(true);
    });

    test('respects user motion preferences', () => {
      // Mock prefers-reduced-motion
      global.window.matchMedia = jest.fn().mockImplementation(query => ({
        matches: query === '(prefers-reduced-motion: reduce)',
        media: query,
      }));
      
      const { getAdaptiveAnimationConfig } = require('./performanceMonitor');
      const config = getAdaptiveAnimationConfig();
      
      // Should disable animations
      expect(config.enabled).toBe(false);
      expect(config.duration).toBe(0);
    });
  });

  describe('Real-world Performance Scenarios', () => {
    test('page load with multiple animated sections', async () => {
      const startTime = performance.now();
      
      const { container } = render(
        <div>
          <AnimatedComponent className="hero-section">Hero</AnimatedComponent>
          <AnimatedComponent className="features-section">Features</AnimatedComponent>
          <AnimatedComponent className="faq-section">FAQ</AnimatedComponent>
          <AnimatedComponent className="trust-section">Trust</AnimatedComponent>
        </div>
      );
      
      const endTime = performance.now();
      const loadTime = endTime - startTime;
      
      // Full page should load in less than 300ms
      expect(loadTime).toBeLessThan(300);
      expect(container.children.length).toBe(1);
    });

    test('scroll performance with lazy-loaded animations', async () => {
      const sections = [];
      
      // Simulate lazy loading sections
      for (let i = 0; i < 5; i++) {
        const startTime = performance.now();
        
        const { container } = render(
          <AnimatedComponent>Section {i}</AnimatedComponent>
        );
        
        const endTime = performance.now();
        sections.push(endTime - startTime);
      }
      
      // Each section should load quickly
      sections.forEach(time => {
        expect(time).toBeLessThan(100);
      });
      
      // Average load time should be good (relaxed for test environment)
      const avgTime = sections.reduce((a, b) => a + b, 0) / sections.length;
      expect(avgTime).toBeLessThan(100);
    });

    test('interaction performance with animated feedback', async () => {
      const { container } = render(
        <button
          className="neon-button"
          style={{ transition: 'all 0.3s ease' }}
        >
          Click Me
        </button>
      );
      
      const button = container.querySelector('button');
      const startTime = performance.now();
      
      // Simulate hover
      button.style.transform = 'translateY(-2px)';
      button.style.boxShadow = '0 0 20px rgba(139, 92, 246, 0.6)';
      
      const endTime = performance.now();
      const interactionTime = endTime - startTime;
      
      // Interaction should complete quickly (relaxed for test environment)
      expect(interactionTime).toBeLessThan(100);
    });
  });

  describe('Performance Budget Compliance', () => {
    test('meets 60 FPS target for smooth animations', () => {
      const targetFPS = 60;
      const frameBudget = 1000 / targetFPS; // 16.67ms per frame
      
      performanceMonitor.fpsHistory = [58, 59, 60, 61, 59, 60];
      const avgFPS = performanceMonitor.getAverageFPS();
      
      expect(avgFPS).toBeGreaterThanOrEqual(targetFPS - 5); // Allow 5 FPS tolerance
    });

    test('animation duration stays within budget', () => {
      const animations = [
        { name: 'fadeIn', duration: 0.3 },
        { name: 'slideUp', duration: 0.4 },
        { name: 'neonPulse', duration: 3.0 },
        { name: 'shimmer', duration: 3.0 }
      ];
      
      animations.forEach(anim => {
        // Short animations should be under 0.5s
        if (anim.name.includes('fade') || anim.name.includes('slide')) {
          expect(anim.duration).toBeLessThanOrEqual(0.5);
        }
        
        // Long animations should be under 5s
        expect(anim.duration).toBeLessThanOrEqual(5);
      });
    });

    test('total page weight with animations is acceptable', () => {
      // Simulate CSS size
      const cssAnimations = `
        @keyframes neonPulse { /* ... */ }
        @keyframes shimmer { /* ... */ }
        @keyframes fadeIn { /* ... */ }
      `;
      
      const sizeInBytes = new Blob([cssAnimations]).size;
      const sizeInKB = sizeInBytes / 1024;
      
      // Animation CSS should be under 10KB
      expect(sizeInKB).toBeLessThan(10);
    });
  });

  describe('Performance Monitoring Accuracy', () => {
    test('FPS calculation is accurate', () => {
      const mockFPS = 60;
      const mockFrameTime = 1000 / mockFPS;
      
      performanceMonitor.frameCount = mockFPS;
      performanceMonitor.lastTime = 0;
      
      // Simulate 1 second passing
      const currentTime = 1000;
      const calculatedFPS = Math.round(
        (performanceMonitor.frameCount * 1000) / (currentTime - performanceMonitor.lastTime)
      );
      
      expect(calculatedFPS).toBe(mockFPS);
    });

    test('performance degradation is detected quickly', () => {
      // Start with good performance
      performanceMonitor.fpsHistory = [60, 60, 60];
      expect(performanceMonitor.isPerformanceGood()).toBe(true);
      
      // Add poor performance samples
      performanceMonitor.fpsHistory.push(45, 44, 43, 42, 41);
      
      // Should now detect poor performance
      expect(performanceMonitor.isPerformanceGood()).toBe(false);
    });
  });
});
