import React, { useState, useRef, useEffect } from 'react';
import { motion, PanInfo } from 'framer-motion';
import { useResponsive } from './ResponsiveContainer';

// Touch-friendly кнопка с увеличенной областью нажатия
export const TouchButton = ({ 
  children, 
  onClick, 
  className = '', 
  size = 'md',
  variant = 'default',
  disabled = false,
  hapticFeedback = true,
  ...props 
}) => {
  const { isTouchDevice } = useResponsive();
  
  const sizeClasses = {
    sm: isTouchDevice ? 'min-h-[44px] min-w-[44px] px-4 py-2' : 'px-3 py-1.5',
    md: isTouchDevice ? 'min-h-[48px] min-w-[48px] px-6 py-3' : 'px-4 py-2',
    lg: isTouchDevice ? 'min-h-[52px] min-w-[52px] px-8 py-4' : 'px-6 py-3'
  };

  const handleClick = (e) => {
    // Haptic feedback для поддерживающих устройств
    if (hapticFeedback && navigator.vibrate && isTouchDevice) {
      navigator.vibrate(10);
    }
    
    if (onClick) {
      onClick(e);
    }
  };

  return (
    <motion.button
      className={`
        ${sizeClasses[size]}
        ${className}
        ${isTouchDevice ? 'touch-manipulation' : ''}
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        transition-all duration-200 rounded-lg font-medium
        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
        active:scale-95
      `}
      onClick={handleClick}
      disabled={disabled}
      whileTap={{ scale: disabled ? 1 : 0.95 }}
      whileHover={{ scale: disabled ? 1 : 1.02 }}
      {...props}
    >
      {children}
    </motion.button>
  );
};

// Swipeable карточка
export const SwipeableCard = ({ 
  children, 
  onSwipeLeft, 
  onSwipeRight, 
  onSwipeUp, 
  onSwipeDown,
  swipeThreshold = 100,
  className = '',
  disabled = false
}) => {
  const { isTouchDevice } = useResponsive();
  const [isDragging, setIsDragging] = useState(false);

  const handleDragEnd = (event, info) => {
    setIsDragging(false);
    
    if (disabled) return;

    const { offset, velocity } = info;
    const swipeConfidenceThreshold = 10000;
    const swipePower = (offset, velocity) => Math.abs(offset) * velocity;

    // Горизонтальные свайпы
    if (swipePower(offset.x, velocity.x) > swipeConfidenceThreshold) {
      if (offset.x > swipeThreshold && onSwipeRight) {
        onSwipeRight();
      } else if (offset.x < -swipeThreshold && onSwipeLeft) {
        onSwipeLeft();
      }
    }

    // Вертикальные свайпы
    if (swipePower(offset.y, velocity.y) > swipeConfidenceThreshold) {
      if (offset.y > swipeThreshold && onSwipeDown) {
        onSwipeDown();
      } else if (offset.y < -swipeThreshold && onSwipeUp) {
        onSwipeUp();
      }
    }
  };

  if (!isTouchDevice) {
    return <div className={className}>{children}</div>;
  }

  return (
    <motion.div
      className={`${className} ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}`}
      drag={!disabled}
      dragConstraints={{ left: 0, right: 0, top: 0, bottom: 0 }}
      dragElastic={0.2}
      onDragStart={() => setIsDragging(true)}
      onDragEnd={handleDragEnd}
      whileDrag={{ scale: 1.05, rotate: isDragging ? 2 : 0 }}
    >
      {children}
    </motion.div>
  );
};

