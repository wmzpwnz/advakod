/**
 * Enhanced Lazy Loading Components for Admin Panel
 * Implements code splitting with performance monitoring
 */

import React, { lazy, Suspense } from 'react';
import LoadingSpinner from './LoadingSpinner';
import ErrorBoundary from './ErrorBoundary';

// Performance monitoring for code splitting
const recordCodeSplittingLoad = (chunkName, loadTime) => {
  if (window.adminPanelMetrics) {
    window.adminPanelMetrics.recordCodeSplittingLoad(chunkName, loadTime);
  }
};

// Enhanced lazy loading with performance monitoring
const createLazyComponent = (importFunc, chunkName, fallback = null) => {
  const LazyComponent = lazy(() => {
    const startTime = performance.now();
    
    return importFunc().then(module => {
      const loadTime = (performance.now() - startTime) / 1000;
      recordCodeSplittingLoad(chunkName, loadTime);
      return module;
    });
  });

  return React.forwardRef((props, ref) => (
    <ErrorBoundary>
      <Suspense fallback={fallback || <LoadingSpinner message={`Loading ${chunkName}...`} />}>
        <LazyComponent {...props} ref={ref} />
      </Suspense>
    </ErrorBoundary>
  ));
};

// Admin Panel Core Components
export const LazyAdminDashboard = createLazyComponent(
  () => import('../pages/AdminDashboard'),
  'admin-dashboard'
);

export const LazyIntegratedAdminPanel = createLazyComponent(
  () => import('../pages/IntegratedAdminPanel'),
  'integrated-admin-panel'
);

// User Management Components
export const LazyUserManagement = createLazyComponent(
  () => import('../pages/UserManagement'),
  'user-management'
);

export const LazyUserProfile = createLazyComponent(
  () => import('../components/admin/UserProfile'),
  'user-profile'
);

export const LazyUserAnalytics = createLazyComponent(
  () => import('../components/admin/UserAnalytics'),
  'user-analytics'
);

// RBAC Components
export const LazyRoleManagement = createLazyComponent(
  () => import('../pages/RoleManagement'),
  'role-management'
);

export const LazyPermissionMatrix = createLazyComponent(
  () => import('../components/admin/PermissionMatrix'),
  'permission-matrix'
);

export const LazyRoleHistory = createLazyComponent(
  () => import('../components/admin/RoleHistory'),
  'role-history'
);

// Moderation Components
export const LazyModerationPanel = createLazyComponent(
  () => import('../pages/ModerationPanel'),
  'moderation-panel'
);

export const LazyModerationDashboard = createLazyComponent(
  () => import('../pages/ModerationDashboard'),
  'moderation-dashboard'
);

export const LazyModerationQueue = createLazyComponent(
  () => import('../components/moderation/ModerationQueue'),
  'moderation-queue'
);

export const LazyModeratorLeaderboard = createLazyComponent(
  () => import('../components/moderation/ModeratorLeaderboard'),
  'moderator-leaderboard'
);

// Marketing Components
export const LazyMarketingDashboard = createLazyComponent(
  () => import('../components/admin/MarketingDashboard'),
  'marketing-dashboard'
);

export const LazySalesFunnel = createLazyComponent(
  () => import('../components/admin/SalesFunnel'),
  'sales-funnel'
);

export const LazyPromoCodeManager = createLazyComponent(
  () => import('../components/admin/PromoCodeManager'),
  'promo-code-manager'
);

export const LazyTrafficAnalytics = createLazyComponent(
  () => import('../components/admin/TrafficAnalytics'),
  'traffic-analytics'
);

export const LazyABTestManager = createLazyComponent(
  () => import('../components/admin/ABTestManager'),
  'ab-test-manager'
);

// Project Management Components
export const LazyProjectDashboard = createLazyComponent(
  () => import('../components/admin/ProjectDashboard'),
  'project-dashboard'
);

export const LazyTaskManager = createLazyComponent(
  () => import('../components/admin/TaskManager'),
  'task-manager'
);

export const LazyResourceTracker = createLazyComponent(
  () => import('../components/admin/ResourceTracker'),
  'resource-tracker'
);

export const LazyProjectCalendar = createLazyComponent(
  () => import('../components/admin/ProjectCalendar'),
  'project-calendar'
);

