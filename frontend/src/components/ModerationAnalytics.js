import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  BarChart3,
  TrendingUp,
  TrendingDown,
  Eye,
  Clock,
  Users,
  Target,
  AlertTriangle,
  CheckCircle,
  Star,
  Calendar,
  Filter,
  Download,
  RefreshCw,
  Zap
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import ModuleCard from './ModuleCard';
import EnhancedButton from './EnhancedButton';
import LoadingSpinner from './LoadingSpinner';

const ModerationAnalytics = () => {
  const { getModuleColor } = useTheme();
  const [analytics, setAnalytics] = useState({
    overview: {},
    qualityTrends: [],
    moderatorPerformance: [],
    categoryBreakdown: [],
    timeDistribution: [],
    aiAccuracy: {}
  });
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState('7d');
  const [selectedMetric, setSelectedMetric] = useState('quality');

  useEffect(() => {
    loadAnalytics();
  }, [dateRange]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`/api/v1/moderation/analytics?period=${dateRange}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      }
    } catch (err) {
      console.error('Error loading analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  const exportAnalytics = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/v1/moderation/analytics/export?period=${dateRange}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `moderation-analytics-${dateRange}-${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (err) {
      console.error('Error exporting analytics:', err);
    }
  };

  const getQualityColor = (score) => {
    if (score >= 8) return 'text-green-600';
    if (score >= 6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getQualityBg = (score) => {
    if (score >= 8) return 'bg-green-100 dark:bg-green-900/30';
    if (score >= 6) return 'bg-yellow-100 dark:bg-yellow-900/30';
    return 'bg-red-100 dark:bg-red-900/30';
  };

  const getTrendIcon = (trend) => {
    if (trend > 0) return <TrendingUp className="h-4 w-4 text-green-500" />;
    if (trend < 0) return <TrendingDown className="h-4 w-4 text-red-500" />;
    return <div className="h-4 w-4" />;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <LoadingSpinner 
          size="lg" 
          module="moderation" 
          variant="neon"
          text="Загрузка аналитики модерации..."
        />
      </div>
    );
  }

  return (
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
                <BarChart3 className="h-8 w-8 text-purple-500 mr-3" />
                Аналитика модерации
              </h1>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                Детальная аналитика качества ответов ИИ и эффективности модераторов
              </p>
            </div>
            
            <div className="mt-6 lg:mt-0 flex flex-wrap gap-3">
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-purple-500"
              >
                <option value="1d">Сегодня</option>
                <option value="7d">7 дней</option>
                <option value="30d">30 дней</option>
                <option value="90d">3 месяца</option>
                <option value="1y">Год</option>
              </select>
              
              <EnhancedButton
                variant="module-outline"
                module="moderation"
                onClick={exportAnalytics}
                icon={<Download className="h-4 w-4" />}
              >
                Экспорт
              </EnhancedButton>
              
              <EnhancedButton
                variant="module"
                module="moderation"
                onClick={loadAnalytics}
                icon={<RefreshCw className="h-4 w-4" />}
              >
                Обновить
              </EnhancedButton>
            </div>
          </div>
        </motion.div>

        {/* Overview Cards */}
        <motion.div 
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <ModuleCard module="moderation" variant="module-neon">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Средняя оценка</p>
                <p className={`text-2xl font-bold ${getQualityColor(analytics.overview.avgRating)}`}>
                  {analytics.overview.avgRating?.toFixed(1) || 0}/10
                </p>
                <div className="flex items-center mt-1">
                  {getTrendIcon(analytics.overview.ratingTrend)}
                  <span className="text-xs text-gray-500 ml-1">
                    {analytics.overview.ratingTrend > 0 ? '+' : ''}{analytics.overview.ratingTrend?.toFixed(1)}%
                  </span>
                </div>
              </div>
              <div className={`p-3 rounded-lg ${getQualityBg(analytics.overview.avgRating)}`}>
                <Star className={`h-6 w-6 ${getQualityColor(analytics.overview.avgRating)}`} />
              </div>
            </div>
          </ModuleCard>

          <ModuleCard module="moderation" variant="module">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Всего оценок</p>
                <p className="text-2xl font-bold text-blue-600">
                  {analytics.overview.totalReviews?.toLocaleString() || 0}
                </p>
                <div className="flex items-center mt-1">
                  {getTrendIcon(analytics.overview.reviewsTrend)}
                  <span className="text-xs text-gray-500 ml-1">
                    {analytics.overview.reviewsTrend > 0 ? '+' : ''}{analytics.overview.reviewsTrend?.toFixed(1)}%
                  </span>
                </div>
              </div>
              <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <Eye className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </ModuleCard>

          <ModuleCard module="moderation" variant="module">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Активных модераторов</p>
                <p className="text-2xl font-bold text-green-600">
                  {analytics.overview.activeModerators || 0}
                </p>
                <div className="flex items-center mt-1">
                  <span className="text-xs text-gray-500">
                    Среднее время: {analytics.overview.avgReviewTime || 0}м
                  </span>
                </div>
              </div>
              <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                <Users className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </ModuleCard>

          <ModuleCard module="moderation" variant="module">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Точность ИИ</p>
                <p className="text-2xl font-bold text-purple-600">
                  {analytics.aiAccuracy.overall?.toFixed(1) || 0}%
                </p>
                <div className="flex items-center mt-1">
                  {getTrendIcon(analytics.aiAccuracy.trend)}
                  <span className="text-xs text-gray-500 ml-1">
                    {analytics.aiAccuracy.trend > 0 ? '+' : ''}{analytics.aiAccuracy.trend?.toFixed(1)}%
                  </span>
                </div>
              </div>
              <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <Target className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </ModuleCard>
        </motion.div>

        {/* Quality Trends Chart */}
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <ModuleCard module="moderation" variant="module">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                Тренды качества
              </h2>
              <div className="flex space-x-2">
                {['quality', 'volume', 'speed'].map((metric) => (
                  <button
                    key={metric}
                    onClick={() => setSelectedMetric(metric)}
                    className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                      selectedMetric === metric
                        ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-600'
                        : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
                    }`}
                  >
                    {metric === 'quality' && 'Качество'}
                    {metric === 'volume' && 'Объем'}
                    {metric === 'speed' && 'Скорость'}
                  </button>
                ))}
              </div>
            </div>

            {/* Simple chart representation */}
            <div className="h-64 flex items-end space-x-2">
              {analytics.qualityTrends.map((point, index) => (
                <div key={index} className="flex-1 flex flex-col items-center">
                  <div 
                    className="w-full bg-gradient-to-t from-purple-500 to-purple-300 rounded-t-lg transition-all duration-500 hover:from-purple-600 hover:to-purple-400"
                    style={{ 
                      height: `${(point[selectedMetric] / Math.max(...analytics.qualityTrends.map(p => p[selectedMetric]))) * 100}%`,
                      minHeight: '4px'
                    }}
                  />
                  <div className="text-xs text-gray-500 mt-2 transform -rotate-45 origin-left">
                    {point.date}
                  </div>
                </div>
              ))}
            </div>
          </ModuleCard>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Category Breakdown */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <ModuleCard module="moderation" variant="module">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-6">
                Категории проблем
              </h2>
              
              <div className="space-y-4">
                {analytics.categoryBreakdown.map((category, index) => (
                  <div key={category.name} className="flex items-center">
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          {category.icon} {category.name}
                        </span>
                        <span className="text-sm text-gray-500">
                          {category.count} ({category.percentage}%)
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div 
                          className="h-2 rounded-full transition-all duration-500"
                          style={{ 
                            width: `${category.percentage}%`,
                            backgroundColor: getModuleColor('moderation')
                          }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ModuleCard>
          </motion.div>

          {/* Moderator Performance */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            <ModuleCard module="moderation" variant="module">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-6">
                Топ модераторов
              </h2>
              
              <div className="space-y-4">
                {analytics.moderatorPerformance.map((moderator, index) => (
                  <div key={moderator.id} className="flex items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <div className="flex items-center mr-4">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold ${
                        index === 0 ? 'bg-yellow-500' : index === 1 ? 'bg-gray-400' : index === 2 ? 'bg-orange-500' : 'bg-gray-300'
                      }`}>
                        {index + 1}
                      </div>
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h3 className="font-medium text-gray-900 dark:text-gray-100">
                          {moderator.name}
                        </h3>
                        <div className="flex items-center space-x-3 text-sm">
                          <span className="text-purple-600">
                            {moderator.reviews} оценок
                          </span>
                          <span className={getQualityColor(moderator.avgRating)}>
                            {moderator.avgRating.toFixed(1)}/10
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center mt-1 text-xs text-gray-500">
                        <Clock className="h-3 w-3 mr-1" />
                        <span>Среднее время: {moderator.avgTime}м</span>
                        <Zap className="h-3 w-3 ml-3 mr-1" />
                        <span>{moderator.points} баллов</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ModuleCard>
          </motion.div>
        </div>

        {/* Time Distribution */}
        <motion.div
          className="mt-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
        >
          <ModuleCard module="moderation" variant="module">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-6">
              Распределение активности по времени
            </h2>
            
            <div className="grid grid-cols-12 gap-2">
              {analytics.timeDistribution.map((hour, index) => (
                <div key={index} className="text-center">
                  <div 
                    className="w-full bg-gradient-to-t from-purple-500 to-purple-300 rounded-lg mb-2 transition-all duration-300 hover:from-purple-600 hover:to-purple-400"
                    style={{ 
                      height: `${Math.max((hour.reviews / Math.max(...analytics.timeDistribution.map(h => h.reviews))) * 60, 4)}px`
                    }}
                    title={`${hour.hour}:00 - ${hour.reviews} оценок`}
                  />
                  <div className="text-xs text-gray-500">
                    {hour.hour}
                  </div>
                </div>
              ))}
            </div>
          </ModuleCard>
        </motion.div>
      </div>
    </div>
  );
};

export default ModerationAnalytics;