import React, { useState } from 'react';
import { Shield, Key, AlertCircle } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

const TwoFactorInput = ({ onVerify, onCancel, loading = false, error = '' }) => {
  const [token, setToken] = useState('');
  const { isDark } = useTheme();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (token.length === 6) {
      onVerify(token);
    }
  };

  const handleTokenChange = (e) => {
    const value = e.target.value.replace(/\D/g, '').slice(0, 6);
    setToken(value);
  };

  return (
    <div className="max-w-md mx-auto p-6 bg-white dark:bg-gray-800 rounded-lg shadow-lg">
      <div className="text-center mb-6">
        <div className="mx-auto w-12 h-12 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center mb-4">
          <Shield className="h-6 w-6 text-primary-600" />
        </div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
          Двухфакторная аутентификация
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
          Введите код из приложения аутентификатора
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center space-x-2">
          <AlertCircle className="h-4 w-4 text-red-500" />
          <span className="text-sm text-red-600 dark:text-red-400">{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Код аутентификации
          </label>
          <input
            type="text"
            value={token}
            onChange={handleTokenChange}
            placeholder="000000"
            className="w-full px-4 py-3 text-center text-2xl font-mono border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            maxLength={6}
            autoComplete="one-time-code"
            autoFocus
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Введите 6-значный код из приложения Google Authenticator или аналогичного
          </p>
        </div>

        <div className="flex space-x-3">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 btn-secondary"
            >
              Отмена
            </button>
          )}
          <button
            type="submit"
            disabled={loading || token.length !== 6}
            className="flex-1 btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="flex items-center justify-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Проверка...</span>
              </div>
            ) : (
              'Подтвердить'
            )}
          </button>
        </div>
      </form>

      <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
        <div className="flex items-start space-x-2">
          <Key className="h-4 w-4 text-blue-600 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-blue-800 dark:text-blue-200">
              Нет доступа к приложению?
            </p>
            <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
              Используйте один из резервных кодов, которые вы сохранили при настройке 2FA.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TwoFactorInput;
