import React from 'react';
import { motion } from 'framer-motion';

const GlassCard = ({ 
  children, 
  variant = 'default',
  hover = true,
  className = '',
  ...props 
}) => {
  const baseClasses = `
    rounded-2xl p-6 transition-all duration-300
    ${className}
  `;

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
    glassStrong: `
      bg-white/20 backdrop-blur-lg border border-white/30 
      shadow-xl hover:bg-white/30 hover:shadow-2xl
    `,
    neo: `
      bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900 
      border border-gray-200/50 dark:border-gray-700/50 
      shadow-lg
    `,
    neon: `
      bg-white/90 dark:bg-gray-800/90 
      border border-primary-200 dark:border-primary-700 
      shadow-lg hover:shadow-xl
      neon-glow hover:neon-glow
    `,
    'neon-glass': `
      bg-gradient-to-br from-blue-500/10 via-purple-500/10 to-cyan-500/10
      dark:bg-gray-900/60 
      backdrop-blur-lg 
      border border-blue-400/30
      neon-border-flow
      shadow-[0_8px_32px_rgba(0,122,255,0.2),0_4px_16px_rgba(191,90,242,0.15)]
      hover:shadow-[0_12px_48px_rgba(0,122,255,0.3),0_8px_32px_rgba(191,90,242,0.25)]
    `,
    'neon-purple': `
      bg-gradient-to-br from-purple-500/10 via-pink-500/10 to-purple-500/10
      dark:bg-gray-900/70 
      backdrop-blur-xl
      border border-purple-400/30
      neon-glow-purple neon-pulse
      shadow-[0_8px_32px_rgba(191,90,242,0.25),0_4px_16px_rgba(255,45,85,0.15)]
      hover:shadow-[0_16px_56px_rgba(191,90,242,0.4),0_8px_32px_rgba(255,45,85,0.25)]
    `,
    'neon-blue': `
      bg-gradient-to-br from-blue-500/10 via-cyan-500/10 to-blue-500/10
      dark:bg-gray-900/70 
      backdrop-blur-xl
      border border-blue-400/30
      shadow-[0_8px_32px_rgba(0,122,255,0.25),0_4px_16px_rgba(50,173,230,0.15)]
      hover:shadow-[0_16px_56px_rgba(0,122,255,0.4),0_8px_32px_rgba(50,173,230,0.25)]
    `,
    'neon-cyan': `
      bg-gradient-to-br from-cyan-500/10 via-teal-500/10 to-cyan-500/10
      dark:bg-gray-900/70 
      backdrop-blur-xl
      border border-cyan-400/30
      shadow-[0_8px_32px_rgba(50,173,230,0.25),0_4px_16px_rgba(0,199,190,0.15)]
      hover:shadow-[0_16px_56px_rgba(50,173,230,0.4),0_8px_32px_rgba(0,199,190,0.25)]
    `,
    'neon-pink': `
      bg-gradient-to-br from-pink-500/10 via-rose-500/10 to-pink-500/10
      dark:bg-gray-900/70 
      backdrop-blur-xl
      border border-pink-400/30
      shadow-[0_8px_32px_rgba(255,45,85,0.25),0_4px_16px_rgba(255,55,95,0.15)]
      hover:shadow-[0_16px_56px_rgba(255,45,85,0.4),0_8px_32px_rgba(255,55,95,0.25)]
    `,
    'neon-orange': `
      bg-gradient-to-br from-orange-500/10 via-amber-500/10 to-orange-500/10
      dark:bg-gray-900/70 
      backdrop-blur-xl
      border border-orange-400/30
      shadow-[0_8px_32px_rgba(255,149,0,0.25),0_4px_16px_rgba(255,159,10,0.15)]
      hover:shadow-[0_16px_56px_rgba(255,149,0,0.4),0_8px_32px_rgba(255,159,10,0.25)]
    `,
    'neon-green': `
      bg-gradient-to-br from-green-500/10 via-emerald-500/10 to-green-500/10
      dark:bg-gray-900/70 
      backdrop-blur-xl
      border border-green-400/30
      shadow-[0_8px_32px_rgba(52,199,89,0.25),0_4px_16px_rgba(48,209,88,0.15)]
      hover:shadow-[0_16px_56px_rgba(52,199,89,0.4),0_8px_32px_rgba(48,209,88,0.25)]
    `
  };

  const cardClasses = `
    ${baseClasses}
    ${variantClasses[variant]}
    ${hover ? 'hover:scale-105' : ''}
  `;

  // Enhanced hover animation for neon variants
  const getHoverAnimation = () => {
    if (!hover) return {};
    
    if (variant === 'neon-glass' || variant === 'neon-purple') {
      return {
        y: -8,
        scale: 1.02,
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
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={getHoverAnimation()}
      transition={{ duration: 0.3 }}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export default GlassCard;
