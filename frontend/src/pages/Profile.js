import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { User, Building, CreditCard, Settings, LogOut, Save, Edit3 } from 'lucide-react';
import axios from 'axios';

const Profile = () => {
  const { user, logout } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [formData, setFormData] = useState({
    full_name: user?.full_name || '',
    company_name: user?.company_name || '',
    legal_form: user?.legal_form || '',
    inn: user?.inn || '',
    ogrn: user?.ogrn || ''
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSave = async () => {
    setIsLoading(true);
    try {
      await axios.put('/api/v1/users/me', formData);
      setMessage('Профиль успешно обновлен');
      setIsEditing(false);
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      setMessage('Ошибка при обновлении профиля');
      setTimeout(() => setMessage(''), 3000);
    } finally {
      setIsLoading(false);
    }
  };

  const getSubscriptionStatus = () => {
    if (user?.is_premium) {
      return { text: 'Премиум', color: 'text-green-600 bg-green-100' };
    }
    return { text: 'Базовый', color: 'text-blue-600 bg-blue-100' };
  };

  const subscriptionStatus = getSubscriptionStatus();

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 transition-colors duration-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <User className="h-8 w-8 text-primary-600 dark:text-primary-400" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Профиль</h1>
                <p className="text-gray-600 dark:text-gray-300">Управление вашим аккаунтом</p>
              </div>
            </div>
            <button
              onClick={logout}
              className="flex items-center space-x-2 text-gray-600 dark:text-gray-300 hover:text-red-600 dark:hover:text-red-400 transition-colors"
            >
              <LogOut className="h-5 w-5" />
              <span>Выйти</span>
            </button>
          </div>
        </div>

        <div className="p-6">
          {message && (
            <div className={`mb-6 p-4 rounded-lg ${
              (typeof message === 'string' && message.includes('успешно')) 
                ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-700' 
                : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-700'
            }`}>
              {typeof message === 'string' ? message : JSON.stringify(message)}
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Основная информация */}
            <div className="lg:col-span-2 space-y-8">
              {/* Личная информация */}
              <div className="card bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 p-6 rounded-lg">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center space-x-2">
                    <User className="h-5 w-5" />
                    <span>Личная информация</span>
                  </h2>
                  <button
                    onClick={() => setIsEditing(!isEditing)}
                    className="flex items-center space-x-2 text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300"
                  >
                    <Edit3 className="h-4 w-4" />
                    <span>{isEditing ? 'Отмена' : 'Редактировать'}</span>
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Email
                    </label>
                    <input
                      type="email"
                      value={user?.email || ''}
                      disabled
                      className="input-field bg-gray-50 dark:bg-gray-600"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Имя пользователя
                    </label>
                    <input
                      type="text"
                      value={user?.username || ''}
                      disabled
                      className="input-field bg-gray-50 dark:bg-gray-600"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Полное имя
                    </label>
                    <input
                      type="text"
                      name="full_name"
                      value={formData.full_name}
                      onChange={handleChange}
                      disabled={!isEditing}
                      className="input-field"
                    />
                  </div>
                </div>
              </div>

              {/* Информация о компании */}
              <div className="card bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 p-6 rounded-lg">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center space-x-2 mb-6">
                  <Building className="h-5 w-5" />
                  <span>Информация о компании</span>
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Название компании
                    </label>
                    <input
                      type="text"
                      name="company_name"
                      value={formData.company_name}
                      onChange={handleChange}
                      disabled={!isEditing}
                      className="input-field"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Организационно-правовая форма
                    </label>
                    <select
                      name="legal_form"
                      value={formData.legal_form}
                      onChange={handleChange}
                      disabled={!isEditing}
                      className="input-field"
                    >
                      <option value="">Выберите форму</option>
                      <option value="ИП">ИП</option>
                      <option value="ООО">ООО</option>
                      <option value="АО">АО</option>
                      <option value="Самозанятый">Самозанятый</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      ИНН
                    </label>
                    <input
                      type="text"
                      name="inn"
                      value={formData.inn}
                      onChange={handleChange}
                      disabled={!isEditing}
                      className="input-field"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      ОГРН
                    </label>
                    <input
                      type="text"
                      name="ogrn"
                      value={formData.ogrn}
                      onChange={handleChange}
                      disabled={!isEditing}
                      className="input-field"
                    />
                  </div>
                </div>
              </div>

              {/* Кнопка сохранения */}
              {isEditing && (
                <div className="flex justify-end">
                  <button
                    onClick={handleSave}
                    disabled={isLoading}
                    className="btn-primary flex items-center space-x-2"
                  >
                    <Save className="h-4 w-4" />
                    <span>{isLoading ? 'Сохранение...' : 'Сохранить'}</span>
                  </button>
                </div>
              )}
            </div>

            {/* Боковая панель */}
            <div className="space-y-6">
              {/* Подписка */}
              <div className="card bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 p-6 rounded-lg">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center space-x-2 mb-4">
                  <CreditCard className="h-5 w-5" />
                  <span>Подписка</span>
                </h3>

                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-gray-600 dark:text-gray-300">Текущий тариф</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${subscriptionStatus.color}`}>
                        {subscriptionStatus.text}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {user?.subscription_type || 'free'}
                    </p>
                  </div>

                  <div>
                    <span className="text-sm text-gray-600 dark:text-gray-300">Дата регистрации</span>
                    <p className="text-sm text-gray-900 dark:text-gray-100">
                      {user?.created_at ? new Date(user.created_at).toLocaleDateString('ru-RU') : 'Не указано'}
                    </p>
                  </div>

                  <button className="w-full btn-primary">
                    Изменить тариф
                  </button>
                </div>
              </div>

              {/* Статистика */}
              <div className="card bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 p-6 rounded-lg">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                  Статистика использования
                </h3>

                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-300">Запросов в этом месяце</span>
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100">0</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-300">Документов проанализировано</span>
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100">0</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-300">Сессий чата</span>
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100">0</span>
                  </div>
                </div>
              </div>

              {/* Настройки */}
              <div className="card bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 p-6 rounded-lg">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center space-x-2 mb-4">
                  <Settings className="h-5 w-5" />
                  <span>Настройки</span>
                </h3>

                <div className="space-y-3">
                  <button className="w-full text-left text-sm text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400">
                    Уведомления
                  </button>
                  <button className="w-full text-left text-sm text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400">
                    Безопасность
                  </button>
                  <button className="w-full text-left text-sm text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400">
                    Экспорт данных
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
