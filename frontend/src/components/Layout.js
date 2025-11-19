import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useAdmin } from '../contexts/AdminContext';
import { motion } from 'framer-motion';
import { User, LogOut, Menu, X, Settings } from 'lucide-react';
import { useState } from 'react';
import ThemeToggle from './ThemeToggle';
import TokenBalance from './TokenBalance';
import ModernButton from './ModernButton';
import AnimatedScale from './AnimatedScale';

const Layout = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const { isAdmin } = useAdmin();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navigation = [
    { name: 'Главная', href: '/' },
    { name: 'Тарифы', href: '/pricing' },
    { name: 'Чат', href: '/chat' },
  ];

  const isActive = (path) => location.pathname === path;
  
  // Скрываем футер в чате
  const isChatPage = location.pathname === '/chat';

  return (
    <div className={`min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200 overflow-x-hidden ${isChatPage ? 'flex flex-col h-screen overflow-hidden' : ''}`}>
      {/* Header */}
      <header className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-md shadow-lg border-b border-gray-200/50 dark:border-gray-700/50 transition-colors duration-200 sticky top-0 z-50 overflow-x-hidden">
        <div className="max-w-7xl mx-auto px-3 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-14 sm:h-16 gap-2">
            {/* Logo */}
            <div className="flex items-center flex-shrink-0">
              <Link to="/" className="flex items-center space-x-1 sm:space-x-2">
                <AnimatedScale size={28} className="sm:w-8 sm:h-8" />
                <span className="text-base sm:text-lg md:text-xl font-bold gradient-text animate-pulse-glow">АДВАКОД</span>
              </Link>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex space-x-2 flex-1 justify-center">
              {navigation.map((item) => (
                <motion.div
                  key={item.name}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Link
                    to={item.href}
                    className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300 ${
                      isActive(item.href)
                        ? 'text-primary-600 bg-primary-50/80 dark:bg-primary-900/30 shadow-md'
                        : 'text-gray-700 dark:text-gray-300 hover:text-primary-600 hover:bg-gray-50/80 dark:hover:bg-gray-700/80 hover:shadow-md'
                    }`}
                  >
                    {item.name}
                  </Link>
                </motion.div>
              ))}
            </nav>

            {/* User Menu - Desktop */}
            <div className="hidden md:flex items-center space-x-2 lg:space-x-4 flex-shrink-0">
              {/* Theme Toggle */}
              <ThemeToggle />
              
              {isAuthenticated ? (
                <>
                  {/* Баланс токенов */}
                  <TokenBalance />
                  
                  <Link
                    to="/profile"
                    className="flex items-center space-x-2 text-gray-700 hover:text-primary-600"
                    title={user?.username}
                  >
                    <User className="h-5 w-5" />
                    <span className="hidden lg:block">{user?.username}</span>
                  </Link>
                  
                  {isAdmin && !isChatPage && (
                    <Link
                      to="/admin"
                      className="flex items-center space-x-2 text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 px-2 py-1 rounded-md hover:bg-red-50 dark:hover:bg-red-900/30 border border-red-200 dark:border-red-800"
                      title="🛡️ Админ панель (безопасный режим)"
                    >
                      <Settings className="h-5 w-5" />
                      <span className="hidden lg:block">🛡️ Админ</span>
                    </Link>
                  )}
                  
                  <button
                    onClick={logout}
                    className="flex items-center space-x-2 text-gray-700 dark:text-gray-300 hover:text-red-500 dark:hover:text-red-400 transition-colors duration-200 px-2 py-1 rounded-md hover:bg-red-50 dark:hover:bg-red-900/20"
                    title="Выйти"
                  >
                    <LogOut className="h-5 w-5" />
                    <span className="hidden lg:block">Выйти</span>
                  </button>
                </>
              ) : (
                <>
                  <ModernButton
                    variant="glass-ghost"
                    size="sm"
                  >
                    <Link to="/login" className="flex items-center space-x-2">
                      <span>Войти</span>
                    </Link>
                  </ModernButton>
                  <ModernButton
                    variant="glass-primary"
                    size="sm"
                  >
                    <Link to="/register" className="flex items-center space-x-2">
                      <span>Регистрация</span>
                    </Link>
                  </ModernButton>
                </>
              )}
            </div>

            {/* Mobile menu button - показываем первым на мобильных */}
            <div className="md:hidden flex items-center space-x-2 flex-shrink-0">
              {/* Theme Toggle на мобильных */}
              <ThemeToggle />
              
              {/* Гамбургер меню */}
              <button
                className="p-2 rounded-md text-gray-700 dark:text-gray-300 hover:text-primary-600 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                aria-label="Toggle menu"
              >
                {mobileMenuOpen ? (
                  <X className="h-5 w-5" />
                ) : (
                  <Menu className="h-5 w-5" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <motion.div 
            className="md:hidden border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            <div className="px-2 pt-2 pb-3 space-y-1">
              {navigation.map((item) => (
                <motion.div
                  key={item.name}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Link
                    to={item.href}
                    className={`block px-3 py-2 rounded-md text-base font-medium transition-colors ${
                      isActive(item.href)
                        ? 'text-primary-600 bg-primary-50 dark:bg-primary-900/30'
                        : 'text-gray-700 dark:text-gray-300 hover:text-primary-600 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    {item.name}
                  </Link>
                </motion.div>
              ))}
              
              {/* Mobile User Actions */}
              {isAuthenticated ? (
                <div className="border-t border-gray-200 dark:border-gray-700 pt-2 mt-2">
                  {/* Баланс токенов в мобильном меню */}
                  <div className="px-3 py-2 mb-2">
                    <TokenBalance />
                  </div>
                  <Link
                    to="/profile"
                    className="block px-3 py-2 rounded-md text-base font-medium text-gray-700 dark:text-gray-300 hover:text-primary-600 hover:bg-gray-50 dark:hover:bg-gray-700"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Профиль
                  </Link>
                  {isAdmin && (
                    <Link
                      to="/admin"
                      className="block px-3 py-2 rounded-md text-base font-medium text-red-600 dark:text-red-400 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/30 border border-red-200 dark:border-red-800"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      <Settings className="h-4 w-4 inline mr-2" />
                      🛡️ Админ панель
                    </Link>
                  )}
                  <button
                    onClick={() => {
                      logout();
                      setMobileMenuOpen(false);
                    }}
                    className="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-gray-700 dark:text-gray-300 hover:text-red-500 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors duration-200"
                  >
                    Выйти
                  </button>
                </div>
              ) : (
                <div className="border-t border-gray-200 dark:border-gray-700 pt-2 mt-2 space-y-2">
                  <ModernButton
                    variant="glass-ghost"
                    size="md"
                    className="w-full"
                  >
                    <Link 
                      to="/login" 
                      className="flex items-center justify-center space-x-2 w-full"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      <span>Войти</span>
                    </Link>
                  </ModernButton>
                  <ModernButton
                    variant="glass-primary"
                    size="md"
                    className="w-full"
                  >
                    <Link 
                      to="/register" 
                      className="flex items-center justify-center space-x-2 w-full"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      <span>Регистрация</span>
                    </Link>
                  </ModernButton>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </header>

      {/* Main Content */}
      <main className={isChatPage ? "flex-1 min-h-0 overflow-hidden" : ""}>
        <Outlet />
      </main>

      {/* Footer - скрываем в чате */}
      {!isChatPage && (
        <motion.footer 
          className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 mt-auto overflow-x-hidden"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6 }}
        >
          <div className="max-w-7xl mx-auto py-6 sm:py-8 px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6 sm:gap-8">
              <motion.div 
                className="col-span-1 md:col-span-2"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 }}
              >
                <div className="flex items-center space-x-2 mb-4">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                  >
                    <AnimatedScale size={24} />
                  </motion.div>
                  <span className="text-lg font-bold gradient-text-modern">АДВАКОД</span>
                </div>
                <p className="body-medium text-gray-600 dark:text-gray-300">
                  Ваш персональный <span className="gradient-text-modern">AI юрист-консультант</span>. Решайте юридические вопросы 
                  в разы быстрее и дешевле на основе актуального законодательства РФ.
                </p>
              </motion.div>
              
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.2 }}
              >
                <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-4">Продукт</h3>
                <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-300">
                  <li>
                    <motion.div whileHover={{ x: 5 }}>
                      <Link to="/pricing" className="hover:text-primary-600 dark:hover:text-primary-400 transition-colors">
                        Тарифы
                      </Link>
                    </motion.div>
                  </li>
                  <li>
                    <motion.div whileHover={{ x: 5 }}>
                      <Link to="/chat" className="hover:text-primary-600 dark:hover:text-primary-400 transition-colors">
                        Чат с ИИ
                      </Link>
                    </motion.div>
                  </li>
                  <li><span className="text-gray-400 dark:text-gray-500">API (скоро)</span></li>
                </ul>
              </motion.div>
              
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.3 }}
              >
                <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-4">Поддержка</h3>
                <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-300">
                  <li><span className="text-gray-400 dark:text-gray-500">Помощь (скоро)</span></li>
                  <li><span className="text-gray-400 dark:text-gray-500">Контакты (скоро)</span></li>
                  <li><span className="text-gray-400 dark:text-gray-500">Правовая информация (скоро)</span></li>
                </ul>
              </motion.div>
            </div>
            
            <motion.div 
              className="border-t border-gray-200 dark:border-gray-700 mt-8 pt-8 text-center text-sm text-gray-600 dark:text-gray-300"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.4 }}
            >
              <p>&copy; 2024 АДВАКОД. Все права защищены.</p>
            </motion.div>
          </div>
        </motion.footer>
      )}
    </div>
  );
};

export default Layout;
