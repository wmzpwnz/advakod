import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Shield, 
  AlertTriangle, 
  Key, 
  Clock, 
  Lock, 
  Unlock,
  Eye,
  EyeOff,
  Smartphone,
  Mail,
  RefreshCw,
  CheckCircle,
  XCircle,
  Zap,
  Settings,
  Download,
  Upload
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import ModuleCard from './ModuleCard';
import EnhancedButton from './EnhancedButton';
import LoadingSpinner from './LoadingSpinner';

const SuperAdminProtection = () => {
  const { getModuleColor } = useTheme();
  const [protectionSettings, setProtectionSettings] = useState({
    twoFactorEnabled: false,
    emergencyCodesEnabled: true,
    sessionTimeout: 30, // minutes
    ipWhitelist: [],
    auditLogging: true,
    criticalActionConfirmation: true,
    emergencyAccess: {
      enabled: true,
      codes: [],
      lastGenerated: null
    }
  });

  const [emergencyRecovery, setEmergencyRecovery] = useState({
    showModal: false,
    step: 1,
    recoveryCode: '',
    newPassword: '',
    confirmPassword: '',
    verificationMethod: 'email' // email, sms, backup_codes
  });

  const [criticalActions, setCriticalActions] = useState([]);
  const [securityLogs, setSecurityLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadProtectionData();
  }, []);

  const loadProtectionData = async () => {
    try {
      setLoading(true);
      const [settingsRes, actionsRes, logsRes] = await Promise.all([
        fetch('/api/v1/admin/security/protection-settings', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        fetch('/api/v1/admin/security/critical-actions', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        fetch('/api/v1/admin/security/logs?limit=50', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        })
      ]);

      if (settingsRes.ok) {
        const settings = await settingsRes.json();
        setProtectionSettings(settings);
      }

      if (actionsRes.ok) {
        const actions = await actionsRes.json();
        setCriticalActions(actions);
      }

      if (logsRes.ok) {
        const logs = await logsRes.json();
        setSecurityLogs(logs.logs || []);
      }

    } catch (err) {
      setError('Ошибка загрузки данных безопасности');
      console.error('Error loading protection data:', err);
    } finally {
      setLoading(false);
    }
  };

  const generateEmergencyCodes = async () => {
    try {
      const response = await fetch('/api/v1/admin/security/emergency-codes', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setProtectionSettings(prev => ({
          ...prev,
          emergencyAccess: {
            ...prev.emergencyAccess,
            codes: data.codes,
            lastGenerated: new Date()
          }
        }));
      }
    } catch (err) {
      setError('Ошибка генерации аварийных кодов');
    }
  };

  const updateProtectionSetting = async (key, value) => {
    try {
      const response = await fetch('/api/v1/admin/security/protection-settings', {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ [key]: value })
      });

      if (response.ok) {
        setProtectionSettings(prev => ({ ...prev, [key]: value }));
      }
    } catch (err) {
      setError('Ошибка обновления настроек');
    }
  };

  const initiateEmergencyRecovery = () => {
    setEmergencyRecovery(prev => ({ ...prev, showModal: true, step: 1 }));
  };

  const processEmergencyRecovery = async () => {
    try {
      const response = await fetch('/api/v1/admin/security/emergency-recovery', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          recoveryCode: emergencyRecovery.recoveryCode,
          newPassword: emergencyRecovery.newPassword,
          verificationMethod: emergencyRecovery.verificationMethod
        })
      });

      if (response.ok) {
        setEmergencyRecovery(prev => ({ ...prev, step: 4 }));
      } else {
        setError('Неверный код восстановления');
      }
    } catch (err) {
      setError('Ошибка восстановления доступа');
    }
  };

  const exportSecuritySettings = async () => {
    try {
      const response = await fetch('/api/v1/admin/security/export', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `security-settings-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (err) {
      setError('Ошибка экспорта настроек');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <LoadingSpinner 
          size="lg" 
          module="system" 
          variant="neon"
          text="Загрузка системы защиты..."
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <motion.div 
          className="mb-8"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 flex items-center">
                <Shield className="h-8 w-8 text-red-500 mr-3" />
                Защита супер-администратора
              </h1>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                Расширенные механизмы защиты и экстренного восстановления доступа
              </p>
            </div>
            
            <div className="mt-6 lg:mt-0 flex flex-wrap gap-3">
              <EnhancedButton
                variant="module-outline"
                module="system"
                onClick={exportSecuritySettings}
                icon={<Download className="h-4 w-4" />}
              >
                Экспорт настроек
              </EnhancedButton>
              <EnhancedButton
                variant="module"
                module="system"
                onClick={generateEmergencyCodes}
                icon={<Key className="h-4 w-4" />}
              >
                Генерировать коды
              </EnhancedButton>
              <EnhancedButton
                variant="module-neon"
                module="system"
                onClick={initiateEmergencyRecovery}
                icon={<Zap className="h-4 w-4" />}
              >
                Экстренное восстановление
              </EnhancedButton>
            </div>
          </div>
        </motion.div>

        {/* Error Message */}
        <AnimatePresence>
          {error && (
            <motion.div 
              className="mb-6"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
            >
              <ModuleCard module="system" variant="module" className="border-red-300 bg-red-50 dark:bg-red-900/20">
                <div className="flex items-center">
                  <XCircle className="h-5 w-5 text-red-500 mr-3" />
                  <div>
                    <h3 className="text-sm font-medium text-red-800 dark:text-red-300">Ошибка</h3>
                    <p className="text-sm text-red-700 dark:text-red-400 mt-1">{error}</p>
                  </div>
                  <button 
                    onClick={() => setError('')}
                    className="ml-auto text-red-500 hover:text-red-700"
                  >
                    <XCircle className="h-4 w-4" />
                  </button>
                </div>
              </ModuleCard>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Protection Settings */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            <ModuleCard module="system" variant="module-neon">
              <div className="flex items-center mb-6">
                <Settings className="h-6 w-6 text-red-500 mr-3" />
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                  Настройки защиты
                </h2>
              </div>

              <div className="space-y-6">
                {/* Two-Factor Authentication */}
                <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                  <div className="flex items-center">
                    <Smartphone className="h-5 w-5 text-blue-500 mr-3" />
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-gray-100">
                        Двухфакторная аутентификация
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Дополнительная защита входа
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => updateProtectionSetting('twoFactorEnabled', !protectionSettings.twoFactorEnabled)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      protectionSettings.twoFactorEnabled ? 'bg-green-600' : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        protectionSettings.twoFactorEnabled ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                {/* Session Timeout */}
                <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                  <div className="flex items-center mb-3">
                    <Clock className="h-5 w-5 text-yellow-500 mr-3" />
                    <h3 className="font-medium text-gray-900 dark:text-gray-100">
                      Таймаут сессии
                    </h3>
                  </div>
                  <div className="flex items-center space-x-3">
                    <input
                      type="range"
                      min="5"
                      max="120"
                      value={protectionSettings.sessionTimeout}
                      onChange={(e) => updateProtectionSetting('sessionTimeout', parseInt(e.target.value))}
                      className="flex-1"
                    />
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100 min-w-[60px]">
                      {protectionSettings.sessionTimeout} мин
                    </span>
                  </div>
                </div>

                {/* Critical Action Confirmation */}
                <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                  <div className="flex items-center">
                    <AlertTriangle className="h-5 w-5 text-orange-500 mr-3" />
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-gray-100">
                        Подтверждение критических действий
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Дополнительное подтверждение для опасных операций
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => updateProtectionSetting('criticalActionConfirmation', !protectionSettings.criticalActionConfirmation)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      protectionSettings.criticalActionConfirmation ? 'bg-green-600' : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        protectionSettings.criticalActionConfirmation ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                {/* Audit Logging */}
                <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                  <div className="flex items-center">
                    <Eye className="h-5 w-5 text-purple-500 mr-3" />
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-gray-100">
                        Аудит действий
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Логирование всех административных действий
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => updateProtectionSetting('auditLogging', !protectionSettings.auditLogging)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      protectionSettings.auditLogging ? 'bg-green-600' : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        protectionSettings.auditLogging ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              </div>
            </ModuleCard>
          </motion.div>

          {/* Emergency Access */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <ModuleCard module="system" variant="module-neon">
              <div className="flex items-center mb-6">
                <Key className="h-6 w-6 text-red-500 mr-3" />
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                  Экстренный доступ
                </h2>
              </div>

              <div className="space-y-4">
                <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                  <div className="flex items-center mb-2">
                    <AlertTriangle className="h-5 w-5 text-yellow-600 mr-2" />
                    <h3 className="font-medium text-yellow-800 dark:text-yellow-300">
                      Аварийные коды восстановления
                    </h3>
                  </div>
                  <p className="text-sm text-yellow-700 dark:text-yellow-400 mb-3">
                    Используйте эти коды для восстановления доступа в случае потери основных средств аутентификации.
                  </p>
                  
                  {protectionSettings.emergencyAccess.codes.length > 0 ? (
                    <div className="space-y-2">
                      <div className="text-xs text-yellow-600 dark:text-yellow-400">
                        Сгенерировано: {protectionSettings.emergencyAccess.lastGenerated && 
                          new Date(protectionSettings.emergencyAccess.lastGenerated).toLocaleString()}
                      </div>
                      <div className="grid grid-cols-2 gap-2 font-mono text-sm">
                        {protectionSettings.emergencyAccess.codes.map((code, index) => (
                          <div key={index} className="p-2 bg-white dark:bg-gray-800 rounded border">
                            {code}
                          </div>
                        ))}
                      </div>
                      <div className="text-xs text-yellow-600 dark:text-yellow-400">
                        ⚠️ Сохраните эти коды в безопасном месте. Они показываются только один раз.
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-4">
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                        Аварийные коды не сгенерированы
                      </p>
                      <EnhancedButton
                        variant="module"
                        module="system"
                        size="sm"
                        onClick={generateEmergencyCodes}
                        icon={<RefreshCw className="h-4 w-4" />}
                      >
                        Генерировать коды
                      </EnhancedButton>
                    </div>
                  )}
                </div>

                {/* Emergency Recovery Process */}
                <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <h3 className="font-medium text-red-800 dark:text-red-300 mb-2">
                    Процедура экстренного восстановления
                  </h3>
                  <ol className="text-sm text-red-700 dark:text-red-400 space-y-1 list-decimal list-inside">
                    <li>Нажмите кнопку "Экстренное восстановление"</li>
                    <li>Введите один из аварийных кодов</li>
                    <li>Подтвердите через email или SMS</li>
                    <li>Установите новый пароль</li>
                    <li>Настройте новую двухфакторную аутентификацию</li>
                  </ol>
                </div>
              </div>
            </ModuleCard>
          </motion.div>
        </div>

        {/* Security Logs */}
        <motion.div
          className="mt-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <ModuleCard module="system" variant="module">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center">
                <Eye className="h-6 w-6 text-red-500 mr-3" />
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                  Журнал безопасности
                </h2>
              </div>
              <EnhancedButton
                variant="module-outline"
                module="system"
                size="sm"
                onClick={loadProtectionData}
                icon={<RefreshCw className="h-4 w-4" />}
              >
                Обновить
              </EnhancedButton>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-800">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Время
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Действие
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Пользователь
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      IP адрес
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Статус
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                  {securityLogs.map((log, index) => (
                    <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                        {log.action}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                        {log.userName}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {log.ipAddress}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {log.success ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            Успешно
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300">
                            <XCircle className="h-3 w-3 mr-1" />
                            Ошибка
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </ModuleCard>
        </motion.div>

        {/* Emergency Recovery Modal */}
        <AnimatePresence>
          {emergencyRecovery.showModal && (
            <motion.div 
              className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <motion.div 
                className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-md w-full"
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
              >
                <div className="p-6">
                  <div className="flex items-center mb-6">
                    <Zap className="h-6 w-6 text-red-500 mr-3" />
                    <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                      Экстренное восстановление доступа
                    </h3>
                  </div>

                  {emergencyRecovery.step === 1 && (
                    <div className="space-y-4">
                      <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                        <p className="text-sm text-red-700 dark:text-red-400">
                          ⚠️ Эта процедура предназначена только для экстренных случаев потери доступа к основным средствам аутентификации.
                        </p>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Аварийный код восстановления
                        </label>
                        <input
                          type="text"
                          value={emergencyRecovery.recoveryCode}
                          onChange={(e) => setEmergencyRecovery(prev => ({...prev, recoveryCode: e.target.value}))}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-red-500 focus:border-transparent font-mono"
                          placeholder="XXXX-XXXX-XXXX-XXXX"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Метод подтверждения
                        </label>
                        <select
                          value={emergencyRecovery.verificationMethod}
                          onChange={(e) => setEmergencyRecovery(prev => ({...prev, verificationMethod: e.target.value}))}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-red-500 focus:border-transparent"
                        >
                          <option value="email">Email подтверждение</option>
                          <option value="sms">SMS подтверждение</option>
                          <option value="backup_codes">Резервные коды</option>
                        </select>
                      </div>

                      <div className="flex justify-end space-x-3 pt-4">
                        <EnhancedButton
                          variant="secondary"
                          onClick={() => setEmergencyRecovery(prev => ({...prev, showModal: false}))}
                        >
                          Отмена
                        </EnhancedButton>
                        <EnhancedButton
                          variant="module"
                          module="system"
                          onClick={() => setEmergencyRecovery(prev => ({...prev, step: 2}))}
                          disabled={!emergencyRecovery.recoveryCode}
                        >
                          Продолжить
                        </EnhancedButton>
                      </div>
                    </div>
                  )}

                  {emergencyRecovery.step === 2 && (
                    <div className="space-y-4">
                      <div className="text-center">
                        <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                        <h4 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                          Код подтвержден
                        </h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          Установите новый пароль для восстановления доступа
                        </p>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Новый пароль
                        </label>
                        <input
                          type="password"
                          value={emergencyRecovery.newPassword}
                          onChange={(e) => setEmergencyRecovery(prev => ({...prev, newPassword: e.target.value}))}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-red-500 focus:border-transparent"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Подтвердите пароль
                        </label>
                        <input
                          type="password"
                          value={emergencyRecovery.confirmPassword}
                          onChange={(e) => setEmergencyRecovery(prev => ({...prev, confirmPassword: e.target.value}))}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-red-500 focus:border-transparent"
                        />
                      </div>

                      <div className="flex justify-end space-x-3 pt-4">
                        <EnhancedButton
                          variant="secondary"
                          onClick={() => setEmergencyRecovery(prev => ({...prev, step: 1}))}
                        >
                          Назад
                        </EnhancedButton>
                        <EnhancedButton
                          variant="module"
                          module="system"
                          onClick={processEmergencyRecovery}
                          disabled={!emergencyRecovery.newPassword || emergencyRecovery.newPassword !== emergencyRecovery.confirmPassword}
                        >
                          Восстановить доступ
                        </EnhancedButton>
                      </div>
                    </div>
                  )}

                  {emergencyRecovery.step === 4 && (
                    <div className="text-center space-y-4">
                      <CheckCircle className="h-16 w-16 text-green-500 mx-auto" />
                      <h4 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                        Доступ восстановлен
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        Ваш пароль успешно изменен. Рекомендуется настроить новую двухфакторную аутентификацию.
                      </p>
                      <EnhancedButton
                        variant="module"
                        module="system"
                        onClick={() => {
                          setEmergencyRecovery(prev => ({...prev, showModal: false}));
                          window.location.reload();
                        }}
                      >
                        Закрыть
                      </EnhancedButton>
                    </div>
                  )}
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default SuperAdminProtection;