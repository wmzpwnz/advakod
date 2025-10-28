import React from 'react';
import { motion } from 'framer-motion';
import useIntersectionObserver from '../hooks/useIntersectionObserver';

/**
 * AnimatedSection component with staggered animations
 * Wraps content and animates it when it enters the viewport
 */
const AnimatedSection = ({ 
  children, 
  className = '',
  delay = 0,
  duration = 0.6,
  staggerChildren = 0.1,
  animationType = 'fadeUp',
  triggerOnce = true,
  threshold = 0.1
}) => {
  const { ref, hasIntersected } = useIntersectionObserver({
    threshold,
    triggerOnce
  });

  // Animation variants for different types
  const animationVariants = {
    fadeUp: {
      hidden: { 
        opacity: 0, 
        y: 50 
      },
      visible: { 
        opacity: 1, 
        y: 0,
        transition: {
          duration,
          delay,
          ease: [0.25, 0.46, 0.45, 0.94] // Custom easing for smooth motion
        }
      }
    },
    fadeIn: {
      hidden: { 
        opacity: 0 
      },
      visible: { 
        opacity: 1,
        transition: {
          duration,
          delay,
          ease: 'easeOut'
        }
      }
    },
    fadeLeft: {
      hidden: { 
        opacity: 0, 
        x: -50 
      },
      visible: { 
        opacity: 1, 
        x: 0,
        transition: {
          duration,
          delay,
          ease: [0.25, 0.46, 0.45, 0.94]
        }
      }
    },
    fadeRight: {
      hidden: { 
        opacity: 0, 
        x: 50 
      },
      visible: { 
        opacity: 1, 
        x: 0,
        transition: {
          duration,
          delay,
          ease: [0.25, 0.46, 0.45, 0.94]
        }
      }
    },
    scale: {
      hidden: { 
        opacity: 0, 
        scale: 0.8 
      },
      visible: { 
        opacity: 1, 
        scale: 1,
        transition: {
          duration,
          delay,
          ease: [0.25, 0.46, 0.45, 0.94]
        }
      }
    },
    stagger: {
      hidden: { 
        opacity: 0 
      },
      visible: {
        opacity: 1,
        transition: {
          staggerChildren,
          delayChildren: delay
        }
      }
    }
  };

  // Get the selected animation variant
  const selectedVariant = animationVariants[animationType] || animationVariants.fadeUp;

  return (
    <motion.div
      ref={ref}
      initial="hidden"
      animate={hasIntersected ? "visible" : "hidden"}
      variants={selectedVariant}
      className={className}
    >
      {children}
    </motion.div>
  );
};

/**
 * AnimatedItem component for use within staggered animations
 * Use this as a child of AnimatedSection with animationType="stagger"
 */
export const AnimatedItem = ({ 
  children, 
  className = '',
  animationType = 'fadeUp'
}) => {
  const itemVariants = {
    fadeUp: {
      hidden: { opacity: 0, y: 20 },
      visible: { opacity: 1, y: 0 }
    },
    fadeIn: {
      hidden: { opacity: 0 },
      visible: { opacity: 1 }
    },
    scale: {
      hidden: { opacity: 0, scale: 0.9 },
      visible: { opacity: 1, scale: 1 }
    }
  };

  return (
    <motion.div
      variants={itemVariants[animationType] || itemVariants.fadeUp}
      className={className}
    >
      {children}
    </motion.div>
  );
};

export default AnimatedSection;
