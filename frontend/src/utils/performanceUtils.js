/**
 * Performance Utility Functions
 * Collection of utilities for optimizing React application performance
 */

// Debounce function for search and input handling
export const debounce = (func, wait, immediate = false) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      timeout = null;
      if (!immediate) func(...args);
    };
    const callNow = immediate && !timeout;
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
    if (callNow) func(...args);
  };
};

// Throttle function for scroll and resize handlers
export const throttle = (func, limit) => {
  let inThrottle;
  return function executedFunction(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

// Memoization utility for expensive calculations
export const memoize = (fn, getKey = (...args) => JSON.stringify(args)) => {
  const cache = new Map();
  
  return (...args) => {
    const key = getKey(...args);
    
    if (cache.has(key)) {
      return cache.get(key);
    }
    
    const result = fn(...args);
    cache.set(key, result);
    
    // Prevent memory leaks by limiting cache size
    if (cache.size > 100) {
      const firstKey = cache.keys().next().value;
      cache.delete(firstKey);
    }
    
    return result;
  };
};

// Virtual scrolling utilities
export const virtualScrollUtils = {
  // Calculate visible items for virtual scrolling
  calculateVisibleRange: (scrollTop, itemHeight, containerHeight, totalItems, overscan = 5) => {
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const endIndex = Math.min(
      totalItems - 1,
      Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
    );
    
    return { startIndex, endIndex, visibleCount: endIndex - startIndex + 1 };
  },
  
  // Get transform style for virtual scrolling container
  getContainerStyle: (totalItems, itemHeight) => ({
    height: totalItems * itemHeight,
    position: 'relative'
  }),
  
  // Get item style for virtual scrolling
  getItemStyle: (index, itemHeight, width = '100%') => ({
    position: 'absolute',
    top: index * itemHeight,
    left: 0,
    width,
    height: itemHeight
  })
};

// Image optimization utilities
export const imageUtils = {
  // Lazy load images with intersection observer
  createLazyImageLoader: (threshold = 0.1, rootMargin = '50px') => {
    const imageCache = new Set();
    
    return (imgElement, src, placeholder = '') => {
      if (imageCache.has(src)) {
        imgElement.src = src;
        return;
      }
      
      imgElement.src = placeholder;
      
      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            const img = new Image();
            img.onload = () => {
              imgElement.src = src;
              imageCache.add(src);
              observer.disconnect();
            };
            img.onerror = () => {
              observer.disconnect();
            };
            img.src = src;
          }
        },
        { threshold, rootMargin }
      );
      
      observer.observe(imgElement);
      
      return () => observer.disconnect();
    };
  },
  
  // Preload critical images
  preloadImages: (urls) => {
    urls.forEach(url => {
      const img = new Image();
      img.src = url;
    });
  },
  
  // Generate responsive image URLs
  generateResponsiveUrl: (baseUrl, width, height, quality = 80) => {
    const params = new URLSearchParams({
      w: width,
      h: height,
      q: quality,
      f: 'webp'
    });
    return `${baseUrl}?${params.toString()}`;
  }
};

// Bundle optimization utilities
export const bundleUtils = {
  // Dynamic import with error handling and retry
  dynamicImport: async (importFn, retries = 3, delay = 1000) => {
    for (let i = 0; i < retries; i++) {
      try {
        return await importFn();
      } catch (error) {
        if (i === retries - 1) throw error;
        await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
      }
    }
  },
  
  // Preload chunks during idle time
  preloadChunks: (chunkImports) => {
    if ('requestIdleCallback' in window) {
      requestIdleCallback(() => {
        chunkImports.forEach(importFn => {
          importFn().catch(() => {
            // Ignore preload errors
          });
        });
      });
    } else {
      // Fallback for browsers without requestIdleCallback
      setTimeout(() => {
        chunkImports.forEach(importFn => {
          importFn().catch(() => {
            // Ignore preload errors
          });
        });
      }, 2000);
    }
  }
};

// Memory optimization utilities
export const memoryUtils = {
  // Clean up event listeners
  createCleanupManager: () => {
    const cleanupFunctions = [];
    
    return {
      add: (cleanupFn) => {
        cleanupFunctions.push(cleanupFn);
      },
      
      cleanup: () => {
        cleanupFunctions.forEach(fn => {
          try {
            fn();
          } catch (error) {
            console.warn('Cleanup function failed:', error);
          }
        });
        cleanupFunctions.length = 0;
      }
    };
  },
  
  // Weak reference cache for preventing memory leaks
  createWeakCache: () => {
    const cache = new WeakMap();
    
    return {
      get: (key) => cache.get(key),
      set: (key, value) => cache.set(key, value),
      has: (key) => cache.has(key),
      delete: (key) => cache.delete(key)
    };
  }
};

