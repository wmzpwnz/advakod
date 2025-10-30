import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { getApiUrl } from '../config/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  }, []);

  const fetchUser = useCallback(async () => {
    try {
      const response = await axios.get(getApiUrl('/auth/me'));
      setUser(response.data);
    } catch (error) {
      console.error('Error fetching user:', error);
      // Проверяем, не истек ли токен
      if (error.response?.status === 401) {
        console.log('Token expired, logging out');
        logout();
      }
    } finally {
      setLoading(false);
    }
  }, [logout]);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUser();
      
      // Настраиваем перехватчик для автоматического обновления токена
      const responseInterceptor = axios.interceptors.response.use(
        (response) => response,
        (error) => {
          if (error.response?.status === 401) {
            console.log('Token expired, logging out automatically');
            logout();
          }
          return Promise.reject(error);
        }
      );
      
      return () => {
        axios.interceptors.response.eject(responseInterceptor);
      };
    } else {
      setLoading(false);
    }
  }, [token, fetchUser, logout]); // Добавляем зависимости

  const login = async (email, password) => {
    try {
      const response = await axios.post(getApiUrl('/auth/login-email'), {
        email,
        password
      });
      
      const { access_token } = response.data;
      setToken(access_token);
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      await fetchUser();
      return { success: true };
    } catch (error) {
      const errorData = error.response?.data;
      let errorMessage = 'Ошибка входа';
      
      if (errorData) {
        if (typeof errorData === 'string') {
          errorMessage = errorData;
        } else if (errorData.detail) {
          if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else if (errorData.detail.message) {
            errorMessage = errorData.detail.message;
          }
        } else if (errorData.message) {
          errorMessage = errorData.message;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      return { 
        success: false, 
        error: errorMessage
      };
    }
  };

  const register = async (userData) => {
    try {
      const response = await axios.post(getApiUrl('/auth/register'), userData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Registration error:', error);
      
      // Проверяем, есть ли ответ от сервера
      if (!error.response) {
        return { 
          success: false, 
          error: 'Ошибка сети. Проверьте подключение к интернету и убедитесь, что сервер запущен.'
        };
      }
      
      const errorData = error.response?.data;
      let errorMessage = 'Ошибка регистрации';
      
      if (errorData) {
        if (typeof errorData === 'string') {
          errorMessage = errorData;
        } else if (errorData.detail) {
          if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else if (errorData.detail.message) {
            errorMessage = errorData.detail.message;
          } else if (Array.isArray(errorData.detail)) {
            // Обработка массива ошибок валидации от FastAPI
            errorMessage = errorData.detail.map(err => err.msg || err.message).join(', ');
          }
        } else if (errorData.message) {
          errorMessage = errorData.message;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      return { 
        success: false, 
        error: errorMessage
      };
    }
  };

  const value = {
    user,
    token,
    login,
    register,
    logout,
    fetchUser,
    loading,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
