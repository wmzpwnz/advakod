import React, { useState, useEffect } from 'react';
import { 
  ShieldCheckIcon as FiShield, 
  CheckIcon as FiCheck, 
  XMarkIcon as FiX, 
  ExclamationTriangleIcon as FiAlertTriangle, 
  ArrowPathIcon as FiRefreshCw,
  ClockIcon as FiClock, 
  CircleStackIcon as FiDatabase, 
  DocumentTextIcon as FiFileText, 
  ChartBarIcon as FiActivity
} from '@heroicons/react/24/outline';
import { motion } from 'framer-motion';
import { toast } from 'react-hot-toast';
import GlassCard from './GlassCard';
import LoadingSpinner from './LoadingSpinner';
import ModernButton from './ModernButton';

const BackupIntegrityMonitor = ({ backupId, onClose }) => {
  const [checks, setChecks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [runningCheck, setRunningCheck] = useState(false);

  useEffect(() => {
    if (backupId) {
      loadIntegrityChecks();
    }
  }, [backupId]);

  const loadIntegrityChecks = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/admin/backups/${backupId}/integrity`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to load integrity checks');
      }
      
      const data = await response.json();
      setChecks(data.checks || []);
    } catch (error) {
      console.error('Error loading integrity checks:', error);
      toast.error('Failed to load integrity checks');
    } finally {
      setLoading(false);
    }
  };

  const runIntegrityCheck = async () => {
    setRunningCheck(true);
    try {
      const response = await fetch(`/api/v1/admin/backups/${backupId}/integrity/run`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to run integrity check');
      }
      
      await loadIntegrityChecks();
      toast.success('Integrity check completed');
    } catch (error) {
      console.error('Error running integrity check:', error);
      toast.error('Failed to run integrity check');
    } finally {
      setRunningCheck(false);
    }
  };

  const getCheckStatusIcon = (status) => {
    switch (status) {
      case 'passed':
        return <FiCheck className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <FiX className="h-5 w-5 text-red-500" />;
      case 'warning':
        return <FiAlertTriangle className="h-5 w-5 text-yellow-500" />;
      default:
        return <FiClock className="h-5 w-5 text-gray-500" />;
    }
  };

  const getCheckStatusColor = (status) => {
    switch (status) {
      case 'passed':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      case 'failed':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400';
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto"
      >
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <FiShield className="h-6 w-6 text-blue-500" />
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              Backup Integrity Monitor
            </h2>
          </div>
          <div className="flex items-center space-x-3">
            <ModernButton
              onClick={runIntegrityCheck}
              disabled={runningCheck || loading}
              variant="primary"
              size="sm"
              icon={FiRefreshCw}
            >
              Run Check
            </ModernButton>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <FiX className="h-6 w-6" />
            </button>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-8">
            <LoadingSpinner />
          </div>
        ) : (
          <GlassCard>
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Integrity Check Results
              </h3>
              
              {checks.length === 0 ? (
                <div className="text-center py-8">
                  <FiDatabase className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
                    No integrity checks found
                  </h3>
                  <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    Run an integrity check to see results.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {checks.map((check, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg"
                    >
                      <div className="flex items-center space-x-3">
                        {getCheckStatusIcon(check.status)}
                        <div>
                          <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                            {check.name}
                          </h4>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            {check.description}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-3">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getCheckStatusColor(check.status)}`}>
                          {check.status}
                        </span>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          <FiClock className="inline h-4 w-4 mr-1" />
                          {new Date(check.timestamp).toLocaleString()}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </GlassCard>
        )}
      </motion.div>
    </div>
  );
};

export default BackupIntegrityMonitor;