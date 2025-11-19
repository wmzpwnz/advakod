import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Play, 
  BookOpen, 
  Users, 
  FileText, 
  Shield, 
  MessageSquare,
  TrendingUp,
  Target,
  Bell,
  BarChart3,
  Database,
  Settings,
  HelpCircle,
  X
} from 'lucide-react';
import InteractiveTour from './InteractiveTour';

const AdminTourManager = () => {
  const [activeTour, setActiveTour] = useState(null);
  const [showTourMenu, setShowTourMenu] = useState(false);
  const [completedTours, setCompletedTours] = useState([]);

  // Load completed tours from localStorage
  useEffect(() => {
    const completed = JSON.parse(localStorage.getItem('completedTours') || '[]');
    setCompletedTours(completed);
  }, []);

  // Tour definitions
  const tours = {
    overview: {
      id: 'overview',
      title: 'Обзор админ-панели',
      description: 'Знакомство с основными возможностями',
      icon: BookOpen,
      duration: '5 мин',
      steps: [
        {
          title: 'Добро пожаловать в админ-панель АДВАКОД!',
          description: 'Это интегрированная система управления, которая объединяет все инструменты администрирования в едином интерфейсе.',
          icon: BookOpen,
          target: '.admin-header',
          duration: 4000,
          tips: [
            'Используйте боковое меню для навигации между модулями',
            'Все данные обновляются в реальном времени',
            'Доступные функции зависят от вашей роли'
          ]
        },
        {
          title: 'Навигация и поиск',
          description: 'Боковая панель содержит все модули системы. Используйте поиск для быстрого доступа к нужным функциям.',
          icon: Target,
          target: '.sidebar-nav',
          duration: 5000,
          tips: [
            'Нажмите Ctrl+K для открытия командной палитры',
            'Используйте поиск в верхней части боковой панели',
            'Модули группируются по функциональности'
          ]
        },
        {
          title: 'Дашборд и метрики',
          description: 'Главный дашборд показывает ключевые метрики системы и статус всех компонентов.',
          icon: BarChart3,
          target: '.dashboard-metrics',
          duration: 4000,
          tips: [
            'Метрики обновляются каждые 30 секунд',
            'Кликните на карточку для детального просмотра',
            'Зеленый индикатор означает нормальную работу'
          ]
        },
        {
          title: 'Уведомления и алерты',
          description: 'Система уведомлений информирует о важных событиях в реальном времени.',
          icon: Bell,
          target: '.notification-bell',
          duration: 4000,
          tips: [
            'Красный значок указывает на критические алерты',
            'Настройте типы уведомлений в профиле',
            'Уведомления синхронизируются между вкладками'
          ]
        },
        {
          title: 'Горячие клавиши',
          description: 'Используйте горячие клавиши для быстрой работы с системой.',
          icon: HelpCircle,
          target: '.hotkey-indicator',
          duration: 5000,
          tips: [
            'Ctrl+K - командная палитра',
            'Ctrl+B - переключить боковую панель',
            'Ctrl+H - перейти на главную страницу'
          ]
        }
      ]
    },

    users: {
      id: 'users',
      title: 'Управление пользователями',
      description: 'Работа с пользователями и их данными',
      icon: Users,
      duration: '7 мин',
      steps: [
        {
          title: 'Модуль управления пользователями',
          description: 'Здесь вы можете просматривать, редактировать и управлять всеми пользователями системы.',
          icon: Users,
          target: '.user-management',
          duration: 4000,
          tips: [
            'Используйте фильтры для поиска нужных пользователей',
            'Массовые операции доступны через чекбоксы',
            'Экспорт данных доступен в различных форматах'
          ]
        },
        {
          title: 'Поиск и фильтрация',
          description: 'Мощные инструменты поиска помогают быстро найти нужных пользователей.',
          icon: Target,
          target: '.user-search',
          duration: 4000,
          tips: [
            'Поиск работает по email, имени и ID',
            'Используйте фильтры по статусу и роли',
            'Сохраняйте часто используемые фильтры'
          ]
        },
        {
          title: 'Профиль пользователя',
          description: 'Детальная информация о пользователе включает активность, подписки и историю.',
          icon: FileText,
          target: '.user-profile',
          duration: 5000,
          tips: [
            'Вкладки содержат разные аспекты профиля',
            'История действий помогает в расследованиях',
            'Изменения логируются для аудита'
          ]
        }
      ]
    },

    moderation: {
      id: 'moderation',
      title: 'Система модерации',
      description: 'Модерация контента и геймификация',
      icon: MessageSquare,
      duration: '6 мин',
      steps: [
        {
          title: 'Очередь модерации',
          description: 'Сообщения, требующие модерации, отображаются в приоритетном порядке.',
          icon: MessageSquare,
          target: '.moderation-queue',
          duration: 4000,
          tips: [
            'Приоритет определяется автоматически',
            'Используйте фильтры по категориям проблем',
            'Быстрые действия доступны через горячие клавиши'
          ]
        },
        {
          title: 'Система оценок',
          description: 'Оценивайте качество ответов ИИ по шкале от 1 до 10 звезд.',
          icon: Target,
          target: '.rating-system',
          duration: 4000,
          tips: [
            'Обязательно оставляйте комментарии к оценкам',
            'Низкие оценки помогают улучшить модель',
            'Ваши оценки влияют на обучение ИИ'
          ]
        },
        {
          title: 'Геймификация и рейтинг',
          description: 'Система баллов, рангов и достижений мотивирует модераторов.',
          icon: Target,
          target: '.gamification',
          duration: 5000,
          tips: [
            'Баллы начисляются за качественную модерацию',
            'Участвуйте в еженедельных челленджах',
            'Высокий рейтинг дает дополнительные привилегии'
          ]
        }
      ]
    },

    marketing: {
      id: 'marketing',
      title: 'Маркетинговые инструменты',
      description: 'Воронки продаж, промокоды и аналитика',
      icon: TrendingUp,
      duration: '8 мин',
      steps: [
        {
          title: 'Дашборд маркетинга',
          description: 'Обзор ключевых маркетинговых метрик и воронки продаж.',
          icon: TrendingUp,
          target: '.marketing-dashboard',
          duration: 4000,
          tips: [
            'Воронка показывает конверсию по этапам',
            'Анализируйте падения конверсии',
            'Сегментируйте пользователей по поведению'
          ]
        },
        {
          title: 'Управление промокодами',
          description: 'Создавайте и отслеживайте эффективность промокодов.',
          icon: Target,
          target: '.promo-manager',
          duration: 4000,
          tips: [
            'Настраивайте ограничения по времени и количеству',
            'Отслеживайте использование в реальном времени',
            'Создавайте автоматические промокоды'
          ]
        },
        {
          title: 'Аналитика трафика',
          description: 'Анализ источников трафика и эффективности каналов привлечения.',
          icon: BarChart3,
          target: '.traffic-analytics',
          duration: 5000,
          tips: [
            'UTM параметры отслеживаются автоматически',
            'Сравнивайте эффективность каналов',
            'Оптимизируйте бюджет на основе данных'
          ]
        }
      ]
    },

    project: {
      id: 'project',
      title: 'Управление проектом',
      description: 'Задачи, календарь и ресурсы',
      icon: Target,
      duration: '7 мин',
      steps: [
        {
          title: 'Дашборд проекта',
          description: 'Обзор KPI проекта, прогресса и ключевых метрик.',
          icon: Target,
          target: '.project-dashboard',
          duration: 4000,
          tips: [
            'KPI обновляются в реальном времени',
            'Используйте виджеты для кастомизации',
            'Настройте алерты для критических метрик'
          ]
        },
        {
          title: 'Управление задачами',
          description: 'Канбан-доска для управления задачами и спринтами.',
          icon: Target,
          target: '.task-manager',
          duration: 5000,
          tips: [
            'Перетаскивайте задачи между колонками',
            'Назначайте ответственных и дедлайны',
            'Отслеживайте время выполнения'
          ]
        },
        {
          title: 'Календарь и ресурсы',
          description: 'Планирование событий и отслеживание нагрузки команды.',
          icon: Target,
          target: '.project-calendar',
          duration: 4000,
          tips: [
            'Интеграция с задачами и дедлайнами',
            'Планируйте отпуска и недоступность',
            'Анализируйте загруженность команды'
          ]
        }
      ]
    },

    analytics: {
      id: 'analytics',
      title: 'Продвинутая аналитика',
      description: 'Дашборды, когорты и ML прогнозы',
      icon: BarChart3,
      duration: '9 мин',
      steps: [
        {
          title: 'Конструктор дашбордов',
          description: 'Создавайте персонализированные дашборды с помощью drag-and-drop.',
          icon: BarChart3,
          target: '.dashboard-builder',
          duration: 5000,
          tips: [
            'Перетаскивайте виджеты для создания макета',
            'Настраивайте источники данных',
            'Сохраняйте и делитесь дашбордами'
          ]
        },
        {
          title: 'Когортный анализ',
          description: 'Анализ удержания пользователей и их поведения по когортам.',
          icon: Users,
          target: '.cohort-analysis',
          duration: 4000,
          tips: [
            'Создавайте когорты по различным критериям',
            'Анализируйте LTV и удержание',
            'Сравнивайте поведение разных сегментов'
          ]
        },
        {
          title: 'ML прогнозы',
          description: 'Машинное обучение для прогнозирования и рекомендаций.',
          icon: Target,
          target: '.ml-insights',
          duration: 5000,
          tips: [
            'Прогнозы обновляются ежедневно',
            'Интерпретация результатов доступна',
            'Используйте рекомендации для оптимизации'
          ]
        }
      ]
    }
  };

  const startTour = (tourId) => {
    setActiveTour(tourId);
    setShowTourMenu(false);
  };

  const closeTour = () => {
    setActiveTour(null);
  };

  const isTourCompleted = (tourId) => {
    return completedTours.includes(tourId);
  };

  return (
    <>
      {/* Tour Menu Button */}
      <motion.button
        onClick={() => setShowTourMenu(true)}
        className="fixed bottom-6 right-6 z-40 bg-blue-500 hover:bg-blue-600 text-white p-3 rounded-full shadow-lg transition-colors"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        <HelpCircle className="h-6 w-6" />
      </motion.button>

      {/* Tour Menu Modal */}
      {showTourMenu && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                  Интерактивные туры
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mt-1">
                  Изучите возможности админ-панели с помощью пошаговых туров
                </p>
              </div>
              <button
                onClick={() => setShowTourMenu(false)}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            {/* Tour List */}
            <div className="p-6">
              <div className="grid gap-4">
                {Object.entries(tours).map(([tourId, tour]) => {
                  const Icon = tour.icon;
                  const completed = isTourCompleted(tourId);
                  
                  return (
                    <motion.div
                      key={tourId}
                      className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                        completed
                          ? 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20'
                          : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600'
                      }`}
                      onClick={() => startTour(tourId)}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <div className="flex items-start space-x-4">
                        <div className={`p-3 rounded-lg ${
                          completed
                            ? 'bg-green-100 dark:bg-green-900'
                            : 'bg-blue-100 dark:bg-blue-900'
                        }`}>
                          <Icon className={`h-6 w-6 ${
                            completed
                              ? 'text-green-600 dark:text-green-400'
                              : 'text-blue-600 dark:text-blue-400'
                          }`} />
                        </div>
                        
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                              {tour.title}
                            </h3>
                            <div className="flex items-center space-x-2">
                              <span className="text-sm text-gray-500 dark:text-gray-400">
                                {tour.duration}
                              </span>
                              {completed && (
                                <span className="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs rounded-full">
                                  Завершен
                                </span>
                              )}
                            </div>
                          </div>
                          
                          <p className="text-gray-600 dark:text-gray-400 mt-1">
                            {tour.description}
                          </p>
                          
                          <div className="flex items-center justify-between mt-3">
                            <span className="text-sm text-gray-500 dark:text-gray-400">
                              {tour.steps.length} шагов
                            </span>
                            
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                startTour(tourId);
                              }}
                              className="flex items-center space-x-1 px-3 py-1.5 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600 transition-colors"
                            >
                              <Play className="h-4 w-4" />
                              <span>{completed ? 'Пройти снова' : 'Начать тур'}</span>
                            </button>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>

              {/* Progress Summary */}
              <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Прогресс изучения
                  </span>
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    {completedTours.length} из {Object.keys(tours).length}
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                    style={{ 
                      width: `${(completedTours.length / Object.keys(tours).length) * 100}%` 
                    }}
                  />
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      )}

      {/* Active Tour */}
      {activeTour && (
        <InteractiveTour
          isOpen={true}
          onClose={closeTour}
          tourSteps={tours[activeTour].steps}
          tourId={activeTour}
          autoPlay={false}
          showProgress={true}
          allowSkip={true}
        />
      )}
    </>
  );
};

export default AdminTourManager;