import React, { useState, useEffect } from 'react';
import { 
  Wifi, 
  WifiOff, 
  RefreshCw, 
  CheckCircle, 
  AlertCircle, 
  Clock,
  Activity,
  Zap,
  Settings
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * Улучшенный компонент статуса соединения с расширенными возможностями
 * Реализует требования 6.2, 6.3 из спецификации
 */
const EnhancedConnectionStatus = ({ 
  websocket, 
  onReconnect,
  onForceReconnect,
  showDetails = false,
  autoHide = true,
  className = "" 
}) => {
  const [status, setStatus] = useState(null);
  const [isVisible, setIsVisible] = useState(false);
  const [showDetailedInfo, setShowDetailedInfo] = useState(false);
  const [lastError, setLastError] = useState(null);
  const [reconnectCountdown, setReconnectCountdown] = useState(0);

  useEffect(() => {
    if (!websocket) return;

    const updateStatus = () => {
      const currentStatus = websocket.getStatus();
      const userStatus = websocket.getUserFriendlyStatus();
      setStatus({ ...currentStatus, ...userStatus });
    };

    updateStatus();

    const handleStateChange = (state) => {
      updateStatus();
      
      // Показываем статус при изменениях
      if (['connecting', 'reconnecting', 'failed'].includes(state)) {
        setIsVisible(true);
      } else if (state === 'connected') {
        setIsVisible(true);
        if (autoHide) {
          setTimeout(() => setIsVisible(false), 3000);
        }
      }
    };

    const handleError = (error) => {
      setLastError(error);
      setIsVisible(true);
      updateStatus();
    };

    websocket.on('stateChange', handleStateChange);
    websocket.on('error', handleError);
    websocket.on('open', updateStatus);
    websocket.on('close', updateStatus);

    const interval = setInterval(updateStatus, 5000);

    return () => {
      websocket.off('stateChange', handleStateChange);
      websocket.off('error', handleError);
      websocket.off('open', updateStatus);
      websocket.off('close', updateStatus);
      clearInterval(interval);
    };
  }, [websocket, autoHide]);

  // Обратный отсчет до переподключения
  useEffect(() => {
    if (status?.connectionState === 'reconnecting' && websocket) {
      const startCountdown = () => {
        const delay = websocket.options?.reconnectDelay || 1000;
        const attempts = status.reconnectAttempts || 0;
        const actualDelay = Math.min(delay * Math.pow(2, attempts), 30000);
        
        setReconnectCountdown(Math.ceil(actualDelay / 1000));
        
        const countdownInterval = setInterval(() => {
          setReconnectCountdown(prev => {
            if (prev <= 1) {
              clearInterval(countdownInterval);
              return 0;
            }
            return prev - 1;
          });
        }, 1000);
        
        return countdownInterval;
      };
      
      const interval = startCountdown();
      return () => clearInterval(interval);
    }
  }, [status?.connectionState, status?.reconnectAttempts, websocket]);

  if (!status) return null; 
 const getStatusIcon = () => {
    switch (status.icon) {
      case 'connected':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'connecting':
      case 'reconnecting':
        return (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          >
            <RefreshCw className="h-4 w-4 text-blue-600" />
          </motion.div>
        );
      case 'disconnected':
        return <WifiOff className="h-4 w-4 text-gray-600" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-600" />;
      default:
        return <Wifi className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusColor = () => {
    switch (status.color) {
      case 'green':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'yellow':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'orange':
        return 'bg-orange-50 border-orange-200 text-orange-800';
      case 'red':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'blue':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      case 'gray':
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  const handleReconnectClick = () => {
    if (onForceReconnect) {
      onForceReconnect();
    } else if (onReconnect) {
      onReconnect();
    } else if (websocket) {
      websocket.reconnect();
    }
  };

  // Компактный индикатор для встраивания
  if (!showDetails && !isVisible) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <div className="flex items-center space-x-1">
          <div className={`w-2 h-2 rounded-full ${
            status.connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
          }`}></div>
          <span className={`text-sm font-medium ${
            status.connected ? 'text-green-600' : 'text-red-600'
          }`}>
            {status.connected ? 'Онлайн' : 'Офлайн'}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className={className}>
      <AnimatePresence>
        {(isVisible || showDetails) && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className={`
              flex items-center justify-between p-3 rounded-lg border transition-all duration-300
              ${getStatusColor()}
            `}
          >
            <div className="flex items-center space-x-3">
              {getStatusIcon()}
              <div>
                <div className="text-sm font-medium">{status.text}</div>
                
                {/* Дополнительная информация */}
                {status.reconnectAttempts > 0 && (
                  <div className="text-xs opacity-75">
                    Попытка {status.reconnectAttempts}/{websocket?.options?.maxReconnectAttempts || 10}
                    {reconnectCountdown > 0 && ` • Следующая через ${reconnectCountdown}с`}
                  </div>
                )}
                
                {status.queuedMessages > 0 && (
                  <div className="text-xs opacity-75">
                    {status.queuedMessages} сообщений в очереди
                  </div>
                )}
                
                {lastError && status.connectionState === 'failed' && (
                  <div className="text-xs text-red-600 mt-1">
                    {lastError.message || 'Ошибка соединения'}
                  </div>
                )}
              </div>
            </div>

            <div className="flex items-center space-x-2">
              {/* Кнопка переподключения */}
              {['failed', 'disconnected'].includes(status.connectionState) && (
                <button
                  onClick={handleReconnectClick}
                  className="px-3 py-1 text-xs font-medium bg-white rounded border hover:bg-gray-50 transition-colors"
                >
                  Переподключить
                </button>
              )}

              {/* Кнопка принудительного переподключения */}
              {status.connectionState === 'reconnecting' && (
                <button
                  onClick={handleReconnectClick}
                  className="px-3 py-1 text-xs font-medium bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                >
                  Переподключить сейчас
                </button>
              )}

              {/* Кнопка деталей */}
              {showDetails && (
                <button
                  onClick={() => setShowDetailedInfo(!showDetailedInfo)}
                  className="p-1 hover:bg-white hover:bg-opacity-50 rounded transition-colors"
                >
                  <Activity className="h-4 w-4" />
                </button>
              )}

              {/* Кнопка закрытия */}
              {isVisible && !showDetails && autoHide && (
                <button
                  onClick={() => setIsVisible(false)}
                  className="p-1 hover:bg-white hover:bg-opacity-50 rounded transition-colors"
                >
                  ×
                </button>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Детальная информация */}
      <AnimatePresence>
        {showDetailedInfo && status.stats && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-2 p-3 bg-white rounded-lg border border-gray-200 text-sm"
          >
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="font-medium text-gray-700 mb-2">Статистика соединения</div>
                <div className="space-y-1 text-gray-600">
                  <div className="flex justify-between">
                    <span>Подключений:</span>
                    <span>{status.stats.totalConnections}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Переподключений:</span>
                    <span>{status.stats.totalReconnections}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Сообщений:</span>
                    <span>{status.stats.totalMessages}</span>
                  </div>
                </div>
              </div>
              
              <div>
                <div className="font-medium text-gray-700 mb-2">Время соединения</div>
                <div className="space-y-1 text-gray-600">
                  {status.stats.lastConnectedAt && (
                    <div className="flex items-center space-x-1">
                      <Clock className="h-3 w-3" />
                      <span className="text-xs">
                        {new Date(status.stats.lastConnectedAt).toLocaleTimeString()}
                      </span>
                    </div>
                  )}
                  {status.lastPong && (
                    <div className="flex items-center space-x-1">
                      <Zap className="h-3 w-3" />
                      <span className="text-xs">
                        Ping: {Date.now() - status.lastPong}ms назад
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default EnhancedConnectionStatus;