import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Users,
  Plus,
  Calendar,
  Clock,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  User,
  Settings,
  Filter,
  Download,
  RefreshCw,
  Edit,
  Eye,
  BarChart3,
  Target,
  Activity,
  Percent,
  DollarSign,
  Award,
  Zap
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import ModuleCard from './ModuleCard';
import EnhancedButton from './EnhancedButton';
import LoadingSpinner from './LoadingSpinner';
import ModuleErrorBoundary from './ModuleErrorBoundary';

const ResourceTracker = () => {
  const { getModuleColor } = useTheme();
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedPeriod, setSelectedPeriod] = useState('current');
  const [viewMode, setViewMode] = useState('overview'); // overview, detailed, calendar
  const [filters, setFilters] = useState({
    department: '',
    role: '',
    overallocated: false
  });

  // Modal states
  const [showAllocationModal, setShowAllocationModal] = useState(false);
  const [showAvailabilityModal, setShowAvailabilityModal] = useState(false);
  const [selectedResource, setSelectedResource] = useState(null);

  useEffect(() => {
    loadResourceData();
  }, [selectedPeriod, filters]);

  const loadResourceData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const params = new URLSearchParams({
        period: selectedPeriod,
        ...filters
      });
      
      const response = await fetch(`/api/v1/project/resources?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setResources(data);
      } else {
        // Mock data for demonstration
        setResources([
          {
            id: 1,
            user_id: 1,
            user_name: 'Алексей Иванов',
            email: 'alexey@advakod.ru',
            role: 'Senior Developer',
            department: 'Engineering',
            total_capacity: 40,
            current_allocation: 85,
            utilization: 85,
            overallocated: false,
            hourly_rate: 2500,
            currency: 'RUB',
            skills: [
              { name: 'React', level: 'expert' },
              { name: 'Python', level: 'advanced' },
              { name: 'FastAPI', level: 'advanced' }
            ],
            allocations: [
              {
                project_id: 1,
                project_name: 'АДВАКОД',
                allocation: 60,
                role: 'Lead Developer',
                start_date: '2025-10-01',
                end_date: '2025-12-31',
                is_active: true
              },
              {
                project_id: 2,
                project_name: 'Маркетинг',
                allocation: 25,
                role: 'Developer',
                start_date: '2025-10-15',
                end_date: '2025-11-30',
                is_active: true
              }
            ],
            availability: [
              {
                type: 'vacation',
                start_date: '2025-11-15',
                end_date: '2025-11-22',
                description: 'Отпуск',
                is_approved: true
              }
            ]
          },
          {
            id: 2,
            user_id: 2,
            user_name: 'Мария Петрова',
            email: 'maria@advakod.ru',
            role: 'UI/UX Designer',
            department: 'Design',
            total_capacity: 40,
            current_allocation: 120,
            utilization: 120,
            overallocated: true,
            hourly_rate: 2000,
            currency: 'RUB',
            skills: [
              { name: 'Figma', level: 'expert' },
              { name: 'UI Design', level: 'expert' },
              { name: 'UX Research', level: 'advanced' }
            ],
            allocations: [
              {
                project_id: 1,
                project_name: 'АДВАКОД',
                allocation: 80,
                role: 'Lead Designer',
                start_date: '2025-10-01',
                end_date: '2025-12-31',
                is_active: true
              },
              {
                project_id: 3,
                project_name: 'Новый проект',
                allocation: 40,
                role: 'Designer',
                start_date: '2025-10-20',
                end_date: '2025-11-30',
                is_active: true
              }
            ],
            availability: []
          }
        ]);
      }
    } catch (err) {
      console.error('Error loading resource data:', err);
      setError('Ошибка загрузки данных ресурсов');
    } finally {
      setLoading(false);
    }
  };

  const getUtilizationColor = (utilization) => {
    if (utilization > 100) return 'text-red-600';
    if (utilization > 90) return 'text-orange-600';
    if (utilization > 80) return 'text-yellow-600';
    if (utilization > 60) return 'text-green-600';
    return 'text-blue-600';
  };

  const getUtilizationBgColor = (utilization) => {
    if (utilization > 100) return 'bg-red-500';
    if (utilization > 90) return 'bg-orange-500';
    if (utilization > 80) return 'bg-yellow-500';
    if (utilization > 60) return 'bg-green-500';
    return 'bg-blue-500';
  };

  const getSkillLevelColor = (level) => {
    const colors = {
      expert: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
      advanced: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
      intermediate: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
      beginner: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
    };
    return colors[level] || colors.beginner;
  };

  const formatCurrency = (amount, currency = 'RUB') => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  const calculateTotalRevenue = () => {
    return resources.reduce((total, resource) => {
      const weeklyHours = (resource.current_allocation / 100) * resource.total_capacity;
      const weeklyRevenue = weeklyHours * (resource.hourly_rate || 0);
      return total + (weeklyRevenue * 4); // Monthly estimate
    }, 0);
  };

  const getOverallocatedCount = () => {
    return resources.filter(r => r.overallocated).length;
  };

  const getAverageUtilization = () => {
    if (resources.length === 0) return 0;
    const totalUtilization = resources.reduce((sum, r) => sum + r.utilization, 0);
    return totalUtilization / resources.length;
  };

  const renderResourceCard = (resource, index) => (
    <motion.div
      key={resource.id}
      className={`bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border-l-4 ${
        resource.overallocated 
          ? 'border-red-500' 
          : resource.utilization > 90 
            ? 'border-orange-500'
            : 'border-green-500'
      } hover:shadow-md transition-shadow cursor-pointer`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.1 }}
      onClick={() => {
        setSelectedResource(resource);
        setShowAllocationModal(true);
      }}
    >
      {/* Resource Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center text-white font-semibold">
            {resource.user_name.split(' ').map(n => n[0]).join('').toUpperCase()}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-gray-100">
              {resource.user_name}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {resource.role} • {resource.department}
            </p>
          </div>
        </div>
        
        <div className="text-right">
          <div className={`text-2xl font-bold ${getUtilizationColor(resource.utilization)}`}>
            {resource.utilization}%
          </div>
          <div className="text-xs text-gray-500">
            {resource.current_allocation}ч / {resource.total_capacity}ч
          </div>
        </div>
      </div>

      {/* Utilization Bar */}
      <div className="mb-4">
        <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-1">
          <span>Загрузка</span>
          <span>{resource.utilization}%</span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
          <div 
            className={`h-3 rounded-full transition-all duration-300 ${getUtilizationBgColor(resource.utilization)}`}
            style={{ width: `${Math.min(resource.utilization, 100)}%` }}
          />
          {resource.utilization > 100 && (
            <div className="relative">
              <div 
                className="absolute top-0 h-3 bg-red-600 opacity-50 rounded-full"
                style={{ 
                  width: `${(resource.utilization - 100)}%`,
                  left: '100%',
                  transform: 'translateX(-100%)'
                }}
              />
            </div>
          )}
        </div>
      </div>

      {/* Project Allocations */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
          Проекты ({resource.allocations.length})
        </h4>
        <div className="space-y-2">
          {resource.allocations.slice(0, 2).map((allocation, idx) => (
            <div key={idx} className="flex items-center justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-400 truncate">
                {allocation.project_name}
              </span>
              <span className="font-medium text-gray-900 dark:text-gray-100">
                {allocation.allocation}%
              </span>
            </div>
          ))}
          {resource.allocations.length > 2 && (
            <div className="text-xs text-gray-500 text-center">
              +{resource.allocations.length - 2} проектов
            </div>
          )}
        </div>
      </div>

      {/* Skills */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
          Навыки
        </h4>
        <div className="flex flex-wrap gap-1">
          {resource.skills.slice(0, 3).map((skill, idx) => (
            <span key={idx} className={`text-xs px-2 py-1 rounded-full ${getSkillLevelColor(skill.level)}`}>
              {skill.name}
            </span>
          ))}
          {resource.skills.length > 3 && (
            <span className="text-xs text-gray-500">+{resource.skills.length - 3}</span>
          )}
        </div>
      </div>

      {/* Revenue */}
      {resource.hourly_rate && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">Месячный доход:</span>
          <span className="font-medium text-green-600">
            {formatCurrency((resource.current_allocation / 100) * resource.total_capacity * 4 * resource.hourly_rate)}
          </span>
        </div>
      )}

      {/* Status Indicators */}
      <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-2">
          {resource.overallocated && (
            <div className="flex items-center text-red-600">
              <AlertTriangle className="h-4 w-4 mr-1" />
              <span className="text-xs">Перегружен</span>
            </div>
          )}
          
          {resource.availability.length > 0 && (
            <div className="flex items-center text-yellow-600">
              <Calendar className="h-4 w-4 mr-1" />
              <span className="text-xs">Отпуск запланирован</span>
            </div>
          )}
        </div>
        
        <div className="flex items-center space-x-1">
          <button className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1">
            <Eye className="h-4 w-4" />
          </button>
          <button className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 p-1">
            <Edit className="h-4 w-4" />
          </button>
        </div>
      </div>
    </motion.div>
  );

  const renderOverviewStats = () => (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <ModuleCard module="project" variant="module-neon">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Всего ресурсов</p>
            <p className="text-2xl font-bold text-blue-600">
              {resources.length}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Активных участников
            </p>
          </div>
          <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
            <Users className="h-6 w-6 text-blue-600" />
          </div>
        </div>
      </ModuleCard>

      <ModuleCard module="project" variant="module">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Перегруженных</p>
            <p className="text-2xl font-bold text-red-600">
              {getOverallocatedCount()}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Требуют внимания
            </p>
          </div>
          <div className="p-3 bg-red-100 dark:bg-red-900/30 rounded-lg">
            <AlertTriangle className="h-6 w-6 text-red-600" />
          </div>
        </div>
      </ModuleCard>

      <ModuleCard module="project" variant="module">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Средняя загрузка</p>
            <p className="text-2xl font-bold text-green-600">
              {getAverageUtilization().toFixed(1)}%
            </p>
            <p className="text-xs text-gray-500 mt-1">
              По всей команде
            </p>
          </div>
          <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
            <BarChart3 className="h-6 w-6 text-green-600" />
          </div>
        </div>
      </ModuleCard>

      <ModuleCard module="project" variant="module">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Месячный доход</p>
            <p className="text-2xl font-bold text-purple-600">
              {formatCurrency(calculateTotalRevenue())}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Общий доход команды
            </p>
          </div>
          <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
            <DollarSign className="h-6 w-6 text-purple-600" />
          </div>
        </div>
      </ModuleCard>
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <LoadingSpinner 
          size="lg" 
          module="project" 
          variant="neon"
          text="Загрузка ресурсов..."
        />
      </div>
    );
  }

  return (
    <ModuleErrorBoundary module="project" componentName="ResourceTracker">
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
                  <Users className="h-8 w-8 text-blue-500 mr-3" />
                  Управление ресурсами
                </h1>
                <p className="mt-2 text-gray-600 dark:text-gray-400">
                  Отслеживание нагрузки команды и планирование ресурсов
                </p>
              </div>
              
              <div className="mt-6 lg:mt-0 flex flex-wrap gap-3">
                <select
                  value={selectedPeriod}
                  onChange={(e) => setSelectedPeriod(e.target.value)}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                >
                  <option value="current">Текущий период</option>
                  <option value="next">Следующий период</option>
                  <option value="quarter">Квартал</option>
                </select>

                <div className="flex items-center space-x-2">
                  {['overview', 'detailed', 'calendar'].map((mode) => (
                    <button
                      key={mode}
                      onClick={() => setViewMode(mode)}
                      className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                        viewMode === mode
                          ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600'
                          : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
                      }`}
                    >
                      {mode === 'overview' ? 'Обзор' : mode === 'detailed' ? 'Детали' : 'Календарь'}
                    </button>
                  ))}
                </div>

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
                  onClick={() => setShowAllocationModal(true)}
                  icon={<Plus className="h-4 w-4" />}
                >
                  Добавить ресурс
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

          {/* Overview Statistics */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            {renderOverviewStats()}
          </motion.div>

          {/* Filters */}
          <motion.div
            className="mb-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <ModuleCard module="project" variant="module">
              <div className="flex flex-col lg:flex-row lg:items-center space-y-4 lg:space-y-0 lg:space-x-4">
                <select
                  value={filters.department}
                  onChange={(e) => setFilters(prev => ({ ...prev, department: e.target.value }))}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                >
                  <option value="">Все отделы</option>
                  <option value="Engineering">Разработка</option>
                  <option value="Design">Дизайн</option>
                  <option value="Marketing">Маркетинг</option>
                  <option value="QA">Тестирование</option>
                </select>
                
                <select
                  value={filters.role}
                  onChange={(e) => setFilters(prev => ({ ...prev, role: e.target.value }))}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                >
                  <option value="">Все роли</option>
                  <option value="Senior Developer">Senior Developer</option>
                  <option value="Developer">Developer</option>
                  <option value="Designer">Designer</option>
                  <option value="QA Engineer">QA Engineer</option>
                </select>
                
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={filters.overallocated}
                    onChange={(e) => setFilters(prev => ({ ...prev, overallocated: e.target.checked }))}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    Только перегруженные
                  </span>
                </label>

                <EnhancedButton
                  variant="module-outline"
                  module="project"
                  size="sm"
                  onClick={loadResourceData}
                  icon={<RefreshCw className="h-4 w-4" />}
                >
                  Обновить
                </EnhancedButton>
              </div>
            </ModuleCard>
          </motion.div>

          {/* Resources Grid */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            {resources.length === 0 ? (
              <ModuleCard module="project" variant="module">
                <div className="text-center py-12">
                  <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                    Нет ресурсов
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 mb-6">
                    Добавьте участников команды для отслеживания загрузки
                  </p>
                  <EnhancedButton
                    variant="module"
                    module="project"
                    onClick={() => setShowAllocationModal(true)}
                    icon={<Plus className="h-4 w-4" />}
                  >
                    Добавить ресурс
                  </EnhancedButton>
                </div>
              </ModuleCard>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {resources
                  .filter(resource => {
                    if (filters.department && resource.department !== filters.department) return false;
                    if (filters.role && resource.role !== filters.role) return false;
                    if (filters.overallocated && !resource.overallocated) return false;
                    return true;
                  })
                  .map((resource, index) => renderResourceCard(resource, index))
                }
              </div>
            )}
          </motion.div>
        </div>
      </div>
    </ModuleErrorBoundary>
  );
};

export default ResourceTracker;