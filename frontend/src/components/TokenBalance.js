import React, { useState, useEffect } from 'react';
import { Coins, Plus, History } from 'lucide-react';
import axios from 'axios';
import { getApiUrl } from '../config/api';

const TokenBalance = () => {
  const [balance, setBalance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchBalance = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await axios.get(getApiUrl('/tokens/balance'), {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      setBalance(response.data);
      setError(null);
    } catch (err) {
      console.error('Ошибка загрузки баланса:', err);
      
      // Если токен истек, очищаем его и перенаправляем на логин
      if (err.response?.status === 401) {
        console.log('Token expired, logging out automatically');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        return;
      }
      
      setError('Не удалось загрузить баланс');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBalance();
    
    // Обновляем баланс каждые 30 секунд
    const interval = setInterval(fetchBalance, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center space-x-2 text-gray-600">
        <Coins className="w-4 h-4" />
        <span className="text-sm">Загрузка...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center space-x-2 text-red-600">
        <Coins className="w-4 h-4" />
        <span className="text-sm">Ошибка</span>
      </div>
    );
  }

  if (!balance) {
    return null;
  }

  return (
    <div className="flex items-center space-x-3">
      {/* Основной баланс */}
      <div className="flex items-center space-x-2 bg-blue-50 px-3 py-1 rounded-full">
        <Coins className="w-4 h-4 text-blue-600" />
        <span className="text-sm font-medium text-blue-800">
          {balance.balance.toLocaleString()} токенов
        </span>
      </div>

      {/* Кнопка пополнения */}
      <button
        onClick={() => {
          // Здесь можно добавить модальное окно для пополнения
          alert('Функция пополнения будет добавлена позже');
        }}
        className="flex items-center space-x-1 text-green-600 hover:text-green-700 transition-colors"
        title="Пополнить баланс"
      >
        <Plus className="w-4 h-4" />
        <span className="text-sm">Пополнить</span>
      </button>

      {/* Кнопка истории */}
      <button
        onClick={() => {
          // Здесь можно добавить модальное окно с историей транзакций
          alert('История транзакций будет добавлена позже');
        }}
        className="flex items-center space-x-1 text-gray-600 hover:text-gray-700 transition-colors"
        title="История транзакций"
      >
        <History className="w-4 h-4" />
        <span className="text-sm">История</span>
      </button>
    </div>
  );
};

export default TokenBalance;
