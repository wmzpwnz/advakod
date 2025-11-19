import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  TrendingUp,
  Users,
  DollarSign,
  Target,
  Zap,
  Eye,
  MousePointer,
  ShoppingCart,
  CreditCard,
  ArrowRight,
  ArrowDown,
  Filter,
  Calendar,
  Download,
  RefreshCw,
  BarChart3,
  PieChart,
  Activity,
  Percent
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import ModuleCard from './ModuleCard';
import EnhancedButton from './EnhancedButton';
import LoadingSpinner, { MarketingSpinner } from './LoadingSpinner';
import ModuleErrorBoundary from './ModuleErrorBoundary';

const MarketingDashboard = () => {
  const { getModuleColor } = useTheme();
  const [salesFunnel, setSalesFunnel] = useState(null);
  const [conversionMetrics, setConversionMetrics] = useState({});
  const [trafficSources, setTrafficSources] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dateRange, setDateRange] = useState('30d');
  const [selectedFunnel, setSelectedFunnel] = useState(null);

  useEffect(() => {
    loadMarketingData();
  }, [dateRange]);

  const loadMarketingData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const [funnelRes, metricsRes, trafficRes, campaignsRes] = await Promise.all([
        fetch(`/api/v1/marketing/funnel?period=${dateRange}`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`/api/v1/marketing/conversion-metrics?period=${dateRange}`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`/api/v1/marketing/traffic-sources?period=${dateRange}`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`/api/v1/marketing/campaigns?period=${dateRange}`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      if (funnelRes.ok) {
        const funnelData = await funnelRes.json();
        setSalesFunnel(funnelData);
      }

      if (metricsRes.ok) {
        const metricsData = await metricsRes.json();
        setConversionMetrics(metricsData);
      }

      if (trafficRes.ok) {
        const trafficData = await trafficRes.json();
        setTrafficSources(trafficData);
      }

      if (campaignsRes.ok) {
        const campaignsData = await campaignsRes.json();
        setCampaigns(campaignsData);
      }

    } catch (err) {
      setError('Ошибка загрузки маркетинговых данных');
      console.error('Error loading marketing data:', err);
    } finally {
      setLoading(false);
    }
  };

  const exportReport = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/v1/marketing/export?period=${dateRange}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `marketing-report-${dateRange}-${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (err) {
      setError('Ошибка экспорта отчета');
    }
  };

  const getConversionColor = (rate) => {
    if (rate >= 10) return 'text-green-600';
    if (rate >= 5) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConversionBg = (rate) => {
    if (rate >= 10) return 'bg-green-100 dark:bg-green-900/30';
    if (rate >= 5) return 'bg-yellow-100 dark:bg-yellow-900/30';
    return 'bg-red-100 dark:bg-red-900/30';
  };

  const calculateDropOff = (current, previous) => {
    if (!previous) return 0;
    return ((previous - current) / previous * 100).toFixed(1);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <MarketingSpinner 
          size="lg" 
          text="Загрузка маркетингового дашборда..."
        />
      </div>
    );
  }

  return (
    <ModuleErrorBoundary module="marketing" componentName="MarketingDashboard">
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
                  <TrendingUp className="h-8 w-8 text-orange-500 mr-3" />
                  Маркетинговый дашборд
                </h1>
                <p className="mt-2 text-gray-600 dark:text-gray-400">
                  Воронка продаж, конверсии и аналитика маркетинговых кампаний
                </p>
              </div>
              
              <div className="mt-6 lg:mt-0 flex flex-wrap gap-3">
                <select
                  value={dateRange}
                  onChange={(e) => setDateRange(e.target.value)}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-orange-500"
                >
                  <option value="7d">7 дней</option>
                  <option value="30d">30 дней</option>
                  <option value="90d">3 месяца</option>
                  <option value="1y">Год</option>
                </select>
                
                <EnhancedButton
                  variant="module-outline"
                  module="marketing"
                  onClick={exportReport}
                  icon={<Download className="h-4 w-4" />}
                >
                  Экспорт
                </EnhancedButton>
                
                <EnhancedButton
                  variant="module"
                  module="marketing"
                  onClick={loadMarketingData}
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
                <ModuleCard module="marketing" variant="module" className="border-red-300 bg-red-50 dark:bg-red-900/20">
                  <div className="flex items-center">
                    <Target className="h-5 w-5 text-red-500 mr-3" />
                    <div>
                      <h3 className="text-sm font-medium text-red-800 dark:text-red-300">Ошибка</h3>
                      <p className="text-sm text-red-700 dark:text-red-400 mt-1">{error}</p>
                    </div>
                    <button 
                      onClick={() => setError('')}
                      className="ml-auto text-red-500 hover:text-red-700"
                    >
                      <Target className="h-4 w-4" />
                    </button>
                  </div>
                </ModuleCard>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Key Metrics */}
          <motion.div 
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <ModuleCard module="marketing" variant="module-neon">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Общая конверсия</p>
                  <p className={`text-2xl font-bold ${getConversionColor(conversionMetrics.overall)}`}>
                    {conversionMetrics.overall?.toFixed(1) || 0}%
                  </p>
                  <div className="flex items-center mt-1">
                    <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
                    <span className="text-xs text-green-600">
                      +{conversionMetrics.trend || 0}%
                    </span>
                  </div>
                </div>
                <div className={`p-3 rounded-lg ${getConversionBg(conversionMetrics.overall)}`}>
                  <Percent className={`h-6 w-6 ${getConversionColor(conversionMetrics.overall)}`} />
                </div>
              </div>
            </ModuleCard>

            <ModuleCard module="marketing" variant="module">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Посетители</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {conversionMetrics.visitors?.toLocaleString() || 0}
                  </p>
                  <div className="flex items-center mt-1">
                    <Eye className="h-4 w-4 text-blue-500 mr-1" />
                    <span className="text-xs text-gray-500">
                      {conversionMetrics.uniqueVisitors?.toLocaleString() || 0} уникальных
                    </span>
                  </div>
                </div>
                <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                  <Users className="h-6 w-6 text-blue-600" />
                </div>
              </div>
            </ModuleCard>

            <ModuleCard module="marketing" variant="module">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Доход</p>
                  <p className="text-2xl font-bold text-green-600">
                    ${conversionMetrics.revenue?.toLocaleString() || 0}
                  </p>
                  <div className="flex items-center mt-1">
                    <DollarSign className="h-4 w-4 text-green-500 mr-1" />
                    <span className="text-xs text-gray-500">
                      AOV: ${conversionMetrics.averageOrderValue || 0}
                    </span>
                  </div>
                </div>
                <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                  <DollarSign className="h-6 w-6 text-green-600" />
                </div>
              </div>
            </ModuleCard>

            <ModuleCard module="marketing" variant="module">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">CAC</p>
                  <p className="text-2xl font-bold text-purple-600">
                    ${conversionMetrics.customerAcquisitionCost || 0}
                  </p>
                  <div className="flex items-center mt-1">
                    <Target className="h-4 w-4 text-purple-500 mr-1" />
                    <span className="text-xs text-gray-500">
                      LTV: ${conversionMetrics.lifetimeValue || 0}
                    </span>
                  </div>
                </div>
                <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                  <Target className="h-6 w-6 text-purple-600" />
                </div>
              </div>
            </ModuleCard>
          </motion.div>

          {/* Sales Funnel */}
          <motion.div
            className="mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <ModuleCard module="marketing" variant="module-neon">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                  Воронка продаж
                </h2>
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <Activity className="h-4 w-4" />
                  <span>Конверсия по этапам</span>
                </div>
              </div>

              {salesFunnel && (
                <div className="space-y-4">
                  {salesFunnel.stages?.map((stage, index) => {
                    const previousStage = index > 0 ? salesFunnel.stages[index - 1] : null;
                    const dropOff = calculateDropOff(stage.users, previousStage?.users);
                    const conversionRate = previousStage 
                      ? ((stage.users / previousStage.users) * 100).toFixed(1)
                      : 100;

                    return (
                      <motion.div
                        key={stage.id}
                        className="relative"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.3, delay: index * 0.1 }}
                      >
                        <div className="flex items-center">
                          {/* Stage Icon */}
                          <div 
                            className="flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center mr-4"
                            style={{ 
                              backgroundColor: `${getModuleColor('marketing')}20`,
                              border: `2px solid ${getModuleColor('marketing')}40`
                            }}
                          >
                            {index === 0 && <Eye className="h-6 w-6" style={{ color: getModuleColor('marketing') }} />}
                            {index === 1 && <MousePointer className="h-6 w-6" style={{ color: getModuleColor('marketing') }} />}
                            {index === 2 && <ShoppingCart className="h-6 w-6" style={{ color: getModuleColor('marketing') }} />}
                            {index === 3 && <CreditCard className="h-6 w-6" style={{ color: getModuleColor('marketing') }} />}
                            {index > 3 && <Target className="h-6 w-6" style={{ color: getModuleColor('marketing') }} />}
                          </div>

                          {/* Stage Content */}
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-2">
                              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                                {stage.name}
                              </h3>
                              <div className="flex items-center space-x-4">
                                <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                                  {stage.users.toLocaleString()}
                                </span>
                                {previousStage && (
                                  <div className="flex items-center text-sm">
                                    <span className={`font-medium ${getConversionColor(parseFloat(conversionRate))}`}>
                                      {conversionRate}%
                                    </span>
                                    {dropOff > 0 && (
                                      <span className="text-red-500 ml-2">
                                        (-{dropOff}%)
                                      </span>
                                    )}
                                  </div>
                                )}
                              </div>
                            </div>

                            {/* Progress Bar */}
                            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 mb-2">
                              <div 
                                className="h-3 rounded-full transition-all duration-1000"
                                style={{ 
                                  width: `${(stage.users / salesFunnel.stages[0].users) * 100}%`,
                                  background: `linear-gradient(90deg, ${getModuleColor('marketing')}, ${getModuleColor('marketing', 'light')})`
                                }}
                              />
                            </div>

                            {/* Stage Details */}
                            <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
                              <span>
                                Среднее время: {stage.averageTimeSpent}с
                              </span>
                              <span>
                                Конверсия: {stage.conversionRate.toFixed(1)}%
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Arrow to next stage */}
                        {index < salesFunnel.stages.length - 1 && (
                          <div className="flex justify-center my-2">
                            <ArrowDown className="h-5 w-5 text-gray-400" />
                          </div>
                        )}
                      </motion.div>
                    );
                  })}
                </div>
              )}
            </ModuleCard>
          </motion.div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Traffic Sources */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
            >
              <ModuleCard module="marketing" variant="module">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-6">
                  Источники трафика
                </h2>
                
                <div className="space-y-4">
                  {trafficSources.map((source, index) => (
                    <div key={source.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <div className="flex items-center">
                        <div 
                          className="w-4 h-4 rounded-full mr-3"
                          style={{ backgroundColor: getModuleColor('marketing') }}
                        />
                        <div>
                          <h3 className="font-medium text-gray-900 dark:text-gray-100">
                            {source.name}
                          </h3>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            {source.type}
                          </p>
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                          {source.visitors.toLocaleString()}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {source.conversionRate.toFixed(1)}% конверсия
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </ModuleCard>
            </motion.div>

            {/* Active Campaigns */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
            >
              <ModuleCard module="marketing" variant="module">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-6">
                  Активные кампании
                </h2>
                
                <div className="space-y-4">
                  {campaigns.map((campaign, index) => (
                    <div key={campaign.id} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-medium text-gray-900 dark:text-gray-100">
                          {campaign.name}
                        </h3>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          campaign.status === 'active' 
                            ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
                            : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'
                        }`}>
                          {campaign.status}
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-500 dark:text-gray-400">Бюджет:</span>
                          <span className="ml-1 font-medium">${campaign.budget?.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="text-gray-500 dark:text-gray-400">Потрачено:</span>
                          <span className="ml-1 font-medium">${campaign.spent?.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="text-gray-500 dark:text-gray-400">CTR:</span>
                          <span className="ml-1 font-medium">{campaign.metrics?.ctr?.toFixed(2)}%</span>
                        </div>
                        <div>
                          <span className="text-gray-500 dark:text-gray-400">ROI:</span>
                          <span className={`ml-1 font-medium ${
                            campaign.metrics?.roi > 0 ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {campaign.metrics?.roi?.toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </ModuleCard>
            </motion.div>
          </div>
        </div>
      </div>
    </ModuleErrorBoundary>
  );
};

export default MarketingDashboard;