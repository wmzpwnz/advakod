import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Wifi, 
  WifiOff, 
  AlertCircle, 
  CheckCircle, 
  Clock,
  RefreshCw,
  Users,
  Activity
} from 'lucide-react';

const RealTimeStatusIndicator = ({ 
  connectionStatus, 
  isConnected, 
  onlineUsers = 0,
  lastUpdate,
  onReconnect,
  className = '' 
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const [lastUpdateText, setLastUpdateText] = useState('');

  // Update last update text
  useEffect(() => {
    if (!lastUpdate) return;

    const updateText = () => {
      const now = new Date();
      const diff = Math.floor((now - lastUpdate) / 1000);
      
      if (diff < 60) {
        setLastUpdateText(`${diff}с назад`);
      } else if (diff < 3600) {
        setLastUpdateText(`${Math.floor(diff / 60)}м назад`);
      } else {
        setLastUpdateText(`${Math.floor(diff / 3600)}ч назад`);
      }
    };

    updateText();
    const interval = setInterval(updateText, 1000);
    return () => clearInterval(interval);
  }, [lastUpdate]);

  const getStatusConfig = () => {
    switch (connectionStatus) {
      case 'connected':
        return {
          icon: CheckCircle,
          color: 'text-green-500',
          bgColor: 'bg-green-100 dark:bg-green-900/20',
          borderColor: 'border-green-200 dark:border-green-800',
          text: 'Подключено',
          description: 'Real-time обновления активны'
        };
      case 'connecting':
        return {
          icon: RefreshCw,
          color: 'text-yellow-500',
          bgColor: 'bg-yellow-100 dark:bg-yellow-900/20',
          borderColor: 'border-yellow-200 dark:border-yellow-800',
          text: 'Подключение...',
          description: 'Устанавливается соединение'
        };
      case 'disconnected':
        return {
          icon: WifiOff,
          color: 'text-gray-500',
          bgColor: 'bg-gray-100 dark:bg-gray-900/20',
          borderColor: 'border-gray-200 dark:border-gray-800',
          text: 'Отключено',
          description: 'Real-time обновления недоступны'
        };
      case 'error':
        return {
          icon: AlertCircle,
          color: 'text-red-500',
          bgColor: 'bg-red-100 dark:bg-red-900/20',
          borderColor: 'border-red-200 dark:border-red-800',
          text: 'Ошибка',
          description: 'Проблема с подключением'
        };
      default:
        return {
          icon: Clock,
          color: 'text-gray-400',
          bgColor: 'bg-gray-100 dark:bg-gray-900/20',
          borderColor: 'border-gray-200 dark:border-gray-800',
          text: 'Неизвестно',
          description: 'Статус неопределен'
        };
    }
  };

  const statusConfig = getStatusConfig();
  const StatusIcon = statusConfig.icon;

  return (
    <div className={`relative ${className}`}>
      {/* Main status indicator */}
      <motion.div
        className={`
          flex items-center space-x-2 px-3 py-2 rounded-lg border cursor-pointer
          ${statusConfig.bgColor} ${statusConfig.borderColor}
          hover:shadow-md transition-all duration-200
        `}
        onClick={() => setShowDetails(!showDetails)}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
      >
        <motion.div
          animate={connectionStatus === 'connecting' ? { rotate: 360 } : { rotate: 0 }}
          transition={{ duration: 1, repeat: connectionStatus === 'connecting' ? Infinity : 0 }}
        >
          <StatusIcon className={`w-4 h-4 ${statusConfig.color}`} />
        </motion.div>
        
        <span className={`text-sm font-medium ${statusConfig.color}`}>
          {statusConfig.text}
        </span>
        
        {isConnected && onlineUsers > 0 && (
          <div className="flex items-center space-x-1 text-xs text-gray-500">
            <Users className="w-3 h-3" />
            <span>{onlineUsers}</span>
          </div>
        )}
        
        {/* Connection pulse indicator */}
        {isConnected && (
          <motion.div
            className="w-2 h-2 bg-green-500 rounded-full"
            animate={{ opacity: [1, 0.3, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
        )}
      </motion.div>

      {/* Detailed status popup */}
      <AnimatePresence>
        {showDetails && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            className="absolute top-full right-0 mt-2 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50"
          >
            <div className="p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                  Статус Real-time соединения
                </h3>
                <button
                  onClick={() => setShowDetails(false)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  ×
                </button>
              </div>
              
              <div className="space-y-3">
                {/* Connection status */}
                <div className="flex items-center space-x-3">
                  <StatusIcon className={`w-5 h-5 ${statusConfig.color}`} />
                  <div>
                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                      {statusConfig.text}
                    </div>
                    <div className="text-xs text-gray-500">
                      {statusConfig.description}
                    </div>
                  </div>
                </div>
                
                {/* Online users */}
                {isConnected && (
                  <div className="flex items-center space-x-3">
                    <Users className="w-5 h-5 text-blue-500" />
                    <div>
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {onlineUsers} активных админов
                      </div>
                      <div className="text-xs text-gray-500">
                        Подключены к системе
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Last update */}
                {lastUpdate && (
                  <div className="flex items-center space-x-3">
                    <Activity className="w-5 h-5 text-green-500" />
                    <div>
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        Последнее обновление
                      </div>
                      <div className="text-xs text-gray-500">
                        {lastUpdateText}
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Reconnect button for error states */}
                {(connectionStatus === 'error' || connectionStatus === 'disconnected') && onReconnect && (
                  <motion.button
                    onClick={onReconnect}
                    className="w-full mt-3 px-3 py-2 bg-blue-500 text-white text-sm rounded-md hover:bg-blue-600 transition-colors"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    Переподключиться
                  </motion.button>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default RealTimeStatusIndicator;