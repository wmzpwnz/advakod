import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Scale, Eye, EyeOff, Loader2 } from 'lucide-react';

const Register = () => {
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    fullName: '',
    companyName: '',
    legalForm: '',
    inn: '',
    ogrn: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState({
    length: false,
    uppercase: false,
    lowercase: false,
    number: false,
    special: false
  });

  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
    setError('');

    // Обновляем индикатор силы пароля
    if (name === 'password') {
      setPasswordStrength({
        length: value.length >= 12,
        uppercase: /[A-ZА-Я]/.test(value),
        lowercase: /[a-zа-я]/.test(value),
        number: /\d/.test(value),
        special: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(value)
      });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    // Валидация
    if (formData.password !== formData.confirmPassword) {
      setError('Пароли не совпадают');
      setIsLoading(false);
      return;
    }

    if (formData.password.length < 12) {
      setError('Пароль должен содержать минимум 12 символов');
      setIsLoading(false);
      return;
    }

    // Проверка на заглавные буквы
    if (!/[A-ZА-Я]/.test(formData.password)) {
      setError('Пароль должен содержать хотя бы одну заглавную букву');
      setIsLoading(false);
      return;
    }

    // Проверка на строчные буквы
    if (!/[a-zа-я]/.test(formData.password)) {
      setError('Пароль должен содержать хотя бы одну строчную букву');
      setIsLoading(false);
      return;
    }

    // Проверка на цифры
    if (!/\d/.test(formData.password)) {
      setError('Пароль должен содержать хотя бы одну цифру');
      setIsLoading(false);
      return;
    }

    // Проверка на специальные символы
    if (!/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(formData.password)) {
      setError('Пароль должен содержать хотя бы один специальный символ (!@#$%^&*()_+-=[]{}|;\':",./<>?)');
      setIsLoading(false);
      return;
    }

    const result = await register({
      email: formData.email,
      username: formData.username,
      password: formData.password,
      full_name: formData.fullName || null,
      company_name: formData.companyName || null,
      legal_form: formData.legalForm || null,
      inn: formData.inn || null,
      ogrn: formData.ogrn || null
    });

    if (result.success) {
      navigate('/login', {
        state: { message: 'Регистрация успешна! Теперь войдите в систему.' }
      });
    } else {
      setError(result.error);
    }

    setIsLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8 transition-colors duration-200">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="flex justify-center">
            <Scale className="h-12 w-12 text-primary-600 dark:text-primary-400" />
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900 dark:text-gray-100">
            Регистрация в ИИ-Юрист
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
            Или{' '}
            <Link
              to="/login"
              className="font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
            >
              войдите в существующий аккаунт
            </Link>
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 px-4 py-3 rounded-lg">
              {typeof error === 'string' ? error : (error.message || error.detail || 'Произошла ошибка')}
            </div>
          )}

          <div className="space-y-4">
            {/* Основная информация */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Email адрес *
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={formData.email}
                onChange={handleChange}
                className="input-field mt-1"
                placeholder="your@email.com"
              />
            </div>

            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Имя пользователя *
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                value={formData.username}
                onChange={handleChange}
                className="input-field mt-1"
                placeholder="username"
              />
            </div>

            <div>
              <label htmlFor="fullName" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Полное имя
              </label>
              <input
                id="fullName"
                name="fullName"
                type="text"
                value={formData.fullName}
                onChange={handleChange}
                className="input-field mt-1"
                placeholder="Иван Иванов"
              />
            </div>

            {/* Пароли */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Пароль *
              </label>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Минимум 12 символов, включая заглавные и строчные буквы, цифры и спецсимволы
              </p>
              <div className="mt-1 relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  value={formData.password}
                  onChange={handleChange}
                  className="input-field pr-10"
                  placeholder="Например: MyPass123!@#"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5 text-gray-400" />
                  ) : (
                    <Eye className="h-5 w-5 text-gray-400" />
                  )}
                </button>
              </div>
              {formData.password && (
                <div className="mt-2 space-y-1">
                  <div className="flex items-center text-xs">
                    <span className={`mr-2 ${passwordStrength.length ? 'text-green-600' : 'text-gray-400'}`}>
                      {passwordStrength.length ? '✓' : '○'}
                    </span>
                    <span className={passwordStrength.length ? 'text-green-600' : 'text-gray-500'}>
                      Минимум 12 символов
                    </span>
                  </div>
                  <div className="flex items-center text-xs">
                    <span className={`mr-2 ${passwordStrength.uppercase ? 'text-green-600' : 'text-gray-400'}`}>
                      {passwordStrength.uppercase ? '✓' : '○'}
                    </span>
                    <span className={passwordStrength.uppercase ? 'text-green-600' : 'text-gray-500'}>
                      Заглавная буква
                    </span>
                  </div>
                  <div className="flex items-center text-xs">
                    <span className={`mr-2 ${passwordStrength.lowercase ? 'text-green-600' : 'text-gray-400'}`}>
                      {passwordStrength.lowercase ? '✓' : '○'}
                    </span>
                    <span className={passwordStrength.lowercase ? 'text-green-600' : 'text-gray-500'}>
                      Строчная буква
                    </span>
                  </div>
                  <div className="flex items-center text-xs">
                    <span className={`mr-2 ${passwordStrength.number ? 'text-green-600' : 'text-gray-400'}`}>
                      {passwordStrength.number ? '✓' : '○'}
                    </span>
                    <span className={passwordStrength.number ? 'text-green-600' : 'text-gray-500'}>
                      Цифра
                    </span>
                  </div>
                  <div className="flex items-center text-xs">
                    <span className={`mr-2 ${passwordStrength.special ? 'text-green-600' : 'text-gray-400'}`}>
                      {passwordStrength.special ? '✓' : '○'}
                    </span>
                    <span className={passwordStrength.special ? 'text-green-600' : 'text-gray-500'}>
                      Специальный символ (!@#$%...)
                    </span>
                  </div>
                </div>
              )}
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Подтвердите пароль *
              </label>
              <div className="mt-1 relative">
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  className="input-field pr-10"
                  placeholder="Повторите пароль"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                >
                  {showConfirmPassword ? (
                    <EyeOff className="h-5 w-5 text-gray-400" />
                  ) : (
                    <Eye className="h-5 w-5 text-gray-400" />
                  )}
                </button>
              </div>
            </div>

            {/* Информация о компании */}
            <div className="border-t pt-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">Информация о компании (необязательно)</h3>

              <div>
                <label htmlFor="companyName" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Название компании
                </label>
                <input
                  id="companyName"
                  name="companyName"
                  type="text"
                  value={formData.companyName}
                  onChange={handleChange}
                  className="input-field mt-1"
                  placeholder="ООО Ромашка"
                />
              </div>

              <div className="mt-4">
                <label htmlFor="legalForm" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  Организационно-правовая форма
                </label>
                <select
                  id="legalForm"
                  name="legalForm"
                  value={formData.legalForm}
                  onChange={handleChange}
                  className="input-field mt-1"
                >
                  <option value="">Выберите форму</option>
                  <option value="ИП">ИП</option>
                  <option value="ООО">ООО</option>
                  <option value="АО">АО</option>
                  <option value="Самозанятый">Самозанятый</option>
                </select>
              </div>

              <div className="mt-4">
                <label htmlFor="inn" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  ИНН
                </label>
                <input
                  id="inn"
                  name="inn"
                  type="text"
                  value={formData.inn}
                  onChange={handleChange}
                  className="input-field mt-1"
                  placeholder="1234567890"
                />
              </div>

              <div className="mt-4">
                <label htmlFor="ogrn" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                  ОГРН
                </label>
                <input
                  id="ogrn"
                  name="ogrn"
                  type="text"
                  value={formData.ogrn}
                  onChange={handleChange}
                  className="input-field mt-1"
                  placeholder="1234567890123"
                />
              </div>
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full flex justify-center py-3 px-4 text-sm font-medium rounded-xl btn-glass-primary disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300"
            >
              {isLoading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                'Зарегистрироваться'
              )}
            </button>
          </div>

          <div className="text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Уже есть аккаунт?{' '}
              <Link
                to="/login"
                className="font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
              >
                Войти
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Register;
