import React, { useState, useEffect } from 'react';
import { Shield, Smartphone, Key, Copy, Check, AlertCircle } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import axios from 'axios';

const TwoFactorSetup = ({ onSetupComplete, onCancel }) => {
  const [step, setStep] = useState(1); // 1: QR code, 2: verification, 3: backup codes
  const [qrCode, setQrCode] = useState('');
  const [secret, setSecret] = useState('');
  const [backupCodes, setBackupCodes] = useState([]);
  const [verificationToken, setVerificationToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const { isDark } = useTheme();

  useEffect(() => {
    setup2FA();
  }, []);

  const setup2FA = async () => {
    try {
      setLoading(true);
      const response = await axios.post('/api/v1/2fa/setup');
      setQrCode(response.data.qr_code);
      setSecret(response.data.secret);
      setBackupCodes(response.data.backup_codes);
      setStep(1);
    } catch (error) {
      setError('Ошибка при настройке 2FA');
      console.error('2FA setup error:', error);
    } finally {
      setLoading(false);
    }
  };

  const verifyToken = async () => {
    if (!verificationToken.trim()) {
      setError('Введите код из приложения');
      return;
    }

    try {
      setLoading(true);
      setError('');
      
      const response = await axios.post('/api/v1/2fa/confirm', {
        token: verificationToken
      });

      if (response.data.enabled) {
        setStep(3);
      }
    } catch (error) {
      setError(error.response?.data?.detail || 'Неверный код');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const downloadBackupCodes = () => {
    const codesText = backupCodes.join('\n');
    const blob = new Blob([codesText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'backup-codes.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading && step === 1) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        <span className="ml-2 text-gray-600 dark:text-gray-400">Настройка 2FA...</span>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto p-6 bg-white dark:bg-gray-800 rounded-lg shadow-lg">
      <div className="text-center mb-6">
        <div className="mx-auto w-12 h-12 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center mb-4">
          <Shield className="h-6 w-6 text-primary-600" />
        </div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
          Настройка двухфакторной аутентификации
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
          Защитите свой аккаунт дополнительным уровнем безопасности
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center space-x-2">
          <AlertCircle className="h-4 w-4 text-red-500" />
          <span className="text-sm text-red-600 dark:text-red-400">{error}</span>
        </div>
      )}

      {/* Step 1: QR Code */}
      {step === 1 && (
        <div className="space-y-4">
          <div className="text-center">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
              Шаг 1: Сканируйте QR-код
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Отсканируйте QR-код в приложении Google Authenticator или аналогичном
            </p>
          </div>

          <div className="flex justify-center">
            <div className="p-4 bg-white rounded-lg border border-gray-200 dark:border-gray-700">
              <img src={qrCode} alt="2FA QR Code" className="w-48 h-48" />
            </div>
          </div>

          <div className="text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
              Или введите секретный ключ вручную:
            </p>
            <div className="flex items-center justify-center space-x-2">
              <code className="px-3 py-2 bg-gray-100 dark:bg-gray-700 rounded text-sm font-mono">
                {secret}
              </code>
              <button
                onClick={() => copyToClipboard(secret)}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <button
            onClick={() => setStep(2)}
            className="w-full btn-primary"
          >
            Далее
          </button>
        </div>
      )}

      {/* Step 2: Verification */}
      {step === 2 && (
        <div className="space-y-4">
          <div className="text-center">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
              Шаг 2: Подтвердите код
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Введите 6-значный код из приложения аутентификатора
            </p>
          </div>

          <div>
            <input
              type="text"
              value={verificationToken}
              onChange={(e) => setVerificationToken(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder="000000"
              className="w-full px-4 py-3 text-center text-2xl font-mono border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              maxLength={6}
            />
          </div>

          <div className="flex space-x-3">
            <button
              onClick={() => setStep(1)}
              className="flex-1 btn-secondary"
            >
              Назад
            </button>
            <button
              onClick={verifyToken}
              disabled={loading || verificationToken.length !== 6}
              className="flex-1 btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Проверка...' : 'Подтвердить'}
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Backup Codes */}
      {step === 3 && (
        <div className="space-y-4">
          <div className="text-center">
            <div className="mx-auto w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mb-4">
              <Check className="h-6 w-6 text-green-600" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
              2FA успешно настроен!
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Сохраните резервные коды в безопасном месте
            </p>
          </div>

          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
            <div className="flex items-start space-x-2">
              <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                  Важно!
                </p>
                <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                  Резервные коды можно использовать только один раз. Сохраните их в безопасном месте.
                </p>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                Резервные коды:
              </h4>
              <button
                onClick={downloadBackupCodes}
                className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400"
              >
                Скачать
              </button>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {backupCodes.map((code, index) => (
                <div
                  key={index}
                  className="px-3 py-2 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-600 text-sm font-mono text-center"
                >
                  {code}
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={onSetupComplete}
            className="w-full btn-primary"
          >
            Завершить настройку
          </button>
        </div>
      )}

      <div className="mt-6 text-center">
        <button
          onClick={onCancel}
          className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          Отмена
        </button>
      </div>
    </div>
  );
};

export default TwoFactorSetup;
