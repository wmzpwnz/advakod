import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const SmartSearchInput = ({ 
  onSearch, 
  placeholder = "Задайте вопрос AI-юристу...",
  className = "" 
}) => {
  const [query, setQuery] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [typingPlaceholder, setTypingPlaceholder] = useState('');
  const [isTyping, setIsTyping] = useState(true);
  const inputRef = useRef(null);

  // Animated typing placeholder effect
  useEffect(() => {
    if (query.length > 0) {
      setIsTyping(false);
      return;
    }

    setIsTyping(true);
    let currentIndex = 0;
    const typingInterval = setInterval(() => {
      if (currentIndex <= placeholder.length) {
        setTypingPlaceholder(placeholder.slice(0, currentIndex));
        currentIndex++;
      } else {
        // Pause at the end before restarting
        setTimeout(() => {
          currentIndex = 0;
          setTypingPlaceholder('');
        }, 2000);
      }
    }, 100);

    return () => clearInterval(typingInterval);
  }, [placeholder, query]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && onSearch) {
      onSearch(query);
    }
  };

  const handleChange = (e) => {
    setQuery(e.target.value);
  };

  return (
    <motion.form
      onSubmit={handleSubmit}
      className={`relative w-full max-w-3xl mx-auto ${className}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="relative">
        {/* Input field with glassmorphism and neon glow */}
        <motion.div
          className="relative"
          animate={{
            scale: isFocused ? 1.02 : isHovered ? 1.01 : 1,
          }}
          transition={{ duration: 0.3, ease: "easeOut" }}
        >
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={handleChange}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            className={`
              w-full px-6 py-5 text-lg
              bg-gray-900/80 backdrop-blur-xl
              dark:bg-gray-900/80
              light:bg-gradient-to-r light:from-blue-500/10 light:via-purple-500/10 light:to-cyan-500/10
              border-2 rounded-2xl
              text-gray-100 placeholder-gray-500
              dark:text-gray-100 dark:placeholder-gray-500
              light:text-gray-900 light:placeholder-blue-400
              transition-all duration-300 ease-out
              outline-none
              neon-glow-purple
              ${isFocused ? 'neon-focus' : ''}
              ${isHovered && !isFocused ? 'neon-hover' : ''}
              min-h-[60px] touch-manipulation
              md:min-h-[auto] md:py-5
            `}
            placeholder={isTyping && query.length === 0 ? typingPlaceholder : ''}
            aria-label="Поиск юридической консультации"
            aria-describedby="search-hint"
            role="searchbox"
          />
          <span id="search-hint" className="sr-only">
            Введите ваш юридический вопрос для получения консультации от AI-юриста
          </span>

          {/* Animated border gradient overlay */}
          <motion.div
            className="absolute inset-0 rounded-2xl pointer-events-none"
            style={{
              background: 'linear-gradient(45deg, #8B5CF6, #06B6D4, #A78BFA, #22D3EE)',
              backgroundSize: '300% 300%',
              padding: '2px',
              WebkitMask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
              WebkitMaskComposite: 'xor',
              maskComposite: 'exclude',
            }}
            animate={{
              backgroundPosition: isFocused 
                ? ['0% 50%', '100% 50%', '0% 50%']
                : ['0% 50%'],
              opacity: isFocused ? 1 : isHovered ? 0.6 : 0,
            }}
            transition={{
              backgroundPosition: {
                duration: isFocused ? 2 : 4,
                repeat: isFocused ? Infinity : 0,
                ease: "easeInOut"
              },
              opacity: { duration: 0.3 }
            }}
          />

          {/* Shimmer sweep effect on hover */}
          <AnimatePresence>
            {isHovered && !isFocused && (
              <motion.div
                className="absolute inset-0 rounded-2xl pointer-events-none overflow-hidden"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <motion.div
                  className="absolute inset-0"
                  style={{
                    background: 'linear-gradient(90deg, transparent, rgba(139, 92, 246, 0.3), rgba(6, 182, 212, 0.3), transparent)',
                  }}
                  initial={{ x: '-100%' }}
                  animate={{ x: '100%' }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Search icon */}
          <div className="absolute right-4 top-1/2 transform -translate-y-1/2 pointer-events-none">
            <motion.svg
              className="w-6 h-6 text-gray-400"
              animate={{
                color: isFocused ? '#8B5CF6' : isHovered ? '#06B6D4' : '#9CA3AF',
                scale: isFocused ? 1.1 : 1,
              }}
              transition={{ duration: 0.3 }}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </motion.svg>
          </div>
        </motion.div>

        {/* Typing cursor animation */}
        <AnimatePresence>
          {isTyping && query.length === 0 && (
            <motion.span
              className="absolute left-6 top-1/2 transform -translate-y-1/2 text-lg text-gray-400 pointer-events-none"
              style={{ marginLeft: `${typingPlaceholder.length * 0.6}ch` }}
              initial={{ opacity: 0 }}
              animate={{ opacity: [1, 0, 1] }}
              exit={{ opacity: 0 }}
              transition={{
                opacity: { duration: 0.8, repeat: Infinity, ease: "easeInOut" }
              }}
            >
              |
            </motion.span>
          )}
        </AnimatePresence>
      </div>

      {/* Glow effect underneath when focused */}
      <AnimatePresence>
        {isFocused && (
          <motion.div
            className="absolute -inset-1 rounded-2xl blur-xl pointer-events-none -z-10"
            style={{
              background: 'radial-gradient(circle, rgba(139, 92, 246, 0.4), rgba(6, 182, 212, 0.2), transparent)',
            }}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ 
              opacity: [0.5, 0.8, 0.5],
              scale: 1,
            }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{
              opacity: { duration: 2, repeat: Infinity, ease: "easeInOut" },
              scale: { duration: 0.3 }
            }}
          />
        )}
      </AnimatePresence>
    </motion.form>
  );
};

export default SmartSearchInput;
