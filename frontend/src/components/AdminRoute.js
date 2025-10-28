import React, { useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useAdmin } from '../contexts/AdminContext';
import { useAdminSession } from '../hooks/useAdminSession';

const AdminRoute = ({ children }) => {
  const { isAdmin, loading } = useAdmin();
  const { checkAdminSessionExpiry } = useAdminSession();

  useEffect(() => {
    // Проверяем сессию при входе в админку
    if (isAdmin) {
      checkAdminSessionExpiry();
    }
  }, [isAdmin, checkAdminSessionExpiry]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto mb-4"></div>
          <p className="text-gray-300">Проверка админских прав...</p>
        </div>
      </div>
    );
  }

  // Проверяем админскую сессию
  const adminSession = localStorage.getItem('admin_session');
  const adminExpires = localStorage.getItem('admin_expires');
  
  if (isAdmin && adminSession !== 'true') {
    // Админ, но нет активной админской сессии - перенаправляем на админский логин
    return <Navigate to="/admin-login" replace />;
  }

  if (isAdmin && adminExpires) {
    const expiryTime = parseInt(adminExpires);
    const currentTime = Date.now();
    
    if (currentTime >= expiryTime) {
      // Сессия истекла
      localStorage.removeItem('admin_session');
      localStorage.removeItem('admin_expires');
      return <Navigate to="/admin-login" replace />;
    }
  }

  if (!isAdmin) {
    return <Navigate to="/admin-login" replace />;
  }

  return (
    <div className="admin-secure-zone">
      {/* Индикатор безопасной зоны */}
      <div className="bg-red-900 text-red-100 px-4 py-2 text-center text-sm">
        🛡️ Безопасная админская зона • Сессия истекает через {
          adminExpires ? Math.ceil((parseInt(adminExpires) - Date.now()) / 60000) : '?'
        } мин.
      </div>
      {children}
    </div>
  );
};

export default AdminRoute;
