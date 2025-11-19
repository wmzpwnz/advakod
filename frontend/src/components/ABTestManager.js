import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  TestTube,
  Plus,
  Play,
  Pause,
  Square,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Users,
  Target,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Eye,
  Edit,
  Trash2,
  Copy,
  Download,
  RefreshCw,
  Zap,
  Award,
  Activity,
  Percent
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import ModuleCard from './ModuleCard';
import EnhancedButton from './EnhancedButton';
import LoadingSpinner from './LoadingSpinner';
import ModuleErrorBoundary from './ModuleErrorBoundary';

const ABTestManager = () => {
  const { getModuleColor } = useTheme();
  const [tests, setTests] = useState([]);
  const [testStats, setTestStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showResultsModal, setShowResultsModal] = useState(false);
  const [selectedTest, setSelectedTest] = useState(null);
  
  // Form state
  const [testForm, setTestForm] = useState({
    name: '',
    description: '',
    hypothesis: '',
    type: 'page',
    variants: [
      { name: 'Control', description: '', isControl: true, trafficPercentage: 50 },
      { name: 'Variant A', description: '', isControl: false, trafficPercentage: 50 }
    ],
    trafficAllocation: 100,
    duration: 14,
    sampleSize: 1000,
    confidenceLevel: 95,
    primaryMetric: 'conversion_rate',
    secondaryMetrics: ['bounce_rate', 'session_duration']
  });

  useEffect(() => {
    loadTestData();
  }, []);

  const loadTestData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const [testsRes, statsRes] = await Promise.all([
        fetch('/api/v1/marketing/ab-tests', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch('/api/v1/marketing/ab-tests/stats', {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      if (testsRes.ok) {
        const testsData = await testsRes.json();
        setTests(testsData);
      }

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setTestStats(statsData);
      }

    } catch (err) {
      setError('Ошибка загрузки A/B тестов');
      console.error('Error loading AB tests:', err);
    } finally {
      setLoading(false);
    }
  };

  const createTest = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v1/marketing/ab-tests', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(testForm)
      });

      if (response.ok) {
        setShowCreateModal(false);
        resetForm();
        loadTestData();
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Ошибка создания теста');
      }
    } catch (err) {
      setError('Ошибка создания теста');
    }
  };

  const updateTestStatus = async (testId, status) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/v1/marketing/ab-tests/${testId}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ status })
      });

      if (response.ok) {
        loadTestData();
      } else {
        setError('Ошибка изменения статуса теста');
      }
    } catch (err) {
      setError('Ошибка изменения статуса теста');
    }
  };

  const deleteTest = async (testId) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот тест?')) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/v1/marketing/ab-tests/${testId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        loadTestData();
      } else {
        setError('Ошибка удаления теста');
      }
    } catch (err) {
      setError('Ошибка удаления теста');
    }
  };

  const addVariant = () => {
    const newVariant = {
      name: `Variant ${String.fromCharCode(65 + testForm.variants.length - 1)}`,
      description: '',
      isControl: false,
      trafficPercentage: 0
    };
    setTestForm(prev => ({
      ...prev,
      variants: [...prev.variants, newVariant]
    }));
  };

  const removeVariant = (index) => {
    if (testForm.variants.length <= 2) return;
    setTestForm(prev => ({
      ...prev,
      variants: prev.variants.filter((_, i) => i !== index)
    }));
  };

  const resetForm = () => {
    setTestForm({
      name: '',
      description: '',
      hypothesis: '',
      type: 'page',
      variants: [
        { name: 'Control', description: '', isControl: true, trafficPercentage: 50 },
        { name: 'Variant A', description: '', isControl: false, trafficPercentage: 50 }
      ],
      trafficAllocation: 100,
      duration: 14,
      sampleSize: 1000,
      confidenceLevel: 95,
      primaryMetric: 'conversion_rate',
      secondaryMetrics: ['bounce_rate', 'session_duration']
    });
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running': return <Play className="h-4 w-4 text-green-500" />;
      case 'paused': return <Pause className="h-4 w-4 text-yellow-500" />;
      case 'completed': return <CheckCircle className="h-4 w-4 text-blue-500" />;
      case 'cancelled': return <XCircle className="h-4 w-4 text-red-500" />;
      default: return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusLabel = (status) => {
    const labels = {
      draft: 'Черновик',
      running: 'Запущен',
      paused: 'Приостановлен',
      completed: 'Завершен',
      cancelled: 'Отменен'
    };
    return labels[status] || status;
  };

  const getWinnerVariant = (test) => {
    if (!test.results?.winner) return null;
    return test.variants.find(v => v.id === test.results.winner);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <LoadingSpinner 
          size="lg" 
          module="marketing" 
          variant="neon"
          text="Загрузка A/B тестов..."
        />
      </div>
    );
  }

  return (
    <ModuleErrorBoundary module="marketing" componentName="ABTestManager">
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
                  <TestTube className="h-8 w-8 text-orange-500 mr-3" />
                  A/B Тестирование
                </h1>
                <p className="mt-2 text-gray-600 dark:text-gray-400">
                  Создание, управление и анализ A/B тестов для оптимизации конверсий
                </p>
              </div>
              
              <div className="mt-6 lg:mt-0 flex flex-wrap gap-3">
                <EnhancedButton
                  variant="module-outline"
                  module="marketing"
                  onClick={() => setShowResultsModal(true)}
                  icon={<BarChart3 className="h-4 w-4" />}
                >
                  Сводка результатов
                </EnhancedButton>
                
                <EnhancedButton
                  variant="module"
                  module="marketing"
                  onClick={() => setShowCreateModal(true)}
                  icon={<Plus className="h-4 w-4" />}
                >
                  Создать тест
                </EnhancedButton>
              </div>
            </div>
          </motion.div>

          {/* Stats Cards */}
          <motion.div 
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <ModuleCard module="marketing" variant="module-neon">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Всего тестов</p>
                  <p className="text-2xl font-bold text-orange-600">
                    {testStats.totalTests || 0}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {testStats.runningTests || 0} активных
                  </p>
                </div>
                <div className="p-3 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
                  <TestTube className="h-6 w-6 text-orange-600" />
                </div>
              </div>
            </ModuleCard>

            <ModuleCard module="marketing" variant="module">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Участников</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {testStats.totalParticipants?.toLocaleString() || 0}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    В активных тестах
                  </p>
                </div>
                <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                  <Users className="h-6 w-6 text-blue-600" />
                </div>
              </div>
            </ModuleCard>

            <ModuleCard module="marketing" variant="module">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Успешных тестов</p>
                  <p className="text-2xl font-bold text-green-600">
                    {testStats.successfulTests || 0}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Со значимыми результатами
                  </p>
                </div>
                <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                  <Award className="h-6 w-6 text-green-600" />
                </div>
              </div>
            </ModuleCard>

            <ModuleCard module="marketing" variant="module">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Средний прирост</p>
                  <p className="text-2xl font-bold text-purple-600">
                    +{testStats.averageUplift?.toFixed(1) || 0}%
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    По завершенным тестам
                  </p>
                </div>
                <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                  <TrendingUp className="h-6 w-6 text-purple-600" />
                </div>
              </div>
            </ModuleCard>
          </motion.div>

          {/* Tests List */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <ModuleCard module="marketing" variant="module">
              <div className="space-y-6">
                {tests.length === 0 ? (
                  <div className="text-center py-12">
                    <TestTube className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                      Нет A/B тестов
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400 mb-6">
                      Создайте свой первый A/B тест для оптимизации конверсий
                    </p>
                    <EnhancedButton
                      variant="module"
                      module="marketing"
                      onClick={() => setShowCreateModal(true)}
                      icon={<Plus className="h-4 w-4" />}
                    >
                      Создать первый тест
                    </EnhancedButton>
                  </div>
                ) : (
                  tests.map((test, index) => (
                  <motion.div
                    key={test.id}
                    className="border border-gray-200 dark:border-gray-700 rounded-lg p-6"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.1 }}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center mb-2">
                          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mr-3">
                            {test.name}
                          </h3>
                          <div className="flex items-center">
                            {getStatusIcon(test.status)}
                            <span className="ml-1 text-sm font-medium">
                              {getStatusLabel(test.status)}
                            </span>
                          </div>
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                          {test.description}
                        </p>
                        <div className="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
                          <span className="flex items-center">
                            <Users className="h-4 w-4 mr-1" />
                            {test.participants?.toLocaleString()} участников
                          </span>
                          <span className="flex items-center">
                            <Clock className="h-4 w-4 mr-1" />
                            {test.duration} дней
                          </span>
                          <span className="flex items-center">
                            <Target className="h-4 w-4 mr-1" />
                            {test.confidenceLevel}% уверенность
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        {test.status === 'draft' && (
                          <EnhancedButton
                            variant="module-outline"
                            module="marketing"
                            size="sm"
                            onClick={() => updateTestStatus(test.id, 'running')}
                            icon={<Play className="h-4 w-4" />}
                          >
                            Запустить
                          </EnhancedButton>
                        )}
                        
                        {test.status === 'running' && (
                          <>
                            <EnhancedButton
                              variant="module-outline"
                              module="marketing"
                              size="sm"
                              onClick={() => updateTestStatus(test.id, 'paused')}
                              icon={<Pause className="h-4 w-4" />}
                            >
                              Пауза
                            </EnhancedButton>
                            <EnhancedButton
                              variant="module-outline"
                              module="marketing"
                              size="sm"
                              onClick={() => updateTestStatus(test.id, 'completed')}
                              icon={<Square className="h-4 w-4" />}
                            >
                              Завершить
                            </EnhancedButton>
                          </>
                        )}
                        
                        {test.status === 'paused' && (
                          <EnhancedButton
                            variant="module-outline"
                            module="marketing"
                            size="sm"
                            onClick={() => updateTestStatus(test.id, 'running')}
                            icon={<Play className="h-4 w-4" />}
                          >
                            Продолжить
                          </EnhancedButton>
                        )}
                        
                        {(test.status === 'completed' || test.status === 'cancelled') && (
                          <EnhancedButton
                            variant="module-outline"
                            module="marketing"
                            size="sm"
                            onClick={() => {
                              setSelectedTest(test);
                              setShowResultsModal(true);
                            }}
                            icon={<BarChart3 className="h-4 w-4" />}
                          >
                            Результаты
                          </EnhancedButton>
                        )}
                        
                        <button
                          onClick={() => deleteTest(test.id)}
                          className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 p-1"
                          title="Удалить"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>

                    {/* Variants */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {test.variants?.map((variant, vIndex) => {
                        const conversionRate = variant.participants > 0 
                          ? (variant.conversions / variant.participants * 100).toFixed(2)
                          : 0;
                        const isWinner = test.results?.winner === variant.id;
                        
                        return (
                          <div 
                            key={variant.id}
                            className={`p-4 rounded-lg border-2 transition-all ${
                              isWinner 
                                ? 'border-green-400 bg-green-50 dark:bg-green-900/20' 
                                : variant.isControl
                                  ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/20'
                                  : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800'
                            }`}
                          >
                            <div className="flex items-center justify-between mb-2">
                              <h4 className="font-medium text-gray-900 dark:text-gray-100">
                                {variant.name}
                                {variant.isControl && (
                                  <span className="ml-2 text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-2 py-1 rounded-full">
                                    Контроль
                                  </span>
                                )}
                                {isWinner && (
                                  <span className="ml-2 text-xs bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 px-2 py-1 rounded-full">
                                    Победитель
                                  </span>
                                )}
                              </h4>
                              <span className="text-sm text-gray-500 dark:text-gray-400">
                                {variant.trafficPercentage}%
                              </span>
                            </div>
                            
                            <div className="space-y-2 text-sm">
                              <div className="flex justify-between">
                                <span className="text-gray-600 dark:text-gray-400">Участники:</span>
                                <span className="font-medium">{variant.participants?.toLocaleString()}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600 dark:text-gray-400">Конверсии:</span>
                                <span className="font-medium">{variant.conversions?.toLocaleString()}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-600 dark:text-gray-400">Конверсия:</span>
                                <span className={`font-medium ${
                                  isWinner ? 'text-green-600' : 'text-gray-900 dark:text-gray-100'
                                }`}>
                                  {conversionRate}%
                                </span>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Test Results Summary */}
                    {test.results && (
                      <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <Award className="h-5 w-5 text-blue-600 mr-2" />
                            <span className="font-medium text-blue-800 dark:text-blue-300">
                              Результаты теста
                            </span>
                          </div>
                          <div className="flex items-center space-x-4 text-sm">
                            <span className="text-blue-700 dark:text-blue-400">
                              Уверенность: {test.results.confidence}%
                            </span>
                            <span className="text-blue-700 dark:text-blue-400">
                              Прирост: +{test.results.uplift?.toFixed(1)}%
                            </span>
                            {test.results.statisticalSignificance && (
                              <span className="text-green-600 font-medium">
                                Статистически значим
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </motion.div>
                  ))
                )}
              </div>
            </ModuleCard>
          </motion.div>
        </div>

        {/* Create Test Modal */}
        <AnimatePresence>
          {showCreateModal && (
            <motion.div
              className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <motion.div
                className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto"
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
              >
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    Создать A/B тест
                  </h2>
                  <button
                    onClick={() => setShowCreateModal(false)}
                    className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  >
                    <XCircle className="h-6 w-6" />
                  </button>
                </div>

                <form onSubmit={createTest} className="space-y-6">
                  {/* Basic Information */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Название теста *
                      </label>
                      <input
                        type="text"
                        value={testForm.name}
                        onChange={(e) => setTestForm(prev => ({ ...prev, name: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        placeholder="Например: Тест новой кнопки регистрации"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Тип теста
                      </label>
                      <select
                        value={testForm.type}
                        onChange={(e) => setTestForm(prev => ({ ...prev, type: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                      >
                        <option value="page">Страница</option>
                        <option value="feature">Функция</option>
                        <option value="element">Элемент</option>
                        <option value="flow">Поток</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Описание
                    </label>
                    <textarea
                      value={testForm.description}
                      onChange={(e) => setTestForm(prev => ({ ...prev, description: e.target.value }))}
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                      placeholder="Краткое описание теста и его целей"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Гипотеза
                    </label>
                    <textarea
                      value={testForm.hypothesis}
                      onChange={(e) => setTestForm(prev => ({ ...prev, hypothesis: e.target.value }))}
                      rows={2}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                      placeholder="Мы считаем, что изменение X приведет к Y, потому что..."
                    />
                  </div>

                  {/* Test Configuration */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Трафик (%)
                      </label>
                      <input
                        type="number"
                        min="1"
                        max="100"
                        value={testForm.trafficAllocation}
                        onChange={(e) => setTestForm(prev => ({ ...prev, trafficAllocation: parseInt(e.target.value) }))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Длительность (дни)
                      </label>
                      <input
                        type="number"
                        min="1"
                        max="365"
                        value={testForm.duration}
                        onChange={(e) => setTestForm(prev => ({ ...prev, duration: parseInt(e.target.value) }))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Размер выборки
                      </label>
                      <input
                        type="number"
                        min="100"
                        value={testForm.sampleSize}
                        onChange={(e) => setTestForm(prev => ({ ...prev, sampleSize: parseInt(e.target.value) }))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                      />
                    </div>
                  </div>

                  {/* Metrics Configuration */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Основная метрика
                      </label>
                      <select
                        value={testForm.primaryMetric}
                        onChange={(e) => setTestForm(prev => ({ ...prev, primaryMetric: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                      >
                        <option value="conversion_rate">Конверсия</option>
                        <option value="click_through_rate">CTR</option>
                        <option value="bounce_rate">Отказы</option>
                        <option value="session_duration">Время сессии</option>
                        <option value="revenue_per_user">Доход на пользователя</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Уровень доверия (%)
                      </label>
                      <select
                        value={testForm.confidenceLevel}
                        onChange={(e) => setTestForm(prev => ({ ...prev, confidenceLevel: parseFloat(e.target.value) }))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                      >
                        <option value="90">90%</option>
                        <option value="95">95%</option>
                        <option value="99">99%</option>
                      </select>
                    </div>
                  </div>

                  {/* Variants */}
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                        Варианты теста
                      </h3>
                      <EnhancedButton
                        type="button"
                        variant="module-outline"
                        module="marketing"
                        size="sm"
                        onClick={addVariant}
                        icon={<Plus className="h-4 w-4" />}
                      >
                        Добавить вариант
                      </EnhancedButton>
                    </div>

                    <div className="space-y-4">
                      {testForm.variants.map((variant, index) => (
                        <div key={index} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center">
                              <input
                                type="checkbox"
                                checked={variant.isControl}
                                onChange={(e) => {
                                  const newVariants = [...testForm.variants];
                                  // Ensure only one control variant
                                  if (e.target.checked) {
                                    newVariants.forEach((v, i) => {
                                      v.isControl = i === index;
                                    });
                                  }
                                  setTestForm(prev => ({ ...prev, variants: newVariants }));
                                }}
                                className="mr-2"
                              />
                              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                Контрольный вариант
                              </label>
                            </div>
                            {testForm.variants.length > 2 && (
                              <button
                                type="button"
                                onClick={() => removeVariant(index)}
                                className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            )}
                          </div>

                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Название варианта
                              </label>
                              <input
                                type="text"
                                value={variant.name}
                                onChange={(e) => {
                                  const newVariants = [...testForm.variants];
                                  newVariants[index].name = e.target.value;
                                  setTestForm(prev => ({ ...prev, variants: newVariants }));
                                }}
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                placeholder="Название варианта"
                              />
                            </div>

                            <div>
                              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Трафик (%)
                              </label>
                              <input
                                type="number"
                                min="0"
                                max="100"
                                value={variant.trafficPercentage}
                                onChange={(e) => {
                                  const newVariants = [...testForm.variants];
                                  newVariants[index].trafficPercentage = parseFloat(e.target.value);
                                  setTestForm(prev => ({ ...prev, variants: newVariants }));
                                }}
                                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                              />
                            </div>
                          </div>

                          <div className="mt-3">
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                              Описание
                            </label>
                            <textarea
                              value={variant.description}
                              onChange={(e) => {
                                const newVariants = [...testForm.variants];
                                newVariants[index].description = e.target.value;
                                setTestForm(prev => ({ ...prev, variants: newVariants }));
                              }}
                              rows={2}
                              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                              placeholder="Описание изменений в этом варианте"
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Form Actions */}
                  <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200 dark:border-gray-700">
                    <EnhancedButton
                      type="button"
                      variant="outline"
                      onClick={() => {
                        setShowCreateModal(false);
                        resetForm();
                      }}
                    >
                      Отмена
                    </EnhancedButton>
                    <EnhancedButton
                      type="submit"
                      variant="module"
                      module="marketing"
                      icon={<TestTube className="h-4 w-4" />}
                    >
                      Создать тест
                    </EnhancedButton>
                  </div>
                </form>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Results Modal */}
        <AnimatePresence>
          {showResultsModal && selectedTest && (
            <motion.div
              className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              <motion.div
                className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-6xl max-h-[90vh] overflow-y-auto"
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.9, opacity: 0 }}
              >
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    Результаты теста: {selectedTest.name}
                  </h2>
                  <button
                    onClick={() => {
                      setShowResultsModal(false);
                      setSelectedTest(null);
                    }}
                    className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  >
                    <XCircle className="h-6 w-6" />
                  </button>
                </div>

                {/* Test Overview */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                  <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-blue-600 dark:text-blue-400">Участники</p>
                        <p className="text-2xl font-bold text-blue-800 dark:text-blue-300">
                          {selectedTest.participants?.toLocaleString() || 0}
                        </p>
                      </div>
                      <Users className="h-8 w-8 text-blue-600" />
                    </div>
                  </div>

                  <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-green-600 dark:text-green-400">Конверсии</p>
                        <p className="text-2xl font-bold text-green-800 dark:text-green-300">
                          {selectedTest.conversions?.toLocaleString() || 0}
                        </p>
                      </div>
                      <Target className="h-8 w-8 text-green-600" />
                    </div>
                  </div>

                  <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-purple-600 dark:text-purple-400">Прирост</p>
                        <p className="text-2xl font-bold text-purple-800 dark:text-purple-300">
                          +{selectedTest.results?.uplift?.toFixed(1) || 0}%
                        </p>
                      </div>
                      <TrendingUp className="h-8 w-8 text-purple-600" />
                    </div>
                  </div>

                  <div className="bg-orange-50 dark:bg-orange-900/20 p-4 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-orange-600 dark:text-orange-400">Уверенность</p>
                        <p className="text-2xl font-bold text-orange-800 dark:text-orange-300">
                          {selectedTest.results?.confidence || selectedTest.confidenceLevel}%
                        </p>
                      </div>
                      <Award className="h-8 w-8 text-orange-600" />
                    </div>
                  </div>
                </div>

                {/* Statistical Significance */}
                {selectedTest.results && (
                  <div className={`p-4 rounded-lg mb-6 ${
                    selectedTest.results.statisticalSignificance
                      ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
                      : 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800'
                  }`}>
                    <div className="flex items-center">
                      {selectedTest.results.statisticalSignificance ? (
                        <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                      ) : (
                        <AlertTriangle className="h-5 w-5 text-yellow-600 mr-2" />
                      )}
                      <span className={`font-medium ${
                        selectedTest.results.statisticalSignificance
                          ? 'text-green-800 dark:text-green-300'
                          : 'text-yellow-800 dark:text-yellow-300'
                      }`}>
                        {selectedTest.results.statisticalSignificance
                          ? 'Результаты статистически значимы'
                          : 'Результаты не достигли статистической значимости'
                        }
                      </span>
                    </div>
                    {selectedTest.results.pValue && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        p-value: {selectedTest.results.pValue.toFixed(4)}
                      </p>
                    )}
                  </div>
                )}

                {/* Variants Comparison */}
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                    Сравнение вариантов
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {selectedTest.variants?.map((variant) => {
                      const conversionRate = variant.participants > 0 
                        ? (variant.conversions / variant.participants * 100).toFixed(2)
                        : 0;
                      const isWinner = selectedTest.results?.winner === variant.id;
                      
                      return (
                        <div 
                          key={variant.id}
                          className={`p-4 rounded-lg border-2 ${
                            isWinner 
                              ? 'border-green-400 bg-green-50 dark:bg-green-900/20' 
                              : variant.isControl
                                ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/20'
                                : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-3">
                            <h4 className="font-medium text-gray-900 dark:text-gray-100">
                              {variant.name}
                            </h4>
                            <div className="flex space-x-1">
                              {variant.isControl && (
                                <span className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-2 py-1 rounded-full">
                                  Контроль
                                </span>
                              )}
                              {isWinner && (
                                <span className="text-xs bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 px-2 py-1 rounded-full">
                                  Победитель
                                </span>
                              )}
                            </div>
                          </div>
                          
                          <div className="space-y-3">
                            <div className="flex justify-between">
                              <span className="text-sm text-gray-600 dark:text-gray-400">Участники:</span>
                              <span className="font-medium">{variant.participants?.toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-sm text-gray-600 dark:text-gray-400">Конверсии:</span>
                              <span className="font-medium">{variant.conversions?.toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-sm text-gray-600 dark:text-gray-400">Конверсия:</span>
                              <span className={`font-bold text-lg ${
                                isWinner ? 'text-green-600' : 'text-gray-900 dark:text-gray-100'
                              }`}>
                                {conversionRate}%
                              </span>
                            </div>
                            {variant.confidenceInterval && (
                              <div className="text-xs text-gray-500 dark:text-gray-400">
                                95% CI: [{variant.confidenceInterval.lower.toFixed(2)}%, {variant.confidenceInterval.upper.toFixed(2)}%]
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Recommendations */}
                {selectedTest.results?.recommendations && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                      Рекомендации
                    </h3>
                    <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                      <ul className="space-y-2">
                        {selectedTest.results.recommendations.map((recommendation, index) => (
                          <li key={index} className="flex items-start">
                            <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                            <span className="text-blue-800 dark:text-blue-300">{recommendation}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200 dark:border-gray-700">
                  <EnhancedButton
                    variant="module-outline"
                    module="marketing"
                    icon={<Download className="h-4 w-4" />}
                  >
                    Экспорт данных
                  </EnhancedButton>
                  <EnhancedButton
                    variant="module"
                    module="marketing"
                    onClick={() => {
                      setShowResultsModal(false);
                      setSelectedTest(null);
                    }}
                  >
                    Закрыть
                  </EnhancedButton>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </ModuleErrorBoundary>
  );
};

export default ABTestManager;