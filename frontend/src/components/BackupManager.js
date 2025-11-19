import React, { useState, useEffect } from 'react';
import { 
  CircleStackIcon as FiDatabase, 
  ArrowDownTrayIcon as FiDownload, 
  ArrowUpTrayIcon as FiUpload, 
  ClockIcon as FiClock, 
  CogIcon as FiSettings,
  PlayIcon as FiPlay, 
  PauseIcon as FiPause, 
  TrashIcon as FiTrash2, 
  CheckIcon as FiCheck, 
  XMarkIcon as FiX, 
  ExclamationTriangleIcon as FiAlertTriangle,
  ArrowPathIcon as FiRefreshCw, 
  CalendarIcon as FiCalendar, 
  ServerIcon as FiHardDrive, 
  ShieldCheckIcon as FiShield
} from '@heroicons/react/24/outline';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';
import GlassCard from './GlassCard';
import LoadingSpinner from './LoadingSpinner';
import ModernButton from './ModernButton';

const BackupManager = () => {
  const [backups, setBackups] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [stats, setStats] = useState(null);
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedBackup, setSelectedBackup] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [showRestoreModal, setShowRestoreModal] = useState(false);
  const [activeTab, setActiveTab] = useState('backups');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [backupsRes, schedulesRes, statsRes, statusRes] = await Promise.all([
        fetch('/api/v1/backup/list'),
        fetch('/api/v1/backup/schedules'),
        fetch('/api/v1/backup/stats'),
        fetch('/api/v1/backup/status')
      ]);

      if (backupsRes.ok) {
        const backupsData = await backupsRes.json();
        setBackups(backupsData.backups || []);
      }

      if (schedulesRes.ok) {
        const schedulesData = await schedulesRes.json();
        setSchedules(schedulesData);
      }

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }

      if (statusRes.ok) {
        const statusData = await statusRes.json();
        setSystemStatus(statusData);
      }
    } catch (error) {
      console.error('Ошибка загрузки данных:', error);
      toast.error('Ошибка загрузки данных резервного копирования');
    } finally {
      setLoading(false);
    }
  };

  const createBackup = async (backupData) => {
    try {
      const response = await fetch('/api/v1/backup/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(backupData),
      });

      if (response.ok) {
        const result = await response.json();
        toast.success('Резервная копия создается...');
        setShowCreateModal(false);
        loadData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Ошибка создания резервной копии');
      }
    } catch (error) {
      console.error('Ошибка создания резервной копии:', error);
      toast.error('Ошибка создания резервной копии');
    }
  };

  const deleteBackup = async (backupId) => {
    if (!window.confirm('Вы уверены, что хотите удалить эту резервную копию?')) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/backup/${backupId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        toast.success('Резервная копия удалена');
        loadData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Ошибка удаления резервной копии');
      }
    } catch (error) {
      console.error('Ошибка удаления резервной копии:', error);
      toast.error('Ошибка удаления резервной копии');
    }
  };

  const restoreBackup = async (backupId, restoreData) => {
    try {
      const response = await fetch(`/api/v1/backup/${backupId}/restore`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(restoreData),
      });

      if (response.ok) {
        const result = await response.json();
        toast.success('Восстановление запущено...');
        setShowRestoreModal(false);
        loadData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Ошибка восстановления');
      }
    } catch (error) {
      console.error('Ошибка восстановления:', error);
      toast.error('Ошибка восстановления');
    }
  };

  const checkIntegrity = async (backupId) => {
    try {
      const response = await fetch(`/api/v1/backup/${backupId}/check-integrity`, {
        method: 'POST',
      });

      if (response.ok) {
        toast.success('Проверка целостности запущена');
        loadData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Ошибка проверки целостности');
      }
    } catch (error) {
      console.error('Ошибка проверки целостности:', error);
      toast.error('Ошибка проверки целостности');
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
    
    if (hours > 0) return `${hours}h ${minutes}m ${secs}s`;
    if (minutes > 0) return `${minutes}m ${secs}s`;
    return `${secs}s`;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-400';
      case 'failed': return 'text-red-400';
      case 'in_progress': return 'text-blue-400';
      case 'pending': return 'text-yellow-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <FiCheck className="w-4 h-4" />;
      case 'failed': return <FiX className="w-4 h-4" />;
      case 'in_progress': return <FiRefreshCw className="w-4 h-4 animate-spin" />;
      case 'pending': return <FiClock className="w-4 h-4" />;
      default: return <FiAlertTriangle className="w-4 h-4" />;
    }
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
      {/* Заголовок и статистика */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">
            Система резервного копирования
          </h1>
          <p className="text-gray-400">
            Управление резервными копиями и восстановлением данных
          </p>
        </div>
        <div className="flex space-x-3">
          <ModernButton
            onClick={() => setShowCreateModal(true)}
            className="bg-blue-600 hover:bg-blue-700"
          >
            <FiDatabase className="w-4 h-4 mr-2" />
            Создать резервную копию
          </ModernButton>
          <ModernButton
            onClick={() => setShowScheduleModal(true)}
            className="bg-purple-600 hover:bg-purple-700"
          >
            <FiCalendar className="w-4 h-4 mr-2" />
            Настроить расписание
          </ModernButton>
        </div>
      </div>

      {/* Статистика системы */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <GlassCard className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Всего резервных копий</p>
                <p className="text-2xl font-bold text-white">{stats.total_backups}</p>
              </div>
              <FiDatabase className="w-8 h-8 text-blue-400" />
            </div>
          </GlassCard>

          <GlassCard className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Успешных</p>
                <p className="text-2xl font-bold text-green-400">{stats.successful_backups}</p>
              </div>
              <FiCheck className="w-8 h-8 text-green-400" />
            </div>
          </GlassCard>

          <GlassCard className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Общий размер</p>
                <p className="text-2xl font-bold text-white">{formatSize(stats.total_size)}</p>
              </div>
              <FiHardDrive className="w-8 h-8 text-purple-400" />
            </div>
          </GlassCard>

          <GlassCard className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Активных расписаний</p>
                <p className="text-2xl font-bold text-white">{stats.active_schedules}</p>
              </div>
              <FiCalendar className="w-8 h-8 text-orange-400" />
            </div>
          </GlassCard>
        </div>
      )}

      {/* Статус системы */}
      {systemStatus && (
        <GlassCard className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Статус системы</h3>
            <div className={`flex items-center space-x-2 ${
              systemStatus.status === 'healthy' ? 'text-green-400' :
              systemStatus.status === 'warning' ? 'text-yellow-400' : 'text-red-400'
            }`}>
              <FiShield className="w-5 h-5" />
              <span className="capitalize">{systemStatus.status}</span>
            </div>
          </div>

          {systemStatus.warnings.length > 0 && (
            <div className="mb-4">
              <h4 className="text-sm font-medium text-yellow-400 mb-2">Предупреждения:</h4>
              <ul className="space-y-1">
                {systemStatus.warnings.map((warning, index) => (
                  <li key={index} className="text-sm text-yellow-300 flex items-center">
                    <FiAlertTriangle className="w-4 h-4 mr-2" />
                    {warning}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {systemStatus.recommendations.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-blue-400 mb-2">Рекомендации:</h4>
              <ul className="space-y-1">
                {systemStatus.recommendations.map((recommendation, index) => (
                  <li key={index} className="text-sm text-blue-300 flex items-center">
                    <FiSettings className="w-4 h-4 mr-2" />
                    {recommendation}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </GlassCard>
      )}

      {/* Вкладки */}
      <div className="flex space-x-1 bg-gray-800/50 rounded-lg p-1">
        <button
          onClick={() => setActiveTab('backups')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'backups'
              ? 'bg-blue-600 text-white'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          Резервные копии
        </button>
        <button
          onClick={() => setActiveTab('schedules')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'schedules'
              ? 'bg-blue-600 text-white'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          Расписания
        </button>
      </div>

      {/* Содержимое вкладок */}
      <AnimatePresence mode="wait">
        {activeTab === 'backups' && (
          <motion.div
            key="backups"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
          >
            <BackupsList 
              backups={backups}
              onDelete={deleteBackup}
              onRestore={(backup) => {
                setSelectedBackup(backup);
                setShowRestoreModal(true);
              }}
              onCheckIntegrity={checkIntegrity}
              formatSize={formatSize}
              formatDuration={formatDuration}
              getStatusColor={getStatusColor}
              getStatusIcon={getStatusIcon}
            />
          </motion.div>
        )}

        {activeTab === 'schedules' && (
          <motion.div
            key="schedules"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
          >
            <SchedulesList 
              schedules={schedules}
              onRefresh={loadData}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Модальные окна */}
      {showCreateModal && (
        <CreateBackupModal
          onClose={() => setShowCreateModal(false)}
          onCreate={createBackup}
        />
      )}

      {showScheduleModal && (
        <CreateScheduleModal
          onClose={() => setShowScheduleModal(false)}
          onRefresh={loadData}
        />
      )}

      {showRestoreModal && selectedBackup && (
        <RestoreBackupModal
          backup={selectedBackup}
          onClose={() => {
            setShowRestoreModal(false);
            setSelectedBackup(null);
          }}
          onRestore={restoreBackup}
        />
      )}
    </div>
  );
};

// Компонент списка резервных копий
const BackupsList = ({ 
  backups, 
  onDelete, 
  onRestore, 
  onCheckIntegrity,
  formatSize,
  formatDuration,
  getStatusColor,
  getStatusIcon
}) => {
  return (
    <div className="space-y-4">
      {backups.length === 0 ? (
        <GlassCard className="p-8 text-center">
          <FiDatabase className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-400">Резервные копии не найдены</p>
        </GlassCard>
      ) : (
        backups.map((backup) => (
          <GlassCard key={backup.id} className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h3 className="text-lg font-semibold text-white">{backup.name}</h3>
                  <div className={`flex items-center space-x-1 ${getStatusColor(backup.status)}`}>
                    {getStatusIcon(backup.status)}
                    <span className="text-sm capitalize">{backup.status}</span>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-400">
                  <div>
                    <span className="block text-gray-500">Размер:</span>
                    <span className="text-white">{formatSize(backup.total_size)}</span>
                  </div>
                  <div>
                    <span className="block text-gray-500">Длительность:</span>
                    <span className="text-white">{formatDuration(backup.duration_seconds)}</span>
                  </div>
                  <div>
                    <span className="block text-gray-500">Создано:</span>
                    <span className="text-white">
                      {new Date(backup.created_at).toLocaleDateString('ru-RU')}
                    </span>
                  </div>
                  <div>
                    <span className="block text-gray-500">Тип:</span>
                    <span className="text-white capitalize">{backup.backup_type}</span>
                  </div>
                </div>

                {backup.description && (
                  <p className="text-gray-400 text-sm mt-2">{backup.description}</p>
                )}

                {backup.tags && backup.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {backup.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-blue-600/20 text-blue-400 text-xs rounded"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex items-center space-x-2 ml-4">
                {backup.status === 'completed' && (
                  <>
                    <ModernButton
                      onClick={() => onRestore(backup)}
                      className="bg-green-600 hover:bg-green-700 text-sm px-3 py-1"
                    >
                      <FiUpload className="w-4 h-4 mr-1" />
                      Восстановить
                    </ModernButton>
                    <ModernButton
                      onClick={() => onCheckIntegrity(backup.id)}
                      className="bg-purple-600 hover:bg-purple-700 text-sm px-3 py-1"
                    >
                      <FiShield className="w-4 h-4 mr-1" />
                      Проверить
                    </ModernButton>
                  </>
                )}
                <ModernButton
                  onClick={() => onDelete(backup.id)}
                  className="bg-red-600 hover:bg-red-700 text-sm px-3 py-1"
                >
                  <FiTrash2 className="w-4 h-4" />
                </ModernButton>
              </div>
            </div>
          </GlassCard>
        ))
      )}
    </div>
  );
};

// Компонент списка расписаний
const SchedulesList = ({ schedules, onRefresh }) => {
  const toggleSchedule = async (scheduleId, enabled) => {
    try {
      const response = await fetch(`/api/v1/backup/schedules/${scheduleId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ enabled: !enabled }),
      });

      if (response.ok) {
        toast.success(`Расписание ${!enabled ? 'включено' : 'отключено'}`);
        onRefresh();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Ошибка обновления расписания');
      }
    } catch (error) {
      console.error('Ошибка обновления расписания:', error);
      toast.error('Ошибка обновления расписания');
    }
  };

  return (
    <div className="space-y-4">
      {schedules.length === 0 ? (
        <GlassCard className="p-8 text-center">
          <FiCalendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-400">Расписания не настроены</p>
        </GlassCard>
      ) : (
        schedules.map((schedule) => (
          <GlassCard key={schedule.id} className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h3 className="text-lg font-semibold text-white">{schedule.name}</h3>
                  <div className={`flex items-center space-x-1 ${
                    schedule.enabled ? 'text-green-400' : 'text-gray-400'
                  }`}>
                    {schedule.enabled ? <FiPlay className="w-4 h-4" /> : <FiPause className="w-4 h-4" />}
                    <span className="text-sm">{schedule.enabled ? 'Активно' : 'Отключено'}</span>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm text-gray-400">
                  <div>
                    <span className="block text-gray-500">Расписание:</span>
                    <span className="text-white font-mono">{schedule.cron_expression}</span>
                  </div>
                  <div>
                    <span className="block text-gray-500">Следующий запуск:</span>
                    <span className="text-white">
                      {schedule.next_run_at 
                        ? new Date(schedule.next_run_at).toLocaleString('ru-RU')
                        : 'Не запланировано'
                      }
                    </span>
                  </div>
                  <div>
                    <span className="block text-gray-500">Успешных запусков:</span>
                    <span className="text-white">{schedule.successful_runs}/{schedule.total_runs}</span>
                  </div>
                </div>

                {schedule.description && (
                  <p className="text-gray-400 text-sm mt-2">{schedule.description}</p>
                )}
              </div>

              <div className="flex items-center space-x-2 ml-4">
                <ModernButton
                  onClick={() => toggleSchedule(schedule.id, schedule.enabled)}
                  className={`text-sm px-3 py-1 ${
                    schedule.enabled 
                      ? 'bg-yellow-600 hover:bg-yellow-700' 
                      : 'bg-green-600 hover:bg-green-700'
                  }`}
                >
                  {schedule.enabled ? <FiPause className="w-4 h-4" /> : <FiPlay className="w-4 h-4" />}
                </ModernButton>
              </div>
            </div>
          </GlassCard>
        ))
      )}
    </div>
  );
};

// Заглушки для модальных окон (будут реализованы в следующих компонентах)
const CreateBackupModal = ({ onClose, onCreate }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    components: ['main_db', 'vector_db'],
    tags: [],
    compression_enabled: true,
    encryption_enabled: false,
    retention_days: 30
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onCreate(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <GlassCard className="p-6 w-full max-w-md">
        <h2 className="text-xl font-bold text-white mb-4">Создать резервную копию</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Название
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Описание
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white"
              rows="3"
            />
          </div>

          <div className="flex items-center space-x-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.compression_enabled}
                onChange={(e) => setFormData({ ...formData, compression_enabled: e.target.checked })}
                className="mr-2"
              />
              <span className="text-sm text-gray-300">Сжатие</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.encryption_enabled}
                onChange={(e) => setFormData({ ...formData, encryption_enabled: e.target.checked })}
                className="mr-2"
              />
              <span className="text-sm text-gray-300">Шифрование</span>
            </label>
          </div>

          <div className="flex justify-end space-x-3">
            <ModernButton
              type="button"
              onClick={onClose}
              className="bg-gray-600 hover:bg-gray-700"
            >
              Отмена
            </ModernButton>
            <ModernButton
              type="submit"
              className="bg-blue-600 hover:bg-blue-700"
            >
              Создать
            </ModernButton>
          </div>
        </form>
      </GlassCard>
    </div>
  );
};

const CreateScheduleModal = ({ onClose, onRefresh }) => {
  // Заглушка для модального окна создания расписания
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <GlassCard className="p-6 w-full max-w-md">
        <h2 className="text-xl font-bold text-white mb-4">Создать расписание</h2>
        <p className="text-gray-400 mb-4">Функция будет реализована в следующей версии</p>
        <div className="flex justify-end">
          <ModernButton onClick={onClose} className="bg-gray-600 hover:bg-gray-700">
            Закрыть
          </ModernButton>
        </div>
      </GlassCard>
    </div>
  );
};

const RestoreBackupModal = ({ backup, onClose, onRestore }) => {
  const [formData, setFormData] = useState({
    name: `Восстановление ${backup.name}`,
    description: '',
    components_to_restore: ['main_db'],
    restore_options: {}
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onRestore(backup.id, formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <GlassCard className="p-6 w-full max-w-md">
        <h2 className="text-xl font-bold text-white mb-4">Восстановить данные</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Название операции
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Описание
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white"
              rows="3"
            />
          </div>

          <div className="bg-yellow-600/20 border border-yellow-600/30 rounded-md p-3">
            <div className="flex items-center">
              <FiAlertTriangle className="w-5 h-5 text-yellow-400 mr-2" />
              <span className="text-yellow-400 font-medium">Внимание!</span>
            </div>
            <p className="text-yellow-300 text-sm mt-1">
              Восстановление заменит текущие данные. Убедитесь, что у вас есть актуальная резервная копия.
            </p>
          </div>

          <div className="flex justify-end space-x-3">
            <ModernButton
              type="button"
              onClick={onClose}
              className="bg-gray-600 hover:bg-gray-700"
            >
              Отмена
            </ModernButton>
            <ModernButton
              type="submit"
              className="bg-red-600 hover:bg-red-700"
            >
              Восстановить
            </ModernButton>
          </div>
        </form>
      </GlassCard>
    </div>
  );
};

export default BackupManager;