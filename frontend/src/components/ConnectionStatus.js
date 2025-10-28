import React, { useState, useEffect } from 'react';
import { Wifi, WifiOff, RefreshCw, CheckCircle, AlertCircle } from 'lucide-react';
import { useServiceWorker } from '../hooks/useServiceWorker';
import { useTheme } from '../contexts/ThemeContext';

const ConnectionStatus = () => {
  const { isOnline, isUpdateAvailable, updateServiceWorker } = useServiceWorker();
  const [localUpdateAvailable, setLocalUpdateAvailable] = useState(false);
  const { isDark } = useTheme();
  const [showStatus, setShowStatus] = useState(false);
  const [lastOfflineTime, setLastOfflineTime] = useState(null);

  useEffect(() => {
    if (!isOnline) {
      setShowStatus(true);
      setLastOfflineTime(Date.now());
    } else if (lastOfflineTime) {
      // Показываем статус "онлайн" на 3 секунды после восстановления
      setShowStatus(true);
      setTimeout(() => {
        setShowStatus(false);
        setLastOfflineTime(null);
      }, 3000);
    }
  }, [isOnline, lastOfflineTime]);

  useEffect(() => {
    setLocalUpdateAvailable(isUpdateAvailable);
  }, [isUpdateAvailable]);

  if (!showStatus && !localUpdateAvailable) {
    return null;
  }

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {/* Статус подключения */}
      {showStatus && (
        <div
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg shadow-lg transition-all duration-300 ${
            isOnline
              ? 'bg-green-500 text-white'
              : 'bg-red-500 text-white'
          }`}
        >
          {isOnline ? (
            <>
              <CheckCircle className="h-5 w-5" />
              <span className="text-sm font-medium">Подключение восстановлено</span>
            </>
          ) : (
            <>
              <WifiOff className="h-5 w-5" />
              <span className="text-sm font-medium">Нет подключения к интернету</span>
            </>
          )}
        </div>
      )}

      {/* Уведомление об обновлении */}
      {localUpdateAvailable && (
        <div className="bg-blue-500 text-white px-4 py-3 rounded-lg shadow-lg max-w-sm">
          <div className="flex items-start space-x-3">
            <RefreshCw className="h-5 w-5 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h4 className="text-sm font-medium mb-1">Доступно обновление</h4>
              <p className="text-xs opacity-90 mb-3">
                Новая версия приложения готова к установке
              </p>
              <div className="flex space-x-2">
                <button
                  onClick={updateServiceWorker}
                  className="bg-white text-blue-500 px-3 py-1 rounded text-xs font-medium hover:bg-gray-100 transition-colors"
                >
                  Обновить
                </button>
                <button
                  onClick={() => setLocalUpdateAvailable(false)}
                  className="text-white opacity-75 hover:opacity-100 text-xs transition-opacity"
                >
                  Позже
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConnectionStatus;
