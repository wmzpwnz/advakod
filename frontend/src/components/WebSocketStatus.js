import React, { useState, useEffect } from 'react';
import { 
  Wifi, 
  WifiOff, 
  RefreshCw, 
  CheckCircle, 
  AlertCircle, 
  Clock,
  Activity,
  Zap
} from 'lucide-react';

/**
 * Компонент для отображения статуса WebSocket соединения
 * Реализует требования 6.3 из спецификации
 */
const WebSocketStatus = ({ 
  websocket, 
  showDetails = false, 
  onReconnect,
  className = "" 
}) => {
  const [status, setStatus] = useState(null);
  const [isVisible, setIsVisible] = useState(false);
  const [showDetailedInfo, setShowDetailedInfo] = useState(false);

  useEffect(() => {
    if (!websocket) return;

    const updateStatus = () => {
      const currentStatus = websocket.getStatus();
      const userStatus = websocket.getUserFriendlyStatus();
      setStatus({ ...currentStatus, ...userStatus });
    };

    // Обновляем статус сразу
    updateStatus();

    // Подписываемся на изменения состояния
    const handleStateChange = (state) => {
      updateStatus();
      
      // Показываем статус при изменениях
      if (state === 'connecting' || state === 'reconnecting' || state === 'failed') {
        setIsVisible(true);
      } else if (state === 'connected') {
        setIsVisible(true);
        // Скрываем через 3 секунды после успешного подключения
        setTimeout(() => setIsVisible(false), 3000);
      }
    };

    const handleError = () => {
      setIsVisible(true);
      updateStatus();
    };

    websocket.on('stateChange', handleStateChange);
    websocket.on('error', handleError);
    websocket.on('open', updateStatus);
    websocket.on('close', updateStatus);

    // Периодически обновляем статус
    const interval = setInterval(updateStatus, 5000);

    return () => {
      websocket.off('stateChange', handleStateChange);
      websocket.off('error', handleError);
      websocket.off('open', updateStatus);
      websocket.off('close', updateStatus);
      clearInterval(interval);
    };
  }, [websocket]);

  if (!status) return null;

  const getStatusIcon = () => {
    switch (status.icon) {
      case 'connected':
        return <CheckCircle className="h-4 w-4" />;
      case 'connecting':
      case 'reconnecting':
        return <RefreshCw className="h-4 w-4 animate-spin" />;
      case 'disconnected':
        return <WifiOff className="h-4 w-4" />;
      case 'error':
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <Wifi className="h-4 w-4" />;
    }
  };

  const getStatusColor = () => {
    switch (status.color) {
      case 'green':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'yellow':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'orange':
        return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'red':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'gray':
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  // Компактный индикатор для встраивания в интерфейс
  if (!showDetails && !isVisible) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <div className={`flex items-center space-x-1 ${status.color === 'green' ? 'text-green-600' : 'text-red-600'}`}>
          <div className={`w-2 h-2 rounded-full ${
            status.connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
          }`}></div>
          <span className="text-sm font-medium">
            {status.connected ? 'Онлайн' : 'Офлайн'}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className={`${className}`}>
      {/* Основной статус */}
      {(isVisible || showDetails) && (
        <div className={`
          flex items-center justify-between p-3 rounded-lg border transition-all duration-300
          ${getStatusColor()}
        `}>
          <div className="flex items-center space-x-3">
            {getStatusIcon()}
            <div>
              <div className="text-sm font-medium">{status.text}</div>
              {status.reconnectAttempts > 0 && (
                <div className="text-xs opacity-75">
                  Попытка {status.reconnectAttempts}/{websocket.options.maxReconnectAttempts}
                </div>
              )}
              {status.queuedMessages > 0 && (
                <div className="text-xs opacity-75">
                  {status.queuedMessages} сообщений в очереди
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* Кнопка переподключения */}
            {(status.connectionState === 'failed' || status.connectionState === 'disconnected') && (
              <button
                onClick={() => {
                  if (onReconnect) {
                    onReconnect();
                  } else if (websocket) {
                    websocket.reconnect();
                  }
                }}
                className="px-3 py-1 text-xs font-medium bg-white rounded border hover:bg-gray-50 transition-colors"
              >
                Переподключить
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
            {isVisible && !showDetails && (
              <button
                onClick={() => setIsVisible(false)}
                className="p-1 hover:bg-white hover:bg-opacity-50 rounded transition-colors"
              >
                ×
              </button>
            )}
          </div>
        </div>
      )}

      {/* Детальная информация */}
      {showDetailedInfo && status.stats && (
        <div className="mt-2 p-3 bg-white rounded-lg border border-gray-200 text-sm">
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
        </div>
      )}
    </div>
  );
};

export default WebSocketStatus;