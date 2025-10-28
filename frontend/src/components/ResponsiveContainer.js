import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

const ResponsiveContainer = ({ 
  children, 
  className = '', 
  mobileClassName = '',
  tabletClassName = '',
  desktopClassName = '',
  breakpoints = {
    mobile: 768,
    tablet: 1024,
    desktop: 1280
  }
}) => {
  const [screenSize, setScreenSize] = useState('desktop');
  const [dimensions, setDimensions] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 1280,
    height: typeof window !== 'undefined' ? window.innerHeight : 720
  });

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      
      setDimensions({ width, height });
      
      if (width < breakpoints.mobile) {
        setScreenSize('mobile');
      } else if (width < breakpoints.tablet) {
        setScreenSize('tablet');
      } else {
        setScreenSize('desktop');
      }
    };

    // Устанавливаем начальный размер
    handleResize();

    // Добавляем слушатель изменения размера окна
    window.addEventListener('resize', handleResize);
    
    // Добавляем слушатель изменения ориентации для мобильных устройств
    window.addEventListener('orientationchange', () => {
      setTimeout(handleResize, 100); // Небольшая задержка для корректного определения размеров
    });

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleResize);
    };
  }, [breakpoints]);

  // Определяем CSS классы в зависимости от размера экрана
  const getResponsiveClasses = () => {
    const baseClasses = className;
    
    switch (screenSize) {
      case 'mobile':
        return `${baseClasses} ${mobileClassName}`.trim();
      case 'tablet':
        return `${baseClasses} ${tabletClassName}`.trim();
      case 'desktop':
        return `${baseClasses} ${desktopClassName}`.trim();
      default:
        return baseClasses;
    }
  };

  // Контекст для дочерних компонентов
  const responsiveContext = {
    screenSize,
    dimensions,
    isMobile: screenSize === 'mobile',
    isTablet: screenSize === 'tablet',
    isDesktop: screenSize === 'desktop',
    isTouchDevice: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
    isLandscape: dimensions.width > dimensions.height,
    isPortrait: dimensions.height > dimensions.width
  };

  return (
    <motion.div
      className={getResponsiveClasses()}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      data-screen-size={screenSize}
      data-touch-device={responsiveContext.isTouchDevice}
      style={{
        '--screen-width': `${dimensions.width}px`,
        '--screen-height': `${dimensions.height}px`,
        '--is-mobile': screenSize === 'mobile' ? '1' : '0',
        '--is-tablet': screenSize === 'tablet' ? '1' : '0',
        '--is-desktop': screenSize === 'desktop' ? '1' : '0'
      }}
    >
      {typeof children === 'function' ? children(responsiveContext) : children}
    </motion.div>
  );
};

// Hook для использования responsive контекста
export const useResponsive = () => {
  const [screenSize, setScreenSize] = useState('desktop');
  const [dimensions, setDimensions] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 1280,
    height: typeof window !== 'undefined' ? window.innerHeight : 720
  });

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      
      setDimensions({ width, height });
      
      if (width < 768) {
        setScreenSize('mobile');
      } else if (width < 1024) {
        setScreenSize('tablet');
      } else {
        setScreenSize('desktop');
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    window.addEventListener('orientationchange', () => {
      setTimeout(handleResize, 100);
    });

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleResize);
    };
  }, []);

  return {
    screenSize,
    dimensions,
    isMobile: screenSize === 'mobile',
    isTablet: screenSize === 'tablet',
    isDesktop: screenSize === 'desktop',
    isTouchDevice: 'ontouchstart' in window || navigator.maxTouchPoints > 0,
    isLandscape: dimensions.width > dimensions.height,
    isPortrait: dimensions.height > dimensions.width,
    
    // Утилиты для условного рендеринга
    showOnMobile: screenSize === 'mobile',
    showOnTablet: screenSize === 'tablet',
    showOnDesktop: screenSize === 'desktop',
    showOnMobileAndTablet: screenSize === 'mobile' || screenSize === 'tablet',
    showOnTabletAndDesktop: screenSize === 'tablet' || screenSize === 'desktop',
    
    // Утилиты для CSS классов
    mobileClass: (className) => screenSize === 'mobile' ? className : '',
    tabletClass: (className) => screenSize === 'tablet' ? className : '',
    desktopClass: (className) => screenSize === 'desktop' ? className : '',
    responsiveClass: (mobile, tablet, desktop) => {
      switch (screenSize) {
        case 'mobile': return mobile || '';
        case 'tablet': return tablet || mobile || '';
        case 'desktop': return desktop || tablet || mobile || '';
        default: return '';
      }
    }
  };
};

// Компонент для условного рендеринга на разных устройствах
export const ResponsiveRender = ({ 
  mobile, 
  tablet, 
  desktop, 
  mobileAndTablet, 
  tabletAndDesktop,
  fallback = null 
}) => {
  const { screenSize } = useResponsive();

  if (mobileAndTablet && (screenSize === 'mobile' || screenSize === 'tablet')) {
    return mobileAndTablet;
  }

  if (tabletAndDesktop && (screenSize === 'tablet' || screenSize === 'desktop')) {
    return tabletAndDesktop;
  }

  switch (screenSize) {
    case 'mobile':
      return mobile || fallback;
    case 'tablet':
      return tablet || fallback;
    case 'desktop':
      return desktop || fallback;
    default:
      return fallback;
  }
};

// Компонент для адаптивной сетки
export const ResponsiveGrid = ({ 
  children, 
  cols = { mobile: 1, tablet: 2, desktop: 3 },
  gap = { mobile: 4, tablet: 6, desktop: 8 },
  className = ''
}) => {
  const { screenSize } = useResponsive();
  
  const currentCols = cols[screenSize] || cols.desktop || 3;
  const currentGap = gap[screenSize] || gap.desktop || 8;
  
  const gridClasses = `grid grid-cols-${currentCols} gap-${currentGap} ${className}`;
  
  return (
    <div className={gridClasses}>
      {children}
    </div>
  );
};

// Компонент для адаптивного текста
export const ResponsiveText = ({ 
  mobile, 
  tablet, 
  desktop, 
  className = '',
  as: Component = 'div'
}) => {
  const { screenSize } = useResponsive();
  
  const text = screenSize === 'mobile' ? mobile : 
               screenSize === 'tablet' ? (tablet || mobile) : 
               (desktop || tablet || mobile);
  
  return (
    <Component className={className}>
      {text}
    </Component>
  );
};

export default ResponsiveContainer;