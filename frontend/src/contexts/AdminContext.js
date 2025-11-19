import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';

const AdminContext = createContext();

export const useAdmin = () => {
  const context = useContext(AdminContext);
  if (!context) {
    throw new Error('useAdmin must be used within an AdminProvider');
  }
  return context;
};

export const AdminProvider = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const [isAdmin, setIsAdmin] = useState(false);
  const [adminData, setAdminData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isAuthenticated && user) {
      checkAdminStatus();
    } else {
      setIsAdmin(false);
      setAdminData(null);
      setLoading(false);
    }
  }, [isAuthenticated, user]);

  const checkAdminStatus = async () => {
    if (!isAuthenticated || !user) {
      setIsAdmin(false);
      setAdminData(null);
      setLoading(false);
      return;
    }

    try {
      // Используем данные пользователя из AuthContext
      if (user.is_admin) {
        setIsAdmin(true);
        setAdminData(user);
      } else {
        setIsAdmin(false);
        setAdminData(null);
      }
    } catch (error) {
      console.error('Error checking admin status:', error);
      setIsAdmin(false);
      setAdminData(null);
    } finally {
      setLoading(false);
    }
  };

  const refreshAdminData = async () => {
    await checkAdminStatus();
  };

  const value = {
    isAdmin,
    adminData,
    loading,
    refreshAdminData
  };

  return (
    <AdminContext.Provider value={value}>
      {children}
    </AdminContext.Provider>
  );
};
