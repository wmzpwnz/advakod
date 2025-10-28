import React from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../contexts/ThemeContext';

const ModuleCard = ({ 
  children, 
  module = 'default',
  variant = 'default',
  hover = true,
  className = '',
  onClick,
  ...props 
}) => {
  const { getModuleColor, isDark } = useTheme();

  const baseClasses = `
    rounded-2xl p-6 transition-all duration-300 cursor-pointer
    ${className}
  `;

  // Get module-specific colors
  const moduleColor = getModuleColor(module);
  const moduleColorLight = getModuleColor(module, 'light');
  const moduleColorDark = getModuleColor(module, 'dark');

  const variantClasses = {
    default: `
      bg-white/80 dark:bg-gray-800/80 
      backdrop-blur-sm border border-gray-200/50 dark:border-gray-700/50 
      shadow-lg hover:shadow-xl
    `,
    glass: `
      bg-white/10 backdrop-blur-md border border-white/20 
      shadow-xl hover:bg-white/20 hover:shadow-2xl
    `,
    module: `
      bg-gradient-to-br from-white/90 via-white/80 to-white/70
      dark:bg-gradient-to-br dark:from-gray-800/90 dark:via-gray-800/80 dark:to-gray-900/70
      backdrop-blur-lg border-2
      shadow-lg hover:shadow-2xl
      ${isDark ? 'neon-glow-purple' : ''}
    `,
    'module-neon': `
      bg-gradient-to-br from-gray-900/60 via-gray-800/70 to-gray-900/80
      backdrop-blur-xl border-2
      neon-glow-purple neon-pulse
      shadow-[0_8px_32px_rgba(0,0,0,0.4)]
      hover:shadow-[0_16px_48px_rgba(0,0,0,0.6)]
    `,
  };

  // Dynamic styles based on module
  const getModuleStyles = () => {
    if (variant === 'module' || variant === 'module-neon') {
      const borderOpacity = variant === 'module-neon' ? '0.6' : '0.3';
      const shadowOpacity = variant === 'module-neon' ? '0.4' : '0.2';
      
      return {
        borderColor: `${moduleColor}${Math.round(255 * parseFloat(borderOpacity)).toString(16).padStart(2, '0')}`,
        boxShadow: variant === 'module-neon' 
          ? `0 8px 32px ${moduleColor}${Math.round(255 * 0.2).toString(16).padStart(2, '0')}, 0 0 20px ${moduleColor}${Math.round(255 * 0.15).toString(16).padStart(2, '0')}`
          : `0 4px 16px ${moduleColor}${Math.round(255 * 0.1).toString(16).padStart(2, '0')}`,
      };
    }
    return {};
  };

  const cardClasses = `
    ${baseClasses}
    ${variantClasses[variant]}
    ${hover ? 'hover:scale-105' : ''}
  `;

  // Enhanced hover animation for module variants
  const getHoverAnimation = () => {
    if (!hover) return {};
    
    if (variant === 'module-neon') {
      return {
        y: -8,
        scale: 1.02,
        transition: {
          duration: 0.3,
          ease: "easeOut"
        }
      };
    }
    
    if (variant === 'module') {
      return {
        y: -6,
        scale: 1.01,
        transition: {
          duration: 0.3,
          ease: "easeOut"
        }
      };
    }
    
    return { y: -5 };
  };

  return (
    <motion.div
      className={cardClasses}
      style={getModuleStyles()}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={getHoverAnimation()}
      transition={{ duration: 0.3 }}
      onClick={onClick}
      {...props}
    >
      {/* Module accent line */}
      {(variant === 'module' || variant === 'module-neon') && (
        <div 
          className="absolute top-0 left-0 right-0 h-1 rounded-t-2xl"
          style={{ backgroundColor: moduleColor }}
        />
      )}
      
      {/* Shimmer effect for neon variant */}
      {variant === 'module-neon' && (
        <div className="absolute inset-0 rounded-2xl overflow-hidden">
          <div 
            className="absolute inset-0 opacity-20 animate-pulse"
            style={{
              background: `linear-gradient(45deg, transparent 30%, ${moduleColorLight} 50%, transparent 70%)`,
            }}
          />
        </div>
      )}
      
      <div className="relative z-10">
        {children}
      </div>
    </motion.div>
  );
};

export default ModuleCard;