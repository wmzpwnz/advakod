import React, { useState, useEffect } from 'react';
import { Bot, Square, Clock, Zap, Brain } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

/**
 * Компонент индикатора "ИИ думает..." с возможностью остановки
 * Реализует требования 6.4, 6.5 из спецификации
 */
const AIThinkingIndicator = ({ 
  isGenerating, 
  onStop, 
  startTime,
  estimatedTime,
  className = "",
  variant = "default" // "default", "compact", "detailed"
}) => {
  const [elapsedTime, setElapsedTime] = useState(0);
  const [thinkingPhase, setThinkingPhase] = useState(0);

  // Фазы "размышления" ИИ для более интересного отображения
  const thinkingPhases = [
    { text: "ИИ анализирует ваш вопрос...", icon: Brain },
    { text: "ИИ ищет релевантную информацию...", icon: Zap },
    { text: "ИИ формулирует ответ...", icon: Bot },
    { text: "ИИ проверяет точность ответа...", icon: Clock }
  ];

  // Обновление времени и фазы
  useEffect(() => {
    if (!isGenerating || !startTime) {
      setElapsedTime(0);
      setThinkingPhase(0);
      return;
    }

    const interval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      setElapsedTime(elapsed);

      // Меняем фазу каждые 5 секунд
      const phase = Math.floor(elapsed / 5) % thinkingPhases.length;
      setThinkingPhase(phase);
    }, 1000);

    return () => clearInterval(interval);
  }, [isGenerating, startTime, thinkingPhases.length]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}:${secs.toString().padStart(2, '0')}` : `${secs}с`;
  };

  const getProgressPercentage = () => {
    if (!estimatedTime) return 0;
    return Math.min((elapsedTime / estimatedTime) * 100, 95); // Максимум 95% до завершения
  };

  const currentPhase = thinkingPhases[thinkingPhase];
  const PhaseIcon = currentPhase.icon;

  if (!isGenerating) return null;

  if (variant === "compact") {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full"
        />
        <span className="text-sm text-gray-600">ИИ думает...</span>
        {onStop && (
          <button
            onClick={onStop}
            className="p-1 text-red-600 hover:text-red-700 hover:bg-red-50 rounded transition-colors"
            title="Остановить генерацию"
          >
            <Square className="w-3 h-3" />
          </button>
        )}
      </div>
    );
  }

  if (variant === "detailed") {
    return (
      <div className={`bg-white border border-gray-200 rounded-lg p-4 shadow-sm ${className}`}>
        <div className="flex items-start space-x-3">
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            >
              <Bot className="w-4 h-4 text-white" />
            </motion.div>
          </div>
          
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <PhaseIcon className="w-4 h-4 text-blue-600" />
                <AnimatePresence mode="wait">
                  <motion.span
                    key={thinkingPhase}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="text-sm font-medium text-gray-700"
                  >
                    {currentPhase.text}
                  </motion.span>
                </AnimatePresence>
              </div>
              
              <div className="flex items-center space-x-2">
                <span className="text-xs text-gray-500">
                  {formatTime(elapsedTime)}
                </span>
                {onStop && (
                  <button
                    onClick={onStop}
                    className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors flex items-center space-x-1"
                    title="Остановить генерацию"
                  >
                    <Square className="w-3 h-3" />
                    <span>Остановить</span>
                  </button>
                )}
              </div>
            </div>
            
            {/* Прогресс-бар (если есть оценка времени) */}
            {estimatedTime && (
              <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                <motion.div
                  className="bg-blue-600 h-2 rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${getProgressPercentage()}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>
            )}
            
            {/* Дополнительная информация */}
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>
                {estimatedTime ? `Примерное время: ${formatTime(estimatedTime)}` : 'Генерация в процессе...'}
              </span>
              {elapsedTime > 30 && (
                <span className="text-orange-600">
                  Сложный вопрос, требует больше времени
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Default variant
  return (
    <div className={`flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg ${className}`}>
      <div className="flex items-center space-x-3">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full"
        />
        
        <div>
          <AnimatePresence mode="wait">
            <motion.div
              key={thinkingPhase}
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              className="flex items-center space-x-2"
            >
              <PhaseIcon className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium text-gray-700">
                {currentPhase.text}
              </span>
            </motion.div>
          </AnimatePresence>
          
          <div className="flex items-center space-x-2 mt-1">
            <span className="text-xs text-gray-500">
              {formatTime(elapsedTime)}
            </span>
            {elapsedTime > 60 && (
              <span className="text-xs text-orange-600">
                • Сложный запрос
              </span>
            )}
          </div>
        </div>
      </div>
      
      {onStop && (
        <button
          onClick={onStop}
          className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors flex items-center space-x-1"
          title="Остановить генерацию"
        >
          <Square className="w-3 h-3" />
          <span>Остановить</span>
        </button>
      )}
    </div>
  );
};

export default AIThinkingIndicator;