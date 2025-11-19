import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Clock,
  Play,
  Pause,
  Square,
  Plus,
  Calendar,
  BarChart3,
  Download,
  Filter,
  Search,
  Timer,
  DollarSign,
  Target,
  AlertTriangle,
  CheckCircle,
  Edit,
  Trash2,
  RefreshCw
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import ModuleCard from './ModuleCard';
import EnhancedButton from './EnhancedButton';
import LoadingSpinner from './LoadingSpinner';
import ModuleErrorBoundary from './ModuleErrorBoundary';

const TimeTracker = () => {
  const { getModuleColor } = useTheme();
  const [timeEntries, setTimeEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTimer, setActiveTimer] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState('week');
  const [filters, setFilters] = useState({
    project: '',
    user: '',
    billable: ''
  });

  // Timer state
  const [timerData, setTimerData] = useState({
    taskId: null,
    projectId: null,
    description: '',
    startTime: null,
    elapsedTime: 0
  });

  // Modal states
  const [showEntryModal, setShowEntryModal] = useState(false);
  const [selectedEntry, setSelectedEntry] = useState(null);

  useEffect(() => {
    loadTimeEntries();
  }, [selectedPeriod, filters]);

  useEffect(() => {
    let interval;
    if (activeTimer) {
      interval = setInterval(() => {
        setTimerData(prev => ({
          ...prev,
          elapsedTime: Date.now() - prev.startTime
        }));
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [activeTimer]);

  const loadTimeEntries = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const params = new URLSearchParams({
        period: selectedPeriod,
        ...filters
      });
      
      const response = await fetch(`/api/v1/project/time-entries?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setTimeEntries(data);
      } else {
        setError('Ошибка загрузки записей времени');
      }
    } catch (err) {
      console.error('Error loading time entries:', err);
      setError('Ошибка загрузки записей времени');
    } finally {
      setLoading(false);
    }
  };

  const startTimer = (taskId = null, projectId = null, description = '') => {
    setTimerData({
      taskId,
      projectId,
      description: description || 'Работа над задачей',
      startTime: Date.now(),
      elapsedTime: 0
    });
    setActiveTimer(true);
  };

  const stopTimer = async () => {
    if (!activeTimer || !timerData.startTime) {
      return;
    }

    const hours = Math.max(timerData.elapsedTime / (1000 * 60 * 60), 0.01); // Minimum 1 minute

    const entryData = {
      task_id: timerData.taskId,
      project_id: timerData.projectId,
      description: timerData.description,
      hours,
      date: new Date().toISOString(),
      billable: true
    });

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v1/project/time-entries', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(entryData)
      });

      if (response.ok) {
        setActiveTimer(false);
        setTimerData({
          taskId: null,
          projectId: null,
          description: '',
          startTime: null,
          elapsedTime: 0
        });
        loadTimeEntries();
      } else {
        setError('Ошибка сохранения записи времени');
      }
    } catch (err) {
      setError('Ошибка сохранения записи времени');
    }
  };

  const formatTime = (milliseconds) => {
    const totalSeconds = Math.floor(milliseconds / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  const formatHours = (hours) => {
    return `${hours.toFixed(2)}ч`;
  };

  const calculateTotalHours = () => {
    return timeEntries.reduce((total, entry) => total + entry.hours, 0);
  };

  const calculateBillableHours = () => {
    return timeEntries
      .filter(entry => entry.billable)
      .reduce((total, entry) => total + entry.hours, 0);
  };

  const calculateRevenue = () => {
    return timeEntries
      .filter(entry => entry.billable && entry.hourly_rate)
      .reduce((total, entry) => total + (entry.hours * entry.hourly_rate), 0);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <LoadingSpinner 
          size="lg" 
          module="project" 
          variant="neon"
          text="Загрузка учета времени..."
        />
      </div>
    );
  }

  return (
    <ModuleErrorBoundary module="project" componentName="TimeTracker">
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
                  <Clock className="h-8 w-8 text-blue-500 mr-3" />
                  Учет времени
                </h1>
                <p className="mt-2 text-gray-600 dark:text-gray-400">
                  Отслеживание времени работы и оценка задач
                </p>
              </div>
              
              <div className="mt-6 lg:mt-0 flex flex-wrap gap-3">
                <select
                  value={selectedPeriod}
                  onChange={(e) => setSelectedPeriod(e.target.value)}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                >
                  <option value="today">Сегодня</option>
                  <option value="week">Эта неделя</option>
                  <option value="month">Этот месяц</option>
                  <option value="year">Этот год</option>
                </select>

                <EnhancedButton
                  variant="module-outline"
                  module="project"
                  icon={<Download className="h-4 w-4" />}
                >
                  Экспорт
                </EnhancedButton>
                
                <EnhancedButton
                  variant="module"
                  module="project"
                  onClick={() => setShowEntryModal(true)}
                  icon={<Plus className="h-4 w-4" />}
                >
                  Добавить запись
                </EnhancedButton>
              </div>
            </div>
          </motion.div>

          {/* Timer Widget */}
          <motion.div
            className="mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <ModuleCard module="project" variant="module-neon">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold font-mono text-blue-600">
                      {formatTime(timerData.elapsedTime)}
                    </div>
                    <div className="text-sm text-gray-500">
                      Текущая сессия
                    </div>
                  </div>
                  
                  {activeTimer && timerData.description && (
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      <div className="font-medium text-gray-900 dark:text-gray-100 mb-1">
                        {timerData.description}
                      </div>
                      <div>
                        Начато: {new Date(timerData.startTime).toLocaleTimeString('ru-RU')}
                      </div>
                    </div>
                  )}
                </div>
                
                <div className="flex items-center space-x-3">
                  {!activeTimer ? (
                    <EnhancedButton
                      variant="module"
                      module="project"
                      onClick={() => startTimer()}
                      icon={<Play className="h-4 w-4" />}
                    >
                      Начать
                    </EnhancedButton>
                  ) : (
                    <>
                      <EnhancedButton
                        variant="module-outline"
                        module="project"
                        onClick={stopTimer}
                        icon={<Square className="h-4 w-4" />}
                      >
                        Остановить
                      </EnhancedButton>
                    </>
                  )}
                </div>
              </div>
            </ModuleCard>
          </motion.div>

          {/* Statistics Cards */}
          <motion.div 
            className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <ModuleCard module="project" variant="module">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Всего часов</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {formatHours(calculateTotalHours())}
                  </p>
                </div>
                <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                  <Clock className="h-6 w-6 text-blue-600" />
                </div>
              </div>
            </ModuleCard>

            <ModuleCard module="project" variant="module">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Оплачиваемые</p>
                  <p className="text-2xl font-bold text-green-600">
                    {formatHours(calculateBillableHours())}
                  </p>
                </div>
                <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                  <DollarSign className="h-6 w-6 text-green-600" />
                </div>
              </div>
            </ModuleCard>

            <ModuleCard module="project" variant="module">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Доход</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {calculateRevenue().toLocaleString('ru-RU', {
                      style: 'currency',
                      currency: 'RUB'
                    })}
                  </p>
                </div>
                <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                  <Target className="h-6 w-6 text-purple-600" />
                </div>
              </div>
            </ModuleCard>
          </motion.div>

          {/* Filters */}
          <motion.div
            className="mb-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <ModuleCard module="project" variant="module">
              <div className="flex flex-col lg:flex-row lg:items-center space-y-4 lg:space-y-0 lg:space-x-4">
                {/* Search */}
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Поиск записей..."
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  />
                </div>
                
                {/* Project Filter */}
                <select
                  value={filters.project}
                  onChange={(e) => setFilters(prev => ({ ...prev, project: e.target.value }))}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                >
                  <option value="">Все проекты</option>
                  <option value="1">АДВАКОД</option>
                  <option value="2">Маркетинг</option>
                </select>
                
                {/* Billable Filter */}
                <select
                  value={filters.billable}
                  onChange={(e) => setFilters(prev => ({ ...prev, billable: e.target.value }))}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                >
                  <option value="">Все записи</option>
                  <option value="true">Оплачиваемые</option>
                  <option value="false">Неоплачиваемые</option>
                </select>
              </div>
            </ModuleCard>
          </motion.div>

          {error && (
            <motion.div
              className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className="flex items-center">
                <AlertTriangle className="h-5 w-5 text-red-600 mr-2" />
                <span className="text-red-800 dark:text-red-300">{error}</span>
              </div>
            </motion.div>
          )}

          {/* Time Entries List */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            <ModuleCard module="project" variant="module">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                  Записи времени
                </h2>
                <div className="flex items-center space-x-2">
                  <EnhancedButton
                    variant="module-outline"
                    module="project"
                    size="sm"
                    onClick={loadTimeEntries}
                    icon={<RefreshCw className="h-4 w-4" />}
                  >
                    Обновить
                  </EnhancedButton>
                </div>
              </div>

              {timeEntries.length === 0 ? (
                <div className="text-center py-12">
                  <Timer className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                    Нет записей времени
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 mb-6">
                    Начните отслеживать время или добавьте запись вручную
                  </p>
                  <EnhancedButton
                    variant="module"
                    module="project"
                    onClick={() => setShowEntryModal(true)}
                    icon={<Plus className="h-4 w-4" />}
                  >
                    Добавить запись
                  </EnhancedButton>
                </div>
              ) : (
                <div className="space-y-4">
                  {timeEntries.map((entry, index) => (
                    <motion.div
                      key={entry.id}
                      className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: index * 0.05 }}
                    >
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h4 className="font-medium text-gray-900 dark:text-gray-100">
                            {entry.description}
                          </h4>
                          {entry.billable && (
                            <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 text-xs rounded-full">
                              Оплачиваемо
                            </span>
                          )}
                          {entry.status === 'approved' && (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          )}
                        </div>
                        
                        <div className="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
                          {entry.project_name && (
                            <span>{entry.project_name}</span>
                          )}
                          {entry.task_title && (
                            <span>• {entry.task_title}</span>
                          )}
                          <span>• {new Date(entry.date).toLocaleDateString('ru-RU')}</span>
                          <span>• {entry.user_name}</span>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-4">
                        <div className="text-right">
                          <div className="font-semibold text-gray-900 dark:text-gray-100">
                            {formatHours(entry.hours)}
                          </div>
                          {entry.hourly_rate && entry.billable && (
                            <div className="text-sm text-gray-500">
                              {(entry.hours * entry.hourly_rate).toLocaleString('ru-RU', {
                                style: 'currency',
                                currency: entry.currency || 'RUB'
                              })}
                            </div>
                          )}
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => {
                              setSelectedEntry(entry);
                              setShowEntryModal(true);
                            }}
                            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"
                          >
                            <Edit className="h-4 w-4" />
                          </button>
                          <button className="text-gray-400 hover:text-red-600 p-1">
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </ModuleCard>
          </motion.div>
        </div>
      </div>
    </ModuleErrorBoundary>
  );
};

export default TimeTracker;