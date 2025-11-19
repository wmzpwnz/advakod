import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Tag,
  Plus,
  Edit,
  Trash2,
  Copy,
  Eye,
  EyeOff,
  Calendar,
  Users,
  DollarSign,
  Percent,
  Gift,
  Zap,
  Target,
  TrendingUp,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Search,
  Filter,
  Download,
  RefreshCw
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import ModuleCard from './ModuleCard';
import EnhancedButton from './EnhancedButton';
import LoadingSpinner from './LoadingSpinner';
import ModuleErrorBoundary from './ModuleErrorBoundary';

const PromoCodeManager = () => {
  const { getModuleColor } = useTheme();
  const [promoCodes, setPromoCodes] = useState([]);
  const [promoStats, setPromoStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Filters and search
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterType, setFilterType] = useState('all');
  
  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showAnalyticsModal, setShowAnalyticsModal] = useState(false);
  const [selectedPromo, setSelectedPromo] = useState(null);
  
  // Form state
  const [promoForm, setPromoForm] = useState({
    code: '',
    name: '',
    description: '',
    type: 'percentage',
    value: '',
    currency: 'USD',
    minOrderAmount: '',
    maxDiscountAmount: '',
    usageLimit: '',
    userLimit: '',
    validFrom: '',
    validTo: '',
    applicableProducts: [],
    excludedProducts: [],
    isActive: true
  });

  useEffect(() => {
    loadPromoData();
  }, []);

  const loadPromoData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const [codesRes, statsRes] = await Promise.all([
        fetch('/api/v1/marketing/promo-codes', {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch('/api/v1/marketing/promo-codes/stats', {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      if (codesRes.ok) {
        const codesData = await codesRes.json();
        setPromoCodes(codesData);
      }

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setPromoStats(statsData);
      }

    } catch (err) {
      setError('Ошибка загрузки промокодов');
      console.error('Error loading promo codes:', err);
    } finally {
      setLoading(false);
    }
  };

  const generatePromoCode = () => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = '';
    for (let i = 0; i < 8; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    setPromoForm(prev => ({ ...prev, code: result }));
  };

  const createPromoCode = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v1/marketing/promo-codes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(promoForm)
      });

      if (response.ok) {
        setShowCreateModal(false);
        resetForm();
        loadPromoData();
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Ошибка создания промокода');
      }
    } catch (err) {
      setError('Ошибка создания промокода');
    }
  };

  const updatePromoCode = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/v1/marketing/promo-codes/${selectedPromo.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(promoForm)
      });

      if (response.ok) {
        setShowEditModal(false);
        setSelectedPromo(null);
        resetForm();
        loadPromoData();
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Ошибка обновления промокода');
      }
    } catch (err) {
      setError('Ошибка обновления промокода');
    }
  };

  const deletePromoCode = async (promoId) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот промокод?')) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/v1/marketing/promo-codes/${promoId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.ok) {
        loadPromoData();
      } else {
        setError('Ошибка удаления промокода');
      }
    } catch (err) {
      setError('Ошибка удаления промокода');
    }
  };

  const togglePromoStatus = async (promoId, currentStatus) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/v1/marketing/promo-codes/${promoId}/toggle`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ isActive: !currentStatus })
      });

      if (response.ok) {
        loadPromoData();
      } else {
        setError('Ошибка изменения статуса промокода');
      }
    } catch (err) {
      setError('Ошибка изменения статуса промокода');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    // Show toast notification
  };

  const resetForm = () => {
    setPromoForm({
      code: '',
      name: '',
      description: '',
      type: 'percentage',
      value: '',
      currency: 'USD',
      minOrderAmount: '',
      maxDiscountAmount: '',
      usageLimit: '',
      userLimit: '',
      validFrom: '',
      validTo: '',
      applicableProducts: [],
      excludedProducts: [],
      isActive: true
    });
  };

  const openEditModal = (promo) => {
    setSelectedPromo(promo);
    setPromoForm({
      code: promo.code,
      name: promo.name,
      description: promo.description || '',
      type: promo.type,
      value: promo.value.toString(),
      currency: promo.currency || 'USD',
      minOrderAmount: promo.minOrderAmount?.toString() || '',
      maxDiscountAmount: promo.maxDiscountAmount?.toString() || '',
      usageLimit: promo.usageLimit?.toString() || '',
      userLimit: promo.userLimit?.toString() || '',
      validFrom: promo.validFrom ? new Date(promo.validFrom).toISOString().split('T')[0] : '',
      validTo: promo.validTo ? new Date(promo.validTo).toISOString().split('T')[0] : '',
      applicableProducts: promo.applicableProducts || [],
      excludedProducts: promo.excludedProducts || [],
      isActive: promo.isActive
    });
    setShowEditModal(true);
  };

  const getPromoTypeIcon = (type) => {
    switch (type) {
      case 'percentage': return Percent;
      case 'fixed_amount': return DollarSign;
      case 'free_trial': return Gift;
      default: return Tag;
    }
  };

  const getPromoTypeLabel = (type) => {
    switch (type) {
      case 'percentage': return 'Процент';
      case 'fixed_amount': return 'Фиксированная сумма';
      case 'free_trial': return 'Бесплатный период';
      default: return type;
    }
  };

  const getStatusColor = (promo) => {
    if (!promo.isActive) return 'text-gray-500';
    
    const now = new Date();
    const validFrom = new Date(promo.validFrom);
    const validTo = new Date(promo.validTo);
    
    if (now < validFrom) return 'text-blue-500';
    if (now > validTo) return 'text-red-500';
    if (promo.usageLimit && promo.usageCount >= promo.usageLimit) return 'text-orange-500';
    
    return 'text-green-500';
  };

  const getStatusLabel = (promo) => {
    if (!promo.isActive) return 'Неактивен';
    
    const now = new Date();
    const validFrom = new Date(promo.validFrom);
    const validTo = new Date(promo.validTo);
    
    if (now < validFrom) return 'Запланирован';
    if (now > validTo) return 'Истек';
    if (promo.usageLimit && promo.usageCount >= promo.usageLimit) return 'Исчерпан';
    
    return 'Активен';
  };

  const filteredPromoCodes = promoCodes.filter(promo => {
    const matchesSearch = promo.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         promo.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = filterStatus === 'all' || 
                         (filterStatus === 'active' && promo.isActive) ||
                         (filterStatus === 'inactive' && !promo.isActive);
    const matchesType = filterType === 'all' || promo.type === filterType;
    
    return matchesSearch && matchesStatus && matchesType;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <LoadingSpinner 
          size="lg" 
          module="marketing" 
          variant="neon"
          text="Загрузка промокодов..."
        />
      </div>
    );
  }

  return (
    <ModuleErrorBoundary module="marketing" componentName="PromoCodeManager">
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
                  <Tag className="h-8 w-8 text-orange-500 mr-3" />
                  Управление промокодами
                </h1>
                <p className="mt-2 text-gray-600 dark:text-gray-400">
                  Создание, управление и аналитика промокодов и скидок
                </p>
              </div>
              
              <div className="mt-6 lg:mt-0 flex flex-wrap gap-3">
                <EnhancedButton
                  variant="module-outline"
                  module="marketing"
                  onClick={() => setShowAnalyticsModal(true)}
                  icon={<TrendingUp className="h-4 w-4" />}
                >
                  Аналитика
                </EnhancedButton>
                
                <EnhancedButton
                  variant="module"
                  module="marketing"
                  onClick={() => setShowCreateModal(true)}
                  icon={<Plus className="h-4 w-4" />}
                >
                  Создать промокод
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
                    <AlertTriangle className="h-5 w-5 text-red-500 mr-3" />
                    <div>
                      <h3 className="text-sm font-medium text-red-800 dark:text-red-300">Ошибка</h3>
                      <p className="text-sm text-red-700 dark:text-red-400 mt-1">{error}</p>
                    </div>
                    <button 
                      onClick={() => setError('')}
                      className="ml-auto text-red-500 hover:text-red-700"
                    >
                      <XCircle className="h-4 w-4" />
                    </button>
                  </div>
                </ModuleCard>
              </motion.div>
            )}
          </AnimatePresence>

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
                  <p className="text-sm text-gray-600 dark:text-gray-400">Всего промокодов</p>
                  <p className="text-2xl font-bold text-orange-600">
                    {promoStats.totalCodes || 0}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {promoStats.activeCodes || 0} активных
                  </p>
                </div>
                <div className="p-3 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
                  <Tag className="h-6 w-6 text-orange-600" />
                </div>
              </div>
            </ModuleCard>

            <ModuleCard module="marketing" variant="module">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Использований</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {promoStats.totalUsage?.toLocaleString() || 0}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    За последние 30 дней
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
                  <p className="text-sm text-gray-600 dark:text-gray-400">Скидка дана</p>
                  <p className="text-2xl font-bold text-green-600">
                    ${promoStats.totalDiscount?.toLocaleString() || 0}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Общая сумма скидок
                  </p>
                </div>
                <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                  <DollarSign className="h-6 w-6 text-green-600" />
                </div>
              </div>
            </ModuleCard>

            <ModuleCard module="marketing" variant="module">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Конверсия</p>
                  <p className="text-2xl font-bold text-purple-600">
                    {promoStats.conversionRate?.toFixed(1) || 0}%
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Использование промокодов
                  </p>
                </div>
                <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                  <Target className="h-6 w-6 text-purple-600" />
                </div>
              </div>
            </ModuleCard>
          </motion.div>

          {/* Filters */}
          <motion.div
            className="mb-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <ModuleCard module="marketing" variant="module">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div className="flex flex-col md:flex-row gap-4 flex-1">
                  {/* Search */}
                  <div className="relative flex-1 max-w-md">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Поиск промокодов..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 pr-4 py-2 w-full border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    />
                  </div>

                  {/* Status Filter */}
                  <select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-orange-500"
                  >
                    <option value="all">Все статусы</option>
                    <option value="active">Активные</option>
                    <option value="inactive">Неактивные</option>
                  </select>

                  {/* Type Filter */}
                  <select
                    value={filterType}
                    onChange={(e) => setFilterType(e.target.value)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-orange-500"
                  >
                    <option value="all">Все типы</option>
                    <option value="percentage">Процент</option>
                    <option value="fixed_amount">Фиксированная сумма</option>
                    <option value="free_trial">Бесплатный период</option>
                  </select>
                </div>

                <div className="flex gap-2">
                  <EnhancedButton
                    variant="module-outline"
                    module="marketing"
                    size="sm"
                    onClick={loadPromoData}
                    icon={<RefreshCw className="h-4 w-4" />}
                  >
                    Обновить
                  </EnhancedButton>
                </div>
              </div>
            </ModuleCard>
          </motion.div>

          {/* Promo Codes List */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <ModuleCard module="marketing" variant="module">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-800">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Промокод
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Тип и значение
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Использование
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Период действия
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Статус
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                        Действия
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                    {filteredPromoCodes.map((promo, index) => {
                      const TypeIcon = getPromoTypeIcon(promo.type);
                      const statusColor = getStatusColor(promo);
                      
                      return (
                        <motion.tr 
                          key={promo.id}
                          className="hover:bg-gray-50 dark:hover:bg-gray-800"
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ duration: 0.2, delay: index * 0.05 }}
                        >
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <div 
                                className="p-2 rounded-lg mr-3"
                                style={{ 
                                  backgroundColor: `${getModuleColor('marketing')}20`,
                                  border: `1px solid ${getModuleColor('marketing')}40`
                                }}
                              >
                                <TypeIcon 
                                  className="h-4 w-4" 
                                  style={{ color: getModuleColor('marketing') }}
                                />
                              </div>
                              <div>
                                <div className="flex items-center">
                                  <span className="text-sm font-medium text-gray-900 dark:text-gray-100 font-mono">
                                    {promo.code}
                                  </span>
                                  <button
                                    onClick={() => copyToClipboard(promo.code)}
                                    className="ml-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                                  >
                                    <Copy className="h-3 w-3" />
                                  </button>
                                </div>
                                <div className="text-sm text-gray-500 dark:text-gray-400">
                                  {promo.name}
                                </div>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900 dark:text-gray-100">
                              {getPromoTypeLabel(promo.type)}
                            </div>
                            <div className="text-sm font-medium text-orange-600">
                              {promo.type === 'percentage' && `${promo.value}%`}
                              {promo.type === 'fixed_amount' && `${promo.currency} ${promo.value}`}
                              {promo.type === 'free_trial' && `${promo.value} дней`}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900 dark:text-gray-100">
                              {promo.usageCount} / {promo.usageLimit || '∞'}
                            </div>
                            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mt-1">
                              <div 
                                className="h-2 rounded-full transition-all duration-300"
                                style={{ 
                                  width: promo.usageLimit 
                                    ? `${Math.min((promo.usageCount / promo.usageLimit) * 100, 100)}%`
                                    : '0%',
                                  backgroundColor: getModuleColor('marketing')
                                }}
                              />
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                            <div className="flex items-center">
                              <Calendar className="h-4 w-4 mr-1" />
                              <div>
                                <div>{new Date(promo.validFrom).toLocaleDateString()}</div>
                                <div>{new Date(promo.validTo).toLocaleDateString()}</div>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColor}`}>
                              {getStatusLabel(promo)}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            <div className="flex items-center space-x-2">
                              <button
                                onClick={() => openEditModal(promo)}
                                className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
                                title="Редактировать"
                              >
                                <Edit className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() => togglePromoStatus(promo.id, promo.isActive)}
                                className={`${promo.isActive ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'} hover:opacity-75`}
                                title={promo.isActive ? 'Деактивировать' : 'Активировать'}
                              >
                                {promo.isActive ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                              </button>
                              <button
                                onClick={() => deletePromoCode(promo.id)}
                                className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300"
                                title="Удалить"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            </div>
                          </td>
                        </motion.tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </ModuleCard>
          </motion.div>
        </div>
      </div>
    </ModuleErrorBoundary>
  );
};

export default PromoCodeManager;