import React from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../contexts/ThemeContext';

const EnhancedButton = ({ 
  children, 
  variant = 'primary', 
  module = null,
  size = 'md', 
  disabled = false,
  loading = false,
  icon = null,
  className = '',
  onClick,
  ...props 
}) => {
  const { getModuleColor, isDark } = useTheme();

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

  // Get module colors if module is specified
  const moduleColor = module ? getModuleColor(module) : null;
  const moduleColorLight = module ? getModuleColor(module, 'light') : null;
  const moduleColorDark = module ? getModuleColor(module, 'dark') : null;

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
    module: module ? `
      text-white shadow-lg hover:shadow-xl
      border border-opacity-30
    ` : `
      bg-gradient-to-r from-gray-500 to-gray-600 
      hover:from-gray-600 hover:to-gray-700 
      text-white shadow-lg hover:shadow-xl
    `,
    'module-outline': module ? `
      bg-transparent border-2 
      hover:bg-opacity-10 shadow-md hover:shadow-lg
    ` : `
      bg-transparent border-2 border-gray-400 
      text-gray-600 dark:text-gray-300 
      hover:bg-gray-100 dark:hover:bg-gray-800
    `,
    'module-neon': module ? `
      backdrop-blur-lg border-2 
      text-white shadow-xl hover:shadow-2xl
      neon-glow-purple
    ` : `
      bg-gray-900/80 backdrop-blur-lg border-2 border-purple-400/30
      text-white shadow-xl hover:shadow-2xl
      neon-glow-purple
    `,
  };

  // Dynamic styles based on module
  const getModuleStyles = () => {
    if (!module) return {};

    switch (variant) {
      case 'module':
        return {
          background: `linear-gradient(135deg, ${moduleColor}, ${moduleColorDark})`,
          borderColor: `${moduleColor}4D`, // 30% opacity
        };
      case 'module-outline':
        return {
          borderColor: moduleColor,
          color: moduleColor,
          '--hover-bg': `${moduleColor}1A`, // 10% opacity
        };
      case 'module-neon':
        return {
          background: `linear-gradient(135deg, ${moduleColor}20, ${moduleColorDark}30)`,
          borderColor: `${moduleColor}80`, // 50% opacity
          boxShadow: `0 0 20px ${moduleColor}40, 0 4px 16px ${moduleColor}20`,
        };
      default:
        return {};
    }
  };

  const buttonClasses = `
    ${baseClasses}
    ${sizeClasses[size]}
    ${variantClasses[variant]}
    ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
  `;

  const getHoverAnimation = () => {
    if (disabled) return {};
    
    if (variant === 'module-neon') {
      return { 
        scale: 1.05,
        boxShadow: module 
          ? `0 0 30px ${moduleColor}60, 0 8px 24px ${moduleColor}30`
          : "0 0 30px rgba(139, 92, 246, 0.6), 0 8px 24px rgba(139, 92, 246, 0.3)"
      };
    }
    
    return { scale: 1.05 };
  };

  return (
    <motion.button
      className={buttonClasses}
      style={getModuleStyles()}
      whileHover={getHoverAnimation()}
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
      
      {/* Neon glow effect for module-neon variant */}
      {variant === 'module-neon' && !disabled && (
        <div 
          className="absolute inset-0 rounded-xl opacity-0 hover:opacity-100 transition-opacity duration-300"
          style={{
            background: module 
              ? `linear-gradient(45deg, transparent 30%, ${moduleColorLight}40 50%, transparent 70%)`
              : 'linear-gradient(45deg, transparent 30%, rgba(167, 139, 250, 0.4) 50%, transparent 70%)',
            animation: 'shimmerSweep 2s infinite',
          }}
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

export default EnhancedButton;