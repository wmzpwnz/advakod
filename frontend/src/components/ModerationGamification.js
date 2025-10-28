import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Trophy,
  Star,
  Zap,
  Target,
  Award,
  Crown,
  Medal,
  Flame,
  TrendingUp,
  Calendar,
  Users,
  CheckCircle,
  Gift,
  Sparkles,
  Clock,
  BarChart3
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import ModuleCard from './ModuleCard';
import EnhancedButton from './EnhancedButton';
import LoadingSpinner from './LoadingSpinner';

const ModerationGamification = () => {
  const { getModuleColor } = useTheme();
  const [moderatorStats, setModeratorStats] = useState(null);
  const [achievements, setAchievements] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [challenges, setChallenges] = useState([]);
  const [rewards, setRewards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadGamificationData();
  }, []);

  const loadGamificationData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const [statsRes, achievementsRes, leaderboardRes, challengesRes, rewardsRes] = await Promise.all([
        fetch('/api/v1/moderation/gamification/stats', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch('/api/v1/moderation/gamification/achievements', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch('/api/v1/moderation/gamification/leaderboard', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch('/api/v1/moderation/gamification/challenges', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch('/api/v1/moderation/gamification/rewards', {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      if (statsRes.ok) {
        const stats = await statsRes.json();
        setModeratorStats(stats);
      }

      if (achievementsRes.ok) {
        const achievementsData = await achievementsRes.json();
        setAchievements(achievementsData);
      }

      if (leaderboardRes.ok) {
        const leaderboardData = await leaderboardRes.json();
        setLeaderboard(leaderboardData);
      }

      if (challengesRes.ok) {
        const challengesData = await challengesRes.json();
        setChallenges(challengesData);
      }

      if (rewardsRes.ok) {
        const rewardsData = await rewardsRes.json();
        setRewards(rewardsData);
      }

    } catch (err) {
      console.error('Error loading gamification data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getRankConfig = (rank) => {
    const configs = {
      legend: { 
        icon: Crown, 
        color: 'text-yellow-500', 
        bg: 'bg-gradient-to-r from-yellow-400 to-orange-500',
        label: 'Легенда',
        minPoints: 50000
      },
      master: { 
        icon: Trophy, 
        color: 'text-purple-500', 
        bg: 'bg-gradient-to-r from-purple-500 to-pink-500',
        label: 'Мастер',
        minPoints: 25000
      },
      expert: { 
        icon: Medal, 
        color: 'text-blue-500', 
        bg: 'bg-gradient-to-r from-blue-500 to-cyan-500',
        label: 'Эксперт',
        minPoints: 10000
      },
      advanced: { 
        icon: Award, 
        color: 'text-green-500', 
        bg: 'bg-gradient-to-r from-green-500 to-emerald-500',
        label: 'Продвинутый',
        minPoints: 5000
      },
      intermediate: { 
        icon: Star, 
        color: 'text-orange-500', 
        bg: 'bg-gradient-to-r from-orange-500 to-red-500',
        label: 'Средний',
        minPoints: 1000
      },
      beginner: { 
        icon: Sparkles, 
        color: 'text-gray-500', 
        bg: 'bg-gradient-to-r from-gray-400 to-gray-600',
        label: 'Новичок',
        minPoints: 0
      }
    };
    return configs[rank] || configs.beginner;
  };

  const getNextRank = (currentRank, currentPoints) => {
    const ranks = ['beginner', 'intermediate', 'advanced', 'expert', 'master', 'legend'];
    const currentIndex = ranks.indexOf(currentRank);
    
    if (currentIndex < ranks.length - 1) {
      const nextRank = ranks[currentIndex + 1];
      const nextRankConfig = getRankConfig(nextRank);
      const pointsNeeded = nextRankConfig.minPoints - currentPoints;
      return { rank: nextRank, pointsNeeded, config: nextRankConfig };
    }
    
    return null;
  };

  const calculateProgress = (current, target) => {
    return Math.min((current / target) * 100, 100);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <LoadingSpinner 
          size="lg" 
          module="moderation" 
          variant="neon"
          text="Загрузка системы достижений..."
        />
      </div>
    );
  }

  const currentRankConfig = getRankConfig(moderatorStats?.rank);
  const nextRank = getNextRank(moderatorStats?.rank, moderatorStats?.points);

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
                <Trophy className="h-8 w-8 text-purple-500 mr-3" />
                Система достижений
              </h1>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                Геймификация модерации с рангами, достижениями и наградами
              </p>
            </div>
          </div>
        </motion.div>

        {/* Moderator Profile Card */}
        <motion.div
          className="mb-8"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <ModuleCard module="moderation" variant="module-neon" className="relative overflow-hidden">
            {/* Background gradient */}
            <div 
              className="absolute inset-0 opacity-10"
              style={{ background: currentRankConfig.bg }}
            />
            
            <div className="relative z-10">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between">
                <div className="flex items-center mb-6 md:mb-0">
                  <div 
                    className="p-4 rounded-2xl mr-6"
                    style={{ background: currentRankConfig.bg }}
                  >
                    <currentRankConfig.icon className="h-12 w-12 text-white" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                      {moderatorStats?.userName || 'Модератор'}
                    </h2>
                    <p className={`text-lg font-semibold ${currentRankConfig.color}`}>
                      {currentRankConfig.label}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {moderatorStats?.points?.toLocaleString()} баллов
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {moderatorStats?.totalReviews || 0}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">Оценок</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {moderatorStats?.accuracy || 0}%
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">Точность</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {moderatorStats?.streak || 0}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">Серия</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">
                      {achievements.filter(a => a.unlocked).length}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">Достижения</div>
                  </div>
                </div>
              </div>

              {/* Progress to next rank */}
              {nextRank && (
                <div className="mt-6 p-4 bg-white/50 dark:bg-gray-800/50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Прогресс до {nextRank.config.label}
                    </span>
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      {nextRank.pointsNeeded.toLocaleString()} баллов до повышения
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                    <div 
                      className="h-3 rounded-full transition-all duration-500"
                      style={{ 
                        width: `${calculateProgress(moderatorStats?.points, nextRank.config.minPoints)}%`,
                        background: nextRank.config.bg
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          </ModuleCard>
        </motion.div>

        {/* Tabs */}
        <div className="mb-6">
          <nav className="flex space-x-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
            {[
              { id: 'overview', name: 'Обзор', icon: BarChart3 },
              { id: 'achievements', name: 'Достижения', icon: Award },
              { id: 'challenges', name: 'Челленджи', icon: Target },
              { id: 'leaderboard', name: 'Рейтинг', icon: Trophy },
              { id: 'rewards', name: 'Награды', icon: Gift }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`${
                  activeTab === tab.id
                    ? 'bg-white dark:bg-gray-700 text-purple-600 shadow-sm'
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
          {activeTab === 'achievements' && (
            <motion.div
              key="achievements"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {achievements.map((achievement) => (
                  <motion.div
                    key={achievement.id}
                    layout
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.2 }}
                  >
                    <ModuleCard 
                      module="moderation" 
                      variant={achievement.unlocked ? "module-neon" : "module"}
                      className={`relative ${!achievement.unlocked ? 'opacity-60' : ''}`}
                    >
                      {achievement.unlocked && (
                        <div className="absolute top-2 right-2">
                          <CheckCircle className="h-6 w-6 text-green-500" />
                        </div>
                      )}
                      
                      <div className="text-center">
                        <div className="text-4xl mb-3">{achievement.icon}</div>
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                          {achievement.name}
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                          {achievement.description}
                        </p>
                        
                        {achievement.unlocked ? (
                          <div className="flex items-center justify-center text-green-600">
                            <Trophy className="h-4 w-4 mr-1" />
                            <span className="text-sm font-medium">
                              +{achievement.points} баллов
                            </span>
                          </div>
                        ) : (
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            {achievement.progress}/{achievement.target} ({Math.round((achievement.progress / achievement.target) * 100)}%)
                          </div>
                        )}
                        
                        {!achievement.unlocked && (
                          <div className="mt-3">
                            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                              <div 
                                className="bg-purple-500 h-2 rounded-full transition-all duration-500"
                                style={{ width: `${Math.min((achievement.progress / achievement.target) * 100, 100)}%` }}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    </ModuleCard>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {activeTab === 'challenges' && (
            <motion.div
              key="challenges"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {challenges.map((challenge) => (
                  <ModuleCard key={challenge.id} module="moderation" variant="module-neon">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center">
                        <div className="text-3xl mr-3">{challenge.icon}</div>
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                            {challenge.name}
                          </h3>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {challenge.description}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center text-sm">
                        <Clock className="h-4 w-4 mr-1 text-gray-500" />
                        <span className="text-gray-500 dark:text-gray-400">
                          {challenge.timeLeft}
                        </span>
                      </div>
                    </div>

                    <div className="mb-4">
                      <div className="flex justify-between text-sm mb-2">
                        <span className="text-gray-600 dark:text-gray-400">Прогресс</span>
                        <span className="font-medium">
                          {challenge.progress}/{challenge.target}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                        <div 
                          className="bg-gradient-to-r from-purple-500 to-pink-500 h-3 rounded-full transition-all duration-500"
                          style={{ width: `${Math.min((challenge.progress / challenge.target) * 100, 100)}%` }}
                        />
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center text-purple-600">
                        <Zap className="h-4 w-4 mr-1" />
                        <span className="text-sm font-medium">
                          +{challenge.reward} баллов
                        </span>
                      </div>
                      {challenge.completed && (
                        <div className="flex items-center text-green-600">
                          <CheckCircle className="h-4 w-4 mr-1" />
                          <span className="text-sm font-medium">Завершено</span>
                        </div>
                      )}
                    </div>
                  </ModuleCard>
                ))}
              </div>
            </motion.div>
          )}

          {activeTab === 'leaderboard' && (
            <motion.div
              key="leaderboard"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <ModuleCard module="moderation" variant="module">
                <div className="space-y-4">
                  {leaderboard.map((moderator, index) => {
                    const rankConfig = getRankConfig(moderator.rank);
                    const isCurrentUser = moderator.id === moderatorStats?.id;
                    
                    return (
                      <motion.div
                        key={moderator.id}
                        className={`flex items-center p-4 rounded-lg transition-all ${
                          isCurrentUser 
                            ? 'bg-purple-50 dark:bg-purple-900/20 border-2 border-purple-200 dark:border-purple-700' 
                            : 'bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700'
                        }`}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.2, delay: index * 0.05 }}
                      >
                        <div className="flex items-center mr-4">
                          {index < 3 ? (
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold ${
                              index === 0 ? 'bg-yellow-500' : index === 1 ? 'bg-gray-400' : 'bg-orange-500'
                            }`}>
                              {index + 1}
                            </div>
                          ) : (
                            <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-600 flex items-center justify-center text-gray-600 dark:text-gray-400 font-bold">
                              {index + 1}
                            </div>
                          )}
                        </div>

                        <div className="flex-1 flex items-center">
                          <div 
                            className="p-2 rounded-lg mr-4"
                            style={{ background: `${getModuleColor('moderation')}20` }}
                          >
                            <rankConfig.icon className={`h-5 w-5 ${rankConfig.color}`} />
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center">
                              <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                                {moderator.name}
                                {isCurrentUser && (
                                  <span className="ml-2 text-xs bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 px-2 py-1 rounded-full">
                                    Вы
                                  </span>
                                )}
                              </h3>
                            </div>
                            <p className={`text-sm ${rankConfig.color}`}>
                              {rankConfig.label}
                            </p>
                          </div>
                        </div>

                        <div className="text-right">
                          <div className="text-lg font-bold text-gray-900 dark:text-gray-100">
                            {moderator.points.toLocaleString()}
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            {moderator.reviews} оценок
                          </div>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </ModuleCard>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default ModerationGamification;