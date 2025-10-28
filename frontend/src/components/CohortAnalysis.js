import React, { useState, useEffect } from 'react';
import { 
  PlusIcon, 
  TrashIcon, 
  ArrowPathIcon,
  CalendarIcon,
  UsersIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import LoadingSpinner from './LoadingSpinner';
import CohortHeatmap from './CohortHeatmap';
import CohortCreateModal from './CohortCreateModal';
import UserSegmentModal from './UserSegmentModal';

const CohortAnalysis = () => {
  const [cohortAnalyses, setCohortAnalyses] = useState([]);
  const [userSegments, setUserSegments] = useState([]);
  const [selectedCohort, setSelectedCohort] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('cohorts');
  
  // Модальные окна
  const [showCreateCohort, setShowCreateCohort] = useState(false);
  const [showCreateSegment, setShowCreateSegment] = useState(false);
  const [editingSegment, setEditingSegment] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        loadCohortAnalyses(),
        loadUserSegments()
      ]);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const loadCohortAnalyses = async () => {
    try {
      const response = await fetch('/api/v1/advanced-analytics/cohort-analysis', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load cohort analyses');
      }

      const data = await response.json();
      setCohortAnalyses(data);

      // Устанавливаем первый анализ как выбранный
      if (data.length > 0 && !selectedCohort) {
        setSelectedCohort(data[0]);
      }
    } catch (error) {
      console.error('Error loading cohort analyses:', error);
      throw error;
    }
  };

  const loadUserSegments = async () => {
    try {
      const response = await fetch('/api/v1/advanced-analytics/user-segments', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load user segments');
      }

      const data = await response.json();
      setUserSegments(data);
    } catch (error) {
      console.error('Error loading user segments:', error);
      throw error;
    }
  };

  const handleCreateCohort = async (cohortData) => {
    try {
      const response = await fetch('/api/v1/advanced-analytics/cohort-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(cohortData)
      });

      if (!response.ok) {
        throw new Error('Failed to create cohort analysis');
      }

      const newCohort = await response.json();
      setCohortAnalyses(prev => [newCohort, ...prev]);
      setSelectedCohort(newCohort);
      setShowCreateCohort(false);
      
      toast.success('Когортный анализ создан');
    } catch (error) {
      console.error('Error creating cohort analysis:', error);
      toast.error('Ошибка создания когортного анализа');
    }
  };

  const handleDeleteCohort = async (cohortId) => {
    if (!window.confirm('Удалить когортный анализ?')) return;

    try {
      const response = await fetch(`/api/v1/advanced-analytics/cohort-analysis/${cohortId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete cohort analysis');
      }

      setCohortAnalyses(prev => prev.filter(c => c.id !== cohortId));
      
      if (selectedCohort?.id === cohortId) {
        setSelectedCohort(cohortAnalyses.find(c => c.id !== cohortId) || null);
      }

      toast.success('Когортный анализ удален');
    } catch (error) {
      console.error('Error deleting cohort analysis:', error);
      toast.error('Ошибка удаления когортного анализа');
    }
  };

  const handleRefreshCohort = async (cohortId) => {
    try {
      const response = await fetch(`/api/v1/advanced-analytics/cohort-analysis/${cohortId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to refresh cohort analysis');
      }

      const updatedCohort = await response.json();
      setCohortAnalyses(prev => prev.map(c => c.id === cohortId ? updatedCohort : c));
      
      if (selectedCohort?.id === cohortId) {
        setSelectedCohort(updatedCohort);
      }

      toast.success('Данные когорт обновлены');
    } catch (error) {
      console.error('Error refreshing cohort analysis:', error);
      toast.error('Ошибка обновления данных');
    }
  };

  const handleCreateSegment = async (segmentData) => {
    try {
      const response = await fetch('/api/v1/advanced-analytics/user-segments', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(segmentData)
      });

      if (!response.ok) {
        throw new Error('Failed to create user segment');
      }

      const newSegment = await response.json();
      setUserSegments(prev => [newSegment, ...prev]);
      setShowCreateSegment(false);
      
      toast.success('Сегмент пользователей создан');
    } catch (error) {
      console.error('Error creating user segment:', error);
      toast.error('Ошибка создания сегмента');
    }
  };

  const handleUpdateSegment = async (segmentId, segmentData) => {
    try {
      const response = await fetch(`/api/v1/advanced-analytics/user-segments/${segmentId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(segmentData)
      });

      if (!response.ok) {
        throw new Error('Failed to update user segment');
      }

      const updatedSegment = await response.json();
      setUserSegments(prev => prev.map(s => s.id === segmentId ? updatedSegment : s));
      setEditingSegment(null);
      setShowCreateSegment(false);
      
      toast.success('Сегмент обновлен');
    } catch (error) {
      console.error('Error updating user segment:', error);
      toast.error('Ошибка обновления сегмента');
    }
  };

  const handleDeleteSegment = async (segmentId) => {
    if (!window.confirm('Удалить сегмент пользователей?')) return;

    try {
      const response = await fetch(`/api/v1/advanced-analytics/user-segments/${segmentId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete user segment');
      }

      setUserSegments(prev => prev.filter(s => s.id !== segmentId));
      toast.success('Сегмент удален');
    } catch (error) {
      console.error('Error deleting user segment:', error);
      toast.error('Ошибка удаления сегмента');
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('ru-RU');
  };

  const getCohortTypeLabel = (type) => {
    const types = {
      'registration': 'Регистрация',
      'first_purchase': 'Первая покупка',
      'first_query': 'Первый запрос',
      'subscription': 'Подписка'
    };
    return types[type] || type;
  };

  const getPeriodTypeLabel = (type) => {
    const types = {
      'daily': 'Ежедневно',
      'weekly': 'Еженедельно',
      'monthly': 'Ежемесячно'
    };
    return types[type] || type;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Когортный анализ и сегментация
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Анализ удержания пользователей и создание сегментов
            </p>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowCreateCohort(true)}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              <PlusIcon className="h-4 w-4 mr-2" />
              Новый анализ
            </button>
            
            <button
              onClick={() => setShowCreateSegment(true)}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
            >
              <UsersIcon className="h-4 w-4 mr-2" />
              Новый сегмент
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="mt-6">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('cohorts')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'cohorts'
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              Когортный анализ
            </button>
            <button
              onClick={() => setActiveTab('segments')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'segments'
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              Сегменты пользователей
            </button>
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex overflow-hidden">
        {activeTab === 'cohorts' ? (
          <>
            {/* Cohort List */}
            <div className="w-1/3 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 overflow-y-auto">
              <div className="p-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                  Анализы когорт
                </h3>
                
                {cohortAnalyses.length === 0 ? (
                  <div className="text-center py-8">
                    <ChartBarIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500 dark:text-gray-400">
                      Нет созданных анализов
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {cohortAnalyses.map(cohort => (
                      <div
                        key={cohort.id}
                        className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                          selectedCohort?.id === cohort.id
                            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                            : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
                        }`}
                        onClick={() => setSelectedCohort(cohort)}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium text-gray-900 dark:text-white">
                            {cohort.name}
                          </h4>
                          <div className="flex items-center space-x-1">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleRefreshCohort(cohort.id);
                              }}
                              className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                              title="Обновить данные"
                            >
                              <ArrowPathIcon className="h-4 w-4" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDeleteCohort(cohort.id);
                              }}
                              className="p-1 text-gray-400 hover:text-red-600"
                              title="Удалить"
                            >
                              <TrashIcon className="h-4 w-4" />
                            </button>
                          </div>
                        </div>
                        
                        <div className="text-sm text-gray-500 dark:text-gray-400 space-y-1">
                          <div>Тип: {getCohortTypeLabel(cohort.cohort_type)}</div>
                          <div>Период: {getPeriodTypeLabel(cohort.period_type)}</div>
                          <div>
                            {formatDate(cohort.start_date)} - {formatDate(cohort.end_date)}
                          </div>
                          {cohort.data?.summary && (
                            <div className="mt-2 text-xs">
                              Пользователей: {cohort.data.summary.total_users} | 
                              Когорт: {cohort.data.summary.total_cohorts} |
                              Средний retention: {cohort.data.summary.avg_retention}%
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Cohort Visualization */}
            <div className="flex-1 bg-white dark:bg-gray-800 overflow-y-auto">
              {selectedCohort ? (
                <div className="p-6">
                  <div className="mb-6">
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                      {selectedCohort.name}
                    </h2>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {selectedCohort.description}
                    </div>
                  </div>

                  <CohortHeatmap cohortData={selectedCohort.data} />
                </div>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <ChartBarIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                      Выберите анализ когорт
                    </h3>
                    <p className="text-gray-500 dark:text-gray-400">
                      Выберите анализ из списка слева для просмотра данных
                    </p>
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          /* User Segments */
          <div className="flex-1 bg-white dark:bg-gray-800 overflow-y-auto">
            <div className="p-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Сегменты пользователей
              </h3>
              
              {userSegments.length === 0 ? (
                <div className="text-center py-12">
                  <UsersIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    Нет созданных сегментов
                  </h3>
                  <p className="text-gray-500 dark:text-gray-400 mb-4">
                    Создайте первый сегмент пользователей для анализа
                  </p>
                  <button
                    onClick={() => setShowCreateSegment(true)}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                  >
                    Создать сегмент
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {userSegments.map(segment => (
                    <div
                      key={segment.id}
                      className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-medium text-gray-900 dark:text-white">
                          {segment.name}
                        </h4>
                        <div className="flex items-center space-x-1">
                          <button
                            onClick={() => {
                              setEditingSegment(segment);
                              setShowCreateSegment(true);
                            }}
                            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                            title="Редактировать"
                          >
                            <PlusIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteSegment(segment.id)}
                            className="p-1 text-gray-400 hover:text-red-600"
                            title="Удалить"
                          >
                            <TrashIcon className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                      
                      {segment.description && (
                        <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
                          {segment.description}
                        </p>
                      )}
                      
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-500 dark:text-gray-400">
                          Пользователей:
                        </span>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {segment.user_count.toLocaleString()}
                        </span>
                      </div>
                      
                      <div className="flex items-center justify-between text-sm mt-1">
                        <span className="text-gray-500 dark:text-gray-400">
                          Тип:
                        </span>
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          segment.is_dynamic 
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                            : 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
                        }`}>
                          {segment.is_dynamic ? 'Динамический' : 'Статический'}
                        </span>
                      </div>
                      
                      <div className="mt-3 text-xs text-gray-400">
                        Создан: {formatDate(segment.created_at)}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      {showCreateCohort && (
        <CohortCreateModal
          onSave={handleCreateCohort}
          onClose={() => setShowCreateCohort(false)}
        />
      )}

      {showCreateSegment && (
        <UserSegmentModal
          segment={editingSegment}
          onSave={editingSegment ? 
            (data) => handleUpdateSegment(editingSegment.id, data) : 
            handleCreateSegment
          }
          onClose={() => {
            setShowCreateSegment(false);
            setEditingSegment(null);
          }}
        />
      )}
    </div>
  );
};

export default CohortAnalysis;