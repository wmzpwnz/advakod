import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, 
  ChevronLeft, 
  ChevronRight, 
  Play, 
  Pause,
  RotateCcw,
  CheckCircle,
  Info,
  ArrowRight,
  Target
} from 'lucide-react';

const InteractiveTour = ({ 
  isOpen, 
  onClose, 
  tourSteps = [], 
  tourId,
  autoPlay = false,
  showProgress = true,
  allowSkip = true 
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(autoPlay);
  const [completedSteps, setCompletedSteps] = useState(new Set());
  const [tourCompleted, setTourCompleted] = useState(false);

  // Auto-advance timer
  useEffect(() => {
    if (!isPlaying || tourCompleted) return;

    const timer = setTimeout(() => {
      if (currentStep < tourSteps.length - 1) {
        nextStep();
      } else {
        completeTour();
      }
    }, tourSteps[currentStep]?.duration || 5000);

    return () => clearTimeout(timer);
  }, [currentStep, isPlaying, tourCompleted, tourSteps]);

  // Mark tour as completed in localStorage
  useEffect(() => {
    if (tourCompleted && tourId) {
      const completedTours = JSON.parse(localStorage.getItem('completedTours') || '[]');
      if (!completedTours.includes(tourId)) {
        completedTours.push(tourId);
        localStorage.setItem('completedTours', JSON.stringify(completedTours));
      }
    }
  }, [tourCompleted, tourId]);

  const nextStep = useCallback(() => {
    if (currentStep < tourSteps.length - 1) {
      setCompletedSteps(prev => new Set([...prev, currentStep]));
      setCurrentStep(prev => prev + 1);
    } else {
      completeTour();
    }
  }, [currentStep, tourSteps.length]);

  const prevStep = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  }, [currentStep]);

  const goToStep = useCallback((stepIndex) => {
    if (stepIndex >= 0 && stepIndex < tourSteps.length) {
      setCurrentStep(stepIndex);
    }
  }, [tourSteps.length]);

  const completeTour = useCallback(() => {
    setCompletedSteps(prev => new Set([...prev, currentStep]));
    setTourCompleted(true);
    setIsPlaying(false);
  }, [currentStep]);

  const restartTour = useCallback(() => {
    setCurrentStep(0);
    setCompletedSteps(new Set());
    setTourCompleted(false);
    setIsPlaying(autoPlay);
  }, [autoPlay]);

  const togglePlayPause = useCallback(() => {
    setIsPlaying(prev => !prev);
  }, []);

  // Highlight target element
  useEffect(() => {
    if (!isOpen || !tourSteps[currentStep]?.target) return;

    const targetElement = document.querySelector(tourSteps[currentStep].target);
    if (targetElement) {
      targetElement.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'center' 
      });
      
      // Add highlight class
      targetElement.classList.add('tour-highlight');
      
      return () => {
        targetElement.classList.remove('tour-highlight');
      };
    }
  }, [isOpen, currentStep, tourSteps]);

  if (!isOpen || tourSteps.length === 0) return null;

  const currentStepData = tourSteps[currentStep];
  const progress = ((currentStep + 1) / tourSteps.length) * 100;

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50" />
      
      {/* Tour Modal */}
      <AnimatePresence>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
        >
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl max-w-md w-full">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center space-x-2">
                <Target className="h-5 w-5 text-blue-500" />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {tourCompleted ? 'Тур завершен!' : `Шаг ${currentStep + 1} из ${tourSteps.length}`}
                </h3>
              </div>
              
              <div className="flex items-center space-x-2">
                {/* Play/Pause button */}
                {!tourCompleted && (
                  <button
                    onClick={togglePlayPause}
                    className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  >
                    {isPlaying ? (
                      <Pause className="h-4 w-4" />
                    ) : (
                      <Play className="h-4 w-4" />
                    )}
                  </button>
                )}
                
                {/* Restart button */}
                {tourCompleted && (
                  <button
                    onClick={restartTour}
                    className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  >
                    <RotateCcw className="h-4 w-4" />
                  </button>
                )}
                
                {/* Close button */}
                {allowSkip && (
                  <button
                    onClick={onClose}
                    className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>

            {/* Progress bar */}
            {showProgress && !tourCompleted && (
              <div className="px-4 pt-2">
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <motion.div
                    className="bg-blue-500 h-2 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
              </div>
            )}

            {/* Content */}
            <div className="p-6">
              {tourCompleted ? (
                <div className="text-center">
                  <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                  <h4 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                    Поздравляем!
                  </h4>
                  <p className="text-gray-600 dark:text-gray-400 mb-4">
                    Вы успешно завершили интерактивный тур по админ-панели. 
                    Теперь вы знаете основные функции и можете эффективно работать с системой.
                  </p>
                  <div className="flex space-x-3">
                    <button
                      onClick={restartTour}
                      className="flex-1 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                    >
                      Пройти снова
                    </button>
                    <button
                      onClick={onClose}
                      className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                    >
                      Закрыть
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  {/* Step icon */}
                  {currentStepData.icon && (
                    <div className="flex justify-center mb-4">
                      <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-full">
                        <currentStepData.icon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                      </div>
                    </div>
                  )}

                  {/* Step title */}
                  <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 text-center">
                    {currentStepData.title}
                  </h4>

                  {/* Step description */}
                  <p className="text-gray-600 dark:text-gray-400 mb-4 text-center">
                    {currentStepData.description}
                  </p>

                  {/* Step tips */}
                  {currentStepData.tips && currentStepData.tips.length > 0 && (
                    <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 mb-4">
                      <div className="flex items-start space-x-2">
                        <Info className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                        <div>
                          <p className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-1">
                            Полезные советы:
                          </p>
                          <ul className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
                            {currentStepData.tips.map((tip, index) => (
                              <li key={index} className="flex items-start space-x-1">
                                <span className="text-blue-500">•</span>
                                <span>{tip}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Interactive element */}
                  {currentStepData.interactive && (
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 mb-4">
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                        Попробуйте сами:
                      </p>
                      <div className="text-sm text-gray-800 dark:text-gray-200">
                        {currentStepData.interactive}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Footer */}
            {!tourCompleted && (
              <div className="flex items-center justify-between p-4 border-t border-gray-200 dark:border-gray-700">
                <button
                  onClick={prevStep}
                  disabled={currentStep === 0}
                  className="flex items-center space-x-1 px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="h-4 w-4" />
                  <span>Назад</span>
                </button>

                {/* Step indicators */}
                <div className="flex space-x-1">
                  {tourSteps.map((_, index) => (
                    <button
                      key={index}
                      onClick={() => goToStep(index)}
                      className={`w-2 h-2 rounded-full transition-colors ${
                        index === currentStep
                          ? 'bg-blue-500'
                          : completedSteps.has(index)
                          ? 'bg-green-500'
                          : 'bg-gray-300 dark:bg-gray-600'
                      }`}
                    />
                  ))}
                </div>

                <button
                  onClick={nextStep}
                  className="flex items-center space-x-1 px-3 py-1.5 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                >
                  <span>{currentStep === tourSteps.length - 1 ? 'Завершить' : 'Далее'}</span>
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            )}
          </div>
        </motion.div>
      </AnimatePresence>

      {/* CSS for highlighting */}
      <style jsx global>{`
        .tour-highlight {
          position: relative;
          z-index: 51;
          box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.5), 0 0 0 8px rgba(59, 130, 246, 0.2);
          border-radius: 8px;
          transition: all 0.3s ease;
        }
      `}</style>
    </>
  );
};

export default InteractiveTour;