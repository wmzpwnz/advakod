import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Shield, Lock, Eye, EyeOff, AlertTriangle } from 'lucide-react';
import { getApiUrl } from '../config/api';

const AdminLogin = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();
  const { login, fetchUser } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Используем специальный админский эндпоинт
      const response = await fetch(getApiUrl('/auth/admin-login'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (response.ok) {
        // Сохраняем админский токен
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('admin_session', 'true');
        localStorage.setItem('admin_expires', Date.now() + (data.expires_in * 1000));
        
        // Обновляем axios headers
        const axios = (await import('axios')).default;
        axios.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`;
        
        // Обновляем контекст аутентификации
        await fetchUser();
        
        // Показываем успешный вход
        setSuccess(true);
        setError('');
        
        // Перенаправляем на админ-панель через 1 секунду
        setTimeout(() => {
          navigate('/admin');
        }, 1000);
      } else {
        setError(data.detail || 'Ошибка входа в админку');
      }
    } catch (err) {
      console.error('Admin login error:', err);
      setError('Ошибка подключения к серверу');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-900 via-gray-900 to-black flex items-center justify-center px-4">
      {/* Предупреждающий фон */}
      <div className="absolute inset-0 bg-black/50"></div>
      
      <div className="relative max-w-md w-full">
        {/* Предупреждение о безопасности */}
        <div className="bg-red-900/30 border border-red-500/50 rounded-xl p-4 mb-6 backdrop-blur-md">
          <div className="flex items-center space-x-3 text-red-200">
            <AlertTriangle className="h-5 w-5 text-red-400" />
            <div>
              <p className="text-sm font-medium">Административная зона</p>
              <p className="text-xs text-red-300">Доступ только для авторизованного персонала</p>
            </div>
          </div>
        </div>

        {/* Форма входа */}
        <div className="bg-white/10 backdrop-blur-md rounded-2xl shadow-2xl border border-white/20 p-8">
          <div className="text-center mb-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-red-600 rounded-full flex items-center justify-center">
              <Shield className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">Админ панель АДВАКОД</h1>
            <p className="text-gray-300 text-sm">Вход для администраторов системы</p>
          </div>

          {success ? (
            <div className="text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-green-600 rounded-full flex items-center justify-center">
                <Shield className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-xl font-bold text-green-400 mb-2">Вход выполнен успешно!</h2>
              <p className="text-gray-300 text-sm">Перенаправление на админ-панель...</p>
              <div className="mt-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-400 mx-auto"></div>
              </div>
            </div>
          ) : (
            <>
              {error && (
                <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3 mb-6">
                  <p className="text-red-200 text-sm text-center">{error}</p>
                </div>
              )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-200 mb-2">
                Email администратора
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200"
                placeholder="admin@example.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-200 mb-2">
                Пароль
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  required
                  className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent transition-all duration-200 pr-12"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-glass-danger font-semibold py-3 px-6 rounded-xl transition-all duration-200 transform hover:scale-105 disabled:scale-100"
            >
              {loading ? (
                <div className="flex items-center justify-center space-x-2">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>Проверка доступа...</span>
                </div>
              ) : (
                <div className="flex items-center justify-center space-x-2">
                  <Lock className="h-5 w-5" />
                  <span>Войти в админку</span>
                </div>
              )}
            </button>
          </form>

          {/* Дополнительная информация */}
          <div className="mt-8 text-center">
            <div className="bg-yellow-900/30 border border-yellow-500/50 rounded-lg p-3 mb-4">
              <p className="text-yellow-200 text-xs">
                ⚠️ Сессия администратора действует 30 минут
              </p>
            </div>
            
            <Link 
              to="/" 
              className="text-gray-400 hover:text-white text-sm transition-colors"
            >
              ← Вернуться на главную
            </Link>
          </div>
            </>
          )}
        </div>

        {/* Информация о безопасности */}
        <div className="mt-6 text-center">
          <p className="text-gray-400 text-xs">
            Все действия администраторов логируются и мониторятся
          </p>
        </div>
      </div>
    </div>
  );
};

export default AdminLogin;
