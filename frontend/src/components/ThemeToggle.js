import React, { useState, useEffect } from 'react';
import { Sun, Moon } from 'lucide-react';
import { motion } from 'framer-motion';

const ThemeToggle = () => {
  const [theme, setTheme] = useState('dark');

  useEffect(() => {
    // Проверяем сохраненную тему
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);
    applyTheme(savedTheme);
  }, []);

  const applyTheme = (newTheme) => {
    const root = document.documentElement;
    
    if (newTheme === 'light') {
      root.classList.add('light');
      root.classList.remove('dark');
    } else {
      root.classList.add('dark');
      root.classList.remove('light');
    }
    
    localStorage.setItem('theme', newTheme);
  };

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    applyTheme(newTheme);
  };

  return (
    <motion.button
      onClick={toggleTheme}
      className={`
        relative w-14 h-4 md:w-16 md:h-6 rounded-full p-0 md:p-0 transition-all duration-300
        flex items-center justify-center
        ${theme === 'light' 
          ? 'bg-gradient-to-r from-blue-500 to-purple-500' 
          : 'bg-gray-700'
        }
        shadow-md hover:shadow-lg
        focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500
      `}
      whileTap={{ scale: 0.95 }}
      aria-label={theme === 'dark' ? 'Переключить на светлую тему' : 'Переключить на темную тему'}
    >
      <motion.div
        className="absolute top-1/2 -translate-y-1/2 w-4 h-4 md:w-6 md:h-6 rounded-full bg-white shadow-lg flex items-center justify-center"
        animate={{
          left: theme === 'light' 
            ? 'calc(100% - 1.25rem)' // Для w-14 (56px): 56px - 16px (w-4) = 40px от левого края
            : '0.25rem' // 4px от левого края
        }}
        transition={{
          type: 'spring',
          stiffness: 500,
          damping: 30
        }}
      >
        {theme === 'light' ? (
          <Sun className="w-3 h-3 md:w-4 md:h-4 text-yellow-500" />
        ) : (
          <Moon className="w-3 h-3 md:w-4 md:h-4 text-indigo-500" />
        )}
      </motion.div>
    </motion.button>
  );
};

export default ThemeToggle;
