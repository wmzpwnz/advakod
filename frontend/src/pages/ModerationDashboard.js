import React, { useState, useEffect, useCallback } from 'react';
import { Shield, TrendingUp, Users, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import axios from 'axios';
import { getApiUrl } from '../config/api';

const ModerationDashboard = () => {
  const [dashboardData, setDashboardData] = useState({
    stats: {
      totalModerations: 0,
      pendingModerations: 0,
      approvedModerations: 0,
      rejectedModerations: 0
    },
    trends: {
      dailyModerations: [],
      weeklyModerations: []
    },
    recentActivity: []
  });
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${getApiUrl()}/moderation/dashboard`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Ошибка загрузки данных дашборда:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const StatCard = ({ title, value, icon: Icon, color, trend }) => (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {trend && (
            <div className="flex items-center mt-1">
              <TrendingUp className="w-4 h-4 text-green-500" />
              <span className="text-sm text-green-600 ml-1">{trend}%</span>
            </div>
          )}
        </div>
        <div className={`w-12 h-12 ${color} rounded-lg flex items-center justify-center`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Заголовок */}
        <div className="mb-8">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Дашборд модерации</h1>
              <p className="text-gray-600">Аналитика и статистика модерации</p>
            </div>
          </div>
        </div>

        {/* Статистика */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Всего модераций"
            value={dashboardData.stats.totalModerations}
            icon={Shield}
            color="bg-blue-100"
          />
          <StatCard
            title="Ожидают модерации"
            value={dashboardData.stats.pendingModerations}
            icon={Clock}
            color="bg-yellow-100"
          />
          <StatCard
            title="Одобрено"
            value={dashboardData.stats.approvedModerations}
            icon={CheckCircle}
            color="bg-green-100"
          />
          <StatCard
            title="Отклонено"
            value={dashboardData.stats.rejectedModerations}
            icon={AlertTriangle}
            color="bg-red-100"
          />
        </div>

        {/* Графики и активность */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* График трендов */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Тренды модерации</h3>
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-500">
                <p>График трендов будет здесь</p>
              </div>
            )}
          </div>

          {/* Последняя активность */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Последняя активность</h3>
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : dashboardData.recentActivity.length === 0 ? (
              <div className="flex items-center justify-center h-64 text-gray-500">
                <p>Нет недавней активности</p>
              </div>
            ) : (
              <div className="space-y-4">
                {dashboardData.recentActivity.map((activity, index) => (
                  <div key={index} className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                      <Shield className="w-4 h-4 text-gray-600" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm text-gray-900">{activity.description}</p>
                      <p className="text-xs text-gray-500">{activity.timestamp}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModerationDashboard;
