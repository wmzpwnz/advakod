import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Хук для ленивой загрузки данных
 * @param {Function} fetchFunction - Функция для загрузки данных
 * @param {Object} options - Опции
 * @returns {Object} - Состояние и методы
 */
export const useLazyData = (fetchFunction, options = {}) => {
  const {
    initialData = null,
    enabled = true,
    retryCount = 3,
    retryDelay = 1000,
    cacheTime = 5 * 60 * 1000, // 5 минут
    staleTime = 0,
    onSuccess = null,
    onError = null,
    onRetry = null
  } = options;

  const [data, setData] = useState(initialData);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isStale, setIsStale] = useState(false);
  
  const retryCountRef = useRef(0);
  const lastFetchTimeRef = useRef(0);
  const cacheRef = useRef(new Map());

  const fetchData = useCallback(async (params = {}) => {
    if (!enabled) return;

    const cacheKey = JSON.stringify(params);
    const now = Date.now();
    
    // Проверяем кэш
    if (cacheRef.current.has(cacheKey)) {
      const cached = cacheRef.current.get(cacheKey);
      if (now - cached.timestamp < cacheTime) {
        setData(cached.data);
        setIsStale(now - cached.timestamp > staleTime);
        return cached.data;
      }
    }

    setIsLoading(true);
    setError(null);

    try {
      const result = await fetchFunction(params);
      
      // Кэшируем результат
      cacheRef.current.set(cacheKey, {
        data: result,
        timestamp: now
      });
      
      setData(result);
      setIsStale(false);
      lastFetchTimeRef.current = now;
      retryCountRef.current = 0;
      
      if (onSuccess) {
        onSuccess(result);
      }
      
      return result;
    } catch (err) {
      setError(err);
      
      if (onError) {
        onError(err);
      }
      
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [fetchFunction, enabled, cacheTime, staleTime, onSuccess, onError]);

  const retry = useCallback(async (params = {}) => {
    if (retryCountRef.current >= retryCount) {
      return;
    }

    retryCountRef.current++;
    
    if (onRetry) {
      onRetry(retryCountRef.current);
    }

    // Задержка перед повтором
    if (retryDelay > 0) {
      await new Promise(resolve => setTimeout(resolve, retryDelay));
    }

    return fetchData(params);
  }, [fetchData, retryCount, retryDelay, onRetry]);

  const invalidate = useCallback((params = {}) => {
    const cacheKey = JSON.stringify(params);
    cacheRef.current.delete(cacheKey);
    setIsStale(true);
  }, []);

  const clearCache = useCallback(() => {
    cacheRef.current.clear();
  }, []);

  const refetch = useCallback((params = {}) => {
    invalidate(params);
    return fetchData(params);
  }, [fetchData, invalidate]);

  // Автоматическая загрузка при изменении зависимостей
  useEffect(() => {
    if (enabled && !data && !isLoading) {
      fetchData();
    }
  }, [enabled, data, isLoading, fetchData]);

  return {
    data,
    isLoading,
    error,
    isStale,
    fetchData,
    retry,
    invalidate,
    clearCache,
    refetch,
    retryCount: retryCountRef.current
  };
};

/**
 * Хук для ленивой загрузки с Intersection Observer
 */
export const useLazyIntersection = (options = {}) => {
  const {
    rootMargin = '50px',
    threshold = 0.1,
    triggerOnce = true
  } = options;

  const [isIntersecting, setIsIntersecting] = useState(false);
  const [hasIntersected, setHasIntersected] = useState(false);
  const ref = useRef();

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsIntersecting(true);
          if (triggerOnce) {
            setHasIntersected(true);
            observer.disconnect();
          }
        } else if (!triggerOnce) {
          setIsIntersecting(false);
        }
      },
      { rootMargin, threshold }
    );

    observer.observe(element);

    return () => observer.disconnect();
  }, [rootMargin, threshold, triggerOnce]);

  return {
    ref,
    isIntersecting: triggerOnce ? hasIntersected : isIntersecting,
    hasIntersected
  };
};

/**
 * Хук для ленивой загрузки изображений
 */
export const useLazyImage = (src, options = {}) => {
  const {
    placeholder = '',
    errorImage = '',
    crossOrigin = null
  } = options;

  const [imageSrc, setImageSrc] = useState(placeholder);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!src) {
      setImageSrc(placeholder);
      setIsLoading(false);
      return;
    }

    const img = new Image();
    
    if (crossOrigin) {
      img.crossOrigin = crossOrigin;
    }

    img.onload = () => {
      setImageSrc(src);
      setIsLoading(false);
      setError(false);
    };

    img.onerror = () => {
      setImageSrc(errorImage || placeholder);
      setIsLoading(false);
      setError(true);
    };

    img.src = src;
  }, [src, placeholder, errorImage, crossOrigin]);

  return {
    src: imageSrc,
    isLoading,
    error
  };
};

/**
 * Хук для ленивой загрузки с виртуализацией
 */
export const useLazyVirtualization = (items, options = {}) => {
  const {
    itemHeight = 50,
    containerHeight = 400,
    overscan = 5
  } = options;

  const [scrollTop, setScrollTop] = useState(0);
  const [containerRef, setContainerRef] = useState(null);

  const visibleStart = Math.floor(scrollTop / itemHeight);
  const visibleEnd = Math.min(
    visibleStart + Math.ceil(containerHeight / itemHeight),
    items.length
  );

  const startIndex = Math.max(0, visibleStart - overscan);
  const endIndex = Math.min(items.length, visibleEnd + overscan);

  const visibleItems = items.slice(startIndex, endIndex).map((item, index) => ({
    ...item,
    index: startIndex + index
  }));

  const totalHeight = items.length * itemHeight;
  const offsetY = startIndex * itemHeight;

  const handleScroll = (e) => {
    setScrollTop(e.target.scrollTop);
  };

  return {
    visibleItems,
    totalHeight,
    offsetY,
    setContainerRef,
    handleScroll
  };
};

export default useLazyData;
