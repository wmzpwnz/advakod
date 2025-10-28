import React, { useState, useEffect } from 'react';
import { 
  FiActivity, FiAlertTriangle, FiCheck, FiX, FiClock, FiTrendingUp,
  FiTrendingDown, FiDatabase, FiHardDrive, FiShield, FiRefreshCw,
  FiPlay, FiPause, FiBarChart3, FiPieChart, FiSettings
} from 'react-icons/fi';
import { motion } from 'framer-motion';
import { toast } from 'react-hot-toast';
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement,
} from 'chart.js';
import GlassCard from './GlassCard';
import LoadingSpinner from './LoadingSpinner';
import ModernButton from './ModernButton';

// Регистрируем компоненты Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement
);

const BackupMonitoringDashboard = () => {
  const [metrics, setMetrics] = useState(null);
  const [healthReport, setHealthReport] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [monitoringActive, setMonitoringActive] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    loadData();
    
    // Автообновление каждые 30 секунд
    const interval = setInterval(() => {
      if (autoRefresh) {
        loadData();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [metricsRes, healthRes, alertsRes] = await Promise.all([
        fetch('/api/v1/backup/monitoring/metrics'),
        fetch('/api/v1/backup/monitoring/health-report'),
        fetch('/api/v1/backup/monitoring/alerts')
      ]);

      if (metricsRes.ok) {
        const metricsData = await metricsRes.json();
        setMetrics(metricsData);
      }

      if (healthRes.ok) {
        const healthData = await healthRes.json();
        setHealthReport(healthData);
      }

      if (alertsRes.ok) {
        const alertsData = await alertsRes.json();
        setAlerts(alertsData);
      }
    } catch (error) {
      console.error('Ошибка загрузки данных мониторинга:', error);
      toast.error('Ошибка загрузки данных мониторинга');
    } finally {
      setLoading(false);
    }
  };

  const toggleMonitoring = async () => {
    try {
      const endpoint = monitoringActive ? 'stop' : 'start';
      const response = await fetch(`/api/v1/backup/monitoring/${endpoint}`, {
        method: 'POST',
      });

      if (response.ok) {
        setMonitoringActive(!monitoringActive);
        toast.success(`Мониторинг ${monitoringActive ? 'остановлен' : 'запущен'}`);
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Ошибка управления мониторингом');
      }
    } catch (error) {
      console.error('Ошибка управления мониторингом:', error);
      toast.error('Ошибка управления мониторингом');
    }
  };

  const formatSize = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '0s';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${secs}s`;
    return `${secs}s`;
  };

  const getHealthColor = (status) => {
    switch (status) {
      case 'healthy': return 'text-green-400';
      case 'warning': return 'text-yellow-400';
      case 'critical': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getHealthIcon = (status) => {
    switch (status) {
      case 'healthy': return <FiCheck className="w-6 h-6" />;
      case 'warning': return <FiAlertTriangle className="w-6 h-6" />;
      case 'critical': return <FiX className="w-6 h-6" />;
      default: return <FiClock className="w-6 h-6" />;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return 'text-red-400 bg-red-600/20 border-red-600/30';
      case 'medium': return 'text-yellow-400 bg-yellow-600/20 border-yellow-600/30';
      case 'low': return 'text-blue-400 bg-blue-600/20 border-blue-600/30';
      default: return 'text-gray-400 bg-gray-600/20 border-gray-600/30';
    }
  };

  // Данные для графиков
  const successRateData = {
    labels: ['Успешные', 'Неудачные'],
    datasets: [
      {
        data: metrics ? [metrics.successful_backups, metrics.failed_backups] : [0, 0],
        backgroundColor: ['#10b981', '#ef4444'],
        borderColor: ['#059669', '#dc2626'],
        borderWidth: 2,
      },
    ],
  };

  const storageUsageData = {
    labels: ['Использовано', 'Свободно'],
    datasets: [
      {
        data: metrics?.storage_usage ? [
          metrics.storage_usage.used_bytes,
          metrics.storage_usage.free_bytes
        ] : [0, 100],
        backgroundColor: ['#3b82f6', '#6b7280'],
        borderColor: ['#2563eb', '#4b5563'],
        borderWidth: 2,
      },
    ],
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Заголовок и управление */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">
            Мониторинг резервного копирования
          </h1>
          <p className="text-gray-400">
            Отслеживание состояния и производительности системы резервного копирования
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
            />
            <span className="text-gray-300 text-sm">Автообновление</span>
          </label>
          <ModernButton
            onClick={loadData}
            className="bg-blue-600 hover:bg-blue-700"
          >
            <FiRefreshCw className="w-4 h-4 mr-2" />
            Обновить
          </ModernButton>
          <ModernButton
            onClick={toggleMonitoring}
            className={monitoringActive 
              ? "bg-red-600 hover:bg-red-700" 
              : "bg-green-600 hover:bg-green-700"
            }
          >
            {monitoringActive ? (
              <>
                <FiPause className="w-4 h-4 mr-2" />
                Остановить мониторинг
              </>
            ) : (
              <>
                <FiPlay className="w-4 h-4 mr-2" />
                Запустить мониторинг
              </>
            )}
          </ModernButton>
        </div>
      </div>

      {/* Общее состояние системы */}
      {healthReport && (
        <GlassCard className={`p-6 border-l-4 ${
          healthReport.summary.overall_health === 'healthy' ? 'border-green-500' :
          healthReport.summary.overall_health === 'warning' ? 'border-yellow-500' :
          healthReport.summary.overall_health === 'critical' ? 'border-red-500' : 'border-gray-500'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className={`p-3 rounded-full ${
                healthReport.summary.overall_health === 'healthy' ? 'bg-green-600/20' :
                healthReport.summary.overall_health === 'warning' ? 'bg-yellow-600/20' :
                healthReport.summary.overall_health === 'critical' ? 'bg-red-600/20' : 'bg-gray-600/20'
              }`}>
                <div className={getHealthColor(healthReport.summary.overall_health)}>
                  {getHealthIcon(healthReport.summary.overall_health)}
                </div>
              </div>
              <div>
                <h2 className={`text-xl font-bold ${getHealthColor(healthReport.summary.overall_health)}`}>
                  Система резервного копирования
                </h2>
                <p className="text-gray-400">
                  Общий балл здоровья: {healthReport.summary.health_score}/100
                </p>
              </div>
            </div>
            
            <div className="text-right">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-red-400 font-semibold">{healthReport.summary.critical_issues}</span>
                  <p className="text-gray-400">Критических</p>
                </div>
                <div>
                  <span className="text-yellow-400 font-semibold">{healthReport.summary.warning_issues}</span>
                  <p className="text-gray-400">Предупреждений</p>
                </div>
              </div>
            </div>
          </div>
        </GlassCard>
      )}

      {/* Активные алерты */}
      {alerts.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-white mb-4">Активные алерты</h3>
          <div className="space-y-3">
            {alerts.map((alert, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`p-4 rounded-lg border ${getSeverityColor(alert.severity)}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <FiAlertTriangle className="w-5 h-5 mt-0.5" />
                    <div>
                      <h4 className="font-medium">{alert.title}</h4>
                      <p className="text-sm opacity-90 mt-1">{alert.message}</p>
                    </div>
                  </div>
                  <div className="text-right text-sm">
                    <p className="font-medium capitalize">{alert.severity}</p>
                    <p className="opacity-75">
                      {alert.current_value} / {alert.threshold}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Ключевые метрики */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <GlassCard className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Процент успешности</p>
                <p className="text-2xl font-bold text-white">
                  {(metrics.success_rate * 100).toFixed(1)}%
                </p>
                <p className="text-xs text-gray-500">
                  {metrics.successful_backups} из {metrics.total_backups}
                </p>
              </div>
              <div className={`p-2 rounded-full ${
                metrics.success_rate >= 0.9 ? 'bg-green-600/20' : 
                metrics.success_rate >= 0.7 ? 'bg-yellow-600/20' : 'bg-red-600/20'
              }`}>
                <FiTrendingUp className={`w-6 h-6 ${
                  metrics.success_rate >= 0.9 ? 'text-green-400' : 
                  metrics.success_rate >= 0.7 ? 'text-yellow-400' : 'text-red-400'
                }`} />
              </div>
            </div>
          </GlassCard>

          <GlassCard className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Последняя резервная копия</p>
                <p className="text-2xl font-bold text-white">
                  {metrics.last_successful_backup_age_hours 
                    ? `${metrics.last_successful_backup_age_hours.toFixed(1)}ч`
                    : 'Нет'
                  }
                </p>
                <p className="text-xs text-gray-500">назад</p>
              </div>
              <div className={`p-2 rounded-full ${
                !metrics.last_successful_backup_age_hours || metrics.last_successful_backup_age_hours <= 24 
                  ? 'bg-green-600/20' : 'bg-red-600/20'
              }`}>
                <FiClock className={`w-6 h-6 ${
                  !metrics.last_successful_backup_age_hours || metrics.last_successful_backup_age_hours <= 24 
                    ? 'text-green-400' : 'text-red-400'
                }`} />
              </div>
            </div>
          </GlassCard>

          <GlassCard className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Общий размер</p>
                <p className="text-2xl font-bold text-white">
                  {formatSize(metrics.total_size_bytes)}
                </p>
                <p className="text-xs text-gray-500">резервных копий</p>
              </div>
              <div className="p-2 rounded-full bg-blue-600/20">
                <FiHardDrive className="w-6 h-6 text-blue-400" />
              </div>
            </div>
          </GlassCard>

          <GlassCard className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Активные расписания</p>
                <p className="text-2xl font-bold text-white">{metrics.active_schedules}</p>
                <p className="text-xs text-gray-500">
                  {metrics.overdue_schedules > 0 && (
                    <span className="text-red-400">{metrics.overdue_schedules} просрочено</span>
                  )}
                </p>
              </div>
              <div className={`p-2 rounded-full ${
                metrics.overdue_schedules === 0 ? 'bg-green-600/20' : 'bg-red-600/20'
              }`}>
                <FiSettings className={`w-6 h-6 ${
                  metrics.overdue_schedules === 0 ? 'text-green-400' : 'text-red-400'
                }`} />
              </div>
            </div>
          </GlassCard>
        </div>
      )}

      {/* Графики */}
      {metrics && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* График успешности */}
          <GlassCard className="p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Статистика резервных копий</h3>
            <div className="h-64">
              <Doughnut 
                data={successRateData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      labels: {
                        color: '#ffffff'
                      }
                    }
                  }
                }}
              />
            </div>
          </GlassCard>

          {/* График использования хранилища */}
          <GlassCard className="p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Использование хранилища</h3>
            <div className="h-64">
              <Doughnut 
                data={storageUsageData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      labels: {
                        color: '#ffffff'
                      }
                    },
                    tooltip: {
                      callbacks: {
                        label: function(context) {
                          return context.label + ': ' + formatSize(context.raw);
                        }
                      }
                    }
                  }
                }}
              />
            </div>
          </GlassCard>
        </div>
      )}

      {/* Детальная информация */}
      {metrics && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Производительность */}
          <GlassCard className="p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Производительность</h3>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-gray-400">Среднее время резервного копирования:</span>
                <span className="text-white">
                  {metrics.average_duration_seconds 
                    ? formatDuration(metrics.average_duration_seconds)
                    : 'Нет данных'
                  }
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Резервных копий за 24ч:</span>
                <span className="text-white">{metrics.recent_backups_24h}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Успешных за 24ч:</span>
                <span className="text-green-400">{metrics.recent_successful_24h}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Неудачных за 24ч:</span>
                <span className="text-red-400">{metrics.recent_failed_24h}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Подряд неудачных:</span>
                <span className={metrics.consecutive_failures > 0 ? 'text-red-400' : 'text-green-400'}>
                  {metrics.consecutive_failures}
                </span>
              </div>
            </div>
          </GlassCard>

          {/* Целостность и восстановление */}
          <GlassCard className="p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Целостность и восстановление</h3>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-gray-400">Последняя проверка целостности:</span>
                <span className="text-white">
                  {metrics.last_integrity_check_age_days !== null
                    ? `${metrics.last_integrity_check_age_days} дней назад`
                    : 'Не выполнялась'
                  }
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Неудачных проверок за 7 дней:</span>
                <span className={metrics.failed_integrity_checks_7d > 0 ? 'text-red-400' : 'text-green-400'}>
                  {metrics.failed_integrity_checks_7d}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Всего восстановлений:</span>
                <span className="text-white">{metrics.total_restores}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Успешных восстановлений:</span>
                <span className="text-green-400">{metrics.successful_restores}</span>
              </div>
              {metrics.storage_usage && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Использование диска:</span>
                  <span className={`${
                    metrics.storage_usage.usage_percent > 90 ? 'text-red-400' :
                    metrics.storage_usage.usage_percent > 80 ? 'text-yellow-400' : 'text-green-400'
                  }`}>
                    {metrics.storage_usage.usage_percent.toFixed(1)}%
                  </span>
                </div>
              )}
            </div>
          </GlassCard>
        </div>
      )}

      {/* Рекомендации */}
      {healthReport?.recommendations && healthReport.recommendations.length > 0 && (
        <GlassCard className="p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Рекомендации по улучшению</h3>
          <ul className="space-y-2">
            {healthReport.recommendations.map((recommendation, index) => (
              <li key={index} className="flex items-start space-x-2 text-blue-300">
                <FiShield className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <span className="text-sm">{recommendation}</span>
              </li>
            ))}
          </ul>
        </GlassCard>
      )}
    </div>
  );
};

export default BackupMonitoringDashboard;