import React from 'react';
import { motion } from 'framer-motion';

const AnimatedScale = ({ size = 48, className = '', ...props }) => {
  return (
    <motion.div
      className={`flex items-center justify-center ${className}`}
      whileHover={{ scale: 1.1 }}
      transition={{ duration: 0.3 }}
      {...props}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 48 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="text-primary-600 dark:text-primary-400"
      >
        {/* Центральная стойка */}
        <motion.line
          x1="24"
          y1="8"
          x2="24"
          y2="42"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
        />
        
        {/* Верхняя часть весов - округлая */}
        <motion.circle
          cx="24"
          cy="8"
          r="4"
          fill="currentColor"
          opacity="0.8"
          animate={{ 
            scale: [1, 1.05, 1]
          }}
          transition={{ 
            duration: 4,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        
        {/* Горизонтальная перекладина */}
        <motion.line
          x1="6"
          y1="18"
          x2="42"
          y2="18"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
          animate={{ 
            rotate: [0, 1, -1, 0],
          }}
          transition={{ 
            duration: 3,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        
        {/* Соединение стойки с перекладиной */}
        <motion.line
          x1="24"
          y1="8"
          x2="24"
          y2="18"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
        />
        
        {/* Левая чаша */}
        <motion.g
          animate={{ 
            y: [0, -3, 3, 0],
            rotate: [0, 2, -2, 0]
          }}
          transition={{ 
            duration: 2.5,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 0.2
          }}
        >
          {/* Подвес левой чаши */}
          <motion.line
            x1="6"
            y1="18"
            x2="6"
            y2="24"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            animate={{ 
              rotate: [0, 2, -2, 0]
            }}
            transition={{ 
              duration: 2.5,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 0.2
            }}
          />
          {/* Сама левая чаша */}
          <motion.ellipse
            cx="6"
            cy="28"
            rx="6"
            ry="3"
            fill="currentColor"
            opacity="0.8"
            animate={{ 
              y: [0, -3, 3, 0]
            }}
            transition={{ 
              duration: 2.5,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 0.2
            }}
          />
          {/* Внутренняя часть левой чаши */}
          <motion.ellipse
            cx="6"
            cy="28"
            rx="4"
            ry="2"
            fill="currentColor"
            opacity="0.4"
            animate={{ 
              y: [0, -3, 3, 0]
            }}
            transition={{ 
              duration: 2.5,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 0.2
            }}
          />
        </motion.g>
        
        {/* Правая чаша */}
        <motion.g
          animate={{ 
            y: [0, 3, -3, 0],
            rotate: [0, -2, 2, 0]
          }}
          transition={{ 
            duration: 2.5,
            repeat: Infinity,
            ease: "easeInOut",
            delay: 0.2
          }}
        >
          {/* Подвес правой чаши */}
          <motion.line
            x1="42"
            y1="18"
            x2="42"
            y2="24"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            animate={{ 
              rotate: [0, -2, 2, 0]
            }}
            transition={{ 
              duration: 2.5,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 0.2
            }}
          />
          {/* Сама правая чаша */}
          <motion.ellipse
            cx="42"
            cy="28"
            rx="6"
            ry="3"
            fill="currentColor"
            opacity="0.8"
            animate={{ 
              y: [0, 3, -3, 0]
            }}
            transition={{ 
              duration: 2.5,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 0.2
            }}
          />
          {/* Внутренняя часть правой чаши */}
          <motion.ellipse
            cx="42"
            cy="28"
            rx="4"
            ry="2"
            fill="currentColor"
            opacity="0.4"
            animate={{ 
              y: [0, 3, -3, 0]
            }}
            transition={{ 
              duration: 2.5,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 0.2
            }}
          />
        </motion.g>
        
        {/* Основание */}
        <motion.rect
          x="18"
          y="40"
          width="12"
          height="6"
          rx="3"
          fill="currentColor"
          opacity="0.7"
          animate={{ 
            scale: [1, 1.02, 1]
          }}
          transition={{ 
            duration: 4,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        
        {/* Декоративные элементы на основании */}
        <motion.rect
          x="20"
          y="42"
          width="8"
          height="2"
          rx="1"
          fill="currentColor"
          opacity="0.5"
          animate={{ 
            scale: [1, 1.02, 1]
          }}
          transition={{ 
            duration: 4,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      </svg>
    </motion.div>
  );
};

export default AnimatedScale;
