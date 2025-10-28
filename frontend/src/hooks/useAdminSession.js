import { useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useAdmin } from '../contexts/AdminContext';

/**
 * Хук для управления админскими сессиями с автоматическим logout
 */
export const useAdminSession = () => {
  const { logout } = useAuth();
  const { isAdmin } = useAdmin();

  // Проверка истечения админской сессии
  const checkAdminSessionExpiry = useCallback(() => {
    if (!isAdmin) return;

    const adminSession = localStorage.getItem('admin_session');
    const adminExpires = localStorage.getItem('admin_expires');

    if (adminSession === 'true' && adminExpires) {
      const expiryTime = parseInt(adminExpires);
      const currentTime = Date.now();

      if (currentTime >= expiryTime) {
        // Сессия истекла
        console.log('Admin session expired, logging out...');
        localStorage.removeItem('admin_session');
        localStorage.removeItem('admin_expires');
        
        // Показываем предупреждение
        alert('Админская сессия истекла. Необходимо войти заново.');
        
        logout();
        window.location.href = '/admin-login';
      }
    }
  }, [isAdmin, logout]);

  // Предупреждение за 5 минут до истечения
  const checkSessionWarning = useCallback(() => {
    if (!isAdmin) return;

    const adminExpires = localStorage.getItem('admin_expires');
    if (adminExpires) {
      const expiryTime = parseInt(adminExpires);
      const currentTime = Date.now();
      const timeLeft = expiryTime - currentTime;
      
      // Предупреждаем за 5 минут (300000 мс)
      if (timeLeft > 0 && timeLeft <= 300000 && timeLeft > 240000) {
        const minutesLeft = Math.ceil(timeLeft / 60000);
        
        const shouldExtend = window.confirm(
          `Админская сессия истекает через ${minutesLeft} минут. Продлить сессию?`
        );
        
        if (shouldExtend) {
          // Перенаправляем на повторный вход
          window.location.href = '/admin-login';
        }
      }
    }
  }, [isAdmin]);

  useEffect(() => {
    if (!isAdmin) return;

    // Проверяем каждые 30 секунд
    const sessionCheckInterval = setInterval(checkAdminSessionExpiry, 30000);
    
    // Проверяем предупреждение каждую минуту
    const warningCheckInterval = setInterval(checkSessionWarning, 60000);

    // Проверяем сразу при монтировании
    checkAdminSessionExpiry();

    return () => {
      clearInterval(sessionCheckInterval);
      clearInterval(warningCheckInterval);
    };
  }, [isAdmin, checkAdminSessionExpiry, checkSessionWarning]);

  // Функция для продления сессии
  const extendAdminSession = useCallback(async () => {
    try {
      // Перенаправляем на админский логин для продления
      window.location.href = '/admin-login';
    } catch (error) {
      console.error('Error extending admin session:', error);
      logout();
    }
  }, [logout]);

  return {
    checkAdminSessionExpiry,
    extendAdminSession
  };
};
