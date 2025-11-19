import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Kanban,
  Plus,
  Filter,
  Search,
  Calendar,
  Clock,
  Users,
  Tag,
  AlertTriangle,
  CheckCircle,
  Circle,
  MoreHorizontal,
  Edit,
  Trash2,
  Eye,
  ArrowRight,
  Target,
  Zap,
  Flag,
  User,
  MessageSquare,
  Paperclip,
  BarChart3,
  Settings,
  Download,
  RefreshCw
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import ModuleCard from './ModuleCard';
import EnhancedButton from './EnhancedButton';
import LoadingSpinner from './LoadingSpinner';
import ModuleErrorBoundary from './ModuleErrorBoundary';

const TaskManager = () => {
  const { getModuleColor } = useTheme();
  const [kanbanData, setKanbanData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedProject, setSelectedProject] = useState(null);
  const [selectedSprint, setSelectedSprint] = useState(null);
  const [filters, setFilters] = useState({
    assignee: '',
    priority: '',
    type: '',
    labels: []
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState('kanban'); // kanban, list, calendar

  // Modal states
  const [showTaskModal, setShowTaskModal] = useState(false);
  const [showSprintModal, setShowSprintModal] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [draggedTask, setDraggedTask] = useState(null);

  useEffect(() => {
    loadKanbanData();
  }, [selectedProject, selectedSprint, filters]);

  const loadKanbanData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const params = new URLSearchParams();
      if (selectedProject) params.append('project_id', selectedProject);
      if (selectedSprint) params.append('sprint_id', selectedSprint);
      if (filters.assignee) params.append('assignee_id', filters.assignee);
      if (filters.priority) params.append('priority', filters.priority);
      if (filters.type) params.append('type', filters.type);
      
      const response = await fetch(`/api/v1/project/kanban?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setKanbanData(data);
      } else {
        setError('Ошибка загрузки канбан-доски');
      }
    } catch (err) {
      setError('Ошибка загрузки канбан-доски');
      console.error('Error loading kanban:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDragStart = (e, task) => {
    setDraggedTask(task);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = async (e, columnStatus) => {
    e.preventDefault();
    
    if (!draggedTask || draggedTask.status === columnStatus) {
      setDraggedTask(null);
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/v1/project/tasks/${draggedTask.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ status: columnStatus })
      });

      if (response.ok) {
        // Update local state
        setKanbanData(prev => {
          const newData = { ...prev };
          
          // Remove task from old column
          newData.columns = newData.columns.map(col => ({
            ...col,
            tasks: col.tasks.filter(t => t.id !== draggedTask.id)
          }));
          
          // Add task to new column
          const targetColumn = newData.columns.find(col => col.status === columnStatus);
          if (targetColumn) {
            targetColumn.tasks.push({ ...draggedTask, status: columnStatus });
          }
          
          return newData;
        });
      } else {
        setError('Ошибка обновления статуса задачи');
      }
    } catch (err) {
      setError('Ошибка обновления статуса задачи');
    }
    
    setDraggedTask(null);
  };

  const getPriorityColor = (priority) => {
    const colors = {
      critical: 'bg-red-500',
      high: 'bg-orange-500',
      medium: 'bg-yellow-500',
      low: 'bg-green-500'
    };
    return colors[priority] || 'bg-gray-500';
  };

  const getPriorityIcon = (priority) => {
    const icons = {
      critical: <AlertTriangle className="h-4 w-4" />,
      high: <Flag className="h-4 w-4" />,
      medium: <Circle className="h-4 w-4" />,
      low: <CheckCircle className="h-4 w-4" />
    };
    return icons[priority] || <Circle className="h-4 w-4" />;
  };

  const getTypeIcon = (type) => {
    const icons = {
      feature: <Zap className="h-4 w-4" />,
      bug: <AlertTriangle className="h-4 w-4" />,
      improvement: <Target className="h-4 w-4" />,
      maintenance: <Settings className="h-4 w-4" />,
      research: <BarChart3 className="h-4 w-4" />,
      documentation: <MessageSquare className="h-4 w-4" />
    };
    return icons[type] || <Circle className="h-4 w-4" />;
  };

  const formatDate = (date) => {
    if (!date) return null;
    return new Date(date).toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: '2-digit'
    });
  };

  const isOverdue = (dueDate) => {
    if (!dueDate) return false;
    return new Date(dueDate) < new Date();
  };

  const renderTaskCard = (task) => (
    <motion.div
      key={task.id}
      className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm border border-gray-200 dark:border-gray-700 cursor-pointer hover:shadow-md transition-shadow"
      draggable
      onDragStart={(e) => handleDragStart(e, task)}
      onClick={() => setSelectedTask(task)}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      {/* Task Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          <div className={`p-1 rounded ${getPriorityColor(task.priority)} text-white`}>
            {getPriorityIcon(task.priority)}
          </div>
          <div className="text-gray-500">
            {getTypeIcon(task.type)}
          </div>
        </div>
        
        <div className="flex items-center space-x-1">
          {task.due_date && (
            <span className={`text-xs px-2 py-1 rounded-full ${
              isOverdue(task.due_date) 
                ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                : 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
            }`}>
              {formatDate(task.due_date)}
            </span>
          )}
          
          <button className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
            <MoreHorizontal className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Task Title */}
      <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2 line-clamp-2">
        {task.title}
      </h4>

      {/* Task Description */}
      {task.description && (
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
          {task.description}
        </p>
      )}

      {/* Task Labels */}
      {task.labels && task.labels.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {task.labels.slice(0, 3).map((label, index) => (
            <span key={index} className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full">
              {label}
            </span>
          ))}
          {task.labels.length > 3 && (
            <span className="text-xs text-gray-500">+{task.labels.length - 3}</span>
          )}
        </div>
      )}

      {/* Task Footer */}
      <div className="flex items-center justify-between text-sm text-gray-500">
        <div className="flex items-center space-x-3">
          {task.assignee_name && (
            <div className="flex items-center space-x-1">
              <User className="h-3 w-3" />
              <span className="truncate max-w-20">{task.assignee_name}</span>
            </div>
          )}
          
          {task.estimated_hours && (
            <div className="flex items-center space-x-1">
              <Clock className="h-3 w-3" />
              <span>{task.estimated_hours}ч</span>
            </div>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          {task.comments_count > 0 && (
            <div className="flex items-center space-x-1">
              <MessageSquare className="h-3 w-3" />
              <span>{task.comments_count}</span>
            </div>
          )}
          
          {task.attachments_count > 0 && (
            <div className="flex items-center space-x-1">
              <Paperclip className="h-3 w-3" />
              <span>{task.attachments_count}</span>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );

  const renderKanbanView = () => (
    <div className="flex space-x-6 overflow-x-auto pb-6">
      {kanbanData?.columns?.map((column, index) => (
        <motion.div
          key={column.id}
          className="flex-shrink-0 w-80"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3, delay: index * 0.1 }}
        >
          <ModuleCard module="project" variant="module" className="h-full">
            {/* Column Header */}
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center space-x-2">
                <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                  {column.name}
                </h3>
                <span className="bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 text-sm px-2 py-1 rounded-full">
                  {column.tasks?.length || 0}
                </span>
                {column.wip_limit && (
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    (column.tasks?.length || 0) > column.wip_limit
                      ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                      : 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                  }`}>
                    WIP: {column.tasks?.length || 0}/{column.wip_limit}
                  </span>
                )}
              </div>
              
              <button
                onClick={() => {
                  setSelectedTask({ status: column.status });
                  setShowTaskModal(true);
                }}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>

            {/* Column Tasks */}
            <div
              className="space-y-3 min-h-[200px]"
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, column.status)}
            >
              <AnimatePresence>
                {column.tasks?.map(task => renderTaskCard(task))}
              </AnimatePresence>
              
              {(!column.tasks || column.tasks.length === 0) && (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  <Circle className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">Нет задач</p>
                </div>
              )}
            </div>
          </ModuleCard>
        </motion.div>
      ))}
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <LoadingSpinner 
          size="lg" 
          module="project" 
          variant="neon"
          text="Загрузка задач..."
        />
      </div>
    );
  }

  return (
    <ModuleErrorBoundary module="project" componentName="TaskManager">
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
                  <Kanban className="h-8 w-8 text-blue-500 mr-3" />
                  Управление задачами
                </h1>
                <p className="mt-2 text-gray-600 dark:text-gray-400">
                  Канбан-доска для планирования и отслеживания задач
                </p>
              </div>
              
              <div className="mt-6 lg:mt-0 flex flex-wrap gap-3">
                <div className="flex items-center space-x-2">
                  {['kanban', 'list', 'calendar'].map((mode) => (
                    <button
                      key={mode}
                      onClick={() => setViewMode(mode)}
                      className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                        viewMode === mode
                          ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600'
                          : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
                      }`}
                    >
                      {mode === 'kanban' ? 'Канбан' : mode === 'list' ? 'Список' : 'Календарь'}
                    </button>
                  ))}
                </div>
                
                <EnhancedButton
                  variant="module-outline"
                  module="project"
                  icon={<Filter className="h-4 w-4" />}
                >
                  Фильтры
                </EnhancedButton>
                
                <EnhancedButton
                  variant="module-outline"
                  module="project"
                  icon={<RefreshCw className="h-4 w-4" />}
                  onClick={loadKanbanData}
                >
                  Обновить
                </EnhancedButton>
                
                <EnhancedButton
                  variant="module"
                  module="project"
                  onClick={() => setShowTaskModal(true)}
                  icon={<Plus className="h-4 w-4" />}
                >
                  Новая задача
                </EnhancedButton>
              </div>
            </div>
          </motion.div>

          {/* Filters and Search */}
          <motion.div
            className="mb-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <ModuleCard module="project" variant="module">
              <div className="flex flex-col lg:flex-row lg:items-center space-y-4 lg:space-y-0 lg:space-x-4">
                {/* Search */}
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Поиск задач..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  />
                </div>
                
                {/* Project Filter */}
                <select
                  value={selectedProject || ''}
                  onChange={(e) => setSelectedProject(e.target.value || null)}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                >
                  <option value="">Все проекты</option>
                  <option value="1">АДВАКОД</option>
                  <option value="2">Маркетинг</option>
                </select>
                
                {/* Sprint Filter */}
                <select
                  value={selectedSprint || ''}
                  onChange={(e) => setSelectedSprint(e.target.value || null)}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                >
                  <option value="">Все спринты</option>
                  <option value="1">Спринт 1</option>
                  <option value="2">Спринт 2</option>
                </select>
                
                {/* Priority Filter */}
                <select
                  value={filters.priority}
                  onChange={(e) => setFilters(prev => ({ ...prev, priority: e.target.value }))}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                >
                  <option value="">Все приоритеты</option>
                  <option value="critical">Критический</option>
                  <option value="high">Высокий</option>
                  <option value="medium">Средний</option>
                  <option value="low">Низкий</option>
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

          {/* Main Content */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            {viewMode === 'kanban' && renderKanbanView()}
            {viewMode === 'list' && (
              <ModuleCard module="project" variant="module">
                <div className="text-center py-12">
                  <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">Список задач - в разработке</p>
                </div>
              </ModuleCard>
            )}
            {viewMode === 'calendar' && (
              <ModuleCard module="project" variant="module">
                <div className="text-center py-12">
                  <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">Календарь задач - в разработке</p>
                </div>
              </ModuleCard>
            )}
          </motion.div>
        </div>
      </div>
    </ModuleErrorBoundary>
  );
};

export default TaskManager;