// Touch-friendly слайдер
export const TouchSlider = ({ 
  value, 
  onChange, 
  min = 0, 
  max = 100, 
  step = 1,
  className = '',
  disabled = false,
  showValue = true
}) => {
  const { isTouchDevice } = useResponsive();
  const sliderRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  const handlePointerDown = (e) => {
    if (disabled) return;
    setIsDragging(true);
    updateValue(e);
  };

  const handlePointerMove = (e) => {
    if (!isDragging || disabled) return;
    updateValue(e);
  };

  const handlePointerUp = () => {
    setIsDragging(false);
  };

  const updateValue = (e) => {
    if (!sliderRef.current) return;

    const rect = sliderRef.current.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const percentage = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
    const newValue = min + (max - min) * percentage;
    const steppedValue = Math.round(newValue / step) * step;
    
    onChange(Math.max(min, Math.min(max, steppedValue)));
  };

  useEffect(() => {
    const handleGlobalPointerMove = (e) => handlePointerMove(e);
    const handleGlobalPointerUp = () => handlePointerUp();

    if (isDragging) {
      document.addEventListener('mousemove', handleGlobalPointerMove);
      document.addEventListener('mouseup', handleGlobalPointerUp);
      document.addEventListener('touchmove', handleGlobalPointerMove);
      document.addEventListener('touchend', handleGlobalPointerUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleGlobalPointerMove);
      document.removeEventListener('mouseup', handleGlobalPointerUp);
      document.removeEventListener('touchmove', handleGlobalPointerMove);
      document.removeEventListener('touchend', handleGlobalPointerUp);
    };
  }, [isDragging]);

  const percentage = ((value - min) / (max - min)) * 100;

  return (
    <div className={`relative ${className}`}>
      <div
        ref={sliderRef}
        className={`
          relative w-full bg-gray-200 dark:bg-gray-700 rounded-full cursor-pointer
          ${isTouchDevice ? 'h-8' : 'h-4'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
        `}
        onMouseDown={handlePointerDown}
        onTouchStart={handlePointerDown}
      >
        {/* Track */}
        <div
          className="absolute top-0 left-0 h-full bg-blue-500 rounded-full transition-all duration-150"
          style={{ width: `${percentage}%` }}
        />
        
        {/* Thumb */}
        <motion.div
          className={`
            absolute top-1/2 transform -translate-y-1/2 bg-white border-2 border-blue-500 rounded-full shadow-lg
            ${isTouchDevice ? 'w-8 h-8' : 'w-6 h-6'}
            ${isDragging ? 'scale-110' : 'scale-100'}
            ${disabled ? 'cursor-not-allowed' : 'cursor-grab'}
          `}
          style={{ left: `calc(${percentage}% - ${isTouchDevice ? '16px' : '12px'})` }}
          animate={{ scale: isDragging ? 1.1 : 1 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        />
      </div>
      
      {showValue && (
        <div className="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
          {value}
        </div>
      )}
    </div>
  );
};

// Touch-friendly переключатель
export const TouchToggle = ({ 
  checked, 
  onChange, 
  label,
  description,
  disabled = false,
  size = 'md',
  className = ''
}) => {
  const { isTouchDevice } = useResponsive();

  const sizeClasses = {
    sm: isTouchDevice ? 'w-12 h-7' : 'w-10 h-6',
    md: isTouchDevice ? 'w-14 h-8' : 'w-12 h-7',
    lg: isTouchDevice ? 'w-16 h-9' : 'w-14 h-8'
  };

  const thumbSizeClasses = {
    sm: isTouchDevice ? 'w-5 h-5' : 'w-4 h-4',
    md: isTouchDevice ? 'w-6 h-6' : 'w-5 h-5',
    lg: isTouchDevice ? 'w-7 h-7' : 'w-6 h-6'
  };

  const handleToggle = () => {
    if (disabled) return;
    
    // Haptic feedback
    if (navigator.vibrate && isTouchDevice) {
      navigator.vibrate(10);
    }
    
    onChange(!checked);
  };

  return (
    <div className={`flex items-center space-x-3 ${className}`}>
      <motion.button
        className={`
          relative inline-flex items-center rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
          ${sizeClasses[size]}
          ${checked ? 'bg-blue-500' : 'bg-gray-300 dark:bg-gray-600'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
          ${isTouchDevice ? 'touch-manipulation' : ''}
        `}
        onClick={handleToggle}
        disabled={disabled}
        whileTap={{ scale: disabled ? 1 : 0.95 }}
      >
        <motion.div
          className={`
            inline-block rounded-full bg-white shadow-lg transform transition-transform duration-200
            ${thumbSizeClasses[size]}
          `}
          animate={{
            x: checked ? 
              (size === 'sm' ? (isTouchDevice ? 20 : 16) :
               size === 'md' ? (isTouchDevice ? 24 : 20) :
               (isTouchDevice ? 28 : 24)) : 4
          }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        />
      </motion.button>
      
      {(label || description) && (
        <div className="flex-1">
          {label && (
            <div className="text-sm font-medium text-gray-900 dark:text-white">
              {label}
            </div>
          )}
          {description && (
            <div className="text-xs text-gray-500 dark:text-gray-400">
              {description}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Touch-friendly input с увеличенной областью нажатия
export const TouchInput = ({ 
  className = '', 
  size = 'md',
  ...props 
}) => {
  const { isTouchDevice } = useResponsive();

  const sizeClasses = {
    sm: isTouchDevice ? 'min-h-[44px] px-4 py-3' : 'px-3 py-2',
    md: isTouchDevice ? 'min-h-[48px] px-4 py-3' : 'px-4 py-2',
    lg: isTouchDevice ? 'min-h-[52px] px-6 py-4' : 'px-6 py-3'
  };

  return (
    <input
      className={`
        ${sizeClasses[size]}
        ${className}
        ${isTouchDevice ? 'touch-manipulation' : ''}
        w-full rounded-lg border border-gray-300 dark:border-gray-600 
        bg-white dark:bg-gray-800 text-gray-900 dark:text-white
        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
        transition-all duration-200
      `}
      {...props}
    />
  );
};

// Компонент для обнаружения touch-жестов
export const TouchGestureDetector = ({ 
  children, 
  onTap, 
  onDoubleTap, 
  onLongPress,
  onPinch,
  className = ''
}) => {
  const { isTouchDevice } = useResponsive();
  const [lastTap, setLastTap] = useState(0);
  const [longPressTimer, setLongPressTimer] = useState(null);

  const handleTouchStart = (e) => {
    if (!isTouchDevice) return;

    // Long press detection
    const timer = setTimeout(() => {
      if (onLongPress) {
        onLongPress(e);
        // Haptic feedback for long press
        if (navigator.vibrate) {
          navigator.vibrate(50);
        }
      }
    }, 500);
    
    setLongPressTimer(timer);
  };

  const handleTouchEnd = (e) => {
    if (!isTouchDevice) return;

    // Clear long press timer
    if (longPressTimer) {
      clearTimeout(longPressTimer);
      setLongPressTimer(null);
    }

    // Double tap detection
    const now = Date.now();
    const timeDiff = now - lastTap;
    
    if (timeDiff < 300 && timeDiff > 0) {
      // Double tap
      if (onDoubleTap) {
        onDoubleTap(e);
        // Haptic feedback for double tap
        if (navigator.vibrate) {
          navigator.vibrate([10, 50, 10]);
        }
      }
      setLastTap(0);
    } else {
      // Single tap
      if (onTap) {
        setTimeout(() => {
          if (lastTap === now) {
            onTap(e);
          }
        }, 300);
      }
      setLastTap(now);
    }
  };

  if (!isTouchDevice) {
    return <div className={className}>{children}</div>;
  }

  return (
    <div
      className={`${className} touch-manipulation`}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      {children}
    </div>
  );
};

export default {
  TouchButton,
  SwipeableCard,
  TouchSlider,
  TouchToggle,
  TouchInput,
  TouchGestureDetector
};