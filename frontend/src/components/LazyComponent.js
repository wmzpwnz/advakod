import React, { Suspense, lazy, useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

// Компонент загрузки
const LoadingSpinner = ({ message = "Загрузка..." }) => {
  const { isDark } = useTheme();
  
  return (
    <div className={`flex items-center justify-center p-8 ${isDark ? 'bg-gray-800' : 'bg-gray-50'} rounded-lg`}>
      <div className="flex flex-col items-center space-y-3">
        <Loader2 className="h-8 w-8 text-primary-600 animate-spin" />
        <p className="text-sm text-gray-600 dark:text-gray-400">{message}</p>
      </div>
    </div>
  );
};

// Компонент ошибки
const ErrorBoundary = ({ error, retry }) => {
  const { isDark } = useTheme();
  
  return (
    <div className={`p-8 ${isDark ? 'bg-gray-800' : 'bg-gray-50'} rounded-lg border border-red-200 dark:border-red-800`}>
      <div className="text-center">
        <div className="text-red-600 dark:text-red-400 mb-4">
          <svg className="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
          Ошибка загрузки компонента
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          {error?.message || "Произошла неизвестная ошибка"}
        </p>
        <button
          onClick={retry}
          className="btn-primary text-sm px-4 py-2"
        >
          Попробовать снова
        </button>
      </div>
    </div>
  );
};

// Основной компонент ленивой загрузки
const LazyComponent = ({ 
  importFunc, 
  fallback = null, 
  errorFallback = null,
  loadingMessage = "Загрузка компонента...",
  delay = 0,
  ...props 
}) => {
  const [Component, setComponent] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showLoading, setShowLoading] = useState(delay === 0);

  useEffect(() => {
    let timeoutId;
    
    // Задержка перед показом индикатора загрузки
    if (delay > 0) {
      timeoutId = setTimeout(() => {
        setShowLoading(true);
      }, delay);
    }

    // Загружаем компонент
    const loadComponent = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        const module = await importFunc();
        const component = module.default || module;
        setComponent(() => component);
      } catch (err) {
        console.error('Error loading component:', err);
        setError(err);
      } finally {
        setIsLoading(false);
        if (timeoutId) {
          clearTimeout(timeoutId);
        }
      }
    };

    loadComponent();

    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [importFunc, delay]);

  const retry = () => {
    setError(null);
    setComponent(null);
    setIsLoading(true);
    setShowLoading(delay === 0);
  };

  // Показываем ошибку
  if (error) {
    if (errorFallback) {
      return errorFallback(error, retry);
    }
    return <ErrorBoundary error={error} retry={retry} />;
  }

  // Показываем загрузку
  if (isLoading || !Component) {
    if (showLoading) {
      if (fallback) {
        return fallback;
      }
      return <LoadingSpinner message={loadingMessage} />;
    }
    return null; // Не показываем ничего до истечения задержки
  }

  // Рендерим загруженный компонент
  return <Component {...props} />;
};

// HOC для ленивой загрузки
export const withLazyLoading = (importFunc, options = {}) => {
  return (props) => (
    <LazyComponent
      importFunc={importFunc}
      {...options}
      {...props}
    />
  );
};

// Предустановленные ленивые компоненты
export const LazyChat = withLazyLoading(
  () => import('../pages/Chat'),
  { loadingMessage: "Загрузка чата..." }
);

export const LazyProfile = withLazyLoading(
  () => import('../pages/Profile'),
  { loadingMessage: "Загрузка профиля..." }
);

export const LazyPricing = withLazyLoading(
  () => import('../pages/Pricing'),
  { loadingMessage: "Загрузка тарифов..." }
);

export const LazyFileUpload = withLazyLoading(
  () => import('./FileUpload'),
  { loadingMessage: "Загрузка компонента загрузки файлов..." }
);

export const LazyQuestionTemplates = withLazyLoading(
  () => import('./QuestionTemplates'),
  { loadingMessage: "Загрузка шаблонов вопросов..." }
);

export const LazyMessageSearch = withLazyLoading(
  () => import('./MessageSearch'),
  { loadingMessage: "Загрузка поиска..." }
);

export const LazyTwoFactorSetup = withLazyLoading(
  () => import('./TwoFactorSetup'),
  { loadingMessage: "Загрузка настройки 2FA..." }
);

export const LazyTwoFactorInput = withLazyLoading(
  () => import('./TwoFactorInput'),
  { loadingMessage: "Загрузка ввода 2FA..." }
);

// Компонент для ленивой загрузки изображений
export const LazyImage = ({ src, alt, className, placeholder, ...props }) => {
  const [imageSrc, setImageSrc] = useState(placeholder || '');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const img = new Image();
    
    img.onload = () => {
      setImageSrc(src);
      setIsLoading(false);
    };
    
    img.onerror = () => {
      setError(true);
      setIsLoading(false);
    };
    
    img.src = src;
  }, [src]);

  if (error) {
    return (
      <div className={`flex items-center justify-center bg-gray-200 dark:bg-gray-700 ${className}`}>
        <span className="text-gray-500 dark:text-gray-400 text-sm">Ошибка загрузки</span>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-200 dark:bg-gray-700">
          <Loader2 className="h-6 w-6 text-primary-600 animate-spin" />
        </div>
      )}
      <img
        src={imageSrc}
        alt={alt}
        className={`transition-opacity duration-300 ${isLoading ? 'opacity-0' : 'opacity-100'}`}
        {...props}
      />
    </div>
  );
};

// Компонент для ленивой загрузки с Intersection Observer
export const LazyIntersection = ({ 
  children, 
  rootMargin = '50px',
  threshold = 0.1,
  fallback = null,
  ...props 
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [hasIntersected, setHasIntersected] = useState(false);
  const ref = React.useRef();

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasIntersected) {
          setIsVisible(true);
          setHasIntersected(true);
          observer.disconnect();
        }
      },
      { rootMargin, threshold }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => observer.disconnect();
  }, [rootMargin, threshold, hasIntersected]);

  return (
    <div ref={ref} {...props}>
      {isVisible ? children : (fallback || <div style={{ height: '200px' }} />)}
    </div>
  );
};

export default LazyComponent;
