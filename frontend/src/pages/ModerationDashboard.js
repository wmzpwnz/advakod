import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { 
  TrendingUp, TrendingDown, Star, AlertCircle, 
  CheckCircle, Users, Award, BarChart3 
} from 'lucide-react';

const ModerationDashboard = () => {
  const [analytics, setAnalytics] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState(30);

  const loadAnalyticsData = useCallback(async () => {
    await loadData();
  }, [period]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    loadAnalyticsData();
  }, [loadAnalyticsData]);

  const loadData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const [analyticsRes, leaderboardRes] = await Promise.all([
        axios.get(
          `${process.env.REACT_APP_API_URL}/api/v1/moderation/analytics?days=${period}`,
          { headers: { Authorization: `Bearer ${token}` } }
        ),
        axios.get(
          `${process.env.REACT_APP_API_URL}/api/v1/moderation/leaderboard?limit=10`,
          { headers: { Authorization: `Bearer ${token}` } }
        )
      ]);

      setAnalytics(analyticsRes.data);
      setLeaderboard(leaderboardRes.data.leaderboard);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRankIcon = (rank) => {
    switch (rank) {
      case 'legend': return '👑';
      case 'master': return '⭐';
      case 'expert': return '🎯';
      default: return '🌱';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-purple-50/30 dark:from-gray-900 dark:via-gray-800 dark:to-purple-900/20 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-purple-500/20 border-t-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-purple-50/30 dark:from-gray-900 dark:via-gray-800 dark:to-purple-900/20">
      {/* Header */}
      <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl border-b border-purple-200/30 dark:border-purple-500/20 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 via-blue-600 to-cyan-600 bg-clip-text text-transparent">
                Аналитика модерации
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Статистика качества ответов ИИ
              </p>
            </div>

            <select
              value={period}
              onChange={(e) => setPeriod(Number(e.target.value))}
              className="px-4 py-2 bg-white/70 dark:bg-gray-800/70 backdrop-blur-md rounded-lg border border-purple-200/30 dark:border-purple-500/20 focus:border-purple-400/60 focus:ring-2 focus:ring-purple-500/20"
            >
              <option value={7}>Последние 7 дней</option>
              <option value={30}>Последние 30 дней</option>
              <option value={90}>Последние 90 дней</option>
            </select>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-xl p-6 border border-purple-200/30 dark:border-purple-500/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Всего оценок</p>
                <p className="text-3xl font-bold text-purple-600 dark:text-purple-400 mt-1">
                  {analytics?.total_reviews || 0}
                </p>
              </div>
              <CheckCircle className="w-12 h-12 text-purple-500/30" />
            </div>
          </div>

          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-xl p-6 border border-blue-200/30 dark:border-blue-500/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Средний рейтинг</p>
                <div className="flex items-center gap-2 mt-1">
                  <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                    {analytics?.average_rating?.toFixed(1) || '0.0'}
                  </p>
                  <Star className="w-6 h-6 text-yellow-500 fill-current" />
                </div>
              </div>
              <BarChart3 className="w-12 h-12 text-blue-500/30" />
            </div>
          </div>

          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-xl p-6 border border-green-200/30 dark:border-green-500/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Качество</p>
                <div className="flex items-center gap-2 mt-1">
                  <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                    {analytics?.average_rating >= 7 ? 'Хорошо' : analytics?.average_rating >= 5 ? 'Средне' : 'Низко'}
                  </p>
                  {analytics?.average_rating >= 7 ? (
                    <TrendingUp className="w-6 h-6 text-green-500" />
                  ) : (
                    <TrendingDown className="w-6 h-6 text-red-500" />
                  )}
                </div>
              </div>
              <AlertCircle className="w-12 h-12 text-green-500/30" />
            </div>
          </div>

          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-xl p-6 border border-cyan-200/30 dark:border-cyan-500/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Модераторов</p>
                <p className="text-3xl font-bold text-cyan-600 dark:text-cyan-400 mt-1">
                  {leaderboard?.length || 0}
                </p>
              </div>
              <Users className="w-12 h-12 text-cyan-500/30" />
            </div>
          </div>
        </div>

        {/* Rating Distribution */}
        {analytics?.rating_distribution && (
          <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-xl p-6 border border-purple-200/30 dark:border-purple-500/20">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4">
              Распределение оценок
            </h3>
            <div className="space-y-3">
              {Object.entries(analytics.rating_distribution)
                .sort(([a], [b]) => Number(b) - Number(a))
                .map(([rating, count]) => {
                  const percentage = (count / analytics.total_reviews) * 100;
                  return (
                    <div key={rating} className="flex items-center gap-3">
                      <div className="w-12 text-sm font-semibold text-gray-700 dark:text-gray-300">
                        {rating} ⭐
                      </div>
                      <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-6 overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-purple-500 to-blue-500 flex items-center justify-end px-2 transition-all duration-500"
                          style={{ width: `${percentage}%` }}
                        >
                          <span className="text-xs font-semibold text-white">
                            {count}
                          </span>
                        </div>
                      </div>
                      <div className="w-16 text-sm text-gray-600 dark:text-gray-400 text-right">
                        {percentage.toFixed(1)}%
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>
        )}

        {/* Leaderboard */}
        <div className="bg-white/70 dark:bg-gray-800/70 backdrop-blur-xl rounded-xl p-6 border border-purple-200/30 dark:border-purple-500/20">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
            <Award className="w-5 h-5 text-yellow-500" />
            Рейтинг модераторов
          </h3>
          <div className="space-y-3">
            {leaderboard.map((moderator, index) => (
              <div
                key={moderator.moderator_id}
                className={`flex items-center gap-4 p-4 rounded-lg ${
                  index === 0
                    ? 'bg-gradient-to-r from-yellow-500/20 to-orange-500/20 border-2 border-yellow-400/40'
                    : index === 1
                    ? 'bg-gradient-to-r from-gray-400/20 to-gray-500/20 border-2 border-gray-400/40'
                    : index === 2
                    ? 'bg-gradient-to-r from-orange-600/20 to-orange-700/20 border-2 border-orange-600/40'
                    : 'bg-gray-100/50 dark:bg-gray-700/50'
                }`}
              >
                <div className="text-2xl font-bold text-gray-400 dark:text-gray-500 w-8">
                  {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `#${index + 1}`}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-gray-800 dark:text-gray-200">
                      {moderator.moderator_name}
                    </span>
                    <span className="text-sm">
                      {getRankIcon(moderator.rank_title)} {moderator.rank_title}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    {moderator.total_reviews} оценок
                    {moderator.average_rating && (
                      <span className="ml-2">
                        • Средняя оценка: {moderator.average_rating.toFixed(1)} ⭐
                      </span>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                    {moderator.points}
                  </div>
                  <div className="text-xs text-gray-500">баллов</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModerationDashboard;
