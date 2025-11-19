import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BarChart3,
  TrendingUp,
  TrendingDown,
  Users,
  Eye,
  MousePointer,
  Clock,
  Globe,
  Smartphone,
  Monitor,
  Tablet,
  MapPin,
  ExternalLink,
  Search,
  Hash,
  Mail,
  MessageCircle,
  Share2,
  Calendar,
  Filter,
  Download,
  RefreshCw,
  Target,
  Zap,
  Activity
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import ModuleCard from './ModuleCard';
import EnhancedButton from './EnhancedButton';
import LoadingSpinner from './LoadingSpinner';
import ModuleErrorBoundary from './ModuleErrorBoundary';

const TrafficAnalytics = () => {
  const { getModuleColor } = useTheme();
  const [trafficData, setTrafficData] = useState({
    overview: {},
    sources: [],
    channels: [],
    campaigns: [],
    devices: [],
    locations: [],
    utmAnalytics: {}
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dateRange, setDateRange] = useState('30d');
  const [selectedMetric, setSelectedMetric] = useState('visitors');
  const [activeTab, setActiveTab] = useState('sources');

  useEffect(() => {
    loadTrafficData();
  }, [dateRange]);

  const loadTrafficData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`/api/v1/marketing/traffic-analytics?period=${dateRange}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setTrafficData(data);
      } else {
        throw new Error('Failed to load traffic data');
      }
    } catch (err) {
      setError('Ошибка загрузки аналитики трафика');
      console.error('Error loading traffic data:', err);
    } finally {
      setLoading(false);
    }
  };

  const exportReport = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/v1/marketing/traffic-analytics/export?period=${dateRange}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `traffic-analytics-${dateRange}-${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (err) {
      setError('Ошибка экспорта отчета');
    }
  };

  const getSourceIcon = (type) => {
    const icons = {
      organic: Search,
      paid: Target,
      social: Share2,
      email: Mail,
      direct: Globe,
      referral: ExternalLink,
      affiliate: Hash
    };
    return icons[type] || Globe;
  };

  const getDeviceIcon = (device) => {
    const icons = {
      desktop: Monitor,
      mobile: Smartphone,
      tablet: Tablet
    };
    return icons[device] || Monitor;
  };

  const getTrendIcon = (trend) => {
    if (trend > 0) return <TrendingUp className="h-4 w-4 text-green-500" />;
    if (trend < 0) return <TrendingDown className="h-4 w-4 text-red-500" />;
    return <div className="h-4 w-4" />;
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num?.toLocaleString() || 0;
  };

  const calculatePercentage = (value, total) => {
    return total > 0 ? ((value / total) * 100).toFixed(1) : 0;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <LoadingSpinner 
          size="lg" 
          module="marketing" 
          variant="neon"
          text="Загрузка аналитики трафика..."
        />
      </div>
    );
  }

  return (
    <ModuleErrorBoundary module="marketing" componentName="TrafficAnalytics">
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
                  <BarChart3 className="h-8 w-8 text-orange-500 mr-3" />
                  Аналитика трафика
                </h1>
                <p className="mt-2 text-gray-600 dark:text-gray-400">
                  Детальный анализ источников трафика, UTM параметров и эффективности каналов
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
                  onClick={loadTrafficData}
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

          {/* Overview Metrics */}
          <motion.div 
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <ModuleCard module="marketing" variant="module-neon">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Посетители</p>
                  <p className="text-2xl font-bold text-orange-600">
                    {formatNumber(trafficData.overview.totalVisitors)}
                  </p>
                  <div className="flex items-center mt-1">
                    {getTrendIcon(trafficData.overview.visitorsTrend)}
                    <span className="text-xs text-gray-500 ml-1">
                      {trafficData.overview.visitorsTrend > 0 ? '+' : ''}{trafficData.overview.visitorsTrend?.toFixed(1)}%
                    </span>
                  </div>
                </div>
                <div className="p-3 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
                  <Users className="h-6 w-6 text-orange-600" />
                </div>
              </div>
            </ModuleCard>

            <ModuleCard module="marketing" variant="module">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Просмотры страниц</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {formatNumber(trafficData.overview.pageViews)}
                  </p>
                  <div className="flex items-center mt-1">
                    <Eye className="h-4 w-4 text-blue-500 mr-1" />
                    <span className="text-xs text-gray-500">
                      {trafficData.overview.avgPagesPerSession?.toFixed(1)} на сессию
                    </span>
                  </div>
                </div>
                <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                  <Eye className="h-6 w-6 text-blue-600" />
                </div>
              </div>
            </ModuleCard>

            <ModuleCard module="marketing" variant="module">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Время на сайте</p>
                  <p className="text-2xl font-bold text-green-600">
                    {Math.floor(trafficData.overview.avgSessionDuration / 60)}м {trafficData.overview.avgSessionDuration % 60}с
                  </p>
                  <div className="flex items-center mt-1">
                    <Clock className="h-4 w-4 text-green-500 mr-1" />
                    <span className="text-xs text-gray-500">
                      Среднее время сессии
                    </span>
                  </div>
                </div>
                <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                  <Clock className="h-6 w-6 text-green-600" />
                </div>
              </div>
            </ModuleCard>

            <ModuleCard module="marketing" variant="module">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Показатель отказов</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {trafficData.overview.bounceRate?.toFixed(1)}%
                  </p>
                  <div className="flex items-center mt-1">
                    {getTrendIcon(-trafficData.overview.bounceRateTrend)}
                    <span className="text-xs text-gray-500 ml-1">
                      {trafficData.overview.bounceRateTrend > 0 ? '+' : ''}{trafficData.overview.bounceRateTrend?.toFixed(1)}%
                    </span>
                  </div>
                </div>
                <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                  <Activity className="h-6 w-6 text-purple-600" />
                </div>
              </div>
            </ModuleCard>
          </motion.div>

          {/* Tabs */}
          <div className="mb-6">
            <nav className="flex space-x-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
              {[
                { id: 'sources', name: 'Источники', icon: Globe },
                { id: 'channels', name: 'Каналы', icon: Share2 },
                { id: 'campaigns', name: 'Кампании', icon: Target },
                { id: 'devices', name: 'Устройства', icon: Monitor },
                { id: 'locations', name: 'География', icon: MapPin }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`${
                    activeTab === tab.id
                      ? 'bg-white dark:bg-gray-700 text-orange-600 shadow-sm'
                      : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                  } px-4 py-2 rounded-md font-medium text-sm flex items-center transition-all duration-200`}
                >
                  <tab.icon className="h-4 w-4 mr-2" />
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <AnimatePresence mode="wait">
            {activeTab === 'sources' && (
              <motion.div
                key="sources"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <ModuleCard module="marketing" variant="module">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-6">
                    Источники трафика
                  </h2>
                  
                  <div className="space-y-4">
                    {trafficData.sources?.map((source, index) => {
                      const SourceIcon = getSourceIcon(source.type);
                      const percentage = calculatePercentage(source.visitors, trafficData.overview.totalVisitors);
                      
                      return (
                        <motion.div
                          key={source.id}
                          className="flex items-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ duration: 0.2, delay: index * 0.05 }}
                        >
                          <div className="flex items-center flex-1">
                            <div 
                              className="p-3 rounded-lg mr-4"
                              style={{ 
                                backgroundColor: `${getModuleColor('marketing')}20`,
                                border: `1px solid ${getModuleColor('marketing')}40`
                              }}
                            >
                              <SourceIcon 
                                className="h-5 w-5" 
                                style={{ color: getModuleColor('marketing') }}
                              />
                            </div>
                            
                            <div className="flex-1">
                              <div className="flex items-center justify-between mb-2">
                                <h3 className="font-medium text-gray-900 dark:text-gray-100">
                                  {source.name}
                                </h3>
                                <div className="text-right">
                                  <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                                    {source.visitors.toLocaleString()}
                                  </div>
                                  <div className="text-sm text-gray-500 dark:text-gray-400">
                                    {percentage}%
                                  </div>
                                </div>
                              </div>
                              
                              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mb-2">
                                <div 
                                  className="h-2 rounded-full transition-all duration-500"
                                  style={{ 
                                    width: `${percentage}%`,
                                    backgroundColor: getModuleColor('marketing')
                                  }}
                                />
                              </div>
                              
                              <div className="grid grid-cols-3 gap-4 text-sm text-gray-500 dark:text-gray-400">
                                <div>
                                  <span className="font-medium">Конверсия:</span> {source.conversionRate?.toFixed(1)}%
                                </div>
                                <div>
                                  <span className="font-medium">Отказы:</span> {source.bounceRate?.toFixed(1)}%
                                </div>
                                <div>
                                  <span className="font-medium">Время:</span> {Math.floor(source.averageSessionDuration / 60)}м
                                </div>
                              </div>
                            </div>
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </ModuleCard>
              </motion.div>
            )}

            {activeTab === 'devices' && (
              <motion.div
                key="devices"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  <ModuleCard module="marketing" variant="module">
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-6">
                      Устройства
                    </h2>
                    
                    <div className="space-y-4">
                      {trafficData.devices?.map((device, index) => {
                        const DeviceIcon = getDeviceIcon(device.type);
                        const percentage = calculatePercentage(device.sessions, trafficData.overview.totalSessions);
                        
                        return (
                          <div key={device.type} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                            <div className="flex items-center">
                              <DeviceIcon className="h-5 w-5 text-orange-500 mr-3" />
                              <div>
                                <h3 className="font-medium text-gray-900 dark:text-gray-100 capitalize">
                                  {device.type}
                                </h3>
                                <p className="text-sm text-gray-500 dark:text-gray-400">
                                  {device.sessions.toLocaleString()} сессий
                                </p>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                                {percentage}%
                              </div>
                              <div className="text-sm text-gray-500 dark:text-gray-400">
                                {device.conversionRate?.toFixed(1)}% конверсия
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </ModuleCard>

                  <ModuleCard module="marketing" variant="module">
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-6">
                      UTM Аналитика
                    </h2>
                    
                    <div className="space-y-6">
                      {/* UTM Source */}
                      <div>
                        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                          Топ UTM источники
                        </h3>
                        <div className="space-y-2">
                          {trafficData.utmAnalytics?.topSources?.map((source, index) => (
                            <div key={index} className="flex items-center justify-between text-sm">
                              <span className="text-gray-600 dark:text-gray-400">{source.name}</span>
                              <span className="font-medium text-gray-900 dark:text-gray-100">
                                {source.sessions.toLocaleString()}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* UTM Medium */}
                      <div>
                        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                          Топ UTM каналы
                        </h3>
                        <div className="space-y-2">
                          {trafficData.utmAnalytics?.topMediums?.map((medium, index) => (
                            <div key={index} className="flex items-center justify-between text-sm">
                              <span className="text-gray-600 dark:text-gray-400">{medium.name}</span>
                              <span className="font-medium text-gray-900 dark:text-gray-100">
                                {medium.sessions.toLocaleString()}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* UTM Campaign */}
                      <div>
                        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                          Топ UTM кампании
                        </h3>
                        <div className="space-y-2">
                          {trafficData.utmAnalytics?.topCampaigns?.map((campaign, index) => (
                            <div key={index} className="flex items-center justify-between text-sm">
                              <span className="text-gray-600 dark:text-gray-400">{campaign.name}</span>
                              <span className="font-medium text-gray-900 dark:text-gray-100">
                                {campaign.sessions.toLocaleString()}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </ModuleCard>
                </div>
              </motion.div>
            )}

            {activeTab === 'locations' && (
              <motion.div
                key="locations"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <ModuleCard module="marketing" variant="module">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-6">
                    География посетителей
                  </h2>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
                        По странам
                      </h3>
                      <div className="space-y-3">
                        {trafficData.locations?.countries?.map((country, index) => {
                          const percentage = calculatePercentage(country.sessions, trafficData.overview.totalSessions);
                          
                          return (
                            <div key={country.code} className="flex items-center justify-between">
                              <div className="flex items-center">
                                <span className="text-2xl mr-3">{country.flag}</span>
                                <span className="text-gray-900 dark:text-gray-100">{country.name}</span>
                              </div>
                              <div className="text-right">
                                <div className="font-medium text-gray-900 dark:text-gray-100">
                                  {country.sessions.toLocaleString()}
                                </div>
                                <div className="text-sm text-gray-500 dark:text-gray-400">
                                  {percentage}%
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    <div>
                      <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
                        По городам
                      </h3>
                      <div className="space-y-3">
                        {trafficData.locations?.cities?.map((city, index) => {
                          const percentage = calculatePercentage(city.sessions, trafficData.overview.totalSessions);
                          
                          return (
                            <div key={index} className="flex items-center justify-between">
                              <div className="flex items-center">
                                <MapPin className="h-4 w-4 text-orange-500 mr-3" />
                                <span className="text-gray-900 dark:text-gray-100">{city.name}</span>
                              </div>
                              <div className="text-right">
                                <div className="font-medium text-gray-900 dark:text-gray-100">
                                  {city.sessions.toLocaleString()}
                                </div>
                                <div className="text-sm text-gray-500 dark:text-gray-400">
                                  {percentage}%
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                </ModuleCard>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </ModuleErrorBoundary>
  );
};

export default TrafficAnalytics;