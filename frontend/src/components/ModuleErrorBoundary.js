import React from 'react';
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import ModuleCard from './ModuleCard';
import EnhancedButton from './EnhancedButton';

class ModuleErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null,
      retryCount: 0
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error(`ModuleErrorBoundary caught an error in ${this.props.module || 'unknown'} module:`, error, errorInfo);
    
    this.setState({
      error: error,
      errorInfo: errorInfo
    });

    // Send error to monitoring service if available
    if (window.errorReporting) {
      window.errorReporting.captureException(error, {
        module: this.props.module,
        component: this.props.componentName,
        errorInfo
      });
    }
  }

  handleRetry = () => {
    this.setState(prevState => ({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: prevState.retryCount + 1
    }));
  };

  render() {
    if (this.state.hasError) {
      const { error, errorInfo, retryCount } = this.state;
      const { fallback, module = 'system', componentName = 'Component' } = this.props;

      // If custom fallback is provided
      if (fallback) {
        return fallback(error, this.handleRetry, module);
      }

      // Module-specific error messages
      const getModuleErrorMessage = () => {
        switch (module) {
          case 'marketing':
            return 'Произошла ошибка в маркетинговом модуле. Проверьте подключение к аналитическим сервисам.';
          case 'moderation':
            return 'Ошибка в системе модерации. Возможны проблемы с загрузкой очереди сообщений.';
          case 'project':
            return 'Ошибка в модуле управления проектом. Проверьте доступность системы задач.';
          case 'analytics':
            return 'Ошибка в аналитическом модуле. Возможны проблемы с обработкой данных.';
          case 'system':
            return 'Системная ошибка. Обратитесь к администратору если проблема повторяется.';
          default:
            return 'Произошла непредвиденная ошибка в модуле админ-панели.';
        }
      };

      return (
        <ModuleErrorBoundaryUI
          module={module}
          componentName={componentName}
          error={error}
          errorInfo={errorInfo}
          retryCount={retryCount}
          onRetry={this.handleRetry}
          errorMessage={getModuleErrorMessage()}
        />
      );
    }

    return this.props.children;
  }
}

// Separate UI component to use hooks
const ModuleErrorBoundaryUI = ({ 
  module, 
  componentName, 
  error, 
  errorInfo, 
  retryCount, 
  onRetry, 
  errorMessage 
}) => {
  const { getModuleColor } = useTheme();
  const moduleColor = getModuleColor(module);

  return (
    <div className="min-h-[400px] flex items-center justify-center p-4">
      <ModuleCard 
        module={module} 
        variant="module" 
        hover={false}
        className="max-w-lg w-full"
      >
        <div className="text-center">
          {/* Error Icon */}
          <div 
            className="w-16 h-16 mx-auto mb-6 rounded-full flex items-center justify-center"
            style={{ 
              backgroundColor: `${moduleColor}20`,
              border: `2px solid ${moduleColor}40`
            }}
          >
            <AlertTriangle 
              className="w-8 h-8" 
              style={{ color: moduleColor }}
            />
          </div>
          
          {/* Error Title */}
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Ошибка в модуле {componentName}
          </h2>
          
          {/* Error Message */}
          <p className="text-gray-600 dark:text-gray-400 mb-6 leading-relaxed">
            {errorMessage}
          </p>

          {/* Development Error Details */}
          {process.env.NODE_ENV === 'development' && error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6 text-left">
              <div className="flex items-center mb-2">
                <Bug className="w-4 h-4 text-red-600 dark:text-red-400 mr-2" />
                <h3 className="text-sm font-semibold text-red-800 dark:text-red-300">
                  Детали ошибки (режим разработки):
                </h3>
              </div>
              <pre className="text-xs text-red-700 dark:text-red-400 whitespace-pre-wrap break-all max-h-32 overflow-y-auto">
                {error.toString()}
                {errorInfo && errorInfo.componentStack}
              </pre>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <EnhancedButton
              variant="module"
              module={module}
              onClick={onRetry}
              disabled={retryCount >= 3}
              icon={<RefreshCw className="w-4 h-4" />}
            >
              {retryCount >= 3 ? 'Лимит попыток' : 'Попробовать снова'}
            </EnhancedButton>
            
            <Link to="/admin">
              <EnhancedButton
                variant="module-outline"
                module={module}
                icon={<Home className="w-4 h-4" />}
              >
                К дашборду
              </EnhancedButton>
            </Link>
          </div>

          {/* Retry Counter */}
          {retryCount > 0 && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-4">
              Попыток восстановления: {retryCount}/3
            </p>
          )}

          {/* Module Info */}
          <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Модуль: {module} • Компонент: {componentName}
            </p>
          </div>
        </div>
      </ModuleCard>
    </div>
  );
};

// Preset error boundaries for different modules
export const MarketingErrorBoundary = ({ children, ...props }) => (
  <ModuleErrorBoundary module="marketing" {...props}>
    {children}
  </ModuleErrorBoundary>
);

export const ModerationErrorBoundary = ({ children, ...props }) => (
  <ModuleErrorBoundary module="moderation" {...props}>
    {children}
  </ModuleErrorBoundary>
);

export const ProjectErrorBoundary = ({ children, ...props }) => (
  <ModuleErrorBoundary module="project" {...props}>
    {children}
  </ModuleErrorBoundary>
);

export const AnalyticsErrorBoundary = ({ children, ...props }) => (
  <ModuleErrorBoundary module="analytics" {...props}>
    {children}
  </ModuleErrorBoundary>
);

export const SystemErrorBoundary = ({ children, ...props }) => (
  <ModuleErrorBoundary module="system" {...props}>
    {children}
  </ModuleErrorBoundary>
);

export default ModuleErrorBoundary;