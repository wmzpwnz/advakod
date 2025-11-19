/**
 * Performance monitoring utilities for animations
 * Monitors FPS and provides adaptive animation intensity based on device capabilities
 */

class PerformanceMonitor {
  constructor() {
    this.fps = 60;
    this.frameCount = 0;
    this.lastTime = performance.now();
    this.isMonitoring = false;
    this.fpsHistory = [];
    this.maxHistoryLength = 60; // Keep last 60 FPS measurements
  }

  /**
   * Start monitoring FPS (development mode only)
   */
  startMonitoring() {
    if (process.env.NODE_ENV !== 'development') {
      return;
    }

    this.isMonitoring = true;
    this.measureFPS();
  }

  /**
   * Stop monitoring FPS
   */
  stopMonitoring() {
    this.isMonitoring = false;
  }

  /**
   * Measure FPS using requestAnimationFrame
   */
  measureFPS() {
    if (!this.isMonitoring) return;

    const currentTime = performance.now();
    this.frameCount++;

    // Calculate FPS every second
    if (currentTime >= this.lastTime + 1000) {
      this.fps = Math.round((this.frameCount * 1000) / (currentTime - this.lastTime));
      this.fpsHistory.push(this.fps);

      // Keep history limited
      if (this.fpsHistory.length > this.maxHistoryLength) {
        this.fpsHistory.shift();
      }

      // Log FPS in development
      if (process.env.NODE_ENV === 'development') {
        console.log(`[Performance] Current FPS: ${this.fps}`);
      }

      this.frameCount = 0;
      this.lastTime = currentTime;
    }

    requestAnimationFrame(() => this.measureFPS());
  }

  /**
   * Get current FPS
   */
  getCurrentFPS() {
    return this.fps;
  }

  /**
   * Get average FPS from history
   */
  getAverageFPS() {
    if (this.fpsHistory.length === 0) return 60;
    const sum = this.fpsHistory.reduce((a, b) => a + b, 0);
    return Math.round(sum / this.fpsHistory.length);
  }

  /**
   * Check if performance is good (FPS > 50)
   */
  isPerformanceGood() {
    return this.getAverageFPS() > 50;
  }
}

/**
 * Get device performance level based on various factors
 * @returns {string} - 'high', 'medium', or 'low'
 */
export const getDevicePerformance = () => {
  let score = 0;

  // Check device memory (if available)
  if (navigator.deviceMemory) {
    if (navigator.deviceMemory >= 8) score += 3;
    else if (navigator.deviceMemory >= 4) score += 2;
    else score += 1;
  } else {
    score += 2; // Default to medium if not available
  }

  // Check hardware concurrency (CPU cores)
  if (navigator.hardwareConcurrency) {
    if (navigator.hardwareConcurrency >= 8) score += 3;
    else if (navigator.hardwareConcurrency >= 4) score += 2;
    else score += 1;
  } else {
    score += 2; // Default to medium
  }

  // Check connection speed (if available)
  if (navigator.connection) {
    const effectiveType = navigator.connection.effectiveType;
    if (effectiveType === '4g') score += 2;
    else if (effectiveType === '3g') score += 1;
    else score += 0;
  } else {
    score += 1; // Default to medium
  }

  // Determine performance level
  if (score >= 7) return 'high';
  if (score >= 4) return 'medium';
  return 'low';
};

/**
 * Get adaptive animation configuration based on device performance
 * @returns {Object} - Animation configuration object
 */
export const getAdaptiveAnimationConfig = () => {
  const performance = getDevicePerformance();
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // If user prefers reduced motion, disable all animations
  if (prefersReducedMotion) {
    return {
      enabled: false,
      duration: 0,
      staggerDelay: 0,
      particleCount: 0,
      blurIntensity: 0,
      glowIntensity: 0
    };
  }

  // Configure based on performance level
  const configs = {
    high: {
      enabled: true,
      duration: 0.6,
      staggerDelay: 0.15,
      particleCount: 50,
      blurIntensity: 20,
      glowIntensity: 1
    },
    medium: {
      enabled: true,
      duration: 0.4,
      staggerDelay: 0.1,
      particleCount: 25,
      blurIntensity: 15,
      glowIntensity: 0.7
    },
    low: {
      enabled: true,
      duration: 0.3,
      staggerDelay: 0.05,
      particleCount: 10,
      blurIntensity: 10,
      glowIntensity: 0.5
    }
  };

  return configs[performance];
};

/**
 * Apply adaptive CSS variables to document root
 */
export const applyAdaptiveStyles = () => {
  const config = getAdaptiveAnimationConfig();
  const root = document.documentElement;

  root.style.setProperty('--animation-duration', `${config.duration}s`);
  root.style.setProperty('--blur-intensity', `${config.blurIntensity}px`);
  root.style.setProperty('--glow-intensity', config.glowIntensity.toString());

  if (process.env.NODE_ENV === 'development') {
    console.log('[Performance] Applied adaptive styles:', config);
  }
};

/**
 * Check if browser supports required features
 */
export const checkBrowserSupport = () => {
  const support = {
    intersectionObserver: 'IntersectionObserver' in window,
    backdropFilter: CSS.supports('backdrop-filter', 'blur(10px)'),
    cssGrid: CSS.supports('display', 'grid'),
    cssVariables: CSS.supports('--test', '0'),
    webAnimations: 'animate' in document.createElement('div')
  };

  if (process.env.NODE_ENV === 'development') {
    console.log('[Performance] Browser support:', support);
  }

  return support;
};

// Create singleton instance
const performanceMonitor = new PerformanceMonitor();

export default performanceMonitor;
