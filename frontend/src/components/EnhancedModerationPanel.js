import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Star, 
  CheckCircle, 
  Clock, 
  Award, 
  Zap,
  Filter,
  Search,
  Eye,
  MessageSquare,
  AlertTriangle,
  ThumbsUp,
  ThumbsDown,
  Target,
  TrendingUp,
  Users,
  Calendar,
  Download,
  RefreshCw,
  Settings,
  BarChart3,
  Layers,
  Flag
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import ModuleCard from './ModuleCard';
import EnhancedButton from './EnhancedButton';
import LoadingSpinner, { ModerationSpinner } from './LoadingSpinner';
import ModuleErrorBoundary from './ModuleErrorBoundary';

const EnhancedModerationPanel = () => {
  const { getModuleColor } = useTheme();
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Enhanced filters
  const [filters, setFilters] = useState({
    priority: '',
    status: '',
    category: '',
    assigned_to_me: false,
    confidence_range: [0, 100],
    date_range: 'all',
    user_feedback: '',
    complexity: ''
  });
  
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState('cards'); // cards, list, detailed
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  
  // Pagination
  const [page, setPage] = useState(1);
  const [itemsPerPage] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);

  // Stats and analytics
  const [stats, setStats] = useState(null);
  const [categories, setCategories] = useState([]);
  const [analytics, setAnalytics] = useState({
    dailyProgress: [],
    categoryBreakdown: [],
    qualityTrends: []
  });

  // Modal states
  const [selectedMessage, setSelectedMessage] = useState(null);
  const [showFilters, setShowFilters] = useState(false);
  const [showAnalytics, setShowAnalytics] = useState(false);

  const loadQueueData = useCallback(async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({
        page,
        page_size: itemsPerPage,
        sort_by: sortBy,
        sort_order: sortOrder,
        search: searchTerm,
        ...filters
      });

      const response = await fetch(
        `/api/v1/moderation/queue?${params}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (response.ok) {
        const data = await response.json();
        setQueue(data.items || []);
        setTotalPages(data.total_pages || 1);
        setTotalItems(data.total || 0);
      } else {
        throw new Error('Failed to load queue');
      }
    } catch (err) {
      setError('Ошибка загрузки очереди модерации');
      console.error('Error loading queue:', err);
    } finally {
      setLoading(false);
    }
  }, [page, itemsPerPage, sortBy, sortOrder, searchTerm, filters]);

  useEffect(() => {
    loadQueueData();
    loadStats();
    loadCategories();
    loadAnalytics();
  }, [loadQueueData]);

  const loadStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v1/moderation/my-stats', {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Error loading stats:', err);
    }
  };

  const loadCategories = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v1/moderation/categories', {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setCategories(data);
      }
    } catch (err) {
      console.error('Error loading categories:', err);
    }
  };

  const loadAnalytics = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v1/moderation/analytics', {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      }
    } catch (err) {
      console.error('Error loading analytics:', err);
    }
  };
  
  const getPriorityConfig = (priority) => {
    const configs = {
      critical: { 
        color: 'text-red-600 dark:text-red-400', 
        bg: 'bg-red-100 dark:bg-red-900/30',
        icon: '🚨',
        label: 'Критический'
      },
      high: { 
        color: 'text-orange-600 dark:text-orange-400', 
        bg: 'bg-orange-100 dark:bg-orange-900/30',
        icon: '🔴',
        label: 'Высокий'
      },
      medium: { 
        color: 'text-yellow-600 dark:text-yellow-400', 
        bg: 'bg-yellow-100 dark:bg-yellow-900/30',
        icon: '🟡',
        label: 'Средний'
      },
      low: { 
        color: 'text-green-600 dark:text-green-400', 
        bg: 'bg-green-100 dark:bg-green-900/30',
        icon: '🟢',
        label: 'Низкий'
      }
    };
    return configs[priority] || configs.medium;
  };

  const getReasonConfig = (reason) => {
    const configs = {
      user_complaint: { icon: '👤', label: 'Жалоба пользователя', color: 'text-red-600' },
      low_confidence: { icon: '⚠️', label: 'Низкая уверенность', color: 'text-yellow-600' },
      random_sample: { icon: '🎲', label: 'Случайная выборка', color: 'text-blue-600' },
      quality_check: { icon: '🔍', label: 'Проверка качества', color: 'text-purple-600' },
      flagged_content: { icon: '🚩', label: 'Помеченный контент', color: 'text-orange-600' }
    };
    return configs[reason] || { icon: '❓', label: reason, color: 'text-gray-600' };
  };

  const getRankConfig = (rank) => {
    const configs = {
      legend: { icon: '👑', label: 'Легенда', color: 'text-yellow-500', bg: 'bg-yellow-100' },
      master: { icon: '⭐', label: 'Мастер', color: 'text-purple-500', bg: 'bg-purple-100' },
      expert: { icon: '🎯', label: 'Эксперт', color: 'text-blue-500', bg: 'bg-blue-100' },
      advanced: { icon: '🔥', label: 'Продвинутый', color: 'text-orange-500', bg: 'bg-orange-100' },
      intermediate: { icon: '⚡', label: 'Средний', color: 'text-green-500', bg: 'bg-green-100' },
      beginner: { icon: '🌱', label: 'Новичок', color: 'text-gray-500', bg: 'bg-gray-100' }
    };
    return configs[rank] || configs.beginner;
  };

  const exportReport = async () => {
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams(filters);
      
      const response = await fetch(`/api/v1/moderation/export?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `moderation-report-${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (err) {
      setError('Ошибка экспорта отчета');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <ModerationSpinner 
          size="lg" 
          text="Загрузка панели модерации..."
        />
      </div>
    );
  }

  return (
    <ModuleErrorBoundary module="moderation" componentName="ModerationPanel">
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Enhanced Header */}
          <motion.div 
            className="mb-8"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
              <div className="flex-1">
                <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 flex items-center">
                  <Eye className="h-8 w-8 text-purple-500 mr-3" />
                  Панель модерации
                </h1>
                <p className="mt-2 text-gray-600 dark:text-gray-400">
                  Расширенная система оценки качества ответов ИИ с аналитикой и геймификацией
                </p>
                
                {/* Quick Stats */}
                <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
                    <div className="text-sm text-gray-500 dark:text-gray-400">В очереди</div>
                    <div className="text-xl font-semibold text-gray-900 dark:text-gray-100">{totalItems}</div>
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
                    <div className="text-sm text-gray-500 dark:text-gray-400">Сегодня оценено</div>
                    <div className="text-xl font-semibold text-purple-600">{stats?.today_reviews || 0}</div>
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
                    <div className="text-sm text-gray-500 dark:text-gray-400">Средняя оценка</div>
                    <div className="text-xl font-semibold text-blue-600">{stats?.avg_rating || 0}/10</div>
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
                    <div className="text-sm text-gray-500 dark:text-gray-400">Эффективность</div>
                    <div className="text-xl font-semibold text-green-600">{stats?.efficiency || 0}%</div>
                  </div>
                </div>
              </div>
              
              <div className="mt-6 lg:mt-0 flex flex-wrap gap-3">
                <EnhancedButton
                  variant="module-outline"
                  module="moderation"
                  onClick={() => setShowAnalytics(true)}
                  icon={<BarChart3 className="h-4 w-4" />}
                >
                  Аналитика
                </EnhancedButton>
                <EnhancedButton
                  variant="module-outline"
                  module="moderation"
                  onClick={exportReport}
                  icon={<Download className="h-4 w-4" />}
                >
                  Экспорт
                </EnhancedButton>
                <EnhancedButton
                  variant="module"
                  module="moderation"
                  onClick={loadQueueData}
                  icon={<RefreshCw className="h-4 w-4" />}
                >
                  Обновить
                </EnhancedButton>
              </div>
            </div>
          </motion.div>

          {/* Error Message */}
          <AnimatePresence>
            {error && (
              <motion.div 
                className="mb-6"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
              >
                <ModuleCard module="moderation" variant="module" className="border-red-300 bg-red-50 dark:bg-red-900/20">
                  <div className="flex items-center">
                    <AlertTriangle className="h-5 w-5 text-red-500 mr-3" />
                    <div>
                      <h3 className="text-sm font-medium text-red-800 dark:text-red-300">Ошибка</h3>
                      <p className="text-sm text-red-700 dark:text-red-400 mt-1">{error}</p>
                    </div>
                    <button 
                      onClick={() => setError('')}
                      className="ml-auto text-red-500 hover:text-red-700"
                    >
                      <AlertTriangle className="h-4 w-4" />
                    </button>
                  </div>
                </ModuleCard>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Moderator Stats Cards */}
          {stats && (
            <motion.div 
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              <ModuleCard module="moderation" variant="module-neon">
                <div className="flex items-center">
                  <div className={`p-3 rounded-lg ${getRankConfig(stats.rank).bg}`}>
                    <span className="text-2xl">{getRankConfig(stats.rank).icon}</span>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Ранг модератора</p>
                    <p className={`text-lg font-semibold ${getRankConfig(stats.rank).color}`}>
                      {getRankConfig(stats.rank).label}
                    </p>
                  </div>
                </div>
              </ModuleCard>

              <ModuleCard module="moderation" variant="module">
                <div className="flex items-center">
                  <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                    <Zap className="h-6 w-6 text-blue-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Баллы</p>
                    <p className="text-2xl font-semibold text-blue-600">
                      {stats.points?.toLocaleString()}
                    </p>
                  </div>
                </div>
              </ModuleCard>

              <ModuleCard module="moderation" variant="module">
                <div className="flex items-center">
                  <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                    <CheckCircle className="h-6 w-6 text-green-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Всего оценок</p>
                    <p className="text-2xl font-semibold text-green-600">
                      {stats.total_reviews?.toLocaleString()}
                    </p>
                  </div>
                </div>
              </ModuleCard>

              <ModuleCard module="moderation" variant="module">
                <div className="flex items-center">
                  <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                    <TrendingUp className="h-6 w-6 text-purple-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm text-gray-600 dark:text-gray-400">Точность</p>
                    <p className="text-2xl font-semibold text-purple-600">
                      {stats.accuracy || 0}%
                    </p>
                  </div>
                </div>
              </ModuleCard>
            </motion.div>
          )}
        </div>
      </div>
    </ModuleErrorBoundary>
  );
};

export default EnhancedModerationPanel;