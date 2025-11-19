import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BarChart3,
  Calendar,
  Clock,
  Users,
  Target,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Activity,
  DollarSign,
  Zap,
  Award,
  Settings,
  Filter,
  Download,
  RefreshCw,
  Plus,
  Eye,
  Edit,
  MoreHorizontal,
  ArrowUp,
  ArrowDown,
  Minus
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import ModuleCard from './ModuleCard';
import EnhancedButton from './EnhancedButton';
import LoadingSpinner from './LoadingSpinner';
import ModuleErrorBoundary from './ModuleErrorBoundary';

const ProjectDashboard = () => {
  const { getModuleColor } = useTheme();
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedPeriod, setSelectedPeriod] = useState('30d');
  const [refreshing, setRefreshing] = useState(false);

  // Modal states
  const [showProjectModal, setShowProjectModal] = useState(false);
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [showMilestoneModal, setShowMilestoneModal] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, [selectedPeriod]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`/api/v1/project/dashboard?period=${selectedPeriod}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
      } else {
        setError('Ошибка загрузки данных дашборда');
      }
    } catch (err) {
      setError('Ошибка загрузки данных дашборда');
      console.error('Error loading dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const refreshDashboard = async () => {
    setRefreshing(true);
    await loadDashboardData();
    setRefreshing(false);
  };

  const getHealthColor = (health) => {
    switch (health) {
      case 'green': return 'text-green-600';
      case 'yellow': return 'text-yellow-600';
      case 'red': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getHealthIcon = (health) => {
    switch (health) {
      case 'green': return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'yellow': return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
      case 'red': return <AlertTriangle className="h-5 w-5 text-red-600" />;
      default: return <Minus className="h-5 w-5 text-gray-600" />;
    }
  };

  const formatCurrency = (amount, currency = 'RUB') => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  const formatDate = (date) => {
    return new Date(date).toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <LoadingSpinner 
          size="lg" 
          module="project" 
          variant="neon"
          text="Загрузка дашборда проекта..."
        />
      </div>
    );
  }

  return (
    <ModuleErrorBoundary module="project" componentName="ProjectDashboard">
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
                  <BarChart3 className="h-8 w-8 text-blue-500 mr-3" />
                  Управление проектом
                </h1>
                <p className="mt-2 text-gray-600 dark:text-gray-400">
                  Центр управления проектом с KPI, задачами и ресурсами
                </p>
              </div>
              
              <div className="mt-6 lg:mt-0 flex flex-wrap gap-3">
                <select
                  value={selectedPeriod}
                  onChange={(e) => setSelectedPeriod(e.target.value)}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                >
                  <option value="7d">7 дней</option>
                  <option value="30d">30 дней</option>
                  <option value="90d">90 дней</option>
                  <option value="1y">1 год</option>
                </select>

                <EnhancedButton
                  variant="module-outline"
                  module="project"
                  onClick={refreshDashboard}
                  disabled={refreshing}
                  icon={<RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />}
                >
                  Обновить
                </EnhancedButton>
                
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
                  onClick={() => setShowProjectModal(true)}
                  icon={<Plus className="h-4 w-4" />}
                >
                  Новый проект
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

          {/* KPI Cards */}
          <motion.div 
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <ModuleCard module="project" variant="module-neon">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Активные проекты</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {dashboardData?.activeProjects || 0}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    из {dashboardData?.totalProjects || 0} всего
                  </p>
                </div>
                <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                  <Target className="h-6 w-6 text-blue-600" />
                </div>
              </div>
            </ModuleCard>

            <ModuleCard module="project" variant="module">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Просроченные задачи</p>
                  <p className="text-2xl font-bold text-red-600">
                    {dashboardData?.overdueTasks || 0}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Требуют внимания
                  </p>
                </div>
                <div className="p-3 bg-red-100 dark:bg-red-900/30 rounded-lg">
                  <Clock className="h-6 w-6 text-red-600" />
                </div>
              </div>
            </ModuleCard>

            <ModuleCard module="project" variant="module">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Команда</p>
                  <p className="text-2xl font-bold text-green-600">
                    {dashboardData?.totalTeamMembers || 0}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Участников проектов
                  </p>
                </div>
                <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                  <Users className="h-6 w-6 text-green-600" />
                </div>
              </div>
            </ModuleCard>

            <ModuleCard module="project" variant="module">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Бюджет</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {dashboardData?.budgetUtilization || 0}%
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Использование бюджета
                  </p>
                </div>
                <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                  <DollarSign className="h-6 w-6 text-purple-600" />
                </div>
              </div>
            </ModuleCard>
          </motion.div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column - Charts and Analytics */}
            <div className="lg:col-span-2 space-y-8">
              {/* Velocity Trend Chart */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
              >
                <ModuleCard module="project" variant="module">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      Скорость команды
                    </h3>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-500">Последние спринты</span>
                      <TrendingUp className="h-4 w-4 text-green-500" />
                    </div>
                  </div>
                  
                  {dashboardData?.velocityTrend?.length > 0 ? (
                    <div className="space-y-4">
                      {dashboardData.velocityTrend.map((point, index) => (
                        <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                          <div>
                            <p className="font-medium text-gray-900 dark:text-gray-100">
                              {point.sprintName}
                            </p>
                            <p className="text-sm text-gray-500">
                              {formatDate(point.date)}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-lg font-bold text-blue-600">
                              {point.completed}/{point.planned}
                            </p>
                            <p className="text-sm text-gray-500">
                              {((point.completed / point.planned) * 100).toFixed(0)}%
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-500">Нет данных о скорости команды</p>
                    </div>
                  )}
                </ModuleCard>
              </motion.div>

              {/* Resource Utilization */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.3 }}
              >
                <ModuleCard module="project" variant="module">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      Загрузка ресурсов
                    </h3>
                    <EnhancedButton
                      variant="module-outline"
                      module="project"
                      size="sm"
                      icon={<Settings className="h-4 w-4" />}
                    >
                      Настроить
                    </EnhancedButton>
                  </div>
                  
                  {dashboardData?.resourceUtilization?.length > 0 ? (
                    <div className="space-y-4">
                      {dashboardData.resourceUtilization.map((resource, index) => (
                        <div key={index} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-medium text-gray-900 dark:text-gray-100">
                              {resource.userName}
                            </h4>
                            <span className={`text-sm font-medium ${
                              resource.overallocated ? 'text-red-600' : 'text-green-600'
                            }`}>
                              {resource.utilization}%
                            </span>
                          </div>
                          
                          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mb-2">
                            <div 
                              className={`h-2 rounded-full ${
                                resource.overallocated 
                                  ? 'bg-red-500' 
                                  : resource.utilization > 80 
                                    ? 'bg-yellow-500' 
                                    : 'bg-green-500'
                              }`}
                              style={{ width: `${Math.min(resource.utilization, 100)}%` }}
                            />
                          </div>
                          
                          <div className="flex justify-between text-sm text-gray-500">
                            <span>{resource.allocated}ч из {resource.totalCapacity}ч</span>
                            {resource.overallocated && (
                              <span className="text-red-600 font-medium">Перегружен</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-500">Нет данных о загрузке ресурсов</p>
                    </div>
                  )}
                </ModuleCard>
              </motion.div>
            </div>

            {/* Right Column - Upcoming Deadlines and Activity */}
            <div className="space-y-8">
              {/* Upcoming Deadlines */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.4 }}
              >
                <ModuleCard module="project" variant="module">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      Ближайшие дедлайны
                    </h3>
                    <Calendar className="h-5 w-5 text-blue-500" />
                  </div>
                  
                  {dashboardData?.upcomingDeadlines?.length > 0 ? (
                    <div className="space-y-3">
                      {dashboardData.upcomingDeadlines.map((milestone, index) => {
                        const daysLeft = Math.ceil((new Date(milestone.dueDate) - new Date()) / (1000 * 60 * 60 * 24));
                        const isOverdue = daysLeft < 0;
                        const isUrgent = daysLeft <= 3 && daysLeft >= 0;
                        
                        return (
                          <div key={index} className={`p-3 rounded-lg border-l-4 ${
                            isOverdue 
                              ? 'border-red-500 bg-red-50 dark:bg-red-900/20' 
                              : isUrgent 
                                ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20'
                                : 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                          }`}>
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <h4 className="font-medium text-gray-900 dark:text-gray-100">
                                  {milestone.name}
                                </h4>
                                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                  {formatDate(milestone.dueDate)}
                                </p>
                                <div className="flex items-center mt-2">
                                  <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mr-2">
                                    <div 
                                      className="bg-blue-500 h-1.5 rounded-full"
                                      style={{ width: `${milestone.progress}%` }}
                                    />
                                  </div>
                                  <span className="text-xs text-gray-500">
                                    {milestone.progress}%
                                  </span>
                                </div>
                              </div>
                              <div className="text-right">
                                <span className={`text-sm font-medium ${
                                  isOverdue 
                                    ? 'text-red-600' 
                                    : isUrgent 
                                      ? 'text-yellow-600'
                                      : 'text-blue-600'
                                }`}>
                                  {isOverdue 
                                    ? `${Math.abs(daysLeft)} дн. просрочено`
                                    : daysLeft === 0 
                                      ? 'Сегодня'
                                      : `${daysLeft} дн.`
                                  }
                                </span>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-500">Нет ближайших дедлайнов</p>
                    </div>
                  )}
                </ModuleCard>
              </motion.div>

              {/* Recent Activity */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.5 }}
              >
                <ModuleCard module="project" variant="module">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      Последняя активность
                    </h3>
                    <Activity className="h-5 w-5 text-green-500" />
                  </div>
                  
                  {dashboardData?.recentActivity?.length > 0 ? (
                    <div className="space-y-3">
                      {dashboardData.recentActivity.map((activity, index) => (
                        <div key={index} className="flex items-start space-x-3 p-3 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg transition-colors">
                          <div className="flex-shrink-0">
                            {activity.type === 'task_completed' && <CheckCircle className="h-5 w-5 text-green-500" />}
                            {activity.type === 'task_created' && <Plus className="h-5 w-5 text-blue-500" />}
                            {activity.type === 'milestone_reached' && <Award className="h-5 w-5 text-purple-500" />}
                            {activity.type === 'sprint_started' && <Zap className="h-5 w-5 text-yellow-500" />}
                            {activity.type === 'sprint_completed' && <Target className="h-5 w-5 text-green-500" />}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-gray-900 dark:text-gray-100">
                              <span className="font-medium">{activity.userName}</span>
                              {' '}
                              {activity.description}
                            </p>
                            <p className="text-xs text-gray-500 mt-1">
                              {new Date(activity.createdAt).toLocaleString('ru-RU')}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-500">Нет недавней активности</p>
                    </div>
                  )}
                </ModuleCard>
              </motion.div>

              {/* Quick Actions */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.6 }}
              >
                <ModuleCard module="project" variant="module">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                    Быстрые действия
                  </h3>
                  
                  <div className="space-y-3">
                    <EnhancedButton
                      variant="module-outline"
                      module="project"
                      className="w-full justify-start"
                      onClick={() => setShowTaskModal(true)}
                      icon={<Plus className="h-4 w-4" />}
                    >
                      Создать задачу
                    </EnhancedButton>
                    
                    <EnhancedButton
                      variant="module-outline"
                      module="project"
                      className="w-full justify-start"
                      onClick={() => setShowMilestoneModal(true)}
                      icon={<Target className="h-4 w-4" />}
                    >
                      Добавить веху
                    </EnhancedButton>
                    
                    <EnhancedButton
                      variant="module-outline"
                      module="project"
                      className="w-full justify-start"
                      icon={<Calendar className="h-4 w-4" />}
                    >
                      Планировать спринт
                    </EnhancedButton>
                    
                    <EnhancedButton
                      variant="module-outline"
                      module="project"
                      className="w-full justify-start"
                      icon={<BarChart3 className="h-4 w-4" />}
                    >
                      Создать отчет
                    </EnhancedButton>
                  </div>
                </ModuleCard>
              </motion.div>
            </div>
          </div>
        </div>
      </div>
    </ModuleErrorBoundary>
  );
};

export default ProjectDashboard;