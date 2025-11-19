import React from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../contexts/ThemeContext';

const LoadingSpinner = ({ 
  size = 'md',
  module = null,
  variant = 'default',
  className = '',
  text = null,
  ...props 
}) => {
  const { getModuleColor } = useTheme();

  const sizeClasses = {
    xs: 'w-4 h-4',
    sm: 'w-6 h-6', 
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16'
  };

  const textSizeClasses = {
    xs: 'text-xs',
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg', 
    xl: 'text-xl'
  };

  // Get module color if specified
  const moduleColor = module ? getModuleColor(module) : null;
  const moduleColorLight = module ? getModuleColor(module, 'light') : null;

  const getSpinnerStyles = () => {
    if (module && variant === 'module') {
      return {
        borderColor: `${moduleColor}30`, // 20% opacity for border
        borderTopColor: moduleColor,
      };
    }
    
    if (module && variant === 'neon') {
      return {
        borderColor: `${moduleColor}40`,
        borderTopColor: moduleColor,
        boxShadow: `0 0 10px ${moduleColor}60`,
      };
    }
    
    return {};
  };

  const getVariantClasses = () => {
    switch (variant) {
      case 'module':
        return 'border-2 border-gray-200 dark:border-gray-700';
      case 'neon':
        return 'border-2 border-purple-200 dark:border-purple-700';
      case 'dots':
        return '';
      default:
        return 'border-2 border-gray-200 dark:border-gray-700 border-t-primary-500';
    }
  };

  const spinnerClasses = `
    ${sizeClasses[size]}
    ${getVariantClasses()}
    ${variant !== 'dots' ? 'rounded-full animate-spin' : ''}
    ${className}
  `;

  // Dots variant
  if (variant === 'dots') {
    const dotColor = module ? moduleColor : '#6366f1';
    
    return (
      <div className={`flex items-center space-x-1 ${className}`} {...props}>
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className={`rounded-full ${size === 'xs' ? 'w-1 h-1' : size === 'sm' ? 'w-1.5 h-1.5' : size === 'md' ? 'w-2 h-2' : size === 'lg' ? 'w-3 h-3' : 'w-4 h-4'}`}
            style={{ backgroundColor: dotColor }}
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.5, 1, 0.5],
            }}
            transition={{
              duration: 0.8,
              repeat: Infinity,
              delay: i * 0.2,
              ease: "easeInOut",
            }}
          />
        ))}
        {text && (
          <span className={`ml-3 text-gray-600 dark:text-gray-400 ${textSizeClasses[size]}`}>
            {text}
          </span>
        )}
      </div>
    );
  }

  // Pulse variant for neon effect
  if (variant === 'neon') {
    return (
      <div className={`flex flex-col items-center space-y-3 ${className}`} {...props}>
        <motion.div
          className={spinnerClasses}
          style={getSpinnerStyles()}
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        />
        {text && (
          <motion.span 
            className={`text-center ${textSizeClasses[size]}`}
            style={{ color: moduleColor || '#8b5cf6' }}
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
          >
            {text}
          </motion.span>
        )}
      </div>
    );
  }

  // Default spinner
  return (
    <div className={`flex flex-col items-center space-y-3 ${className}`} {...props}>
      <div
        className={spinnerClasses}
        style={getSpinnerStyles()}
      />
      {text && (
        <span className={`text-gray-600 dark:text-gray-400 text-center ${textSizeClasses[size]}`}>
          {text}
        </span>
      )}
    </div>
  );
};

// Preset spinners for different modules
export const MarketingSpinner = (props) => (
  <LoadingSpinner module="marketing" variant="module" {...props} />
);

export const ModerationSpinner = (props) => (
  <LoadingSpinner module="moderation" variant="neon" {...props} />
);

export const ProjectSpinner = (props) => (
  <LoadingSpinner module="project" variant="module" {...props} />
);

export const AnalyticsSpinner = (props) => (
  <LoadingSpinner module="analytics" variant="dots" {...props} />
);

export const SystemSpinner = (props) => (
  <LoadingSpinner module="system" variant="module" {...props} />
);

export default LoadingSpinner;