// Performance monitoring utilities
export const performanceUtils = {
  // Measure function execution time
  measureTime: (name, fn) => {
    return async (...args) => {
      const start = performance.now();
      try {
        const result = await fn(...args);
        const duration = performance.now() - start;
        console.log(`${name} took ${duration.toFixed(2)}ms`);
        return result;
      } catch (error) {
        const duration = performance.now() - start;
        console.log(`${name} failed after ${duration.toFixed(2)}ms`);
        throw error;
      }
    };
  },
  
  // Monitor component render performance
  createRenderProfiler: (componentName) => {
    return {
      onRender: (id, phase, actualDuration, baseDuration, startTime, commitTime) => {
        console.log(`${componentName} ${phase} phase:`, {
          actualDuration: actualDuration.toFixed(2),
          baseDuration: baseDuration.toFixed(2),
          startTime: startTime.toFixed(2),
          commitTime: commitTime.toFixed(2)
        });
      }
    };
  },
  
  // Monitor Core Web Vitals
  monitorWebVitals: () => {
    if ('web-vitals' in window) {
      import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
        getCLS(console.log.bind(console, 'CLS:'));
        getFID(console.log.bind(console, 'FID:'));
        getFCP(console.log.bind(console, 'FCP:'));
        getLCP(console.log.bind(console, 'LCP:'));
        getTTFB(console.log.bind(console, 'TTFB:'));
      });
    }
  }
};

// Cache utilities
export const cacheUtils = {
  // Create LRU cache
  createLRUCache: (maxSize = 100) => {
    const cache = new Map();
    
    return {
      get: (key) => {
        if (cache.has(key)) {
          const value = cache.get(key);
          cache.delete(key);
          cache.set(key, value);
          return value;
        }
        return undefined;
      },
      
      set: (key, value) => {
        if (cache.has(key)) {
          cache.delete(key);
        } else if (cache.size >= maxSize) {
          const firstKey = cache.keys().next().value;
          cache.delete(firstKey);
        }
        cache.set(key, value);
      },
      
      has: (key) => cache.has(key),
      delete: (key) => cache.delete(key),
      clear: () => cache.clear(),
      size: () => cache.size
    };
  },
  
  // Create time-based cache
  createTTLCache: (defaultTTL = 300000) => { // 5 minutes default
    const cache = new Map();
    
    return {
      get: (key) => {
        const item = cache.get(key);
        if (!item) return undefined;
        
        if (Date.now() > item.expiry) {
          cache.delete(key);
          return undefined;
        }
        
        return item.value;
      },
      
      set: (key, value, ttl = defaultTTL) => {
        cache.set(key, {
          value,
          expiry: Date.now() + ttl
        });
      },
      
      has: (key) => {
        const item = cache.get(key);
        if (!item) return false;
        
        if (Date.now() > item.expiry) {
          cache.delete(key);
          return false;
        }
        
        return true;
      },
      
      delete: (key) => cache.delete(key),
      clear: () => cache.clear(),
      size: () => cache.size
    };
  }
};

// Network optimization utilities
export const networkUtils = {
  // Create optimized fetch with retry and timeout
  createOptimizedFetch: (defaultTimeout = 10000, maxRetries = 3) => {
    return async (url, options = {}) => {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), defaultTimeout);
      
      const fetchOptions = {
        ...options,
        signal: controller.signal
      };
      
      for (let attempt = 0; attempt < maxRetries; attempt++) {
        try {
          const response = await fetch(url, fetchOptions);
          clearTimeout(timeoutId);
          
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }
          
          return response;
        } catch (error) {
          if (attempt === maxRetries - 1) {
            clearTimeout(timeoutId);
            throw error;
          }
          
          // Exponential backoff
          await new Promise(resolve => 
            setTimeout(resolve, Math.pow(2, attempt) * 1000)
          );
        }
      }
    };
  },
  
  // Batch API requests
  createRequestBatcher: (batchSize = 5, delay = 100) => {
    const queue = [];
    let timeoutId = null;
    
    const processBatch = async () => {
      const batch = queue.splice(0, batchSize);
      const promises = batch.map(({ url, options, resolve, reject }) => {
        return fetch(url, options)
          .then(resolve)
          .catch(reject);
      });
      
      await Promise.allSettled(promises);
      
      if (queue.length > 0) {
        timeoutId = setTimeout(processBatch, delay);
      }
    };
    
    return (url, options = {}) => {
      return new Promise((resolve, reject) => {
        queue.push({ url, options, resolve, reject });
        
        if (!timeoutId) {
          timeoutId = setTimeout(processBatch, delay);
        }
      });
    };
  }
};

// Export all utilities
export default {
  debounce,
  throttle,
  memoize,
  virtualScrollUtils,
  imageUtils,
  bundleUtils,
  memoryUtils,
  performanceUtils,
  cacheUtils,
  networkUtils
};