// Notification Components
export const LazyNotificationCenter = createLazyComponent(
  () => import('../components/admin/NotificationCenter'),
  'notification-center'
);

export const LazyNotificationSettings = createLazyComponent(
  () => import('../components/admin/NotificationSettings'),
  'notification-settings'
);

export const LazyNotificationTemplates = createLazyComponent(
  () => import('../components/admin/NotificationTemplates'),
  'notification-templates'
);

// Analytics Components
export const LazyAdvancedAnalytics = createLazyComponent(
  () => import('../components/admin/AdvancedAnalytics'),
  'advanced-analytics'
);

export const LazyDashboardBuilder = createLazyComponent(
  () => import('../components/admin/DashboardBuilder'),
  'dashboard-builder'
);

export const LazyCohortAnalysis = createLazyComponent(
  () => import('../components/admin/CohortAnalysis'),
  'cohort-analysis'
);

export const LazyMetricsBuilder = createLazyComponent(
  () => import('../components/admin/MetricsBuilder'),
  'metrics-builder'
);

// Backup Components
export const LazyBackupManager = createLazyComponent(
  () => import('../components/admin/BackupManager'),
  'backup-manager'
);

export const LazyRestoreManager = createLazyComponent(
  () => import('../components/admin/RestoreManager'),
  'restore-manager'
);

// Settings Components
export const LazySettingsPanel = createLazyComponent(
  () => import('../components/admin/SettingsPanel'),
  'settings-panel'
);

export const LazySystemSettings = createLazyComponent(
  () => import('../components/admin/SystemSettings'),
  'system-settings'
);

// Heavy Chart Components
export const LazyChartComponents = createLazyComponent(
  () => import('../components/charts/ChartComponents'),
  'chart-components'
);

export const LazyDataVisualization = createLazyComponent(
  () => import('../components/charts/DataVisualization'),
  'data-visualization'
);

// Utility function to preload critical components
export const preloadCriticalComponents = () => {
  const criticalComponents = [
    'admin-dashboard',
    'integrated-admin-panel',
    'notification-center'
  ];

  criticalComponents.forEach(chunkName => {
    // Preload during idle time
    if ('requestIdleCallback' in window) {
      requestIdleCallback(() => {
        switch (chunkName) {
          case 'admin-dashboard':
            import('../pages/AdminDashboard');
            break;
          case 'integrated-admin-panel':
            import('../pages/IntegratedAdminPanel');
            break;
          case 'notification-center':
            import('../components/admin/NotificationCenter');
            break;
          default:
            break;
        }
      });
    }
  });
};

// Component for lazy loading with intersection observer
export const LazyLoadOnVisible = ({ 
  children, 
  fallback = <LoadingSpinner />, 
  rootMargin = '50px',
  threshold = 0.1 
}) => {
  const [isVisible, setIsVisible] = React.useState(false);
  const ref = React.useRef();

  React.useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin, threshold }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => observer.disconnect();
  }, [rootMargin, threshold]);

  return (
    <div ref={ref}>
      {isVisible ? children : fallback}
    </div>
  );
};

// Hook for managing lazy loading state
export const useLazyLoading = (triggerReason = 'user_interaction') => {
  const [loadedComponents, setLoadedComponents] = React.useState(new Set());

  const recordLazyLoadingTrigger = React.useCallback((componentType) => {
    if (window.adminPanelMetrics) {
      window.adminPanelMetrics.recordLazyLoadingTrigger(componentType, triggerReason);
    }
  }, [triggerReason]);

  const loadComponent = React.useCallback((componentName) => {
    if (!loadedComponents.has(componentName)) {
      recordLazyLoadingTrigger(componentName);
      setLoadedComponents(prev => new Set([...prev, componentName]));
    }
  }, [loadedComponents, recordLazyLoadingTrigger]);

  return { loadedComponents, loadComponent };
};

export default {
  LazyAdminDashboard,
  LazyIntegratedAdminPanel,
  LazyUserManagement,
  LazyRoleManagement,
  LazyModerationPanel,
  LazyMarketingDashboard,
  LazyProjectDashboard,
  LazyNotificationCenter,
  LazyAdvancedAnalytics,
  LazyBackupManager,
  preloadCriticalComponents,
  LazyLoadOnVisible,
  useLazyLoading
};