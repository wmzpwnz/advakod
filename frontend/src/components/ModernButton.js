import React from 'react';
import { motion } from 'framer-motion';

const ModernButton = ({ 
  children, 
  variant = 'primary', 
  size = 'md', 
  disabled = false,
  loading = false,
  icon = null,
  className = '',
  onClick,
  ...props 
}) => {
  const baseClasses = `
    relative overflow-hidden rounded-xl font-medium transition-all duration-300
    focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500
    disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none
    ${className}
  `;

  const sizeClasses = {
    sm: 'px-4 py-2 text-sm',
    md: 'px-6 py-3 text-base',
    lg: 'px-8 py-4 text-lg',
    xl: 'px-10 py-5 text-xl'
  };

  const variantClasses = {
    primary: `
      bg-gradient-to-r from-primary-500 to-primary-600 
      hover:from-primary-600 hover:to-primary-700 
      text-white shadow-lg hover:shadow-xl
    `,
    secondary: `
      bg-white dark:bg-gray-800 
      hover:bg-gray-50 dark:hover:bg-gray-700 
      text-gray-700 dark:text-gray-300 
      border border-gray-300 dark:border-gray-600 
      hover:shadow-lg
    `,
    ghost: `
      text-gray-600 dark:text-gray-300 
      hover:text-gray-900 dark:hover:text-white 
      hover:bg-gray-100 dark:hover:bg-gray-800
    `,
    glass: `
      bg-white/10 backdrop-blur-md border border-white/20 
      text-white hover:bg-white/20
    `,
    'glass-primary': `
      btn-glass-primary
    `,
    'glass-secondary': `
      btn-glass-secondary
    `,
    'glass-success': `
      btn-glass-success
    `,
    'glass-danger': `
      btn-glass-danger
    `,
    'glass-ghost': `
      btn-glass-ghost
    `,
    success: `
      bg-gradient-to-r from-success-500 to-success-600 
      hover:from-success-600 hover:to-success-700 
      text-white shadow-lg hover:shadow-xl
    `,
    warning: `
      bg-gradient-to-r from-warning-500 to-warning-600 
      hover:from-warning-600 hover:to-warning-700 
      text-white shadow-lg hover:shadow-xl
    `,
    error: `
      bg-gradient-to-r from-error-500 to-error-600 
      hover:from-error-600 hover:to-error-700 
      text-white shadow-lg hover:shadow-xl
    `
  };

  const buttonClasses = `
    ${baseClasses}
    ${sizeClasses[size]}
    ${variantClasses[variant]}
    ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
  `;

  return (
    <motion.button
      className={buttonClasses}
      whileHover={!disabled ? { scale: 1.05 } : {}}
      whileTap={!disabled ? { scale: 0.95 } : {}}
      onClick={onClick}
      disabled={disabled || loading}
      {...props}
    >
      {/* Shimmer effect */}
      {!disabled && (
        <motion.div
          className="absolute inset-0 bg-white/20"
          initial={{ x: '-100%' }}
          whileHover={{ x: '100%' }}
          transition={{ duration: 0.6 }}
        />
      )}
      
      {/* Content */}
      <span className="relative z-10 flex items-center justify-center space-x-2">
        {loading && (
          <motion.div
            className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          />
        )}
        {!loading && icon && (
          <span className="flex items-center">
            {icon}
          </span>
        )}
        <span>{children}</span>
      </span>
    </motion.button>
  );
};

export default ModernButton;
