import React, { useState, useEffect } from 'react';
import { 
  ArrowUpTrayIcon as FiUpload, 
  EyeIcon as FiEye, 
  CheckIcon as FiCheck, 
  XMarkIcon as FiX, 
  ExclamationTriangleIcon as FiAlertTriangle, 
  ArrowPathIcon as FiRefreshCw,
  CircleStackIcon as FiDatabase, 
  ServerIcon as FiHardDrive, 
  CogIcon as FiSettings, 
  ClockIcon as FiClock, 
  ShieldCheckIcon as FiShield
} from '@heroicons/react/24/outline';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';
import GlassCard from './GlassCard';
import LoadingSpinner from './LoadingSpinner';
import ModernButton from './ModernButton';

const RestoreManager = () => {
  const [backups, setBackups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedBackup, setSelectedBackup] = useState(null);
  const [restoreProgress, setRestoreProgress] = useState(0);
  const [isRestoring, setIsRestoring] = useState(false);

  useEffect(() => {
    loadBackups();
  }, []);

  const loadBackups = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/admin/backups', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to load backups');
      }
      
      const data = await response.json();
      setBackups(data.backups || []);
    } catch (error) {
      console.error('Error loading backups:', error);
      toast.error('Failed to load backups');
    } finally {
      setLoading(false);
    }
  };

  const handleRestore = async (backup) => {
    if (!backup) return;
    
    setIsRestoring(true);
    setRestoreProgress(0);
    
    try {
      const response = await fetch(`/api/v1/admin/restore/${backup.id}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to start restore');
      }
      
      // Simulate progress
      const progressInterval = setInterval(() => {
        setRestoreProgress(prev => {
          if (prev >= 100) {
            clearInterval(progressInterval);
            return 100;
          }
          return prev + 10;
        });
      }, 500);
      
      toast.success('Restore completed successfully');
    } catch (error) {
      console.error('Error during restore:', error);
      toast.error('Failed to restore backup');
    } finally {
      setIsRestoring(false);
      setRestoreProgress(0);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getBackupTypeIcon = (type) => {
    switch (type) {
      case 'full':
        return <FiDatabase className="h-5 w-5" />;
      case 'incremental':
        return <FiHardDrive className="h-5 w-5" />;
      case 'config':
        return <FiSettings className="h-5 w-5" />;
      default:
        return <FiShield className="h-5 w-5" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Restore Manager
        </h2>
        <ModernButton
          onClick={loadBackups}
          disabled={loading}
          variant="secondary"
          icon={FiRefreshCw}
        >
          Refresh
        </ModernButton>
      </div>

      {loading ? (
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      ) : (
        <GlassCard>
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Available Backups
            </h3>
            
            {backups.length === 0 ? (
              <div className="text-center py-8">
                <FiDatabase className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
                  No backups found
                </h3>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  No backup files are available for restore.
                </p>
              </div>
            ) : (
              <div className="grid gap-4">
                {backups.map((backup) => (
                  <motion.div
                    key={backup.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="flex-shrink-0">
                          {getBackupTypeIcon(backup.type)}
                        </div>
                        <div>
                          <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                            {backup.name}
                          </h4>
                          <div className="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
                            <span className="flex items-center">
                              <FiClock className="h-4 w-4 mr-1" />
                              {new Date(backup.created_at).toLocaleString()}
                            </span>
                            <span>{formatFileSize(backup.size)}</span>
                            <span className="capitalize">{backup.type}</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        <ModernButton
                          onClick={() => setSelectedBackup(backup)}
                          variant="secondary"
                          size="sm"
                          icon={FiEye}
                        >
                          View
                        </ModernButton>
                        <ModernButton
                          onClick={() => handleRestore(backup)}
                          disabled={isRestoring}
                          variant="primary"
                          size="sm"
                          icon={FiUpload}
                        >
                          Restore
                        </ModernButton>
                      </div>
                    </div>
                    
                    {backup.description && (
                      <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
                        {backup.description}
                      </p>
                    )}
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </GlassCard>
      )}

      {/* Restore Progress Modal */}
      <AnimatePresence>
        {isRestoring && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4"
            >
              <div className="text-center">
                <FiRefreshCw className="mx-auto h-12 w-12 text-blue-500 animate-spin" />
                <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">
                  Restoring Backup
                </h3>
                <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                  Please wait while we restore your data...
                </p>
                
                <div className="mt-4">
                  <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${restoreProgress}%` }}
                    ></div>
                  </div>
                  <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                    {restoreProgress}% complete
                  </p>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Backup Details Modal */}
      <AnimatePresence>
        {selectedBackup && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
            onClick={() => setSelectedBackup(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Backup Details
                </h3>
                <button
                  onClick={() => setSelectedBackup(null)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <FiX className="h-6 w-6" />
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Name
                  </label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white">
                    {selectedBackup.name}
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Type
                  </label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white capitalize">
                    {selectedBackup.type}
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Size
                  </label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white">
                    {formatFileSize(selectedBackup.size)}
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Created
                  </label>
                  <p className="mt-1 text-sm text-gray-900 dark:text-white">
                    {new Date(selectedBackup.created_at).toLocaleString()}
                  </p>
                </div>
                
                {selectedBackup.description && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      Description
                    </label>
                    <p className="mt-1 text-sm text-gray-900 dark:text-white">
                      {selectedBackup.description}
                    </p>
                  </div>
                )}
              </div>
              
              <div className="mt-6 flex justify-end space-x-3">
                <ModernButton
                  onClick={() => setSelectedBackup(null)}
                  variant="secondary"
                >
                  Close
                </ModernButton>
                <ModernButton
                  onClick={() => {
                    handleRestore(selectedBackup);
                    setSelectedBackup(null);
                  }}
                  variant="primary"
                  icon={FiUpload}
                >
                  Restore This Backup
                </ModernButton>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default RestoreManager;