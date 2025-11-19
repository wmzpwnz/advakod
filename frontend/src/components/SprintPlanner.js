import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Calendar,
  Plus,
  Play,
  Pause,
  Square,
  Target,
  Clock,
  Users,
  BarChart3,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Edit,
  Trash2,
  Eye,
  ArrowRight,
  Zap,
  Flag,
  Settings,
  Download,
  RefreshCw,
  Filter
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import ModuleCard from './ModuleCard';
import EnhancedButton from './EnhancedButton';
import LoadingSpinner from './LoadingSpinner';
import ModuleErrorBoundary from './ModuleErrorBoundary';

const SprintPlanner = () => {
  const { getModuleColor } = useTheme();
  const [sprints, setSprints] = useState([]);
  const [currentSprint, setCurrentSprint] = useState(null);
  const [backlogTasks, setBacklogTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedProject, setSelectedProject] = useState(null);
  
  // Modal states
  const [showSprintModal, setShowSprintModal] = useState(false);
  const [showPlanningModal, setShowPlanningModal] = useState(false);
  const [selectedSprint, setSelectedSprint] = useState(null);
  
  // Sprint planning state
  const [planningData, setPlanningData] = useState({
    capacity: 0,
    commitment: 0,
    selectedTasks: [],
    velocity: 0
  });

  useEffect(() => {
    loadSprintData();
  }, [selectedProject]);

  const loadSprintData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const params = new URLSearchParams();
      if (selectedProject) params.append('project_id', selectedProject);
      
      const [sprintsRes, backlogRes] = await Promise.all([
        fetch(`/api/v1/project/sprints?${params}`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`/api/v1/project/tasks?status=backlog&${params}`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      if (sprintsRes.ok) {
        const sprintsData = await sprintsRes.json();
        setSprints(sprintsData);
        
        // Find current active sprint
        const activeSprint = sprintsData.find(s => s.status === 'active');
        setCurrentSprint(activeSprint);
      }

      if (backlogRes.ok) {
        const backlogData = await backlogRes.json();
        setBacklogTasks(backlogData);
      }

    } catch (err) {
      setError('Ошибка загрузки данных спринтов');
      console.error('Error loading sprint data:', err);
    } finally {
      setLoading(false);
    }
  };

  const createSprint = async (sprintData) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v1/project/sprints', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(sprintData)
      });

      if (response.ok) {
        setShowSprintModal(false);
        loadSprintData();
      } else {
        setError('Ошибка создания спринта');
      }
    } catch (err) {
      setError('Ошибка создания спринта');
    }
  };

  const updateSprintStatus = async (sprintId, status) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/v1/project/sprints/${sprintId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ status })
      });

      if (response.ok) {
        loadSprintData();
      } else {
        setError('Ошибка обновления статуса спринта');
      }
    } catch (err) {
      setError('Ошибка обновления статуса спринта');
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return <Play className="h-4 w-4 text-green-500" />;
      case 'completed': return <CheckCircle className="h-4 w-4 text-blue-500" />;
      case 'cancelled': return <Square className="h-4 w-4 text-red-500" />;
      default: return <Pause className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusLabel = (status) => {
    const labels = {
      planning: 'Планирование',
      active: 'Активный',
      completed: 'Завершен',
      cancelled: 'Отменен'
    };
    return labels[status] || status;
  };

  const calculateSprintProgress = (sprint) => {
    if (!sprint.commitment || sprint.commitment === 0) return 0;
    return Math.min((sprint.completed / sprint.commitment) * 100, 100);
  };

  const formatDate = (date) => {
    return new Date(date).toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  const getDaysRemaining = (endDate) => {
    const end = new Date(endDate);
    const now = new Date();
    const diffTime = end - now;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const renderSprintCard = (sprint, index) => {
    const progress = calculateSprintProgress(sprint);
    const daysRemaining = getDaysRemaining(sprint.end_date);
    const isOverdue = daysRemaining < 0;
    
    return (
      <motion.div
        key={sprint.id}
        className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: index * 0.1 }}
      >
        {/* Sprint Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center mb-2">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mr-3">
                {sprint.name}
              </h3>
              <div className="flex items-center">
                {getStatusIcon(sprint.status)}
                <span className="ml-1 text-sm font-medium">
                  {getStatusLabel(sprint.status)}
                </span>
              </div>
            </div>
            
            {sprint.goal && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                {sprint.goal}
              </p>
            )}
            
            <div className="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
              <span className="flex items-center">
                <Calendar className="h-4 w-4 mr-1" />
                {formatDate(sprint.start_date)} - {formatDate(sprint.end_date)}
              </span>
              
              {sprint.status === 'active' && (
                <span className={`flex items-center ${isOverdue ? 'text-red-600' : 'text-blue-600'}`}>
                  <Clock className="h-4 w-4 mr-1" />
                  {isOverdue 
                    ? `${Math.abs(daysRemaining)} дн. просрочено`
                    : `${daysRemaining} дн. осталось`
                  }
                </span>
              )}
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {sprint.status === 'planning' && (
              <>
                <EnhancedButton
                  variant="module-outline"
                  module="project"
                  size="sm"
                  onClick={() => {
                    setSelectedSprint(sprint);
                    setShowPlanningModal(true);
                  }}
                  icon={<Target className="h-4 w-4" />}
                >
                  Планировать
                </EnhancedButton>
                <EnhancedButton
                  variant="module-outline"
                  module="project"
                  size="sm"
                  onClick={() => updateSprintStatus(sprint.id, 'active')}
                  icon={<Play className="h-4 w-4" />}
                >
                  Запустить
                </EnhancedButton>
              </>
            )}
            
            {sprint.status === 'active' && (
              <EnhancedButton
                variant="module-outline"
                module="project"
                size="sm"
                onClick={() => updateSprintStatus(sprint.id, 'completed')}
                icon={<CheckCircle className="h-4 w-4" />}
              >
                Завершить
              </EnhancedButton>
            )}
            
            <button
              onClick={() => {
                setSelectedSprint(sprint);
                setShowSprintModal(true);
              }}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1"
            >
              <Edit className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Sprint Metrics */}
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {sprint.capacity}
            </div>
            <div className="text-xs text-gray-500">Емкость</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              {sprint.commitment}
            </div>
            <div className="text-xs text-gray-500">Обязательства</div>
          </div>
          
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">
              {sprint.completed}
            </div>
            <div className="text-xs text-gray-500">Выполнено</div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-1">
            <span>Прогресс</span>
            <span>{progress.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-300 ${
                progress >= 100 
                  ? 'bg-green-500' 
                  : progress >= 80 
                    ? 'bg-blue-500' 
                    : progress >= 50 
                      ? 'bg-yellow-500' 
                      : 'bg-red-500'
              }`}
              style={{ width: `${Math.min(progress, 100)}%` }}
            />
          </div>
        </div>

        {/* Velocity */}
        {sprint.velocity > 0 && (
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">Скорость:</span>
            <div className="flex items-center">
              <Zap className="h-4 w-4 text-yellow-500 mr-1" />
              <span className="font-medium">{sprint.velocity}</span>
            </div>
          </div>
        )}
      </motion.div>
    );
  };

  const renderBurndownChart = () => {
    if (!currentSprint || !currentSprint.burndown_data) {
      return (
        <div className="text-center py-8">
          <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500">Нет данных для диаграммы сгорания</p>
        </div>
      );
    }

    // Simplified burndown chart representation
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="font-medium text-gray-900 dark:text-gray-100">
            Диаграмма сгорания
          </h4>
          <div className="flex items-center space-x-4 text-sm text-gray-500">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-blue-500 rounded mr-2"></div>
              <span>Идеальная</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-green-500 rounded mr-2"></div>
              <span>Фактическая</span>
            </div>
          </div>
        </div>
        
        <div className="h-48 bg-gray-50 dark:bg-gray-800 rounded-lg flex items-center justify-center">
          <p className="text-gray-500">График сгорания - в разработке</p>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <LoadingSpinner 
          size="lg" 
          module="project" 
          variant="neon"
          text="Загрузка спринтов..."
        />
      </div>
    );
  }

  return (
    <ModuleErrorBoundary module="project" componentName="SprintPlanner">
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
                  <Target className="h-8 w-8 text-blue-500 mr-3" />
                  Планирование спринтов
                </h1>
                <p className="mt-2 text-gray-600 dark:text-gray-400">
                  Управление спринтами и планирование итераций
                </p>
              </div>
              
              <div className="mt-6 lg:mt-0 flex flex-wrap gap-3">
                <select
                  value={selectedProject || ''}
                  onChange={(e) => setSelectedProject(e.target.value || null)}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                >
                  <option value="">Все проекты</option>
                  <option value="1">АДВАКОД</option>
                  <option value="2">Маркетинг</option>
                </select>

                <EnhancedButton
                  variant="module-outline"
                  module="project"
                  onClick={loadSprintData}
                  icon={<RefreshCw className="h-4 w-4" />}
                >
                  Обновить
                </EnhancedButton>
                
                <EnhancedButton
                  variant="module"
                  module="project"
                  onClick={() => setShowSprintModal(true)}
                  icon={<Plus className="h-4 w-4" />}
                >
                  Новый спринт
                </EnhancedButton>
              </div>
            </div>
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

          {/* Current Sprint Overview */}
          {currentSprint && (
            <motion.div
              className="mb-8"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              <ModuleCard module="project" variant="module-neon">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                    Текущий спринт: {currentSprint.name}
                  </h2>
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(currentSprint.status)}
                    <span className="font-medium">{getStatusLabel(currentSprint.status)}</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  {/* Sprint Info */}
                  <div>
                    <div className="grid grid-cols-3 gap-4 mb-6">
                      <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                        <div className="text-2xl font-bold text-blue-600">
                          {currentSprint.capacity}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Емкость</div>
                      </div>
                      
                      <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                        <div className="text-2xl font-bold text-green-600">
                          {currentSprint.commitment}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Обязательства</div>
                      </div>
                      
                      <div className="text-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                        <div className="text-2xl font-bold text-purple-600">
                          {currentSprint.completed}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Выполнено</div>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600 dark:text-gray-400">Прогресс:</span>
                        <span className="font-medium">{calculateSprintProgress(currentSprint).toFixed(1)}%</span>
                      </div>
                      
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                        <div 
                          className="h-3 bg-gradient-to-r from-blue-500 to-green-500 rounded-full transition-all duration-500"
                          style={{ width: `${Math.min(calculateSprintProgress(currentSprint), 100)}%` }}
                        />
                      </div>
                      
                      <div className="flex justify-between text-sm text-gray-500">
                        <span>Начало: {formatDate(currentSprint.start_date)}</span>
                        <span>Окончание: {formatDate(currentSprint.end_date)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Burndown Chart */}
                  <div>
                    {renderBurndownChart()}
                  </div>
                </div>
              </ModuleCard>
            </motion.div>
          )}

          {/* All Sprints */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                Все спринты
              </h2>
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <span>Всего: {sprints.length}</span>
                <span>•</span>
                <span>Активных: {sprints.filter(s => s.status === 'active').length}</span>
                <span>•</span>
                <span>Завершенных: {sprints.filter(s => s.status === 'completed').length}</span>
              </div>
            </div>

            {sprints.length === 0 ? (
              <ModuleCard module="project" variant="module">
                <div className="text-center py-12">
                  <Target className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                    Нет спринтов
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 mb-6">
                    Создайте свой первый спринт для планирования работы
                  </p>
                  <EnhancedButton
                    variant="module"
                    module="project"
                    onClick={() => setShowSprintModal(true)}
                    icon={<Plus className="h-4 w-4" />}
                  >
                    Создать спринт
                  </EnhancedButton>
                </div>
              </ModuleCard>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {sprints.map((sprint, index) => renderSprintCard(sprint, index))}
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </ModuleErrorBoundary>
  );
};

export default SprintPlanner;