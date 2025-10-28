/**
 * Monitoring Dashboard Component
 * Comprehensive monitoring and alerting interface for admin panel
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  ChartBarIcon, 
  ExclamationTriangleIcon, 
  CheckCircleIcon,
  ClockIcon,
  BellIcon,
  CogIcon,
  EyeIcon,
  PlayIcon,
  StopIcon
} from '@heroicons/react/24/outline';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const MonitoringDashboard = () => {
  const [metrics, setMetrics] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [alertRules, setAlertRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTimeRange, setSelectedTimeRange] = useState('1h');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30000); // 30 seconds

  // Fetch monitoring data
  const fetchMonitoringData = useCallback(async () => {
    try {
      const [metricsRes, alertsRes, rulesRes] = await Promise.all([
        fetch('/api/v1/metrics/json'),
        fetch('/api/v1/alerts/active'),
        fetch('/api/v1/alerts/rules')
      ]);

      const [metricsData, alertsData, rulesData] = await Promise.all([
        metricsRes.json(),
        alertsRes.json(),
        rulesRes.json()
      ]);

      setMetrics(metricsData);
      setAlerts(alertsData.data || []);
      setAlertRules(rulesData.data || []);
      setError(null);
    } catch (err) {
      setError('Failed to fetch monitoring data');
      console.error('Monitoring data fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Auto-refresh effect
  useEffect(() => {
    fetchMonitoringData();

    if (autoRefresh) {
      const interval = setInterval(fetchMonitoringData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchMonitoringData, autoRefresh, refreshInterval]);

  // Alert severity colors
  const alertColors = {
    info: 'bg-blue-100 text-blue-800 border-blue-200',
    warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    critical: 'bg-red-100 text-red-800 border-red-200',
    emergency: 'bg-purple-100 text-purple-800 border-purple-200'
  };

  // Alert severity icons
  const alertIcons = {
    info: <BellIcon className="h-4 w-4" />,
    warning: <ExclamationTriangleIcon className="h-4 w-4" />,
    critical: <ExclamationTriangleIcon className="h-4 w-4" />,
    emergency: <ExclamationTriangleIcon className="h-4 w-4" />
  };

  // System health status
  const systemHealth = useMemo(() => {
    const criticalAlerts = alerts.filter(alert => alert.severity === 'critical').length;
    const warningAlerts = alerts.filter(alert => alert.severity === 'warning').length;
    
    if (criticalAlerts > 0) return { status: 'critical', color: 'text-red-600' };
    if (warningAlerts > 0) return { status: 'warning', color: 'text-yellow-600' };
    return { status: 'healthy', color: 'text-green-600' };
  }, [alerts]);

  // Performance metrics chart data
  const performanceChartData = useMemo(() => {
    const labels = ['CPU', 'Memory', 'Disk', 'Network'];
    const data = [
      metrics.cpu_usage || 0,
      metrics.memory_usage || 0,
      metrics.disk_usage || 0,
      metrics.network_usage || 0
    ];

    return {
      labels,
      datasets: [{
        label: 'Usage %',
        data,
        backgroundColor: [
          'rgba(59, 130, 246, 0.5)',
          'rgba(16, 185, 129, 0.5)',
          'rgba(245, 158, 11, 0.5)',
          'rgba(239, 68, 68, 0.5)'
        ],
        borderColor: [
          'rgba(59, 130, 246, 1)',
          'rgba(16, 185, 129, 1)',
          'rgba(245, 158, 11, 1)',
          'rgba(239, 68, 68, 1)'
        ],
        borderWidth: 2
      }]
    };
  }, [metrics]);

  // Alert distribution chart data
  const alertDistributionData = useMemo(() => {
    const distribution = alerts.reduce((acc, alert) => {
      acc[alert.severity] = (acc[alert.severity] || 0) + 1;
      return acc;
    }, {});

    return {
      labels: Object.keys(distribution),
      datasets: [{
        data: Object.values(distribution),
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(147, 51, 234, 0.8)'
        ],
        borderWidth: 0
      }]
    };
  }, [alerts]);

  // Acknowledge alert
  const acknowledgeAlert = async (alertId) => {
    try {
      const response = await fetch('/api/v1/alerts/acknowledge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alert_id: alertId })
      });

      if (response.ok) {
        await fetchMonitoringData();
      }
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            System Monitoring
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Real-time monitoring and alerting dashboard
          </p>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Auto-refresh toggle */}
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center px-3 py-2 rounded-md text-sm font-medium ${
              autoRefresh 
                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
            }`}
          >
            {autoRefresh ? <StopIcon className="h-4 w-4 mr-2" /> : <PlayIcon className="h-4 w-4 mr-2" />}
            Auto-refresh {autoRefresh ? 'ON' : 'OFF'}
          </button>
          
          {/* Manual refresh */}
          <button
            onClick={fetchMonitoringData}
            className="flex items-center px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium"
          >
            <ClockIcon className="h-4 w-4 mr-2" />
            Refresh
          </button>
        </div>
      </div>

      {/* System Health Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className={`p-2 rounded-md ${systemHealth.status === 'healthy' ? 'bg-green-100' : systemHealth.status === 'warning' ? 'bg-yellow-100' : 'bg-red-100'}`}>
              <CheckCircleIcon className={`h-6 w-6 ${systemHealth.color}`} />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">System Health</p>
              <p className={`text-lg font-semibold ${systemHealth.color}`}>
                {systemHealth.status.charAt(0).toUpperCase() + systemHealth.status.slice(1)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-md">
              <ChartBarIcon className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Active Alerts</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">{alerts.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-md">
              <CogIcon className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Alert Rules</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {alertRules.filter(rule => rule.enabled).length}/{alertRules.length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-md">
              <EyeIcon className="h-6 w-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Uptime</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">99.9%</p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Performance Metrics */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            System Performance
          </h3>
          <div className="h-64">
            <Bar 
              data={performanceChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: false }
                },
                scales: {
                  y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                      callback: function(value) {
                        return value + '%';
                      }
                    }
                  }
                }
              }}
            />
          </div>
        </div>

        {/* Alert Distribution */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Alert Distribution
          </h3>
          <div className="h-64">
            {alerts.length > 0 ? (
              <Doughnut 
                data={alertDistributionData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'bottom'
                    }
                  }
                }}
              />
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                No active alerts
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Active Alerts */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Active Alerts ({alerts.length})
          </h3>
        </div>
        
        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {alerts.length === 0 ? (
            <div className="px-6 py-8 text-center">
              <CheckCircleIcon className="mx-auto h-12 w-12 text-green-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
                No active alerts
              </h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                All systems are operating normally.
              </p>
            </div>
          ) : (
            alerts.map((alert) => (
              <div key={alert.id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className={`flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${alertColors[alert.severity]}`}>
                      {alertIcons[alert.severity]}
                      <span className="ml-1">{alert.severity.toUpperCase()}</span>
                    </div>
                    <div className="ml-4">
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                        {alert.name}
                      </h4>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {alert.description}
                      </p>
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                        Started: {new Date(alert.started_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      {alert.current_value} / {alert.threshold}
                    </span>
                    {alert.status === 'active' && (
                      <button
                        onClick={() => acknowledgeAlert(alert.id)}
                        className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
                      >
                        Acknowledge
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Alert Rules Summary */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Alert Rules ({alertRules.length})
          </h3>
        </div>
        
        <div className="px-6 py-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {alertRules.slice(0, 6).map((rule) => (
              <div key={rule.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                    {rule.name}
                  </h4>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    rule.enabled 
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                      : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                  }`}>
                    {rule.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                  {rule.description}
                </p>
                <div className="text-xs text-gray-400 dark:text-gray-500">
                  {rule.metric_name} {rule.condition} {rule.threshold}
                </div>
              </div>
            ))}
          </div>
          
          {alertRules.length > 6 && (
            <div className="mt-4 text-center">
              <button className="text-blue-600 hover:text-blue-700 text-sm font-medium">
                View all {alertRules.length} rules →
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MonitoringDashboard;