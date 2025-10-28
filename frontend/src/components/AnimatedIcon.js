import React from 'react';
import { motion } from 'framer-motion';

const AnimatedIcon = ({ 
  icon: Icon, 
  isActive = false, 
  size = 'md',
  color = 'default',
  animation = 'scale',
  className = '',
  ...props 
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
    xl: 'w-8 h-8'
  };

  const colorClasses = {
    default: 'text-gray-600 dark:text-gray-300',
    primary: 'text-primary-600 dark:text-primary-400',
    success: 'text-success-600 dark:text-success-400',
    warning: 'text-warning-600 dark:text-warning-400',
    error: 'text-error-600 dark:text-error-400',
    white: 'text-white'
  };

  const animationVariants = {
    scale: {
      scale: isActive ? 1.1 : 1,
      transition: { duration: 0.2 }
    },
    rotate: {
      rotate: isActive ? 360 : 0,
      transition: { duration: 0.3 }
    },
    bounce: {
      y: isActive ? -2 : 0,
      transition: { duration: 0.2 }
    },
    pulse: {
      scale: isActive ? [1, 1.2, 1] : 1,
      transition: { duration: 0.6, repeat: isActive ? Infinity : 0 }
    },
    glow: {
      boxShadow: isActive 
        ? '0 0 20px rgba(59, 130, 246, 0.5)' 
        : '0 0 0px rgba(59, 130, 246, 0)',
      transition: { duration: 0.3 }
    }
  };

  return (
    <motion.div
      className={`
        flex items-center justify-center p-2 rounded-lg
        ${isActive ? 'bg-primary-100 dark:bg-primary-900/30' : 'bg-gray-100 dark:bg-gray-700'}
        transition-colors duration-200
        ${className}
      `}
      variants={animationVariants[animation]}
      animate={animationVariants[animation]}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      {...props}
    >
      <Icon 
        className={`
          ${sizeClasses[size]}
          ${colorClasses[color]}
          transition-colors duration-200
        `}
      />
    </motion.div>
  );
};

export default AnimatedIcon;
